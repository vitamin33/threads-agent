# services/orchestrator/viral_metrics_endpoints.py
from __future__ import annotations

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

try:
    from services.viral_engine.viral_coefficient_calculator import (
        ViralCoefficientCalculator,
    )
    # Global calculator instance for tracking stats across requests
    _calculator = ViralCoefficientCalculator()
    VIRAL_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Viral engine not available: {e}")
    _calculator = None
    VIRAL_ENGINE_AVAILABLE = False

viral_metrics_router = APIRouter(prefix="/viral-metrics", tags=["viral-metrics"])


# Pydantic models for request/response
class ViralCoefficientRequest(BaseModel):
    shares: float = Field(ge=0, description="Number of shares (must be >= 0)")
    comments: float = Field(ge=0, description="Number of comments (must be >= 0)")
    views: float = Field(gt=0, description="Number of views (must be > 0)")
    post_id: Optional[str] = Field(None, description="Optional post identifier")
    timestamp: Optional[str] = Field(None, description="Optional timestamp")


class ViralCoefficientResponse(BaseModel):
    viral_coefficient: float
    metadata: Optional[Dict[str, Any]] = None


class BatchViralCoefficientRequest(BaseModel):
    metrics_data: List[Dict[str, float]]
    skip_invalid: bool = Field(
        False, description="Skip invalid entries instead of raising error"
    )


class BatchViralCoefficientResponse(BaseModel):
    results: List[float]


class ViralMetricsStats(BaseModel):
    total_calculations: int
    average_viral_coefficient: float
    min_viral_coefficient: Optional[float]
    max_viral_coefficient: Optional[float]


@viral_metrics_router.post("/calculate", response_model=ViralCoefficientResponse)
async def calculate_viral_coefficient(
    request: ViralCoefficientRequest,
) -> ViralCoefficientResponse:
    """
    Calculate viral coefficient for a single post

    Formula: (Shares + Comments) / Views * 100
    """
    try:
        if request.post_id or request.timestamp:
            # Use metadata version if metadata provided
            result = _calculator.calculate_viral_coefficient_with_metadata(
                shares=request.shares,
                comments=request.comments,
                views=request.views,
                post_id=request.post_id,
                timestamp=request.timestamp,
            )
            return ViralCoefficientResponse(**result)
        else:
            # Use simple version
            viral_coefficient = _calculator.calculate_viral_coefficient(
                shares=request.shares, comments=request.comments, views=request.views
            )
            return ViralCoefficientResponse(viral_coefficient=viral_coefficient)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@viral_metrics_router.post(
    "/batch-calculate", response_model=BatchViralCoefficientResponse
)
async def batch_calculate_viral_coefficients(
    request: BatchViralCoefficientRequest,
) -> BatchViralCoefficientResponse:
    """
    Calculate viral coefficients for multiple posts in batch
    """
    try:
        results = _calculator.batch_calculate_viral_coefficients(
            metrics_data=request.metrics_data, skip_invalid=request.skip_invalid
        )
        return BatchViralCoefficientResponse(results=results)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@viral_metrics_router.get("/stats", response_model=ViralMetricsStats)
async def get_viral_metrics_stats() -> ViralMetricsStats:
    """
    Get statistics about viral coefficient calculations
    """
    stats = _calculator.get_calculation_stats()
    return ViralMetricsStats(**stats)


@viral_metrics_router.delete("/stats")
async def reset_viral_metrics_stats() -> Dict[str, str]:
    """
    Reset viral metrics calculation statistics
    """
    _calculator.reset_calculation_stats()
    return {"status": "stats_reset"}
