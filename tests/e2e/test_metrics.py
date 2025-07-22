# tests/e2e/test_metrics.py
import httpx
import pytest


@pytest.mark.e2e
def test_metrics_endpoint() -> None:
    data = httpx.get("http://localhost:8080/metrics", timeout=5).text
    assert "# TYPE request_latency_seconds" in data
    assert "# TYPE llm_tokens_total" in data
