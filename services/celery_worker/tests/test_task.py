# services/celery_worker/tests/test_task.py
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.orchestrator.main import app

client = TestClient(app)


def test_post_task() -> None:
    payload = {"persona_id": "ai-jesus", "task_type": "create_post"}

    with patch("services.orchestrator.main.celery_app.send_task") as stub:
        stub.return_value = None  # don't actually hit AMQP
        res = client.post("/task", json=payload)

    stub.assert_called_once_with("tasks.queue_post", args=[payload])
    assert res.status_code == 200
    assert res.json() == {"status": "queued"}
