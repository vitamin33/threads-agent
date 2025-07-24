# services/orchestrator/experiment_endpoints.py
"""API endpoints for A/B testing experiments"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.common.metrics import record_http_request
from services.orchestrator.experiments import (
    ExperimentManager,
    ExperimentStatus,
    ExperimentType,
    StatisticalAnalyzer,
    StoppingReason,
)
from services.orchestrator.scheduler import ExperimentScheduler

logger = logging.getLogger(__name__)

# Create router
experiment_router = APIRouter(prefix="/experiments", tags=["experiments"])

# Initialize managers
experiment_manager = ExperimentManager()
scheduler = ExperimentScheduler()
analyzer = StatisticalAnalyzer()


# Request/Response Models
class CreateExperimentRequest(BaseModel):
    name: str = Field(..., description="Experiment name")
    variant_ids: List[str] = Field(..., min_items=2, description="Variant IDs to test")
    persona_id: str = Field(..., description="Persona running the experiment")
    type: ExperimentType = Field(ExperimentType.AB_TEST, description="Experiment type")
    description: Optional[str] = Field(None, description="Experiment description")
    config: Optional[Dict[str, Any]] = Field(
        None, description="Additional configuration"
    )


class ExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    status: str
    type: str
    persona_id: str
    created_at: datetime
    started_at: Optional[datetime]
    duration_hours: Optional[float]
    variant_count: int


class ExperimentStatsResponse(BaseModel):
    experiment_id: str
    name: str
    status: str
    duration_hours: float
    total_impressions: int
    variants: List[Dict[str, Any]]
    winner: Optional[str]
    stopping_reason: Optional[str]


class ScheduleResponse(BaseModel):
    scheduled_posts: int
    posts: List[Dict[str, Any]]
    next_window_start: datetime


class PowerAnalysisRequest(BaseModel):
    baseline_rate: float = Field(..., ge=0, le=1, description="Current engagement rate")
    minimum_effect: float = Field(..., ge=0, description="Minimum detectable effect")
    power: float = Field(0.8, ge=0.5, le=0.99, description="Statistical power")
    alpha: float = Field(0.05, ge=0.01, le=0.1, description="Significance level")


# Endpoints
@experiment_router.post("/create", response_model=ExperimentResponse)
async def create_experiment(request: CreateExperimentRequest):
    """Create a new A/B testing experiment"""

    start_time = time.time()
    status = 200

    try:
        # Validate variant count
        if len(request.variant_ids) < 2:
            raise HTTPException(
                status_code=400, detail="At least 2 variants required for experiment"
            )

        if len(request.variant_ids) > 10:
            raise HTTPException(
                status_code=400, detail="Maximum 10 variants allowed per experiment"
            )

        # Create experiment
        experiment_id = experiment_manager.create_experiment(
            name=request.name,
            variant_ids=request.variant_ids,
            persona_id=request.persona_id,
            experiment_type=request.type,
            config=request.config,
        )

        # Get experiment details for validation (not used in response)
        _ = experiment_manager.get_experiment_stats(experiment_id)

        return ExperimentResponse(
            experiment_id=experiment_id,
            name=request.name,
            status=ExperimentStatus.DRAFT,
            type=request.type,
            persona_id=request.persona_id,
            created_at=datetime.utcnow(),
            started_at=None,
            duration_hours=None,
            variant_count=len(request.variant_ids),
        )

    except Exception as e:
        logger.error(f"Error creating experiment: {str(e)}")
        status = 500
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration = time.time() - start_time
        record_http_request("POST", "/experiments/create", status, duration)


@experiment_router.post("/{experiment_id}/start")
async def start_experiment(experiment_id: str):
    """Start an experiment"""

    start_time = time.time()
    status = 200

    try:
        success = experiment_manager.start_experiment(experiment_id)

        if not success:
            status = 400
            raise HTTPException(
                status_code=400, detail="Experiment not found or already started"
            )

        return {"status": "started", "experiment_id": experiment_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting experiment: {str(e)}")
        status = 500
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/experiments/{experiment_id}/start", status, duration
        )


@experiment_router.get("/{experiment_id}/stats", response_model=ExperimentStatsResponse)
async def get_experiment_stats(experiment_id: str):
    """Get current experiment statistics and results"""

    start_time = time.time()
    status = 200

    try:
        stats = experiment_manager.get_experiment_stats(experiment_id)

        if not stats:
            raise HTTPException(status_code=404, detail="Experiment not found")

        # Calculate total impressions
        total_impressions = sum(v["impressions"] for v in stats["variants"])

        # Determine winner if any
        winner = None
        stopping_reason = None

        # Check stopping conditions
        stop_reason = experiment_manager.check_stopping_conditions(experiment_id)
        if stop_reason:
            stopping_reason = stop_reason

            # Find winner based on reason
            if stop_reason == StoppingReason.SIGNIFICANCE_REACHED:
                # Find variant with highest engagement rate
                best_variant = max(
                    stats["variants"], key=lambda v: v["engagement_rate"]
                )
                winner = best_variant["variant_id"]

        return ExperimentStatsResponse(
            experiment_id=experiment_id,
            name=stats["name"],
            status=stats["status"],
            duration_hours=stats["duration_hours"],
            total_impressions=total_impressions,
            variants=stats["variants"],
            winner=winner,
            stopping_reason=stopping_reason,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiment stats: {str(e)}")
        status = 500
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration = time.time() - start_time
        record_http_request(
            "GET", f"/experiments/{experiment_id}/stats", status, duration
        )


@experiment_router.get("/{experiment_id}/significance")
async def get_significance_analysis(experiment_id: str):
    """Get detailed statistical significance analysis"""

    start_time = time.time()
    status = 200

    try:
        stats = experiment_manager.get_experiment_stats(experiment_id)

        if not stats:
            raise HTTPException(status_code=404, detail="Experiment not found")

        # Find control variant
        control = next((v for v in stats["variants"] if v["is_control"]), None)
        if not control:
            raise HTTPException(status_code=400, detail="No control variant found")

        results = {
            "experiment_id": experiment_id,
            "control_variant": control["variant_id"],
            "comparisons": [],
        }

        # Compare each treatment to control
        for variant in stats["variants"]:
            if variant["is_control"]:
                continue

            if variant["impressions"] >= 30 and control["impressions"] >= 30:
                analysis = analyzer.test_significance(
                    {
                        "engagements_total": control["engagements"],
                        "impressions_total": control["impressions"],
                    },
                    {
                        "engagements_total": variant["engagements"],
                        "impressions_total": variant["impressions"],
                    },
                )

                # Add Bayesian probability
                bayesian_prob = analyzer.calculate_bayesian_probability(
                    {
                        "engagements_total": control["engagements"],
                        "impressions_total": control["impressions"],
                    },
                    {
                        "engagements_total": variant["engagements"],
                        "impressions_total": variant["impressions"],
                    },
                )

                results["comparisons"].append(
                    {
                        "variant_id": variant["variant_id"],
                        "p_value": analysis["p_value"],
                        "confidence_interval": analysis["confidence_interval"],
                        "effect_size": analysis["effect_size"],
                        "is_significant": analysis["is_significant"],
                        "bayesian_probability": bayesian_prob,
                        "recommendation": _get_recommendation(
                            analysis["p_value"], bayesian_prob, variant["impressions"]
                        ),
                    }
                )
            else:
                results["comparisons"].append(
                    {
                        "variant_id": variant["variant_id"],
                        "status": "insufficient_data",
                        "message": f"Need at least 30 impressions (current: {variant['impressions']})",
                    }
                )

        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing significance: {str(e)}")
        status = 500
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration = time.time() - start_time
        record_http_request(
            "GET", f"/experiments/{experiment_id}/significance", status, duration
        )


@experiment_router.post("/{experiment_id}/power-analysis")
async def calculate_power_analysis(experiment_id: str, request: PowerAnalysisRequest):
    """Calculate required sample size for desired power"""

    start_time = time.time()
    status = 200

    try:
        sample_size = analyzer.calculate_sample_size(
            baseline_rate=request.baseline_rate,
            minimum_effect=request.minimum_effect,
            power=request.power,
            alpha=request.alpha,
        )

        # Calculate time to reach sample size
        stats = experiment_manager.get_experiment_stats(experiment_id)
        if stats and stats["duration_hours"] > 0:
            current_rate = (
                sum(v["impressions"] for v in stats["variants"])
                / stats["duration_hours"]
            )
            hours_needed = sample_size / current_rate if current_rate > 0 else 0
        else:
            hours_needed = 0

        return {
            "required_sample_size": sample_size,
            "baseline_rate": request.baseline_rate,
            "minimum_effect": request.minimum_effect,
            "power": request.power,
            "alpha": request.alpha,
            "estimated_hours_needed": round(hours_needed, 1),
            "estimated_days_needed": round(hours_needed / 24, 1),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating power analysis: {str(e)}")
        status = 500
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/experiments/{experiment_id}/power-analysis", status, duration
        )


@experiment_router.get("/scheduler/next-posts", response_model=ScheduleResponse)
async def get_next_scheduled_posts(hours: int = 1):
    """Get posts scheduled for the next time window"""

    start_time = time.time()
    status = 200

    try:
        scheduled = scheduler.schedule_next_posts(time_window_hours=hours)

        posts = [
            {
                "variant_id": s.variant_id,
                "experiment_id": s.experiment_id,
                "persona_id": s.persona_id,
                "scheduled_time": s.scheduled_time,
                "priority": s.priority,
                "content_preview": s.content[:100] + "..."
                if len(s.content) > 100
                else s.content,
            }
            for s in scheduled
        ]

        return ScheduleResponse(
            scheduled_posts=len(posts), posts=posts, next_window_start=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduled posts: {str(e)}")
        status = 500
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration = time.time() - start_time
        record_http_request(
            "GET", "/experiments/scheduler/next-posts", status, duration
        )


@experiment_router.get("/active")
async def get_active_experiments():
    """Get all active experiments"""

    start_time = time.time()
    status = 200

    try:
        from sqlalchemy.orm import Session
        from services.orchestrator.db.models import Experiment
        from services.orchestrator.experiments import engine

        with Session(engine) as session:
            experiments = (
                session.query(Experiment)
                .filter_by(status=ExperimentStatus.ACTIVE)
                .all()
            )

            return [
                {
                    "experiment_id": exp.experiment_id,
                    "name": exp.name,
                    "persona_id": exp.persona_id,
                    "type": exp.type,
                    "started_at": exp.started_at,
                    "duration_hours": (
                        (datetime.utcnow() - exp.started_at).total_seconds() / 3600
                        if exp.started_at
                        else 0
                    ),
                }
                for exp in experiments
            ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active experiments: {str(e)}")
        status = 500
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/experiments/active", status, duration)


def _get_recommendation(p_value: float, bayesian_prob: float, sample_size: int) -> str:
    """Generate recommendation based on statistical results"""

    if sample_size < 30:
        return "Insufficient data - need more samples"
    elif p_value < 0.05 and bayesian_prob > 0.95:
        return "Strong winner - implement this variant"
    elif p_value < 0.05:
        return "Statistically significant - consider implementing"
    elif p_value < 0.10:
        return "Trending positive - continue testing"
    elif bayesian_prob > 0.80:
        return "Promising based on Bayesian analysis - gather more data"
    else:
        return "No clear difference - may want to test other variants"
