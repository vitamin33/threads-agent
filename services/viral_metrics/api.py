"""
FastAPI endpoints for viral metrics collection service.
Provides real-time metrics access and batch processing capabilities.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from .metrics_collector import ViralMetricsCollector
from .background_processor import ViralMetricsProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/viral-metrics", tags=["viral-metrics"])


# Pydantic models for API requests/responses
class MetricsResponse(BaseModel):
    """Response model for viral metrics."""

    post_id: str
    viral_coefficient: float = Field(
        ..., description="Secondary engagement generation rate"
    )
    scroll_stop_rate: float = Field(
        ..., description="Content stopping power percentage"
    )
    share_velocity: float = Field(..., description="Peak sharing rate per hour")
    reply_depth: float = Field(..., description="Average conversation thread depth")
    engagement_trajectory: float = Field(
        ..., description="Engagement acceleration/deceleration"
    )
    pattern_fatigue: float = Field(..., description="Content pattern freshness score")
    collected_at: datetime


class BatchMetricsRequest(BaseModel):
    """Request model for batch metrics collection."""

    post_ids: List[str] = Field(..., min_items=1, max_items=100)
    timeframe: str = Field(default="1h", pattern="^\\d+[hd]$")


class AnomalyAlert(BaseModel):
    """Model for anomaly alerts."""

    post_id: str
    anomaly_type: str
    severity: str
    message: str
    current_value: float
    baseline_value: Optional[float]


# Initialize collectors lazily
_metrics_collector = None
_batch_processor = None


def get_metrics_collector():
    """Get or create metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = ViralMetricsCollector()
    return _metrics_collector


def get_batch_processor():
    """Get or create batch processor instance."""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = ViralMetricsProcessor()
    return _batch_processor


@router.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {
        "status": "healthy",
        "service": "viral-metrics",
        "timestamp": datetime.utcnow(),
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    try:
        # Check if we can access cache and database
        await get_metrics_collector().get_cached_metrics("test_post")
        return {"status": "ready", "cache": "connected", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/metrics/{post_id}", response_model=MetricsResponse)
async def get_post_metrics(
    post_id: str,
    timeframe: str = Query(default="1h", pattern="^\\d+[hd]$"),
    use_cache: bool = Query(default=True),
):
    """
    Get viral metrics for a specific post.

    Args:
        post_id: Unique post identifier
        timeframe: Time window for metrics (e.g., "1h", "3h", "24h")
        use_cache: Whether to use cached metrics if available
    """
    try:
        # Try cache first if enabled
        if use_cache:
            cached_metrics = await get_metrics_collector().get_cached_metrics(post_id)
            if cached_metrics:
                logger.info(f"Returning cached metrics for post {post_id}")
                return MetricsResponse(
                    post_id=post_id, collected_at=datetime.utcnow(), **cached_metrics
                )

        # Collect fresh metrics
        metrics = await get_metrics_collector().collect_viral_metrics(
            post_id, timeframe
        )

        return MetricsResponse(
            post_id=post_id, collected_at=datetime.utcnow(), **metrics
        )

    except Exception as e:
        logger.error(f"Failed to get metrics for post {post_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to collect metrics: {str(e)}"
        )


@router.post("/metrics/batch", response_model=List[MetricsResponse])
async def collect_batch_metrics(
    request: BatchMetricsRequest, background_tasks: BackgroundTasks
):
    """
    Collect metrics for multiple posts in batch.

    Processes requests asynchronously and returns results.
    """
    try:
        results = []

        # Process each post
        for post_id in request.post_ids:
            try:
                metrics = await get_metrics_collector().collect_viral_metrics(
                    post_id, request.timeframe
                )
                results.append(
                    MetricsResponse(
                        post_id=post_id, collected_at=datetime.utcnow(), **metrics
                    )
                )
            except Exception as e:
                logger.error(f"Failed to collect metrics for post {post_id}: {e}")
                # Continue with other posts

        return results

    except Exception as e:
        logger.error(f"Batch metrics collection failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Batch processing failed: {str(e)}"
        )


@router.post("/process-active-posts")
async def trigger_active_posts_processing(
    background_tasks: BackgroundTasks, batch_size: int = Query(default=50, ge=1, le=200)
):
    """
    Trigger background processing of active posts.

    This endpoint initiates async processing of posts from the last 24 hours.
    """
    try:
        # Add to background tasks for async processing
        background_tasks.add_task(
            get_batch_processor().process_active_posts, batch_size=batch_size
        )

        return {
            "status": "processing_started",
            "batch_size": batch_size,
            "timestamp": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Failed to trigger batch processing: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start processing: {str(e)}"
        )


@router.get("/anomalies", response_model=List[AnomalyAlert])
async def get_recent_anomalies(
    hours: int = Query(default=24, ge=1, le=168),
    severity: Optional[str] = Query(default=None, regex="^(high|medium|low)$"),
):
    """
    Get recent viral metrics anomalies.

    Args:
        hours: Number of hours to look back (max 7 days)
        severity: Filter by severity level
    """
    try:
        # This would query the database for recent anomalies
        # For now, return empty list
        return []

    except Exception as e:
        logger.error(f"Failed to fetch anomalies: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch anomalies: {str(e)}"
        )


@router.get("/stats/summary")
async def get_metrics_summary(
    persona_id: Optional[str] = None, hours: int = Query(default=24, ge=1, le=168)
):
    """
    Get summary statistics for viral metrics.

    Returns aggregated metrics across posts for analysis.
    """
    try:
        # This would aggregate metrics from the database
        # For now, return mock summary
        return {
            "time_period_hours": hours,
            "persona_id": persona_id,
            "metrics_summary": {
                "avg_viral_coefficient": 12.5,
                "avg_scroll_stop_rate": 65.3,
                "avg_share_velocity": 35.2,
                "total_posts_analyzed": 0,
                "high_performers": 0,
                "anomalies_detected": 0,
            },
            "timestamp": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate summary: {str(e)}"
        )


@router.get("/patterns/fatigue")
async def get_pattern_fatigue_report(
    persona_id: Optional[str] = None,
    threshold: float = Query(default=0.8, ge=0.0, le=1.0),
):
    """
    Get content patterns showing high fatigue scores.

    Helps identify overused patterns that need refreshing.
    """
    try:
        # This would query pattern usage history
        # For now, return empty report
        return {
            "persona_id": persona_id,
            "fatigue_threshold": threshold,
            "fatigued_patterns": [],
            "recommendations": ["No patterns currently showing high fatigue"],
            "timestamp": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Failed to generate fatigue report: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}"
        )


# Prometheus metrics endpoint would be handled by the metrics server on port 9090
# The actual metrics are exposed via prometheus_client in the metrics_collector
