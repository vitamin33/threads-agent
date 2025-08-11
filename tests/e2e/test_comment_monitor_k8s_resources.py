# /tests/e2e/test_comment_monitor_k8s_resources.py
"""
Kubernetes resource constraint tests for comment monitoring pipeline.

These tests validate performance and behavior under CPU/memory limits,
resource scaling, and pod resource management in Kubernetes environments.
"""

import pytest
import time
from unittest.mock import Mock
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from services.orchestrator.comment_monitor import CommentMonitor


@dataclass
class K8sResourceMetrics:
    """Kubernetes resource usage metrics."""

    cpu_usage_percent: float
    memory_usage_mb: float
    memory_limit_mb: float
    cpu_limit_cores: float
    pod_status: str
    restart_count: int
    oom_kills: int
    throttle_events: int


@dataclass
class ResourceConstraintTestResult:
    """Results from resource constraint testing."""

    throughput_comments_per_second: float
    avg_response_time_ms: float
    error_rate_percent: float
    resource_efficiency: float
    constraint_violations: int


class TestCommentMonitorK8sResourceConstraints:
    """Kubernetes resource constraint tests for comment monitoring."""

    @pytest.fixture
    def mock_k8s_resource_monitor(self):
        """Mock Kubernetes resource monitoring."""

        class MockK8sResourceMonitor:
            def __init__(self):
                self.current_cpu_percent = 0.0
                self.current_memory_mb = 100.0
                self.memory_limit_mb = 512.0
                self.cpu_limit_cores = 1.0
                self.oom_kills = 0
                self.throttle_events = 0
                self.resource_history = []

            def simulate_resource_usage(self, cpu_percent: float, memory_mb: float):
                """Simulate resource usage for testing."""
                self.current_cpu_percent = min(cpu_percent, 100.0)
                self.current_memory_mb = memory_mb

                # Simulate OOM kill if memory exceeds limit
                if memory_mb > self.memory_limit_mb:
                    self.oom_kills += 1
                    self.current_memory_mb = 50.0  # Reset after OOM kill

                # Simulate CPU throttling if CPU exceeds limit
                if cpu_percent > (self.cpu_limit_cores * 100):
                    self.throttle_events += 1

                self.resource_history.append(
                    {
                        "timestamp": time.time(),
                        "cpu_percent": self.current_cpu_percent,
                        "memory_mb": self.current_memory_mb,
                    }
                )

            def get_current_metrics(self) -> K8sResourceMetrics:
                """Get current resource metrics."""
                return K8sResourceMetrics(
                    cpu_usage_percent=self.current_cpu_percent,
                    memory_usage_mb=self.current_memory_mb,
                    memory_limit_mb=self.memory_limit_mb,
                    cpu_limit_cores=self.cpu_limit_cores,
                    pod_status="Running" if self.oom_kills == 0 else "Restarting",
                    restart_count=self.oom_kills,
                    oom_kills=self.oom_kills,
                    throttle_events=self.throttle_events,
                )

            def set_resource_limits(self, cpu_cores: float, memory_mb: float):
                """Set resource limits for testing."""
                self.cpu_limit_cores = cpu_cores
                self.memory_limit_mb = memory_mb

        return MockK8sResourceMonitor()

    @pytest.fixture
    def resource_constrained_comment_monitor(self, mock_k8s_resource_monitor):
        """Comment monitor with resource monitoring."""

        class ResourceConstrainedCommentMonitor(CommentMonitor):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.resource_monitor = mock_k8s_resource_monitor
                self.processing_times = []
                self.error_count = 0

            def _simulate_cpu_intensive_operation(self, duration_ms: float):
                """Simulate CPU-intensive comment processing."""
                start_time = time.time()

                # Simulate CPU usage
                cpu_usage = min(
                    50 + (duration_ms / 10), 100
                )  # Scale CPU with processing time
                memory_usage = self.resource_monitor.current_memory_mb + (
                    duration_ms / 100
                )

                self.resource_monitor.simulate_resource_usage(cpu_usage, memory_usage)

                # Simulate processing delay
                time.sleep(duration_ms / 1000)

                processing_time = (time.time() - start_time) * 1000
                self.processing_times.append(processing_time)

            def _deduplicate_comments_with_resource_monitoring(
                self, comments: List[Dict[str, Any]]
            ) -> List[Dict[str, Any]]:
                """Enhanced deduplication with resource monitoring."""
                try:
                    # Simulate resource usage based on comment count
                    processing_intensity = min(
                        len(comments) * 0.5, 100
                    )  # 0.5ms per comment
                    self._simulate_cpu_intensive_operation(processing_intensity)

                    # Call original deduplication
                    return self._deduplicate_comments(comments)
                except Exception:
                    self.error_count += 1
                    raise

            def get_performance_metrics(self) -> Dict[str, float]:
                """Get performance metrics."""
                if not self.processing_times:
                    return {"avg_time": 0, "throughput": 0}

                avg_time = sum(self.processing_times) / len(self.processing_times)
                throughput = (
                    len(self.processing_times) / (sum(self.processing_times) / 1000)
                    if self.processing_times
                    else 0
                )

                return {
                    "avg_processing_time_ms": avg_time,
                    "throughput_ops_per_second": throughput,
                    "error_count": self.error_count,
                }

        mock_db_session = Mock()
        # Set up the query chain for deduplication: query().filter().all() should return empty list
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []  # No existing comments in DB
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()

        return ResourceConstrainedCommentMonitor(
            fake_threads_client=None, celery_client=Mock(), db_session=mock_db_session
        )

    @pytest.mark.e2e
    def test_performance_under_cpu_limits(
        self, resource_constrained_comment_monitor, mock_k8s_resource_monitor
    ):
        """
        Test comment monitoring performance under CPU resource limits.

        Validates that the system gracefully handles CPU constraints.
        """
        # Set conservative CPU limits
        mock_k8s_resource_monitor.set_resource_limits(cpu_cores=0.5, memory_mb=256)

        # Generate test comments
        test_comments = []
        for i in range(200):
            test_comments.append(
                {
                    "id": f"cpu_test_comment_{i}",
                    "post_id": f"cpu_test_post_{i % 20}",
                    "text": f"CPU constraint test comment {i} with additional content to simulate realistic processing load",
                    "author": f"cpu_user_{i % 50}",
                    "timestamp": f"2024-01-01T{10 + (i % 14):02d}:{i % 60:02d}:00Z",
                }
            )

        # Process comments in batches under CPU limits
        batch_size = 25
        batch_results = []

        for i in range(0, len(test_comments), batch_size):
            batch = test_comments[i : i + batch_size]

            start_time = time.time()
            unique_comments = resource_constrained_comment_monitor._deduplicate_comments_with_resource_monitoring(
                batch
            )
            processing_time = time.time() - start_time

            batch_results.append(
                {
                    "batch_id": i // batch_size,
                    "processed_count": len(unique_comments),
                    "processing_time": processing_time,
                    "resource_metrics": mock_k8s_resource_monitor.get_current_metrics(),
                }
            )

        # Analyze performance under CPU limits
        final_metrics = mock_k8s_resource_monitor.get_current_metrics()
        performance_metrics = (
            resource_constrained_comment_monitor.get_performance_metrics()
        )

        # CPU constraint assertions
        assert final_metrics.throttle_events < 3, (
            f"Too many CPU throttle events: {final_metrics.throttle_events}, "
            "system should handle CPU limits gracefully"
        )

        assert performance_metrics["avg_processing_time_ms"] < 1000, (
            f"Average processing time {performance_metrics['avg_processing_time_ms']:.2f}ms too high under CPU limits"
        )

        # Verify system stayed within CPU limits most of the time
        avg_cpu_usage = sum(
            b["resource_metrics"].cpu_usage_percent for b in batch_results
        ) / len(batch_results)
        cpu_limit_percent = final_metrics.cpu_limit_cores * 100

        assert avg_cpu_usage <= cpu_limit_percent * 1.2, (
            f"Average CPU usage {avg_cpu_usage:.1f}% significantly exceeds limit {cpu_limit_percent:.1f}%"
        )

        # Performance should be reasonable despite constraints
        total_processed = sum(b["processed_count"] for b in batch_results)
        assert total_processed > 0, "Should process comments despite CPU constraints"

        print(
            f"CPU constraint test: {avg_cpu_usage:.1f}% avg CPU, {performance_metrics['throughput_ops_per_second']:.1f} ops/s"
        )

    @pytest.mark.e2e
    def test_memory_usage_under_memory_limits(
        self, resource_constrained_comment_monitor, mock_k8s_resource_monitor
    ):
        """
        Test comment monitoring memory usage under memory resource limits.

        Validates that the system handles memory constraints without OOM kills.
        """
        # Set tight memory limits
        mock_k8s_resource_monitor.set_resource_limits(cpu_cores=2.0, memory_mb=128)

        # Generate memory-intensive test scenario
        large_comments = []
        for i in range(100):
            # Create comments with large text content
            large_text = (
                f"Large memory test comment {i} with extensive content. " * 50
            )  # ~2.5KB per comment
            large_comments.append(
                {
                    "id": f"memory_test_comment_{i}",
                    "post_id": f"memory_post_{i % 10}",
                    "text": large_text,
                    "author": f"memory_user_{i}",
                    "timestamp": f"2024-01-01T{11 + (i % 13):02d}:{i % 60:02d}:00Z",
                }
            )

        # Process in small batches to manage memory
        batch_size = 10
        memory_snapshots = []

        for i in range(0, len(large_comments), batch_size):
            batch = large_comments[i : i + batch_size]

            # Monitor memory before processing
            pre_metrics = mock_k8s_resource_monitor.get_current_metrics()

            # Process batch
            start_time = time.time()
            try:
                unique_comments = resource_constrained_comment_monitor._deduplicate_comments_with_resource_monitoring(
                    batch
                )
                processing_time = time.time() - start_time
                success = True
            except Exception:
                processing_time = time.time() - start_time
                success = False
                unique_comments = []

            # Monitor memory after processing
            post_metrics = mock_k8s_resource_monitor.get_current_metrics()

            memory_snapshots.append(
                {
                    "batch_id": i // batch_size,
                    "pre_memory_mb": pre_metrics.memory_usage_mb,
                    "post_memory_mb": post_metrics.memory_usage_mb,
                    "memory_delta": post_metrics.memory_usage_mb
                    - pre_metrics.memory_usage_mb,
                    "processing_time": processing_time,
                    "success": success,
                    "processed_count": len(unique_comments),
                }
            )

        # Analyze memory behavior
        final_metrics = mock_k8s_resource_monitor.get_current_metrics()
        peak_memory = max(s["post_memory_mb"] for s in memory_snapshots)
        successful_batches = sum(1 for s in memory_snapshots if s["success"])

        # Memory constraint assertions
        assert final_metrics.oom_kills == 0, (
            f"OOM kills occurred: {final_metrics.oom_kills}"
        )

        assert peak_memory <= final_metrics.memory_limit_mb * 1.1, (
            f"Peak memory {peak_memory:.2f}MB exceeded limit {final_metrics.memory_limit_mb}MB by too much"
        )

        # Most batches should succeed despite memory constraints
        success_rate = successful_batches / len(memory_snapshots)
        assert success_rate > 0.8, (
            f"Success rate {success_rate:.1%} too low under memory constraints"
        )

        # Memory growth per batch should be reasonable
        avg_memory_delta = sum(s["memory_delta"] for s in memory_snapshots) / len(
            memory_snapshots
        )
        assert avg_memory_delta < 20, (
            f"Average memory growth {avg_memory_delta:.2f}MB per batch too high"
        )

        print(
            f"Memory constraint test: {peak_memory:.2f}MB peak, {success_rate:.1%} success rate"
        )

    @pytest.mark.e2e
    def test_concurrent_processing_under_resource_limits(
        self, resource_constrained_comment_monitor, mock_k8s_resource_monitor
    ):
        """
        Test concurrent comment processing under combined resource limits.

        Validates system behavior when both CPU and memory are constrained.
        """
        # Set realistic production limits
        mock_k8s_resource_monitor.set_resource_limits(cpu_cores=1.0, memory_mb=256)

        def process_comments_with_constraints(worker_id: int):
            """Worker function for concurrent processing."""
            comments = []
            for i in range(50):
                comments.append(
                    {
                        "id": f"concurrent_comment_{worker_id}_{i}",
                        "post_id": f"concurrent_post_{worker_id}",
                        "text": f"Concurrent test comment {i} from worker {worker_id}",
                        "author": f"worker_{worker_id}_user_{i}",
                        "timestamp": f"2024-01-01T{12 + (i % 12):02d}:{i % 60:02d}:00Z",
                    }
                )

            start_time = time.time()
            try:
                unique_comments = resource_constrained_comment_monitor._deduplicate_comments_with_resource_monitoring(
                    comments
                )
                processing_time = time.time() - start_time

                return {
                    "worker_id": worker_id,
                    "success": True,
                    "processed_count": len(unique_comments),
                    "original_count": len(comments),
                    "processing_time": processing_time,
                    "final_metrics": mock_k8s_resource_monitor.get_current_metrics(),
                }
            except Exception as e:
                return {
                    "worker_id": worker_id,
                    "success": False,
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                    "final_metrics": mock_k8s_resource_monitor.get_current_metrics(),
                }

        # Run concurrent workers
        num_workers = 6
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(process_comments_with_constraints, worker_id)
                for worker_id in range(num_workers)
            ]

            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # Analyze concurrent performance under constraints
        successful_workers = [r for r in results if r["success"]]
        [r for r in results if not r["success"]]

        final_resource_metrics = mock_k8s_resource_monitor.get_current_metrics()

        # Concurrent processing assertions
        success_rate = len(successful_workers) / len(results)
        assert success_rate > 0.7, (
            f"Concurrent success rate {success_rate:.1%} too low under resource limits"
        )

        # Resource limits should not be severely violated
        assert final_resource_metrics.oom_kills <= 1, (
            f"Too many OOM kills during concurrent processing: {final_resource_metrics.oom_kills}"
        )

        assert final_resource_metrics.throttle_events < num_workers, (
            f"Excessive CPU throttling events: {final_resource_metrics.throttle_events}"
        )

        # Performance metrics
        if successful_workers:
            avg_processing_time = sum(
                r["processing_time"] for r in successful_workers
            ) / len(successful_workers)
            total_processed = sum(r["processed_count"] for r in successful_workers)
            concurrent_throughput = total_processed / total_time

            assert avg_processing_time < 5.0, (
                f"Average processing time {avg_processing_time:.2f}s too high for concurrent processing"
            )

            assert concurrent_throughput > 20, (
                f"Concurrent throughput {concurrent_throughput:.1f} comments/s too low"
            )

        print(
            f"Concurrent constraint test: {success_rate:.1%} success, "
            f"{final_resource_metrics.throttle_events} throttles, {final_resource_metrics.oom_kills} OOM kills"
        )

    @pytest.mark.e2e
    def test_resource_scaling_behavior(
        self, resource_constrained_comment_monitor, mock_k8s_resource_monitor
    ):
        """
        Test system behavior as resource limits are scaled up and down.

        Validates that performance scales appropriately with resource availability.
        """
        # Test different resource limit scenarios
        resource_scenarios = [
            {"cpu_cores": 0.25, "memory_mb": 64, "name": "very_low"},
            {"cpu_cores": 0.5, "memory_mb": 128, "name": "low"},
            {"cpu_cores": 1.0, "memory_mb": 256, "name": "medium"},
            {"cpu_cores": 2.0, "memory_mb": 512, "name": "high"},
        ]

        scaling_results = []

        for scenario in resource_scenarios:
            # Set resource limits
            mock_k8s_resource_monitor.set_resource_limits(
                scenario["cpu_cores"], scenario["memory_mb"]
            )

            # Reset resource monitor state
            mock_k8s_resource_monitor.oom_kills = 0
            mock_k8s_resource_monitor.throttle_events = 0

            # Generate test workload
            test_comments = []
            for i in range(100):
                test_comments.append(
                    {
                        "id": f"scaling_comment_{scenario['name']}_{i}",
                        "post_id": f"scaling_post_{scenario['name']}",
                        "text": f"Resource scaling test comment {i}",
                        "author": f"scaling_user_{i}",
                        "timestamp": f"2024-01-01T13:{i % 60:02d}:00Z",
                    }
                )

            # Process workload
            start_time = time.time()
            try:
                unique_comments = resource_constrained_comment_monitor._deduplicate_comments_with_resource_monitoring(
                    test_comments
                )
                processing_time = time.time() - start_time
                success = True
                error_message = None
            except Exception as e:
                processing_time = time.time() - start_time
                success = False
                error_message = str(e)
                unique_comments = []

            # Collect metrics
            resource_metrics = mock_k8s_resource_monitor.get_current_metrics()
            (resource_constrained_comment_monitor.get_performance_metrics())

            scaling_results.append(
                {
                    "scenario": scenario["name"],
                    "cpu_limit": scenario["cpu_cores"],
                    "memory_limit_mb": scenario["memory_mb"],
                    "success": success,
                    "processing_time": processing_time,
                    "processed_count": len(unique_comments),
                    "throughput": len(unique_comments) / processing_time
                    if processing_time > 0
                    else 0,
                    "oom_kills": resource_metrics.oom_kills,
                    "throttle_events": resource_metrics.throttle_events,
                    "peak_memory_mb": resource_metrics.memory_usage_mb,
                    "error_message": error_message,
                }
            )

        # Analyze scaling behavior
        successful_scenarios = [r for r in scaling_results if r["success"]]

        # Scaling assertions
        assert len(successful_scenarios) >= 3, (
            "At least 3 resource scenarios should succeed"
        )

        # Performance should generally improve with more resources
        if len(successful_scenarios) >= 2:
            low_resource_throughput = min(r["throughput"] for r in successful_scenarios)
            high_resource_throughput = max(
                r["throughput"] for r in successful_scenarios
            )

            scaling_factor = (
                high_resource_throughput / low_resource_throughput
                if low_resource_throughput > 0
                else 1
            )
            assert scaling_factor > 1.2, (
                f"Performance scaling factor {scaling_factor:.2f}x too low, "
                "system should benefit from additional resources"
            )

        # Very low resource scenarios may fail, but higher resource scenarios should succeed
        high_resource_scenarios = [r for r in scaling_results if r["cpu_limit"] >= 1.0]
        high_resource_success_rate = (
            sum(1 for r in high_resource_scenarios if r["success"])
            / len(high_resource_scenarios)
            if high_resource_scenarios
            else 0
        )

        assert high_resource_success_rate > 0.8, (
            f"High resource scenarios success rate {high_resource_success_rate:.1%} too low"
        )

        # Print scaling results
        for result in scaling_results:
            print(
                f"Scaling {result['scenario']}: "
                f"{result['throughput']:.1f} comments/s, "
                f"{'SUCCESS' if result['success'] else 'FAILED'}"
            )

    @pytest.mark.e2e
    def test_resource_monitoring_and_alerting(
        self, resource_constrained_comment_monitor, mock_k8s_resource_monitor
    ):
        """
        Test resource monitoring and alerting thresholds.

        Validates that resource monitoring correctly identifies constraint violations.
        """
        # Set alerting thresholds
        cpu_alert_threshold = 80.0  # 80% CPU
        memory_alert_threshold = 200.0  # 200MB memory

        mock_k8s_resource_monitor.set_resource_limits(cpu_cores=1.0, memory_mb=256)

        alert_events = []

        def check_resource_alerts(metrics: K8sResourceMetrics):
            """Check for resource threshold violations."""
            if metrics.cpu_usage_percent > cpu_alert_threshold:
                alert_events.append(
                    {
                        "type": "cpu_high",
                        "value": metrics.cpu_usage_percent,
                        "threshold": cpu_alert_threshold,
                        "timestamp": time.time(),
                    }
                )

            if metrics.memory_usage_mb > memory_alert_threshold:
                alert_events.append(
                    {
                        "type": "memory_high",
                        "value": metrics.memory_usage_mb,
                        "threshold": memory_alert_threshold,
                        "timestamp": time.time(),
                    }
                )

            if metrics.oom_kills > 0:
                alert_events.append(
                    {
                        "type": "oom_kill",
                        "value": metrics.oom_kills,
                        "timestamp": time.time(),
                    }
                )

        # Generate workload that triggers alerts
        high_load_comments = []
        for i in range(300):
            high_load_comments.append(
                {
                    "id": f"alert_test_comment_{i}",
                    "post_id": f"alert_post_{i % 30}",
                    "text": f"Resource alert test comment {i} with content designed to trigger resource usage alerts",
                    "author": f"alert_user_{i}",
                    "timestamp": f"2024-01-01T14:{i % 60:02d}:00Z",
                }
            )

        # Process in batches while monitoring resources
        batch_size = 30
        for i in range(0, len(high_load_comments), batch_size):
            batch = high_load_comments[i : i + batch_size]

            # Process batch
            resource_constrained_comment_monitor._deduplicate_comments_with_resource_monitoring(
                batch
            )

            # Check for alerts
            current_metrics = mock_k8s_resource_monitor.get_current_metrics()
            check_resource_alerts(current_metrics)

        # Analyze alerting behavior
        cpu_alerts = [a for a in alert_events if a["type"] == "cpu_high"]
        memory_alerts = [a for a in alert_events if a["type"] == "memory_high"]
        oom_alerts = [a for a in alert_events if a["type"] == "oom_kill"]

        # Alerting assertions
        # Should detect high resource usage
        assert len(cpu_alerts) > 0 or len(memory_alerts) > 0, (
            "Should detect resource threshold violations during high load"
        )

        # Alerts should be reasonable in frequency
        total_batches = len(high_load_comments) // batch_size
        alert_rate = len(alert_events) / total_batches
        assert alert_rate < 0.8, (
            f"Alert rate {alert_rate:.1%} too high, may indicate over-sensitive thresholds"
        )

        # Critical alerts (OOM kills) should be minimal
        assert len(oom_alerts) <= 1, f"Too many OOM kill alerts: {len(oom_alerts)}"

        print(
            f"Resource monitoring test: {len(cpu_alerts)} CPU alerts, "
            f"{len(memory_alerts)} memory alerts, {len(oom_alerts)} OOM alerts"
        )
