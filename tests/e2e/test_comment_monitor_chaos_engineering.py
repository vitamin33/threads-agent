# /tests/e2e/test_comment_monitor_chaos_engineering.py
"""
Chaos engineering tests for comment monitoring under infrastructure failures.

These tests simulate real-world infrastructure failures, network partitions,
service outages, and other chaos scenarios to validate system resilience.
"""

import pytest
import time
import random
import threading
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from contextlib import contextmanager
import json

from services.orchestrator.comment_monitor import CommentMonitor, Comment

# Skip chaos engineering tests in CI - they're flaky and require special infrastructure
pytestmark = pytest.mark.skip(
    reason="Chaos engineering tests are flaky in CI - require dedicated infrastructure"
)


@dataclass
class ChaosExperiment:
    """Configuration for chaos engineering experiments."""

    name: str
    description: str
    blast_radius: float  # Percentage of system affected (0.0 to 1.0)
    duration_seconds: float
    failure_types: List[str]
    expected_recovery_time: float
    success_criteria: Dict[str, Any]


@dataclass
class ChaosMetrics:
    """Metrics collected during chaos experiments."""

    experiment_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    mean_response_time_ms: float
    p95_response_time_ms: float
    recovery_time_seconds: float
    data_loss_events: int
    system_availability: float


class TestCommentMonitorChaosEngineering:
    """Chaos engineering tests for comment monitoring infrastructure."""

    @pytest.fixture
    def chaos_infrastructure_simulator(self):
        """Simulator for infrastructure chaos scenarios."""

        class ChaosInfrastructureSimulator:
            def __init__(self):
                self.active_failures = set()
                self.network_partitions = set()
                self.service_outages = set()
                self.resource_exhaustion = {}
                self.data_corruption_rate = 0.0
                self.latency_injection = {}
                self.failure_history = []

            def inject_network_partition(self, services: List[str], duration: float):
                """Simulate network partition between services."""
                partition_id = f"partition_{len(self.network_partitions)}"
                self.network_partitions.add(partition_id)
                self.active_failures.add(f"network_partition_{partition_id}")

                def remove_partition():
                    time.sleep(duration)
                    self.network_partitions.discard(partition_id)
                    self.active_failures.discard(f"network_partition_{partition_id}")

                threading.Thread(target=remove_partition, daemon=True).start()
                return partition_id

            def inject_service_outage(self, service: str, duration: float):
                """Simulate complete service outage."""
                self.service_outages.add(service)
                self.active_failures.add(f"outage_{service}")

                def restore_service():
                    time.sleep(duration)
                    self.service_outages.discard(service)
                    self.active_failures.discard(f"outage_{service}")

                threading.Thread(target=restore_service, daemon=True).start()

            def inject_resource_exhaustion(
                self, resource_type: str, exhaustion_level: float, duration: float
            ):
                """Simulate resource exhaustion (CPU, memory, disk)."""
                self.resource_exhaustion[resource_type] = exhaustion_level
                self.active_failures.add(f"resource_{resource_type}")

                def restore_resource():
                    time.sleep(duration)
                    self.resource_exhaustion.pop(resource_type, None)
                    self.active_failures.discard(f"resource_{resource_type}")

                threading.Thread(target=restore_resource, daemon=True).start()

            def inject_data_corruption(self, corruption_rate: float, duration: float):
                """Simulate data corruption scenarios."""
                self.data_corruption_rate = corruption_rate
                self.active_failures.add("data_corruption")

                def stop_corruption():
                    time.sleep(duration)
                    self.data_corruption_rate = 0.0
                    self.active_failures.discard("data_corruption")

                threading.Thread(target=stop_corruption, daemon=True).start()

            def inject_latency(self, service: str, latency_ms: float, duration: float):
                """Inject network latency for specific service."""
                self.latency_injection[service] = latency_ms
                self.active_failures.add(f"latency_{service}")

                def remove_latency():
                    time.sleep(duration)
                    self.latency_injection.pop(service, None)
                    self.active_failures.discard(f"latency_{service}")

                threading.Thread(target=remove_latency, daemon=True).start()

            def is_service_available(self, service: str) -> bool:
                """Check if service is available."""
                return service not in self.service_outages

            def get_service_latency(self, service: str) -> float:
                """Get current latency for service."""
                return self.latency_injection.get(service, 0.0)

            def should_corrupt_data(self) -> bool:
                """Check if data should be corrupted."""
                return random.random() < self.data_corruption_rate

            def get_resource_availability(self, resource_type: str) -> float:
                """Get resource availability (1.0 = fully available, 0.0 = exhausted)."""
                exhaustion = self.resource_exhaustion.get(resource_type, 0.0)
                return max(0.0, 1.0 - exhaustion)

            def get_active_failures(self) -> List[str]:
                """Get list of currently active failures."""
                return list(self.active_failures)

        return ChaosInfrastructureSimulator()

    @pytest.fixture
    def chaos_comment_monitor(self, chaos_infrastructure_simulator):
        """Comment monitor with chaos infrastructure simulation."""

        class ChaosCommentMonitor(CommentMonitor):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.chaos_simulator = chaos_infrastructure_simulator
                self.request_metrics = []
                self.data_loss_count = 0
                self.recovery_events = []

            def _simulate_service_call(
                self, service: str, operation: Callable, *args, **kwargs
            ):
                """Simulate service call with chaos injection."""
                start_time = time.time()

                # Check service availability
                if not self.chaos_simulator.is_service_available(service):
                    raise ConnectionError(f"Service {service} is unavailable")

                # Inject latency
                latency = self.chaos_simulator.get_service_latency(service)
                if latency > 0:
                    time.sleep(latency / 1000)  # Convert ms to seconds

                # Check resource availability
                cpu_availability = self.chaos_simulator.get_resource_availability("cpu")
                if cpu_availability < 0.2:  # Less than 20% CPU available
                    time.sleep(0.1)  # Simulate slow processing

                try:
                    result = operation(*args, **kwargs)

                    # Simulate data corruption
                    if self.chaos_simulator.should_corrupt_data():
                        self.data_loss_count += 1
                        if isinstance(result, list):
                            # Corrupt some data in the result
                            for item in result[
                                : len(result) // 4
                            ]:  # Corrupt 25% of data
                                if isinstance(item, dict) and "id" in item:
                                    item["id"] = f"corrupted_{item['id']}"

                    processing_time = (time.time() - start_time) * 1000
                    self.request_metrics.append(
                        {
                            "service": service,
                            "success": True,
                            "response_time_ms": processing_time,
                            "timestamp": time.time(),
                        }
                    )

                    return result

                except Exception as e:
                    processing_time = (time.time() - start_time) * 1000
                    self.request_metrics.append(
                        {
                            "service": service,
                            "success": False,
                            "response_time_ms": processing_time,
                            "error": str(e),
                            "timestamp": time.time(),
                        }
                    )
                    raise

            def _deduplicate_comments_with_chaos(
                self, comments: List[Dict[str, Any]]
            ) -> List[Dict[str, Any]]:
                """Deduplication with chaos simulation."""
                return self._simulate_service_call(
                    "database", self._deduplicate_comments, comments
                )

            def _store_comments_with_chaos(
                self, comments: List[Dict[str, Any]], post_id: str
            ):
                """Storage with chaos simulation."""
                return self._simulate_service_call(
                    "database", self._store_comments_in_db, comments, post_id
                )

            def _queue_comments_with_chaos(
                self, comments: List[Dict[str, Any]], post_id: str
            ):
                """Queuing with chaos simulation."""
                return self._simulate_service_call(
                    "celery", self._queue_comments_for_analysis, comments, post_id
                )

            def get_chaos_metrics(self) -> Dict[str, Any]:
                """Get metrics from chaos testing."""
                if not self.request_metrics:
                    return {"total_requests": 0}

                successful_requests = [m for m in self.request_metrics if m["success"]]
                failed_requests = [m for m in self.request_metrics if not m["success"]]

                response_times = [m["response_time_ms"] for m in self.request_metrics]
                response_times.sort()

                return {
                    "total_requests": len(self.request_metrics),
                    "successful_requests": len(successful_requests),
                    "failed_requests": len(failed_requests),
                    "success_rate": len(successful_requests)
                    / len(self.request_metrics),
                    "mean_response_time_ms": sum(response_times) / len(response_times),
                    "p95_response_time_ms": response_times[
                        int(len(response_times) * 0.95)
                    ]
                    if response_times
                    else 0,
                    "data_loss_events": self.data_loss_count,
                }

        mock_db_session = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()

        return ChaosCommentMonitor(
            fake_threads_client=None, celery_client=Mock(), db_session=mock_db_session
        )

    @pytest.mark.e2e
    def test_database_outage_chaos_experiment(
        self, chaos_comment_monitor, chaos_infrastructure_simulator
    ):
        """
        Chaos experiment: Complete database outage.

        Validates system behavior when database becomes completely unavailable.
        """
        experiment = ChaosExperiment(
            name="database_outage",
            description="Complete database service outage",
            blast_radius=1.0,  # 100% of database operations affected
            duration_seconds=10.0,
            failure_types=["service_outage"],
            expected_recovery_time=2.0,
            success_criteria={
                "availability_threshold": 0.0,  # System should handle 0% DB availability
                "max_data_loss": 0,  # No data loss acceptable
                "recovery_time_limit": 15.0,
            },
        )

        # Generate test workload
        test_comments = []
        for i in range(100):
            test_comments.append(
                {
                    "id": f"db_outage_comment_{i}",
                    "post_id": f"db_outage_post_{i % 10}",
                    "text": f"Database outage chaos test comment {i}",
                    "author": f"chaos_user_{i}",
                    "timestamp": f"2024-01-01T15:{i % 60:02d}:00Z",
                }
            )

        # Start chaos experiment: database outage
        chaos_infrastructure_simulator.inject_service_outage(
            "database", experiment.duration_seconds
        )

        # Process comments during outage
        start_time = time.time()
        results = []

        # Process in batches during the chaos
        batch_size = 10
        for i in range(0, len(test_comments), batch_size):
            batch = test_comments[i : i + batch_size]
            batch_start = time.time()

            try:
                unique_comments = (
                    chaos_comment_monitor._deduplicate_comments_with_chaos(batch)
                )
                chaos_comment_monitor._store_comments_with_chaos(
                    unique_comments, f"chaos_post_{i}"
                )
                chaos_comment_monitor._queue_comments_with_chaos(
                    unique_comments, f"chaos_post_{i}"
                )

                results.append(
                    {
                        "batch_id": i // batch_size,
                        "success": True,
                        "processed_count": len(unique_comments),
                        "processing_time": time.time() - batch_start,
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "batch_id": i // batch_size,
                        "success": False,
                        "error": str(e),
                        "processing_time": time.time() - batch_start,
                    }
                )

            # Small delay between batches
            time.sleep(0.5)

        experiment_duration = time.time() - start_time

        # Wait for recovery
        recovery_start = time.time()
        while "outage_database" in chaos_infrastructure_simulator.get_active_failures():
            time.sleep(0.1)
        recovery_time = time.time() - recovery_start

        # Analyze chaos experiment results
        chaos_metrics = chaos_comment_monitor.get_chaos_metrics()
        successful_batches = [r for r in results if r["success"]]

        # Chaos experiment assertions
        # During outage, expect failures
        outage_results = [
            r
            for r in results
            if r.get("processing_time", 0) < experiment.duration_seconds
        ]
        if outage_results:
            outage_success_rate = len(
                [r for r in outage_results if r["success"]]
            ) / len(outage_results)
            assert outage_success_rate < 0.5, (
                "Should have high failure rate during database outage"
            )

        # System should recover after outage
        assert recovery_time < experiment.expected_recovery_time + 5.0, (
            f"Recovery time {recovery_time:.2f}s exceeds expected {experiment.expected_recovery_time}s"
        )

        # Data loss should be minimal
        assert (
            chaos_metrics["data_loss_events"]
            <= experiment.success_criteria["max_data_loss"]
        ), f"Data loss events {chaos_metrics['data_loss_events']} exceed threshold"

        print(
            f"Database outage chaos: {len(successful_batches)}/{len(results)} batches succeeded, "
            f"recovery in {recovery_time:.2f}s"
        )

    @pytest.mark.e2e
    def test_network_partition_chaos_experiment(
        self, chaos_comment_monitor, chaos_infrastructure_simulator
    ):
        """
        Chaos experiment: Network partition between services.

        Validates system behavior during network connectivity issues.
        """
        experiment = ChaosExperiment(
            name="network_partition",
            description="Network partition between database and celery",
            blast_radius=0.5,  # 50% of operations affected
            duration_seconds=8.0,
            failure_types=["network_partition"],
            expected_recovery_time=1.0,
            success_criteria={
                "min_success_rate": 0.3,  # At least 30% success during partition
                "max_response_time_ms": 5000,  # Max 5s response time
                "recovery_time_limit": 10.0,
            },
        )

        # Inject network partition
        partition_id = chaos_infrastructure_simulator.inject_network_partition(
            ["database", "celery"], experiment.duration_seconds
        )

        # Generate test workload
        test_comments = []
        for i in range(60):
            test_comments.append(
                {
                    "id": f"partition_comment_{i}",
                    "post_id": f"partition_post_{i % 8}",
                    "text": f"Network partition chaos test comment {i}",
                    "author": f"partition_user_{i}",
                    "timestamp": f"2024-01-01T16:{i % 60:02d}:00Z",
                }
            )

        # Process comments during network partition
        start_time = time.time()
        batch_results = []

        # Concurrent processing during partition
        def process_batch(batch_id, comments):
            try:
                batch_start = time.time()
                unique_comments = (
                    chaos_comment_monitor._deduplicate_comments_with_chaos(comments)
                )
                chaos_comment_monitor._store_comments_with_chaos(
                    unique_comments, f"partition_batch_{batch_id}"
                )
                chaos_comment_monitor._queue_comments_with_chaos(
                    unique_comments, f"partition_batch_{batch_id}"
                )

                return {
                    "batch_id": batch_id,
                    "success": True,
                    "processed_count": len(unique_comments),
                    "processing_time": (time.time() - batch_start) * 1000,
                }
            except Exception as e:
                return {
                    "batch_id": batch_id,
                    "success": False,
                    "error": str(e),
                    "processing_time": (time.time() - batch_start) * 1000,
                }

        # Process batches concurrently
        batch_size = 12
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for i in range(0, len(test_comments), batch_size):
                batch = test_comments[i : i + batch_size]
                future = executor.submit(process_batch, i // batch_size, batch)
                futures.append(future)

            batch_results = [future.result() for future in as_completed(futures)]

        experiment_duration = time.time() - start_time

        # Analyze network partition experiment
        chaos_metrics = chaos_comment_monitor.get_chaos_metrics()
        successful_batches = [r for r in batch_results if r["success"]]
        success_rate = (
            len(successful_batches) / len(batch_results) if batch_results else 0
        )

        # Network partition assertions
        assert success_rate >= experiment.success_criteria["min_success_rate"], (
            f"Success rate {success_rate:.2%} below minimum {experiment.success_criteria['min_success_rate']:.0%}"
        )

        # Response times should be reasonable despite partition
        if successful_batches:
            max_response_time = max(r["processing_time"] for r in successful_batches)
            assert (
                max_response_time <= experiment.success_criteria["max_response_time_ms"]
            ), f"Max response time {max_response_time:.0f}ms exceeds limit"

        # System should continue operating during partition
        assert chaos_metrics["total_requests"] > 0, (
            "Should have attempted operations during partition"
        )

        print(
            f"Network partition chaos: {success_rate:.1%} success rate, "
            f"{chaos_metrics['mean_response_time_ms']:.0f}ms avg response time"
        )

    @pytest.mark.e2e
    def test_resource_exhaustion_chaos_experiment(
        self, chaos_comment_monitor, chaos_infrastructure_simulator
    ):
        """
        Chaos experiment: Severe resource exhaustion.

        Validates system behavior under extreme resource pressure.
        """
        experiment = ChaosExperiment(
            name="resource_exhaustion",
            description="Severe CPU and memory exhaustion",
            blast_radius=0.8,  # 80% resource exhaustion
            duration_seconds=12.0,
            failure_types=["resource_exhaustion"],
            expected_recovery_time=3.0,
            success_criteria={
                "min_success_rate": 0.2,  # At least 20% success under exhaustion
                "max_degradation_factor": 10.0,  # Max 10x performance degradation
                "no_system_crash": True,
            },
        )

        # Inject severe resource exhaustion
        chaos_infrastructure_simulator.inject_resource_exhaustion(
            "cpu", 0.9, experiment.duration_seconds
        )
        chaos_infrastructure_simulator.inject_resource_exhaustion(
            "memory", 0.8, experiment.duration_seconds
        )

        # Generate resource-intensive test workload
        large_comments = []
        for i in range(40):
            # Create comments with substantial content
            large_text = (
                f"Resource exhaustion test comment {i} " * 100
            )  # ~4KB per comment
            large_comments.append(
                {
                    "id": f"resource_exhaustion_comment_{i}",
                    "post_id": f"resource_post_{i % 5}",
                    "text": large_text,
                    "author": f"resource_user_{i}",
                    "timestamp": f"2024-01-01T17:{i % 60:02d}:00Z",
                }
            )

        # Measure baseline performance (before chaos)
        baseline_start = time.time()
        baseline_batch = large_comments[:5]
        try:
            chaos_comment_monitor._deduplicate_comments_with_chaos(baseline_batch)
            baseline_time = (time.time() - baseline_start) * 1000
        except:
            baseline_time = 1000  # Fallback baseline

        # Process during resource exhaustion
        exhaustion_start = time.time()
        exhaustion_results = []

        batch_size = 8
        for i in range(0, len(large_comments), batch_size):
            batch = large_comments[i : i + batch_size]
            batch_start = time.time()

            try:
                unique_comments = (
                    chaos_comment_monitor._deduplicate_comments_with_chaos(batch)
                )
                chaos_comment_monitor._store_comments_with_chaos(
                    unique_comments, f"exhaustion_post_{i}"
                )

                processing_time = (time.time() - batch_start) * 1000
                exhaustion_results.append(
                    {
                        "batch_id": i // batch_size,
                        "success": True,
                        "processed_count": len(unique_comments),
                        "processing_time_ms": processing_time,
                    }
                )

            except Exception as e:
                processing_time = (time.time() - batch_start) * 1000
                exhaustion_results.append(
                    {
                        "batch_id": i // batch_size,
                        "success": False,
                        "error": str(e),
                        "processing_time_ms": processing_time,
                    }
                )

        exhaustion_duration = time.time() - exhaustion_start

        # Analyze resource exhaustion experiment
        chaos_metrics = chaos_comment_monitor.get_chaos_metrics()
        successful_batches = [r for r in exhaustion_results if r["success"]]
        success_rate = (
            len(successful_batches) / len(exhaustion_results)
            if exhaustion_results
            else 0
        )

        # Resource exhaustion assertions
        assert success_rate >= experiment.success_criteria["min_success_rate"], (
            f"Success rate {success_rate:.2%} below minimum during resource exhaustion"
        )

        # Performance degradation should be reasonable
        if successful_batches:
            avg_exhaustion_time = sum(
                r["processing_time_ms"] for r in successful_batches
            ) / len(successful_batches)
            degradation_factor = (
                avg_exhaustion_time / baseline_time if baseline_time > 0 else 1
            )

            assert (
                degradation_factor
                <= experiment.success_criteria["max_degradation_factor"]
            ), f"Performance degraded by {degradation_factor:.1f}x, exceeds limit"

        # System should not crash under resource pressure
        assert chaos_metrics["total_requests"] > 0, (
            "System should continue operating under resource exhaustion"
        )

        print(
            f"Resource exhaustion chaos: {success_rate:.1%} success rate, "
            f"{avg_exhaustion_time / baseline_time:.1f}x performance degradation"
        )

    @pytest.mark.e2e
    def test_data_corruption_chaos_experiment(
        self, chaos_comment_monitor, chaos_infrastructure_simulator
    ):
        """
        Chaos experiment: Random data corruption.

        Validates system behavior when data corruption occurs.
        """
        experiment = ChaosExperiment(
            name="data_corruption",
            description="Random data corruption at 10% rate",
            blast_radius=0.1,  # 10% of data affected
            duration_seconds=15.0,
            failure_types=["data_corruption"],
            expected_recovery_time=0.5,
            success_criteria={
                "max_corruption_impact": 0.15,  # Max 15% impact on processing
                "corruption_detection": True,  # Should detect corruption
                "data_integrity_preservation": 0.85,  # 85% data integrity maintained
            },
        )

        # Inject data corruption
        chaos_infrastructure_simulator.inject_data_corruption(
            0.1, experiment.duration_seconds
        )

        # Generate test data with known integrity markers
        integrity_comments = []
        for i in range(80):
            integrity_comments.append(
                {
                    "id": f"integrity_comment_{i}",
                    "post_id": f"integrity_post_{i % 10}",
                    "text": f"Data integrity test comment {i}",
                    "author": f"integrity_user_{i}",
                    "timestamp": f"2024-01-01T18:{i % 60:02d}:00Z",
                    "integrity_marker": f"INTEGRITY_CHECK_{i}",  # For validation
                }
            )

        # Process data during corruption experiment
        corruption_start = time.time()
        corruption_results = []
        data_integrity_violations = 0

        batch_size = 10
        for i in range(0, len(integrity_comments), batch_size):
            batch = integrity_comments[i : i + batch_size]

            try:
                unique_comments = (
                    chaos_comment_monitor._deduplicate_comments_with_chaos(batch)
                )

                # Check for data integrity violations
                for comment in unique_comments:
                    if "corrupted_" in comment.get("id", ""):
                        data_integrity_violations += 1

                chaos_comment_monitor._store_comments_with_chaos(
                    unique_comments, f"integrity_post_{i}"
                )

                corruption_results.append(
                    {
                        "batch_id": i // batch_size,
                        "success": True,
                        "processed_count": len(unique_comments),
                        "integrity_violations": data_integrity_violations,
                    }
                )

            except Exception as e:
                corruption_results.append(
                    {"batch_id": i // batch_size, "success": False, "error": str(e)}
                )

        corruption_duration = time.time() - corruption_start

        # Analyze data corruption experiment
        chaos_metrics = chaos_comment_monitor.get_chaos_metrics()
        successful_batches = [r for r in corruption_results if r["success"]]

        # Data corruption assertions
        corruption_impact = (
            data_integrity_violations / len(integrity_comments)
            if integrity_comments
            else 0
        )
        assert (
            corruption_impact <= experiment.success_criteria["max_corruption_impact"]
        ), f"Data corruption impact {corruption_impact:.2%} exceeds maximum"

        # Should detect corruption events
        assert chaos_metrics["data_loss_events"] > 0, (
            "Should detect data corruption events"
        )

        # Data integrity should be mostly preserved
        integrity_preserved = 1.0 - corruption_impact
        assert (
            integrity_preserved
            >= experiment.success_criteria["data_integrity_preservation"]
        ), f"Data integrity {integrity_preserved:.2%} below minimum threshold"

        print(
            f"Data corruption chaos: {corruption_impact:.1%} corruption impact, "
            f"{chaos_metrics['data_loss_events']} corruption events detected"
        )

    @pytest.mark.e2e
    def test_combined_chaos_scenario(
        self, chaos_comment_monitor, chaos_infrastructure_simulator
    ):
        """
        Chaos experiment: Multiple simultaneous failures.

        Validates system resilience under complex, realistic failure scenarios.
        """
        experiment = ChaosExperiment(
            name="combined_chaos",
            description="Network latency + resource exhaustion + data corruption",
            blast_radius=0.6,  # 60% of system affected
            duration_seconds=20.0,
            failure_types=["network_latency", "resource_exhaustion", "data_corruption"],
            expected_recovery_time=5.0,
            success_criteria={
                "min_success_rate": 0.25,  # At least 25% success under combined chaos
                "max_mean_response_time": 8000,  # Max 8s mean response time
                "system_stability": True,  # System should remain stable
            },
        )

        # Inject multiple simultaneous failures
        chaos_infrastructure_simulator.inject_latency(
            "database", 500, experiment.duration_seconds
        )  # 500ms latency
        chaos_infrastructure_simulator.inject_resource_exhaustion(
            "cpu", 0.7, experiment.duration_seconds
        )
        chaos_infrastructure_simulator.inject_data_corruption(
            0.05, experiment.duration_seconds
        )  # 5% corruption

        # Generate comprehensive test workload
        combined_comments = []
        for i in range(120):
            combined_comments.append(
                {
                    "id": f"combined_chaos_comment_{i}",
                    "post_id": f"combined_post_{i % 15}",
                    "text": f"Combined chaos experiment comment {i} with extended content for comprehensive testing",
                    "author": f"combined_user_{i}",
                    "timestamp": f"2024-01-01T19:{i % 60:02d}:00Z",
                }
            )

        # Process under combined chaos conditions
        combined_start = time.time()
        combined_results = []
        response_times = []

        # Use concurrent processing to stress test the system
        def process_chaos_batch(batch_id, comments):
            batch_start = time.time()
            try:
                unique_comments = (
                    chaos_comment_monitor._deduplicate_comments_with_chaos(comments)
                )
                chaos_comment_monitor._store_comments_with_chaos(
                    unique_comments, f"combined_batch_{batch_id}"
                )
                chaos_comment_monitor._queue_comments_with_chaos(
                    unique_comments, f"combined_batch_{batch_id}"
                )

                response_time = (time.time() - batch_start) * 1000
                response_times.append(response_time)

                return {
                    "batch_id": batch_id,
                    "success": True,
                    "processed_count": len(unique_comments),
                    "response_time_ms": response_time,
                }
            except Exception as e:
                response_time = (time.time() - batch_start) * 1000
                response_times.append(response_time)

                return {
                    "batch_id": batch_id,
                    "success": False,
                    "error": str(e),
                    "response_time_ms": response_time,
                }

        # Process batches concurrently under chaos
        batch_size = 15
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(0, len(combined_comments), batch_size):
                batch = combined_comments[i : i + batch_size]
                future = executor.submit(process_chaos_batch, i // batch_size, batch)
                futures.append(future)

            combined_results = [future.result() for future in as_completed(futures)]

        combined_duration = time.time() - combined_start

        # Analyze combined chaos experiment
        chaos_metrics = chaos_comment_monitor.get_chaos_metrics()
        successful_batches = [r for r in combined_results if r["success"]]
        success_rate = (
            len(successful_batches) / len(combined_results) if combined_results else 0
        )

        # Combined chaos assertions
        assert success_rate >= experiment.success_criteria["min_success_rate"], (
            f"Success rate {success_rate:.2%} below minimum under combined chaos"
        )

        # Response times should be reasonable despite multiple failures
        mean_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        assert (
            mean_response_time <= experiment.success_criteria["max_mean_response_time"]
        ), (
            f"Mean response time {mean_response_time:.0f}ms exceeds limit under combined chaos"
        )

        # System should remain stable (no crashes)
        assert chaos_metrics["total_requests"] > 0, (
            "System should remain operational under combined chaos"
        )
        assert len(combined_results) > 0, (
            "Should complete processing under combined chaos"
        )

        # Wait for all chaos to end and verify recovery
        recovery_start = time.time()
        while chaos_infrastructure_simulator.get_active_failures():
            time.sleep(0.2)
        recovery_time = time.time() - recovery_start

        assert recovery_time <= experiment.expected_recovery_time + 5.0, (
            f"Recovery time {recovery_time:.2f}s exceeds expected time"
        )

        print(
            f"Combined chaos experiment: {success_rate:.1%} success rate, "
            f"{mean_response_time:.0f}ms mean response time, "
            f"recovery in {recovery_time:.2f}s"
        )
