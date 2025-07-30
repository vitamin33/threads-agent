# services/threads_adaptor/main.py
"""
Real Threads API integration service.

This service handles:
- OAuth 2.0 authentication with Threads/Meta
- Publishing posts to Threads
- Fetching engagement metrics (likes, comments, shares, follows)
- Storing analytics in PostgreSQL
- Rate limiting and error handling
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from services.common.metrics import (
    record_business_metric,
    record_engagement_rate,
    update_revenue_projection,
)

from .limiter import rate_limited_call

app = FastAPI(title="threads-adaptor")

# Environment variables
THREADS_APP_ID = os.getenv("THREADS_APP_ID", "")
THREADS_APP_SECRET = os.getenv("THREADS_APP_SECRET", "")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/postgres"
)

# API endpoints
THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_MEDIA_ENDPOINT = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads"
THREADS_PUBLISH_ENDPOINT = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads_publish"
THREADS_PROFILE_ENDPOINT = f"{THREADS_API_BASE}/{THREADS_USER_ID}"

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ThreadsPost(Base):
    """
    Database model for Threads posts with engagement metrics.
    """

    __tablename__ = "threads_posts"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True)  # Threads post ID
    persona_id = Column(String, index=True)  # Which AI persona created this
    content = Column(String)  # Post content
    media_type = Column(String)  # "TEXT", "IMAGE", "VIDEO", "CAROUSEL"
    published_at = Column(DateTime)  # When it was published
    engagement_data = Column(JSON)  # Raw engagement data from API

    # Engagement metrics
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    impressions_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)  # (likes+comments+shares)/impressions

    updated_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


class PublishRequest(BaseModel):
    """
    Request model for publishing content to Threads.
    """

    content: str = Field(..., description="Post content (max 500 chars)")
    persona_id: str = Field(..., description="AI persona that generated this")
    variant_id: Optional[str] = Field(None, description="Variant ID for A/B testing")
    expected_engagement_rate: Optional[float] = Field(
        None, description="Expected engagement rate for monitoring"
    )
    media_urls: Optional[List[str]] = Field(
        None, description="Optional media URLs to attach"
    )
    reply_to: Optional[str] = Field(None, description="Thread ID to reply to")


class EngagementResponse(BaseModel):
    """
    Response model for engagement metrics.
    """

    thread_id: str
    persona_id: str
    engagement_rate: float
    likes_count: int
    comments_count: int
    shares_count: int
    impressions_count: int
    published_at: datetime
    updated_at: datetime


class ProfileMetrics(BaseModel):
    """
    Response model for profile-level metrics.
    """

    followers_count: int
    posts_count: int
    avg_engagement_rate: float
    total_impressions: int
    growth_rate: float  # followers gained in last 30 days


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "threads-adaptor"}


@app.post("/publish", response_model=dict)
async def publish_post(
    request: PublishRequest, background_tasks: BackgroundTasks
) -> dict:
    """
    Publish content to Threads.

    Args:
        request: Post content and metadata
        background_tasks: For async engagement tracking

    Returns:
        Published post metadata including Threads post ID
    """
    if not all([THREADS_APP_ID, THREADS_ACCESS_TOKEN, THREADS_USER_ID]):
        raise HTTPException(
            status_code=503, detail="Threads API credentials not configured"
        )

    try:
        # Step 1: Create media container
        media_payload = {
            "media_type": "TEXT",
            "text": request.content,
            "access_token": THREADS_ACCESS_TOKEN,
        }

        # Add media if provided
        if request.media_urls:
            media_payload["media_type"] = "IMAGE"  # or VIDEO, CAROUSEL
            media_payload["image_url"] = request.media_urls[0]  # Simplified

        # Add reply_to if provided
        if request.reply_to:
            media_payload["reply_to_id"] = request.reply_to

        # Rate-limited API call
        media_response = await rate_limited_call(
            "POST", THREADS_MEDIA_ENDPOINT, json=media_payload
        )
        media_id = media_response["id"]

        # Step 2: Publish the media
        publish_payload = {
            "creation_id": media_id,
            "access_token": THREADS_ACCESS_TOKEN,
        }

        publish_response = await rate_limited_call(
            "POST", THREADS_PUBLISH_ENDPOINT, json=publish_payload
        )
        thread_id = publish_response["id"]

        # Step 3: Store in database
        db = SessionLocal()
        try:
            threads_post = ThreadsPost(
                thread_id=thread_id,
                persona_id=request.persona_id,
                content=request.content,
                media_type=media_payload["media_type"],
                published_at=datetime.utcnow(),
                engagement_data={"initial": publish_response},
            )
            db.add(threads_post)
            db.commit()
            db.refresh(threads_post)
        finally:
            db.close()

        # Step 4: Schedule engagement tracking
        background_tasks.add_task(track_engagement_async, thread_id, request.persona_id)

        # Step 5: Trigger performance monitoring if variant_id is provided
        if request.variant_id:
            try:
                # Import here to avoid circular dependency
                from services.performance_monitor.integration import on_variant_posted

                monitoring_data = {
                    "variant_id": request.variant_id,
                    "persona_id": request.persona_id,
                    "post_id": thread_id,
                    "expected_engagement_rate": request.expected_engagement_rate
                    or 0.06,
                }
                on_variant_posted(monitoring_data)
            except Exception as e:
                print(
                    f"Failed to start monitoring for variant {request.variant_id}: {e}"
                )

        # Record business metric
        record_business_metric(
            "posts_published_total", 1, {"persona_id": request.persona_id}
        )

        return {
            "thread_id": thread_id,
            "status": "published",
            "persona_id": request.persona_id,
            "variant_id": request.variant_id,
            "published_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Publishing failed: {str(e)}")


@app.get("/engagement/{thread_id}", response_model=EngagementResponse)
async def get_engagement(thread_id: str) -> EngagementResponse:
    """
    Get engagement metrics for a specific post.

    Args:
        thread_id: Threads post ID

    Returns:
        Current engagement metrics
    """
    db = SessionLocal()
    try:
        post = db.query(ThreadsPost).filter(ThreadsPost.thread_id == thread_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Fetch fresh metrics from Threads API
        await update_post_engagement(post)

        return EngagementResponse(
            thread_id=post.thread_id,
            persona_id=post.persona_id,
            engagement_rate=post.engagement_rate,
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            shares_count=post.shares_count,
            impressions_count=post.impressions_count,
            published_at=post.published_at,
            updated_at=post.updated_at,
        )
    finally:
        db.close()


@app.get("/profile", response_model=ProfileMetrics)
async def get_profile_metrics() -> ProfileMetrics:
    """
    Get profile-level engagement metrics.

    Returns:
        Aggregated metrics across all posts
    """
    if not THREADS_ACCESS_TOKEN:
        raise HTTPException(
            status_code=503, detail="Threads API credentials not configured"
        )

    try:
        # Fetch profile data from Threads API
        profile_payload = {
            "fields": "id,username,threads_profile_picture_url,threads_biography",
            "access_token": THREADS_ACCESS_TOKEN,
        }

        await rate_limited_call("GET", THREADS_PROFILE_ENDPOINT, params=profile_payload)

        # Calculate metrics from database
        db = SessionLocal()
        try:
            posts = db.query(ThreadsPost).all()
            total_posts = len(posts)
            avg_engagement = (
                sum(p.engagement_rate for p in posts) / total_posts
                if total_posts > 0
                else 0.0
            )
            total_impressions = sum(p.impressions_count for p in posts)

            # Calculate growth rate (simplified)
            recent_posts = [
                p
                for p in posts
                if p.published_at > datetime.utcnow() - timedelta(days=30)
            ]
            growth_rate = len(recent_posts) / 30.0 if recent_posts else 0.0

            return ProfileMetrics(
                followers_count=0,  # Not available in basic API
                posts_count=total_posts,
                avg_engagement_rate=avg_engagement,
                total_impressions=total_impressions,
                growth_rate=growth_rate,
            )
        finally:
            db.close()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch profile metrics: {str(e)}"
        )


@app.get("/posts")
async def list_posts(persona_id: Optional[str] = None, limit: int = 50) -> List[dict]:
    """
    List published posts with engagement data.

    Args:
        persona_id: Filter by AI persona (optional)
        limit: Maximum posts to return

    Returns:
        List of posts with engagement metrics
    """
    db = SessionLocal()
    try:
        query = db.query(ThreadsPost)
        if persona_id:
            query = query.filter(ThreadsPost.persona_id == persona_id)

        posts = query.order_by(ThreadsPost.published_at.desc()).limit(limit).all()

        return [
            {
                "thread_id": p.thread_id,
                "persona_id": p.persona_id,
                "content": p.content[:100] + "..."
                if len(p.content) > 100
                else p.content,
                "engagement_rate": p.engagement_rate,
                "likes_count": p.likes_count,
                "comments_count": p.comments_count,
                "published_at": p.published_at.isoformat(),
            }
            for p in posts
        ]
    finally:
        db.close()


async def track_engagement_async(thread_id: str, persona_id: str) -> None:
    """
    Background task to track engagement metrics over time.

    Args:
        thread_id: Threads post ID
        persona_id: AI persona that created the post
    """
    # Wait a bit for initial engagement
    await asyncio.sleep(300)  # 5 minutes

    db = SessionLocal()
    try:
        post = db.query(ThreadsPost).filter(ThreadsPost.thread_id == thread_id).first()
        if post:
            await update_post_engagement(post)
            # Record engagement rate for business metrics
            record_engagement_rate(persona_id, post.engagement_rate)
            # Update revenue projection based on engagement
            revenue_impact = post.engagement_rate * 10  # $10 per 1% engagement
            update_revenue_projection("engagement", revenue_impact)
    finally:
        db.close()


async def update_post_engagement(post: ThreadsPost) -> None:
    """
    Update engagement metrics for a post from Threads API.

    Args:
        post: Database post object to update
    """
    try:
        # Fetch engagement data from Threads API
        insights_payload = {
            "metric": "likes,comments,shares,impressions",
            "access_token": THREADS_ACCESS_TOKEN,
        }

        insights_url = f"{THREADS_API_BASE}/{post.thread_id}/insights"
        insights_response = await rate_limited_call(
            "GET", insights_url, params=insights_payload
        )

        # Parse metrics (simplified - actual API response structure may vary)
        metrics = {
            item["name"]: item["values"][0]["value"]
            for item in insights_response.get("data", [])
        }

        post.likes_count = metrics.get("likes", 0)
        post.comments_count = metrics.get("comments", 0)
        post.shares_count = metrics.get("shares", 0)
        post.impressions_count = metrics.get("impressions", 1)  # Avoid division by zero

        # Calculate engagement rate
        total_engagement = post.likes_count + post.comments_count + post.shares_count
        post.engagement_rate = total_engagement / post.impressions_count

        post.engagement_data = {
            "latest": insights_response,
            "updated_at": datetime.utcnow().isoformat(),
        }
        post.updated_at = datetime.utcnow()

        # Commit to database
        db = SessionLocal()
        try:
            db.merge(post)
            db.commit()
        finally:
            db.close()

    except Exception as e:
        print(f"Failed to update engagement for {post.thread_id}: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8070)
