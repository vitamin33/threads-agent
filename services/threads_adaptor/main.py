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
from typing import Any, Dict, List, Optional

import httpx
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
    "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/threads_agent"
)

# API endpoints
THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_MEDIA_ENDPOINT = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads"
THREADS_PUBLISH_ENDPOINT = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads_publish"

# Database setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ThreadsPost(Base):
    """Database model for tracking published Threads posts."""

    __tablename__ = "threads_posts"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True)
    persona_id = Column(String, index=True)
    content = Column(String)
    media_type = Column(String, default="TEXT")
    published_at = Column(DateTime, default=datetime.utcnow)
    engagement_data = Column(JSON)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    impressions_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models
class PostRequest(BaseModel):
    """Request model for creating a Threads post."""

    topic: str
    content: str
    persona_id: str = Field(default="ai-jesus")
    media_type: str = Field(
        default="TEXT", description="TEXT, IMAGE, VIDEO, or CAROUSEL"
    )
    media_urls: Optional[List[str]] = Field(
        default=None, description="URLs for media content"
    )


class PostResponse(BaseModel):
    """Response model for a published Threads post."""

    status: str
    thread_id: str
    permalink: Optional[str] = None
    message: Optional[str] = None


class EngagementMetrics(BaseModel):
    """Model for engagement metrics from Threads."""

    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    impressions_count: int = 0
    engagement_rate: float = 0.0
    followers_count: int = 0


# Create tables
Base.metadata.create_all(bind=engine)


@app.get("/ping")
def ping() -> dict[str, bool]:
    """Liveness probe."""
    return {"pong": True}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    # Check if we have valid credentials
    if not all([THREADS_APP_ID, THREADS_ACCESS_TOKEN, THREADS_USER_ID]):
        return {"status": "unhealthy", "reason": "Missing Threads API credentials"}

    # Try to validate token with a simple API call
    try:
        async with httpx.AsyncClient() as client:
            response = await rate_limited_call(
                client.get,
                f"{THREADS_API_BASE}/{THREADS_USER_ID}",
                params={"access_token": THREADS_ACCESS_TOKEN, "fields": "id"},
                timeout=5.0,
            )
            if response.status_code == 200:
                return {"status": "ok"}
            else:
                return {
                    "status": "unhealthy",
                    "reason": f"API returned {response.status_code}",
                }
    except Exception as e:
        return {"status": "unhealthy", "reason": str(e)}


@app.post("/publish", response_model=PostResponse)
async def publish_post(
    post: PostRequest, background_tasks: BackgroundTasks
) -> PostResponse:
    """
    Publish a post to Threads.

    This replaces the fake-threads /publish endpoint with real Threads API integration.
    """
    if not THREADS_ACCESS_TOKEN:
        raise HTTPException(status_code=503, detail="Threads API not configured")

    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Create media container
            create_params = {
                "access_token": THREADS_ACCESS_TOKEN,
                "media_type": post.media_type,
                "text": post.content,
            }

            # Add media URLs if provided
            if post.media_urls and post.media_type != "TEXT":
                if post.media_type == "IMAGE":
                    create_params["image_url"] = post.media_urls[0]
                elif post.media_type == "VIDEO":
                    create_params["video_url"] = post.media_urls[0]
                elif post.media_type == "CAROUSEL":
                    # Carousel requires child media containers
                    # This is more complex and would need separate implementation
                    pass

            # Create the media container
            create_response = await rate_limited_call(
                client.post, THREADS_MEDIA_ENDPOINT, params=create_params, timeout=30.0
            )
            create_data = create_response.json()

            if "error" in create_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to create media: {create_data['error']['message']}",
                )

            media_id = create_data["id"]

            # Step 2: Publish the media container
            publish_params = {
                "access_token": THREADS_ACCESS_TOKEN,
                "creation_id": media_id,
            }

            publish_response = await rate_limited_call(
                client.post,
                THREADS_PUBLISH_ENDPOINT,
                params=publish_params,
                timeout=30.0,
            )
            publish_data = publish_response.json()

            if "error" in publish_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to publish: {publish_data['error']['message']}",
                )

            thread_id = publish_data["id"]

            # Store in database
            db = SessionLocal()
            try:
                db_post = ThreadsPost(
                    thread_id=thread_id,
                    persona_id=post.persona_id,
                    content=post.content,
                    media_type=post.media_type,
                    published_at=datetime.utcnow(),
                )
                db.add(db_post)
                db.commit()
            finally:
                db.close()

            # Schedule background task to fetch initial metrics after a delay
            background_tasks.add_task(
                fetch_engagement_metrics_delayed,
                thread_id,
                post.persona_id,
                delay_seconds=300,  # Wait 5 minutes for initial engagement
            )

            return PostResponse(
                status="published",
                thread_id=thread_id,
                permalink=f"https://www.threads.net/@{THREADS_USER_ID}/post/{thread_id}",
                message="Post published successfully to Threads",
            )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/published")
async def list_published() -> List[Dict[str, Any]]:
    """
    List all published posts with their engagement metrics.

    This replaces fake-threads /published endpoint with real data.
    """
    db = SessionLocal()
    try:
        posts = (
            db.query(ThreadsPost)
            .order_by(ThreadsPost.published_at.desc())
            .limit(100)
            .all()
        )
        return [
            {
                "thread_id": post.thread_id,
                "persona_id": post.persona_id,
                "content": post.content,
                "published_at": post.published_at.isoformat(),
                "engagement": {
                    "likes": post.likes_count,
                    "comments": post.comments_count,
                    "shares": post.shares_count,
                    "impressions": post.impressions_count,
                    "engagement_rate": post.engagement_rate,
                },
                "permalink": f"https://www.threads.net/@{THREADS_USER_ID}/post/{post.thread_id}",
            }
            for post in posts
        ]
    finally:
        db.close()


@app.get("/metrics/{thread_id}", response_model=EngagementMetrics)
async def get_post_metrics(thread_id: str) -> EngagementMetrics:
    """Fetch current engagement metrics for a specific post."""
    metrics = await fetch_post_metrics(thread_id)
    return metrics


@app.post("/refresh-metrics")
async def refresh_all_metrics(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Refresh engagement metrics for all recent posts."""
    db = SessionLocal()
    try:
        # Get posts from last 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        posts = (
            db.query(ThreadsPost).filter(ThreadsPost.published_at >= cutoff_date).all()
        )

        for post in posts:
            background_tasks.add_task(
                update_post_metrics, post.thread_id, post.persona_id
            )

        return {
            "status": "refreshing",
            "message": f"Refreshing metrics for {len(posts)} posts",
        }
    finally:
        db.close()


async def fetch_post_metrics(thread_id: str) -> EngagementMetrics:
    """Fetch engagement metrics for a specific Threads post."""
    if not THREADS_ACCESS_TOKEN:
        return EngagementMetrics()

    try:
        async with httpx.AsyncClient() as client:
            # Fetch post insights
            response = await rate_limited_call(
                client.get,
                f"{THREADS_API_BASE}/{thread_id}/insights",
                params={
                    "access_token": THREADS_ACCESS_TOKEN,
                    "metric": "likes,replies,reposts,quotes,followers_count,impressions",
                },
                timeout=10.0,
            )

            if response.status_code != 200:
                return EngagementMetrics()

            data = response.json()
            metrics_data = data.get("data", [])

            # Parse metrics
            likes = 0
            comments = 0
            shares = 0
            impressions = 0
            followers = 0

            for metric in metrics_data:
                name = metric.get("name", "")
                values = metric.get("values", [])
                if values:
                    value = values[0].get("value", 0)
                    if name == "likes":
                        likes = value
                    elif name == "replies":
                        comments = value
                    elif name in ["reposts", "quotes"]:
                        shares += value
                    elif name == "impressions":
                        impressions = value
                    elif name == "followers_count":
                        followers = value

            # Calculate engagement rate
            if impressions > 0:
                engagement_rate = (likes + comments + shares) / impressions
            else:
                engagement_rate = 0.0

            return EngagementMetrics(
                likes_count=likes,
                comments_count=comments,
                shares_count=shares,
                impressions_count=impressions,
                engagement_rate=engagement_rate,
                followers_count=followers,
            )

    except Exception as e:
        print(f"Error fetching metrics for {thread_id}: {e}")
        return EngagementMetrics()


async def update_post_metrics(thread_id: str, persona_id: str) -> None:
    """Update metrics for a post in the database."""
    metrics = await fetch_post_metrics(thread_id)

    db = SessionLocal()
    try:
        post = db.query(ThreadsPost).filter(ThreadsPost.thread_id == thread_id).first()
        if post:
            post.likes_count = metrics.likes_count
            post.comments_count = metrics.comments_count
            post.shares_count = metrics.shares_count
            post.impressions_count = metrics.impressions_count
            post.engagement_rate = metrics.engagement_rate
            post.engagement_data = metrics.model_dump()
            post.updated_at = datetime.utcnow()
            db.commit()

            # Record metrics for Prometheus
            record_engagement_rate(persona_id, metrics.engagement_rate)

            # Update business metrics
            if metrics.followers_count > 0:
                # Estimate cost per follow based on post performance
                # This is a simplified calculation
                cost_per_follow = 0.05  # $0.05 estimated cost per follower
                record_business_metric(
                    "cost_per_follow", persona_id=persona_id, cost=cost_per_follow
                )

                # Update revenue projection based on follower growth
                # Assuming $1 per 1000 followers per month (simplified)
                monthly_revenue_per_follower = 0.001
                revenue_impact = metrics.followers_count * monthly_revenue_per_follower
                update_revenue_projection("threads_engagement", revenue_impact)
    finally:
        db.close()


async def fetch_engagement_metrics_delayed(
    thread_id: str, persona_id: str, delay_seconds: int = 300
) -> None:
    """Fetch engagement metrics after a delay to allow for initial engagement."""
    await asyncio.sleep(delay_seconds)
    await update_post_metrics(thread_id, persona_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
