"""
Pytest configuration and shared fixtures for CI/CD Pipeline testing.

This module provides:
- Shared fixtures for all test suites
- Test environment setup and teardown
- Performance monitoring fixtures
- Mock data generators
- Test utilities and helpers

Author: Test Generation Specialist for CRA-297
"""

import pytest
import time
import psutil
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock
import tempfile
import shutil
from pathlib import Path

from services.common.performance_regression_detector import PerformanceData


@pytest.fixture(scope="session")
def test_session_info():
    """Provide test session information."""
    return {
        "start_time": datetime.now(),
        "test_environment": "ci_cd_pipeline_testing",
        "python_version": pytest.__version__,
        "session_id": f"test_session_{int(time.time())}",
    }


@pytest.fixture(scope="session")
def performance_monitor():
    """Monitor system performance during test execution."""

    class PerformanceMonitor:
        def __init__(self):
            self.process = psutil.Process()
            self.start_memory = self.process.memory_info().rss
            self.start_time = time.time()

        def get_current_stats(self):
            current_memory = self.process.memory_info().rss
            current_time = time.time()

            return {
                "memory_usage_mb": current_memory / (1024 * 1024),
                "memory_increase_mb": (current_memory - self.start_memory)
                / (1024 * 1024),
                "execution_time": current_time - self.start_time,
                "cpu_percent": self.process.cpu_percent(),
            }

    monitor = PerformanceMonitor()
    yield monitor

    # Log final stats
    final_stats = monitor.get_current_stats()
    print("\\nTest session performance:")
    print(f"  Memory usage: {final_stats['memory_usage_mb']:.1f} MB")
    print(f"  Memory increase: {final_stats['memory_increase_mb']:.1f} MB")
    print(f"  Total execution time: {final_stats['execution_time']:.2f}s")


@pytest.fixture
def mock_prompt_model():
    """Create a mock prompt model for testing."""
    mock_model = Mock()
    mock_model.name = "test_prompt_model"
    mock_model.version = "v1.0.0"
    mock_model.template = "Test template: {input}"

    def render(**kwargs):
        input_text = kwargs.get("input", "default")
        return f"Processed: {input_text}"

    mock_model.render.side_effect = render
    return mock_model


@pytest.fixture
def mock_model_registry():
    """Create a mock model registry for testing."""
    mock_registry = Mock()
    mock_registry.current_model = "v1.0.0"
    mock_registry.available_models = ["v1.0.0", "v0.9.5", "v0.9.0"]

    def rollback_to_model(target_model):
        if target_model in mock_registry.available_models:
            return Mock(success=True, target_model=target_model, duration=15.0)
        else:
            return Mock(success=False, error="Model not found")

    mock_registry.rollback_to_model.side_effect = rollback_to_model
    return mock_registry


@pytest.fixture
def performance_data_generator():
    """Generate realistic performance data for testing."""

    def generate_data(
        metric_name: str,
        count: int,
        base_value: float,
        variance: float = 0.05,
        trend: float = 0.0,
        start_time: datetime = None,
    ) -> List[PerformanceData]:
        """
        Generate performance data with realistic patterns.

        Args:
            metric_name: Name of the metric
            count: Number of data points
            base_value: Base value for the metric
            variance: Standard deviation as fraction of base_value
            trend: Linear trend per data point
            start_time: Starting timestamp
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=count)

        np.random.seed(42)  # Reproducible data
        data_points = []

        for i in range(count):
            # Add trend and random variance
            value = (
                base_value + (i * trend) + np.random.normal(0, base_value * variance)
            )

            # Ensure reasonable bounds
            if 0 <= base_value <= 1:  # Probability/percentage metrics
                value = max(0, min(1, value))
            else:  # Other metrics (latency, throughput, etc.)
                value = max(0, value)

            timestamp = start_time + timedelta(hours=i)

            data_points.append(
                PerformanceData(
                    timestamp=timestamp,
                    metric_name=metric_name,
                    value=value,
                    metadata={
                        "data_point_id": i,
                        "generated": True,
                        "base_value": base_value,
                        "trend": trend,
                    },
                )
            )

        return data_points

    return generate_data


@pytest.fixture
def regression_data_scenarios():
    """Provide various regression scenarios for testing."""

    def create_scenario(scenario_type: str) -> Dict[str, List[PerformanceData]]:
        """Create performance regression scenarios."""
        np.random.seed(42)

        scenarios = {
            "no_regression": {
                "historical": [
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(hours=i),
                        metric_name="accuracy",
                        value=0.85 + np.random.normal(0, 0.02),
                        metadata={},
                    )
                    for i in range(1, 25)
                ],
                "current": [
                    PerformanceData(
                        timestamp=datetime.now(),
                        metric_name="accuracy",
                        value=0.85 + np.random.normal(0, 0.02),
                        metadata={},
                    )
                    for _ in range(10)
                ],
            },
            "clear_regression": {
                "historical": [
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(hours=i),
                        metric_name="accuracy",
                        value=0.90 + np.random.normal(0, 0.01),
                        metadata={},
                    )
                    for i in range(1, 25)
                ],
                "current": [
                    PerformanceData(
                        timestamp=datetime.now(),
                        metric_name="accuracy",
                        value=0.75 + np.random.normal(0, 0.02),  # Significant drop
                        metadata={},
                    )
                    for _ in range(10)
                ],
            },
            "gradual_degradation": {
                "historical": [
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(hours=i),
                        metric_name="accuracy",
                        value=0.88 + np.random.normal(0, 0.015),
                        metadata={},
                    )
                    for i in range(1, 25)
                ],
                "current": [
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(minutes=i * 10),
                        metric_name="accuracy",
                        value=0.88
                        - (i * 0.002)
                        + np.random.normal(0, 0.01),  # Gradual decline
                        metadata={},
                    )
                    for i in range(10)
                ],
            },
            "improvement": {
                "historical": [
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(hours=i),
                        metric_name="accuracy",
                        value=0.82 + np.random.normal(0, 0.02),
                        metadata={},
                    )
                    for i in range(1, 25)
                ],
                "current": [
                    PerformanceData(
                        timestamp=datetime.now(),
                        metric_name="accuracy",
                        value=0.88 + np.random.normal(0, 0.015),  # Improvement
                        metadata={},
                    )
                    for _ in range(10)
                ],
            },
        }

        return scenarios.get(scenario_type, scenarios["no_regression"])

    return create_scenario


@pytest.fixture
def temp_test_directory():
    """Provide a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="cicd_pipeline_test_")
    temp_path = Path(temp_dir)

    yield temp_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_time_series():
    """Create mock time series data with various patterns."""

    def create_time_series(
        pattern: str,
        duration_hours: int = 24,
        interval_minutes: int = 60,
        base_value: float = 100.0,
    ) -> List[Dict[str, Any]]:
        """
        Create time series data with specific patterns.

        Args:
            pattern: 'stable', 'trending_up', 'trending_down', 'cyclical', 'volatile'
            duration_hours: Duration of the time series
            interval_minutes: Interval between data points
            base_value: Base value for the series
        """
        np.random.seed(42)
        data_points = []
        num_points = duration_hours * 60 // interval_minutes

        for i in range(num_points):
            timestamp = datetime.now() - timedelta(minutes=i * interval_minutes)

            if pattern == "stable":
                value = base_value + np.random.normal(0, base_value * 0.05)
            elif pattern == "trending_up":
                value = (
                    base_value
                    + (i * 0.01 * base_value)
                    + np.random.normal(0, base_value * 0.03)
                )
            elif pattern == "trending_down":
                value = (
                    base_value
                    - (i * 0.01 * base_value)
                    + np.random.normal(0, base_value * 0.03)
                )
            elif pattern == "cyclical":
                cycle_value = base_value * (
                    1 + 0.2 * np.sin(2 * np.pi * i / 24)
                )  # 24-hour cycle
                value = cycle_value + np.random.normal(0, base_value * 0.05)
            elif pattern == "volatile":
                value = base_value + np.random.normal(0, base_value * 0.15)
            else:
                value = base_value

            data_points.append(
                {
                    "timestamp": timestamp,
                    "value": max(0, value),
                    "pattern": pattern,
                    "index": i,
                }
            )

        return data_points

    return create_time_series


@pytest.fixture
def test_execution_timer():
    """Time test execution for performance validation."""

    class ExecutionTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

        def assert_under_limit(
            self, limit_seconds: float, operation_name: str = "operation"
        ):
            """Assert that execution time is under the specified limit."""
            assert self.duration < limit_seconds, (
                f"{operation_name} took {self.duration:.2f}s, exceeds limit of {limit_seconds}s"
            )

    timer = ExecutionTimer()
    timer.start()
    yield timer
    timer.stop()


@pytest.fixture
def cicd_test_config():
    """Provide configuration for CI/CD pipeline tests."""
    return {
        "timeouts": {
            "prompt_test_execution": 30.0,
            "performance_detection": 5.0,
            "rollout_stage_advance": 10.0,
            "rollback_execution": 30.0,
            "health_check": 2.0,
        },
        "thresholds": {
            "test_success_rate": 95.0,
            "coverage_minimum": 95.0,
            "performance_regression_p_value": 0.05,
            "rollout_traffic_percentages": [10, 25, 50, 100],
        },
        "sla_requirements": {
            "rollback_max_time": 30.0,
            "pipeline_max_time": 180.0,
            "health_check_frequency": 60.0,
        },
        "test_data": {
            "min_samples_for_regression": 10,
            "max_test_data_points": 1000,
            "default_confidence_level": 0.95,
        },
    }


@pytest.fixture(autouse=True)
def test_isolation():
    """Ensure test isolation and cleanup."""
    # Setup - ensure clean state
    import gc

    gc.collect()

    yield

    # Teardown - cleanup after test
    gc.collect()


# Markers for categorizing tests
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.performance = pytest.mark.performance
pytest.mark.failure_injection = pytest.mark.failure_injection
pytest.mark.security = pytest.mark.security
pytest.mark.comprehensive = pytest.mark.comprehensive


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit test for individual components")
    config.addinivalue_line(
        "markers", "integration: Integration test between components"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end test requiring full environment"
    )
    config.addinivalue_line("markers", "performance: Performance and timing tests")
    config.addinivalue_line(
        "markers", "failure_injection: Failure injection and resilience tests"
    )
    config.addinivalue_line("markers", "security: Security and permission tests")
    config.addinivalue_line(
        "markers", "comprehensive: Comprehensive test suite execution"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file patterns."""
    for item in items:
        # Add markers based on file name patterns
        if "performance" in item.fspath.basename:
            item.add_marker(pytest.mark.performance)
        elif "integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        elif "advanced" in item.fspath.basename:
            item.add_marker(pytest.mark.advanced)
        elif "failure" in item.fspath.basename:
            item.add_marker(pytest.mark.failure_injection)
        elif "workflow" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        elif "comprehensive" in item.fspath.basename:
            item.add_marker(pytest.mark.comprehensive)
        else:
            item.add_marker(pytest.mark.unit)


def pytest_report_header(config):
    """Add custom header to pytest report."""
    return [
        "CI/CD Pipeline Comprehensive Test Suite",
        "Components: PromptTestRunner, PerformanceRegressionDetector, GradualRolloutManager, RollbackController",
        "Coverage Target: >95%, SLA: <30s rollback time",
    ]


def pytest_sessionfinish(session, exitstatus):
    """Custom session finish handling."""
    if exitstatus == 0:
        print("\\n🎉 All CI/CD Pipeline tests completed successfully!")
    else:
        print(f"\\n⚠️  Some tests failed (exit status: {exitstatus})")
        print("Check the detailed report for failure analysis.")
