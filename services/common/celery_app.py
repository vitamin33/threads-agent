"""Celery app configuration for viral metrics service."""

import os
from celery import Celery


def get_celery_app() -> Celery:
    """Get configured Celery app instance."""
    broker_url = os.getenv("RABBITMQ_URL", "amqp://user:pass@rabbitmq:5672//")

    app = Celery("viral_metrics", broker=broker_url, backend="redis://redis:6379/0")

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )

    return app
