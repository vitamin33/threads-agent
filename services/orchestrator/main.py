# /services/orchestrator/main.py
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any, TypedDict

import httpx
import tenacity
from celery import Celery
from fastapi import BackgroundTasks, FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

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

# ── constants & wiring ────────────────────────────────────────────────────────
BROKER_URL = os.getenv("RABBITMQ_URL", "amqp://user:pass@rabbitmq:5672//")
PERSONA_RUNTIME_URL = os.getenv("PERSONA_RUNTIME_URL", "http://persona-runtime:8080")

app = FastAPI(title="orchestrator")  # single public symbol
celery_app = Celery("orchestrator", broker=BROKER_URL)
maybe_start_metrics_server()  # Prom-client HTTP at :9090

logger = logging.getLogger(__name__)

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
    except Exception:
        # Record failed post generation
        record_post_generation(req.persona_id, "failed")

        # Record error metrics
        duration = time.time() - start_time
        record_http_request("POST", "/task", 500, duration)
        raise


@celery_app.task(name="tasks.run_persona")  # type: ignore[misc]
def run_persona(cfg: dict[str, Any], user_input: str) -> None:
    """Fire-and-forget call to persona-runtime."""
    httpx.post(
        f"{PERSONA_RUNTIME_URL}/run",
        json={"persona_id": cfg["id"], "input": user_input},
        timeout=60,
    )


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
                    "achievement_collector": "healthy"
                }
            },
            "api_latency_ms": 45,
            "success_rate": 99.9,
            "queue_size": 12,
            "active_tasks": 3,
            "completed_today": 89,
            "avg_processing_time_s": 2.3
        }
        
        status = 200
        return summary
    except Exception:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/metrics/summary", status, duration)
