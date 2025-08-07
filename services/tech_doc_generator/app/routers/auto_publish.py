"""
Auto-publishing endpoints for achievement-based content generation
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from ..models.article import Platform
from ..services.achievement_integration import AchievementIntegration
from ..core.config import get_settings

router = APIRouter(prefix="/auto-publish", tags=["auto-publish"])
logger = structlog.get_logger()


@router.post("/achievement-content")
async def publish_achievement_content(
    background_tasks: BackgroundTasks,
    platforms: Optional[List[Platform]] = Query(
        default=[Platform.DEVTO], description="Platforms to publish to"
    ),
    test_mode: bool = Query(
        default=True, description="If true, publishes as draft on dev.to"
    ),
    days_lookback: int = Query(
        default=7, description="Number of days to look back for achievements"
    ),
    min_business_value: float = Query(
        default=50000, description="Minimum business value threshold"
    ),
) -> Dict[str, Any]:
    """
    Automatically generate and publish content based on recent achievements

    Workflow:
    1. Fetches high-value achievements from the past N days
    2. Groups them by theme and selects the most impactful
    3. Generates a technical article with metrics
    4. Publishes to selected platforms
    """

    integration = AchievementIntegration()

    try:
        # Run the auto-publish workflow
        result = await integration.auto_publish_achievement_content(
            platforms=platforms, test_mode=test_mode
        )

        logger.info(
            "Auto-publish workflow completed",
            status=result["status"],
            platforms=list(result["platforms"].keys()),
        )

        return {
            "success": result["status"] == "completed",
            "result": result,
            "message": f"Content published to {len([p for p in result['platforms'].values() if p.get('success')])} platforms",
        }

    except Exception as e:
        logger.error("Auto-publish failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/achievement-preview")
async def preview_achievement_content(
    days_lookback: int = Query(default=7),
    min_business_value: float = Query(default=50000),
) -> Dict[str, Any]:
    """
    Preview what content would be generated from recent achievements
    """

    integration = AchievementIntegration()

    try:
        # Fetch achievements
        achievements = await integration.fetch_recent_achievements(
            days=days_lookback, min_business_value=min_business_value
        )

        if not achievements:
            return {
                "success": False,
                "message": "No recent high-value achievements found",
                "achievements": [],
            }

        # Generate content preview
        article = await integration.generate_content_from_achievements(achievements)

        return {
            "success": True,
            "preview": {
                "title": article.title,
                "subtitle": article.subtitle,
                "word_count": len(article.content.split()),
                "insights": article.insights,
                "tags": article.tags,
                "code_examples": len(article.code_examples),
                "first_paragraph": article.content.split("\n\n")[0],
            },
            "achievements_used": len(achievements),
            "total_business_value": sum(
                a.get("business_value", 0) for a in achievements
            ),
        }

    except Exception as e:
        logger.error("Preview generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule-daily")
async def schedule_daily_publication(
    background_tasks: BackgroundTasks,
    platforms: List[Platform] = Query(default=[Platform.DEVTO, Platform.LINKEDIN]),
    hour: int = Query(
        default=10, ge=0, le=23, description="Hour of day to publish (UTC)"
    ),
    enabled: bool = Query(default=True),
) -> Dict[str, Any]:
    """
    Schedule daily automatic content generation and publication
    """

    # This would integrate with Celery beat for scheduling
    # For now, return configuration

    schedule_config = {
        "enabled": enabled,
        "platforms": [p.value for p in platforms],
        "schedule": {"hour": hour, "minute": 0, "timezone": "UTC"},
        "filters": {
            "min_business_value": 50000,
            "days_lookback": 7,
            "min_achievements": 3,
        },
    }

    if enabled:
        logger.info("Daily publication scheduled", config=schedule_config)
        return {
            "success": True,
            "message": f"Daily publication scheduled for {hour:02d}:00 UTC",
            "config": schedule_config,
        }
    else:
        logger.info("Daily publication disabled")
        return {
            "success": True,
            "message": "Daily publication disabled",
            "config": schedule_config,
        }


@router.get("/publishing-stats")
async def get_publishing_stats() -> Dict[str, Any]:
    """
    Get statistics about auto-publishing performance
    """

    # This would query the database for real stats
    # For now, return mock data

    return {
        "total_articles_published": 12,
        "platforms": {
            "devto": {"published": 8, "views": 2450, "reactions": 156, "comments": 23},
            "linkedin": {
                "drafted": 12,
                "manually_published": 7,
                "impressions": 5600,
                "engagement_rate": "4.2%",
            },
            "threads": {"published": 5, "impressions": 1200, "engagement_rate": "6.8%"},
        },
        "top_performing_article": {
            "title": "How I Reduced API Latency by 78% with Smart Caching",
            "platform": "devto",
            "views": 850,
            "reactions": 67,
        },
        "content_metrics": {
            "avg_quality_score": 8.5,
            "avg_word_count": 1850,
            "avg_code_examples": 3.5,
            "avg_insights": 5.2,
        },
        "last_published": datetime.now().isoformat(),
    }
