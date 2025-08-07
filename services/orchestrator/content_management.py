# /services/orchestrator/content_management.py
"""
Content Management API - Track generated content, drafts, and publishing status
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import os

logger = logging.getLogger(__name__)

# Database setup
POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN", "postgresql://postgres:pass@postgres:5432/postgres"
)
engine = create_engine(POSTGRES_DSN)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter(prefix="/content", tags=["content"])


class ContentStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class Platform(str, Enum):
    DEV_TO = "dev.to"
    LINKEDIN = "linkedin"
    THREADS = "threads"
    MEDIUM = "medium"
    GITHUB = "github"


class ContentItem(BaseModel):
    id: int
    persona_id: str
    hook: str
    body: str
    full_content: str
    status: ContentStatus
    platforms: List[Platform]
    quality_score: Optional[float] = None
    tokens_used: int = 0
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None


class ContentCreate(BaseModel):
    persona_id: str
    hook: str
    body: str
    platforms: List[Platform]
    status: ContentStatus = ContentStatus.DRAFT
    quality_score: Optional[float] = None


class ContentUpdate(BaseModel):
    hook: Optional[str] = None
    body: Optional[str] = None
    status: Optional[ContentStatus] = None
    platforms: Optional[List[Platform]] = None
    scheduled_at: Optional[datetime] = None


class PlatformContent(BaseModel):
    """Platform-specific adapted content"""

    platform: Platform
    title: str
    content: str
    hashtags: List[str]
    call_to_action: str
    estimated_engagement: float


@router.get("/posts", response_model=List[ContentItem])
async def get_content_posts(
    status: Optional[ContentStatus] = None,
    platform: Optional[Platform] = None,
    persona_id: Optional[str] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
):
    """Get list of generated content posts with filters"""
    try:
        with SessionLocal() as db:
            # Base query - get posts with extended info
            query = text("""
                SELECT 
                    p.id,
                    p.persona_id,
                    p.hook,
                    p.body,
                    CONCAT(p.hook, E'\n\n', p.body) as full_content,
                    COALESCE(p.quality_score::text, 'null')::text as quality_score,
                    p.tokens_used,
                    p.ts as created_at,
                    'draft' as status,  -- Default status for now
                    ARRAY['dev.to', 'linkedin'] as platforms,  -- Default platforms
                    null as scheduled_at,
                    null as published_at
                FROM posts p
                ORDER BY p.ts DESC
                LIMIT :limit OFFSET :offset
            """)

            result = db.execute(query, {"limit": limit, "offset": offset})

            posts = []
            for row in result:
                # Parse quality score
                quality_score = None
                if row.quality_score and row.quality_score != "null":
                    try:
                        quality_score = float(row.quality_score)
                    except:
                        pass

                posts.append(
                    ContentItem(
                        id=row.id,
                        persona_id=row.persona_id,
                        hook=row.hook,
                        body=row.body,
                        full_content=row.full_content,
                        status=ContentStatus.DRAFT,  # TODO: Add status tracking
                        platforms=[
                            Platform.DEV_TO,
                            Platform.LINKEDIN,
                        ],  # TODO: Add platform tracking
                        quality_score=quality_score,
                        tokens_used=row.tokens_used or 0,
                        created_at=row.created_at,
                        scheduled_at=None,
                        published_at=None,
                    )
                )

            return posts
    except Exception as e:
        logger.error(f"Error fetching content posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/{post_id}", response_model=ContentItem)
async def get_content_post(post_id: int):
    """Get specific content post by ID"""
    try:
        with SessionLocal() as db:
            query = text("""
                SELECT 
                    p.id,
                    p.persona_id,
                    p.hook,
                    p.body,
                    CONCAT(p.hook, E'\n\n', p.body) as full_content,
                    COALESCE(p.quality_score::text, 'null')::text as quality_score,
                    p.tokens_used,
                    p.ts as created_at
                FROM posts p
                WHERE p.id = :post_id
            """)

            result = db.execute(query, {"post_id": post_id}).fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Content post not found")

            # Parse quality score
            quality_score = None
            if result.quality_score and result.quality_score != "null":
                try:
                    quality_score = float(result.quality_score)
                except:
                    pass

            return ContentItem(
                id=result.id,
                persona_id=result.persona_id,
                hook=result.hook,
                body=result.body,
                full_content=result.full_content,
                status=ContentStatus.DRAFT,
                platforms=[Platform.DEV_TO, Platform.LINKEDIN],
                quality_score=quality_score,
                tokens_used=result.tokens_used or 0,
                created_at=result.created_at,
                scheduled_at=None,
                published_at=None,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching content post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/posts/{post_id}", response_model=ContentItem)
async def update_content_post(post_id: int, update: ContentUpdate):
    """Update content post (edit, change status, schedule, etc.)"""
    try:
        with SessionLocal() as db:
            # Build dynamic update query
            set_clauses = []
            params = {"post_id": post_id}

            if update.hook is not None:
                set_clauses.append("hook = :hook")
                params["hook"] = update.hook

            if update.body is not None:
                set_clauses.append("body = :body")
                params["body"] = update.body

            if not set_clauses:
                # No updates to make, just return current post
                return await get_content_post(post_id)

            # Update the post
            update_query = text(f"""
                UPDATE posts 
                SET {", ".join(set_clauses)}
                WHERE id = :post_id
                RETURNING id
            """)

            result = db.execute(update_query, params)
            db.commit()

            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Content post not found")

            # Return updated post
            return await get_content_post(post_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating content post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/posts/{post_id}/adapt", response_model=List[PlatformContent])
async def adapt_content_for_platforms(post_id: int, platforms: List[Platform]):
    """Adapt content for specific platforms (different formats, lengths, etc.)"""
    try:
        # Get the original content
        post = await get_content_post(post_id)

        adapted_content = []

        for platform in platforms:
            if platform == Platform.DEV_TO:
                # Dev.to format - technical article style
                adapted_content.append(
                    PlatformContent(
                        platform=platform,
                        title=post.hook.replace("🚀", "").strip(),
                        content=f"# {post.hook}\n\n{post.body}\n\n---\n\n*What's your experience with this? Share in the comments below!*",
                        hashtags=["#programming", "#webdev", "#tutorial", "#tech"],
                        call_to_action="Follow for more technical insights and tutorials!",
                        estimated_engagement=7.2,
                    )
                )

            elif platform == Platform.LINKEDIN:
                # LinkedIn format - professional, shorter
                lines = post.body.split("\n")
                short_body = (
                    "\n".join(lines[:3]) + "..." if len(lines) > 3 else post.body
                )

                adapted_content.append(
                    PlatformContent(
                        platform=platform,
                        title=post.hook,
                        content=f"{post.hook}\n\n{short_body}\n\n💼 What's your take on this? Share your thoughts!\n\n#SoftwareDevelopment #TechLeadership #Programming",
                        hashtags=[
                            "#SoftwareDevelopment",
                            "#TechLeadership",
                            "#Programming",
                        ],
                        call_to_action="Connect with me for more tech insights!",
                        estimated_engagement=4.1,
                    )
                )

            elif platform == Platform.THREADS:
                # Threads format - conversational, short
                adapted_content.append(
                    PlatformContent(
                        platform=platform,
                        title=post.hook[:100] + "..."
                        if len(post.hook) > 100
                        else post.hook,
                        content=f"{post.hook}\n\nHere's the key insight:\n{post.body[:200]}...\n\nWhat do you think? 🤔",
                        hashtags=["#tech", "#programming", "#dev"],
                        call_to_action="Follow for daily tech insights!",
                        estimated_engagement=8.3,
                    )
                )

            elif platform == Platform.MEDIUM:
                # Medium format - long-form article
                adapted_content.append(
                    PlatformContent(
                        platform=platform,
                        title=post.hook.replace("🚀", "").strip(),
                        content=f"# {post.hook}\n\n{post.body}\n\n## Key Takeaways\n\n- Implementation requires careful planning\n- Performance monitoring is crucial\n- Documentation helps team adoption\n\n*Thank you for reading! If you found this helpful, please give it a clap and follow for more technical insights.*",
                        hashtags=[
                            "programming",
                            "software-development",
                            "technology",
                            "web-development",
                        ],
                        call_to_action="Follow me on Medium for more in-depth technical articles!",
                        estimated_engagement=5.7,
                    )
                )

        return adapted_content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adapting content for platforms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_content_stats():
    """Get content generation statistics"""
    try:
        with SessionLocal() as db:
            # Get basic stats
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_posts,
                    COUNT(*) FILTER (WHERE ts >= NOW() - INTERVAL '24 hours') as posts_today,
                    COUNT(*) FILTER (WHERE ts >= NOW() - INTERVAL '7 days') as posts_this_week,
                    AVG(COALESCE(quality_score, 0)) as avg_quality_score,
                    COUNT(DISTINCT persona_id) as active_personas
                FROM posts
            """)

            result = db.execute(stats_query).fetchone()

            return {
                "total_posts": result.total_posts or 0,
                "posts_today": result.posts_today or 0,
                "posts_this_week": result.posts_this_week or 0,
                "avg_quality_score": round(float(result.avg_quality_score or 0), 2),
                "active_personas": result.active_personas or 0,
                "draft_count": result.total_posts or 0,  # All are drafts for now
                "scheduled_count": 0,  # TODO: Implement scheduling
                "published_count": 0,  # TODO: Implement publishing tracking
                "ready_count": 0,
            }
    except Exception as e:
        logger.error(f"Error fetching content stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
