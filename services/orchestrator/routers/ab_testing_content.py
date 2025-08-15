"""
A/B Testing Content Generation API Endpoints

These endpoints integrate A/B testing with content generation,
providing optimized content configurations and performance tracking.
"""

import logging
import time
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.orchestrator.db import get_db_session
from services.orchestrator.ab_testing_integration import (
    ABTestingContentOptimizer,
    ContentGenerationIntegration,
    get_ab_testing_optimizer,
)
from services.orchestrator.variant_generator import initialize_default_variants
from services.common.metrics import record_http_request

logger = logging.getLogger(__name__)

# Create router for A/B testing content optimization
ab_content_router = APIRouter(prefix="/ab-content", tags=["ab_testing_content"])


# ── Pydantic Models ──────────────────────────────────────────────────────────


class ContentRequest(BaseModel):
    """Request for optimized content generation."""

    persona_id: str = Field(..., description="ID of the persona generating content")
    content_type: str = Field(default="post", description="Type of content to generate")
    input_text: str = Field(
        ..., description="Input text or topic for content generation"
    )
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class OptimalConfigResponse(BaseModel):
    """Response containing optimal content configuration."""

    variant_id: str = Field(..., description="Selected variant ID")
    dimensions: Dict[str, str] = Field(..., description="Optimal content dimensions")
    performance: Dict[str, Any] = Field(..., description="Variant performance data")
    instructions: Dict[str, str] = Field(..., description="Generation instructions")
    selection_metadata: Dict[str, Any] = Field(..., description="Selection metadata")


class TrackingRequest(BaseModel):
    """Request for tracking content performance."""

    variant_id: str = Field(..., description="Variant ID to track")
    persona_id: str = Field(..., description="Persona ID that generated the content")
    action_type: str = Field(..., description="Type of action (impression, engagement)")
    engagement_type: Optional[str] = Field(None, description="Type of engagement")
    engagement_value: Optional[float] = Field(1.0, description="Value of engagement")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TrackingResponse(BaseModel):
    """Response for tracking requests."""

    success: bool = Field(..., description="Whether tracking was successful")
    variant_id: str = Field(..., description="Variant ID that was tracked")
    message: str = Field(..., description="Status message")


class PerformanceInsight(BaseModel):
    """Performance insight for a variant."""

    variant_id: str
    dimensions: Dict[str, str]
    success_rate: float
    total_impressions: int


class DimensionRecommendation(BaseModel):
    """Recommendation for a content dimension."""

    recommended_value: str
    success_rate: float
    total_impressions: int


class InsightsResponse(BaseModel):
    """Response containing performance insights."""

    top_performing_variants: List[PerformanceInsight]
    dimension_recommendations: Dict[str, DimensionRecommendation]
    total_variants_analyzed: int
    variants_with_data: int


class VariantGenerationRequest(BaseModel):
    """Request for generating new variants."""

    dimensions: Optional[Dict[str, List[str]]] = Field(
        None, description="Custom dimensions"
    )
    max_variants: int = Field(50, description="Maximum variants to generate")
    include_bootstrap: bool = Field(
        True, description="Include bootstrap performance data"
    )


class VariantGenerationResponse(BaseModel):
    """Response for variant generation."""

    variants_created: int
    variants_skipped: int
    total_variants: int
    message: str


# ── API Endpoints ─────────────────────────────────────────────────────────────


@ab_content_router.post("/optimize", response_model=OptimalConfigResponse)
async def get_optimal_content_config(
    request: ContentRequest,
    optimizer: ABTestingContentOptimizer = Depends(get_ab_testing_optimizer),
) -> OptimalConfigResponse:
    """
    Get optimal content configuration using Thompson Sampling A/B testing.

    This endpoint selects the best performing content dimensions for a given
    persona based on historical performance data and Thompson Sampling algorithm.
    """
    start_time = time.time()

    try:
        # Get optimal configuration
        config = await optimizer.get_optimal_content_config(
            persona_id=request.persona_id,
            content_type=request.content_type,
            context=request.context,
        )

        # Create integration layer for instruction generation
        integration = ContentGenerationIntegration()

        # Generate specific instructions based on dimensions
        instructions = {}
        dimensions = config["dimensions"]

        if "hook_style" in dimensions:
            instructions["hook"] = integration._get_hook_instructions(
                dimensions["hook_style"]
            )

        if "tone" in dimensions:
            instructions["tone"] = integration._get_tone_instructions(
                dimensions["tone"]
            )

        if "length" in dimensions:
            instructions["length"] = integration._get_length_instructions(
                dimensions["length"]
            )

        # Prepare response
        response = OptimalConfigResponse(
            variant_id=config["variant_id"],
            dimensions=config["dimensions"],
            performance=config["performance"],
            instructions=instructions,
            selection_metadata={
                "persona_id": request.persona_id,
                "content_type": request.content_type,
                "selection_timestamp": config["selection_timestamp"],
                "algorithm": "thompson_sampling_exploration",
            },
        )

        # Record metrics
        duration = time.time() - start_time
        record_http_request("POST", "/ab-content/optimize", 200, duration)

        return response

    except Exception as e:
        duration = time.time() - start_time
        record_http_request("POST", "/ab-content/optimize", 500, duration)
        logger.error(f"Error getting optimal content config: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while optimizing content configuration",
        )


@ab_content_router.post("/track", response_model=TrackingResponse)
async def track_content_performance(
    request: TrackingRequest,
    optimizer: ABTestingContentOptimizer = Depends(get_ab_testing_optimizer),
) -> TrackingResponse:
    """
    Track content performance for A/B testing optimization.

    Records impressions and engagements to update variant performance
    data used by Thompson Sampling algorithm.
    """
    start_time = time.time()

    try:
        success = False

        if request.action_type == "impression":
            success = await optimizer.track_content_impression(
                variant_id=request.variant_id,
                persona_id=request.persona_id,
                content_metadata=request.metadata,
            )

        elif request.action_type == "engagement":
            if not request.engagement_type:
                raise HTTPException(
                    status_code=400,
                    detail="engagement_type is required for engagement tracking",
                )

            success = await optimizer.track_content_engagement(
                variant_id=request.variant_id,
                persona_id=request.persona_id,
                engagement_type=request.engagement_type,
                engagement_value=request.engagement_value or 1.0,
                content_metadata=request.metadata,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action_type: {request.action_type}. Must be 'impression' or 'engagement'",
            )

        response = TrackingResponse(
            success=success,
            variant_id=request.variant_id,
            message=f"Successfully tracked {request.action_type}"
            if success
            else "Tracking failed",
        )

        # Record metrics
        duration = time.time() - start_time
        status_code = 200 if success else 500
        record_http_request("POST", "/ab-content/track", status_code, duration)

        return response

    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        record_http_request("POST", "/ab-content/track", 500, duration)
        logger.error(f"Error tracking content performance: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while tracking performance"
        )


@ab_content_router.get("/insights", response_model=InsightsResponse)
async def get_performance_insights(
    persona_id: Optional[str] = None,
    limit: int = 10,
    optimizer: ABTestingContentOptimizer = Depends(get_ab_testing_optimizer),
) -> InsightsResponse:
    """
    Get performance insights and recommendations for content optimization.

    Analyzes variant performance data to provide actionable insights
    for improving content generation strategies.
    """
    start_time = time.time()

    try:
        insights = await optimizer.get_performance_insights(
            persona_id=persona_id, limit=limit
        )

        if "error" in insights:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating insights: {insights['error']}",
            )

        # Convert insights to response format
        top_variants = [
            PerformanceInsight(**variant)
            for variant in insights.get("top_performing_variants", [])
        ]

        recommendations = {
            dim_name: DimensionRecommendation(**rec_data)
            for dim_name, rec_data in insights.get(
                "dimension_recommendations", {}
            ).items()
        }

        response = InsightsResponse(
            top_performing_variants=top_variants,
            dimension_recommendations=recommendations,
            total_variants_analyzed=insights.get("total_variants_analyzed", 0),
            variants_with_data=insights.get("variants_with_data", 0),
        )

        # Record metrics
        duration = time.time() - start_time
        record_http_request("GET", "/ab-content/insights", 200, duration)

        return response

    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        record_http_request("GET", "/ab-content/insights", 500, duration)
        logger.error(f"Error getting performance insights: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while generating insights"
        )


@ab_content_router.post("/variants/generate", response_model=VariantGenerationResponse)
async def generate_variants(
    request: VariantGenerationRequest, db: Session = Depends(get_db_session)
) -> VariantGenerationResponse:
    """
    Generate new content variants for A/B testing.

    Creates variants based on dimensional combinations and seeds them
    into the database for Thompson Sampling optimization.
    """
    start_time = time.time()

    try:
        from services.orchestrator.variant_generator import VariantGenerator

        generator = VariantGenerator(db)

        # Generate variants
        if request.dimensions:
            variants = generator.generate_all_variants(
                custom_dimensions=request.dimensions, max_variants=request.max_variants
            )
        else:
            variants = generator.generate_all_variants(
                max_variants=request.max_variants
            )

        # Seed database
        created_variants = generator.seed_database_variants(
            variants=variants, include_bootstrap_data=request.include_bootstrap
        )

        # Count results
        variants_created = len(created_variants)
        variants_skipped = len(variants) - variants_created

        # Get total variant count
        from services.orchestrator.db.models import VariantPerformance

        total_variants = db.query(VariantPerformance).count()

        response = VariantGenerationResponse(
            variants_created=variants_created,
            variants_skipped=variants_skipped,
            total_variants=total_variants,
            message=f"Successfully generated {variants_created} variants, {variants_skipped} skipped",
        )

        # Record metrics
        duration = time.time() - start_time
        record_http_request("POST", "/ab-content/variants/generate", 201, duration)

        return response

    except Exception as e:
        duration = time.time() - start_time
        record_http_request("POST", "/ab-content/variants/generate", 500, duration)
        logger.error(f"Error generating variants: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while generating variants"
        )


@ab_content_router.post("/variants/initialize")
async def initialize_variants(db: Session = Depends(get_db_session)) -> JSONResponse:
    """
    Initialize the database with default high-performing variants.

    This endpoint should be called during system setup to ensure
    variants are available for Thompson Sampling optimization.
    """
    start_time = time.time()

    try:
        success = initialize_default_variants(db)

        if success:
            from services.orchestrator.db.models import VariantPerformance

            total_variants = db.query(VariantPerformance).count()

            response_content = {
                "success": True,
                "message": f"Successfully initialized variants. Total: {total_variants}",
                "total_variants": total_variants,
            }
            status_code = 200
        else:
            response_content = {
                "success": False,
                "message": "Failed to initialize variants",
                "total_variants": 0,
            }
            status_code = 500

        # Record metrics
        duration = time.time() - start_time
        record_http_request(
            "POST", "/ab-content/variants/initialize", status_code, duration
        )

        return JSONResponse(content=response_content, status_code=status_code)

    except Exception as e:
        duration = time.time() - start_time
        record_http_request("POST", "/ab-content/variants/initialize", 500, duration)
        logger.error(f"Error initializing variants: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while initializing variants"
        )


# ── Health Check ──────────────────────────────────────────────────────────────


@ab_content_router.get("/health")
async def health_check(db: Session = Depends(get_db_session)) -> JSONResponse:
    """Health check for A/B testing content optimization system."""
    try:
        from services.orchestrator.db.models import VariantPerformance

        # Check database connectivity
        variant_count = db.query(VariantPerformance).count()

        # Check if we have variants available
        has_variants = variant_count > 0

        # Check if we have performance data
        variants_with_data = (
            db.query(VariantPerformance)
            .filter(VariantPerformance.impressions > 0)
            .count()
        )

        health_status = {
            "status": "healthy" if has_variants else "warning",
            "variant_count": variant_count,
            "variants_with_data": variants_with_data,
            "database_connected": True,
            "message": "A/B testing content optimization system is operational",
        }

        if not has_variants:
            health_status["message"] = (
                "No variants available - initialize variants first"
            )

        return JSONResponse(content=health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "database_connected": False,
                "message": f"Health check failed: {str(e)}",
            },
            status_code=503,
        )
