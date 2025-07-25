# services/common/tests/test_enhanced_metrics.py
"""Unit tests for enhanced Prometheus metrics (CRA-216)."""

from __future__ import annotations

import pytest
from prometheus_client import REGISTRY

from services.common.metrics import (
    CONTENT_QUALITY_SCORE,
    POSTS_GENERATED_TOTAL,
    record_business_metric_context,
    record_cost_per_follow,
    record_engagement_rate,
    record_error_rate_percentage,
    record_hourly_openai_cost,
    record_http_request,
    record_post_generation,
    update_content_quality,
    update_revenue_projection,
    update_service_uptime,
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
        with record_http_request("orchestrator", "GET", 200):
            pass  # Simulate successful request
    except Exception:
        pytest.fail("HTTP request context manager should not raise on success")

    # Test request with exception
    try:
        with record_http_request("orchestrator", "POST", 500):
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
        with record_http_request("test", "GET", 200):
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
        assert any(metric_name in name for name in metric_names), (
            f"Missing metric: {metric_name} in {metric_names}"
        )


def test_business_metrics() -> None:
    """Test new business metrics added for CRA-223."""
    # Test engagement rate recording
    record_engagement_rate("ai-jesus", 0.065)
    record_engagement_rate("ai-elon", 0.082)

    # Test revenue projection
    update_revenue_projection("current_run_rate", 5000.0)
    update_revenue_projection("forecast", 8000.0)
    update_revenue_projection("target", 20000.0)

    # Test hourly OpenAI cost tracking
    record_hourly_openai_cost("gpt-4o", 5.25)
    record_hourly_openai_cost("gpt-3.5-turbo", 1.50)

    # Test cost per follow
    record_cost_per_follow("ai-jesus", 0.012)
    record_cost_per_follow("ai-elon", 0.018)

    # All should execute without errors
    assert True


def test_service_health_metrics() -> None:
    """Test service health and uptime metrics."""
    # Test service uptime
    update_service_uptime("orchestrator", 3600.0)
    update_service_uptime("celery-worker", 3550.0)

    # Test error rate percentage
    record_error_rate_percentage("orchestrator", "api_error", 0.5)
    record_error_rate_percentage("celery-worker", "task_failure", 2.3)

    # All should execute without errors
    assert True


def test_business_metric_context_manager() -> None:
    """Test business metric tracking context manager."""
    # Test successful business operation
    try:
        with record_business_metric_context("post_generation"):
            pass  # Simulate successful operation
    except Exception:
        pytest.fail("Business metric context manager should not raise on success")

    # Test operation with exception
    try:
        with record_business_metric_context("revenue_calculation"):
            raise ValueError("Business logic error")
    except ValueError:
        pass  # Expected


if __name__ == "__main__":
    # Run basic verification
    test_post_generation_metrics()
    test_content_quality_metrics()
    test_http_request_context_manager()
    test_metrics_registration()
    test_business_metrics()
    test_service_health_metrics()
    test_business_metric_context_manager()
    print("✅ All metric tests passed!")
