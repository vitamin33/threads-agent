# services/celery_worker/main.py
from __future__ import annotations

import os
import time
from typing import Any, Dict

import httpx
from celery import Celery, Task, shared_task

from services.celery_worker.sse import run_persona
from services.celery_worker.store import save_post, upsert_vector
from services.common.metrics import maybe_start_metrics_server

maybe_start_metrics_server()

# ─────────────────────────────── env / globals ───────────────────────────────
BROKER_URL = os.getenv("RABBITMQ_URL", "amqp://user:pass@rabbitmq:5672//")
THREADS_BASE_URL = os.getenv("THREADS_BASE_URL", "http://fake-threads:9009")
PERSONA_RUNTIME_URL = os.getenv("PERSONA_RUNTIME_URL", "http://persona-runtime:8080")
POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN", "postgresql://postgres:pass@postgres:5432/postgres"
)
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

app = Celery("worker", broker=BROKER_URL)


# ───────────────────────────── helpers ───────────────────────────────────────
def _publish_to_threads(topic: str, content: str, hdr: dict[str, str]) -> None:
    """Send the final draft to fake-threads backend."""
    draft = {"topic": topic, "content": content}
    httpx.post(
        f"{THREADS_BASE_URL}/publish",
        json=draft,
        headers=hdr,
        timeout=5,
    ).raise_for_status()


# ─────────────────────────── Celery task ─────────────────────────────────────
@shared_task(name="tasks.queue_post", bind=True, max_retries=3)  # type: ignore[misc]
def queue_post(self: Task, payload: Dict[str, Any]) -> None:  # noqa: ANN401
    task_id = self.request.id or "unknown-id"
    hdr = {"X-Task-Id": task_id}

    persona = payload.get("persona_id", "bot")
    user_input = payload.get("pain_statement") or payload.get("trend_snippet") or ""
    task_type = payload.get("task_type", "post")

    try:
        # 1️⃣  persona-runtime
        draft = run_persona(PERSONA_RUNTIME_URL, persona, user_input, headers=hdr)
        hook, body = draft["hook"], draft["body"]

        # 2️⃣  Postgres
        row_id = save_post(
            {
                "persona_id": persona,
                "hook": hook,
                "body": body,
            }
        )

        # 3️⃣  Qdrant
        upsert_vector(persona, row_id, [0.0] * 128)

        # 4️⃣  Threads stub
        topic = f"{persona} – {task_type}"
        _publish_to_threads(topic, f"{hook}\n\n{body}", hdr)

        print(f"✅  task {task_id}: stored row {row_id} & published draft", flush=True)

    except Exception as exc:
        print(f"❌  task {task_id} failed:", exc, flush=True)
        raise self.retry(exc=exc, countdown=2**self.request.retries)

    time.sleep(0.05)
