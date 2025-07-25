# Achievement CRUD Routes

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from services.achievement_collector.api.schemas import (
    Achievement,
    AchievementCreate,
    AchievementList,
    AchievementUpdate,
)
from services.achievement_collector.core.logging import setup_logging
from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Achievement as AchievementModel

logger = setup_logging(__name__)
router = APIRouter()


@router.post("/", response_model=Achievement)
async def create_achievement(
    achievement: AchievementCreate,
    db: Session = Depends(get_db),
):
    """Create a new achievement"""

    # Calculate duration
    duration = (
        achievement.completed_at - achievement.started_at
    ).total_seconds() / 3600

    # Create achievement
    achievement_data = achievement.model_dump(exclude={"duration_hours"})
    db_achievement = AchievementModel(
        **achievement_data,
        duration_hours=duration,
    )

    db.add(db_achievement)
    db.commit()
    db.refresh(db_achievement)

    logger.info(f"Created achievement: {db_achievement.id} - {db_achievement.title}")

    return db_achievement


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

    return AchievementList(
        items=items,
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
