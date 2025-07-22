# tests/e2e/test_metrics.py
import httpx
import pytest

from .conftest import ORCH_PORT


@pytest.mark.e2e
def test_metrics_endpoint() -> None:
    """Test that the orchestrator metrics endpoint is accessible and returns expected metrics."""
    data = httpx.get(f"http://localhost:{ORCH_PORT}/metrics", timeout=5).text
    assert "# TYPE request_latency_seconds" in data
    assert "# TYPE llm_tokens_total" in data
