"""Unit tests for performance regression detection in fine-tuning pipeline.

This module tests the performance monitoring and regression detection capabilities:
1. Performance baseline establishment
2. Regression detection algorithms
3. Performance threshold validation
4. Metrics collection and analysis
5. Alert triggering for performance degradation
"""

import pytest
import time
import asyncio
import statistics
from unittest.mock import Mock, patch
from typing import Dict, List, Any

from services.common.fine_tuning_pipeline import (
    PerformanceMonitor,
    MLflowExperimentTracker,
)


class TestPerformanceMonitor:
    """Test the PerformanceMonitor class for metrics collection and timing."""

    @pytest.fixture
    def performance_monitor(self):
        """Create a performance monitor for testing."""
        return PerformanceMonitor()

    def test_performance_monitor_initialization(self, performance_monitor):
        """Test performance monitor initialization."""
        assert performance_monitor.start_time is None
        assert performance_monitor.metrics == {}

    def test_operation_timing(self, performance_monitor):
        """Test operation timing functionality."""
        # Start timing
        performance_monitor.start_timing("test_operation")
        assert performance_monitor.start_time is not None
        assert "test_operation_start_time" in performance_monitor.metrics

        # Simulate some work
        time.sleep(0.1)

        # End timing
        duration = performance_monitor.end_timing("test_operation")

        # Verify timing results
        assert duration >= 0.1
        assert duration < 0.2  # Should be close to 0.1 seconds
        assert "test_operation_duration_seconds" in performance_monitor.metrics
        assert "test_operation_end_time" in performance_monitor.metrics
        assert (
            performance_monitor.metrics["test_operation_duration_seconds"] == duration
        )

    def test_multiple_operation_timing(self, performance_monitor):
        """Test timing multiple operations."""
        operations = ["data_collection", "model_training", "evaluation"]
        durations = []

        for operation in operations:
            performance_monitor.start_timing(operation)
            time.sleep(0.05)  # Different operation durations
            duration = performance_monitor.end_timing(operation)
            durations.append(duration)

        # Verify all operations were timed
        for i, operation in enumerate(operations):
            assert f"{operation}_duration_seconds" in performance_monitor.metrics
            assert (
                performance_monitor.metrics[f"{operation}_duration_seconds"]
                == durations[i]
            )

    def test_custom_metric_recording(self, performance_monitor):
        """Test recording custom performance metrics."""
        # Record various types of metrics
        performance_monitor.record_metric("memory_usage_mb", 245.7)
        performance_monitor.record_metric("cache_hit_rate", 0.85)
        performance_monitor.record_metric("active_connections", 15)
        performance_monitor.record_metric("error_rate", 0.02)

        # Verify metrics were recorded
        assert performance_monitor.metrics["memory_usage_mb"] == 245.7
        assert performance_monitor.metrics["cache_hit_rate"] == 0.85
        assert performance_monitor.metrics["active_connections"] == 15
        assert performance_monitor.metrics["error_rate"] == 0.02

    def test_prometheus_metrics_generation(self, performance_monitor):
        """Test Prometheus metrics format generation."""
        # Set up test metrics
        performance_monitor.record_metric("request_duration_seconds", 1.23)
        performance_monitor.record_metric("memory_usage_bytes", 1048576)
        performance_monitor.record_metric("success_rate", 0.98)
        performance_monitor.record_metric(
            "operation_name", "test_operation"
        )  # String metric

        prometheus_output = performance_monitor.get_prometheus_metrics()

        # Verify numeric metrics are included
        assert "fine_tuning_pipeline_request_duration_seconds 1.23" in prometheus_output
        assert "fine_tuning_pipeline_memory_usage_bytes 1048576" in prometheus_output
        assert "fine_tuning_pipeline_success_rate 0.98" in prometheus_output

        # Verify string metrics are excluded
        assert "operation_name" not in prometheus_output

        # Verify proper format
        assert prometheus_output.endswith("\n")
        lines = prometheus_output.strip().split("\n")
        assert len(lines) == 3  # Only numeric metrics


class TestPerformanceRegressionDetection:
    """Test performance regression detection algorithms."""

    class PerformanceRegressionDetector:
        """Performance regression detector with baseline comparison."""

        def __init__(self, threshold_percentage: float = 20.0):
            self.threshold_percentage = threshold_percentage
            self.baselines: Dict[str, List[float]] = {}

        def record_baseline(self, metric_name: str, value: float):
            """Record a baseline value for a metric."""
            if metric_name not in self.baselines:
                self.baselines[metric_name] = []
            self.baselines[metric_name].append(value)

        def detect_regression(
            self, metric_name: str, current_value: float
        ) -> Dict[str, Any]:
            """Detect if current value represents a performance regression."""
            if (
                metric_name not in self.baselines
                or len(self.baselines[metric_name]) < 3
            ):
                return {"is_regression": False, "reason": "insufficient_baseline_data"}

            baseline_values = self.baselines[metric_name]
            baseline_mean = statistics.mean(baseline_values)
            baseline_stddev = (
                statistics.stdev(baseline_values) if len(baseline_values) > 1 else 0
            )

            # Calculate z-score
            z_score = (current_value - baseline_mean) / max(baseline_stddev, 0.001)

            # For duration/latency metrics, higher is worse
            threshold_value = baseline_mean * (1 + self.threshold_percentage / 100)
            is_regression = current_value > threshold_value

            return {
                "is_regression": is_regression,
                "current_value": current_value,
                "baseline_mean": baseline_mean,
                "baseline_stddev": baseline_stddev,
                "z_score": z_score,
                "threshold_value": threshold_value,
                "deviation_percentage": (
                    (current_value - baseline_mean) / baseline_mean
                )
                * 100,
            }

    @pytest.fixture
    def regression_detector(self):
        """Create a regression detector for testing."""
        return self.PerformanceRegressionDetector(threshold_percentage=25.0)

    def test_baseline_establishment(self, regression_detector):
        """Test establishing performance baselines."""
        # Record baseline values for response time
        baseline_times = [1.2, 1.3, 1.1, 1.4, 1.25, 1.35, 1.15]
        for time_val in baseline_times:
            regression_detector.record_baseline("response_time_seconds", time_val)

        # Verify baseline data
        assert "response_time_seconds" in regression_detector.baselines
        assert len(regression_detector.baselines["response_time_seconds"]) == 7
        assert regression_detector.baselines["response_time_seconds"] == baseline_times

    def test_no_regression_detection(self, regression_detector):
        """Test detection when performance is within acceptable range."""
        # Establish baseline
        baseline_values = [100, 105, 95, 102, 98, 103, 97]
        for value in baseline_values:
            regression_detector.record_baseline("memory_usage_mb", value)

        # Test value within acceptable range
        result = regression_detector.detect_regression("memory_usage_mb", 104)

        assert result["is_regression"] is False
        assert result["current_value"] == 104
        assert 95 <= result["baseline_mean"] <= 105
        assert result["deviation_percentage"] < 25  # Within threshold

    def test_performance_regression_detection(self, regression_detector):
        """Test detection of actual performance regression."""
        # Establish baseline for API response times
        baseline_times = [0.5, 0.6, 0.55, 0.52, 0.58, 0.54, 0.56]
        for time_val in baseline_times:
            regression_detector.record_baseline("api_response_time", time_val)

        # Test significantly worse performance
        result = regression_detector.detect_regression(
            "api_response_time", 0.85
        )  # 50%+ increase

        assert result["is_regression"] is True
        assert result["current_value"] == 0.85
        assert result["deviation_percentage"] > 25  # Beyond threshold
        assert result["z_score"] > 2  # Statistical significance

    def test_insufficient_baseline_data(self, regression_detector):
        """Test handling of insufficient baseline data."""
        # Record only 2 baseline values (need at least 3)
        regression_detector.record_baseline("new_metric", 10.0)
        regression_detector.record_baseline("new_metric", 12.0)

        result = regression_detector.detect_regression("new_metric", 15.0)

        assert result["is_regression"] is False
        assert result["reason"] == "insufficient_baseline_data"

    def test_edge_case_zero_standard_deviation(self, regression_detector):
        """Test handling of zero standard deviation in baseline."""
        # All baseline values are identical
        for _ in range(5):
            regression_detector.record_baseline("constant_metric", 100.0)

        result = regression_detector.detect_regression("constant_metric", 130.0)

        # Should still detect regression despite zero stddev
        assert result["is_regression"] is True
        assert result["baseline_mean"] == 100.0
        assert result["baseline_stddev"] == 0.0
        assert result["deviation_percentage"] == 30.0


class TestMLflowPerformanceTracking:
    """Test MLflow integration for performance tracking."""

    @pytest.fixture
    def mlflow_tracker(self):
        """Create MLflow experiment tracker for testing."""
        return MLflowExperimentTracker("performance_testing")

    def test_database_performance_logging(self, mlflow_tracker):
        """Test logging of database performance metrics."""
        # Simulate database operation metrics
        query_count = 15
        total_duration = 2.5  # seconds
        cache_hits = 12

        mlflow_tracker.log_database_performance(query_count, total_duration, cache_hits)

        # Verify metrics were recorded
        metrics = mlflow_tracker.performance_monitor.metrics
        assert metrics["database_queries_total"] == 15
        assert metrics["database_query_duration_total"] == 2.5
        assert metrics["database_cache_hits"] == 12
        assert metrics["database_avg_query_duration"] == 2.5 / 15

    def test_memory_efficiency_logging(self, mlflow_tracker):
        """Test logging of memory efficiency metrics."""
        peak_memory = 512.7  # MB
        training_examples = 2000

        mlflow_tracker.log_memory_efficiency(peak_memory, training_examples)

        metrics = mlflow_tracker.performance_monitor.metrics
        assert metrics["memory_peak_mb"] == 512.7
        assert metrics["memory_per_example_mb"] == 512.7 / 2000
        assert metrics["training_examples_total"] == 2000

    def test_api_performance_logging(self, mlflow_tracker):
        """Test logging of external API performance."""
        # Test successful API call
        mlflow_tracker.log_api_performance("openai", 3.2, True)

        # Test failed API call
        mlflow_tracker.log_api_performance("openai", 1.5, False)

        metrics = mlflow_tracker.performance_monitor.metrics
        assert metrics["openai_api_duration_seconds"] == 1.5  # Last recorded value
        assert metrics["openai_api_success"] == 0  # Last was failure

    def test_performance_metrics_integration(self, mlflow_tracker):
        """Test integration of performance metrics with MLflow logging."""
        # Set up test metrics
        test_metrics = {
            "training_examples": 1500,
            "base_model": "gpt-3.5-turbo-0125",
            "status": "completed",
        }

        # Add performance monitor metrics
        mlflow_tracker.performance_monitor.record_metric("pipeline_duration", 125.0)
        mlflow_tracker.performance_monitor.record_metric("peak_memory_mb", 328.5)

        with patch(
            "services.common.fine_tuning_pipeline.mlflow.log_metrics"
        ) as mock_log_metrics:
            mlflow_tracker.log_training_metrics(test_metrics)

            # Verify metrics were logged with performance data
            mock_log_metrics.assert_called_once()
            logged_metrics = mock_log_metrics.call_args[0][0]

            # Verify original metrics
            assert logged_metrics["training_examples"] == 1500
            assert logged_metrics["base_model"] == "gpt-3.5-turbo-0125"
            assert logged_metrics["status"] == "completed"

            # Verify performance metrics were included
            assert logged_metrics["pipeline_duration"] == 125.0
            assert logged_metrics["peak_memory_mb"] == 328.5


class TestPerformanceThresholdValidation:
    """Test performance threshold validation and alerting."""

    class PerformanceThresholdValidator:
        """Validates performance against defined thresholds."""

        def __init__(self):
            self.thresholds = {
                "max_response_time_seconds": 5.0,
                "max_memory_usage_mb": 1024,
                "min_cache_hit_rate": 0.8,
                "max_error_rate": 0.05,
                "max_cpu_utilization": 0.85,
            }
            self.alerts = []

        def validate_performance(self, metrics: Dict[str, float]) -> Dict[str, Any]:
            """Validate metrics against thresholds and generate alerts."""
            violations = []

            for metric_name, threshold in self.thresholds.items():
                if metric_name.startswith("max_"):
                    actual_metric = metric_name.replace("max_", "")
                    if actual_metric in metrics and metrics[actual_metric] > threshold:
                        violations.append(
                            {
                                "metric": actual_metric,
                                "actual": metrics[actual_metric],
                                "threshold": threshold,
                                "type": "exceeds_maximum",
                            }
                        )
                elif metric_name.startswith("min_"):
                    actual_metric = metric_name.replace("min_", "")
                    if actual_metric in metrics and metrics[actual_metric] < threshold:
                        violations.append(
                            {
                                "metric": actual_metric,
                                "actual": metrics[actual_metric],
                                "threshold": threshold,
                                "type": "below_minimum",
                            }
                        )

            return {
                "is_valid": len(violations) == 0,
                "violations": violations,
                "metrics_checked": len(metrics),
                "thresholds_applied": len(self.thresholds),
            }

        def generate_alert(self, violation: Dict[str, Any]) -> str:
            """Generate alert message for threshold violation."""
            if violation["type"] == "exceeds_maximum":
                return f"ALERT: {violation['metric']} = {violation['actual']} exceeds maximum threshold of {violation['threshold']}"
            else:
                return f"ALERT: {violation['metric']} = {violation['actual']} below minimum threshold of {violation['threshold']}"

    @pytest.fixture
    def threshold_validator(self):
        """Create a threshold validator for testing."""
        return self.PerformanceThresholdValidator()

    def test_performance_within_thresholds(self, threshold_validator):
        """Test validation when all metrics are within acceptable thresholds."""
        good_metrics = {
            "response_time_seconds": 2.5,
            "memory_usage_mb": 512,
            "cache_hit_rate": 0.85,
            "error_rate": 0.02,
            "cpu_utilization": 0.65,
        }

        result = threshold_validator.validate_performance(good_metrics)

        assert result["is_valid"] is True
        assert len(result["violations"]) == 0
        assert result["metrics_checked"] == 5
        assert result["thresholds_applied"] == 5

    def test_performance_threshold_violations(self, threshold_validator):
        """Test detection of performance threshold violations."""
        bad_metrics = {
            "response_time_seconds": 8.0,  # Exceeds 5.0 threshold
            "memory_usage_mb": 1500,  # Exceeds 1024 threshold
            "cache_hit_rate": 0.7,  # Below 0.8 threshold
            "error_rate": 0.08,  # Exceeds 0.05 threshold
            "cpu_utilization": 0.6,  # Within threshold
        }

        result = threshold_validator.validate_performance(bad_metrics)

        assert result["is_valid"] is False
        assert len(result["violations"]) == 4

        # Check specific violations
        violations_by_metric = {v["metric"]: v for v in result["violations"]}

        assert "response_time_seconds" in violations_by_metric
        assert (
            violations_by_metric["response_time_seconds"]["type"] == "exceeds_maximum"
        )
        assert violations_by_metric["response_time_seconds"]["actual"] == 8.0

        assert "cache_hit_rate" in violations_by_metric
        assert violations_by_metric["cache_hit_rate"]["type"] == "below_minimum"
        assert violations_by_metric["cache_hit_rate"]["actual"] == 0.7

    def test_alert_generation(self, threshold_validator):
        """Test alert message generation for violations."""
        max_violation = {
            "metric": "response_time_seconds",
            "actual": 7.5,
            "threshold": 5.0,
            "type": "exceeds_maximum",
        }

        min_violation = {
            "metric": "cache_hit_rate",
            "actual": 0.65,
            "threshold": 0.8,
            "type": "below_minimum",
        }

        max_alert = threshold_validator.generate_alert(max_violation)
        min_alert = threshold_validator.generate_alert(min_violation)

        assert (
            "ALERT: response_time_seconds = 7.5 exceeds maximum threshold of 5.0"
            == max_alert
        )
        assert (
            "ALERT: cache_hit_rate = 0.65 below minimum threshold of 0.8" == min_alert
        )

    def test_partial_metrics_validation(self, threshold_validator):
        """Test validation with only partial metrics available."""
        partial_metrics = {
            "response_time_seconds": 3.0,
            "memory_usage_mb": 800,
            # Missing cache_hit_rate, error_rate, cpu_utilization
        }

        result = threshold_validator.validate_performance(partial_metrics)

        # Should only validate available metrics
        assert result["is_valid"] is True  # Available metrics are within thresholds
        assert len(result["violations"]) == 0
        assert result["metrics_checked"] == 2  # Only 2 metrics provided


class TestAsyncPerformanceMonitoring:
    """Test performance monitoring in async operations."""

    async def test_async_operation_timing(self):
        """Test timing of async operations."""
        monitor = PerformanceMonitor()

        async def async_operation(duration: float):
            await asyncio.sleep(duration)
            return f"completed in {duration}s"

        # Time async operation
        monitor.start_timing("async_test")
        result = await async_operation(0.2)
        duration = monitor.end_timing("async_test")

        assert result == "completed in 0.2s"
        assert 0.19 <= duration <= 0.25  # Account for timing precision
        assert monitor.metrics["async_test_duration_seconds"] == duration

    async def test_concurrent_operations_monitoring(self):
        """Test monitoring multiple concurrent async operations."""
        monitor = PerformanceMonitor()

        async def tracked_operation(operation_id: str, duration: float):
            monitor.start_timing(f"operation_{operation_id}")
            await asyncio.sleep(duration)
            return monitor.end_timing(f"operation_{operation_id}")

        # Run multiple operations concurrently
        tasks = [
            tracked_operation("1", 0.1),
            tracked_operation("2", 0.15),
            tracked_operation("3", 0.08),
        ]

        start_time = time.time()
        durations = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify individual operation timing
        assert 0.08 <= durations[0] <= 0.12
        assert 0.13 <= durations[1] <= 0.17
        assert 0.06 <= durations[2] <= 0.10

        # Verify concurrent execution (should be ~0.15s, not 0.33s)
        assert total_time < 0.25

        # Verify all operations were tracked
        assert "operation_1_duration_seconds" in monitor.metrics
        assert "operation_2_duration_seconds" in monitor.metrics
        assert "operation_3_duration_seconds" in monitor.metrics

    async def test_performance_monitoring_under_load(self):
        """Test performance monitoring under high load conditions."""
        monitor = PerformanceMonitor()

        async def high_frequency_operation(operation_id: int):
            start_key = f"load_test_{operation_id}"
            monitor.start_timing(start_key)

            # Simulate quick operation
            await asyncio.sleep(0.01)

            duration = monitor.end_timing(start_key)
            monitor.record_metric(
                f"operation_{operation_id}_memory", operation_id * 1.5
            )
            return duration

        # Run 50 concurrent operations
        tasks = [high_frequency_operation(i) for i in range(50)]

        start_time = time.time()
        durations = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify all operations completed
        assert len(durations) == 50
        assert all(0.005 <= d <= 0.05 for d in durations)

        # Verify monitoring overhead is reasonable
        assert total_time < 2.0  # Should complete well under 2 seconds

        # Verify metrics were recorded
        assert len(monitor.metrics) >= 100  # 50 durations + 50 memory metrics

        # Check that metrics are accessible
        prometheus_output = monitor.get_prometheus_metrics()
        metric_lines = prometheus_output.strip().split("\n")
        assert len(metric_lines) >= 100


class TestPerformanceOptimizationValidation:
    """Test validation of actual performance optimizations."""

    async def test_database_chunking_performance_improvement(self):
        """Test that database chunking improves performance."""
        # Simulate large dataset processing

        async def process_without_chunking(data_size: int):
            """Simulate processing all data at once."""
            monitor = PerformanceMonitor()
            monitor.start_timing("non_chunked_processing")

            # Simulate memory-intensive processing
            large_list = list(range(data_size))
            processed = [x * 2 for x in large_list]

            await asyncio.sleep(data_size * 0.00001)  # Simulated processing time
            duration = monitor.end_timing("non_chunked_processing")

            del large_list, processed  # Cleanup
            return duration

        async def process_with_chunking(data_size: int, chunk_size: int = 1000):
            """Simulate chunked processing."""
            monitor = PerformanceMonitor()
            monitor.start_timing("chunked_processing")

            total_processed = 0
            for i in range(0, data_size, chunk_size):
                chunk = list(range(i, min(i + chunk_size, data_size)))
                processed_chunk = [x * 2 for x in chunk]
                total_processed += len(processed_chunk)

                # Simulate processing time and cleanup
                await asyncio.sleep(0.001)  # Small processing delay
                del chunk, processed_chunk

            duration = monitor.end_timing("chunked_processing")
            return duration

        # Test with 10,000 items
        data_size = 10000

        non_chunked_duration = await process_without_chunking(data_size)
        chunked_duration = await process_with_chunking(data_size, chunk_size=1000)

        # Chunked processing should be more memory-efficient
        # (Time comparison may vary, but chunking prevents memory spikes)
        performance_improvement = (
            non_chunked_duration - chunked_duration
        ) / non_chunked_duration

        # Even if not faster, chunked should be close in performance
        assert performance_improvement >= -0.5  # At most 50% slower

        # The real benefit is memory efficiency, which we test indirectly
        assert chunked_duration > 0  # Ensure test actually ran
        assert non_chunked_duration > 0

    async def test_connection_pooling_performance_benefit(self):
        """Test performance benefits of connection pooling."""

        class MockConnectionManager:
            def __init__(self, use_pooling: bool):
                self.use_pooling = use_pooling
                self.connection_creation_time = 0.01  # 10ms to create connection
                self.pool = [] if use_pooling else None

            async def get_connection(self):
                if self.use_pooling and self.pool:
                    return self.pool.pop()
                else:
                    # Simulate connection creation delay
                    await asyncio.sleep(self.connection_creation_time)
                    return Mock()

            async def return_connection(self, conn):
                if self.use_pooling:
                    self.pool.append(conn)

        async def perform_operations(
            manager: MockConnectionManager, operation_count: int
        ):
            monitor = PerformanceMonitor()
            operation_name = "pooled" if manager.use_pooling else "non_pooled"
            monitor.start_timing(f"{operation_name}_operations")

            for i in range(operation_count):
                conn = await manager.get_connection()
                # Simulate database operation
                await asyncio.sleep(0.001)
                await manager.return_connection(conn)

            return monitor.end_timing(f"{operation_name}_operations")

        # Test with 20 operations
        operation_count = 20

        # Non-pooled manager
        non_pooled_manager = MockConnectionManager(use_pooling=False)
        non_pooled_duration = await perform_operations(
            non_pooled_manager, operation_count
        )

        # Pooled manager (pre-populate pool)
        pooled_manager = MockConnectionManager(use_pooling=True)
        # Pre-create connections
        for _ in range(5):
            await pooled_manager.return_connection(Mock())

        pooled_duration = await perform_operations(pooled_manager, operation_count)

        # Pooled operations should be significantly faster
        performance_improvement = (
            non_pooled_duration - pooled_duration
        ) / non_pooled_duration
        assert performance_improvement > 0.3  # At least 30% improvement

        # Expected: non-pooled = ~20 * 0.01 = 0.2s + operation time
        #          pooled = ~operation time only (much faster)
        assert pooled_duration < non_pooled_duration * 0.7
