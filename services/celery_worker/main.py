# services/celery_worker/main.py
from __future__ import annotations

import os
import time
from typing import Any, Dict

import httpx
from celery import Celery, shared_task

BROKER_URL = os.getenv("RABBITMQ_URL", "amqp://user:pass@rabbitmq:5672//")
THREADS_BASE_URL = os.getenv("THREADS_BASE_URL", "http://fake-threads:9009")

app = Celery("worker", broker=BROKER_URL)


@shared_task(name="tasks.queue_post")  # type: ignore[misc]
def queue_post(payload: Dict[str, Any]) -> None:
    """Store a draft post in fake-threads so GET /published can fetch it."""
    print("📬  received task:", payload, flush=True)

    # must be topic + content  (not "body")          ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
    draft = {
        "topic": f"{payload.get('persona_id', 'bot')} – {payload.get('task_type', 'post')}",
        "content": "hello from celery-worker 👋",
    }

    try:
        resp = httpx.post(f"{THREADS_BASE_URL}/publish", json=draft, timeout=5)
        resp.raise_for_status()
        print("✅  stored draft, id:", resp.json().get("id"), flush=True)
    except Exception as exc:
        print("❌  failed saving draft:", exc, flush=True)

    time.sleep(0.1)
