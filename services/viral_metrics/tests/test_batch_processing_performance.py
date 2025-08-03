"""
Batch processing performance tests for viral metrics system.

Tests parallel execution, throughput, and performance benchmarks
for background processing of viral metrics.
"""

import asyncio
import pytest
import time
from datetime import datetime
from unittest.mock import patch

from services.viral_metrics.background_processor import ViralMetricsProcessor


class TestBatchProcessingPerformance:
    """Performance tests for batch processing viral metrics."""

    @pytest.mark.e2e
    async def test_batch_processing_throughput(
        self, mock_redis, mock_database, mock_prometheus, performance_benchmarks
    ):
        """Test batch processing throughput under various load conditions."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Test different batch sizes
            batch_sizes = [10, 25, 50, 100]
            results = {}

            for batch_size in batch_sizes:
                # Create test posts
                test_posts = [
                    {
                        "id": f"batch_post_{i}",
                        "persona_id": f"persona_{i % 3}",
                        "created_at": datetime.now(),
                    }
                    for i in range(batch_size)
                ]

                with patch.object(
                    processor, "_get_active_posts", return_value=test_posts
                ):
                    with patch.object(
                        processor.metrics_collector,
                        "get_engagement_data",
                        return_value={
                            "views": 1000,
                            "shares": 50,
                            "comments": 25,
                            "impressions": 1200,
                            "engaged_views": 800,
                        },
                    ):
                        start_time = time.time()
                        result = await processor.process_active_posts(
                            batch_size=batch_size
                        )
                        end_time = time.time()

                        processing_time = end_time - start_time
                        throughput = (
                            batch_size / processing_time if processing_time > 0 else 0
                        )

                        results[batch_size] = {
                            "processing_time": processing_time,
                            "throughput": throughput,
                            "success_rate": result["success"] / result["processed"]
                            if result["processed"] > 0
                            else 0,
                        }

                        # Basic performance assertions
                        assert result["processed"] == batch_size
                        assert result["success"] > 0
                        assert throughput > 1.0, (
                            f"Throughput {throughput:.2f} posts/sec too low for batch size {batch_size}"
                        )

            # Verify throughput scales appropriately
            small_batch_throughput = results[10]["throughput"]
            large_batch_throughput = results[100]["throughput"]

            # Large batches should have higher total throughput (more posts per second)
            assert large_batch_throughput >= small_batch_throughput * 0.8, (
                "Batch processing efficiency degraded significantly"
            )

    @pytest.mark.e2e
    async def test_parallel_execution_limits(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test that parallel execution respects concurrency limits and performs efficiently."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Test different concurrency limits
            concurrency_limits = [5, 10, 20]
            processing_times = {}

            for limit in concurrency_limits:
                processor.max_parallel_tasks = limit

                # Create 50 test posts
                test_posts = [
                    {
                        "id": f"parallel_post_{i}_{limit}",
                        "persona_id": f"persona_{i % 3}",
                        "created_at": datetime.now(),
                    }
                    for i in range(50)
                ]

                # Mock processing with simulated delay
                call_count = 0

                async def mock_collect_with_tracking(post_id):
                    nonlocal call_count
                    call_count += 1
                    await asyncio.sleep(0.05)  # 50ms processing time
                    return {
                        "status": "success",
                        "post_id": post_id,
                        "metrics": {"viral_coefficient": 0.1, "scroll_stop_rate": 0.6},
                        "anomalies": [],
                    }

                with patch.object(
                    processor, "_get_active_posts", return_value=test_posts
                ):
                    with patch.object(
                        processor,
                        "collect_post_metrics_async",
                        side_effect=mock_collect_with_tracking,
                    ):
                        start_time = time.time()
                        result = await processor.process_active_posts()
                        end_time = time.time()

                        processing_time = end_time - start_time
                        processing_times[limit] = processing_time

                        # Verify all posts were processed
                        assert result["processed"] == 50
                        assert result["success"] == 50
                        assert call_count == 50

                        # With 50 posts and X parallel tasks, expected time is roughly:
                        # ceil(50 / X) * 0.05 seconds
                        expected_batches = (50 + limit - 1) // limit  # ceiling division
                        expected_time = expected_batches * 0.05

                        # Allow some overhead for task scheduling
                        assert processing_time < expected_time * 2, (
                            f"Processing time {processing_time:.2f}s too high for limit {limit}"
                        )

            # Higher concurrency should generally be faster (up to a point)
            assert processing_times[20] <= processing_times[5] * 1.2, (
                "Higher concurrency should improve performance"
            )

    @pytest.mark.e2e
    async def test_memory_usage_under_load(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test memory usage remains stable under high load."""
        import psutil
        import os

        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()
            process = psutil.Process(os.getpid())

            # Measure initial memory usage
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Process multiple large batches
            for batch_num in range(5):
                large_batch = [
                    {
                        "id": f"memory_test_post_{batch_num}_{i}",
                        "persona_id": f"persona_{i % 10}",
                        "created_at": datetime.now(),
                    }
                    for i in range(200)  # 200 posts per batch
                ]

                with patch.object(
                    processor, "_get_active_posts", return_value=large_batch
                ):
                    with patch.object(
                        processor.metrics_collector,
                        "get_engagement_data",
                        return_value={
                            "views": 1000,
                            "shares": 50,
                            "comments": 25,
                            "impressions": 1200,
                            "engaged_views": 800,
                            "hourly_breakdown": [
                                {
                                    "hour": i,
                                    "shares": i * 5,
                                    "views": i * 100,
                                    "likes": i * 15,
                                    "comments": i * 5,
                                }
                                for i in range(6)
                            ],
                        },
                    ):
                        await processor.process_active_posts(batch_size=50)

                        # Check memory usage after each batch
                        current_memory = process.memory_info().rss / 1024 / 1024  # MB
                        memory_increase = current_memory - initial_memory

                        # Memory increase should be reasonable (less than 100MB per batch)
                        assert memory_increase < 100 * (batch_num + 1), (
                            f"Memory usage increased too much: {memory_increase:.2f}MB"
                        )

                # Force garbage collection between batches
                import gc

                gc.collect()

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            total_increase = final_memory - initial_memory

            # Total memory increase should be reasonable for processing 1000 posts
            assert total_increase < 200, (
                f"Total memory increase {total_increase:.2f}MB too high"
            )

    @pytest.mark.e2e
    async def test_error_recovery_in_batch_processing(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test batch processing recovery from various error conditions."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Create test posts with some that will fail
            test_posts = [
                {
                    "id": f"error_test_post_{i}",
                    "persona_id": f"persona_{i % 3}",
                    "created_at": datetime.now(),
                }
                for i in range(20)
            ]

            # Mock that simulates failures for certain posts
            async def mock_collect_with_failures(post_id):
                if "5" in post_id or "15" in post_id:  # Fail posts with 5 or 15 in ID
                    raise Exception(f"Simulated failure for {post_id}")

                return {
                    "status": "success",
                    "post_id": post_id,
                    "metrics": {"viral_coefficient": 0.1},
                    "anomalies": [],
                }

            with patch.object(processor, "_get_active_posts", return_value=test_posts):
                with patch.object(
                    processor,
                    "collect_post_metrics_async",
                    side_effect=mock_collect_with_failures,
                ):
                    result = await processor.process_active_posts(batch_size=10)

                    # Should process all posts despite some failures
                    assert result["processed"] == 20
                    assert result["success"] == 18  # 20 - 2 failures
                    assert result["failed"] == 2

                    # Processing should continue despite failures
                    assert result["posts_per_second"] > 0

    @pytest.mark.e2e
    async def test_batch_processing_with_varying_load(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test batch processing performance under varying computational load."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Test scenarios with different computational complexity
            scenarios = {
                "light_load": {
                    "engagement_data": {"views": 100, "shares": 5, "comments": 2},
                    "expected_max_time": 5.0,
                },
                "medium_load": {
                    "engagement_data": {
                        "views": 10000,
                        "shares": 500,
                        "comments": 200,
                        "hourly_breakdown": [
                            {
                                "hour": i,
                                "shares": i * 10,
                                "views": i * 1000,
                                "likes": i * 150,
                                "comments": i * 50,
                            }
                            for i in range(24)  # Full day breakdown
                        ],
                    },
                    "expected_max_time": 10.0,
                },
                "heavy_load": {
                    "engagement_data": {
                        "views": 100000,
                        "shares": 5000,
                        "comments": 2000,
                        "hourly_breakdown": [
                            {
                                "hour": i,
                                "shares": i * 100,
                                "views": i * 10000,
                                "likes": i * 1500,
                                "comments": i * 500,
                            }
                            for i in range(24)
                        ],
                        "demographic_data": {
                            "age_groups": {f"age_{i}": 0.1 for i in range(10)},
                            "locations": {f"location_{i}": 0.05 for i in range(20)},
                        },
                    },
                    "expected_max_time": 20.0,
                },
            }

            for scenario_name, scenario_config in scenarios.items():
                test_posts = [
                    {
                        "id": f"{scenario_name}_post_{i}",
                        "persona_id": f"persona_{i % 2}",
                        "created_at": datetime.now(),
                    }
                    for i in range(30)
                ]

                with patch.object(
                    processor, "_get_active_posts", return_value=test_posts
                ):
                    with patch.object(
                        processor.metrics_collector,
                        "get_engagement_data",
                        return_value=scenario_config["engagement_data"],
                    ):
                        start_time = time.time()
                        result = await processor.process_active_posts(batch_size=15)
                        end_time = time.time()

                        processing_time = end_time - start_time

                        # Verify completion
                        assert result["processed"] == 30
                        assert result["success"] > 25  # Allow for some failures

                        # Verify performance bounds
                        assert processing_time < scenario_config["expected_max_time"], (
                            f"{scenario_name} took {processing_time:.2f}s, expected < {scenario_config['expected_max_time']}s"
                        )

                        # Verify reasonable throughput
                        throughput = result["posts_per_second"]
                        assert throughput > 1.0, (
                            f"{scenario_name} throughput {throughput:.2f} posts/sec too low"
                        )

    @pytest.mark.e2e
    async def test_batch_processing_database_optimization(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test batch processing database write optimization."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Track database calls
            db_call_count = 0
            original_execute = mock_database.execute

            async def counting_execute(*args, **kwargs):
                nonlocal db_call_count
                db_call_count += 1
                return await original_execute(*args, **kwargs)

            mock_database.execute = counting_execute

            # Process batch of posts
            test_posts = [
                {
                    "id": f"db_opt_post_{i}",
                    "persona_id": f"persona_{i % 3}",
                    "created_at": datetime.now(),
                }
                for i in range(50)
            ]

            with patch.object(processor, "_get_active_posts", return_value=test_posts):
                with patch.object(
                    processor.metrics_collector,
                    "get_engagement_data",
                    return_value={
                        "views": 1000,
                        "shares": 50,
                        "comments": 25,
                        "impressions": 1200,
                        "engaged_views": 800,
                    },
                ):
                    result = await processor.process_active_posts(batch_size=25)

                    # Verify processing completed
                    assert result["processed"] == 50
                    assert result["success"] > 0

                    # Each successful post should generate:
                    # - 1 insert into viral_metrics
                    # - 6 inserts into viral_metrics_history (one per metric)
                    # Total: 7 database calls per successful post
                    expected_min_calls = result["success"] * 7

                    # Should have reasonable number of database calls
                    assert db_call_count >= expected_min_calls, (
                        f"Expected at least {expected_min_calls} DB calls, got {db_call_count}"
                    )
                    assert db_call_count <= expected_min_calls * 1.2, (
                        f"Too many DB calls: {db_call_count}, expected ~{expected_min_calls}"
                    )

    @pytest.mark.e2e
    async def test_batch_processing_cache_efficiency(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test cache efficiency during batch processing."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Track cache operations
            cache_sets = 0
            cache_gets = 0

            original_setex = mock_redis.setex
            original_get = mock_redis.get

            async def counting_setex(*args, **kwargs):
                nonlocal cache_sets
                cache_sets += 1
                return await original_setex(*args, **kwargs)

            async def counting_get(*args, **kwargs):
                nonlocal cache_gets
                cache_gets += 1
                return await original_get(*args, **kwargs)

            mock_redis.setex = counting_setex
            mock_redis.get = counting_get

            # Process batch with some duplicate posts (simulating cache hits)
            test_posts = [
                {
                    "id": f"cache_post_{i % 20}",
                    "persona_id": f"persona_{i % 3}",
                    "created_at": datetime.now(),
                }
                for i in range(40)  # 40 posts, but only 20 unique IDs
            ]

            with patch.object(processor, "_get_active_posts", return_value=test_posts):
                with patch.object(
                    processor.metrics_collector,
                    "get_engagement_data",
                    return_value={"views": 1000, "shares": 50, "comments": 25},
                ):
                    result = await processor.process_active_posts(batch_size=20)

                    # Verify processing
                    assert result["processed"] == 40

                    # Should have cache operations
                    assert cache_sets > 0, "Should have cached some metrics"

                    # Due to duplicate post IDs, some operations should benefit from caching
                    # (though the exact behavior depends on processing order)
                    total_cache_ops = cache_sets + cache_gets
                    assert total_cache_ops > 0, "Should have some cache operations"
