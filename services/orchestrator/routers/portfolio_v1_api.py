"""
Portfolio V1 API - Matches Frontend Expectations

This API provides the exact data format expected by the portfolio frontend,
connecting to real Supabase achievement data.
"""

import logging
import time
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from services.orchestrator.db import get_db_session
from services.common.metrics import record_http_request

logger = logging.getLogger(__name__)

# Create router matching portfolio frontend expectations
portfolio_v1_router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio_v1"])


@portfolio_v1_router.get("/achievements")
async def get_portfolio_achievements(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, description="Number of achievements"),
    featured_only: bool = Query(False, description="Only featured achievements"),
    db: Session = Depends(get_db_session),
) -> JSONResponse:
    """
    Get achievements in the exact format expected by portfolio frontend.

    Expected by: temp_frontend/components/achievements-live-api.tsx
    """
    start_time = time.time()

    try:
        # Build query filters
        where_clauses = ["portfolio_ready = true"]

        if category:
            where_clauses.append(f"category = '{category}'")

        if featured_only:
            where_clauses.append("impact_score >= 90")

        where_clause = "WHERE " + " AND ".join(where_clauses)

        # Query achievements in expected format
        sql = f"""
            SELECT 
                id::text as id,
                title,
                category,
                impact_score,
                COALESCE(
                    CASE 
                        WHEN business_value ~ '^\\$[0-9,]+' THEN 
                            CAST(REGEXP_REPLACE(business_value, '[^0-9]', '', 'g') AS NUMERIC)
                        WHEN business_value::text LIKE '%"total_value":%' THEN
                            CAST((business_value::json->>'total_value')::text AS NUMERIC)
                        ELSE 0
                    END, 0
                ) as business_value,
                duration_hours,
                COALESCE(skills_demonstrated, '[]'::json) as tech_stack,
                COALESCE(evidence, '{{}}'::json) as evidence,
                ai_summary as summary,
                ai_technical_analysis as technical_analysis,
                ai_impact_analysis as architecture_notes,
                source_url,
                source_id,
                completed_at,
                performance_improvement_pct,
                time_saved_hours
            FROM achievements 
            {where_clause}
            ORDER BY display_priority DESC NULLS LAST, impact_score DESC, completed_at DESC
            LIMIT {limit}
        """

        achievements_raw = db.execute(text(sql)).fetchall()

        # Transform to frontend format
        achievements = []
        for ach in achievements_raw:
            # Parse tech stack (skills_demonstrated)
            try:
                tech_stack = json.loads(ach.tech_stack) if ach.tech_stack else []
                if isinstance(tech_stack, list):
                    tech_stack = tech_stack[:8]  # Limit to 8 skills
                else:
                    tech_stack = []
            except:
                tech_stack = []

            # Parse evidence
            try:
                evidence = json.loads(ach.evidence) if ach.evidence else {}
            except:
                evidence = {}

            # Format evidence for frontend
            formatted_evidence = {
                "before_metrics": evidence.get("metrics_before", {}),
                "after_metrics": evidence.get("metrics_after", {}),
                "pr_number": None,
                "repo_url": ach.source_url,
            }

            # Extract PR number from source_id or URL
            if ach.source_id and ach.source_id.isdigit():
                formatted_evidence["pr_number"] = int(ach.source_id)

            achievement_data = {
                "id": ach.id,
                "title": ach.title,
                "category": ach.category,
                "impact_score": float(ach.impact_score or 0),
                "business_value": float(ach.business_value or 0),
                "duration_hours": float(ach.duration_hours or 0),
                "tech_stack": tech_stack,
                "evidence": formatted_evidence,
                "generated_content": {
                    "summary": ach.summary or "",
                    "technical_analysis": ach.technical_analysis or "",
                    "architecture_notes": ach.architecture_notes or "",
                },
                "performance_improvement": float(ach.performance_improvement_pct or 0),
                "time_saved_hours": float(ach.time_saved_hours or 0),
                "completed_at": ach.completed_at.isoformat()
                if ach.completed_at
                else None,
            }

            achievements.append(achievement_data)

        # Calculate meta statistics
        total_business_value = sum(ach["business_value"] for ach in achievements)
        total_time_saved = sum(ach["time_saved_hours"] for ach in achievements)
        avg_impact = (
            sum(ach["impact_score"] for ach in achievements) / len(achievements)
            if achievements
            else 0
        )

        response_data = {
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_achievements": len(achievements),
                "total_business_value": total_business_value,
                "total_time_saved_hours": total_time_saved,
                "avg_impact_score": avg_impact,
                "data_source": "live",
                "note": "Real achievements from Supabase production database",
            },
            "achievements": achievements,
        }

        # Record metrics
        duration = time.time() - start_time
        record_http_request("GET", "/api/v1/portfolio/achievements", 200, duration)

        return JSONResponse(content=response_data)

    except Exception as e:
        duration = time.time() - start_time
        record_http_request("GET", "/api/v1/portfolio/achievements", 500, duration)
        logger.error(f"Error getting portfolio achievements: {e}")
        raise HTTPException(status_code=500, detail=f"Portfolio API error: {str(e)}")


@portfolio_v1_router.get("/generate")
async def generate_portfolio_data(
    db: Session = Depends(get_db_session),
) -> JSONResponse:
    """
    Generate complete portfolio data for case study sync.

    Expected by: temp_frontend/app/api/case-studies/sync/route.ts
    """
    start_time = time.time()

    try:
        # Get all portfolio-ready achievements
        sql = """
            SELECT 
                id::text as id,
                title,
                category,
                impact_score,
                complexity_score,
                COALESCE(
                    CASE 
                        WHEN business_value ~ '^\\$[0-9,]+' THEN 
                            CAST(REGEXP_REPLACE(business_value, '[^0-9]', '', 'g') AS NUMERIC)
                        WHEN business_value::text LIKE '%"total_value":%' THEN
                            CAST((business_value::json->>'total_value')::text AS NUMERIC)
                        ELSE 0
                    END, 0
                ) as business_value,
                duration_hours,
                COALESCE(skills_demonstrated, '[]'::json) as tech_stack,
                COALESCE(evidence, '{}'::json) as evidence,
                COALESCE(metrics_before, '{}'::json) as metrics_before,
                COALESCE(metrics_after, '{}'::json) as metrics_after,
                ai_summary,
                ai_technical_analysis,
                ai_impact_analysis,
                source_url,
                source_id,
                completed_at
            FROM achievements 
            WHERE portfolio_ready = true
            ORDER BY impact_score DESC
        """

        achievements_raw = db.execute(text(sql)).fetchall()

        # Transform to expected format
        achievements = []
        for ach in achievements_raw:
            # Parse JSON fields safely
            try:
                tech_stack = json.loads(ach.tech_stack) if ach.tech_stack else []
                evidence = json.loads(ach.evidence) if ach.evidence else {}
                metrics_before = (
                    json.loads(ach.metrics_before) if ach.metrics_before else {}
                )
                metrics_after = (
                    json.loads(ach.metrics_after) if ach.metrics_after else {}
                )
            except:
                tech_stack = []
                evidence = {}
                metrics_before = {}
                metrics_after = {}

            achievement_data = {
                "id": ach.id,
                "title": ach.title,
                "category": ach.category,
                "impact_score": float(ach.impact_score or 0),
                "business_value": float(ach.business_value or 0),
                "duration_hours": float(ach.duration_hours or 0),
                "tech_stack": tech_stack,
                "evidence": {
                    "before_metrics": metrics_before,
                    "after_metrics": metrics_after,
                    "pr_number": int(ach.source_id)
                    if ach.source_id and ach.source_id.isdigit()
                    else None,
                    "repo_url": ach.source_url,
                },
                "generated_content": {
                    "summary": ach.ai_summary or "",
                    "technical_analysis": ach.ai_technical_analysis or "",
                    "architecture_notes": ach.ai_impact_analysis or "",
                },
            }

            achievements.append(achievement_data)

        response_data = {
            "achievements": achievements,
            "meta": {
                "total": len(achievements),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "data_source": "supabase_production",
            },
        }

        # Record metrics
        duration = time.time() - start_time
        record_http_request("GET", "/api/v1/portfolio/generate", 200, duration)

        return JSONResponse(content=response_data)

    except Exception as e:
        duration = time.time() - start_time
        record_http_request("GET", "/api/v1/portfolio/generate", 500, duration)
        logger.error(f"Error generating portfolio data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@portfolio_v1_router.get("/stats")
async def get_portfolio_stats(db: Session = Depends(get_db_session)) -> JSONResponse:
    """Get portfolio statistics for frontend display."""
    start_time = time.time()

    try:
        # Get comprehensive stats
        stats_query = """
            SELECT 
                COUNT(*) as total_achievements,
                COUNT(CASE WHEN portfolio_ready = true THEN 1 END) as portfolio_ready,
                AVG(impact_score) as avg_impact,
                AVG(complexity_score) as avg_complexity,
                SUM(time_saved_hours) as total_time_saved,
                SUM(CASE 
                    WHEN business_value ~ '^\\$[0-9,]+' THEN 
                        CAST(REGEXP_REPLACE(business_value, '[^0-9]', '', 'g') AS NUMERIC)
                    WHEN business_value::text LIKE '%"total_value":%' THEN
                        CAST((business_value::json->>'total_value')::text AS NUMERIC)
                    ELSE 0
                END) as total_business_value,
                COUNT(DISTINCT category) as categories_covered
            FROM achievements
        """

        stats = db.execute(text(stats_query)).first()

        # Get category breakdown
        category_stats = db.execute(
            text("""
            SELECT 
                category,
                COUNT(*) as count,
                AVG(impact_score) as avg_impact
            FROM achievements
            WHERE portfolio_ready = true
            GROUP BY category
            ORDER BY count DESC
        """)
        ).fetchall()

        stats_data = {
            "summary": {
                "total_achievements": int(stats.total_achievements or 0),
                "portfolio_ready": int(stats.portfolio_ready or 0),
                "avg_impact_score": float(stats.avg_impact or 0),
                "avg_complexity_score": float(stats.avg_complexity or 0),
                "total_time_saved_hours": float(stats.total_time_saved or 0),
                "total_business_value": float(stats.total_business_value or 0),
                "categories_covered": int(stats.categories_covered or 0),
            },
            "categories": [
                {
                    "category": cat.category,
                    "count": int(cat.count),
                    "avg_impact": float(cat.avg_impact or 0),
                }
                for cat in category_stats
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Record metrics
        duration = time.time() - start_time
        record_http_request("GET", "/api/v1/portfolio/stats", 200, duration)

        return JSONResponse(content=stats_data)

    except Exception as e:
        duration = time.time() - start_time
        record_http_request("GET", "/api/v1/portfolio/stats", 500, duration)
        logger.error(f"Error getting portfolio stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@portfolio_v1_router.get("/health")
async def portfolio_v1_health(db: Session = Depends(get_db_session)) -> JSONResponse:
    """Health check for portfolio V1 API."""
    try:
        # Test database connectivity
        test_query = db.execute(text("SELECT COUNT(*) FROM achievements")).first()
        achievement_count = int(test_query[0] or 0)

        # Test variant performance data
        variant_query = db.execute(
            text("SELECT COUNT(*) FROM variant_performance")
        ).first()
        variant_count = int(variant_query[0] or 0)

        health_status = {
            "status": "healthy",
            "database_connected": True,
            "achievement_count": achievement_count,
            "variant_count": variant_count,
            "api_version": "1.0",
            "data_source": "local_cluster_with_supabase_sync",
            "endpoints": [
                "/api/v1/portfolio/achievements",
                "/api/v1/portfolio/generate",
                "/api/v1/portfolio/stats",
                "/api/v1/portfolio/health",
            ],
            "frontend_compatibility": "next.js portfolio ready",
            "last_check": datetime.now(timezone.utc).isoformat(),
        }

        return JSONResponse(content=health_status)

    except Exception as e:
        logger.error(f"Portfolio V1 health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "database_connected": False,
                "message": f"Health check failed: {str(e)}",
            },
            status_code=503,
        )
