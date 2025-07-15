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
    # first non-empty SSE line → `data:{"draft":{…}}\n\n`
    chunk = next(res.iter_lines())

    assert chunk.startswith("data:")
    # quick sanity: make sure both parts are present in the JSON
    assert '"hook"' in chunk and '"body"' in chunk
