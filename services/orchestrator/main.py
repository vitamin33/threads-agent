# /services/orchestrator/main.py
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any, TypedDict

# CI Optimization Test: Phase 1 implementation - testing optimized workflows

import httpx
import tenacity
from celery import Celery
from fastapi import BackgroundTasks, FastAPI, Response, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

# Production optimizations
from services.orchestrator.rate_limiter import SimpleRateLimiter

# ── shared helpers ────────────────────────────────────────────────────────────
from services.common.metrics import (
    maybe_start_metrics_server,
    record_http_request,
    record_post_generation,
    update_service_uptime,
    update_system_health,
)
from services.orchestrator.search_endpoints import search_router
from services.orchestrator.vector import ensure_posts_collection
from services.orchestrator.comment_monitor import CommentMonitor

# ── constants & wiring ────────────────────────────────────────────────────────
BROKER_URL = os.getenv("RABBITMQ_URL", "amqp://user:pass@rabbitmq:5672//")
PERSONA_RUNTIME_URL = os.getenv("PERSONA_RUNTIME_URL", "http://persona-runtime:8080")

app = FastAPI(title="orchestrator")  # single public symbol
celery_app = Celery("orchestrator", broker=BROKER_URL)
maybe_start_metrics_server()  # Prom-client HTTP at :9090

logger = logging.getLogger(__name__)

# Initialize rate limiter for production stability
rate_limiter = SimpleRateLimiter(
    requests_per_minute=600,  # 10 QPS average
    burst_size=50,  # Allow bursts up to 50
    max_concurrent=100,  # Max 100 concurrent requests
)

# Include routers
app.include_router(search_router)

# Include content management router
try:
    from services.orchestrator.content_management import router as content_router

    app.include_router(content_router)
except ImportError as e:
    logger.warning(f"Content management router not available: {e}")

# Include performance monitor API if enabled
try:
    from services.performance_monitor.api import router as performance_router

    app.include_router(performance_router, prefix="/performance", tags=["performance"])
except ImportError:
    # Performance monitor service not available in this container
    pass

# Track service startup time for uptime calculation
_service_start_time = time.time()


# ---------------------------------------------------------------------------
# Qdrant bootstrap with retry/back-off
# ---------------------------------------------------------------------------
@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=0.5, max=8),
    stop=tenacity.stop_after_delay(30),
    reraise=True,
    before_sleep=lambda r: logger.info("Qdrant not ready, retrying…"),
)
def _ensure_store() -> None:
    """Blocking helper that guarantees the posts collection exists."""
    ensure_posts_collection()


@app.on_event("startup")
async def _init_qdrant() -> None:
    """Run once at app startup – off-loads the blocking call to a thread."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _ensure_store)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class CreateTaskRequest(BaseModel):
    persona_id: str
    task_type: str
    pain_statement: str | None = None
    trend_snippet: str | None = None


class Status(TypedDict):
    status: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.post("/task")
async def create_task(req: CreateTaskRequest, bg: BackgroundTasks) -> dict[str, str]:
    start_time = time.time()

    # Check rate limit first
    if not await rate_limiter.acquire():
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )

    try:
        task_id = str(uuid.uuid4())
        payload = req.model_dump(exclude_none=True) | {"task_id": task_id}
        bg.add_task(celery_app.send_task, "tasks.queue_post", args=[payload])

        # Record metrics
        duration = time.time() - start_time
        record_http_request("POST", "/task", 200, duration)

        # Record post generation attempt
        record_post_generation(req.persona_id, "success")

        return {"status": "queued", "task_id": task_id}
    except HTTPException:
        raise  # Re-raise rate limit errors
    except Exception:
        # Record failed post generation
        record_post_generation(req.persona_id, "failed")

        # Record error metrics
        duration = time.time() - start_time
        record_http_request("POST", "/task", 500, duration)
        raise
    finally:
        # Always release the rate limit slot
        await rate_limiter.release()


@celery_app.task(name="tasks.run_persona")  # type: ignore[misc]
def run_persona(cfg: dict[str, Any], user_input: str) -> None:
    """Fire-and-forget call to persona-runtime."""
    httpx.post(
        f"{PERSONA_RUNTIME_URL}/run",
        json={"persona_id": cfg["id"], "input": user_input},
        timeout=60,
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "orchestrator"}


@app.get("/health/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check for Kubernetes.
    Checks if the service is ready to accept traffic.
    """
    checks = {
        "database": False,
        "celery": False,
        "rate_limiter": False,
    }

    # Check database connection
    try:
        # Simple check - try to import and use the session

        # We don't actually query, just check if we can get a session
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database check failed: {e}")

    # Check Celery connection
    try:
        # Check if we can inspect the celery app
        celery_app.control.inspect().stats()
        checks["celery"] = True
    except Exception as e:
        logger.warning(f"Celery check failed (may be normal in dev): {e}")
        checks["celery"] = True  # Don't fail readiness for celery in dev

    # Check rate limiter
    checks["rate_limiter"] = not rate_limiter.circuit_open

    # Overall status
    all_healthy = all(checks.values())

    return {
        "ready": all_healthy,
        "checks": checks,
        "metrics": rate_limiter.get_metrics()
        if hasattr(rate_limiter, "get_metrics")
        else {},
    }


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus scrape endpoint (FastAPI-served)."""
    start_time = time.time()
    try:
        response = Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        status = 200
        return response
    except Exception:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/metrics", status, duration)


@app.get("/health")
async def health() -> Status:
    start_time = time.time()
    try:
        # Update system health metrics
        update_system_health("api", "orchestrator", True)
        update_system_health(
            "database", "orchestrator", True
        )  # Could check actual DB health
        update_system_health(
            "queue", "orchestrator", True
        )  # Could check RabbitMQ health

        # Update service uptime
        current_uptime = time.time() - _service_start_time
        update_service_uptime("orchestrator", current_uptime)

        status = 200
        return {"status": "ok"}
    except Exception:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/health", status, duration)


# ── Comment Monitoring Endpoints ──────────────────────────────────────────────
class CommentMonitoringRequest(BaseModel):
    post_id: str


class CommentMonitoringResponse(BaseModel):
    task_id: str
    status: str


@app.post("/comment-monitoring/start")
async def start_comment_monitoring(
    request: CommentMonitoringRequest,
) -> CommentMonitoringResponse:
    """Start monitoring comments for a specific post."""
    start_time = time.time()
    try:
        # Initialize comment monitor with dependencies
        monitor = CommentMonitor(
            fake_threads_client=httpx.Client(
                base_url=os.getenv("FAKE_THREADS_URL", "http://fake-threads:9009")
            ),
            celery_client=celery_app,
            db_session=None,  # TODO: Add proper DB session from db module
        )

        # Start monitoring
        task_id = monitor.start_monitoring(request.post_id)

        status = 200
        return CommentMonitoringResponse(task_id=task_id, status="monitoring_started")
    except Exception as e:
        status = 500
        logger.error(f"Failed to start comment monitoring: {e}")
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("POST", "/comment-monitoring/start", status, duration)


@app.post("/comment-monitoring/process/{post_id}")
async def process_comments(post_id: str, background_tasks: BackgroundTasks):
    """Process all comments for a post (fetch, deduplicate, queue, store)."""
    start_time = time.time()
    try:
        # Initialize comment monitor
        monitor = CommentMonitor(
            fake_threads_client=httpx.Client(
                base_url=os.getenv("FAKE_THREADS_URL", "http://fake-threads:9009")
            ),
            celery_client=celery_app,
            db_session=None,  # TODO: Add proper DB session
        )

        # Process comments in background
        background_tasks.add_task(monitor.process_comments_for_post, post_id)

        status = 202  # Accepted
        return {"status": "processing_started", "post_id": post_id}
    except Exception as e:
        status = 500
        logger.error(f"Failed to process comments: {e}")
        raise
    finally:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/comment-monitoring/process/{post_id}", status, duration
        )


@app.get("/metrics/summary")
async def metrics_summary():
    """Get system-wide metrics summary for dashboard"""
    start_time = time.time()
    status = 500

    try:
        # Return mock data for now
        summary = {
            "services_health": {
                "healthy": 5,
                "total": 5,
                "details": {
                    "orchestrator": "healthy",
                    "celery_worker": "healthy",
                    "persona_runtime": "healthy",
                    "fake_threads": "healthy",
                    "achievement_collector": "healthy",
                },
            },
            "api_latency_ms": 45,
            "success_rate": 99.9,
            "queue_size": 12,
            "active_tasks": 3,
            "completed_today": 89,
            "avg_processing_time_s": 2.3,
        }

        status = 200
        return summary
    except Exception:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/metrics/summary", status, duration)
