# services/celery_worker/tests/test_task.py
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from services.orchestrator.main import app

client = TestClient(app)


def test_post_task() -> None:
    """Route should enqueue exactly one Celery job with a generated task_id."""

    base_payload = {"persona_id": "ai-jesus", "task_type": "create_post"}

    # patch out the real Celery call so we don't touch AMQP
    with patch("services.orchestrator.main.celery_app.send_task") as stub:
        stub.return_value = None
        res = client.post("/task", json=base_payload)

    # 1️⃣ called exactly once …
    stub.assert_called_once()

    # 2️⃣ …with our payload *plus* an auto-injected UUID
    sent_payload = stub.call_args.kwargs["args"][0]  # first (and only) arg
    assert sent_payload["persona_id"] == "ai-jesus"
    assert sent_payload["task_type"] == "create_post"
    assert "task_id" in sent_payload and sent_payload["task_id"]

    # 3️⃣ HTTP response includes status and task_id
    assert res.status_code == 200
    response_data = res.json()
    assert response_data["status"] == "queued"
    assert "task_id" in response_data
    assert response_data["task_id"] == sent_payload["task_id"]
