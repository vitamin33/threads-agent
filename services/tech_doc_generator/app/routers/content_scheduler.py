"""
Content Scheduler API Endpoints

REST API for managing automated weekly content generation schedules.
Integrates with achievement_collector and viral_engine for optimized content.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import structlog

from ..services.content_scheduler import (
    ContentScheduler,
    WeeklyContentPlan,
    ContentScheduleEntry,
    ScheduleFrequency,
    get_content_scheduler
)
from ..services.achievement_content_generator import Platform, ContentType

logger = structlog.get_logger()
router = APIRouter()


class CreateScheduleRequest(BaseModel):
    """Request to create a new content schedule"""
    week_start: Optional[datetime] = None
    target_companies: Optional[List[str]] = Field(None, example=["anthropic", "notion", "stripe"])
    platforms: Optional[List[Platform]] = Field(None, example=[Platform.LINKEDIN, Platform.MEDIUM])
    target_posts_per_week: int = Field(3, ge=1, le=7)
    auto_generate: bool = Field(True, description="Automatically generate content when due")


class ScheduleResponse(BaseModel):
    """Response for schedule operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ContentPreview(BaseModel):
    """Preview of generated content"""
    entry_id: str
    achievement_id: int
    platform: Platform
    content_type: ContentType
    target_company: Optional[str]
    title: str
    content_preview: str  # First 200 chars
    engagement_score: float
    quality_score: float
    scheduled_time: datetime
    hashtags: List[str]


@router.post("/schedules", response_model=ScheduleResponse)
async def create_weekly_schedule(
    request: CreateScheduleRequest,
    background_tasks: BackgroundTasks
) -> ScheduleResponse:
    """
    Create a new weekly content generation schedule.
    
    This endpoint creates an automated schedule that will:
    1. Select the best achievements for content generation
    2. Create optimized content using viral_engine
    3. Schedule posts across multiple platforms
    4. Target specific companies for job applications
    """
    try:
        scheduler = get_content_scheduler()
        
        # Create the weekly plan
        plan = await scheduler.create_weekly_schedule(
            week_start=request.week_start,
            target_companies=request.target_companies,
            custom_platforms=request.platforms
        )
        
        # If auto_generate is enabled, schedule background processing
        if request.auto_generate:
            plan_id = f"week_{plan.week_start.strftime('%Y%m%d')}"
            background_tasks.add_task(schedule_auto_processing, plan_id)
        
        logger.info("weekly_schedule_created_via_api",
                   week_start=plan.week_start.isoformat(),
                   entries=len(plan.scheduled_entries),
                   auto_generate=request.auto_generate)
        
        return ScheduleResponse(
            success=True,
            message=f"Weekly schedule created for {plan.week_start.strftime('%Y-%m-%d')}",
            data={
                "plan_id": f"week_{plan.week_start.strftime('%Y%m%d')}",
                "week_start": plan.week_start.isoformat(),
                "total_entries": len(plan.scheduled_entries),
                "target_companies": plan.target_companies,
                "platforms": [p.value for p in plan.platforms],
                "entries": [
                    {
                        "id": entry.id,
                        "achievement_id": entry.achievement_id,
                        "platform": entry.platform.value,
                        "content_type": entry.content_type.value,
                        "scheduled_time": entry.scheduled_time.isoformat(),
                        "target_company": entry.target_company
                    }
                    for entry in plan.scheduled_entries
                ]
            }
        )
        
    except Exception as e:
        logger.error("schedule_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.get("/schedules", response_model=Dict[str, Any])
async def list_active_schedules() -> Dict[str, Any]:
    """List all active content schedules"""
    try:
        scheduler = get_content_scheduler()
        schedules = []
        
        for plan_id, plan in scheduler.active_schedules.items():
            schedule_info = {
                "plan_id": plan_id,
                "week_start": plan.week_start.isoformat(),
                "target_posts": plan.target_posts,
                "platforms": [p.value for p in plan.platforms],
                "target_companies": plan.target_companies,
                "total_entries": len(plan.scheduled_entries),
                "generated": len([e for e in plan.scheduled_entries if e.status == "generated"]),
                "published": len([e for e in plan.scheduled_entries if e.status == "published"]),
                "failed": len([e for e in plan.scheduled_entries if e.status == "failed"])
            }
            schedules.append(schedule_info)
        
        return {
            "active_schedules": len(schedules),
            "schedules": schedules
        }
        
    except Exception as e:
        logger.error("schedule_listing_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list schedules: {str(e)}")


@router.post("/schedules/{plan_id}/process", response_model=ScheduleResponse)
async def process_schedule(plan_id: str) -> ScheduleResponse:
    """
    Process a weekly schedule - generate content for due entries.
    
    This endpoint:
    1. Checks which entries are due for generation
    2. Generates content using achievements + viral optimization
    3. Applies quality gates and engagement prediction
    4. Returns processing results
    """
    try:
        scheduler = get_content_scheduler()
        
        if plan_id not in scheduler.active_schedules:
            raise HTTPException(status_code=404, detail=f"Schedule {plan_id} not found")
        
        # Process the schedule
        results = await scheduler.process_weekly_schedule(plan_id)
        
        logger.info("schedule_processed_via_api",
                   plan_id=plan_id,
                   results=results)
        
        return ScheduleResponse(
            success=True,
            message=f"Processed {results['processed']} entries: {results['successful']} successful, {results['failed']} failed",
            data=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("schedule_processing_failed", plan_id=plan_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process schedule: {str(e)}")


@router.get("/schedules/upcoming", response_model=List[ContentPreview])
async def get_upcoming_content(
    days: int = Query(7, ge=1, le=30, description="Number of days to look ahead")
) -> List[ContentPreview]:
    """Get upcoming scheduled content entries with previews"""
    try:
        scheduler = get_content_scheduler()
        upcoming_entries = await scheduler.get_upcoming_content(days)
        
        previews = []
        for entry in upcoming_entries:
            if entry.generated_content:
                preview = ContentPreview(
                    entry_id=entry.id,
                    achievement_id=entry.achievement_id,
                    platform=entry.platform,
                    content_type=entry.content_type,
                    target_company=entry.target_company,
                    title=entry.generated_content.title,
                    content_preview=entry.generated_content.content[:200] + "..." if len(entry.generated_content.content) > 200 else entry.generated_content.content,
                    engagement_score=entry.generated_content.engagement_score,
                    quality_score=entry.generated_content.quality_score,
                    scheduled_time=entry.scheduled_time,
                    hashtags=entry.generated_content.recommended_hashtags
                )
                previews.append(preview)
            else:
                # Entry not generated yet
                preview = ContentPreview(
                    entry_id=entry.id,
                    achievement_id=entry.achievement_id,
                    platform=entry.platform,
                    content_type=entry.content_type,
                    target_company=entry.target_company,
                    title="Content generation pending",
                    content_preview="Content will be generated automatically before scheduled time",
                    engagement_score=0.0,
                    quality_score=0.0,
                    scheduled_time=entry.scheduled_time,
                    hashtags=[]
                )
                previews.append(preview)
        
        return previews
        
    except Exception as e:
        logger.error("upcoming_content_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch upcoming content: {str(e)}")


@router.get("/schedules/{plan_id}/entries/{entry_id}/content", response_model=Dict[str, Any])
async def get_generated_content(plan_id: str, entry_id: str) -> Dict[str, Any]:
    """Get the full generated content for a specific entry"""
    try:
        scheduler = get_content_scheduler()
        
        if plan_id not in scheduler.active_schedules:
            raise HTTPException(status_code=404, detail=f"Schedule {plan_id} not found")
        
        plan = scheduler.active_schedules[plan_id]
        entry = next((e for e in plan.scheduled_entries if e.id == entry_id), None)
        
        if not entry:
            raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
        
        if not entry.generated_content:
            raise HTTPException(status_code=404, detail="Content not generated yet")
        
        return {
            "entry_id": entry.id,
            "achievement_id": entry.achievement_id,
            "platform": entry.platform.value,
            "content_type": entry.content_type.value,
            "target_company": entry.target_company,
            "scheduled_time": entry.scheduled_time.isoformat(),
            "status": entry.status,
            "generated_content": {
                "title": entry.generated_content.title,
                "content": entry.generated_content.content,
                "hook": entry.generated_content.hook,
                "engagement_score": entry.generated_content.engagement_score,
                "quality_score": entry.generated_content.quality_score,
                "recommended_hashtags": entry.generated_content.recommended_hashtags,
                "best_posting_time": entry.generated_content.best_posting_time,
                "seo_keywords": entry.generated_content.seo_keywords
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("content_fetch_failed", plan_id=plan_id, entry_id=entry_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch content: {str(e)}")


@router.get("/analytics/performance", response_model=Dict[str, Any])
async def get_content_performance() -> Dict[str, Any]:
    """
    Get content performance analytics.
    
    Returns:
    - Overall engagement and quality scores
    - Platform-specific performance breakdown
    - Company targeting effectiveness
    - Weekly generation statistics
    """
    try:
        scheduler = get_content_scheduler()
        performance = await scheduler.get_content_performance_summary()
        
        # Add additional insights
        insights = []
        
        if performance["total_generated"] > 0:
            if performance["avg_engagement_score"] > 80:
                insights.append("🎯 Excellent engagement scores - content resonating well with audience")
            elif performance["avg_engagement_score"] > 60:
                insights.append("📈 Good engagement - consider A/B testing different hook styles")
            else:
                insights.append("⚠️ Lower engagement - review content strategy and viral optimization")
            
            # Platform insights
            if "platform_breakdown" in performance:
                best_platform = max(performance["platform_breakdown"].items(), 
                                  key=lambda x: x[1]["avg_engagement"], 
                                  default=(None, {"avg_engagement": 0}))
                if best_platform[0]:
                    insights.append(f"🏆 {best_platform[0]} performing best with {best_platform[1]['avg_engagement']:.1f}% avg engagement")
            
            # Company insights
            if "company_performance" in performance:
                company_count = len(performance["company_performance"])
                insights.append(f"🎯 Targeting {company_count} companies for focused job search approach")
        
        performance["insights"] = insights
        performance["recommendation"] = generate_performance_recommendation(performance)
        
        return performance
        
    except Exception as e:
        logger.error("performance_analytics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get performance analytics: {str(e)}")


@router.post("/schedules/{plan_id}/entries/{entry_id}/regenerate", response_model=ScheduleResponse)
async def regenerate_content(plan_id: str, entry_id: str) -> ScheduleResponse:
    """Regenerate content for a specific entry (useful if quality is low)"""
    try:
        scheduler = get_content_scheduler()
        
        if plan_id not in scheduler.active_schedules:
            raise HTTPException(status_code=404, detail=f"Schedule {plan_id} not found")
        
        plan = scheduler.active_schedules[plan_id]
        entry = next((e for e in plan.scheduled_entries if e.id == entry_id), None)
        
        if not entry:
            raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
        
        # Reset entry status and regenerate
        entry.status = "scheduled"
        entry.generated_content = None
        
        success = await scheduler.generate_scheduled_content(entry)
        
        if success:
            return ScheduleResponse(
                success=True,
                message="Content regenerated successfully",
                data={
                    "entry_id": entry.id,
                    "new_engagement_score": entry.generated_content.engagement_score if entry.generated_content else None,
                    "new_quality_score": entry.generated_content.quality_score if entry.generated_content else None
                }
            )
        else:
            return ScheduleResponse(
                success=False,
                message="Content regeneration failed",
                data={"entry_id": entry.id, "status": entry.status}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("content_regeneration_failed", plan_id=plan_id, entry_id=entry_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to regenerate content: {str(e)}")


async def schedule_auto_processing(plan_id: str):
    """Background task to automatically process schedules"""
    try:
        # Wait for the scheduled time and then process
        scheduler = get_content_scheduler()
        
        # For now, process immediately in background
        # In production, this would use a job queue like Celery
        await asyncio.sleep(1)  # Small delay to let request complete
        
        results = await scheduler.process_weekly_schedule(plan_id)
        
        logger.info("auto_processing_completed", 
                   plan_id=plan_id, 
                   results=results)
        
    except Exception as e:
        logger.error("auto_processing_failed", plan_id=plan_id, error=str(e))


def generate_performance_recommendation(performance: Dict[str, Any]) -> str:
    """Generate actionable recommendations based on performance data"""
    if performance["total_generated"] == 0:
        return "Start by creating your first weekly content schedule to begin building your professional presence."
    
    avg_engagement = performance.get("avg_engagement_score", 0)
    avg_quality = performance.get("avg_quality_score", 0)
    
    if avg_engagement > 80 and avg_quality > 80:
        return "Excellent performance! Consider expanding to additional platforms and increasing posting frequency."
    elif avg_engagement > 60 and avg_quality > 70:
        return "Good performance. Focus on improving hook quality and experimenting with viral patterns."
    elif avg_engagement < 50 or avg_quality < 60:
        return "Performance needs improvement. Review content strategy, ensure strong achievement selection, and optimize for target companies."
    else:
        return "Steady progress. Continue current strategy while testing new content formats and company targeting."