# /services/persona_runtime/tests/test_run.py
from fastapi.testclient import TestClient

from services.persona_runtime.main import app

cli = TestClient(app)


def test_run_flow() -> None:
    res = cli.post(
        "/run",
        json={"persona_id": "ai-jesus", "input": "Love everyone"},
        headers={"accept": "text/event-stream"},
    )
    # should stream; grab first chunk
    chunk = next(res.iter_lines())
    assert "LOVE EVERYONE" in chunk
