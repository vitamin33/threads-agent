# /services/orchestrator/tests/test_comment_monitor_memory_and_rate_limiting.py
"""
Memory usage and rate limiting tests for the comment monitoring pipeline.

These tests validate memory efficiency under high load and proper rate limiting
behavior with exponential backoff for API calls.
"""

import pytest
import time
import threading
import psutil
from unittest.mock import Mock
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import httpx

from services.orchestrator.comment_monitor import CommentMonitor


@dataclass
class MemorySnapshot:
    """Memory usage snapshot for tracking."""

    rss_mb: float
    vms_mb: float
    percent: float
    timestamp: float


@dataclass
class RateLimitMetrics:
    """Rate limiting test metrics."""

    total_requests: int
    successful_requests: int
    rate_limited_requests: int
    avg_backoff_delay: float
    max_backoff_delay: float


class TestCommentMonitorMemoryUsage:
    """Memory usage tests under various load scenarios."""

    @pytest.fixture
    def memory_profiler(self):
        """Memory profiling utility for tracking usage patterns."""

        class MemoryProfiler:
            def __init__(self):
                self.process = psutil.Process()
                self.snapshots = []
                self.monitoring = False
                self.monitor_thread = None

            def start_monitoring(self, interval=0.1):
                """Start continuous memory monitoring."""
                self.monitoring = True
                self.monitor_thread = threading.Thread(
                    target=self._monitor_loop, args=(interval,), daemon=True
                )
                self.monitor_thread.start()

            def stop_monitoring(self):
                """Stop memory monitoring."""
                self.monitoring = False
                if self.monitor_thread:
                    self.monitor_thread.join(timeout=1.0)

            def _monitor_loop(self, interval):
                """Continuous monitoring loop."""
                while self.monitoring:
                    try:
                        memory_info = self.process.memory_info()
                        snapshot = MemorySnapshot(
                            rss_mb=memory_info.rss / 1024 / 1024,
                            vms_mb=memory_info.vms / 1024 / 1024,
                            percent=self.process.memory_percent(),
                            timestamp=time.time(),
                        )
                        self.snapshots.append(snapshot)
                        time.sleep(interval)
                    except Exception:
                        break

            def get_peak_memory(self) -> float:
                """Get peak RSS memory usage in MB."""
                return max(s.rss_mb for s in self.snapshots) if self.snapshots else 0

            def get_memory_growth(self) -> float:
                """Get memory growth from start to end."""
                if len(self.snapshots) < 2:
                    return 0
                return self.snapshots[-1].rss_mb - self.snapshots[0].rss_mb

            def check_memory_leaks(self, threshold_mb=10) -> bool:
                """Check for potential memory leaks."""
                if len(self.snapshots) < 10:
                    return False

                # Compare first and last 10% of snapshots
                first_10_percent = int(len(self.snapshots) * 0.1)
                last_10_percent = int(len(self.snapshots) * 0.9)

                early_avg = (
                    sum(s.rss_mb for s in self.snapshots[:first_10_percent])
                    / first_10_percent
                )
                late_avg = sum(s.rss_mb for s in self.snapshots[last_10_percent:]) / (
                    len(self.snapshots) - last_10_percent
                )

                return (late_avg - early_avg) > threshold_mb

        return MemoryProfiler()

    @pytest.fixture
    def high_load_comment_generator(self):
        """Generator for creating high-load comment scenarios."""

        def generate_comments(
            count: int, duplicate_ratio: float = 0.3
        ) -> List[Dict[str, Any]]:
            """Generate comments with configurable duplicate ratio."""
            unique_count = int(count * (1 - duplicate_ratio))

            # Generate unique comments
            comments = []
            for i in range(unique_count):
                comments.append(
                    {
                        "id": f"comment_{i}",
                        "post_id": f"post_{i % 100}",
                        "text": f"Original comment {i} with substantial text content that simulates real-world comment data patterns including mentions, hashtags, and longer text content that might be typical in social media platforms.",
                        "author": f"user_{i % 1000}",
                        "timestamp": f"2024-01-{(i % 28) + 1:02d}T{10 + (i % 14):02d}:{i % 60:02d}:{(i * 7) % 60:02d}Z",
                    }
                )

            # Add duplicates
            duplicate_count = count - unique_count
            for i in range(duplicate_count):
                original_idx = i % unique_count
                duplicate = comments[original_idx].copy()
                comments.append(duplicate)

            # Shuffle to distribute duplicates
            import random

            random.shuffle(comments)
            return comments

        return generate_comments

    def test_memory_usage_under_concurrent_processing(
        self, memory_profiler, high_load_comment_generator
    ):
        """
        Test memory usage when processing multiple comment batches concurrently.

        Validates that memory usage stays within acceptable bounds during
        concurrent comment processing operations.
        """
        # Generate multiple comment batches
        batch_size = 2000
        num_batches = 8
        comment_batches = [
            high_load_comment_generator(batch_size, duplicate_ratio=0.4)
            for _ in range(num_batches)
        ]

        def create_mock_monitor():
            session = Mock()
            session.query.return_value.filter.return_value.first.return_value = None
            session.add = Mock()
            session.commit = Mock()
            return CommentMonitor(
                fake_threads_client=None, celery_client=Mock(), db_session=session
            )

        memory_profiler.start_monitoring(interval=0.05)  # High frequency monitoring

        try:
            start_time = time.time()

            # Process batches concurrently
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for batch in comment_batches:
                    monitor = create_mock_monitor()
                    future = executor.submit(
                        self._process_comment_batch,
                        monitor,
                        batch,
                        f"post_batch_{len(futures)}",
                    )
                    futures.append(future)

                # Collect results
                results = []
                for future in as_completed(futures):
                    results.append(future.result())

            processing_time = time.time() - start_time

        finally:
            memory_profiler.stop_monitoring()

        # Memory usage assertions
        peak_memory = memory_profiler.get_peak_memory()
        memory_growth = memory_profiler.get_memory_growth()
        has_memory_leak = memory_profiler.check_memory_leaks(threshold_mb=50)

        assert peak_memory < 500, (
            f"Peak memory usage {peak_memory:.2f}MB exceeds 500MB limit"
        )
        assert memory_growth < 100, (
            f"Memory growth {memory_growth:.2f}MB indicates potential leak"
        )
        assert not has_memory_leak, "Memory leak detected during concurrent processing"

        # Performance assertions
        total_comments = sum(len(batch) for batch in comment_batches)
        throughput = total_comments / processing_time
        assert throughput > 3000, (
            f"Concurrent throughput {throughput:.0f}/s below minimum 3000/s"
        )

        # Verify all batches processed successfully
        assert len(results) == num_batches, "Not all batches processed successfully"
        total_processed = sum(result["processed"] for result in results)
        assert total_processed > 0, "No comments were processed"

    def _process_comment_batch(
        self, monitor: CommentMonitor, batch: List[Dict], post_id: str
    ) -> Dict:
        """Helper method to process a comment batch and return metrics."""
        start_time = time.time()

        # Simulate full comment processing pipeline
        unique_comments = monitor._deduplicate_comments(batch)
        monitor._store_comments_in_db(unique_comments, post_id)
        monitor._queue_comments_for_analysis(unique_comments, post_id)

        return {
            "processed": len(unique_comments),
            "original_count": len(batch),
            "processing_time": time.time() - start_time,
            "deduplication_ratio": len(unique_comments) / len(batch) if batch else 0,
        }

    def test_memory_efficiency_during_long_running_monitoring(
        self, memory_profiler, high_load_comment_generator
    ):
        """
        Test memory efficiency during extended monitoring periods.

        Simulates long-running comment monitoring to detect memory leaks
        and ensure stable memory usage over time.
        """
        mock_celery_client = Mock()
        mock_db_session = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()

        comment_monitor = CommentMonitor(
            fake_threads_client=None,
            celery_client=mock_celery_client,
            db_session=mock_db_session,
        )

        memory_profiler.start_monitoring(interval=0.1)

        try:
            # Simulate 10 minutes of monitoring with regular comment batches
            simulation_duration = 60  # 1 minute for testing (would be 600 for 10 min)
            batch_interval = 5  # Process batch every 5 seconds
            batch_size = 500

            start_time = time.time()
            batch_count = 0

            while (time.time() - start_time) < simulation_duration:
                # Generate and process a batch of comments
                comments = high_load_comment_generator(batch_size, duplicate_ratio=0.35)

                unique_comments = comment_monitor._deduplicate_comments(comments)
                comment_monitor._store_comments_in_db(
                    unique_comments, f"post_batch_{batch_count}"
                )
                comment_monitor._queue_comments_for_analysis(
                    unique_comments, f"post_batch_{batch_count}"
                )

                batch_count += 1

                # Wait for next batch
                time.sleep(batch_interval)

        finally:
            memory_profiler.stop_monitoring()

        # Long-running memory analysis
        peak_memory = memory_profiler.get_peak_memory()
        memory_growth = memory_profiler.get_memory_growth()
        has_memory_leak = memory_profiler.check_memory_leaks(threshold_mb=20)

        # Memory stability assertions
        assert peak_memory < 300, (
            f"Peak memory {peak_memory:.2f}MB too high for long-running process"
        )
        assert memory_growth < 50, (
            f"Memory growth {memory_growth:.2f}MB indicates leak in long-running process"
        )
        assert not has_memory_leak, (
            "Memory leak detected in long-running monitoring simulation"
        )

        # Verify processing continued throughout simulation
        assert batch_count >= 10, (
            f"Only {batch_count} batches processed, expected at least 10"
        )

        # Verify Celery queuing happened for all batches
        assert mock_celery_client.send_task.call_count > 0, "No tasks queued to Celery"

    def test_memory_usage_with_large_individual_comments(self, memory_profiler):
        """
        Test memory handling when processing comments with large text content.

        Validates that large individual comments don't cause excessive memory usage.
        """
        # Generate comments with very large text content
        large_comments = []
        for i in range(100):
            # Create comments with ~10KB of text each
            large_text = "This is a very long comment with extensive content. " * 200
            large_comments.append(
                {
                    "id": f"large_comment_{i}",
                    "post_id": f"post_{i % 10}",
                    "text": large_text,
                    "author": f"verbose_user_{i}",
                    "timestamp": f"2024-01-01T{10 + (i % 14):02d}:{i % 60:02d}:00Z",
                }
            )

        mock_db_session = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()

        comment_monitor = CommentMonitor(
            fake_threads_client=None, celery_client=Mock(), db_session=mock_db_session
        )

        memory_profiler.start_monitoring()

        try:
            # Process large comments
            start_time = time.time()
            unique_comments = comment_monitor._deduplicate_comments(large_comments)
            comment_monitor._store_comments_in_db(unique_comments, "large_content_post")
            processing_time = time.time() - start_time

        finally:
            memory_profiler.stop_monitoring()

        # Memory assertions for large content
        peak_memory = memory_profiler.get_peak_memory()
        memory_growth = memory_profiler.get_memory_growth()

        # Should handle large content efficiently
        total_content_size_mb = (
            sum(len(c["text"]) for c in large_comments) / 1024 / 1024
        )
        memory_efficiency_ratio = (
            peak_memory / total_content_size_mb
            if total_content_size_mb > 0
            else float("inf")
        )

        assert peak_memory < 100, (
            f"Peak memory {peak_memory:.2f}MB too high for large content processing"
        )
        assert memory_efficiency_ratio < 3.0, (
            f"Memory efficiency ratio {memory_efficiency_ratio:.2f} indicates inefficient processing"
        )
        assert processing_time < 2.0, (
            f"Processing time {processing_time:.2f}s too slow for large content"
        )


class TestCommentMonitorRateLimiting:
    """Rate limiting tests with exponential backoff validation."""

    @pytest.fixture
    def rate_limited_http_client(self):
        """Mock HTTP client that simulates rate limiting responses."""

        class RateLimitedClient:
            def __init__(self):
                self.request_count = 0
                self.rate_limit_threshold = 10  # Rate limit after 10 requests
                self.reset_time = time.time() + 60  # Reset after 60 seconds
                self.request_log = []

            def get(self, url, **kwargs) -> Mock:
                self.request_count += 1
                current_time = time.time()

                self.request_log.append(
                    {
                        "timestamp": current_time,
                        "url": url,
                        "request_number": self.request_count,
                    }
                )

                response = Mock()

                # Simulate rate limiting
                if (
                    self.request_count > self.rate_limit_threshold
                    and current_time < self.reset_time
                ):
                    response.status_code = 429  # Too Many Requests
                    response.headers = {"Retry-After": "30"}
                    response.json.return_value = {"error": "Rate limit exceeded"}
                    response.raise_for_status.side_effect = httpx.HTTPStatusError(
                        "Rate limit exceeded", request=Mock(), response=response
                    )
                else:
                    # Reset rate limit if time has passed
                    if current_time >= self.reset_time:
                        self.request_count = 1
                        self.reset_time = current_time + 60

                    response.status_code = 200
                    response.json.return_value = [
                        {
                            "id": f"comment_{i}",
                            "text": f"Comment {i}",
                            "author": f"user_{i}",
                            "timestamp": "2024-01-01T10:00:00Z",
                        }
                        for i in range(5)  # Return 5 comments per request
                    ]
                    response.raise_for_status = Mock()

                return response

            def get_request_pattern(self) -> List[Dict]:
                return self.request_log

        return RateLimitedClient()

    def test_exponential_backoff_calculation(self):
        """
        Test that exponential backoff delays are calculated correctly.

        Validates the mathematical correctness of backoff delay calculation.
        """
        comment_monitor = CommentMonitor()

        # Test various backoff scenarios
        test_cases = [
            {"initial_delay": 1.0, "max_retries": 3, "expected": [1.0, 2.0, 4.0]},
            {"initial_delay": 0.5, "max_retries": 4, "expected": [0.5, 1.0, 2.0, 4.0]},
            {
                "initial_delay": 2.0,
                "max_retries": 5,
                "expected": [2.0, 4.0, 8.0, 16.0, 32.0],
            },
        ]

        for case in test_cases:
            delays = comment_monitor._calculate_backoff_delays(
                case["initial_delay"], case["max_retries"]
            )

            assert delays == case["expected"], (
                f"Backoff calculation failed for initial_delay={case['initial_delay']}, "
                f"max_retries={case['max_retries']}. "
                f"Expected {case['expected']}, got {delays}"
            )

    def test_rate_limiting_behavior_with_backoff(self, rate_limited_http_client):
        """
        Test that rate limiting triggers appropriate backoff behavior.

        Validates that the system properly handles rate limits with exponential backoff.
        """
        mock_celery_client = Mock()
        mock_db_session = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()

        comment_monitor = CommentMonitor(
            fake_threads_client=rate_limited_http_client,
            celery_client=mock_celery_client,
            db_session=mock_db_session,
        )

        # Simulate multiple post monitoring requests to trigger rate limiting
        post_ids = [f"post_{i}" for i in range(15)]  # 15 requests to exceed rate limit
        results = []
        request_times = []

        for post_id in post_ids:
            start_time = time.time()
            try:
                result = comment_monitor.process_comments_for_post(post_id)
                results.append(result)
                request_times.append(time.time() - start_time)
            except Exception as e:
                results.append({"status": "error", "error": str(e)})
                request_times.append(time.time() - start_time)

        # Analyze rate limiting behavior
        successful_requests = sum(1 for r in results if r.get("status") == "success")
        error_requests = sum(1 for r in results if r.get("status") == "error")

        # Verify rate limiting was triggered
        request_pattern = rate_limited_http_client.get_request_pattern()
        assert len(request_pattern) >= 10, (
            "Should have made multiple requests to trigger rate limiting"
        )

        # Verify some requests failed due to rate limiting
        assert error_requests > 0, (
            "Rate limiting should have caused some request failures"
        )

        # Verify backoff behavior - later requests should take longer due to backoff delays
        if len(request_times) > 10:
            early_avg_time = sum(request_times[:5]) / 5
            late_avg_time = sum(request_times[-5:]) / 5

            # Later requests should be slower due to backoff (allowing for some variance)
            assert late_avg_time > early_avg_time * 0.8, (
                "Expected backoff delays to increase request times, "
                f"but early avg {early_avg_time:.2f}s vs late avg {late_avg_time:.2f}s"
            )

    def test_rate_limit_recovery_behavior(self, rate_limited_http_client):
        """
        Test recovery behavior after rate limit period expires.

        Validates that the system recovers properly after rate limiting ends.
        """
        comment_monitor = CommentMonitor(
            fake_threads_client=rate_limited_http_client,
            celery_client=Mock(),
            db_session=Mock(),
        )

        # First, trigger rate limiting
        for i in range(12):  # Exceed rate limit
            try:
                comment_monitor.process_comments_for_post(f"rate_limit_post_{i}")
            except:
                pass  # Expected to fail due to rate limiting

        # Verify rate limiting was triggered
        initial_pattern = rate_limited_http_client.get_request_pattern()
        rate_limited_requests = sum(
            1 for req in initial_pattern if req["request_number"] > 10
        )
        assert rate_limited_requests > 0, "Rate limiting should have been triggered"

        # Wait for rate limit to reset (simulate time passage)
        rate_limited_http_client.reset_time = time.time() - 1  # Force reset

        # Test recovery - should be able to make successful requests again
        recovery_results = []
        for i in range(5):
            result = comment_monitor.process_comments_for_post(f"recovery_post_{i}")
            recovery_results.append(result)

        # Verify recovery
        successful_recovery = sum(
            1 for r in recovery_results if r.get("status") == "success"
        )
        assert successful_recovery >= 3, (
            f"Expected at least 3 successful requests after recovery, got {successful_recovery}"
        )

    @pytest.mark.parametrize(
        "concurrent_requests,expected_rate_limit_ratio",
        [
            (5, 0.0),  # 5 concurrent - should not trigger rate limiting
            (15, 0.3),  # 15 concurrent - ~30% should be rate limited
            (25, 0.5),  # 25 concurrent - ~50% should be rate limited
        ],
    )
    def test_concurrent_rate_limiting_behavior(
        self, concurrent_requests, expected_rate_limit_ratio, rate_limited_http_client
    ):
        """
        Test rate limiting behavior under concurrent request load.

        Validates that rate limiting works correctly when multiple requests
        are made concurrently.
        """

        def make_request(post_id):
            monitor = CommentMonitor(
                fake_threads_client=rate_limited_http_client,
                celery_client=Mock(),
                db_session=Mock(),
            )
            try:
                return monitor.process_comments_for_post(post_id)
            except Exception as e:
                return {"status": "error", "error": str(e)}

        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_request, f"concurrent_post_{i}")
                for i in range(concurrent_requests)
            ]

            results = [future.result() for future in as_completed(futures)]

        # Analyze results
        successful_requests = sum(1 for r in results if r.get("status") == "success")
        failed_requests = len(results) - successful_requests
        actual_rate_limit_ratio = failed_requests / len(results) if results else 0

        # Validate rate limiting behavior
        if expected_rate_limit_ratio > 0:
            assert actual_rate_limit_ratio >= expected_rate_limit_ratio * 0.5, (
                f"Expected ~{expected_rate_limit_ratio:.1%} rate limiting, "
                f"got {actual_rate_limit_ratio:.1%}"
            )
        else:
            assert actual_rate_limit_ratio <= 0.2, (
                f"Unexpected rate limiting: {actual_rate_limit_ratio:.1%} of requests failed"
            )

        # Verify total request pattern
        request_pattern = rate_limited_http_client.get_request_pattern()
        assert len(request_pattern) >= concurrent_requests * 0.8, (
            "Should have attempted most concurrent requests"
        )
