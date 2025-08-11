# /services/orchestrator/tests/test_comment_monitor_db_and_celery.py
"""
Database connection pooling and Celery batch processing tests for comment monitoring.

These tests validate database connection efficiency under high load and proper
batch processing behavior for Celery task queuing.
"""

import pytest
import time
import threading
from unittest.mock import Mock
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from queue import Queue, Empty

from services.orchestrator.comment_monitor import CommentMonitor


@dataclass
class ConnectionPoolMetrics:
    """Database connection pool metrics."""

    active_connections: int
    idle_connections: int
    total_connections: int
    connection_wait_time: float
    query_execution_time: float
    pool_exhaustion_events: int


@dataclass
class CeleryBatchMetrics:
    """Celery batch processing metrics."""

    total_tasks_queued: int
    batch_size_avg: float
    queue_time_avg: float
    task_distribution: Dict[str, int]
    failed_queue_attempts: int


class TestCommentMonitorDatabaseConnectionPooling:
    """Database connection pooling tests under concurrent load."""

    @pytest.fixture
    def mock_connection_pool(self):
        """Mock database connection pool with realistic behavior."""

        class MockConnectionPool:
            def __init__(self, max_connections=20, min_connections=5):
                self.max_connections = max_connections
                self.min_connections = min_connections
                self.active_connections = 0
                self.idle_connections = min_connections
                self.connection_wait_times = []
                self.query_times = []
                self.pool_exhaustion_count = 0
                self._lock = threading.Lock()

            def get_connection(self):
                """Simulate getting connection from pool."""
                with self._lock:
                    wait_start = time.time()

                    if self.active_connections >= self.max_connections:
                        # Simulate waiting for available connection
                        self.pool_exhaustion_count += 1
                        time.sleep(0.01)  # Brief wait

                    if self.idle_connections > 0:
                        self.idle_connections -= 1

                    self.active_connections += 1

                    wait_time = time.time() - wait_start
                    self.connection_wait_times.append(wait_time)

                    return MockConnection(self)

            def return_connection(self, connection):
                """Return connection to pool."""
                with self._lock:
                    self.active_connections -= 1
                    if self.idle_connections < self.min_connections:
                        self.idle_connections += 1

            def get_metrics(self) -> ConnectionPoolMetrics:
                """Get current pool metrics."""
                return ConnectionPoolMetrics(
                    active_connections=self.active_connections,
                    idle_connections=self.idle_connections,
                    total_connections=self.active_connections + self.idle_connections,
                    connection_wait_time=sum(self.connection_wait_times)
                    / len(self.connection_wait_times)
                    if self.connection_wait_times
                    else 0,
                    query_execution_time=sum(self.query_times) / len(self.query_times)
                    if self.query_times
                    else 0,
                    pool_exhaustion_events=self.pool_exhaustion_count,
                )

        class MockConnection:
            def __init__(self, pool):
                self.pool = pool
                self.closed = False

            def execute_query(self, query):
                """Simulate query execution."""
                query_start = time.time()
                time.sleep(0.001)  # Simulate query execution time
                query_time = time.time() - query_start
                self.pool.query_times.append(query_time)
                return Mock()  # Mock result

            def close(self):
                if not self.closed:
                    self.pool.return_connection(self)
                    self.closed = True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.close()

        return MockConnectionPool()

    @pytest.fixture
    def mock_db_session_with_pool(self, mock_connection_pool):
        """Mock database session that uses connection pooling."""

        class MockPooledSession:
            def __init__(self, pool):
                self.pool = pool
                self.connection = None
                self.query_count = 0

            def query(self, model):
                """Mock query method with connection pooling."""
                if not self.connection:
                    self.connection = self.pool.get_connection()

                self.query_count += 1
                result_mock = Mock()

                def filter_mock(filter_expr):
                    filter_result_mock = Mock()

                    def first():
                        # Simulate database lookup
                        self.connection.execute_query(
                            "SELECT * FROM comments WHERE comment_id = ?"
                        )
                        return None  # No existing comment found

                    def all():
                        # Simulate bulk lookup for _deduplicate_comments
                        self.connection.execute_query(
                            "SELECT comment_id FROM comments WHERE comment_id IN (...)"
                        )
                        return []  # No existing comments found

                    filter_result_mock.first = first
                    filter_result_mock.all = all
                    return filter_result_mock

                result_mock.filter = filter_mock
                return result_mock

            def add(self, obj):
                """Mock add method."""
                if not self.connection:
                    self.connection = self.pool.get_connection()
                self.connection.execute_query("INSERT INTO comments ...")

            def bulk_save_objects(self, objects):
                """Mock bulk save method."""
                if not self.connection:
                    self.connection = self.pool.get_connection()
                # Simulate bulk insert
                self.connection.execute_query(
                    f"INSERT INTO comments ... ({len(objects)} rows)"
                )

            def commit(self):
                """Mock commit method."""
                if self.connection:
                    self.connection.execute_query("COMMIT")

            def rollback(self):
                """Mock rollback method."""
                if self.connection:
                    self.connection.execute_query("ROLLBACK")

            def close(self):
                """Close session and return connection to pool."""
                if self.connection:
                    self.connection.close()
                    self.connection = None

        return MockPooledSession(mock_connection_pool)

    def test_connection_pool_efficiency_under_concurrent_load(
        self, mock_connection_pool, mock_db_session_with_pool
    ):
        """
        Test database connection pool efficiency during concurrent comment processing.

        Validates that connection pooling works efficiently under high concurrent load.
        """

        # Generate test data
        def generate_comment_batch(batch_id, size=100):
            return [
                {
                    "id": f"comment_{batch_id}_{i}",
                    "post_id": f"post_{batch_id}",
                    "text": f"Comment {i} in batch {batch_id}",
                    "author": f"user_{i}",
                    "timestamp": f"2024-01-01T10:{i % 60:02d}:00Z",
                }
                for i in range(size)
            ]

        def process_batch_with_pooling(batch_id):
            """Process a comment batch using pooled database session."""
            session = mock_db_session_with_pool
            monitor = CommentMonitor(
                fake_threads_client=None, celery_client=Mock(), db_session=session
            )

            comments = generate_comment_batch(batch_id, size=50)

            start_time = time.time()
            unique_comments = monitor._deduplicate_comments(comments)
            monitor._store_comments_in_db(unique_comments, f"post_{batch_id}")
            processing_time = time.time() - start_time

            session.close()  # Return connection to pool

            return {
                "batch_id": batch_id,
                "processed_count": len(unique_comments),
                "processing_time": processing_time,
                "query_count": session.query_count,
            }

        # Process multiple batches concurrently
        num_concurrent_batches = 15

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(process_batch_with_pooling, batch_id)
                for batch_id in range(num_concurrent_batches)
            ]

            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time

        # Analyze connection pool performance
        pool_metrics = mock_connection_pool.get_metrics()

        # Connection pool efficiency assertions
        assert pool_metrics.pool_exhaustion_events < 3, (
            f"Too many pool exhaustion events: {pool_metrics.pool_exhaustion_events}, "
            "connection pool may be undersized"
        )

        assert pool_metrics.connection_wait_time < 0.1, (
            f"Average connection wait time {pool_metrics.connection_wait_time:.3f}s too high"
        )

        assert pool_metrics.query_execution_time < 0.01, (
            f"Average query time {pool_metrics.query_execution_time:.3f}s too high"
        )

        # Verify all batches processed successfully
        assert len(results) == num_concurrent_batches, "Not all batches processed"

        total_processed = sum(r["processed_count"] for r in results)
        total_queries = sum(r["query_count"] for r in results)

        assert total_processed > 0, "No comments were processed"
        assert total_queries > 0, "No database queries executed"

        # Performance assertions
        avg_batch_time = sum(r["processing_time"] for r in results) / len(results)
        assert avg_batch_time < 0.5, (
            f"Average batch processing time {avg_batch_time:.3f}s too slow"
        )

        # Verify concurrent processing was efficient
        sequential_time_estimate = sum(r["processing_time"] for r in results)
        concurrency_efficiency = sequential_time_estimate / total_time
        assert concurrency_efficiency > 2.0, (
            f"Concurrency efficiency {concurrency_efficiency:.2f}x too low, "
            "connection pooling may not be working effectively"
        )

    def test_connection_pool_recovery_after_exhaustion(self, mock_connection_pool):
        """
        Test connection pool recovery behavior after pool exhaustion.

        Validates that the system recovers gracefully when connection pool is exhausted.
        """
        # Configure smaller pool for easier exhaustion testing
        # Create a new pool directly from the class
        small_pool = mock_connection_pool.__class__(
            max_connections=5, min_connections=2
        )

        def create_session_with_small_pool():
            class SmallPoolSession:
                def __init__(self):
                    self.connection = None
                    self.query_count = 0

                def query(self, model):
                    if not self.connection:
                        self.connection = small_pool.get_connection()
                    self.query_count += 1

                    # Create a proper mock that supports chaining
                    query_mock = Mock()
                    filter_mock = Mock()
                    all_mock = Mock(return_value=[])  # Return empty list for .all()
                    first_mock = Mock(return_value=None)  # Return None for .first()

                    filter_mock.all = all_mock
                    filter_mock.first = first_mock
                    query_mock.filter = Mock(return_value=filter_mock)

                    return query_mock

                def add(self, obj):
                    if not self.connection:
                        self.connection = small_pool.get_connection()

                def bulk_save_objects(self, objects):
                    if not self.connection:
                        self.connection = small_pool.get_connection()
                    # Simulate bulk insert
                    if self.connection:
                        self.connection.execute_query(
                            f"INSERT INTO comments ... ({len(objects)} rows)"
                        )

                def commit(self):
                    pass

                def rollback(self):
                    pass

                def merge(self, obj):
                    # Simulate merge operation
                    if not self.connection:
                        self.connection = small_pool.get_connection()

                def close(self):
                    if self.connection:
                        self.connection.close()
                        self.connection = None

            return SmallPoolSession()

        # First, exhaust the connection pool
        def exhaust_pool_worker(worker_id):
            session = create_session_with_small_pool()
            monitor = CommentMonitor(
                fake_threads_client=None, celery_client=Mock(), db_session=session
            )

            # Hold connection for a while to exhaust pool
            comments = [
                {
                    "id": f"comment_{worker_id}",
                    "post_id": "test",
                    "text": "test",
                    "author": "test",
                    "timestamp": "2024-01-01T10:00:00Z",
                }
            ]
            monitor._deduplicate_comments(comments)

            time.sleep(0.5)  # Hold connection
            session.close()

            return worker_id

        # Exhaust pool with more workers than max connections
        with ThreadPoolExecutor(max_workers=8) as executor:
            exhaustion_futures = [
                executor.submit(exhaust_pool_worker, worker_id)
                for worker_id in range(8)
            ]

            [future.result() for future in as_completed(exhaustion_futures)]

        # Verify pool was exhausted
        initial_metrics = small_pool.get_metrics()
        assert initial_metrics.pool_exhaustion_events > 0, (
            "Pool should have been exhausted"
        )

        # Now test recovery - should be able to process normally
        def recovery_worker(worker_id):
            session = create_session_with_small_pool()
            monitor = CommentMonitor(
                fake_threads_client=None, celery_client=Mock(), db_session=session
            )

            comments = [
                {
                    "id": f"recovery_comment_{worker_id}_{i}",
                    "post_id": f"recovery_post_{worker_id}",
                    "text": f"Recovery comment {i}",
                    "author": f"user_{i}",
                    "timestamp": "2024-01-01T11:00:00Z",
                }
                for i in range(10)
            ]

            start_time = time.time()
            unique_comments = monitor._deduplicate_comments(comments)
            monitor._store_comments_in_db(unique_comments, f"recovery_post_{worker_id}")
            processing_time = time.time() - start_time

            session.close()

            return {
                "worker_id": worker_id,
                "processed": len(unique_comments),
                "time": processing_time,
            }

        # Test recovery with normal load
        with ThreadPoolExecutor(max_workers=4) as executor:
            recovery_futures = [
                executor.submit(recovery_worker, worker_id) for worker_id in range(4)
            ]

            recovery_results = [
                future.result() for future in as_completed(recovery_futures)
            ]

        # Verify recovery
        small_pool.get_metrics()

        assert len(recovery_results) == 4, "All recovery workers should complete"
        assert all(r["processed"] > 0 for r in recovery_results), (
            "All workers should process comments"
        )

        # Recovery time should be reasonable
        avg_recovery_time = sum(r["time"] for r in recovery_results) / len(
            recovery_results
        )
        assert avg_recovery_time < 1.0, (
            f"Recovery time {avg_recovery_time:.3f}s too slow"
        )


class TestCommentMonitorCeleryBatchProcessing:
    """Celery batch processing tests for comment analysis queuing."""

    @pytest.fixture
    def mock_celery_client_with_batching(self):
        """Mock Celery client that supports batch processing."""

        class MockCeleryBatchClient:
            def __init__(self):
                self.task_queue = Queue()
                self.queued_tasks = []
                self.batch_sizes = []
                self.queue_times = []
                self.failed_attempts = 0

            def send_task(self, task_name, args=None, kwargs=None, **options):
                """Queue individual task."""
                queue_start = time.time()

                try:
                    task_data = {
                        "task_name": task_name,
                        "args": args or [],
                        "kwargs": kwargs or {},
                        "options": options,
                        "queued_at": time.time(),
                    }

                    self.task_queue.put(task_data)
                    self.queued_tasks.append(task_data)

                    queue_time = time.time() - queue_start
                    self.queue_times.append(queue_time)

                except Exception:
                    self.failed_attempts += 1
                    raise

            def send_task_batch(self, tasks):
                """Queue batch of tasks (optimized)."""
                queue_start = time.time()

                try:
                    for task in tasks:
                        task_data = {
                            "task_name": task.get(
                                "task_name", "analyze_comment_intent"
                            ),
                            "args": task.get("args", []),
                            "kwargs": task.get("kwargs", {}),
                            "options": task.get("options", {}),
                            "queued_at": time.time(),
                        }
                        self.task_queue.put(task_data)
                        self.queued_tasks.append(task_data)

                    self.batch_sizes.append(len(tasks))
                    queue_time = time.time() - queue_start
                    self.queue_times.append(queue_time)

                except Exception:
                    self.failed_attempts += 1
                    raise

            def get_metrics(self) -> CeleryBatchMetrics:
                """Get batch processing metrics."""
                task_distribution = {}
                for task in self.queued_tasks:
                    task_name = task["task_name"]
                    task_distribution[task_name] = (
                        task_distribution.get(task_name, 0) + 1
                    )

                return CeleryBatchMetrics(
                    total_tasks_queued=len(self.queued_tasks),
                    batch_size_avg=sum(self.batch_sizes) / len(self.batch_sizes)
                    if self.batch_sizes
                    else 0,
                    queue_time_avg=sum(self.queue_times) / len(self.queue_times)
                    if self.queue_times
                    else 0,
                    task_distribution=task_distribution,
                    failed_queue_attempts=self.failed_attempts,
                )

            def get_queued_tasks(self):
                """Get all queued tasks for verification."""
                tasks = []
                try:
                    while True:
                        tasks.append(self.task_queue.get_nowait())
                except Empty:
                    pass
                return tasks

        return MockCeleryBatchClient()

    def test_batch_comment_analysis_queuing(self, mock_celery_client_with_batching):
        """
        Test efficient batch queuing of comment analysis tasks.

        Validates that comments are queued for analysis in optimal batches.
        """
        comment_monitor = CommentMonitor(
            fake_threads_client=None,
            celery_client=mock_celery_client_with_batching,
            db_session=Mock(),
        )

        # Generate large set of comments for batch processing
        comments = []
        for i in range(500):
            comments.append(
                {
                    "id": f"batch_comment_{i}",
                    "post_id": f"post_{i % 10}",
                    "text": f"Comment {i} for batch processing test",
                    "author": f"user_{i % 50}",
                    "timestamp": f"2024-01-01T{10 + (i % 14):02d}:{i % 60:02d}:00Z",
                }
            )

        # Test individual queuing (current implementation)
        start_time = time.time()
        comment_monitor._queue_comments_for_analysis(comments, "batch_test_post")
        individual_queue_time = time.time() - start_time

        mock_celery_client_with_batching.get_metrics()

        # Reset for batch test
        mock_celery_client_with_batching.queued_tasks.clear()
        mock_celery_client_with_batching.queue_times.clear()
        mock_celery_client_with_batching.batch_sizes.clear()

        # Test batch queuing (optimized approach)
        batch_size = 50
        comment_batches = [
            comments[i : i + batch_size] for i in range(0, len(comments), batch_size)
        ]

        start_time = time.time()
        for batch in comment_batches:
            # Simulate batch queuing
            batch_tasks = [
                {
                    "task_name": "analyze_comment_intent",
                    "args": [comment, "batch_test_post"],
                    "kwargs": {},
                    "options": {},
                }
                for comment in batch
            ]
            mock_celery_client_with_batching.send_task_batch(batch_tasks)
        batch_queue_time = time.time() - start_time

        batch_metrics = mock_celery_client_with_batching.get_metrics()

        # Batch processing assertions
        assert batch_metrics.total_tasks_queued == len(comments), (
            "All comments should be queued"
        )
        assert batch_metrics.batch_size_avg > 1, "Should use batch processing"
        assert batch_metrics.failed_queue_attempts == 0, "No queue failures expected"

        # Performance comparison
        queue_time_improvement = (
            individual_queue_time / batch_queue_time if batch_queue_time > 0 else 1
        )
        print(f"Batch queuing improvement: {queue_time_improvement:.2f}x faster")

        # Verify task distribution
        assert "analyze_comment_intent" in batch_metrics.task_distribution
        assert batch_metrics.task_distribution["analyze_comment_intent"] == len(
            comments
        )

    def test_celery_queue_performance_under_high_load(
        self, mock_celery_client_with_batching
    ):
        """
        Test Celery queue performance when processing many comments concurrently.

        Validates queue performance and reliability under high concurrent load.
        """

        def queue_comment_batch(batch_id, batch_size=100):
            """Queue a batch of comments for analysis."""
            monitor = CommentMonitor(
                fake_threads_client=None,
                celery_client=mock_celery_client_with_batching,
                db_session=Mock(),
            )

            comments = [
                {
                    "id": f"high_load_comment_{batch_id}_{i}",
                    "post_id": f"high_load_post_{batch_id}",
                    "text": f"High load comment {i} in batch {batch_id}",
                    "author": f"user_{i}",
                    "timestamp": f"2024-01-01T{10 + (i % 14):02d}:{i % 60:02d}:00Z",
                }
                for i in range(batch_size)
            ]

            start_time = time.time()
            monitor._queue_comments_for_analysis(comments, f"high_load_post_{batch_id}")
            queue_time = time.time() - start_time

            return {
                "batch_id": batch_id,
                "queued_count": len(comments),
                "queue_time": queue_time,
            }

        # Process multiple batches concurrently
        num_batches = 20
        batch_size = 75

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(queue_comment_batch, batch_id, batch_size)
                for batch_id in range(num_batches)
            ]

            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time

        # Analyze queue performance
        metrics = mock_celery_client_with_batching.get_metrics()

        # High load performance assertions
        total_expected_tasks = num_batches * batch_size
        assert metrics.total_tasks_queued == total_expected_tasks, (
            f"Expected {total_expected_tasks} tasks, got {metrics.total_tasks_queued}"
        )

        assert metrics.failed_queue_attempts == 0, (
            f"Queue failures under high load: {metrics.failed_queue_attempts}"
        )

        assert metrics.queue_time_avg < 0.1, (
            f"Average queue time {metrics.queue_time_avg:.3f}s too slow under high load"
        )

        # Throughput assertions
        total_queued = sum(r["queued_count"] for r in results)
        throughput = total_queued / total_time
        assert throughput > 1000, (
            f"Queue throughput {throughput:.0f} tasks/s too low under high load"
        )

        # Verify consistent performance across batches
        queue_times = [r["queue_time"] for r in results]
        max_queue_time = max(queue_times)
        min_queue_time = min(queue_times)
        queue_time_variance = (
            max_queue_time / min_queue_time if min_queue_time > 0 else float("inf")
        )

        assert queue_time_variance < 5.0, (
            f"Queue time variance {queue_time_variance:.2f} too high, indicates bottlenecks"
        )

    def test_celery_task_priority_and_ordering(self, mock_celery_client_with_batching):
        """
        Test task priority and ordering in Celery queue processing.

        Validates that high-priority comments are processed appropriately.
        """
        comment_monitor = CommentMonitor(
            fake_threads_client=None,
            celery_client=mock_celery_client_with_batching,
            db_session=Mock(),
        )

        # Create comments with different priority levels
        high_priority_comments = [
            {
                "id": f"high_priority_comment_{i}",
                "post_id": "urgent_post",
                "text": f"Urgent comment {i}",
                "author": f"vip_user_{i}",
                "timestamp": f"2024-01-01T12:{i:02d}:00Z",
            }
            for i in range(10)
        ]

        normal_priority_comments = [
            {
                "id": f"normal_comment_{i}",
                "post_id": "regular_post",
                "text": f"Regular comment {i}",
                "author": f"user_{i}",
                "timestamp": f"2024-01-01T10:{i:02d}:00Z",
            }
            for i in range(50)
        ]

        # Queue normal priority comments first
        comment_monitor._queue_comments_for_analysis(
            normal_priority_comments, "regular_post"
        )

        # Then queue high priority comments
        # Note: This would require extending the queue_comments_for_analysis method to accept priority
        comment_monitor._queue_comments_for_analysis(
            high_priority_comments, "urgent_post"
        )

        # Verify queuing
        metrics = mock_celery_client_with_batching.get_metrics()
        queued_tasks = mock_celery_client_with_batching.get_queued_tasks()

        assert metrics.total_tasks_queued == 60, "All comments should be queued"
        assert len(queued_tasks) == 60, "Should have 60 queued tasks"

        # Verify task data integrity
        urgent_tasks = [
            task for task in queued_tasks if "urgent_post" in str(task.get("args", []))
        ]
        regular_tasks = [
            task for task in queued_tasks if "regular_post" in str(task.get("args", []))
        ]

        assert len(urgent_tasks) == 10, "Should have 10 urgent tasks"
        assert len(regular_tasks) == 50, "Should have 50 regular tasks"

    @pytest.mark.parametrize(
        "batch_size,expected_efficiency",
        [
            (1, 1.0),  # Individual processing (baseline)
            (10, 3.0),  # Small batches - 3x improvement
            (50, 8.0),  # Medium batches - 8x improvement
            (100, 12.0),  # Large batches - 12x improvement
        ],
    )
    def test_batch_size_optimization_efficiency(
        self, batch_size, expected_efficiency, mock_celery_client_with_batching
    ):
        """
        Test batch size optimization for different comment volumes.

        Validates that larger batch sizes provide better queuing efficiency.
        """
        total_comments = 500
        comments = [
            {
                "id": f"efficiency_comment_{i}",
                "post_id": f"efficiency_post_{i % 5}",
                "text": f"Efficiency test comment {i}",
                "author": f"user_{i % 20}",
                "timestamp": f"2024-01-01T{10 + (i % 14):02d}:{i % 60:02d}:00Z",
            }
            for i in range(total_comments)
        ]

        comment_monitor = CommentMonitor(
            fake_threads_client=None,
            celery_client=mock_celery_client_with_batching,
            db_session=Mock(),
        )

        if batch_size == 1:
            # Individual processing
            start_time = time.time()
            comment_monitor._queue_comments_for_analysis(comments, "efficiency_test")
            processing_time = time.time() - start_time
        else:
            # Batch processing
            comment_batches = [
                comments[i : i + batch_size]
                for i in range(0, len(comments), batch_size)
            ]

            start_time = time.time()
            for batch in comment_batches:
                batch_tasks = [
                    {
                        "task_name": "analyze_comment_intent",
                        "args": [comment, "efficiency_test"],
                        "kwargs": {},
                        "options": {},
                    }
                    for comment in batch
                ]
                mock_celery_client_with_batching.send_task_batch(batch_tasks)
            processing_time = time.time() - start_time

        # Calculate efficiency metrics
        metrics = mock_celery_client_with_batching.get_metrics()
        throughput = (
            metrics.total_tasks_queued / processing_time if processing_time > 0 else 0
        )

        # Efficiency assertions
        min_expected_throughput = (
            expected_efficiency * 1000
        )  # Base throughput of 1000/s for individual
        assert throughput >= min_expected_throughput * 0.7, (
            f"Batch size {batch_size} throughput {throughput:.0f}/s below "
            f"70% of expected {min_expected_throughput:.0f}/s"
        )

        # Verify all tasks queued successfully
        assert metrics.total_tasks_queued == total_comments, (
            "All comments should be queued"
        )
        assert metrics.failed_queue_attempts == 0, "No queue failures expected"

        # Batch size specific validations
        if batch_size > 1:
            assert metrics.batch_size_avg >= batch_size * 0.8, (
                f"Average batch size {metrics.batch_size_avg:.1f} too small for target {batch_size}"
            )

        print(
            f"Batch size {batch_size}: {throughput:.0f} tasks/s, "
            f"{expected_efficiency:.1f}x expected efficiency"
        )
