"""
Performance Tests for Airflow Operators (CRA-284)

This module provides comprehensive performance tests to ensure operators
meet performance requirements under various load conditions.

Test Categories:
- Operator execution speed benchmarks
- Memory usage optimization tests
- Concurrent execution performance
- Throughput and latency measurements
- Resource utilization monitoring
- Performance regression detection

Requirements:
- Unit tests must complete within 100ms
- Integration tests must complete within 1s
- Memory usage must not exceed defined limits
- Throughput targets must be met
"""

import pytest
import time
import psutil
import threading
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import gc

# Import operators for testing
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../operators"))

from health_check_operator import HealthCheckOperator
from metrics_collector_operator import MetricsCollectorOperator


class PerformanceMonitor:
    """Utility class for monitoring performance metrics during tests."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.peak_memory = None
        self.cpu_samples = []
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        self.monitoring = True
        self.cpu_samples = []

        # Start CPU monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring and return metrics."""
        self.monitoring = False
        self.end_time = time.time()

        if self.monitor_thread:
            self.monitor_thread.join(timeout=0.1)

        return {
            "execution_time_ms": (self.end_time - self.start_time) * 1000,
            "memory_start_mb": self.start_memory,
            "memory_peak_mb": self.peak_memory,
            "memory_increase_mb": self.peak_memory - self.start_memory,
            "avg_cpu_percent": statistics.mean(self.cpu_samples)
            if self.cpu_samples
            else 0,
            "max_cpu_percent": max(self.cpu_samples) if self.cpu_samples else 0,
        }

    def _monitor_resources(self):
        """Monitor CPU and memory usage in background thread."""
        process = psutil.Process()

        while self.monitoring:
            try:
                # Sample CPU usage
                cpu_percent = process.cpu_percent()
                if cpu_percent > 0:  # Ignore zero readings
                    self.cpu_samples.append(cpu_percent)

                # Track peak memory
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                self.peak_memory = max(self.peak_memory, current_memory)

                time.sleep(0.01)  # Sample every 10ms
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyboardInterrupt):
                break


class TestHealthCheckOperatorPerformance:
    """Performance tests for HealthCheckOperator."""

    @pytest.fixture
    def performance_config(self):
        """Configuration for performance testing."""
        return {
            "max_execution_time_ms": 100,  # 100ms for unit tests
            "max_memory_increase_mb": 10,  # 10MB memory increase limit
            "max_cpu_percent": 50,  # 50% CPU usage limit
            "services": {
                "test_service_1": "http://service-1:8080",
                "test_service_2": "http://service-2:8080",
                "test_service_3": "http://service-3:8080",
            },
        }

    @pytest.mark.performance
    async def test_single_service_health_check_speed(self, performance_config):
        """Test single service health check execution speed."""
        monitor = PerformanceMonitor()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Fast response mock
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.elapsed.total_seconds.return_value = 0.001  # 1ms response
            mock_session.get.return_value = mock_response

            # Start monitoring
            monitor.start_monitoring()

            # Execute health check
            health_operator = HealthCheckOperator(
                task_id="speed_test_single",
                service_urls={"fast_service": "http://fast-service:8080"},
                timeout=5,
            )

            results = health_operator.execute({})

            # Stop monitoring
            metrics = monitor.stop_monitoring()

            # Validate performance requirements
            assert (
                metrics["execution_time_ms"]
                < performance_config["max_execution_time_ms"]
            ), f"Execution time {metrics['execution_time_ms']:.2f}ms exceeds limit"

            assert (
                metrics["memory_increase_mb"]
                < performance_config["max_memory_increase_mb"]
            ), f"Memory increase {metrics['memory_increase_mb']:.2f}MB exceeds limit"

            # Validate functionality
            assert results["overall_status"] == "healthy"
            assert len(results["services"]) == 1

    @pytest.mark.performance
    async def test_parallel_health_checks_performance(self, performance_config):
        """Test parallel health checks performance vs sequential."""
        services = performance_config["services"]

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate realistic response times
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.elapsed.total_seconds.return_value = 0.01  # 10ms per service
            mock_session.get.return_value = mock_response

            # Test parallel execution
            parallel_monitor = PerformanceMonitor()
            parallel_monitor.start_monitoring()

            parallel_operator = HealthCheckOperator(
                task_id="parallel_performance_test",
                service_urls=services,
                parallel_checks=True,
            )

            parallel_results = parallel_operator.execute({})
            parallel_metrics = parallel_monitor.stop_monitoring()

            # Test sequential execution
            sequential_monitor = PerformanceMonitor()
            sequential_monitor.start_monitoring()

            sequential_operator = HealthCheckOperator(
                task_id="sequential_performance_test",
                service_urls=services,
                parallel_checks=False,
            )

            sequential_results = sequential_operator.execute({})
            sequential_metrics = sequential_monitor.stop_monitoring()

            # Parallel should be significantly faster
            speedup_ratio = (
                sequential_metrics["execution_time_ms"]
                / parallel_metrics["execution_time_ms"]
            )
            assert speedup_ratio >= 2.0, (
                f"Parallel execution speedup {speedup_ratio:.2f}x is insufficient"
            )

            # Both should produce same results
            assert (
                parallel_results["overall_status"]
                == sequential_results["overall_status"]
            )
            assert len(parallel_results["services"]) == len(
                sequential_results["services"]
            )

    @pytest.mark.performance
    async def test_health_check_memory_efficiency(self, performance_config):
        """Test memory efficiency of health check operations."""
        monitor = PerformanceMonitor()

        # Create large service list to test memory scaling
        large_service_list = {}
        for i in range(50):  # 50 services
            large_service_list[f"service_{i}"] = f"http://service-{i}:8080"

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Memory-efficient response mock
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.elapsed.total_seconds.return_value = 0.001
            mock_session.get.return_value = mock_response

            # Force garbage collection before test
            gc.collect()

            monitor.start_monitoring()

            health_operator = HealthCheckOperator(
                task_id="memory_efficiency_test",
                service_urls=large_service_list,
                parallel_checks=True,
            )

            health_operator.execute({})

            metrics = monitor.stop_monitoring()

            # Memory usage should scale reasonably with service count
            memory_per_service = metrics["memory_increase_mb"] / len(large_service_list)
            assert memory_per_service < 1.0, (
                f"Memory per service {memory_per_service:.3f}MB too high"
            )

            # Overall memory increase should be reasonable
            assert metrics["memory_increase_mb"] < 50, (
                f"Total memory increase {metrics['memory_increase_mb']:.2f}MB excessive"
            )

    @pytest.mark.performance
    async def test_health_check_retry_performance(self, performance_config):
        """Test performance impact of retry mechanisms."""
        monitor = PerformanceMonitor()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate transient failures
            call_count = 0

            def retry_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count <= 2:  # First 2 calls fail
                    import requests

                    raise requests.exceptions.ConnectionError("Transient error")
                else:  # 3rd call succeeds
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"status": "healthy"}
                    mock_response.elapsed.total_seconds.return_value = 0.001
                    return mock_response

            mock_session.get.side_effect = retry_side_effect

            monitor.start_monitoring()

            health_operator = HealthCheckOperator(
                task_id="retry_performance_test",
                service_urls={"retry_service": "http://retry-service:8080"},
                max_retries=3,
                retry_delay=0.001,  # Very fast retry for testing
                timeout=5,
            )

            results = health_operator.execute({})

            metrics = monitor.stop_monitoring()

            # Even with retries, should complete quickly
            assert metrics["execution_time_ms"] < 200, (
                f"Retry execution time {metrics['execution_time_ms']:.2f}ms too slow"
            )

            # Should eventually succeed
            assert results["overall_status"] == "healthy"
            assert call_count == 3  # Should have retried exactly 3 times


class TestMetricsCollectorOperatorPerformance:
    """Performance tests for MetricsCollectorOperator."""

    @pytest.mark.performance
    async def test_metrics_collection_speed(self):
        """Test metrics collection execution speed."""
        monitor = PerformanceMonitor()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Fast mock responses
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}
            health_response.elapsed.total_seconds.return_value = 0.001

            metrics_response = Mock()
            metrics_response.status_code = 200
            metrics_response.json.return_value = {
                "engagement_rate": 0.067,
                "cost_per_follow": 0.009,
                "response_time_ms": 45,
            }

            mock_session.get.side_effect = [health_response, metrics_response]

            monitor.start_monitoring()

            metrics_operator = MetricsCollectorOperator(
                task_id="metrics_speed_test",
                service_urls={"fast_metrics_service": "http://fast-metrics:8080"},
            )

            results = metrics_operator.execute({})

            metrics = monitor.stop_monitoring()

            # Should complete within performance limits
            assert metrics["execution_time_ms"] < 100, (
                f"Metrics collection {metrics['execution_time_ms']:.2f}ms too slow"
            )
            assert metrics["memory_increase_mb"] < 15, (
                f"Memory usage {metrics['memory_increase_mb']:.2f}MB too high"
            )

            # Validate functionality
            assert len(results["kpis"]) > 0
            assert results["summary"]["total_services"] == 1

    @pytest.mark.performance
    async def test_large_metrics_dataset_performance(self):
        """Test performance with large metrics datasets."""
        monitor = PerformanceMonitor()

        # Create large metrics dataset
        large_metrics = {}
        for category in ["business", "performance", "operational"]:
            large_metrics[category] = {}
            for i in range(100):  # 100 metrics per category
                large_metrics[category][f"metric_{i}"] = float(i % 50)

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Health response
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}
            health_response.elapsed.total_seconds.return_value = 0.001

            # Large metrics response
            metrics_response = Mock()
            metrics_response.status_code = 200
            metrics_response.json.return_value = large_metrics

            mock_session.get.side_effect = [health_response, metrics_response]

            monitor.start_monitoring()

            metrics_operator = MetricsCollectorOperator(
                task_id="large_dataset_test",
                service_urls={"large_metrics_service": "http://large-metrics:8080"},
            )

            metrics_operator.execute({})

            metrics = monitor.stop_monitoring()

            # Should handle large datasets efficiently
            assert metrics["execution_time_ms"] < 500, (
                f"Large dataset processing {metrics['execution_time_ms']:.2f}ms too slow"
            )

            # Memory usage should be reasonable for dataset size
            metrics_count = sum(
                len(cat_metrics) for cat_metrics in large_metrics.values()
            )
            memory_per_metric = metrics["memory_increase_mb"] / metrics_count
            assert memory_per_metric < 0.1, (
                f"Memory per metric {memory_per_metric:.4f}MB too high"
            )

    @pytest.mark.performance
    async def test_metrics_aggregation_performance(self):
        """Test performance of metrics aggregation algorithms."""
        monitor = PerformanceMonitor()

        # Create multiple services with overlapping metrics
        service_metrics = {}
        for i in range(10):  # 10 services
            service_metrics[f"service_{i}"] = {
                "common_metric_1": float(i * 10),
                "common_metric_2": float(i * 5),
                "unique_metric": float(i),
            }

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Setup responses for all services
            responses = []
            for i in range(10):
                # Health response
                health_response = Mock()
                health_response.status_code = 200
                health_response.json.return_value = {"status": "healthy"}
                health_response.elapsed.total_seconds.return_value = 0.001
                responses.append(health_response)

                # Metrics response
                metrics_response = Mock()
                metrics_response.status_code = 200
                metrics_response.json.return_value = service_metrics[f"service_{i}"]
                responses.append(metrics_response)

            mock_session.get.side_effect = responses

            monitor.start_monitoring()

            service_urls = {
                f"service_{i}": f"http://service-{i}:8080" for i in range(10)
            }

            metrics_operator = MetricsCollectorOperator(
                task_id="aggregation_performance_test", service_urls=service_urls
            )

            results = metrics_operator.execute({})

            metrics = monitor.stop_monitoring()

            # Aggregation should be efficient
            assert metrics["execution_time_ms"] < 300, (
                f"Aggregation {metrics['execution_time_ms']:.2f}ms too slow"
            )

            # Validate aggregation correctness
            aggregated = results["aggregated_metrics"]
            assert aggregated["sum"]["common_metric_1"] == sum(
                i * 10 for i in range(10)
            )
            assert (
                aggregated["avg"]["common_metric_1"]
                == sum(i * 10 for i in range(10)) / 10
            )


class TestConcurrentPerformance:
    """Test performance under concurrent execution."""

    @pytest.mark.performance
    async def test_concurrent_operator_execution(self):
        """Test performance of multiple operators running concurrently."""
        monitor = PerformanceMonitor()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Fast response for concurrent testing
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy", "concurrent": True}
            mock_response.elapsed.total_seconds.return_value = 0.001
            mock_session.get.return_value = mock_response

            monitor.start_monitoring()

            # Create multiple operators
            operators = []
            for i in range(20):  # 20 concurrent operators
                operator = HealthCheckOperator(
                    task_id=f"concurrent_test_{i}",
                    service_urls={f"service_{i}": f"http://service-{i}:8080"},
                    timeout=5,
                )
                operators.append(operator)

            # Execute all operators concurrently
            async def execute_operator(op):
                return op.execute({})

            tasks = [execute_operator(op) for op in operators]
            results = await asyncio.gather(*tasks)

            metrics = monitor.stop_monitoring()

            # Concurrent execution should be efficient
            assert metrics["execution_time_ms"] < 1000, (
                f"Concurrent execution {metrics['execution_time_ms']:.2f}ms too slow"
            )

            # CPU usage should be reasonable
            assert metrics["max_cpu_percent"] < 80, (
                f"Peak CPU {metrics['max_cpu_percent']:.1f}% too high"
            )

            # All operators should succeed
            assert len(results) == 20
            for result in results:
                assert result["overall_status"] == "healthy"

    @pytest.mark.performance
    async def test_thread_pool_efficiency(self):
        """Test thread pool efficiency for parallel operations."""
        monitor = PerformanceMonitor()

        def simulate_io_task(task_id: int) -> Dict[str, Any]:
            """Simulate I/O bound task."""
            time.sleep(0.01)  # 10ms simulated I/O
            return {"task_id": task_id, "status": "completed", "timestamp": time.time()}

        monitor.start_monitoring()

        # Test with different thread pool sizes
        pool_sizes = [5, 10, 20]
        best_performance = float("inf")

        for pool_size in pool_sizes:
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=pool_size) as executor:
                futures = [executor.submit(simulate_io_task, i) for i in range(50)]
                results = [future.result() for future in as_completed(futures)]

            execution_time = (time.time() - start_time) * 1000
            best_performance = min(best_performance, execution_time)

            # Validate results
            assert len(results) == 50
            assert all(r["status"] == "completed" for r in results)

        total_metrics = monitor.stop_monitoring()

        # Thread pool optimization should be effective
        assert best_performance < 200, (
            f"Best thread pool performance {best_performance:.2f}ms too slow"
        )
        assert total_metrics["execution_time_ms"] < 1000, (
            f"Total test time {total_metrics['execution_time_ms']:.2f}ms too long"
        )


class TestPerformanceRegression:
    """Test for performance regressions."""

    @pytest.fixture
    def performance_baselines(self):
        """Define performance baselines for regression testing."""
        return {
            "health_check_single_service": {"max_time_ms": 50, "max_memory_mb": 5},
            "health_check_10_services_parallel": {
                "max_time_ms": 100,
                "max_memory_mb": 15,
            },
            "metrics_collection_single_service": {
                "max_time_ms": 80,
                "max_memory_mb": 10,
            },
            "metrics_aggregation_10_services": {
                "max_time_ms": 200,
                "max_memory_mb": 25,
            },
        }

    @pytest.mark.performance
    @pytest.mark.regression
    async def test_health_check_regression(self, performance_baselines):
        """Test for health check performance regression."""
        baseline = performance_baselines["health_check_single_service"]
        monitor = PerformanceMonitor()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.elapsed.total_seconds.return_value = 0.001
            mock_session.get.return_value = mock_response

            monitor.start_monitoring()

            health_operator = HealthCheckOperator(
                task_id="regression_test_health",
                service_urls={"regression_service": "http://regression-service:8080"},
            )

            health_operator.execute({})

            metrics = monitor.stop_monitoring()

            # Check for regression
            assert metrics["execution_time_ms"] <= baseline["max_time_ms"], (
                f"Performance regression: {metrics['execution_time_ms']:.2f}ms > {baseline['max_time_ms']}ms"
            )

            assert metrics["memory_increase_mb"] <= baseline["max_memory_mb"], (
                f"Memory regression: {metrics['memory_increase_mb']:.2f}MB > {baseline['max_memory_mb']}MB"
            )

    @pytest.mark.performance
    @pytest.mark.regression
    async def test_metrics_collection_regression(self, performance_baselines):
        """Test for metrics collection performance regression."""
        baseline = performance_baselines["metrics_collection_single_service"]
        monitor = PerformanceMonitor()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}
            health_response.elapsed.total_seconds.return_value = 0.001

            metrics_response = Mock()
            metrics_response.status_code = 200
            metrics_response.json.return_value = {
                "business_kpis": {"engagement_rate": 0.067},
                "performance_metrics": {"response_time_ms": 45},
            }

            mock_session.get.side_effect = [health_response, metrics_response]

            monitor.start_monitoring()

            metrics_operator = MetricsCollectorOperator(
                task_id="regression_test_metrics",
                service_urls={"regression_service": "http://regression-service:8080"},
            )

            metrics_operator.execute({})

            metrics = monitor.stop_monitoring()

            # Check for regression
            assert metrics["execution_time_ms"] <= baseline["max_time_ms"], (
                f"Performance regression: {metrics['execution_time_ms']:.2f}ms > {baseline['max_time_ms']}ms"
            )

            assert metrics["memory_increase_mb"] <= baseline["max_memory_mb"], (
                f"Memory regression: {metrics['memory_increase_mb']:.2f}MB > {baseline['max_memory_mb']}MB"
            )


class TestResourceUtilization:
    """Test resource utilization optimization."""

    @pytest.mark.performance
    async def test_cpu_utilization_efficiency(self):
        """Test CPU utilization efficiency during operations."""
        monitor = PerformanceMonitor()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # CPU-intensive mock (simulating JSON processing)
            def cpu_intensive_response(*args, **kwargs):
                # Simulate some CPU work
                result = sum(i * i for i in range(1000))  # Quick computation

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "healthy",
                    "computed_value": result,
                }
                mock_response.elapsed.total_seconds.return_value = 0.001
                return mock_response

            mock_session.get.side_effect = cpu_intensive_response

            monitor.start_monitoring()

            # Execute multiple health checks to test CPU usage
            health_operator = HealthCheckOperator(
                task_id="cpu_utilization_test",
                service_urls={
                    f"cpu_service_{i}": f"http://cpu-service-{i}:8080"
                    for i in range(10)
                },
                parallel_checks=True,
            )

            results = health_operator.execute({})

            metrics = monitor.stop_monitoring()

            # CPU utilization should be reasonable
            assert metrics["avg_cpu_percent"] < 60, (
                f"Average CPU {metrics['avg_cpu_percent']:.1f}% too high"
            )
            assert metrics["max_cpu_percent"] < 80, (
                f"Peak CPU {metrics['max_cpu_percent']:.1f}% too high"
            )

            # All services should be processed successfully
            assert len(results["services"]) == 10
            assert results["overall_status"] == "healthy"

    @pytest.mark.performance
    async def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.elapsed.total_seconds.return_value = 0.001
            mock_session.get.return_value = mock_response

            # Run many iterations to detect memory leaks
            for iteration in range(50):
                health_operator = HealthCheckOperator(
                    task_id=f"memory_leak_test_{iteration}",
                    service_urls={"test_service": "http://test-service:8080"},
                )

                results = health_operator.execute({})
                assert results["overall_status"] == "healthy"

                # Force garbage collection every 10 iterations
                if iteration % 10 == 0:
                    gc.collect()

            # Final garbage collection
            gc.collect()
            time.sleep(0.1)  # Allow cleanup

            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be minimal (no significant leaks)
            assert memory_increase < 20, (
                f"Potential memory leak: {memory_increase:.2f}MB increase after 50 iterations"
            )
