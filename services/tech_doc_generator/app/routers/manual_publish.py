"""API endpoints for manual publishing workflow"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.article import ArticleContent
from app.services.manual_publisher import ManualPublishingTracker, LinkedInManualWorkflow
from app.models.article import Platform

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
            "Post Tuesday-Thursday, 8-10 AM or 5-6 PM (your timezone)"
        ]
    }


@router.post("/confirm/{draft_id}")
async def confirm_manual_post(
    draft_id: str,
    request: ConfirmPostRequest,
    db: Session = Depends(get_db)
):
    """Confirm that content was manually posted"""
    tracker = ManualPublishingTracker(db)
    
    try:
        result = await tracker.confirm_manual_post(
            draft_id=draft_id,
            post_url=request.post_url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analytics/{draft_id}")
async def upload_analytics(
    draft_id: str,
    request: AnalyticsUploadRequest,
    db: Session = Depends(get_db)
):
    """Upload manual analytics for a post"""
    tracker = ManualPublishingTracker(db)
    
    try:
        result = await tracker.upload_analytics(
            draft_id=draft_id,
            analytics_data=request.metrics
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analytics/{draft_id}/screenshot")
async def upload_analytics_screenshot(
    draft_id: str,
    screenshot: UploadFile = File(...),
    db: Session = Depends(get_db)
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
        "size": screenshot.size
    }


@router.get("/drafts")
async def list_drafts(
    platform: Optional[Platform] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
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
                "title": "How I Built an AI System That Measures Developer Impact"
            }
        ],
        "total": 1,
        "filters": {
            "platform": platform.value if platform else None,
            "status": status
        }
    }


@router.get("/drafts/{draft_id}")
async def get_draft_details(
    draft_id: str,
    db: Session = Depends(get_db)
):
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
            type('obj', (object,), {
                'title': 'Example Post',
                'content': 'Example content...',
                'insights': ['Insight 1', 'Insight 2'],
                'tags': ['python', 'ai']
            })()
        ),
        "instructions": [
            "Copy the content above",
            "Post to LinkedIn",
            "Return here to confirm posting"
        ]
    }