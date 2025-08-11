# /services/orchestrator/tests/test_comment_monitor_resilience.py
"""
Error handling and resilience tests for comment monitoring pipeline.

These tests validate graceful failure handling, recovery mechanisms,
circuit breakers, and system resilience under various failure scenarios.
"""

import pytest
import time
from unittest.mock import Mock
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import psycopg2

from services.orchestrator.comment_monitor import CommentMonitor


@dataclass
class ResilienceMetrics:
    """Metrics for resilience testing."""

    total_operations: int
    successful_operations: int
    failed_operations: int
    retry_attempts: int
    recovery_time_seconds: float
    circuit_breaker_trips: int
    fallback_activations: int


@dataclass
class FailureScenario:
    """Configuration for failure scenario testing."""

    name: str
    failure_type: str
    failure_rate: float
    duration_seconds: float
    expected_behavior: str


class TestCommentMonitorErrorHandling:
    """Error handling tests for various failure scenarios."""

    @pytest.fixture
    def failing_db_session(self):
        """Database session that simulates various database failures."""

        class FailingDBSession:
            def __init__(self):
                self.failure_mode = None
                self.failure_count = 0
                self.max_failures = 3
                self.operation_count = 0

            def set_failure_mode(self, mode: str, max_failures: int = 3):
                """Set failure mode for testing."""
                self.failure_mode = mode
                self.failure_count = 0
                self.max_failures = max_failures

            def query(self, model):
                """Mock query with failure simulation."""
                self.operation_count += 1

                if (
                    self.failure_mode == "connection_timeout"
                    and self.failure_count < self.max_failures
                ):
                    self.failure_count += 1
                    raise psycopg2.OperationalError("connection timeout")

                elif (
                    self.failure_mode == "deadlock"
                    and self.failure_count < self.max_failures
                ):
                    self.failure_count += 1
                    raise psycopg2.OperationalError("deadlock detected")

                elif (
                    self.failure_mode == "connection_lost"
                    and self.failure_count < self.max_failures
                ):
                    self.failure_count += 1
                    raise psycopg2.InterfaceError("connection already closed")

                # Success case or after max failures
                result_mock = Mock()
                result_mock.filter.return_value.first.return_value = None
                return result_mock

            def add(self, obj):
                """Mock add with failure simulation."""
                if (
                    self.failure_mode == "disk_full"
                    and self.failure_count < self.max_failures
                ):
                    self.failure_count += 1
                    raise psycopg2.OperationalError("disk full")

            def commit(self):
                """Mock commit with failure simulation."""
                if (
                    self.failure_mode == "commit_failure"
                    and self.failure_count < self.max_failures
                ):
                    self.failure_count += 1
                    raise psycopg2.OperationalError("could not serialize access")

            def rollback(self):
                """Mock rollback."""
                pass

        return FailingDBSession()

    @pytest.fixture
    def failing_celery_client(self):
        """Celery client that simulates queue failures."""

        class FailingCeleryClient:
            def __init__(self):
                self.failure_mode = None
                self.failure_count = 0
                self.max_failures = 3
                self.queued_tasks = []

            def set_failure_mode(self, mode: str, max_failures: int = 3):
                """Set failure mode for testing."""
                self.failure_mode = mode
                self.failure_count = 0
                self.max_failures = max_failures

            def send_task(self, task_name, args=None, kwargs=None, **options):
                """Mock send_task with failure simulation."""
                if (
                    self.failure_mode == "broker_connection_error"
                    and self.failure_count < self.max_failures
                ):
                    self.failure_count += 1
                    raise ConnectionError("broker connection failed")

                elif (
                    self.failure_mode == "queue_full"
                    and self.failure_count < self.max_failures
                ):
                    self.failure_count += 1
                    raise Exception("queue is full")

                elif (
                    self.failure_mode == "serialization_error"
                    and self.failure_count < self.max_failures
                ):
                    self.failure_count += 1
                    raise TypeError("Object of type Mock is not JSON serializable")

                # Success case
                self.queued_tasks.append(
                    {"task_name": task_name, "args": args, "kwargs": kwargs}
                )

        return FailingCeleryClient()

    @pytest.fixture
    def resilient_comment_monitor(self, failing_db_session, failing_celery_client):
        """Comment monitor with enhanced error handling and resilience."""

        class ResilientCommentMonitor(CommentMonitor):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.retry_attempts = 0
                self.circuit_breaker_trips = 0
                self.fallback_activations = 0
                self.error_log = []

            def _retry_with_backoff(
                self,
                operation: Callable,
                max_retries: int = 3,
                backoff_base: float = 1.0,
            ):
                """Retry operation with exponential backoff."""
                for attempt in range(max_retries + 1):
                    try:
                        return operation()
                    except Exception as e:
                        self.retry_attempts += 1
                        self.error_log.append(
                            {
                                "attempt": attempt + 1,
                                "error": str(e),
                                "timestamp": time.time(),
                            }
                        )

                        if attempt < max_retries:
                            backoff_time = backoff_base * (2**attempt)
                            time.sleep(backoff_time)
                        else:
                            raise e

            def _deduplicate_comments_with_resilience(
                self, comments: List[Dict[str, Any]]
            ) -> List[Dict[str, Any]]:
                """Enhanced deduplication with error handling and fallbacks."""

                def deduplication_operation():
                    return self._deduplicate_comments(comments)

                try:
                    return self._retry_with_backoff(
                        deduplication_operation, max_retries=3
                    )
                except Exception:
                    # Fallback: basic deduplication without DB lookup
                    self.fallback_activations += 1
                    unique_comments = []
                    seen_ids = set()

                    for comment in comments:
                        if comment["id"] not in seen_ids:
                            unique_comments.append(comment)
                            seen_ids.add(comment["id"])

                    return unique_comments

            def _store_comments_with_resilience(
                self, comments: List[Dict[str, Any]], post_id: str
            ):
                """Enhanced comment storage with error handling."""

                def storage_operation():
                    self._store_comments_in_db(comments, post_id)

                try:
                    return self._retry_with_backoff(storage_operation, max_retries=3)
                except Exception as e:
                    # Log error but don't fail the entire operation
                    self.error_log.append(
                        {
                            "operation": "storage",
                            "error": str(e),
                            "comment_count": len(comments),
                            "timestamp": time.time(),
                        }
                    )

            def _queue_comments_with_resilience(
                self, comments: List[Dict[str, Any]], post_id: str
            ):
                """Enhanced comment queuing with error handling."""

                def queuing_operation():
                    self._queue_comments_for_analysis(comments, post_id)

                try:
                    return self._retry_with_backoff(queuing_operation, max_retries=3)
                except Exception as e:
                    # Circuit breaker: stop queuing if too many failures
                    if (
                        len(
                            [
                                log
                                for log in self.error_log
                                if log.get("operation") == "queuing"
                            ]
                        )
                        > 5
                    ):
                        self.circuit_breaker_trips += 1
                        return  # Skip queuing to prevent cascading failures

                    self.error_log.append(
                        {
                            "operation": "queuing",
                            "error": str(e),
                            "comment_count": len(comments),
                            "timestamp": time.time(),
                        }
                    )

            def get_resilience_metrics(self) -> ResilienceMetrics:
                """Get resilience metrics for analysis."""
                successful_ops = sum(
                    1 for log in self.error_log if "success" in log.get("operation", "")
                )
                failed_ops = len(self.error_log)

                return ResilienceMetrics(
                    total_operations=successful_ops + failed_ops,
                    successful_operations=successful_ops,
                    failed_operations=failed_ops,
                    retry_attempts=self.retry_attempts,
                    recovery_time_seconds=0.0,  # Would be calculated in real implementation
                    circuit_breaker_trips=self.circuit_breaker_trips,
                    fallback_activations=self.fallback_activations,
                )

        return ResilientCommentMonitor(
            fake_threads_client=None,
            celery_client=failing_celery_client,
            db_session=failing_db_session,
        )

    def test_database_connection_failure_recovery(
        self, resilient_comment_monitor, failing_db_session
    ):
        """
        Test recovery from database connection failures.

        Validates that the system gracefully handles and recovers from DB failures.
        """
        # Configure database to fail initially
        failing_db_session.set_failure_mode("connection_timeout", max_failures=2)

        # Generate test comments
        test_comments = []
        for i in range(20):
            test_comments.append(
                {
                    "id": f"db_failure_comment_{i}",
                    "post_id": "db_failure_post",
                    "text": f"Database failure test comment {i}",
                    "author": f"db_user_{i}",
                    "timestamp": f"2024-01-01T10:{i:02d}:00Z",
                }
            )

        # Process comments with database failures
        start_time = time.time()
        unique_comments = (
            resilient_comment_monitor._deduplicate_comments_with_resilience(
                test_comments
            )
        )
        processing_time = time.time() - start_time

        # Analyze recovery behavior
        metrics = resilient_comment_monitor.get_resilience_metrics()

        # Recovery assertions
        assert len(unique_comments) > 0, (
            "Should successfully process comments after DB recovery"
        )
        assert metrics.retry_attempts > 0, (
            "Should have attempted retries for DB failures"
        )
        assert metrics.fallback_activations <= 1, (
            "Should recover without excessive fallback usage"
        )

        # Processing should complete in reasonable time despite retries
        assert processing_time < 10.0, (
            f"Processing time {processing_time:.2f}s too long for recovery scenario"
        )

        # Verify actual recovery occurred
        assert failing_db_session.failure_count >= 2, (
            "Should have encountered configured failures"
        )
        assert failing_db_session.operation_count > failing_db_session.failure_count, (
            "Should have successful operations after failures"
        )

        print(
            f"DB failure recovery: {metrics.retry_attempts} retries, {len(unique_comments)} comments processed"
        )

    def test_celery_broker_failure_handling(
        self, resilient_comment_monitor, failing_celery_client
    ):
        """
        Test handling of Celery broker connection failures.

        Validates that queue failures don't break the entire pipeline.
        """
        # Configure Celery to fail initially
        failing_celery_client.set_failure_mode(
            "broker_connection_error", max_failures=2
        )

        # Generate test comments
        test_comments = []
        for i in range(15):
            test_comments.append(
                {
                    "id": f"celery_failure_comment_{i}",
                    "post_id": "celery_failure_post",
                    "text": f"Celery failure test comment {i}",
                    "author": f"celery_user_{i}",
                    "timestamp": f"2024-01-01T11:{i:02d}:00Z",
                }
            )

        # Process comments with Celery failures
        start_time = time.time()
        resilient_comment_monitor._queue_comments_with_resilience(
            test_comments, "celery_failure_post"
        )
        time.time() - start_time

        # Analyze queue failure handling
        metrics = resilient_comment_monitor.get_resilience_metrics()

        # Failure handling assertions
        assert metrics.retry_attempts > 0, (
            "Should have attempted retries for Celery failures"
        )

        # Should eventually succeed or gracefully degrade
        queue_errors = [
            log
            for log in resilient_comment_monitor.error_log
            if log.get("operation") == "queuing"
        ]

        # Either successful recovery or graceful degradation
        if failing_celery_client.failure_count >= 2:
            # Recovery occurred - should have queued tasks
            assert len(failing_celery_client.queued_tasks) > 0, (
                "Should have successfully queued tasks after recovery"
            )
        else:
            # Graceful degradation - should have logged errors appropriately
            assert len(queue_errors) > 0, "Should have logged queue failures"

        print(
            f"Celery failure handling: {metrics.retry_attempts} retries, {len(failing_celery_client.queued_tasks)} tasks queued"
        )

    def test_concurrent_failure_scenarios(
        self, resilient_comment_monitor, failing_db_session, failing_celery_client
    ):
        """
        Test resilience under concurrent failure scenarios.

        Validates system behavior when multiple components fail simultaneously.
        """

        def process_batch_with_failures(batch_id: int):
            """Process comment batch with potential failures."""
            # Configure different failure modes for different batches
            if batch_id % 3 == 0:
                failing_db_session.set_failure_mode(
                    "connection_timeout", max_failures=1
                )
            elif batch_id % 3 == 1:
                failing_celery_client.set_failure_mode(
                    "broker_connection_error", max_failures=1
                )
            # batch_id % 3 == 2: no failures (control)

            comments = []
            for i in range(10):
                comments.append(
                    {
                        "id": f"concurrent_failure_comment_{batch_id}_{i}",
                        "post_id": f"concurrent_failure_post_{batch_id}",
                        "text": f"Concurrent failure test comment {i} from batch {batch_id}",
                        "author": f"concurrent_user_{batch_id}_{i}",
                        "timestamp": f"2024-01-01T12:{i:02d}:00Z",
                    }
                )

            start_time = time.time()
            try:
                # Process full pipeline with potential failures
                unique_comments = (
                    resilient_comment_monitor._deduplicate_comments_with_resilience(
                        comments
                    )
                )
                resilient_comment_monitor._store_comments_with_resilience(
                    unique_comments, f"concurrent_failure_post_{batch_id}"
                )
                resilient_comment_monitor._queue_comments_with_resilience(
                    unique_comments, f"concurrent_failure_post_{batch_id}"
                )

                processing_time = time.time() - start_time
                return {
                    "batch_id": batch_id,
                    "success": True,
                    "processed_count": len(unique_comments),
                    "processing_time": processing_time,
                }
            except Exception as e:
                processing_time = time.time() - start_time
                return {
                    "batch_id": batch_id,
                    "success": False,
                    "error": str(e),
                    "processing_time": processing_time,
                }

        # Process multiple batches concurrently with different failure patterns
        num_batches = 9
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(process_batch_with_failures, batch_id)
                for batch_id in range(num_batches)
            ]

            results = [future.result() for future in as_completed(futures)]

        time.time() - start_time

        # Analyze concurrent failure handling
        successful_batches = [r for r in results if r["success"]]
        failed_batches = [r for r in results if not r["success"]]

        success_rate = len(successful_batches) / len(results)
        metrics = resilient_comment_monitor.get_resilience_metrics()

        # Concurrent failure handling assertions
        assert success_rate > 0.6, (
            f"Success rate {success_rate:.1%} too low under concurrent failures"
        )

        # Should have reasonable retry behavior
        assert metrics.retry_attempts > 0, (
            "Should have attempted retries under concurrent failures"
        )
        assert metrics.retry_attempts < num_batches * 10, (
            "Should not have excessive retry attempts"
        )

        # Circuit breaker should prevent cascading failures
        if len(failed_batches) > 3:
            assert metrics.circuit_breaker_trips > 0, (
                "Circuit breaker should trip under high failure rate"
            )

        # Performance should be reasonable despite failures
        if successful_batches:
            avg_processing_time = sum(
                r["processing_time"] for r in successful_batches
            ) / len(successful_batches)
            assert avg_processing_time < 5.0, (
                f"Average processing time {avg_processing_time:.2f}s too high under failures"
            )

        print(
            f"Concurrent failures: {success_rate:.1%} success rate, {metrics.retry_attempts} retries, {metrics.circuit_breaker_trips} circuit breaker trips"
        )

    def test_cascading_failure_prevention(
        self, resilient_comment_monitor, failing_db_session, failing_celery_client
    ):
        """
        Test prevention of cascading failures across components.

        Validates that failure in one component doesn't cause system-wide failure.
        """
        # Configure persistent failures in both DB and Celery
        failing_db_session.set_failure_mode(
            "connection_lost", max_failures=999
        )  # Persistent failure
        failing_celery_client.set_failure_mode(
            "queue_full", max_failures=999
        )  # Persistent failure

        # Generate larger test dataset
        test_comments = []
        for i in range(50):
            test_comments.append(
                {
                    "id": f"cascading_failure_comment_{i}",
                    "post_id": f"cascading_failure_post_{i % 5}",
                    "text": f"Cascading failure prevention test comment {i}",
                    "author": f"cascade_user_{i}",
                    "timestamp": f"2024-01-01T13:{i % 60:02d}:00Z",
                }
            )

        # Process comments with persistent failures
        start_time = time.time()

        # Should not crash despite persistent failures
        try:
            unique_comments = (
                resilient_comment_monitor._deduplicate_comments_with_resilience(
                    test_comments
                )
            )
            resilient_comment_monitor._store_comments_with_resilience(
                unique_comments, "cascading_failure_post"
            )
            resilient_comment_monitor._queue_comments_with_resilience(
                unique_comments, "cascading_failure_post"
            )

            system_crashed = False
        except Exception as e:
            system_crashed = True
            str(e)

        processing_time = time.time() - start_time
        metrics = resilient_comment_monitor.get_resilience_metrics()

        # Cascading failure prevention assertions
        assert not system_crashed, "System should not crash under persistent failures"

        # Should use fallback mechanisms
        assert metrics.fallback_activations > 0, (
            "Should activate fallback mechanisms under persistent failures"
        )

        # Circuit breaker should engage
        assert metrics.circuit_breaker_trips > 0, (
            "Circuit breaker should trip to prevent cascading failures"
        )

        # Should complete processing in reasonable time (not hang indefinitely)
        assert processing_time < 30.0, (
            f"Processing time {processing_time:.2f}s too long, system may be hanging"
        )

        # Should still process some comments via fallback
        unique_comments = (
            resilient_comment_monitor._deduplicate_comments_with_resilience(
                test_comments
            )
        )
        assert len(unique_comments) > 0, (
            "Should process comments via fallback mechanisms"
        )

        print(
            f"Cascading failure prevention: {metrics.fallback_activations} fallbacks, {metrics.circuit_breaker_trips} circuit breaker trips"
        )

    @pytest.mark.parametrize(
        "failure_scenario",
        [
            FailureScenario(
                "db_timeout", "connection_timeout", 0.3, 5.0, "retry_and_recover"
            ),
            FailureScenario(
                "celery_connection",
                "broker_connection_error",
                0.5,
                3.0,
                "graceful_degradation",
            ),
            FailureScenario("disk_full", "disk_full", 0.8, 2.0, "fallback_activation"),
            FailureScenario(
                "serialization", "serialization_error", 0.4, 4.0, "error_handling"
            ),
        ],
    )
    def test_specific_failure_scenario_handling(
        self,
        failure_scenario,
        resilient_comment_monitor,
        failing_db_session,
        failing_celery_client,
    ):
        """
        Test handling of specific failure scenarios.

        Validates appropriate responses to different types of failures.
        """
        # Configure specific failure scenario
        max_failures = max(1, int(10 * failure_scenario.failure_rate))

        if (
            "db" in failure_scenario.failure_type
            or "disk" in failure_scenario.failure_type
        ):
            failing_db_session.set_failure_mode(
                failure_scenario.failure_type, max_failures
            )
        else:
            failing_celery_client.set_failure_mode(
                failure_scenario.failure_type, max_failures
            )

        # Generate test comments
        test_comments = []
        for i in range(20):
            test_comments.append(
                {
                    "id": f"scenario_{failure_scenario.name}_comment_{i}",
                    "post_id": f"scenario_{failure_scenario.name}_post",
                    "text": f"Scenario {failure_scenario.name} test comment {i}",
                    "author": f"scenario_user_{i}",
                    "timestamp": f"2024-01-01T14:{i:02d}:00Z",
                }
            )

        # Process with specific failure scenario
        start_time = time.time()
        processing_successful = True

        try:
            unique_comments = (
                resilient_comment_monitor._deduplicate_comments_with_resilience(
                    test_comments
                )
            )
            resilient_comment_monitor._store_comments_with_resilience(
                unique_comments, f"scenario_{failure_scenario.name}_post"
            )
            resilient_comment_monitor._queue_comments_with_resilience(
                unique_comments, f"scenario_{failure_scenario.name}_post"
            )
        except Exception as e:
            processing_successful = False
            str(e)

        processing_time = time.time() - start_time
        metrics = resilient_comment_monitor.get_resilience_metrics()

        # Scenario-specific behavior validation
        if failure_scenario.expected_behavior == "retry_and_recover":
            assert processing_successful, (
                f"Should recover from {failure_scenario.name} failures"
            )
            assert metrics.retry_attempts > 0, (
                "Should attempt retries for recoverable failures"
            )

        elif failure_scenario.expected_behavior == "graceful_degradation":
            # Should either succeed or fail gracefully without crashing
            assert processing_time < failure_scenario.duration_seconds * 3, (
                "Should not hang during graceful degradation"
            )

        elif failure_scenario.expected_behavior == "fallback_activation":
            assert metrics.fallback_activations > 0, (
                f"Should activate fallbacks for {failure_scenario.name}"
            )

        elif failure_scenario.expected_behavior == "error_handling":
            # Should handle errors appropriately (log, retry, or fail gracefully)
            assert len(resilient_comment_monitor.error_log) > 0, (
                "Should log errors appropriately"
            )

        # Performance should be reasonable for all scenarios
        assert processing_time < 15.0, (
            f"Processing time {processing_time:.2f}s too long for {failure_scenario.name}"
        )

        print(
            f"Scenario {failure_scenario.name}: {'SUCCESS' if processing_successful else 'HANDLED'}, "
            f"{metrics.retry_attempts} retries, {metrics.fallback_activations} fallbacks"
        )
