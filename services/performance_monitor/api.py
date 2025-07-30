"""API endpoints for performance monitoring service."""
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.performance_monitor.models import VariantMonitoring
from services.performance_monitor.tasks import start_monitoring_task

app = FastAPI(title="Performance Monitor Service", version="0.1.0")
router = APIRouter(prefix="/performance-monitor", tags=["performance-monitor"])


class StartMonitoringRequest(BaseModel):
    """Request to start monitoring a variant."""
    variant_id: str
    persona_id: str
    post_id: str
    expected_engagement_rate: float


class MonitoringStatus(BaseModel):
    """Status of a monitoring session."""
    variant_id: str
    persona_id: str
    is_active: bool
    started_at: datetime
    ended_at: Optional[datetime]
    was_killed: bool
    kill_reason: Optional[str]
    final_engagement_rate: Optional[float]
    final_interaction_count: Optional[int]


def get_db():
    """Import get_db from main module."""
    from services.performance_monitor.main import get_db as _get_db
    return _get_db()


@router.post("/start-monitoring")
async def start_monitoring(
    request: StartMonitoringRequest,
    db: Session = Depends(get_db)
) -> dict:
    """Start monitoring a variant for early kill decisions."""
    # Check if already monitoring
    existing = db.query(VariantMonitoring).filter_by(
        variant_id=request.variant_id,
        is_active=True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Already monitoring variant {request.variant_id}"
        )
    
    # Start monitoring task
    result = start_monitoring_task.delay(
        variant_id=request.variant_id,
        persona_id=request.persona_id,
        post_id=request.post_id,
        expected_engagement_rate=request.expected_engagement_rate
    )
    
    return {
        "status": "monitoring_started",
        "task_id": result.id,
        "variant_id": request.variant_id
    }


@router.get("/status/{variant_id}")
async def get_monitoring_status(
    variant_id: str,
    db: Session = Depends(get_db)
) -> MonitoringStatus:
    """Get the status of a monitoring session."""
    monitoring = db.query(VariantMonitoring).filter_by(
        variant_id=variant_id
    ).order_by(VariantMonitoring.created_at.desc()).first()
    
    if not monitoring:
        raise HTTPException(
            status_code=404,
            detail=f"No monitoring found for variant {variant_id}"
        )
    
    return MonitoringStatus(
        variant_id=monitoring.variant_id,
        persona_id=monitoring.persona_id,
        is_active=monitoring.is_active,
        started_at=monitoring.started_at,
        ended_at=monitoring.ended_at,
        was_killed=monitoring.was_killed,
        kill_reason=monitoring.kill_reason,
        final_engagement_rate=monitoring.final_engagement_rate,
        final_interaction_count=monitoring.final_interaction_count
    )


@router.get("/active")
async def get_active_monitoring(
    db: Session = Depends(get_db)
) -> List[MonitoringStatus]:
    """Get all active monitoring sessions."""
    active_sessions = db.query(VariantMonitoring).filter_by(
        is_active=True
    ).all()
    
    return [
        MonitoringStatus(
            variant_id=m.variant_id,
            persona_id=m.persona_id,
            is_active=m.is_active,
            started_at=m.started_at,
            ended_at=m.ended_at,
            was_killed=m.was_killed,
            kill_reason=m.kill_reason,
            final_engagement_rate=m.final_engagement_rate,
            final_interaction_count=m.final_interaction_count
        )
        for m in active_sessions
    ]


@router.post("/stop/{variant_id}")
async def stop_monitoring(
    variant_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Manually stop monitoring a variant."""
    monitoring = db.query(VariantMonitoring).filter_by(
        variant_id=variant_id,
        is_active=True
    ).first()
    
    if not monitoring:
        raise HTTPException(
            status_code=404,
            detail=f"No active monitoring for variant {variant_id}"
        )
    
    monitoring.is_active = False
    monitoring.ended_at = datetime.utcnow()
    monitoring.kill_reason = "Manually stopped"
    db.commit()
    
    return {
        "status": "monitoring_stopped",
        "variant_id": variant_id
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {"status": "healthy", "service": "performance-monitor"}


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # TODO: Implement actual Prometheus metrics
    return {"metrics": "prometheus_metrics_placeholder"}


# Include router
app.include_router(router)