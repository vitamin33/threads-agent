from __future__ import annotations

import os
from typing import Any, TypedDict

import httpx
from celery import Celery
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field

# ── qdrant bootstrap
from services.orchestrator.vector import ensure_posts_collection

BROKER_URL = os.getenv("RABBITMQ_URL", "amqp://user:pass@rabbitmq:5672//")
PERSONA_RUNTIME_URL = os.getenv("PERSONA_RUNTIME_URL", "http://persona-runtime:8080")

# ── fastapi ─────────────────────────────────────────────────────────
app = FastAPI(title="orchestrator")  # single public symbol

# ── Celery app *local to this service* ──────────────────────────────
celery_app = Celery("orchestrator", broker=BROKER_URL)


# This runs exactly once when Uvicorn imports the module,
# before any Celery task can hit the DB / vector store.
@app.on_event("startup")
async def _init_qdrant() -> None:
    ensure_posts_collection()


# ---------- pydantic -----------------
class CreateTaskRequest(BaseModel):
    persona_id: str = Field(..., examples=["ai-jesus"])
    task_type: str = Field(..., examples=["create_post", "create_reply"])
    pain_statement: str | None = None
    trend_snippet: str | None = None


class Status(TypedDict):
    status: str


# ---------- routes -------------------
@app.post("/task")
async def create_task(req: CreateTaskRequest, bg: BackgroundTasks) -> Status:
    bg.add_task(
        celery_app.send_task,
        "tasks.queue_post",
        args=[req.model_dump(exclude_none=True)],
    )
    return {"status": "queued"}


@celery_app.task(name="tasks.run_persona")  # type: ignore[misc]
def run_persona(cfg: dict[str, Any], user_input: str) -> None:
    """Fire-and-forget call to persona-runtime."""
    httpx.post(
        f"{PERSONA_RUNTIME_URL}/run",
        json={"persona_id": cfg["id"], "input": user_input},
        timeout=10,
    )


@app.get("/health")
async def health() -> Status:
    return {"status": "ok"}
