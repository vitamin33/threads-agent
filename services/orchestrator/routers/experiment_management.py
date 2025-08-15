"""
Real Experiment Management API Endpoints

This module provides comprehensive experiment management capabilities
with lifecycle control, traffic allocation, and statistical analysis.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.orchestrator.db import get_db_session
from services.orchestrator.experiment_manager import (
    ExperimentManager,
    ExperimentConfig,
    ExperimentStatus,
    create_experiment_manager,
)
from services.common.metrics import record_http_request

logger = logging.getLogger(__name__)

# Create router for experiment management
experiment_router = APIRouter(prefix="/experiments", tags=["experiment_management"])


# ── Pydantic Models ──────────────────────────────────────────────────────────


class CreateExperimentRequest(BaseModel):
    """Request for creating a new experiment."""

    name: str = Field(..., description="Name of the experiment")
    description: Optional[str] = Field(
        None, description="Description of the experiment"
    )
    variant_ids: List[str] = Field(
        ..., description="List of variant IDs to test", min_items=2
    )
    traffic_allocation: List[float] = Field(
        ..., description="Traffic allocation for each variant", min_items=2
    )
    target_persona: str = Field(..., description="Target persona for the experiment")
    success_metrics: List[str] = Field(..., description="Success metrics to track")
    duration_days: int = Field(..., description="Experiment duration in days", gt=0)
    control_variant_id: Optional[str] = Field(None, description="Control variant ID")
    min_sample_size: Optional[int] = Field(
        None, description="Minimum sample size", gt=0
    )
    significance_level: float = Field(
        0.05, description="Statistical significance level", gt=0, lt=1
    )
    minimum_detectable_effect: float = Field(
        0.05, description="Minimum detectable effect", gt=0
    )
    created_by: Optional[str] = Field(None, description="Creator of the experiment")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ExperimentSummary(BaseModel):
    """Summary information for an experiment."""

    experiment_id: str
    name: str
    status: str
    target_persona: str
    variant_count: int
    total_participants: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_days: int
    winner_variant_id: Optional[str]
    is_statistically_significant: Optional[bool]
    created_at: datetime


class CreateExperimentResponse(BaseModel):
    """Response for experiment creation."""

    experiment_id: str
    name: str
    status: str
    message: str
    variant_ids: List[str]
    traffic_allocation: List[float]


class ExperimentActionRequest(BaseModel):
    """Request for experiment actions (start, pause, complete)."""

    reason: Optional[str] = Field(None, description="Reason for the action")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ExperimentActionResponse(BaseModel):
    """Response for experiment actions."""

    success: bool
    experiment_id: str
    new_status: str
    message: str
    timestamp: datetime


class ParticipantAssignmentRequest(BaseModel):
    """Request for participant assignment."""

    participant_id: str = Field(..., description="ID of the participant")
    context: Optional[Dict[str, Any]] = Field(None, description="Assignment context")


class ParticipantAssignmentResponse(BaseModel):
    """Response for participant assignment."""

    experiment_id: str
    participant_id: str
    assigned_variant_id: Optional[str]
    success: bool
    message: str


class EngagementTrackingRequest(BaseModel):
    """Request for tracking engagement within an experiment."""

    participant_id: str = Field(..., description="ID of the participant")
    variant_id: str = Field(..., description="ID of the assigned variant")
    action_taken: str = Field(..., description="Action taken by participant")
    engagement_value: float = Field(1.0, description="Value of the engagement")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EngagementTrackingResponse(BaseModel):
    """Response for engagement tracking."""

    success: bool
    experiment_id: str
    participant_id: str
    variant_id: str
    message: str


class VariantPerformance(BaseModel):
    """Performance data for a variant within an experiment."""

    variant_id: str
    participants: int
    impressions: int
    conversions: int
    conversion_rate: float
    allocated_traffic: float
    actual_traffic: float
    confidence_lower: Optional[float]
    confidence_upper: Optional[float]


class ExperimentResultsSummary(BaseModel):
    """Summary of experiment results."""

    total_participants: int
    experiment_duration_days: int
    winner_variant_id: Optional[str]
    improvement_percentage: Optional[float]
    is_statistically_significant: bool
    p_value: Optional[float]


class ExperimentResultsResponse(BaseModel):
    """Comprehensive experiment results."""

    experiment_id: str
    name: str
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    results_summary: ExperimentResultsSummary
    variant_performance: Dict[str, VariantPerformance]
    confidence_level: float
    segment_breakdown: Optional[Dict[str, Any]]


# ── API Endpoints ─────────────────────────────────────────────────────────────


@experiment_router.post(
    "/create",
    response_model=CreateExperimentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_experiment(
    request: CreateExperimentRequest,
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> CreateExperimentResponse:
    """Create a new A/B testing experiment with proper validation."""
    start_time = time.time()

    try:
        config = ExperimentConfig(
            name=request.name,
            description=request.description,
            variant_ids=request.variant_ids,
            traffic_allocation=request.traffic_allocation,
            target_persona=request.target_persona,
            success_metrics=request.success_metrics,
            duration_days=request.duration_days,
            control_variant_id=request.control_variant_id,
            min_sample_size=request.min_sample_size,
            significance_level=request.significance_level,
            minimum_detectable_effect=request.minimum_detectable_effect,
            created_by=request.created_by,
            metadata=request.metadata,
        )

        experiment_id = manager.create_experiment(config)

        response = CreateExperimentResponse(
            experiment_id=experiment_id,
            name=request.name,
            status="draft",
            message=f"Experiment '{request.name}' created successfully",
            variant_ids=request.variant_ids,
            traffic_allocation=request.traffic_allocation,
        )

        # Record metrics
        duration = time.time() - start_time
        record_http_request("POST", "/experiments/create", 201, duration)

        return response

    except ValueError as e:
        duration = time.time() - start_time
        record_http_request("POST", "/experiments/create", 400, duration)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        duration = time.time() - start_time
        record_http_request("POST", "/experiments/create", 500, duration)
        logger.error(f"Error creating experiment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@experiment_router.post(
    "/{experiment_id}/start", response_model=ExperimentActionResponse
)
async def start_experiment(
    experiment_id: str,
    request: ExperimentActionRequest = ExperimentActionRequest(),
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> ExperimentActionResponse:
    """Start an experiment (move from draft to active)."""
    start_time = time.time()

    try:
        success = manager.start_experiment(experiment_id)

        if success:
            response = ExperimentActionResponse(
                success=True,
                experiment_id=experiment_id,
                new_status="active",
                message="Experiment started successfully",
                timestamp=datetime.now(timezone.utc),
            )
            status_code = 200
        else:
            response = ExperimentActionResponse(
                success=False,
                experiment_id=experiment_id,
                new_status="unknown",
                message="Failed to start experiment",
                timestamp=datetime.now(timezone.utc),
            )
            status_code = 400

        # Record metrics
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/experiments/{experiment_id}/start", status_code, duration
        )

        return response

    except Exception as e:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/experiments/{experiment_id}/start", 500, duration
        )
        logger.error(f"Error starting experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@experiment_router.post(
    "/{experiment_id}/pause", response_model=ExperimentActionResponse
)
async def pause_experiment(
    experiment_id: str,
    request: ExperimentActionRequest,
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> ExperimentActionResponse:
    """Pause an active experiment."""
    start_time = time.time()

    try:
        success = manager.pause_experiment(experiment_id, request.reason)

        response = ExperimentActionResponse(
            success=success,
            experiment_id=experiment_id,
            new_status="paused" if success else "unknown",
            message=f"Experiment {'paused' if success else 'pause failed'}: {request.reason or 'No reason provided'}",
            timestamp=datetime.now(timezone.utc),
        )

        # Record metrics
        duration = time.time() - start_time
        status_code = 200 if success else 400
        record_http_request(
            "POST", f"/experiments/{experiment_id}/pause", status_code, duration
        )

        return response

    except Exception as e:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/experiments/{experiment_id}/pause", 500, duration
        )
        logger.error(f"Error pausing experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@experiment_router.post(
    "/{experiment_id}/complete", response_model=ExperimentActionResponse
)
async def complete_experiment(
    experiment_id: str,
    request: ExperimentActionRequest = ExperimentActionRequest(),
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> ExperimentActionResponse:
    """Complete an experiment and calculate final results."""
    start_time = time.time()

    try:
        success = manager.complete_experiment(experiment_id)

        response = ExperimentActionResponse(
            success=success,
            experiment_id=experiment_id,
            new_status="completed" if success else "unknown",
            message="Experiment completed with statistical analysis"
            if success
            else "Failed to complete experiment",
            timestamp=datetime.now(timezone.utc),
        )

        # Record metrics
        duration = time.time() - start_time
        status_code = 200 if success else 400
        record_http_request(
            "POST", f"/experiments/{experiment_id}/complete", status_code, duration
        )

        return response

    except Exception as e:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/experiments/{experiment_id}/complete", 500, duration
        )
        logger.error(f"Error completing experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@experiment_router.post(
    "/{experiment_id}/assign", response_model=ParticipantAssignmentResponse
)
async def assign_participant(
    experiment_id: str,
    request: ParticipantAssignmentRequest,
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> ParticipantAssignmentResponse:
    """Assign a participant to a variant based on traffic allocation."""
    start_time = time.time()

    try:
        assigned_variant = manager.assign_participant_to_variant(
            experiment_id=experiment_id,
            participant_id=request.participant_id,
            context=request.context,
        )

        success = assigned_variant is not None

        response = ParticipantAssignmentResponse(
            experiment_id=experiment_id,
            participant_id=request.participant_id,
            assigned_variant_id=assigned_variant,
            success=success,
            message=f"Participant assigned to variant {assigned_variant}"
            if success
            else "Assignment failed",
        )

        # Record metrics
        duration = time.time() - start_time
        status_code = 200 if success else 400
        record_http_request(
            "POST", f"/experiments/{experiment_id}/assign", status_code, duration
        )

        return response

    except Exception as e:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/experiments/{experiment_id}/assign", 500, duration
        )
        logger.error(f"Error assigning participant: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@experiment_router.post(
    "/{experiment_id}/track", response_model=EngagementTrackingResponse
)
async def track_engagement(
    experiment_id: str,
    request: EngagementTrackingRequest,
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> EngagementTrackingResponse:
    """Track participant engagement within an experiment."""
    start_time = time.time()

    try:
        success = manager.record_experiment_engagement(
            experiment_id=experiment_id,
            participant_id=request.participant_id,
            variant_id=request.variant_id,
            action_taken=request.action_taken,
            engagement_value=request.engagement_value,
            metadata=request.metadata,
        )

        response = EngagementTrackingResponse(
            success=success,
            experiment_id=experiment_id,
            participant_id=request.participant_id,
            variant_id=request.variant_id,
            message=f"Engagement {request.action_taken} tracked successfully"
            if success
            else "Tracking failed",
        )

        # Record metrics
        duration = time.time() - start_time
        status_code = 200 if success else 400
        record_http_request(
            "POST", f"/experiments/{experiment_id}/track", status_code, duration
        )

        return response

    except Exception as e:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/experiments/{experiment_id}/track", 500, duration
        )
        logger.error(f"Error tracking engagement: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@experiment_router.get(
    "/{experiment_id}/results", response_model=ExperimentResultsResponse
)
async def get_experiment_results(
    experiment_id: str,
    include_segments: bool = Query(False, description="Include segment breakdown"),
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> ExperimentResultsResponse:
    """Get comprehensive experiment results with statistical analysis."""
    start_time = time.time()

    try:
        results = manager.get_experiment_results(experiment_id, include_segments)

        if not results:
            raise HTTPException(status_code=404, detail="Experiment not found")

        # Convert to response format
        variant_performance = {
            variant_id: VariantPerformance(**perf_data)
            for variant_id, perf_data in results.variant_performance.items()
        }

        response = ExperimentResultsResponse(
            experiment_id=results.experiment_id,
            name=results.experiment_id,  # Will be updated with actual name if needed
            status=results.status,
            start_time=results.start_time,
            end_time=results.end_time,
            results_summary=ExperimentResultsSummary(
                total_participants=results.total_participants,
                experiment_duration_days=results.duration_days,
                winner_variant_id=results.winner_variant_id,
                improvement_percentage=results.improvement_percentage,
                is_statistically_significant=results.is_statistically_significant,
                p_value=results.p_value,
            ),
            variant_performance=variant_performance,
            confidence_level=results.confidence_level,
            segment_breakdown=results.segment_breakdown,
        )

        # Record metrics
        duration = time.time() - start_time
        record_http_request(
            "GET", f"/experiments/{experiment_id}/results", 200, duration
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        record_http_request(
            "GET", f"/experiments/{experiment_id}/results", 500, duration
        )
        logger.error(f"Error getting experiment results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@experiment_router.get("/list", response_model=List[ExperimentSummary])
async def list_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
    target_persona: Optional[str] = Query(None, description="Filter by target persona"),
    limit: int = Query(50, description="Maximum number of experiments", le=100),
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> List[ExperimentSummary]:
    """List experiments with optional filtering."""
    start_time = time.time()

    try:
        experiments = manager.list_experiments(
            status=status, target_persona=target_persona, limit=limit
        )

        # Convert to response format
        response = [ExperimentSummary(**exp) for exp in experiments]

        # Record metrics
        duration = time.time() - start_time
        record_http_request("GET", "/experiments/list", 200, duration)

        return response

    except Exception as e:
        duration = time.time() - start_time
        record_http_request("GET", "/experiments/list", 500, duration)
        logger.error(f"Error listing experiments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@experiment_router.get("/active/{persona_id}")
async def get_active_experiments_for_persona(
    persona_id: str,
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> JSONResponse:
    """Get active experiments for a specific persona."""
    start_time = time.time()

    try:
        active_experiments = manager.get_active_experiments_for_persona(persona_id)

        response_content = {
            "persona_id": persona_id,
            "active_experiments": active_experiments,
            "count": len(active_experiments),
        }

        # Record metrics
        duration = time.time() - start_time
        record_http_request("GET", f"/experiments/active/{persona_id}", 200, duration)

        return JSONResponse(content=response_content)

    except Exception as e:
        duration = time.time() - start_time
        record_http_request("GET", f"/experiments/active/{persona_id}", 500, duration)
        logger.error(f"Error getting active experiments for persona {persona_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ── Health Check and System Status ───────────────────────────────────────────


@experiment_router.get("/health")
async def experiment_system_health(
    manager: ExperimentManager = Depends(
        lambda db=Depends(get_db_session): create_experiment_manager(db)
    ),
) -> JSONResponse:
    """Health check for experiment management system."""
    try:
        from services.orchestrator.db.models import Experiment

        # Get system statistics
        total_experiments = manager.db_session.query(Experiment).count()
        active_experiments = (
            manager.db_session.query(Experiment)
            .filter(Experiment.status == ExperimentStatus.ACTIVE.value)
            .count()
        )
        completed_experiments = (
            manager.db_session.query(Experiment)
            .filter(Experiment.status == ExperimentStatus.COMPLETED.value)
            .count()
        )

        health_status = {
            "status": "healthy",
            "database_connected": True,
            "total_experiments": total_experiments,
            "active_experiments": active_experiments,
            "completed_experiments": completed_experiments,
            "message": "Experiment management system operational",
        }

        return JSONResponse(content=health_status)

    except Exception as e:
        logger.error(f"Experiment health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "database_connected": False,
                "message": f"Health check failed: {str(e)}",
            },
            status_code=503,
        )
