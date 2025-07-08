# /services/orchestrator/main.py
from __future__ import annotations

import os

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field

from services.celery_worker.main import app as celery_app

BROKER_URL = os.getenv("RABBITMQ_URL", "amqp://user:pass@rabbitmq:5672//")

api = FastAPI(title="orchestrator")  # 🟢 keep the clearer name
app = api  # 👈 public alias for tests & uvicorn


class CreateTaskRequest(BaseModel):
    persona_id: str = Field(..., examples=["ai-jesus"])
    task_type: str = Field(..., examples=["create_post", "create_reply"])
    pain_statement: str | None = None
    trend_snippet: str | None = None


@api.post("/task")
async def create_task(req: CreateTaskRequest, bg: BackgroundTasks) -> dict[str, str]:
    bg.add_task(
        celery_app.send_task,
        "tasks.queue_post",
        args=[req.model_dump(exclude_none=True)],
    )
    return {"status": "queued"}


@api.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
