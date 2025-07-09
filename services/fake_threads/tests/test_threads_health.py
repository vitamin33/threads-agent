# /services/fake_threads/tests/test_health.py
from fastapi.testclient import TestClient

# import from the repo path (not the site-packages copy)
from services.fake_threads.main import app

client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
