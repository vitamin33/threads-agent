"""
End-to-end system integration tests for viral metrics collection.

Tests the complete system including Celery tasks, real-time processing,
and full integration scenarios with all components working together.
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch

from services.viral_metrics.metrics_collector import ViralMetricsCollector
from services.viral_metrics.background_processor import (
    ViralMetricsProcessor,
    collect_post_metrics,
    process_active_posts_batch,
)


class TestE2ESystemIntegration:
    """End-to-end integration tests for the complete viral metrics system."""

    @pytest.mark.e2e
    async def test_complete_system_workflow(
        self,
        mock_redis,
        mock_database,
        mock_prometheus,
        sample_engagement_data,
        viral_metrics_assertions,
        performance_benchmarks,
    ):
        """Test the complete system workflow from API call to database storage."""
        with (
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
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
        ):
            # Step 1: Initialize system components
            collector = ViralMetricsCollector()
            processor = ViralMetricsProcessor()

            # Step 2: Simulate real engagement data fetch
            with patch.object(
                collector, "get_engagement_data", return_value=sample_engagement_data
            ):
                # Step 3: Collect metrics (this should complete within SLA)
                start_time = time.time()
                metrics = await collector.collect_viral_metrics("e2e_test_post", "3h")
                collection_time = time.time() - start_time

                # Verify collection performance
                viral_metrics_assertions.assert_sla_compliance(
                    start_time, start_time + collection_time, 60.0
                )
                viral_metrics_assertions.assert_valid_metrics_structure(metrics)

                # Step 4: Verify caching worked
                cached_metrics = await collector.get_cached_metrics("e2e_test_post")
                assert cached_metrics == metrics, (
                    "Cached metrics should match collected metrics"
                )

                # Step 5: Verify database persistence
                viral_metrics_assertions.assert_database_persistence(mock_database, 1)

                # Step 6: Verify Prometheus emission
                viral_metrics_assertions.assert_prometheus_emission(mock_prometheus, 6)

                # Step 7: Test anomaly detection
                baseline_metrics = {"viral_coefficient": 0.05, "scroll_stop_rate": 0.5}
                with patch.object(
                    collector, "get_baseline_metrics", return_value=baseline_metrics
                ):
                    result = await processor.collect_post_metrics_async("e2e_test_post")

                    assert result["status"] == "success"
                    assert result["post_id"] == "e2e_test_post"
                    assert "metrics" in result
                    assert "anomalies" in result

    @pytest.mark.e2e
    async def test_celery_task_integration(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test Celery task integration for background processing."""
        with (
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
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
        ):
            # Mock engagement data fetch
            with patch(
                "services.viral_metrics.metrics_collector.ViralMetricsCollector.get_engagement_data",
                return_value=sample_engagement_data,
            ):
                # Test single post Celery task
                result = collect_post_metrics("celery_test_post")

                assert result["status"] == "success"
                assert result["post_id"] == "celery_test_post"
                assert "metrics" in result

                # Test batch processing Celery task
                with patch(
                    "services.viral_metrics.background_processor.ViralMetricsProcessor._get_active_posts",
                    return_value=[
                        {
                            "id": "batch_post_1",
                            "persona_id": "test_persona",
                            "created_at": datetime.now(),
                        },
                        {
                            "id": "batch_post_2",
                            "persona_id": "test_persona",
                            "created_at": datetime.now(),
                        },
                    ],
                ):
                    batch_result = process_active_posts_batch(batch_size=10)

                    assert batch_result["processed"] == 2
                    assert batch_result["success"] >= 1  # At least one should succeed
                    assert "elapsed_time_seconds" in batch_result
                    assert "posts_per_second" in batch_result

    @pytest.mark.e2e
    async def test_high_concurrency_load_handling(
        self,
        mock_redis,
        mock_database,
        mock_prometheus,
        sample_engagement_data,
        performance_benchmarks,
    ):
        """Test system behavior under high concurrency load."""
        with (
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
            collector = ViralMetricsCollector()

            # Simulate high load with many concurrent requests
            with patch.object(
                collector, "get_engagement_data", return_value=sample_engagement_data
            ):
                # Create 100 concurrent collection tasks
                tasks = []
                for i in range(100):
                    task = collector.collect_viral_metrics(f"load_test_post_{i}", "1h")
                    tasks.append(task)

                # Execute all tasks concurrently
                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

                # Analyze results
                successful_results = [
                    r for r in results if isinstance(r, dict) and len(r) == 6
                ]
                failed_results = [r for r in results if isinstance(r, Exception)]

                # Verify performance under load
                total_time = end_time - start_time
                success_rate = len(successful_results) / len(results)
                throughput = len(successful_results) / total_time

                # System should handle high load gracefully
                assert success_rate > 0.9, (
                    f"Success rate {success_rate:.2%} too low under high load"
                )
                assert throughput > 10, f"Throughput {throughput:.2f} posts/sec too low"
                assert total_time < 60, (
                    f"High load processing took {total_time:.2f}s, should be < 60s"
                )

                # Verify no memory leaks or resource exhaustion
                assert len(failed_results) < 10, (
                    f"Too many failures: {len(failed_results)}"
                )

    @pytest.mark.e2e
    async def test_system_resilience_under_failures(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test system resilience and recovery under various failure conditions."""
        with (
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
            collector = ViralMetricsCollector()

            # Test scenario 1: Intermittent API failures
            failure_count = 0

            async def failing_api_call(post_id):
                nonlocal failure_count
                failure_count += 1
                if failure_count % 3 == 0:  # Fail every 3rd call
                    raise Exception("API temporarily unavailable")
                return sample_engagement_data

            with patch.object(
                collector, "get_engagement_data", side_effect=failing_api_call
            ):
                results = []

                # Make 10 calls, expect ~7 to succeed
                for i in range(10):
                    try:
                        metrics = await collector.collect_viral_metrics(
                            f"resilience_test_{i}", "1h"
                        )
                        results.append(("success", metrics))
                    except Exception as e:
                        results.append(("failure", str(e)))

                successful_calls = [r for r in results if r[0] == "success"]

                # Should have reasonable success rate despite failures
                success_rate = len(successful_calls) / len(results)
                assert success_rate > 0.6, (
                    f"Success rate {success_rate:.2%} too low with intermittent failures"
                )

            # Test scenario 2: Cache failure recovery
            mock_redis.setex.side_effect = Exception("Redis connection lost")

            with patch.object(
                collector, "get_engagement_data", return_value=sample_engagement_data
            ):
                # Should still work without caching
                metrics = await collector.collect_viral_metrics(
                    "cache_failure_test", "1h"
                )
                assert len(metrics) == 6, (
                    "Should calculate metrics despite cache failure"
                )

            # Test scenario 3: Database failure recovery
            mock_database.execute.side_effect = Exception("Database connection lost")

            with patch.object(
                collector, "get_engagement_data", return_value=sample_engagement_data
            ):
                # Should still calculate metrics even if persistence fails
                metrics = await collector.collect_viral_metrics("db_failure_test", "1h")
                assert len(metrics) == 6, (
                    "Should calculate metrics despite database failure"
                )

    @pytest.mark.e2e
    async def test_real_time_streaming_scenario(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test real-time streaming scenario with continuously updating metrics."""
        with (
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
            collector = ViralMetricsCollector()

            # Simulate evolving engagement data over time
            base_data = {
                "post_id": "streaming_test_post",
                "persona_id": "ai_jesus",
                "views": 1000,
                "impressions": 1200,
                "engaged_views": 800,
                "likes": 100,
                "comments": 30,
                "shares": 50,
                "saves": 15,
                "click_throughs": 25,
                "view_duration_avg": 12.0,
                "hourly_breakdown": [],
                "demographic_data": {},
            }

            # Collect metrics at different time points with evolving data
            metrics_timeline = []

            for hour in range(6):
                # Simulate viral growth
                multiplier = 1 + hour * 0.5  # Growth over time
                current_data = base_data.copy()
                current_data.update(
                    {
                        "views": int(base_data["views"] * multiplier),
                        "likes": int(base_data["likes"] * multiplier),
                        "comments": int(base_data["comments"] * multiplier),
                        "shares": int(base_data["shares"] * multiplier),
                        "hourly_breakdown": [
                            {
                                "hour": h,
                                "shares": int(base_data["shares"] * 0.2 * (h + 1)),
                                "views": int(base_data["views"] * 0.2 * (h + 1)),
                                "likes": int(base_data["likes"] * 0.2 * (h + 1)),
                                "comments": int(base_data["comments"] * 0.2 * (h + 1)),
                            }
                            for h in range(hour + 1)
                        ],
                    }
                )

                with patch.object(
                    collector, "get_engagement_data", return_value=current_data
                ):
                    start_time = time.time()
                    metrics = await collector.collect_viral_metrics(
                        "streaming_test_post", f"{hour + 1}h"
                    )
                    collection_time = time.time() - start_time

                    metrics_timeline.append(
                        {
                            "hour": hour,
                            "metrics": metrics,
                            "collection_time": collection_time,
                        }
                    )

                    # Each collection should still meet SLA
                    assert collection_time < 5.0, (
                        f"Collection at hour {hour} took {collection_time:.2f}s"
                    )

                # Small delay to simulate real-time scenario
                await asyncio.sleep(0.1)

            # Analyze metrics evolution
            viral_coefficients = [
                m["metrics"]["viral_coefficient"] for m in metrics_timeline
            ]
            share_velocities = [
                m["metrics"]["share_velocity"] for m in metrics_timeline
            ]

            # Should show viral growth pattern
            assert viral_coefficients[-1] > viral_coefficients[0], (
                "Viral coefficient should increase over time"
            )
            assert share_velocities[-1] > share_velocities[0], (
                "Share velocity should increase over time"
            )

            # Collection times should remain stable despite growing data
            collection_times = [m["collection_time"] for m in metrics_timeline]
            avg_collection_time = sum(collection_times) / len(collection_times)
            assert avg_collection_time < 2.0, (
                f"Average collection time {avg_collection_time:.2f}s too high"
            )

    @pytest.mark.e2e
    async def test_multi_persona_batch_processing(
        self, mock_redis, mock_database, mock_prometheus, performance_benchmarks
    ):
        """Test batch processing across multiple personas simultaneously."""
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

            # Create posts from multiple personas
            personas = ["ai_jesus", "ai_buddha", "ai_socrates", "ai_confucius"]
            multi_persona_posts = []

            for persona in personas:
                for i in range(25):  # 25 posts per persona = 100 total
                    multi_persona_posts.append(
                        {
                            "id": f"{persona}_post_{i}",
                            "persona_id": persona,
                            "created_at": datetime.now() - timedelta(hours=i % 6),
                        }
                    )

            # Create different engagement patterns for each persona
            def get_persona_engagement_data(post_id):
                if "jesus" in post_id:
                    return {
                        "views": 5000,
                        "shares": 400,
                        "comments": 200,
                        "impressions": 6000,
                        "engaged_views": 4000,
                    }
                elif "buddha" in post_id:
                    return {
                        "views": 3000,
                        "shares": 150,
                        "comments": 100,
                        "impressions": 3600,
                        "engaged_views": 2400,
                    }
                elif "socrates" in post_id:
                    return {
                        "views": 2000,
                        "shares": 120,
                        "comments": 80,
                        "impressions": 2400,
                        "engaged_views": 1600,
                    }
                else:  # confucius
                    return {
                        "views": 1500,
                        "shares": 90,
                        "comments": 60,
                        "impressions": 1800,
                        "engaged_views": 1200,
                    }

            with patch.object(
                processor, "_get_active_posts", return_value=multi_persona_posts
            ):
                with patch.object(
                    processor.metrics_collector,
                    "get_engagement_data",
                    side_effect=lambda post_id: get_persona_engagement_data(post_id),
                ):
                    start_time = time.time()
                    result = await processor.process_active_posts(batch_size=20)
                    end_time = time.time()

                    processing_time = end_time - start_time

                    # Verify batch processing completed successfully
                    assert result["processed"] == 100
                    assert result["success"] > 90  # Allow for some failures

                    # Should complete within reasonable time
                    assert (
                        processing_time
                        < performance_benchmarks["batch_processing_max_time"]
                    )

                    # Should achieve good throughput
                    assert result["posts_per_second"] > 3.0, (
                        f"Multi-persona throughput {result['posts_per_second']:.2f} posts/sec too low"
                    )

                    # Verify database contains metrics for all personas
                    stored_metrics = mock_database._viral_metrics_storage
                    personas_in_db = {record["persona_id"] for record in stored_metrics}

                    # Should have processed posts from multiple personas
                    assert len(personas_in_db) > 1, "Should process multiple personas"

    @pytest.mark.e2e
    async def test_system_monitoring_and_observability(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test system monitoring and observability features."""
        with (
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
            collector = ViralMetricsCollector()

            with patch.object(
                collector, "get_engagement_data", return_value=sample_engagement_data
            ):
                # Collect metrics for multiple posts
                posts_to_monitor = [f"monitoring_post_{i}" for i in range(10)]

                for post_id in posts_to_monitor:
                    await collector.collect_viral_metrics(post_id, "1h")

                # Verify Prometheus metrics were emitted
                prometheus_calls = mock_prometheus._metrics_calls

                # Should have gauge metrics for each viral metric
                gauge_calls = [
                    call for call in prometheus_calls if call["type"] == "gauge"
                ]
                histogram_calls = [
                    call for call in prometheus_calls if call["type"] == "histogram"
                ]

                # Should have viral metrics for each post
                assert len(gauge_calls) >= 60, (
                    f"Expected at least 60 gauge calls (10 posts * 6 metrics), got {len(gauge_calls)}"
                )

                # Should have latency measurements
                assert len(histogram_calls) >= 10, (
                    f"Expected at least 10 histogram calls, got {len(histogram_calls)}"
                )

                # Verify metric labels are properly set
                labeled_calls = [call for call in gauge_calls if call.get("labels")]
                assert len(labeled_calls) > 0, "Should have labeled metrics"

                for call in labeled_calls[:5]:  # Check first 5
                    labels = call["labels"]
                    assert "post_id" in labels, "Should have post_id label"
                    assert "persona_id" in labels, "Should have persona_id label"

                # Verify database storage for monitoring
                stored_metrics = mock_database._viral_metrics_storage
                stored_history = mock_database._viral_history_storage

                assert len(stored_metrics) == 10, (
                    "Should store main metrics for all posts"
                )
                assert len(stored_history) == 60, (
                    "Should store history for all metrics (10 posts * 6 metrics)"
                )

                # Verify data structure for monitoring queries
                for record in stored_metrics[:3]:  # Check first 3
                    assert "collected_at" in record, (
                        "Should have timestamp for monitoring"
                    )
                    assert isinstance(record["viral_coefficient"], (int, float)), (
                        "Should have numeric values"
                    )


class TestSystemPerformanceRegression:
    """Regression tests to ensure system performance doesn't degrade."""

    @pytest.mark.e2e
    async def test_performance_regression_baseline(
        self,
        mock_redis,
        mock_database,
        mock_prometheus,
        sample_engagement_data,
        performance_benchmarks,
    ):
        """Establish performance regression baseline."""
        with (
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
            collector = ViralMetricsCollector()

            # Performance test parameters
            test_posts = [f"perf_regression_post_{i}" for i in range(50)]

            with patch.object(
                collector, "get_engagement_data", return_value=sample_engagement_data
            ):
                # Measure single collection performance
                single_times = []
                for i in range(10):
                    start_time = time.time()
                    await collector.collect_viral_metrics(f"single_perf_{i}", "1h")
                    end_time = time.time()
                    single_times.append(end_time - start_time)

                avg_single_time = sum(single_times) / len(single_times)
                max_single_time = max(single_times)

                # Single collection performance benchmarks
                assert (
                    avg_single_time
                    < performance_benchmarks["single_collection_max_time"]
                ), (
                    f"Average single collection time {avg_single_time:.3f}s exceeds benchmark"
                )
                assert (
                    max_single_time
                    < performance_benchmarks["single_collection_max_time"] * 2
                ), f"Max single collection time {max_single_time:.3f}s too high"

                # Measure concurrent performance
                concurrent_tasks = [
                    collector.collect_viral_metrics(post_id, "1h")
                    for post_id in test_posts
                ]

                start_time = time.time()
                results = await asyncio.gather(*concurrent_tasks)
                end_time = time.time()

                concurrent_time = end_time - start_time
                throughput = len(test_posts) / concurrent_time

                # Concurrent performance benchmarks
                assert concurrent_time < 30.0, (
                    f"Concurrent processing took {concurrent_time:.2f}s, expected < 30s"
                )
                assert throughput > 5.0, (
                    f"Throughput {throughput:.2f} posts/sec below baseline"
                )

                # Verify all results are valid
                valid_results = [
                    r for r in results if isinstance(r, dict) and len(r) == 6
                ]
                assert len(valid_results) == len(test_posts), (
                    "All concurrent collections should succeed"
                )

    @pytest.mark.e2e
    async def test_memory_usage_regression(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test for memory usage regression."""
        import psutil
        import os

        with (
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
            collector = ViralMetricsCollector()
            process = psutil.Process(os.getpid())

            # Measure initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            with patch.object(
                collector, "get_engagement_data", return_value=sample_engagement_data
            ):
                # Process many posts to test for memory leaks
                for batch in range(10):  # 10 batches of 20 posts = 200 total
                    batch_tasks = []

                    for i in range(20):
                        post_id = f"memory_regression_batch_{batch}_post_{i}"
                        task = collector.collect_viral_metrics(post_id, "1h")
                        batch_tasks.append(task)

                    await asyncio.gather(*batch_tasks)

                    # Force garbage collection
                    import gc

                    gc.collect()

                    # Check memory usage
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = current_memory - initial_memory

                    # Memory increase should be bounded
                    assert memory_increase < 50, (
                        f"Memory increased by {memory_increase:.2f}MB after batch {batch}"
                    )

            # Final memory check
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            total_increase = final_memory - initial_memory

            # Total memory increase should be reasonable for 200 posts
            assert total_increase < 100, (
                f"Total memory increase {total_increase:.2f}MB too high"
            )
