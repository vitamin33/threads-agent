# /services/celery_worker/main.py
from __future__ import annotations

import os
import time
from typing import Any, Dict

from celery import Celery, shared_task

BROKER_URL = os.getenv("RABBITMQ_URL", "memory://")  # 🟢 fallback broker
app = Celery("worker", broker=BROKER_URL)

# when the broker is “memory://” Celery still queues tasks unless we
# also switch it to eager mode:
if BROKER_URL == "memory://":
    app.conf.task_always_eager = True  # ⬅ key line


@shared_task(name="tasks.queue_post")  # type: ignore[misc]
def queue_post(payload: Dict[str, Any]) -> None:
    print("📬  received task:", payload, flush=True)
    time.sleep(0.1)
