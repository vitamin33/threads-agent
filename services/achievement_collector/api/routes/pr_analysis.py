"""PR Analysis Routes for Achievement Collector.

Endpoints for analyzing PR value and creating enriched achievements.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from services.achievement_collector.core.logging import setup_logging
from services.achievement_collector.db.config import get_db
from services.achievement_collector.services.pr_value_analyzer_integration import (
    pr_value_integration,
)
from services.achievement_collector.api.schemas import Achievement

logger = setup_logging(__name__)
router = APIRouter()


@router.post("/analyze/{pr_number}", response_model=Achievement)
async def analyze_pr_value(
    pr_number: str, db: Session = Depends(get_db)
) -> Achievement:
    """Analyze PR value and create/update achievement with enriched metrics.

    This endpoint is designed to be called by GitHub Actions after PR merge
    to enrich achievement data with business value metrics.
    """
    try:
        # Run analysis
        achievement = await pr_value_integration.analyze_and_create_achievement(
            pr_number
        )

        if not achievement:
            raise HTTPException(
                status_code=404,
                detail=f"PR #{pr_number} not significant enough for achievement or analysis failed",
            )

        return achievement

    except Exception as e:
        logger.error(f"Error analyzing PR #{pr_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze PR: {str(e)}")


@router.get("/value-metrics/{pr_number}")
async def get_pr_value_metrics(pr_number: str) -> Dict[str, Any]:
    """Get value analysis metrics for a PR without creating achievement.

    Useful for previewing PR value before merge.
    """
    try:
        # Run analyzer without creating achievement
        analysis = await pr_value_integration._run_pr_analyzer(pr_number)

        if not analysis:
            raise HTTPException(
                status_code=404, detail=f"No analysis results found for PR #{pr_number}"
            )

        return {
            "pr_number": pr_number,
            "business_metrics": analysis.get("business_metrics", {}),
            "technical_metrics": analysis.get("technical_metrics", {}),
            "kpis": analysis.get("kpis", {}),
            "achievement_tags": analysis.get("achievement_tags", []),
            "future_impact": analysis.get("future_impact", {}),
            "overall_score": analysis.get("kpis", {}).get("overall_score", 0),
            "qualifies_for_achievement": analysis.get("kpis", {}).get(
                "overall_score", 0
            )
            >= 6.0,
        }

    except Exception as e:
        logger.error(f"Error getting PR metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get PR metrics: {str(e)}"
        )


@router.post("/batch-analyze")
async def batch_analyze_prs(
    pr_numbers: list[str], db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Analyze multiple PRs and create achievements.

    Useful for historical analysis or bulk processing.
    """
    results = {"successful": [], "failed": [], "skipped": []}

    for pr_number in pr_numbers:
        try:
            achievement = await pr_value_integration.analyze_and_create_achievement(
                pr_number
            )

            if achievement:
                results["successful"].append(
                    {
                        "pr_number": pr_number,
                        "achievement_id": achievement.id,
                        "title": achievement.title,
                        "score": achievement.impact_score
                        / 10,  # Convert back to 0-10 scale
                    }
                )
            else:
                results["skipped"].append(
                    {
                        "pr_number": pr_number,
                        "reason": "Below threshold or already exists",
                    }
                )

        except Exception as e:
            results["failed"].append({"pr_number": pr_number, "error": str(e)})
            logger.error(f"Failed to analyze PR #{pr_number}: {e}")

    return {"total_processed": len(pr_numbers), "results": results}


@router.get("/thresholds")
async def get_analysis_thresholds() -> Dict[str, Any]:
    """Get current thresholds for PR value analysis."""
    return {
        "min_overall_score": pr_value_integration.min_overall_score,
        "score_levels": {
            "exceptional": 9.0,
            "high_impact": 8.0,
            "significant": 7.0,
            "good": 6.0,
            "moderate": 5.0,
        },
        "portfolio_ready_threshold": 7.0,
        "business_metrics": {
            "roi_excellent": 300,  # 300% ROI
            "roi_good": 100,  # 100% ROI
            "savings_significant": 100000,  # $100k
            "savings_moderate": 50000,  # $50k
        },
    }
