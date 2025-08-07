# Achievement CRUD Routes

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from services.achievement_collector.api.schemas import (
    Achievement,
    AchievementCreate,
    AchievementList,
    AchievementUpdate,
    PRAchievement,
    ComprehensiveAnalysisResult,
)
from services.achievement_collector.core.logging import setup_logging
from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import (
    Achievement as AchievementModel,
    PRAchievement as PRAchievementModel,
)
from services.achievement_collector.services.db_operations import (
    create_achievement_from_pr,
    update_achievement_with_stories,
    get_achievement_by_pr,
)
from services.achievement_collector.utils.calculation_metadata import (
    CalculationMetadata,
)

logger = setup_logging(__name__)
router = APIRouter()


def create_achievement_sync(
    db: Session, achievement: AchievementCreate
) -> AchievementModel:
    """Create a new achievement (synchronous version for internal use)"""
    # Calculate duration
    duration = (
        achievement.completed_at - achievement.started_at
    ).total_seconds() / 3600

    # Enhance metrics with calculation metadata if present
    enhanced_metrics = {}
    if achievement.metrics_after:
        # Enhance business metrics with calculation transparency
        business_enhanced = CalculationMetadata.enhance_business_metrics(
            achievement.metrics_after
        )
        performance_enhanced = CalculationMetadata.enhance_performance_metrics(
            achievement.metrics_after
        )

        # Combine enhanced metrics with original data
        enhanced_metrics = {
            **achievement.metrics_after,
            "enhanced_calculations": {**business_enhanced, **performance_enhanced},
            "calculation_summary": CalculationMetadata.create_calculation_summary(
                {**business_enhanced, **performance_enhanced}
            ),
        }

    # Enhance metadata with calculation version
    enhanced_metadata = getattr(achievement, "metadata", {}) or {}
    enhanced_metadata["calculation_version"] = CalculationMetadata.CALCULATION_VERSION
    enhanced_metadata["enhanced_at"] = datetime.now().isoformat()

    # Create achievement with enhanced data
    achievement_data = achievement.model_dump()
    achievement_data["metrics_after"] = enhanced_metrics or achievement.metrics_after
    achievement_data["metadata_json"] = (
        enhanced_metadata  # Use correct field name from model
    )

    db_achievement = AchievementModel(
        **achievement_data,
        duration_hours=duration,
    )
    db.add(db_achievement)
    db.commit()
    db.refresh(db_achievement)

    logger.info(
        f"Created achievement with enhanced metrics: {db_achievement.id} - {db_achievement.title}"
    )
    return db_achievement


@router.post("/", response_model=Achievement)
async def create_achievement(
    achievement: AchievementCreate,
    db: Session = Depends(get_db),
):
    """Create a new achievement with calculation transparency"""
    # Use the enhanced sync function for consistency
    return create_achievement_sync(db, achievement)


@router.get("/", response_model=AchievementList)
async def list_achievements(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    portfolio_ready: Optional[bool] = None,
    min_impact_score: Optional[float] = Query(None, ge=0, le=100),
    search: Optional[str] = None,
    sort_by: str = Query(
        "completed_at", pattern="^(completed_at|impact_score|business_value)$"
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """List achievements with filtering and pagination"""

    # Base query
    query = db.query(AchievementModel)

    # Apply filters
    if category:
        query = query.filter(AchievementModel.category == category)

    if portfolio_ready is not None:
        query = query.filter(AchievementModel.portfolio_ready == portfolio_ready)

    if min_impact_score is not None:
        query = query.filter(AchievementModel.impact_score >= min_impact_score)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (AchievementModel.title.ilike(search_pattern))
            | (AchievementModel.description.ilike(search_pattern))
        )

    # Count total
    total = query.count()

    # Apply sorting
    sort_column = getattr(AchievementModel, sort_by)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    # Pagination
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()

    # Calculate pages
    pages = (total + per_page - 1) // per_page

    # Convert SQLAlchemy models to dict for pydantic
    items_dict = []
    for item in items:
        # Handle all potential None values with proper defaults
        item_dict = {
            "id": item.id,
            "title": item.title or "",
            "description": item.description or "",
            "category": item.category or "development",
            "started_at": item.started_at or datetime.now(),
            "completed_at": item.completed_at or datetime.now(),
            "duration_hours": item.duration_hours or 0.0,
            "source_type": item.source_type or "manual",
            "source_id": item.source_id,
            "source_url": item.source_url,
            "tags": item.tags if item.tags is not None else [],
            "skills_demonstrated": item.skills_demonstrated
            if item.skills_demonstrated is not None
            else [],
            "impact_score": item.impact_score if item.impact_score is not None else 0.0,
            "complexity_score": item.complexity_score
            if item.complexity_score is not None
            else 0.0,
            "business_value": item.business_value,
            "time_saved_hours": item.time_saved_hours
            if item.time_saved_hours is not None
            else 0.0,
            "performance_improvement_pct": item.performance_improvement_pct
            if item.performance_improvement_pct is not None
            else 0.0,
            "evidence": item.evidence if item.evidence is not None else {},
            "metrics_before": item.metrics_before
            if item.metrics_before is not None
            else {},
            "metrics_after": item.metrics_after
            if item.metrics_after is not None
            else {},
            "ai_summary": item.ai_summary,
            "ai_impact_analysis": item.ai_impact_analysis,
            "ai_technical_analysis": item.ai_technical_analysis,
            "portfolio_ready": item.portfolio_ready
            if item.portfolio_ready is not None
            else False,
            "portfolio_section": item.portfolio_section,
            "display_priority": item.display_priority
            if item.display_priority is not None
            else 50,
            "created_at": item.created_at
            if item.created_at is not None
            else datetime.now(),
            "updated_at": item.updated_at
            if item.updated_at is not None
            else datetime.now(),
        }
        items_dict.append(item_dict)

    return AchievementList(
        items=items_dict,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{achievement_id}", response_model=Achievement)
async def get_achievement(
    achievement_id: int,
    db: Session = Depends(get_db),
):
    """Get specific achievement"""

    achievement = (
        db.query(AchievementModel).filter(AchievementModel.id == achievement_id).first()
    )

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    return achievement


@router.put("/{achievement_id}", response_model=Achievement)
async def update_achievement(
    achievement_id: int,
    update: AchievementUpdate,
    db: Session = Depends(get_db),
):
    """Update achievement"""

    achievement = (
        db.query(AchievementModel).filter(AchievementModel.id == achievement_id).first()
    )

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(achievement, field, value)

    db.commit()
    db.refresh(achievement)

    logger.info(f"Updated achievement: {achievement.id}")

    return achievement


@router.delete("/{achievement_id}")
async def delete_achievement(
    achievement_id: int,
    db: Session = Depends(get_db),
):
    """Delete achievement"""

    achievement = (
        db.query(AchievementModel).filter(AchievementModel.id == achievement_id).first()
    )

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    db.delete(achievement)
    db.commit()

    logger.info(f"Deleted achievement: {achievement_id}")

    return {"status": "deleted", "id": achievement_id}


@router.get("/stats/summary")
async def get_achievement_stats(
    db: Session = Depends(get_db),
):
    """Get achievement statistics"""

    stats = db.query(
        func.count(AchievementModel.id).label("total_achievements"),
        func.sum(AchievementModel.business_value).label("total_value"),
        func.sum(AchievementModel.time_saved_hours).label("total_time_saved"),
        func.avg(AchievementModel.impact_score).label("avg_impact_score"),
        func.avg(AchievementModel.complexity_score).label("avg_complexity_score"),
    ).first()

    category_stats = (
        db.query(
            AchievementModel.category,
            func.count(AchievementModel.id).label("count"),
        )
        .group_by(AchievementModel.category)
        .all()
    )

    return {
        "total_achievements": stats.total_achievements or 0,
        "total_value_generated": float(stats.total_value or 0),
        "total_time_saved_hours": float(stats.total_time_saved or 0),
        "average_impact_score": float(stats.avg_impact_score or 0),
        "average_complexity_score": float(stats.avg_complexity_score or 0),
        "by_category": {cat: count for cat, count in category_stats},
    }


@router.get("/{achievement_id}/calculation-transparency")
async def get_calculation_transparency(
    achievement_id: int, db: Session = Depends(get_db)
):
    """Get calculation transparency details for an achievement."""
    achievement = (
        db.query(AchievementModel).filter(AchievementModel.id == achievement_id).first()
    )

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # Extract calculation metadata
    metrics_after = achievement.metrics_after or {}
    enhanced_calculations = metrics_after.get("enhanced_calculations", {})
    calculation_summary = metrics_after.get("calculation_summary", {})
    metadata = achievement.metadata or {}

    return {
        "achievement_id": achievement_id,
        "calculation_version": metadata.get("calculation_version", "unknown"),
        "enhanced_at": metadata.get("enhanced_at"),
        "enhanced_calculations": enhanced_calculations,
        "calculation_summary": calculation_summary,
        "formulas_used": calculation_summary.get("formulas_used", []),
        "confidence_scores": calculation_summary.get("confidence_scores", {}),
        "methodology_notes": calculation_summary.get("methodology_notes", []),
    }


# PR-specific endpoints


@router.post("/pr/{pr_number}", response_model=Achievement)
async def create_pr_achievement(
    pr_number: int,
    pr_data: dict,
    analysis: ComprehensiveAnalysisResult,
    db: Session = Depends(get_db),
):
    """Create achievement from PR analysis"""

    # Check if achievement already exists for this PR
    existing = get_achievement_by_pr(db, pr_number)
    if existing:
        logger.info(f"Achievement already exists for PR #{pr_number}")
        return existing

    # Create achievement from PR data
    achievement = create_achievement_from_pr(db, pr_data, analysis.model_dump())

    logger.info(f"Created PR achievement: {achievement.id} for PR #{pr_number}")
    return achievement


@router.get("/pr/{pr_number}", response_model=Achievement)
async def get_pr_achievement(
    pr_number: int,
    db: Session = Depends(get_db),
):
    """Get achievement by PR number"""

    achievement = get_achievement_by_pr(db, pr_number)
    if not achievement:
        raise HTTPException(
            status_code=404, detail=f"No achievement found for PR #{pr_number}"
        )

    return achievement


@router.put("/pr/{pr_number}/stories")
async def update_pr_stories(
    pr_number: int,
    stories: dict,
    db: Session = Depends(get_db),
):
    """Update PR achievement with generated stories"""

    achievement = get_achievement_by_pr(db, pr_number)
    if not achievement:
        raise HTTPException(
            status_code=404, detail=f"No achievement found for PR #{pr_number}"
        )

    # Update with stories
    updated = update_achievement_with_stories(db, achievement.id, stories)

    return {
        "status": "updated",
        "achievement_id": updated.id,
        "stories_count": len(stories),
    }


@router.get("/pr/{pr_number}/details", response_model=PRAchievement)
async def get_pr_achievement_details(
    pr_number: int,
    db: Session = Depends(get_db),
):
    """Get detailed PR achievement data"""

    pr_achievement = (
        db.query(PRAchievementModel)
        .filter(PRAchievementModel.pr_number == pr_number)
        .first()
    )

    if not pr_achievement:
        raise HTTPException(
            status_code=404, detail=f"No PR achievement found for PR #{pr_number}"
        )

    return pr_achievement


@router.get("/source/github_pr")
async def list_pr_achievements(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all PR-based achievements"""

    query = db.query(AchievementModel).filter(
        AchievementModel.source_type == "github_pr"
    )

    # Count total
    total = query.count()

    # Sort by completion date
    query = query.order_by(desc(AchievementModel.completed_at))

    # Pagination
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()

    # Calculate pages
    pages = (total + per_page - 1) // per_page

    return AchievementList(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )
