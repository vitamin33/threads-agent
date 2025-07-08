# /services/orchestrator/main.py
from celery import Celery
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="orchestrator")

# ───────────────────── Celery broker ──────────────────────
celery = Celery(
    __name__,
    broker="amqp://guest:guest@rabbitmq//",  # later move to env var
    backend="rpc://",  # simple result backend
)


# ───────────────────── Pydantic schema ────────────────────
class CreateTaskRequest(BaseModel):
    persona_id: str = Field(..., examples=["ai-jesus"])
    task_type: str = Field(..., examples=["create_post", "create_reply"])
    pain_statement: str | None = None
    trend_snippet: str | None = None


# ───────────────────── Routes ─────────────────────────────
@app.post("/task")
async def create_task(req: CreateTaskRequest, bg: BackgroundTasks) -> dict[str, str]:
    bg.add_task(celery.send_task, "tasks.queue_post", args=[req.model_dump()])
    return {"status": "queued"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
