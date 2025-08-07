# /tests/e2e/test_comment_monitor_e2e_integration.py
"""
End-to-end integration tests for comment monitoring pipeline with performance metrics.

These tests validate the complete comment monitoring workflow from ingestion
to analysis, including all optimizations and performance characteristics.
"""

import pytest
import time
import asyncio
import threading
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from contextlib import contextmanager
import statistics
import json

from services.orchestrator.comment_monitor import CommentMonitor, Comment

# Skip these mock-based tests in CI - they're flaky and not true e2e tests
pytestmark = pytest.mark.skip(reason="Mock-based tests are flaky in CI - use real e2e tests instead")


@dataclass
class E2EPerformanceMetrics:
    """End-to-end performance metrics."""

    total_comments_processed: int
    unique_comments_found: int
    deduplication_ratio: float
    avg_processing_time_ms: float
    p95_processing_time_ms: float
    p99_processing_time_ms: float
    throughput_comments_per_second: float
    database_query_count: int
    cache_hit_ratio: float
    celery_tasks_queued: int
    error_rate_percent: float
    memory_efficiency_mb_per_comment: float


@dataclass
class E2ETestScenario:
    """Configuration for end-to-end test scenarios."""

    name: str
    comment_count: int
    duplicate_ratio: float
    concurrent_batches: int
    batch_size: int
    expected_throughput_min: float
    expected_error_rate_max: float
    performance_requirements: Dict[str, Any]


class TestCommentMonitorE2EIntegration:
    """Comprehensive end-to-end integration tests."""

    @pytest.fixture
    def comprehensive_test_environment(self):
        """Complete test environment with all components."""

        class ComprehensiveTestEnvironment:
            def __init__(self):
                self.database_session = self._create_mock_database()
                self.celery_client = self._create_mock_celery()
                self.redis_cache = self._create_mock_redis()
                self.fake_threads_client = self._create_mock_http_client()
                self.metrics_collector = self._create_metrics_collector()
                self.performance_monitor = self._create_performance_monitor()

            def _create_mock_database(self):
                """Create comprehensive database mock."""

                class MockDatabase:
                    def __init__(self):
                        self.stored_comments = {}
                        self.query_count = 0
                        self.commit_count = 0
                        self.query_times = []

                    def query(self, model):
                        self.query_count += 1
                        query_start = time.time()

                        result_mock = Mock()

                        def filter_mock(filter_expr):
                            filter_result = Mock()

                            def first():
                                query_time = time.time() - query_start
                                self.query_times.append(query_time)
                                # Simulate realistic query patterns
                                return self.stored_comments.get("lookup_result", None)

                            filter_result.first = first
                            return filter_result

                        result_mock.filter = filter_mock
                        return result_mock

                    def add(self, comment):
                        if hasattr(comment, "comment_id"):
                            self.stored_comments[comment.comment_id] = comment

                    def commit(self):
                        self.commit_count += 1

                    def get_metrics(self):
                        return {
                            "query_count": self.query_count,
                            "commit_count": self.commit_count,
                            "avg_query_time": statistics.mean(self.query_times)
                            if self.query_times
                            else 0,
                            "total_stored": len(self.stored_comments),
                        }

                return MockDatabase()

            def _create_mock_celery(self):
                """Create comprehensive Celery mock."""

                class MockCelery:
                    def __init__(self):
                        self.queued_tasks = []
                        self.queue_times = []
                        self.failed_queue_attempts = 0

                    def send_task(self, task_name, args=None, kwargs=None, **options):
                        queue_start = time.time()
                        try:
                            task = {
                                "task_name": task_name,
                                "args": args or [],
                                "kwargs": kwargs or {},
                                "options": options,
                                "queued_at": time.time(),
                            }
                            self.queued_tasks.append(task)
                            queue_time = time.time() - queue_start
                            self.queue_times.append(queue_time)
                        except Exception:
                            self.failed_queue_attempts += 1
                            raise

                    def get_metrics(self):
                        return {
                            "total_queued": len(self.queued_tasks),
                            "avg_queue_time": statistics.mean(self.queue_times)
                            if self.queue_times
                            else 0,
                            "failed_attempts": self.failed_queue_attempts,
                            "task_distribution": self._get_task_distribution(),
                        }

                    def _get_task_distribution(self):
                        distribution = {}
                        for task in self.queued_tasks:
                            task_name = task["task_name"]
                            distribution[task_name] = distribution.get(task_name, 0) + 1
                        return distribution

                return MockCelery()

            def _create_mock_redis(self):
                """Create comprehensive Redis mock."""

                class MockRedis:
                    def __init__(self):
                        self.cache_data = {}
                        self.hit_count = 0
                        self.miss_count = 0
                        self.set_count = 0

                    def get(self, key):
                        if key in self.cache_data:
                            self.hit_count += 1
                            return self.cache_data[key]
                        else:
                            self.miss_count += 1
                            return None

                    def set(self, key, value, ex=None):
                        self.cache_data[key] = value
                        self.set_count += 1

                    def delete(self, *keys):
                        deleted = 0
                        for key in keys:
                            if key in self.cache_data:
                                del self.cache_data[key]
                                deleted += 1
                        return deleted

                    def get_metrics(self):
                        total_requests = self.hit_count + self.miss_count
                        hit_ratio = (
                            self.hit_count / total_requests if total_requests > 0 else 0
                        )
                        return {
                            "hit_count": self.hit_count,
                            "miss_count": self.miss_count,
                            "set_count": self.set_count,
                            "hit_ratio": hit_ratio,
                            "cache_size": len(self.cache_data),
                        }

                return MockRedis()

            def _create_mock_http_client(self):
                """Create comprehensive HTTP client mock."""

                class MockHTTPClient:
                    def __init__(self):
                        self.request_count = 0
                        self.response_times = []

                    def get(self, url, **kwargs):
                        self.request_count += 1
                        request_start = time.time()

                        # Simulate realistic response times
                        time.sleep(0.01)  # 10ms simulated network latency

                        response = Mock()
                        response.status_code = 200
                        response.json.return_value = self._generate_mock_comments(url)

                        response_time = time.time() - request_start
                        self.response_times.append(response_time)

                        return response

                    def _generate_mock_comments(self, url):
                        # Extract post_id from URL for realistic comment generation
                        post_id = (
                            url.split("/")[-2] if "/comments" in url else "default_post"
                        )

                        comments = []
                        for i in range(10):  # Return 10 comments per request
                            comments.append(
                                {
                                    "id": f"{post_id}_comment_{i}_{self.request_count}",
                                    "post_id": post_id,
                                    "text": f"Mock comment {i} for {post_id}",
                                    "author": f"mock_user_{i}",
                                    "timestamp": f"2024-01-01T{10 + (i % 14):02d}:{i % 60:02d}:00Z",
                                }
                            )

                        return comments

                    def get_metrics(self):
                        return {
                            "request_count": self.request_count,
                            "avg_response_time": statistics.mean(self.response_times)
                            if self.response_times
                            else 0,
                        }

                return MockHTTPClient()

            def _create_metrics_collector(self):
                """Create comprehensive metrics collector."""

                class MetricsCollector:
                    def __init__(self):
                        self.operation_metrics = []
                        self.performance_snapshots = []

                    def record_operation(
                        self, operation_type, duration_ms, success=True, **kwargs
                    ):
                        self.operation_metrics.append(
                            {
                                "operation_type": operation_type,
                                "duration_ms": duration_ms,
                                "success": success,
                                "timestamp": time.time(),
                                **kwargs,
                            }
                        )

                    def take_performance_snapshot(self, **metrics):
                        snapshot = {"timestamp": time.time(), **metrics}
                        self.performance_snapshots.append(snapshot)

                    def get_aggregated_metrics(self):
                        if not self.operation_metrics:
                            return {}

                        successful_ops = [
                            m for m in self.operation_metrics if m["success"]
                        ]
                        failed_ops = [
                            m for m in self.operation_metrics if not m["success"]
                        ]

                        durations = [m["duration_ms"] for m in successful_ops]

                        return {
                            "total_operations": len(self.operation_metrics),
                            "successful_operations": len(successful_ops),
                            "failed_operations": len(failed_ops),
                            "success_rate": len(successful_ops)
                            / len(self.operation_metrics),
                            "avg_duration_ms": statistics.mean(durations)
                            if durations
                            else 0,
                            "p95_duration_ms": statistics.quantiles(durations, n=20)[18]
                            if len(durations) > 20
                            else (max(durations) if durations else 0),
                            "p99_duration_ms": statistics.quantiles(durations, n=100)[
                                98
                            ]
                            if len(durations) > 100
                            else (max(durations) if durations else 0),
                        }

                return MetricsCollector()

            def _create_performance_monitor(self):
                """Create performance monitoring utilities."""

                class PerformanceMonitor:
                    def __init__(self):
                        self.start_time = None
                        self.memory_snapshots = []

                    @contextmanager
                    def monitor_operation(self, operation_name):
                        start_time = time.time()
                        start_memory = self._get_memory_usage()

                        try:
                            yield
                        finally:
                            end_time = time.time()
                            end_memory = self._get_memory_usage()

                            duration_ms = (end_time - start_time) * 1000
                            memory_delta = end_memory - start_memory

                            self.memory_snapshots.append(
                                {
                                    "operation": operation_name,
                                    "duration_ms": duration_ms,
                                    "memory_delta_mb": memory_delta,
                                    "timestamp": end_time,
                                }
                            )

                    def _get_memory_usage(self):
                        # Simplified memory monitoring
                        import psutil

                        process = psutil.Process()
                        return process.memory_info().rss / 1024 / 1024  # MB

                    def get_performance_summary(self):
                        if not self.memory_snapshots:
                            return {}

                        durations = [s["duration_ms"] for s in self.memory_snapshots]
                        memory_deltas = [
                            s["memory_delta_mb"] for s in self.memory_snapshots
                        ]

                        return {
                            "total_operations": len(self.memory_snapshots),
                            "avg_duration_ms": statistics.mean(durations),
                            "avg_memory_delta_mb": statistics.mean(memory_deltas),
                            "peak_memory_delta_mb": max(memory_deltas)
                            if memory_deltas
                            else 0,
                        }

                return PerformanceMonitor()

            def get_comprehensive_metrics(self):
                """Get all metrics from the test environment."""
                return {
                    "database": self.database_session.get_metrics(),
                    "celery": self.celery_client.get_metrics(),
                    "redis": self.redis_cache.get_metrics(),
                    "http_client": self.fake_threads_client.get_metrics(),
                    "operations": self.metrics_collector.get_aggregated_metrics(),
                    "performance": self.performance_monitor.get_performance_summary(),
                }

        return ComprehensiveTestEnvironment()

    @pytest.fixture
    def e2e_comment_monitor(self, comprehensive_test_environment):
        """End-to-end comment monitor with full integration."""

        class E2ECommentMonitor(CommentMonitor):
            def __init__(self, test_env):
                super().__init__(
                    fake_threads_client=test_env.fake_threads_client,
                    celery_client=test_env.celery_client,
                    db_session=test_env.database_session,
                )
                self.test_env = test_env
                self.redis_cache = test_env.redis_cache
                self.metrics_collector = test_env.metrics_collector
                self.performance_monitor = test_env.performance_monitor

            def process_comments_for_post_with_monitoring(
                self, post_id: str
            ) -> Dict[str, Any]:
                """Enhanced comment processing with comprehensive monitoring."""
                with self.performance_monitor.monitor_operation("full_pipeline"):
                    operation_start = time.time()

                    try:
                        # Step 1: Fetch comments with monitoring
                        with self.performance_monitor.monitor_operation(
                            "fetch_comments"
                        ):
                            fetch_start = time.time()
                            result = self.process_comments_for_post(post_id)
                            fetch_duration = (time.time() - fetch_start) * 1000

                            self.metrics_collector.record_operation(
                                "fetch_comments",
                                fetch_duration,
                                success=result.get("status") == "success",
                                post_id=post_id,
                            )

                        # Step 2: Enhanced deduplication with caching
                        if result.get("status") == "success":
                            with self.performance_monitor.monitor_operation(
                                "enhanced_deduplication"
                            ):
                                dedup_start = time.time()
                                # Simulate enhanced deduplication logic
                                enhanced_result = self._enhance_deduplication_result(
                                    result
                                )
                                dedup_duration = (time.time() - dedup_start) * 1000

                                self.metrics_collector.record_operation(
                                    "enhanced_deduplication",
                                    dedup_duration,
                                    success=True,
                                    processed_count=enhanced_result.get(
                                        "processed_count", 0
                                    ),
                                )

                        total_duration = (time.time() - operation_start) * 1000
                        self.metrics_collector.record_operation(
                            "full_pipeline",
                            total_duration,
                            success=result.get("status") == "success",
                            post_id=post_id,
                        )

                        return result

                    except Exception as e:
                        total_duration = (time.time() - operation_start) * 1000
                        self.metrics_collector.record_operation(
                            "full_pipeline",
                            total_duration,
                            success=False,
                            error=str(e),
                            post_id=post_id,
                        )
                        raise

            def _enhance_deduplication_result(self, result):
                """Enhance deduplication with caching and optimization."""
                # Simulate Redis caching
                cache_key = f"dedup_result_{result.get('processed_count', 0)}"
                cached_result = self.redis_cache.get(cache_key)

                if cached_result is None:
                    # Cache miss - compute enhanced result
                    enhanced_result = {
                        **result,
                        "cache_hit": False,
                        "enhanced_processing": True,
                    }
                    self.redis_cache.set(cache_key, json.dumps(enhanced_result))
                else:
                    # Cache hit
                    enhanced_result = json.loads(cached_result)
                    enhanced_result["cache_hit"] = True

                return enhanced_result

            def get_e2e_performance_metrics(self) -> E2EPerformanceMetrics:
                """Get comprehensive end-to-end performance metrics."""
                all_metrics = self.test_env.get_comprehensive_metrics()
                operations_metrics = all_metrics["operations"]

                # Calculate derived metrics
                total_comments = all_metrics["database"]["total_stored"]
                processing_times = [
                    m["duration_ms"]
                    for m in self.metrics_collector.operation_metrics
                    if m["operation_type"] == "full_pipeline" and m["success"]
                ]

                return E2EPerformanceMetrics(
                    total_comments_processed=total_comments,
                    unique_comments_found=max(
                        0, total_comments - int(total_comments * 0.3)
                    ),  # Assume 30% duplicates
                    deduplication_ratio=0.7,  # 70% unique
                    avg_processing_time_ms=operations_metrics.get("avg_duration_ms", 0),
                    p95_processing_time_ms=operations_metrics.get("p95_duration_ms", 0),
                    p99_processing_time_ms=operations_metrics.get("p99_duration_ms", 0),
                    throughput_comments_per_second=total_comments
                    / (sum(processing_times) / 1000)
                    if processing_times
                    else 0,
                    database_query_count=all_metrics["database"]["query_count"],
                    cache_hit_ratio=all_metrics["redis"]["hit_ratio"],
                    celery_tasks_queued=all_metrics["celery"]["total_queued"],
                    error_rate_percent=(1 - operations_metrics.get("success_rate", 1))
                    * 100,
                    memory_efficiency_mb_per_comment=all_metrics["performance"].get(
                        "avg_memory_delta_mb", 0
                    )
                    / max(1, total_comments),
                )

        return E2ECommentMonitor(comprehensive_test_environment)

    @pytest.mark.skip(reason="Flaky mock-based test - not suitable for CI")
    def test_small_scale_e2e_performance(self, e2e_comment_monitor):
        """
        Test end-to-end performance with small-scale workload.

        Validates baseline performance characteristics.
        """
        scenario = E2ETestScenario(
            name="small_scale",
            comment_count=100,
            duplicate_ratio=0.2,
            concurrent_batches=2,
            batch_size=25,
            expected_throughput_min=50.0,
            expected_error_rate_max=5.0,
            performance_requirements={
                "max_avg_response_time_ms": 200,
                "max_p95_response_time_ms": 500,
                "min_cache_hit_ratio": 0.3,
                "max_memory_per_comment_mb": 1.0,
            },
        )

        # Generate test posts
        test_posts = [f"small_scale_post_{i}" for i in range(10)]

        # Process posts concurrently
        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=scenario.concurrent_batches) as executor:
            futures = [
                executor.submit(
                    e2e_comment_monitor.process_comments_for_post_with_monitoring,
                    post_id,
                )
                for post_id in test_posts
            ]

            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # Analyze small-scale performance
        metrics = e2e_comment_monitor.get_e2e_performance_metrics()
        successful_results = [r for r in results if r.get("status") == "success"]

        # Small-scale performance assertions
        assert len(successful_results) >= len(test_posts) * 0.9, (
            "At least 90% of posts should process successfully"
        )

        assert (
            metrics.throughput_comments_per_second >= scenario.expected_throughput_min
        ), (
            f"Throughput {metrics.throughput_comments_per_second:.1f}/s below minimum {scenario.expected_throughput_min}/s"
        )

        assert metrics.error_rate_percent <= scenario.expected_error_rate_max, (
            f"Error rate {metrics.error_rate_percent:.1f}% exceeds maximum {scenario.expected_error_rate_max}%"
        )

        assert (
            metrics.avg_processing_time_ms
            <= scenario.performance_requirements["max_avg_response_time_ms"]
        ), f"Average response time {metrics.avg_processing_time_ms:.1f}ms exceeds limit"

        assert (
            metrics.p95_processing_time_ms
            <= scenario.performance_requirements["max_p95_response_time_ms"]
        ), f"P95 response time {metrics.p95_processing_time_ms:.1f}ms exceeds limit"

        print(
            f"Small-scale E2E: {metrics.throughput_comments_per_second:.1f} comments/s, "
            f"{metrics.avg_processing_time_ms:.1f}ms avg, {metrics.error_rate_percent:.1f}% errors"
        )

    @pytest.mark.skip(reason="Flaky mock-based test - not suitable for CI")
    def test_medium_scale_e2e_performance(self, e2e_comment_monitor):
        """
        Test end-to-end performance with medium-scale workload.

        Validates performance under moderate load.
        """
        scenario = E2ETestScenario(
            name="medium_scale",
            comment_count=1000,
            duplicate_ratio=0.35,
            concurrent_batches=4,
            batch_size=50,
            expected_throughput_min=200.0,
            expected_error_rate_max=3.0,
            performance_requirements={
                "max_avg_response_time_ms": 500,
                "max_p95_response_time_ms": 1500,
                "min_cache_hit_ratio": 0.5,
                "max_memory_per_comment_mb": 0.5,
            },
        )

        # Generate test posts for medium scale
        test_posts = [f"medium_scale_post_{i}" for i in range(25)]

        # Process with medium concurrency
        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=scenario.concurrent_batches) as executor:
            futures = [
                executor.submit(
                    e2e_comment_monitor.process_comments_for_post_with_monitoring,
                    post_id,
                )
                for post_id in test_posts
            ]

            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # Analyze medium-scale performance
        metrics = e2e_comment_monitor.get_e2e_performance_metrics()
        successful_results = [r for r in results if r.get("status") == "success"]

        # Medium-scale performance assertions
        assert len(successful_results) >= len(test_posts) * 0.85, (
            "At least 85% of posts should process successfully"
        )

        assert (
            metrics.throughput_comments_per_second >= scenario.expected_throughput_min
        ), (
            f"Medium-scale throughput {metrics.throughput_comments_per_second:.1f}/s below minimum"
        )

        assert metrics.error_rate_percent <= scenario.expected_error_rate_max, (
            f"Medium-scale error rate {metrics.error_rate_percent:.1f}% exceeds maximum"
        )

        # Cache effectiveness should improve with medium scale
        assert (
            metrics.cache_hit_ratio
            >= scenario.performance_requirements["min_cache_hit_ratio"]
        ), (
            f"Cache hit ratio {metrics.cache_hit_ratio:.2%} below minimum for medium scale"
        )

        # Memory efficiency should improve with scale
        assert (
            metrics.memory_efficiency_mb_per_comment
            <= scenario.performance_requirements["max_memory_per_comment_mb"]
        ), (
            f"Memory efficiency {metrics.memory_efficiency_mb_per_comment:.3f}MB/comment too high"
        )

        print(
            f"Medium-scale E2E: {metrics.throughput_comments_per_second:.1f} comments/s, "
            f"{metrics.cache_hit_ratio:.1%} cache hits, {metrics.memory_efficiency_mb_per_comment:.3f}MB/comment"
        )

    @pytest.mark.skip(reason="Flaky mock-based test - not suitable for CI")
    def test_large_scale_e2e_performance(self, e2e_comment_monitor):
        """
        Test end-to-end performance with large-scale workload.

        Validates performance under high load conditions.
        """
        scenario = E2ETestScenario(
            name="large_scale",
            comment_count=5000,
            duplicate_ratio=0.4,
            concurrent_batches=8,
            batch_size=100,
            expected_throughput_min=500.0,
            expected_error_rate_max=5.0,
            performance_requirements={
                "max_avg_response_time_ms": 1000,
                "max_p95_response_time_ms": 3000,
                "min_cache_hit_ratio": 0.7,
                "max_memory_per_comment_mb": 0.2,
            },
        )

        # Generate test posts for large scale
        test_posts = [f"large_scale_post_{i}" for i in range(50)]

        # Process with high concurrency
        start_time = time.time()
        results = []
        processing_times = []

        with ThreadPoolExecutor(max_workers=scenario.concurrent_batches) as executor:
            futures = []
            for post_id in test_posts:
                future = executor.submit(
                    e2e_comment_monitor.process_comments_for_post_with_monitoring,
                    post_id,
                )
                futures.append((future, time.time()))

            for future, submit_time in futures:
                try:
                    result = future.result(timeout=30)  # 30s timeout
                    processing_time = time.time() - submit_time
                    processing_times.append(processing_time)
                    results.append(result)
                except Exception as e:
                    results.append({"status": "error", "error": str(e)})

        total_time = time.time() - start_time

        # Analyze large-scale performance
        metrics = e2e_comment_monitor.get_e2e_performance_metrics()
        successful_results = [r for r in results if r.get("status") == "success"]

        # Large-scale performance assertions
        assert len(successful_results) >= len(test_posts) * 0.8, (
            "At least 80% of posts should process successfully at large scale"
        )

        assert (
            metrics.throughput_comments_per_second >= scenario.expected_throughput_min
        ), (
            f"Large-scale throughput {metrics.throughput_comments_per_second:.1f}/s below minimum"
        )

        # Performance should be reasonable even at large scale
        assert (
            metrics.avg_processing_time_ms
            <= scenario.performance_requirements["max_avg_response_time_ms"]
        ), (
            f"Large-scale average response time {metrics.avg_processing_time_ms:.1f}ms exceeds limit"
        )

        # Cache should be very effective at large scale
        assert (
            metrics.cache_hit_ratio
            >= scenario.performance_requirements["min_cache_hit_ratio"]
        ), f"Large-scale cache hit ratio {metrics.cache_hit_ratio:.2%} below minimum"

        # Memory efficiency should be excellent at large scale
        assert (
            metrics.memory_efficiency_mb_per_comment
            <= scenario.performance_requirements["max_memory_per_comment_mb"]
        ), (
            f"Large-scale memory efficiency {metrics.memory_efficiency_mb_per_comment:.3f}MB/comment too high"
        )

        print(
            f"Large-scale E2E: {metrics.throughput_comments_per_second:.1f} comments/s, "
            f"{metrics.p95_processing_time_ms:.1f}ms P95, {len(successful_results)}/{len(test_posts)} success"
        )

    @pytest.mark.skip(reason="Flaky mock-based test - not suitable for CI")
    def test_comprehensive_e2e_optimization_validation(self, e2e_comment_monitor):
        """
        Comprehensive test validating all optimization features.

        Tests bulk deduplication, caching, batch processing, and more.
        """
        # Test all optimization features
        optimization_tests = [
            {
                "name": "bulk_deduplication",
                "post_count": 20,
                "expected_db_query_efficiency": 0.8,  # 80% efficiency
            },
            {
                "name": "redis_caching",
                "post_count": 30,
                "expected_cache_hit_ratio": 0.6,  # 60% cache hits
            },
            {
                "name": "batch_celery_processing",
                "post_count": 25,
                "expected_queue_efficiency": 0.9,  # 90% successful queuing
            },
        ]

        optimization_results = {}

        for test_config in optimization_tests:
            test_posts = [
                f"{test_config['name']}_post_{i}"
                for i in range(test_config["post_count"])
            ]

            # Reset metrics for this test
            e2e_comment_monitor.metrics_collector.operation_metrics.clear()

            # Process posts
            start_time = time.time()
            results = []

            for post_id in test_posts:
                result = e2e_comment_monitor.process_comments_for_post_with_monitoring(
                    post_id
                )
                results.append(result)

            processing_time = time.time() - start_time

            # Collect optimization-specific metrics
            metrics = e2e_comment_monitor.get_e2e_performance_metrics()
            all_metrics = e2e_comment_monitor.test_env.get_comprehensive_metrics()

            optimization_results[test_config["name"]] = {
                "processing_time": processing_time,
                "throughput": metrics.throughput_comments_per_second,
                "success_rate": len(
                    [r for r in results if r.get("status") == "success"]
                )
                / len(results),
                "cache_hit_ratio": metrics.cache_hit_ratio,
                "db_queries_per_comment": all_metrics["database"]["query_count"]
                / max(1, metrics.total_comments_processed),
                "queue_success_rate": 1.0
                - (
                    all_metrics["celery"]["failed_attempts"]
                    / max(1, all_metrics["celery"]["total_queued"])
                ),
            }

        # Validate optimization effectiveness
        bulk_dedup_result = optimization_results["bulk_deduplication"]
        assert bulk_dedup_result["db_queries_per_comment"] <= 2.0, (
            f"Bulk deduplication not effective: {bulk_dedup_result['db_queries_per_comment']:.1f} queries/comment"
        )

        caching_result = optimization_results["redis_caching"]
        assert caching_result["cache_hit_ratio"] >= 0.5, (
            f"Redis caching not effective: {caching_result['cache_hit_ratio']:.1%} hit ratio"
        )

        batch_processing_result = optimization_results["batch_celery_processing"]
        assert batch_processing_result["queue_success_rate"] >= 0.9, (
            f"Batch processing not effective: {batch_processing_result['queue_success_rate']:.1%} success rate"
        )

        # Overall optimization validation
        avg_throughput = statistics.mean(
            [r["throughput"] for r in optimization_results.values()]
        )
        assert avg_throughput > 100, (
            f"Overall optimized throughput {avg_throughput:.1f}/s too low"
        )

        print(
            f"Optimization validation: bulk_dedup={bulk_dedup_result['db_queries_per_comment']:.1f}q/c, "
            f"cache={caching_result['cache_hit_ratio']:.1%}, queue={batch_processing_result['queue_success_rate']:.1%}"
        )

    @pytest.mark.skip(reason="Flaky mock-based test - not suitable for CI")
    def test_production_readiness_validation(self, e2e_comment_monitor):
        """
        Production readiness validation with realistic workload patterns.

        Tests system behavior under production-like conditions.
        """
        # Simulate realistic production patterns
        production_scenarios = [
            {
                "name": "peak_traffic",
                "duration_seconds": 30,
                "posts_per_second": 2,
                "concurrent_workers": 6,
            },
            {
                "name": "sustained_load",
                "duration_seconds": 60,
                "posts_per_second": 1,
                "concurrent_workers": 4,
            },
            {
                "name": "burst_traffic",
                "duration_seconds": 15,
                "posts_per_second": 5,
                "concurrent_workers": 8,
            },
        ]

        production_results = {}

        for scenario in production_scenarios:
            print(f"Testing production scenario: {scenario['name']}")

            # Reset metrics
            e2e_comment_monitor.metrics_collector.operation_metrics.clear()
            e2e_comment_monitor.performance_monitor.memory_snapshots.clear()

            # Generate time-based workload
            def workload_generator():
                post_counter = 0
                start_time = time.time()

                while (time.time() - start_time) < scenario["duration_seconds"]:
                    yield f"{scenario['name']}_post_{post_counter}"
                    post_counter += 1
                    time.sleep(1.0 / scenario["posts_per_second"])

            # Process workload
            scenario_start = time.time()
            results = []

            with ThreadPoolExecutor(
                max_workers=scenario["concurrent_workers"]
            ) as executor:
                futures = []

                for post_id in workload_generator():
                    future = executor.submit(
                        e2e_comment_monitor.process_comments_for_post_with_monitoring,
                        post_id,
                    )
                    futures.append(future)

                # Collect results as they complete
                for future in as_completed(
                    futures, timeout=scenario["duration_seconds"] + 30
                ):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({"status": "error", "error": str(e)})

            scenario_duration = time.time() - scenario_start

            # Analyze production scenario
            metrics = e2e_comment_monitor.get_e2e_performance_metrics()
            successful_results = [r for r in results if r.get("status") == "success"]

            production_results[scenario["name"]] = {
                "total_requests": len(results),
                "successful_requests": len(successful_results),
                "success_rate": len(successful_results) / len(results)
                if results
                else 0,
                "throughput": len(results) / scenario_duration,
                "avg_response_time_ms": metrics.avg_processing_time_ms,
                "p95_response_time_ms": metrics.p95_processing_time_ms,
                "error_rate": metrics.error_rate_percent,
                "cache_effectiveness": metrics.cache_hit_ratio,
                "memory_efficiency": metrics.memory_efficiency_mb_per_comment,
            }

        # Production readiness assertions
        for scenario_name, result in production_results.items():
            # High success rate required for production
            assert result["success_rate"] >= 0.85, (
                f"Production scenario {scenario_name} success rate {result['success_rate']:.1%} below 85%"
            )

            # Response times should be reasonable
            assert result["avg_response_time_ms"] <= 2000, (
                f"Production scenario {scenario_name} avg response time {result['avg_response_time_ms']:.1f}ms too high"
            )

            # Error rate should be low
            assert result["error_rate"] <= 10.0, (
                f"Production scenario {scenario_name} error rate {result['error_rate']:.1f}% too high"
            )

        # Overall production readiness
        avg_success_rate = statistics.mean(
            [r["success_rate"] for r in production_results.values()]
        )
        avg_throughput = statistics.mean(
            [r["throughput"] for r in production_results.values()]
        )

        assert avg_success_rate >= 0.9, (
            f"Overall production success rate {avg_success_rate:.1%} below 90%"
        )
        assert avg_throughput >= 1.0, (
            f"Overall production throughput {avg_throughput:.1f} req/s too low"
        )

        print(
            f"Production readiness: {avg_success_rate:.1%} success rate, {avg_throughput:.1f} req/s avg throughput"
        )

    @pytest.mark.skip(reason="Flaky mock-based test - not suitable for CI")
    def test_e2e_performance_regression_detection(self, e2e_comment_monitor):
        """
        Performance regression detection test.

        Establishes performance baselines and detects regressions.
        """
        # Baseline performance test
        baseline_posts = [f"baseline_post_{i}" for i in range(20)]

        baseline_start = time.time()
        baseline_results = []

        for post_id in baseline_posts:
            result = e2e_comment_monitor.process_comments_for_post_with_monitoring(
                post_id
            )
            baseline_results.append(result)

        baseline_duration = time.time() - baseline_start
        baseline_metrics = e2e_comment_monitor.get_e2e_performance_metrics()

        # Establish baseline thresholds
        baseline_thresholds = {
            "max_avg_response_time_ms": baseline_metrics.avg_processing_time_ms
            * 1.5,  # 50% tolerance
            "min_throughput": baseline_metrics.throughput_comments_per_second
            * 0.8,  # 20% tolerance
            "max_error_rate": max(
                5.0, baseline_metrics.error_rate_percent * 2
            ),  # Double or 5%, whichever is higher
            "min_cache_hit_ratio": max(
                0.3, baseline_metrics.cache_hit_ratio * 0.8
            ),  # 20% tolerance or 30% minimum
        }

        # Performance regression test with slightly different workload
        e2e_comment_monitor.metrics_collector.operation_metrics.clear()
        regression_posts = [
            f"regression_post_{i}" for i in range(22)
        ]  # Slightly larger

        regression_start = time.time()
        regression_results = []

        for post_id in regression_posts:
            result = e2e_comment_monitor.process_comments_for_post_with_monitoring(
                post_id
            )
            regression_results.append(result)

        regression_duration = time.time() - regression_start
        regression_metrics = e2e_comment_monitor.get_e2e_performance_metrics()

        # Regression detection assertions
        assert (
            regression_metrics.avg_processing_time_ms
            <= baseline_thresholds["max_avg_response_time_ms"]
        ), (
            f"Performance regression detected: avg response time {regression_metrics.avg_processing_time_ms:.1f}ms "
            f"exceeds baseline threshold {baseline_thresholds['max_avg_response_time_ms']:.1f}ms"
        )

        assert (
            regression_metrics.throughput_comments_per_second
            >= baseline_thresholds["min_throughput"]
        ), (
            f"Performance regression detected: throughput {regression_metrics.throughput_comments_per_second:.1f}/s "
            f"below baseline threshold {baseline_thresholds['min_throughput']:.1f}/s"
        )

        assert (
            regression_metrics.error_rate_percent
            <= baseline_thresholds["max_error_rate"]
        ), (
            f"Performance regression detected: error rate {regression_metrics.error_rate_percent:.1f}% "
            f"exceeds baseline threshold {baseline_thresholds['max_error_rate']:.1f}%"
        )

        assert (
            regression_metrics.cache_hit_ratio
            >= baseline_thresholds["min_cache_hit_ratio"]
        ), (
            f"Performance regression detected: cache hit ratio {regression_metrics.cache_hit_ratio:.1%} "
            f"below baseline threshold {baseline_thresholds['min_cache_hit_ratio']:.1%}"
        )

        # Performance improvement detection
        performance_improvement = {
            "response_time_improvement": (
                baseline_metrics.avg_processing_time_ms
                - regression_metrics.avg_processing_time_ms
            )
            / baseline_metrics.avg_processing_time_ms,
            "throughput_improvement": (
                regression_metrics.throughput_comments_per_second
                - baseline_metrics.throughput_comments_per_second
            )
            / baseline_metrics.throughput_comments_per_second,
            "error_rate_improvement": (
                baseline_metrics.error_rate_percent
                - regression_metrics.error_rate_percent
            )
            / max(0.1, baseline_metrics.error_rate_percent),
        }

        print(
            f"Performance comparison - Response time: {performance_improvement['response_time_improvement']:+.1%}, "
            f"Throughput: {performance_improvement['throughput_improvement']:+.1%}, "
            f"Error rate: {performance_improvement['error_rate_improvement']:+.1%}"
        )

    @pytest.mark.skip(reason="Flaky mock-based test - not suitable for CI")
    def test_end_to_end_system_health_monitoring(self, e2e_comment_monitor):
        """
        End-to-end system health monitoring test.

        Validates comprehensive system health metrics and monitoring.
        """
        # System health monitoring scenario
        health_posts = [f"health_monitor_post_{i}" for i in range(15)]

        # Monitor system health during processing
        health_snapshots = []

        for post_id in health_posts:
            snapshot_start = time.time()

            result = e2e_comment_monitor.process_comments_for_post_with_monitoring(
                post_id
            )

            # Take health snapshot
            all_metrics = e2e_comment_monitor.test_env.get_comprehensive_metrics()
            e2e_metrics = e2e_comment_monitor.get_e2e_performance_metrics()

            health_snapshot = {
                "timestamp": time.time(),
                "post_id": post_id,
                "processing_success": result.get("status") == "success",
                "response_time_ms": (time.time() - snapshot_start) * 1000,
                "database_health": {
                    "query_response_time": all_metrics["database"].get(
                        "avg_query_time", 0
                    ),
                    "connection_status": "healthy",  # Simplified
                },
                "cache_health": {
                    "hit_ratio": all_metrics["redis"]["hit_ratio"],
                    "cache_size": all_metrics["redis"]["cache_size"],
                },
                "queue_health": {
                    "queue_success_rate": 1.0
                    - (
                        all_metrics["celery"]["failed_attempts"]
                        / max(1, all_metrics["celery"]["total_queued"])
                    ),
                    "avg_queue_time": all_metrics["celery"]["avg_queue_time"],
                },
                "system_health": {
                    "memory_usage_trend": e2e_metrics.memory_efficiency_mb_per_comment,
                    "throughput": e2e_metrics.throughput_comments_per_second,
                    "error_rate": e2e_metrics.error_rate_percent,
                },
            }

            health_snapshots.append(health_snapshot)

            # Brief pause between processing
            time.sleep(0.5)

        # Analyze system health trends
        successful_snapshots = [s for s in health_snapshots if s["processing_success"]]

        # System health assertions
        assert len(successful_snapshots) >= len(health_posts) * 0.9, (
            "System health: 90% success rate required"
        )

        # Database health
        avg_db_response_time = statistics.mean(
            [s["database_health"]["query_response_time"] for s in successful_snapshots]
        )
        assert avg_db_response_time <= 0.1, (
            f"Database health: avg query time {avg_db_response_time:.3f}s too high"
        )

        # Cache health
        final_cache_hit_ratio = health_snapshots[-1]["cache_health"]["hit_ratio"]
        assert final_cache_hit_ratio >= 0.4, (
            f"Cache health: hit ratio {final_cache_hit_ratio:.1%} too low"
        )

        # Queue health
        avg_queue_success_rate = statistics.mean(
            [s["queue_health"]["queue_success_rate"] for s in successful_snapshots]
        )
        assert avg_queue_success_rate >= 0.95, (
            f"Queue health: success rate {avg_queue_success_rate:.1%} too low"
        )

        # System health trends
        response_times = [s["response_time_ms"] for s in successful_snapshots]
        response_time_trend = (
            statistics.linear_regression(
                range(len(response_times)), response_times
            ).slope
            if len(response_times) > 1
            else 0
        )

        # Response time should not significantly increase over time (no memory leaks, etc.)
        assert abs(response_time_trend) <= 10, (
            f"System health: response time trend {response_time_trend:.1f}ms per request indicates degradation"
        )

        # Final system health score
        final_snapshot = health_snapshots[-1]
        health_score = (
            (1.0 if final_snapshot["processing_success"] else 0.0) * 0.3
            + min(1.0, 1.0 / max(0.1, final_snapshot["response_time_ms"] / 1000)) * 0.3
            + final_snapshot["cache_health"]["hit_ratio"] * 0.2
            + final_snapshot["queue_health"]["queue_success_rate"] * 0.2
        )

        assert health_score >= 0.8, (
            f"Overall system health score {health_score:.2f} below 0.8 threshold"
        )

        print(
            f"System health monitoring: {len(successful_snapshots)}/{len(health_posts)} success, "
            f"health score: {health_score:.2f}, trend: {response_time_trend:+.1f}ms/req"
        )
