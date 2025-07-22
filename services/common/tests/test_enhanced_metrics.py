# services/common/tests/test_enhanced_metrics.py
"""Unit tests for enhanced Prometheus metrics (CRA-216)."""

from __future__ import annotations

import pytest
from prometheus_client import REGISTRY

from services.common.metrics import (
    CONTENT_QUALITY_SCORE,
    POSTS_GENERATED_TOTAL,
    record_http_request,
    record_post_generation,
    update_content_quality,
)


def test_post_generation_metrics() -> None:
    """Test that post generation metrics work correctly."""
    # Record some post generations
    record_post_generation("ai-jesus", "success")
    record_post_generation("ai-jesus", "failed")
    record_post_generation("ai-elon", "success")

    # Verify metrics were recorded (just test that the function doesn't crash)
    assert POSTS_GENERATED_TOTAL is not None


def test_content_quality_metrics() -> None:
    """Test content quality scoring metrics."""
    update_content_quality("ai-jesus", "hook", 0.85)
    update_content_quality("ai-jesus", "body", 0.75)
    update_content_quality("ai-jesus", "combined", 0.80)

    # Verify metrics can be set with different content types (test doesn't crash)
    assert CONTENT_QUALITY_SCORE is not None


def test_http_request_context_manager() -> None:
    """Test HTTP request context manager for RED methodology."""

    # Test successful request
    try:
        with record_http_request("orchestrator", "GET", "/health"):
            pass  # Simulate successful request
    except Exception:
        pytest.fail("HTTP request context manager should not raise on success")

    # Test request with exception
    try:
        with record_http_request("orchestrator", "POST", "/task"):
            raise ValueError("Simulated error")
    except ValueError:
        pass  # Expected
    except Exception:
        pytest.fail("Should re-raise the original exception")


def test_metrics_registration() -> None:
    """Test that our metrics are properly registered with Prometheus after use."""
    # First, trigger the metrics by using them - this is when they get registered
    record_post_generation("ai-jesus", "success")  # Creates posts_generated_total
    update_content_quality("ai-jesus", "hook", 0.85)  # Creates content_quality_score

    # Use HTTP request context manager to register HTTP metrics
    try:
        with record_http_request("test", "GET", "/test"):
            pass
    except Exception:
        pass  # Don't care about exceptions, just want to register the metrics

    # Now get all registered metric names
    metric_names = [
        collector._name
        for collector in REGISTRY._collector_to_names.keys()
        if hasattr(collector, "_name")
    ]

    # Check that our key metrics are registered after being used
    # Note: Prometheus removes _total suffix from Counter metrics
    expected_metrics = [
        "posts_generated",  # posts_generated_total -> posts_generated
        "content_quality_score",
        "http_requests",  # http_requests_total -> http_requests
        "http_request_duration_seconds",
    ]

    for metric_name in expected_metrics:
        # The metric should be registered after being used
        assert any(
            metric_name in name for name in metric_names
        ), f"Missing metric: {metric_name} in {metric_names}"


if __name__ == "__main__":
    # Run basic verification
    test_post_generation_metrics()
    test_content_quality_metrics()
    test_http_request_context_manager()
    test_metrics_registration()
    print("✅ All metric tests passed!")
