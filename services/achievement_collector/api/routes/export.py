"""
Export API routes for multi-format portfolio generation.
"""

import os
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db.config import get_db
from ...export.formats.csv_export import CSVExporter
from ...export.formats.json_export import JSONExporter
from ...export.linkedin.integration import LinkedInIntegration
from ...export.pdf.portfolio_generator import PortfolioGenerator
from ...export.pdf.resume_generator import ResumeGenerator
from ...export.web.portfolio_site import WebPortfolioGenerator


class ExportRequest(BaseModel):
    """Base export request model."""

    user_id: Optional[str] = None
    filters: Optional[Dict] = None


class PDFExportRequest(ExportRequest):
    """PDF export request model."""

    format: str = "resume"  # resume, portfolio, executive_brief
    user_info: Optional[Dict[str, str]] = None
    include_charts: bool = True


class LinkedInExportRequest(ExportRequest):
    """LinkedIn export request model."""

    post_type: str = "achievement"  # achievement, milestone, summary


class WebPortfolioRequest(ExportRequest):
    """Web portfolio export request model."""

    user_info: Optional[Dict[str, str]] = None
    theme: str = "modern"  # modern, dark, classic


router = APIRouter(prefix="/export", tags=["export"])

# Initialize exporters
json_exporter = JSONExporter()
csv_exporter = CSVExporter()
resume_generator = ResumeGenerator()
portfolio_generator = PortfolioGenerator()
linkedin_integration = LinkedInIntegration()
web_portfolio_generator = WebPortfolioGenerator()


@router.post("/json")
async def export_json(
    request: ExportRequest,
    db: Session = Depends(get_db),
    include_analytics: bool = Query(True, description="Include analytics data"),
):
    """
    Export achievements as JSON.

    Returns structured JSON with achievements and optional analytics.
    """
    try:
        data = await json_exporter.export(
            db,
            user_id=request.user_id,
            filters=request.filters,
            include_analytics=include_analytics,
        )

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/csv")
async def export_csv(
    request: ExportRequest,
    db: Session = Depends(get_db),
    format_type: str = Query(
        "detailed", description="CSV format type (detailed/summary)"
    ),
):
    """
    Export achievements as CSV.

    Returns CSV file for download.
    """
    try:
        csv_data = await csv_exporter.export(
            db,
            user_id=request.user_id,
            filters=request.filters,
            format_type=format_type,
        )

        # Return as streaming response
        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=achievements_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf")
async def export_pdf(request: PDFExportRequest, db: Session = Depends(get_db)):
    """
    Export achievements as PDF.

    Generates professional PDF documents:
    - resume: Professional resume format
    - portfolio: Comprehensive portfolio with visualizations
    - executive_brief: One-page executive summary
    """
    try:
        filename = (
            f"temp_{request.format}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        if request.format == "resume":
            pdf_path = await resume_generator.export(
                db,
                user_id=request.user_id,
                filters=request.filters,
                user_info=request.user_info,
                filename=filename,
            )
        elif request.format == "portfolio":
            pdf_path = await portfolio_generator.export(
                db,
                user_id=request.user_id,
                filters=request.filters,
                user_info=request.user_info,
                filename=filename,
                include_charts=request.include_charts,
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid PDF format")

        # Return file for download
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={request.format}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if "pdf_path" in locals() and os.path.exists(pdf_path):
            os.remove(pdf_path)


@router.post("/linkedin")
async def export_linkedin(
    request: LinkedInExportRequest, db: Session = Depends(get_db)
):
    """
    Generate LinkedIn-ready content.

    Creates optimized posts for LinkedIn sharing:
    - achievement: Individual achievement posts
    - milestone: Career milestone celebrations
    - summary: Quarterly/yearly summaries
    """
    try:
        posts = await linkedin_integration.export(
            db,
            user_id=request.user_id,
            filters=request.filters,
            post_type=request.post_type,
        )

        return {"posts": [post.dict() for post in posts], "total": len(posts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/linkedin/profile-suggestions")
async def get_profile_suggestions(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="User ID filter"),
):
    """
    Get LinkedIn profile optimization suggestions.

    Returns formatted content for:
    - Professional headline
    - About section
    - Featured achievements
    """
    try:
        achievements = linkedin_integration.get_achievements(db, user_id)

        if not achievements:
            return {"error": "No achievements found", "suggestions": {}}

        suggestions = linkedin_integration.format_for_profile_update(achievements)

        return {"suggestions": suggestions, "achievement_count": len(achievements)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/linkedin/recommendation-template")
async def get_recommendation_template(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="User ID filter"),
    recommender_context: Optional[str] = Query(
        None, description="Context about recommender"
    ),
):
    """
    Generate LinkedIn recommendation template.

    Creates a professional recommendation template based on achievements.
    """
    try:
        achievements = linkedin_integration.get_achievements(db, user_id)

        if not achievements:
            return {"error": "No achievements found", "template": ""}

        template = linkedin_integration.generate_recommendation_text(
            achievements, recommender_context
        )

        return {"template": template, "achievement_count": len(achievements)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/web-portfolio")
async def export_web_portfolio(
    request: WebPortfolioRequest, db: Session = Depends(get_db)
):
    """
    Generate interactive web portfolio.

    Creates a complete portfolio website with:
    - Responsive design
    - Interactive visualizations
    - Achievement timeline
    - Skills radar charts
    """
    try:
        output_dir = await web_portfolio_generator.export(
            db,
            user_id=request.user_id,
            filters=request.filters,
            user_info=request.user_info,
            theme=request.theme,
        )

        # Create zip file of portfolio
        import shutil

        zip_path = f"{output_dir}.zip"
        shutil.make_archive(output_dir, "zip", output_dir)

        # Return zip file
        return FileResponse(
            zip_path,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=portfolio_{datetime.utcnow().strftime('%Y%m%d')}.zip"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary files
        if "output_dir" in locals() and os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        if "zip_path" in locals() and os.path.exists(zip_path):
            os.remove(zip_path)


@router.get("/formats")
async def get_export_formats():
    """
    Get available export formats and their options.
    """
    return {
        "formats": {
            "json": {
                "description": "Structured JSON export",
                "options": ["include_analytics"],
            },
            "csv": {
                "description": "Spreadsheet-friendly CSV",
                "options": ["detailed", "summary"],
            },
            "pdf": {
                "description": "Professional PDF documents",
                "types": ["resume", "portfolio", "executive_brief"],
            },
            "linkedin": {
                "description": "LinkedIn-optimized content",
                "types": ["achievement", "milestone", "summary"],
            },
            "web": {
                "description": "Interactive web portfolio",
                "themes": ["modern", "dark", "classic"],
            },
        }
    }
