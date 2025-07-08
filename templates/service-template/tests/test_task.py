from fastapi.testclient import TestClient

from services.orchestrator.main import app

client = TestClient(app)


def test_post_task():
    payload = {
        "persona_id": "ai-jesus",
        "task_type": "create_post",
        "pain_statement": "no time to write",
        "trend_snippet": "AI agents boom",
    }
    res = client.post("/task", json=payload)
    assert res.status_code == 200
    assert res.json() == {"status": "queued"}
