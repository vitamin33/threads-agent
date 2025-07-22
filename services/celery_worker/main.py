# services/celery_worker/main.py
from __future__ import annotations

import os
import time
from typing import Any, Dict

import httpx
from celery import Celery, Task, shared_task

from services.celery_worker.sse import run_persona
from services.celery_worker.store import save_post, upsert_vector
from services.common.metrics import (
    maybe_start_metrics_server,
    record_business_metric,
    record_celery_task,
    record_content_generation_latency,
    record_database_query,
    record_error,
    record_post_generation,
    record_qdrant_operation,
    update_cost_per_post,
    update_revenue_projection,
)

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

    with record_celery_task("tasks.queue_post"):
        with record_business_metric("post_generation"):
            with record_content_generation_latency(persona, "total"):
                try:
                    # 1️⃣  persona-runtime (content generation)
                    with record_content_generation_latency(persona, "hook"):
                        draft = run_persona(
                            PERSONA_RUNTIME_URL, persona, user_input, headers=hdr
                        )
                        hook, body = draft["hook"], draft["body"]

                    # 2️⃣  Postgres (database storage)
                    with record_database_query("postgres", "insert"):
                        row_id = save_post(
                            {
                                "persona_id": persona,
                                "hook": hook,
                                "body": body,
                            }
                        )

                    # 3️⃣  Qdrant (vector storage)
                    collection_name = f"posts_{persona}"
                    with record_qdrant_operation("upsert", collection_name):
                        upsert_vector(persona, row_id, [0.0] * 128)

                    # 4️⃣  Threads stub (publishing)
                    topic = f"{persona} – {task_type}"
                    _publish_to_threads(topic, f"{hook}\n\n{body}", hdr)

                    # Record successful post generation
                    record_post_generation(persona, "success")

                    # Estimate cost per post (simplified - could be enhanced)
                    estimated_cost = 0.015  # $0.015 estimated per post
                    update_cost_per_post(persona, estimated_cost)

                    # Update revenue projection based on successful posts
                    # Simple projection: posts * engagement * conversion rate * value
                    estimated_monthly_posts = 300  # rough estimate
                    estimated_engagement_rate = 0.06  # 6% target
                    estimated_conversion_rate = 0.02  # 2% conversion to revenue
                    estimated_value_per_conversion = 50.0  # $50 per conversion
                    projected_monthly_revenue = (
                        estimated_monthly_posts
                        * estimated_engagement_rate
                        * estimated_conversion_rate
                        * estimated_value_per_conversion
                    )
                    update_revenue_projection(
                        "current_run_rate", projected_monthly_revenue
                    )

                    print(
                        f"✅  task {task_id}: stored row {row_id} & published draft",
                        flush=True,
                    )

                except Exception as exc:
                    # Record failed post generation and error details
                    record_post_generation(persona, "failed")
                    record_error("celery_worker", type(exc).__name__, "error")

                    print(f"❌  task {task_id} failed:", exc, flush=True)
                    raise self.retry(exc=exc, countdown=2**self.request.retries)

    time.sleep(0.05)
