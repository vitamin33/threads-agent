# Portfolio Generation Routes

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from services.achievement_collector.api.schemas import (
    PortfolioRequest,
    PortfolioResponse,
)
from services.achievement_collector.core.config import settings
from services.achievement_collector.core.logging import setup_logging
from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Achievement, PortfolioSnapshot
from services.achievement_collector.services.portfolio_generator import (
    PortfolioGenerator,
)

logger = setup_logging(__name__)
router = APIRouter()

# Initialize portfolio generator
generator = PortfolioGenerator(output_dir=settings.PORTFOLIO_OUTPUT_DIR)


@router.post("/generate", response_model=PortfolioResponse)
async def generate_portfolio(
    request: PortfolioRequest,
    db: Session = Depends(get_db),
):
    """Generate portfolio document"""

    # Build query for achievements
    query = db.query(Achievement)

    # Apply filters
    conditions = []

    if request.portfolio_ready_only:
        conditions.append(Achievement.portfolio_ready.is_(True))

    if request.min_impact_score > 0:
        conditions.append(Achievement.impact_score >= request.min_impact_score)

    if request.include_categories:
        conditions.append(Achievement.category.in_(request.include_categories))

    if conditions:
        query = query.filter(and_(*conditions))

    # Order by display priority and impact score
    query = query.order_by(
        desc(Achievement.display_priority),
        desc(Achievement.impact_score),
    )

    # Apply limit if specified
    if request.max_achievements:
        query = query.limit(request.max_achievements)

    achievements = query.all()

    if not achievements:
        raise HTTPException(
            status_code=404, detail="No achievements found matching criteria"
        )

    try:
        # Generate portfolio
        portfolio_data = await generator.generate(
            achievements=achievements,
            format=request.format,
        )

        # Create snapshot record
        snapshot = PortfolioSnapshot(
            version=portfolio_data["version"],
            format=request.format,
            content=portfolio_data["content"][:1000],  # Store preview
            metadata={
                "full_content_path": portfolio_data["file_path"],
                "categories": list(set(a.category for a in achievements)),
                "date_range": {
                    "start": min(a.started_at for a in achievements).isoformat(),
                    "end": max(a.completed_at for a in achievements).isoformat(),
                },
            },
            total_achievements=len(achievements),
            total_impact_score=sum(a.impact_score for a in achievements),
            total_value_generated=sum(a.business_value for a in achievements),
            total_time_saved=sum(a.time_saved_hours for a in achievements),
            generation_time_seconds=portfolio_data["generation_time"],
            storage_url=portfolio_data.get("storage_url"),
        )

        db.add(snapshot)
        db.commit()

        logger.info(
            f"Generated {request.format} portfolio with {len(achievements)} achievements"
        )

        return PortfolioResponse(
            version=portfolio_data["version"],
            format=request.format,
            total_achievements=len(achievements),
            total_impact_score=snapshot.total_impact_score,
            total_value_generated=snapshot.total_value_generated,
            total_time_saved=snapshot.total_time_saved,
            content_preview=portfolio_data["content"][:500],
            download_url=f"/portfolio/download/{snapshot.id}",
            storage_url=portfolio_data.get("storage_url"),
        )

    except Exception as e:
        logger.error(f"Portfolio generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Portfolio generation failed: {str(e)}"
        )


@router.get("/download/{snapshot_id}")
async def download_portfolio(
    snapshot_id: int,
    db: Session = Depends(get_db),
):
    """Download generated portfolio"""

    snapshot = (
        db.query(PortfolioSnapshot).filter(PortfolioSnapshot.id == snapshot_id).first()
    )

    if not snapshot:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Get file path from metadata
    file_path = snapshot.metadata.get("full_content_path")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Portfolio file not found")

    # Determine filename
    ext_map = {
        "markdown": "md",
        "pdf": "pdf",
        "html": "html",
        "json": "json",
    }

    filename = f"portfolio_{snapshot.version}.{ext_map.get(snapshot.format, 'txt')}"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=f"application/{snapshot.format}",
    )


@router.get("/snapshots")
async def list_portfolio_snapshots(
    format: str = None,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """List portfolio snapshots"""

    query = db.query(PortfolioSnapshot)

    if format:
        query = query.filter(PortfolioSnapshot.format == format)

    snapshots = query.order_by(desc(PortfolioSnapshot.generated_at)).limit(limit).all()

    return [
        {
            "id": s.id,
            "version": s.version,
            "format": s.format,
            "total_achievements": s.total_achievements,
            "total_impact_score": s.total_impact_score,
            "total_value_generated": float(s.total_value_generated),
            "generated_at": s.generated_at.isoformat(),
            "download_url": f"/portfolio/download/{s.id}",
        }
        for s in snapshots
    ]


@router.post("/templates/{template_name}")
async def generate_from_template(
    template_name: str,
    db: Session = Depends(get_db),
):
    """Generate portfolio using predefined template"""

    templates = {
        "executive_summary": {
            "format": "pdf",
            "portfolio_ready_only": True,
            "min_impact_score": 70,
            "max_achievements": 10,
        },
        "technical_portfolio": {
            "format": "markdown",
            "include_categories": ["feature", "optimization", "architecture"],
            "portfolio_ready_only": True,
        },
        "full_archive": {
            "format": "json",
            "portfolio_ready_only": False,
            "min_impact_score": 0,
        },
    }

    if template_name not in templates:
        raise HTTPException(
            status_code=404, detail=f"Template '{template_name}' not found"
        )

    # Use template configuration
    request = PortfolioRequest(**templates[template_name])

    return await generate_portfolio(request, db)
