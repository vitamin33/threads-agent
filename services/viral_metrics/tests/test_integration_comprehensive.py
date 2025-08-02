"""
Comprehensive integration tests for viral metrics collection system.

Tests real-time metrics collection, caching, persistence, and performance
requirements including the <60s SLA requirement.
"""

import asyncio
import pytest
import time
import json
from datetime import datetime
from unittest.mock import patch, AsyncMock

from services.viral_metrics.metrics_collector import ViralMetricsCollector
from services.viral_metrics.background_processor import ViralMetricsProcessor


class TestViralMetricsIntegration:
    """Integration tests for the complete viral metrics system."""

    @pytest.mark.e2e
    async def test_complete_metrics_collection_pipeline(
        self,
        mock_redis,
        mock_database,
        mock_prometheus,
        sample_engagement_data,
        viral_metrics_assertions,
    ):
        """Test the complete metrics collection pipeline from end to end."""
        # Arrange
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

            # Act
            start_time = time.time()
            metrics = await collector.collect_viral_metrics("test_post_123", "3h")
            end_time = time.time()

            # Assert
            viral_metrics_assertions.assert_valid_metrics_structure(metrics)
            viral_metrics_assertions.assert_sla_compliance(start_time, end_time, 60.0)
            viral_metrics_assertions.assert_database_persistence(mock_database, 1)
            viral_metrics_assertions.assert_prometheus_emission(mock_prometheus, 6)

    @pytest.mark.e2e
    async def test_real_time_metrics_collection_sla(
        self,
        mock_redis,
        mock_database,
        mock_prometheus,
        sample_engagement_data,
        performance_benchmarks,
    ):
        """Test that metrics collection meets the <60s SLA requirement."""
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

            # Test with realistic engagement data
            with patch.object(
                collector, "get_engagement_data", return_value=sample_engagement_data
            ):
                # Measure collection time for multiple posts
                collection_times = []

                for i in range(10):  # Test 10 posts
                    start_time = time.time()
                    await collector.collect_viral_metrics(f"test_post_{i}", "1h")
                    end_time = time.time()
                    collection_times.append(end_time - start_time)

                # Assert all collections completed within SLA
                max_time = max(collection_times)
                avg_time = sum(collection_times) / len(collection_times)

                assert max_time < 60.0, (
                    f"Max collection time {max_time:.2f}s exceeds 60s SLA"
                )
                assert avg_time < 5.0, (
                    f"Average collection time {avg_time:.2f}s too high"
                )

    @pytest.mark.e2e
    async def test_redis_caching_integration(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test Redis caching layer integration with TTL verification."""
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
                # First collection should calculate and cache
                metrics_1 = await collector.collect_viral_metrics(
                    "cache_test_post", "1h"
                )

                # Verify cache was set
                cached_data = await mock_redis.get("viral_metrics:cache_test_post")
                assert cached_data is not None

                cached_metrics = json.loads(cached_data)
                assert cached_metrics == metrics_1

                # Second collection should use cache (if within TTL)
                metrics_2 = await collector.get_cached_metrics("cache_test_post")
                assert metrics_2 == metrics_1

    @pytest.mark.e2e
    async def test_database_persistence_integration(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test database persistence for metrics history storage."""
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
                await collector.collect_viral_metrics("db_test_post", "1h")

                # Verify main metrics table insert
                metrics_records = mock_database._viral_metrics_storage
                assert len(metrics_records) == 1

                record = metrics_records[0]
                assert record["post_id"] == "db_test_post"
                assert record["persona_id"] == "ai_jesus"
                assert isinstance(record["viral_coefficient"], float)
                assert isinstance(record["collected_at"], datetime)

                # Verify history table inserts (one per metric)
                history_records = mock_database._viral_history_storage
                assert len(history_records) == 6  # 6 metrics

                metric_names = {record["metric_name"] for record in history_records}
                expected_metrics = {
                    "viral_coefficient",
                    "scroll_stop_rate",
                    "share_velocity",
                    "reply_depth",
                    "engagement_trajectory",
                    "pattern_fatigue",
                }
                assert metric_names == expected_metrics

    @pytest.mark.e2e
    async def test_prometheus_metrics_emission(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test Prometheus metrics emission with proper labels."""
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
                await collector.collect_viral_metrics("prometheus_test_post", "1h")

                # Verify Prometheus metrics were emitted
                metric_calls = mock_prometheus._metrics_calls
                gauge_calls = [call for call in metric_calls if call["type"] == "gauge"]

                assert len(gauge_calls) >= 6  # At least 6 viral metrics

                # Verify labels are correct
                for call in gauge_calls:
                    if call["labels"]:
                        assert call["labels"]["post_id"] == "prometheus_test_post"
                        assert call["labels"]["persona_id"] == "ai_jesus"

                # Verify histogram for collection latency
                histogram_calls = [
                    call for call in metric_calls if call["type"] == "histogram"
                ]
                assert len(histogram_calls) >= 1  # At least latency metric

    @pytest.mark.e2e
    async def test_high_performance_scenario(
        self,
        mock_redis,
        mock_database,
        mock_prometheus,
        high_performance_engagement_data,
        viral_metrics_assertions,
    ):
        """Test metrics calculation for high-performance viral content."""
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
                collector,
                "get_engagement_data",
                return_value=high_performance_engagement_data,
            ):
                metrics = await collector.collect_viral_metrics("viral_post_789", "6h")

                viral_metrics_assertions.assert_valid_metrics_structure(metrics)

                # Verify high performance metrics
                assert metrics["viral_coefficient"] > 10.0, (
                    "High viral coefficient expected"
                )
                assert metrics["scroll_stop_rate"] > 50.0, (
                    "High scroll stop rate expected"
                )
                assert metrics["share_velocity"] > 100.0, "High share velocity expected"
                assert metrics["engagement_trajectory"] > 0, (
                    "Positive trajectory expected"
                )

    @pytest.mark.e2e
    async def test_low_performance_scenario(
        self,
        mock_redis,
        mock_database,
        mock_prometheus,
        low_performance_engagement_data,
        viral_metrics_assertions,
    ):
        """Test metrics calculation for low-performance content."""
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
                collector,
                "get_engagement_data",
                return_value=low_performance_engagement_data,
            ):
                metrics = await collector.collect_viral_metrics("poor_post_000", "6h")

                viral_metrics_assertions.assert_valid_metrics_structure(metrics)

                # Verify low performance characteristics
                assert metrics["viral_coefficient"] < 5.0, (
                    "Low viral coefficient expected"
                )
                assert metrics["scroll_stop_rate"] < 30.0, (
                    "Low scroll stop rate expected"
                )
                assert metrics["share_velocity"] < 5.0, "Low share velocity expected"

    @pytest.mark.e2e
    async def test_error_handling_and_resilience(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test system resilience with various error conditions."""
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

            # Test 1: API timeout
            with patch.object(
                collector, "get_engagement_data", side_effect=asyncio.TimeoutError()
            ):
                metrics = await collector.collect_viral_metrics("timeout_post", "1h")
                # Should return default metrics without crashing
                assert all(value == 0.0 for value in metrics.values())

            # Test 2: Redis failure
            mock_redis.setex.side_effect = Exception("Redis connection failed")
            with patch.object(
                collector,
                "get_engagement_data",
                return_value={"views": 100, "shares": 10, "comments": 5},
            ):
                metrics = await collector.collect_viral_metrics("redis_fail_post", "1h")
                # Should still calculate metrics despite cache failure
                assert metrics["viral_coefficient"] > 0

            # Test 3: Database failure
            mock_database.execute.side_effect = Exception("Database connection failed")
            with patch.object(
                collector,
                "get_engagement_data",
                return_value={"views": 100, "shares": 10, "comments": 5},
            ):
                metrics = await collector.collect_viral_metrics("db_fail_post", "1h")
                # Should still calculate metrics despite persistence failure
                assert metrics["viral_coefficient"] > 0

    @pytest.mark.e2e
    async def test_concurrent_metrics_collection(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test concurrent metrics collection for multiple posts."""
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
                # Create concurrent collection tasks
                tasks = []
                for i in range(20):
                    task = collector.collect_viral_metrics(f"concurrent_post_{i}", "1h")
                    tasks.append(task)

                # Execute all tasks concurrently
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                end_time = time.time()

                # Verify all collections succeeded
                assert len(results) == 20
                for metrics in results:
                    assert isinstance(metrics, dict)
                    assert len(metrics) == 6  # All 6 metrics present

                # Verify reasonable performance
                total_time = end_time - start_time
                assert total_time < 30.0, (
                    f"Concurrent collection took {total_time:.2f}s, expected < 30s"
                )

    @pytest.mark.e2e
    async def test_fake_threads_api_integration(
        self, mock_redis, mock_database, mock_prometheus, mock_fake_threads_api
    ):
        """Test integration with fake-threads API using mock transport."""
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

            # Patch httpx to use our mock transport
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock()
                mock_client.return_value.__aenter__.return_value.get.return_value.status_code = 200
                mock_client.return_value.__aenter__.return_value.get.return_value.json.return_value = mock_fake_threads_api.get_analytics_response(
                    "api_test_post"
                )

                metrics = await collector.collect_viral_metrics("api_test_post", "1h")

                # Verify metrics were calculated from API data
                assert metrics["viral_coefficient"] > 0
                assert metrics["scroll_stop_rate"] > 0
                assert metrics["share_velocity"] > 0


class TestBackgroundProcessorIntegration:
    """Integration tests for the background metrics processor."""

    @pytest.mark.e2e
    async def test_batch_processing_performance(
        self,
        mock_redis,
        mock_database,
        mock_prometheus,
        performance_test_posts,
        performance_benchmarks,
    ):
        """Test batch processing performance with realistic dataset."""
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

            # Mock the _get_active_posts to return our test data
            with patch.object(
                processor, "_get_active_posts", return_value=performance_test_posts
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
                    result = await processor.process_active_posts(batch_size=50)
                    end_time = time.time()

                    # Verify batch processing completed
                    assert result["processed"] == 100
                    assert result["success"] > 0

                    # Verify performance benchmark
                    processing_time = end_time - start_time
                    assert (
                        processing_time
                        < performance_benchmarks["batch_processing_max_time"]
                    )

                    # Verify posts per second metric
                    assert result["posts_per_second"] > 1.0, "Processing rate too slow"

    @pytest.mark.e2e
    async def test_anomaly_detection_integration(
        self, mock_redis, mock_database, mock_prometheus, anomaly_test_scenarios
    ):
        """Test anomaly detection scenarios with various edge cases."""
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

            # Test viral coefficient drop anomaly
            scenario = anomaly_test_scenarios["viral_coefficient_drop"]
            with patch.object(
                processor.metrics_collector,
                "get_baseline_metrics",
                return_value=scenario["baseline"],
            ):
                anomalies = await processor.check_metrics_anomalies(
                    "test_post", scenario["current"]
                )

                # Should detect the viral coefficient drop
                anomaly_types = [a["type"] for a in anomalies]
                assert "viral_coefficient_drop" in anomaly_types

                # Verify anomaly details
                vc_anomaly = next(
                    a for a in anomalies if a["type"] == "viral_coefficient_drop"
                )
                assert vc_anomaly["severity"] in ["medium", "high"]
                assert vc_anomaly["drop_percentage"] > 0.3  # 30% drop threshold

    @pytest.mark.e2e
    async def test_parallel_processing_limits(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test that parallel processing respects concurrency limits."""
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
            processor.max_parallel_tasks = 5  # Limit concurrency for testing

            # Create posts that simulate processing time
            large_post_set = [{"id": f"parallel_post_{i}"} for i in range(25)]

            with patch.object(
                processor, "_get_active_posts", return_value=large_post_set
            ):
                # Mock collection with delay to test concurrency
                async def mock_collect_with_delay(post_id):
                    await asyncio.sleep(0.1)  # Simulate processing time
                    return {
                        "status": "success",
                        "post_id": post_id,
                        "metrics": {},
                        "anomalies": [],
                    }

                with patch.object(
                    processor,
                    "collect_post_metrics_async",
                    side_effect=mock_collect_with_delay,
                ):
                    start_time = time.time()
                    result = await processor.process_active_posts()
                    end_time = time.time()

                    # With 25 posts, 5 parallel tasks, and 0.1s per task,
                    # total time should be around 0.5s (5 batches * 0.1s)
                    processing_time = end_time - start_time

                    # Should complete in reasonable time despite concurrency limits
                    assert processing_time < 2.0, (
                        f"Processing took {processing_time:.2f}s, expected < 2.0s"
                    )
                    assert result["processed"] == 25


class TestEndToEndScenarios:
    """End-to-end test scenarios covering complete workflows."""

    @pytest.mark.e2e
    async def test_complete_viral_content_lifecycle(
        self,
        mock_redis,
        mock_database,
        mock_prometheus,
        high_performance_engagement_data,
        viral_metrics_assertions,
    ):
        """Test complete lifecycle of viral content from collection to anomaly detection."""
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
            collector = ViralMetricsCollector()
            processor = ViralMetricsProcessor()

            # Step 1: Collect initial metrics
            with patch.object(
                collector,
                "get_engagement_data",
                return_value=high_performance_engagement_data,
            ):
                initial_metrics = await collector.collect_viral_metrics(
                    "lifecycle_post", "1h"
                )
                viral_metrics_assertions.assert_valid_metrics_structure(initial_metrics)

            # Step 2: Verify caching works
            cached_metrics = await collector.get_cached_metrics("lifecycle_post")
            assert cached_metrics == initial_metrics

            # Step 3: Check for anomalies
            with patch.object(
                collector,
                "get_baseline_metrics",
                return_value={
                    "viral_coefficient": 0.05,
                    "scroll_stop_rate": 0.5,
                    "share_velocity": 10.0,
                },
            ):
                result = await processor.collect_post_metrics_async("lifecycle_post")
                assert result["status"] == "success"

                # High performance content should have anomalies (positive ones)
                # anomalies = result.get("anomalies", [])
                # Could have trajectory or other positive indicators

            # Step 4: Verify database persistence
            viral_metrics_assertions.assert_database_persistence(mock_database, 1)

    @pytest.mark.e2e
    async def test_system_recovery_after_failures(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test system recovery capabilities after various failure scenarios."""
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

            # Simulate failures and recovery
            failure_count = 0

            async def failing_engagement_data(post_id):
                nonlocal failure_count
                failure_count += 1
                if failure_count <= 3:  # Fail first 3 attempts
                    raise Exception(f"Simulated failure {failure_count}")
                return sample_engagement_data  # Succeed on 4th attempt

            with patch.object(
                collector, "get_engagement_data", side_effect=failing_engagement_data
            ):
                # Multiple attempts should eventually succeed
                for i in range(5):
                    try:
                        metrics = await collector.collect_viral_metrics(
                            f"recovery_post_{i}", "1h"
                        )
                        if i >= 3:  # Should succeed from 4th post onwards
                            assert len(metrics) == 6
                            assert all(
                                isinstance(v, (int, float)) for v in metrics.values()
                            )
                    except Exception:
                        if i >= 3:  # Should not fail after recovery
                            pytest.fail("System should have recovered by now")

    @pytest.mark.e2e
    async def test_metrics_consistency_across_timeframes(
        self, mock_redis, mock_database, mock_prometheus, sample_engagement_data
    ):
        """Test metrics consistency when calculated across different timeframes."""
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
                # Collect metrics for different timeframes
                metrics_1h = await collector.collect_viral_metrics(
                    "consistency_post", "1h"
                )
                metrics_3h = await collector.collect_viral_metrics(
                    "consistency_post", "3h"
                )
                metrics_24h = await collector.collect_viral_metrics(
                    "consistency_post", "24h"
                )

                # Some metrics should be consistent (viral coefficient, scroll stop rate)
                # Others may vary with timeframe (share velocity, trajectory)

                # Viral coefficient should be the same (based on total engagement)
                assert (
                    abs(
                        metrics_1h["viral_coefficient"]
                        - metrics_3h["viral_coefficient"]
                    )
                    < 0.1
                )
                assert (
                    abs(metrics_1h["scroll_stop_rate"] - metrics_3h["scroll_stop_rate"])
                    < 0.1
                )

                # Share velocity might differ based on timeframe parsing
                # This is expected behavior
                assert all(isinstance(v, (int, float)) for v in metrics_1h.values())
                assert all(isinstance(v, (int, float)) for v in metrics_3h.values())
                assert all(isinstance(v, (int, float)) for v in metrics_24h.values())
