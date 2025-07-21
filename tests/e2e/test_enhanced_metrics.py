# tests/e2e/test_enhanced_metrics.py
"""E2E tests for CRA-216 enhanced Prometheus metrics."""

from __future__ import annotations

import subprocess
import time
from typing import Iterator

import httpx
import pytest

pytestmark = pytest.mark.e2e

ORCH_PORT = 8080
THREADS_PORT = 9009


def _port_forward(svc: str, local: int, remote: int) -> subprocess.Popen[bytes]:
    """Run `kubectl port-forward` in the background and return its process."""
    return subprocess.Popen(
        ["kubectl", "port-forward", f"svc/{svc}", f"{local}:{remote}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@pytest.fixture(autouse=True)
def port_forwards() -> Iterator[None]:
    """Establish local forwards to orchestrator and fake-threads for metrics testing."""
    pf1 = _port_forward("orchestrator", ORCH_PORT, 8080)
    pf2 = _port_forward("fake-threads", THREADS_PORT, 9009)
    time.sleep(3)  # give k8s a moment for port forwards
    try:
        yield
    finally:
        pf1.terminate()
        pf2.terminate()


def test_business_metrics_collection() -> None:
    """Test that business metrics are properly collected during content generation."""
    # 1️⃣ Trigger content generation
    payload = {
        "persona_id": "ai-jesus",
        "task_type": "create_post",
        "trend_snippet": "solar energy innovation",
    }

    response = httpx.post(
        f"http://localhost:{ORCH_PORT}/task", json=payload, timeout=10
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"

    # 2️⃣ Wait for processing to complete
    deadline = time.time() + 30
    while time.time() < deadline:
        published = httpx.get(f"http://localhost:{THREADS_PORT}/published", timeout=5)
        if published.status_code == 200 and published.json():
            break
        time.sleep(1)
    else:
        pytest.fail("Content generation didn't complete within 30s")

    # 3️⃣ Check that enhanced metrics are being collected
    metrics_response = httpx.get(f"http://localhost:{ORCH_PORT}/metrics", timeout=10)
    metrics_response.raise_for_status()
    metrics_text = metrics_response.text

    # Verify business metrics are present
    business_metrics = [
        "posts_generated_total",
        "content_generation_latency_seconds",
        "content_quality_score",
        "cost_per_post_usd",
    ]

    for metric in business_metrics:
        assert f"# TYPE {metric}" in metrics_text, f"Missing business metric: {metric}"

    # Verify RED methodology metrics
    red_metrics = [
        "http_requests_total",
        "http_request_duration_seconds",
        "http_requests_in_flight",
    ]

    for metric in red_metrics:
        assert f"# TYPE {metric}" in metrics_text, f"Missing RED metric: {metric}"

    # Verify USE methodology metrics
    use_metrics = [
        "celery_tasks_total",
        "celery_task_duration_seconds",
        "database_query_duration_seconds",
    ]

    for metric in use_metrics:
        assert f"# TYPE {metric}" in metrics_text, f"Missing USE metric: {metric}"


def test_http_request_metrics() -> None:
    """Test that HTTP request metrics are properly tracked (RED methodology)."""
    # Make several requests to different endpoints
    endpoints = ["/health", "/metrics", "/task"]

    for endpoint in endpoints[:2]:  # Skip /task to avoid triggering actual processing
        response = httpx.get(f"http://localhost:{ORCH_PORT}{endpoint}", timeout=5)
        response.raise_for_status()

    # Check metrics collection
    metrics_response = httpx.get(f"http://localhost:{ORCH_PORT}/metrics", timeout=5)
    metrics_text = metrics_response.text

    # Verify HTTP metrics are incremented
    assert "http_requests_total{" in metrics_text
    assert 'method="GET"' in metrics_text
    assert 'service="orchestrator"' in metrics_text
    assert 'endpoint="/health"' in metrics_text
    assert 'status_code="200"' in metrics_text

    # Verify latency metrics exist
    assert "http_request_duration_seconds_bucket{" in metrics_text
    assert "http_request_duration_seconds_count{" in metrics_text


def test_system_health_metrics() -> None:
    """Test that system health metrics are updated during health checks."""
    # Trigger health check
    health_response = httpx.get(f"http://localhost:{ORCH_PORT}/health", timeout=5)
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"

    # Check that health metrics are updated
    metrics_response = httpx.get(f"http://localhost:{ORCH_PORT}/metrics", timeout=5)
    metrics_text = metrics_response.text

    # Verify system health metrics
    health_components = ["api", "database", "queue"]

    for component in health_components:
        assert (
            f'system_health_status{{component="{component}",service="orchestrator"}} 1'
            in metrics_text
        )


def test_cost_tracking_metrics() -> None:
    """Test that cost metrics are collected during content generation."""
    # Trigger content generation with cost tracking
    payload = {
        "persona_id": "ai-elon",
        "task_type": "create_post",
        "pain_statement": "startup funding challenges",
    }

    response = httpx.post(
        f"http://localhost:{ORCH_PORT}/task", json=payload, timeout=10
    )
    assert response.status_code == 200

    # Wait for processing
    time.sleep(10)

    # Check cost metrics
    metrics_response = httpx.get(f"http://localhost:{ORCH_PORT}/metrics", timeout=5)
    metrics_text = metrics_response.text

    # In test mode, we should see mock costs
    assert "# TYPE openai_api_costs_usd_total counter" in metrics_text
    assert "# TYPE cost_per_post_usd gauge" in metrics_text

    # Verify persona-specific cost tracking
    assert 'persona_id="ai-elon"' in metrics_text


def test_performance_impact() -> None:
    """Test that metrics collection has minimal performance impact."""
    # Time requests with and without metrics (conceptual - metrics always on)
    start_time = time.time()

    # Make multiple requests to test performance impact
    for _ in range(5):
        response = httpx.get(f"http://localhost:{ORCH_PORT}/health", timeout=2)
        assert response.status_code == 200

    elapsed = time.time() - start_time

    # Should complete 5 health checks in under 2 seconds even with full metrics
    assert elapsed < 2.0, f"Performance impact too high: {elapsed:.3f}s for 5 requests"

    # Verify metrics endpoint is responsive
    start_time = time.time()
    metrics_response = httpx.get(f"http://localhost:{ORCH_PORT}/metrics", timeout=5)
    metrics_elapsed = time.time() - start_time

    assert metrics_response.status_code == 200
    assert metrics_elapsed < 1.0, f"Metrics endpoint too slow: {metrics_elapsed:.3f}s"

    # Verify we have substantial metrics (comprehensive instrumentation)
    metrics_lines = len(metrics_response.text.splitlines())
    assert metrics_lines > 100, f"Expected >100 metrics lines, got {metrics_lines}"
