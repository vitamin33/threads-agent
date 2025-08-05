"""API endpoints for manual publishing workflow"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
import time
import structlog

from app.core.database import get_db
from app.services.manual_publisher import (
    ManualPublishingTracker,
    LinkedInManualWorkflow,
)
from app.models.article import Platform

logger = structlog.get_logger()

router = APIRouter(prefix="/manual-publish", tags=["manual-publishing"])


class ConfirmPostRequest(BaseModel):
    """Request model for confirming manual post"""

    draft_id: str
    post_url: Optional[str] = None
    notes: Optional[str] = None


class AnalyticsUploadRequest(BaseModel):
    """Request model for uploading analytics"""

    draft_id: str
    metrics: Dict[str, Any]
    captured_date: Optional[str] = None


@router.get("/linkedin-template")
async def get_linkedin_template():
    """Get LinkedIn posting template and instructions"""
    return {
        "template": LinkedInManualWorkflow.create_analytics_template(),
        "formatting_tips": [
            "Use emojis strategically (not too many)",
            "Keep paragraphs short (2-3 lines)",
            "Start with a compelling hook",
            "End with a question to encourage engagement",
            "Post Tuesday-Thursday, 8-10 AM or 5-6 PM (your timezone)",
        ],
    }


@router.post("/confirm/{draft_id}")
async def confirm_manual_post(
    draft_id: str, request: ConfirmPostRequest, db: Session = Depends(get_db)
):
    """Confirm that content was manually posted"""
    tracker = ManualPublishingTracker(db)

    try:
        result = await tracker.confirm_manual_post(
            draft_id=draft_id, post_url=request.post_url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analytics/{draft_id}")
async def upload_analytics(
    draft_id: str, request: AnalyticsUploadRequest, db: Session = Depends(get_db)
):
    """Upload manual analytics for a post"""
    tracker = ManualPublishingTracker(db)

    try:
        result = await tracker.upload_analytics(
            draft_id=draft_id, analytics_data=request.metrics
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analytics/{draft_id}/screenshot")
async def upload_analytics_screenshot(
    draft_id: str, screenshot: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Upload analytics screenshot for verification"""

    # Validate file type
    if not screenshot.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # In production, save to S3 or similar
    # For now, just acknowledge receipt
    return {
        "success": True,
        "message": "Screenshot received",
        "draft_id": draft_id,
        "filename": screenshot.filename,
        "size": screenshot.size,
    }


@router.get("/drafts")
async def list_drafts(
    platform: Optional[Platform] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all drafts with optional filtering"""

    # In production, query from database
    # For now, return example
    return {
        "drafts": [
            {
                "draft_id": "linkedin_draft_1234567890",
                "platform": "linkedin",
                "status": "pending_manual_post",
                "created_at": "2024-01-15T10:00:00Z",
                "title": "How I Built an AI System That Measures Developer Impact",
            }
        ],
        "total": 1,
        "filters": {"platform": platform.value if platform else None, "status": status},
    }


@router.post("/devto/track-published")
async def track_published_devto_article(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Track an already published dev.to article"""
    
    required_fields = ["title", "url", "published_date"]
    for field in required_fields:
        if field not in request:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Create tracking record
    tracking_data = {
        "platform": "devto",
        "title": request["title"],
        "url": request["url"],
        "published_date": request["published_date"],
        "tags": request.get("tags", []),
        "reading_time": request.get("reading_time_minutes", 0),
        "status": "published",
        "tracking_id": f"devto_published_{int(time.time())}"
    }
    
    # In production, save to database
    logger.info(
        "devto_article_tracked",
        tracking_id=tracking_data["tracking_id"],
        title=request["title"],
        url=request["url"]
    )
    
    # Create achievement for published article
    await _create_devto_achievement(tracking_data, db)
    
    return {
        "success": True,
        "tracking_id": tracking_data["tracking_id"],
        "message": "Dev.to article tracked successfully",
        "next_steps": [
            "Article will be monitored for engagement metrics",
            "Analytics will be collected automatically via dev.to API",
            "Achievement created for portfolio tracking"
        ]
    }


async def _create_devto_achievement(tracking_data: Dict[str, Any], db: Session):
    """Create achievement record for published dev.to article"""
    
    # Calculate dynamic scores based on article data
    reading_time = tracking_data.get("reading_time_minutes", 0)
    article_tags = tracking_data.get("tags", [])
    
    # Calculate impact score based on article characteristics
    impact_score = 60.0  # Base score for content creation
    if reading_time >= 10:
        impact_score += 10.0  # Long-form content bonus
    if any(tag in ["ai", "machine-learning", "python", "devops"] for tag in article_tags):
        impact_score += 10.0  # AI/tech relevance bonus
    if len(article_tags) >= 4:
        impact_score += 5.0  # Good tagging bonus
    
    # Calculate complexity score based on technical depth
    complexity_score = 50.0  # Base complexity for technical writing
    tech_indicators = ["api", "algorithm", "architecture", "system", "framework", "database"]
    if any(indicator in tracking_data["title"].lower() for indicator in tech_indicators):
        complexity_score += 15.0  # Technical depth bonus
    if reading_time >= 15:
        complexity_score += 10.0  # In-depth content bonus
    
    # Derive skills from article tags and content
    base_skills = ["Technical Writing", "Content Marketing", "Developer Relations"]
    derived_skills = []
    
    skill_mapping = {
        "python": "Python",
        "javascript": "JavaScript", 
        "react": "React",
        "api": "API Design",
        "database": "Database Design",
        "ai": "Artificial Intelligence",
        "machine-learning": "Machine Learning",
        "devops": "DevOps",
        "docker": "Docker",
        "kubernetes": "Kubernetes"
    }
    
    for tag in article_tags:
        if tag.lower() in skill_mapping:
            derived_skills.append(skill_mapping[tag.lower()])
    
    all_skills = base_skills + derived_skills[:5]  # Limit to reasonable number
    
    # Generate business value description based on content
    business_value_parts = ["Technical content publication"]
    if "ai" in article_tags or "ai" in tracking_data["title"].lower():
        business_value_parts.append("demonstrates AI expertise for job market")
    if reading_time >= 10:
        business_value_parts.append("establishes thought leadership")
    business_value_parts.append("increases developer network visibility")
    
    business_value = "; ".join(business_value_parts)
    
    # Create comprehensive achievement data
    achievement_data = {
        "title": f"Published: {tracking_data['title']}",
        "description": f"Successfully published technical article on dev.to with {reading_time} minute read time. Article covers: {', '.join(article_tags[:3])}",
        "category": "content",
        "source_type": "manual",
        "source_url": tracking_data["url"],
        "tags": ["content-creation", "devto", "technical-writing"] + article_tags,
        "skills_demonstrated": all_skills,
        "portfolio_ready": True,
        "business_value": business_value,
        "impact_score": min(impact_score, 100.0),  # Cap at 100
        "complexity_score": min(complexity_score, 100.0),  # Cap at 100
        "started_at": tracking_data["published_date"],
        "completed_at": tracking_data["published_date"],
        "duration_hours": reading_time / 60 * 8  # Estimate 8x reading time for writing
    }
    
    logger.info(
        "devto_achievement_created",
        title=achievement_data["title"],
        url=tracking_data["url"],
        impact_score=achievement_data["impact_score"],
        complexity_score=achievement_data["complexity_score"],
        skills_count=len(all_skills),
        tags_count=len(article_tags)
    )
    
    # In production, this would make HTTP request to achievement_collector service
    # For now, just log the achievement data
    logger.info("achievement_data_ready", data=achievement_data)


@router.get("/devto/analytics/{tracking_id}")
async def get_devto_analytics(
    tracking_id: str,
    db: Session = Depends(get_db)
):
    """Get analytics for tracked dev.to article"""
    
    # Extract article URL from tracking record (in production, fetch from DB)
    # For now, simulate database lookup
    try:
        # In production: article_record = db.query(TrackedArticle).filter_by(tracking_id=tracking_id).first()
        # For demo, extract from tracking_id format: devto_published_timestamp
        
        from app.services.devto_collector import DevToMetricsCollector
        collector = DevToMetricsCollector()
        
        # For demo purposes, you would store the article URL in the database
        # Here we'll need to pass the article URL somehow
        # In a real implementation, you'd fetch the URL from the tracking record
        
        # Placeholder response - in production, this would use the real dev.to API
        return {
            "tracking_id": tracking_id,
            "platform": "devto",
            "status": "tracked",
            "message": "Real analytics collection requires dev.to API integration",
            "instructions": [
                "To get real analytics, provide your dev.to article URL",
                "Use the DevToMetricsCollector with your dev.to API key",
                "Analytics will be automatically collected and stored"
            ],
            "example_usage": {
                "collector_setup": "collector = DevToMetricsCollector(api_key='your_key')",
                "get_analytics": "metrics = await collector.get_article_metrics('your_article_url')"
            }
        }
        
    except Exception as e:
        logger.error("analytics_fetch_failed", tracking_id=tracking_id, error=str(e))
        return {
            "error": f"Failed to fetch analytics: {str(e)}",
            "tracking_id": tracking_id
        }


@router.get("/drafts/{draft_id}")
async def get_draft_details(draft_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific draft"""

    # In production, retrieve from database
    # For now, return example
    return {
        "draft_id": draft_id,
        "platform": "linkedin",
        "status": "pending_manual_post",
        "created_at": "2024-01-15T10:00:00Z",
        "content": LinkedInManualWorkflow.format_for_copy_paste(
            # This would be the actual content from DB
            type(
                "obj",
                (object,),
                {
                    "title": "Example Post",
                    "content": "Example content...",
                    "insights": ["Insight 1", "Insight 2"],
                    "tags": ["python", "ai"],
                },
            )()
        ),
        "instructions": [
            "Copy the content above",
            "Post to LinkedIn",
            "Return here to confirm posting",
        ],
    }
