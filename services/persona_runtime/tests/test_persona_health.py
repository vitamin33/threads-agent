# /templates/service-template/tests/test_health.py
from fastapi.testclient import TestClient

from services.persona_runtime.main import app

cli = TestClient(app)


def test_health() -> None:
    res = cli.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
