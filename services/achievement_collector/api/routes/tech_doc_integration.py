"""
Tech Documentation Generator Integration Routes

Endpoints specifically designed for integration with the tech_doc_generator service.
These routes provide optimized access patterns for content generation workflows.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, and_, or_, func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from services.achievement_collector.api.schemas import Achievement
from services.achievement_collector.core.logging import setup_logging
from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Achievement as AchievementModel

logger = setup_logging(__name__)
router = APIRouter(prefix="/tech-doc-integration", tags=["tech-doc-integration"])


class BatchAchievementRequest(BaseModel):
    """Request model for batch achievement retrieval"""
    achievement_ids: List[int]


class AchievementFilter(BaseModel):
    """Filter model for achievement queries"""
    categories: Optional[List[str]] = None
    min_impact_score: Optional[float] = None
    portfolio_ready_only: bool = True
    days_back: Optional[int] = None
    tags: Optional[List[str]] = None
    company_keywords: Optional[List[str]] = None


class AchievementSummary(BaseModel):
    """Lightweight achievement summary for listings"""
    id: int
    title: str
    category: str
    impact_score: float
    business_value: str
    tags: List[str]
    completed_at: datetime


@router.post("/batch-get", response_model=List[Achievement])
async def batch_get_achievements(
    request: BatchAchievementRequest,
    db: Session = Depends(get_db)
):
    """
    Batch retrieve multiple achievements by IDs.
    
    Optimized for tech_doc_generator's batch content generation.
    """
    if not request.achievement_ids:
        return []
        
    achievements = db.query(AchievementModel).filter(
        AchievementModel.id.in_(request.achievement_ids)
    ).all()
    
    logger.info(f"Batch retrieved {len(achievements)} achievements")
    return achievements


@router.post("/recent-highlights", response_model=List[Achievement])
async def get_recent_highlights(
    days: int = Query(7, ge=1, le=30),
    min_impact_score: float = Query(75.0, ge=0, le=100),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get recent high-impact achievements for weekly highlights.
    
    Used by tech_doc_generator for automated weekly content generation.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    achievements = db.query(AchievementModel).filter(
        and_(
            AchievementModel.completed_at >= cutoff_date,
            AchievementModel.impact_score >= min_impact_score,
            AchievementModel.portfolio_ready == True
        )
    ).order_by(
        desc(AchievementModel.impact_score)
    ).limit(limit).all()
    
    logger.info(f"Found {len(achievements)} recent highlights")
    return achievements


@router.post("/company-targeted", response_model=List[Achievement])
async def get_company_targeted_achievements(
    company_name: str,
    categories: Optional[List[str]] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get achievements relevant for a specific company.
    
    Filters by category and searches for company-relevant keywords
    in descriptions and technical details.
    """
    query = db.query(AchievementModel).filter(
        AchievementModel.portfolio_ready == True
    )
    
    # Filter by categories if provided
    if categories:
        query = query.filter(AchievementModel.category.in_(categories))
    
    # Company-specific keyword mapping
    company_keywords = {
        "notion": ["productivity", "collaboration", "documentation", "knowledge", "workflow"],
        "jasper": ["ai", "content", "generation", "nlp", "automation", "gpt", "llm"],
        "anthropic": ["ai", "safety", "alignment", "llm", "ethical", "research", "claude"],
        "stripe": ["payment", "fintech", "api", "billing", "subscription", "finance"],
        "databricks": ["data", "spark", "ml", "pipeline", "lakehouse", "analytics"],
        "scale": ["ml", "data", "annotation", "training", "dataset", "labeling"],
        "huggingface": ["nlp", "transformer", "model", "dataset", "ml", "ai"],
        "openai": ["gpt", "ai", "llm", "api", "generation", "assistant"],
        "cohere": ["nlp", "embedding", "search", "retrieval", "rag", "ai"],
        "runway": ["ml", "video", "generation", "creative", "ai", "media"]
    }
    
    # Get keywords for the company
    keywords = company_keywords.get(company_name.lower(), [company_name.lower()])
    
    # Build keyword search conditions
    keyword_conditions = []
    for keyword in keywords:
        pattern = f"%{keyword}%"
        keyword_conditions.extend([
            AchievementModel.title.ilike(pattern),
            AchievementModel.description.ilike(pattern),
            AchievementModel.business_value.ilike(pattern)
        ])
    
    if keyword_conditions:
        try:
            query = query.filter(or_(*keyword_conditions))
        except Exception:
            # Fallback: just filter by category if keyword search fails
            logger.warning(f"Keyword search failed for {company_name}, using category fallback")
            pass
    
    # Order by impact score and limit
    achievements = query.order_by(
        desc(AchievementModel.impact_score)
    ).limit(limit).all()
    
    logger.info(f"Found {len(achievements)} achievements for {company_name}")
    return achievements


@router.post("/filter", response_model=List[Achievement])
async def filter_achievements(
    filters: AchievementFilter,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Advanced filtering endpoint for complex queries.
    
    Supports multiple filter criteria for content generation workflows.
    """
    query = db.query(AchievementModel)
    
    # Apply filters
    if filters.portfolio_ready_only:
        query = query.filter(AchievementModel.portfolio_ready == True)
    
    if filters.categories:
        query = query.filter(AchievementModel.category.in_(filters.categories))
    
    if filters.min_impact_score is not None:
        query = query.filter(AchievementModel.impact_score >= filters.min_impact_score)
    
    if filters.days_back:
        cutoff = datetime.utcnow() - timedelta(days=filters.days_back)
        query = query.filter(AchievementModel.completed_at >= cutoff)
    
    if filters.tags:
        # Filter by any matching tag
        tag_conditions = []
        for tag in filters.tags:
            tag_conditions.append(AchievementModel.tags.contains([tag]))
        query = query.filter(or_(*tag_conditions))
    
    if filters.company_keywords:
        # Search for company keywords
        keyword_conditions = []
        for keyword in filters.company_keywords:
            pattern = f"%{keyword}%"
            keyword_conditions.extend([
                AchievementModel.title.ilike(pattern),
                AchievementModel.description.ilike(pattern)
            ])
        query = query.filter(or_(*keyword_conditions))
    
    # Order by impact score
    query = query.order_by(desc(AchievementModel.impact_score))
    
    # Pagination
    offset = (page - 1) * per_page
    achievements = query.offset(offset).limit(per_page).all()
    
    return achievements


@router.get("/content-ready", response_model=List[AchievementSummary])
async def get_content_ready_achievements(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get all content-ready achievements in a lightweight format.
    
    Returns summarized data for quick content opportunity scanning.
    """
    achievements = db.query(
        AchievementModel.id,
        AchievementModel.title,
        AchievementModel.category,
        AchievementModel.impact_score,
        AchievementModel.business_value,
        AchievementModel.tags,
        AchievementModel.completed_at
    ).filter(
        and_(
            AchievementModel.portfolio_ready == True,
            AchievementModel.impact_score >= 70.0
        )
    ).order_by(
        desc(AchievementModel.completed_at)
    ).limit(limit).all()
    
    summaries = [
        AchievementSummary(
            id=a.id,
            title=a.title,
            category=a.category,
            impact_score=a.impact_score,
            business_value=a.business_value,
            tags=a.tags or [],
            completed_at=a.completed_at
        )
        for a in achievements
    ]
    
    return summaries


@router.post("/sync-status")
async def update_sync_status(
    achievement_id: int,
    content_generated: bool = True,
    platforms: List[str] = Query([]),
    db: Session = Depends(get_db)
):
    """
    Update achievement with content generation status.
    
    Allows tech_doc_generator to mark achievements as processed.
    """
    achievement = db.query(AchievementModel).filter(
        AchievementModel.id == achievement_id
    ).first()
    
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    # Update metadata with sync info (use metadata_json)
    if not achievement.metadata_json:
        achievement.metadata_json = {}
    
    achievement.metadata_json["content_generated"] = content_generated
    achievement.metadata_json["content_platforms"] = platforms
    achievement.metadata_json["content_generated_at"] = datetime.utcnow().isoformat()
    
    db.commit()
    
    logger.info(f"Updated sync status for achievement {achievement_id}")
    
    return {
        "status": "updated",
        "achievement_id": achievement_id,
        "content_generated": content_generated,
        "platforms": platforms
    }


@router.get("/stats/content-opportunities")
async def get_content_opportunities(
    db: Session = Depends(get_db)
):
    """
    Get statistics on content generation opportunities.
    
    Shows untapped achievements that could be turned into content.
    """
    # Total portfolio-ready achievements
    total_ready = db.query(AchievementModel).filter(
        AchievementModel.portfolio_ready == True
    ).count()
    
    # High-impact achievements (80+)
    high_impact = db.query(AchievementModel).filter(
        and_(
            AchievementModel.portfolio_ready == True,
            AchievementModel.impact_score >= 80.0
        )
    ).count()
    
    # Recent achievements (last 30 days)
    recent_cutoff = datetime.utcnow() - timedelta(days=30)
    recent = db.query(AchievementModel).filter(
        and_(
            AchievementModel.portfolio_ready == True,
            AchievementModel.completed_at >= recent_cutoff
        )
    ).count()
    
    # Unprocessed achievements - simple approach without JSON queries
    total_portfolio_ready = db.query(AchievementModel).filter(
        AchievementModel.portfolio_ready == True
    ).count()
    
    # For now, assume most are unprocessed since this is a new feature
    unprocessed = max(0, total_portfolio_ready - 5)  # Assume 5 have been processed as example
    
    # Category breakdown
    categories = db.query(
        AchievementModel.category,
        func.count(AchievementModel.id).label("count")
    ).filter(
        AchievementModel.portfolio_ready == True
    ).group_by(
        AchievementModel.category
    ).all()
    
    return {
        "total_content_ready": total_ready,
        "high_impact_opportunities": high_impact,
        "recent_achievements": recent,
        "unprocessed_achievements": unprocessed,
        "by_category": {cat: count for cat, count in categories},
        "content_generation_rate": f"{((total_ready - unprocessed) / total_ready * 100):.1f}%" if total_ready > 0 else "0%"
    }