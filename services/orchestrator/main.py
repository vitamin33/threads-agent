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
from services.orchestrator.vector import ensure_posts_collection

# ── constants & wiring ────────────────────────────────────────────────────────
BROKER_URL = os.getenv("RABBITMQ_URL", "amqp://user:pass@rabbitmq:5672//")
PERSONA_RUNTIME_URL = os.getenv("PERSONA_RUNTIME_URL", "http://persona-runtime:8080")

app = FastAPI(title="orchestrator")  # single public symbol
celery_app = Celery("orchestrator", broker=BROKER_URL)
maybe_start_metrics_server()  # Prom-client HTTP at :9090

logger = logging.getLogger(__name__)

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
async def create_task(req: CreateTaskRequest, bg: BackgroundTasks) -> Status:
    with record_http_request("orchestrator", "POST", "/task"):
        try:
            payload = req.model_dump(exclude_none=True) | {"task_id": str(uuid.uuid4())}
            bg.add_task(celery_app.send_task, "tasks.queue_post", args=[payload])

            # Record post generation attempt
            record_post_generation(req.persona_id, "success")

            return {"status": "queued"}
        except Exception:
            # Record failed post generation
            record_post_generation(req.persona_id, "failed")
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
    with record_http_request("orchestrator", "GET", "/metrics"):
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health() -> Status:
    with record_http_request("orchestrator", "GET", "/health"):
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

        return {"status": "ok"}
