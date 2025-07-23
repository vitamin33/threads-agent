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
VIRAL_ENGINE_URL = os.getenv("VIRAL_ENGINE_URL", "http://viral-engine:8080")

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

    start_time = time.time()
    try:
        # 1️⃣  persona-runtime (content generation)
        hook_start = time.time()
        draft = run_persona(PERSONA_RUNTIME_URL, persona, user_input, headers=hdr)
        hook, body = draft["hook"], draft["body"]
        record_content_generation_latency(persona, "hook", time.time() - hook_start)

        # 2️⃣  Viral Engine Pipeline (quality gate + reply magnetizer)
        content = f"{hook}\n\n{body}"
        try:
            pipeline_response = httpx.post(
                f"{VIRAL_ENGINE_URL}/pipeline/process",
                json={
                    "content": content,
                    "persona_id": persona,
                    "enable_hook_optimization": False,  # Already optimized by persona
                    "enable_reply_magnets": True,
                    "metadata": {
                        "task_id": task_id,
                        "task_type": task_type,
                    },
                },
                headers=hdr,
                timeout=10.0,
            )
            pipeline_response.raise_for_status()

            pipeline_result = pipeline_response.json()

            if not pipeline_result["success"]:
                # Content rejected by quality gate
                rejection_reason = pipeline_result.get(
                    "rejection_reason", "Quality below threshold"
                )
                print(f"⚠️  Content rejected by quality gate: {rejection_reason}")
                record_post_generation(persona, "blocked")

                # Could retry with different approach or notify for human review
                return

            # Use enhanced content with reply magnets
            final_content = pipeline_result["final_content"]
            quality_score = pipeline_result["pipeline_stages"]["quality_gate"][
                "quality_score"
            ]

        except Exception as e:
            print(f"⚠️  Viral engine pipeline failed, using original content: {e}")
            final_content = content
            quality_score = None

        # 3️⃣  Postgres (database storage)
        db_start = time.time()
        post_data = {
            "persona_id": persona,
            "hook": hook,
            "body": body,
        }
        if quality_score is not None:
            post_data["quality_score"] = quality_score
        row_id = save_post(post_data)
        record_database_query("insert", "posts", time.time() - db_start)

        # 4️⃣  Qdrant (vector storage)
        collection_name = f"posts_{persona}"
        qdrant_start = time.time()
        upsert_vector(persona, row_id, [0.0] * 128)
        record_qdrant_operation("upsert", collection_name, time.time() - qdrant_start)

        # 5️⃣  Threads stub (publishing)
        topic = f"{persona} – {task_type}"
        _publish_to_threads(topic, final_content, hdr)

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
        update_revenue_projection("current_run_rate", projected_monthly_revenue)

        print(
            f"✅  task {task_id}: stored row {row_id} & published draft",
            flush=True,
        )

        # Record overall task success
        record_celery_task("queue_post", "success", time.time() - start_time)
        record_content_generation_latency(persona, "total", time.time() - start_time)

    except Exception as exc:
        # Record failed post generation and error details
        record_post_generation(persona, "failed")
        record_error("celery_worker", type(exc).__name__, str(exc))
        record_celery_task("queue_post", "failed", time.time() - start_time)

        print(f"❌  task {task_id} failed:", exc, flush=True)
        raise self.retry(exc=exc, countdown=2**self.request.retries)
