"""Comprehensive unit tests for VariantMetricsAPI."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import json

from services.dashboard_api.variant_metrics import VariantMetricsAPI


class TestVariantMetricsAPIComprehensive:
    """Comprehensive test suite for VariantMetricsAPI."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection with realistic data."""
        db = AsyncMock()
        # Setup common database responses
        db.fetch_all.return_value = [
            {
                "id": "var_1",
                "persona_id": "ai-jesus",
                "content": "Test variant 1",
                "predicted_er": 0.065,
                "actual_er": 0.058,
                "posted_at": datetime.now() - timedelta(hours=2),
                "status": "active",
                "interaction_count": 150,
                "view_count": 2500,
            },
            {
                "id": "var_2",
                "persona_id": "ai-jesus",
                "content": "Test variant 2",
                "predicted_er": 0.052,
                "actual_er": 0.067,
                "posted_at": datetime.now() - timedelta(hours=1),
                "status": "active",
                "interaction_count": 180,
                "view_count": 2800,
            },
        ]
        return db

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis connection with caching behavior."""
        redis = AsyncMock()
        redis.get.return_value = None  # No cached data by default
        redis.setex.return_value = True
        return redis

    @pytest.fixture
    def mock_early_kill_monitor(self):
        """Mock EarlyKillMonitor with realistic behavior."""
        monitor = AsyncMock()
        monitor.get_kill_statistics.return_value = {
            "total_kills_today": 3,
            "avg_time_to_kill": 4.2,
            "kill_reasons": {"low_engagement": 2, "negative_sentiment": 1},
        }
        return monitor

    @pytest.fixture
    def mock_fatigue_detector(self):
        """Mock PatternFatigueDetector."""
        detector = AsyncMock()
        detector.get_fatigue_warnings.return_value = [
            {
                "pattern_id": "curiosity_gap",
                "fatigue_score": 0.85,
                "warning_level": "high",
                "recommendation": "Switch to controversy patterns",
            }
        ]
        return detector

    @pytest.fixture
    def metrics_api(
        self, mock_db, mock_redis, mock_early_kill_monitor, mock_fatigue_detector
    ):
        """Create VariantMetricsAPI instance with comprehensive mocks."""
        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            return_value=mock_db,
        ):
            with patch(
                "services.dashboard_api.variant_metrics.get_redis_connection",
                return_value=mock_redis,
            ):
                api = VariantMetricsAPI()
                api.early_kill_monitor = mock_early_kill_monitor
                api.fatigue_detector = mock_fatigue_detector
                return api

    @pytest.mark.asyncio
    async def test_get_live_metrics_comprehensive_data_structure(self, metrics_api):
        """Test comprehensive data structure returned by get_live_metrics."""
        persona_id = "ai-jesus"

        result = await metrics_api.get_live_metrics(persona_id)

        # Verify all required sections are present
        required_sections = [
            "summary",
            "active_variants",
            "performance_leaders",
            "early_kills_today",
            "pattern_fatigue_warnings",
            "optimization_opportunities",
            "real_time_feed",
        ]

        for section in required_sections:
            assert section in result, f"Missing required section: {section}"

    @pytest.mark.asyncio
    async def test_get_performance_summary_calculations(self, metrics_api, mock_db):
        """Test performance summary calculations are accurate."""
        persona_id = "ai-jesus"

        result = await metrics_api.get_performance_summary(persona_id)

        assert "total_variants" in result
        assert "avg_engagement_rate" in result
        assert "performance_trend" in result
        assert "prediction_accuracy" in result

        # Verify calculations
        assert result["total_variants"] == 2
        # Expected avg ER: (0.058 + 0.067) / 2 = 0.0625
        assert abs(result["avg_engagement_rate"] - 0.0625) < 0.001

    @pytest.mark.asyncio
    async def test_get_active_variants_with_time_calculations(
        self, metrics_api, mock_db
    ):
        """Test active variants include accurate time calculations."""
        persona_id = "ai-jesus"

        result = await metrics_api.get_active_variants(persona_id)

        assert len(result) == 2

        # Check first variant (posted 2 hours ago)
        variant1 = result[0]
        assert variant1["id"] == "var_1"
        assert "time_since_post" in variant1
        assert "hours_active" in variant1["time_since_post"]
        assert abs(variant1["time_since_post"]["hours_active"] - 2.0) < 0.1

        # Check performance delta calculation
        assert "performance_vs_prediction" in variant1
        expected_delta = (0.058 - 0.065) / 0.065  # -10.8%
        assert (
            abs(
                variant1["performance_vs_prediction"]["relative_delta"] - expected_delta
            )
            < 0.01
        )

    @pytest.mark.asyncio
    async def test_get_top_performers_ranking(self, metrics_api, mock_db):
        """Test that top performers are correctly ranked."""
        persona_id = "ai-jesus"

        result = await metrics_api.get_top_performers(persona_id)

        assert len(result) > 0
        # Should be sorted by engagement rate (descending)
        if len(result) > 1:
            assert result[0]["actual_er"] >= result[1]["actual_er"]

        # Top performer should be var_2 (0.067 ER)
        assert result[0]["id"] == "var_2"
        assert result[0]["actual_er"] == 0.067

    @pytest.mark.asyncio
    async def test_get_optimization_suggestions_logic(self, metrics_api, mock_db):
        """Test optimization suggestion generation logic."""
        persona_id = "ai-jesus"

        # Mock methods for different scenarios
        metrics_api.calculate_early_kill_rate = AsyncMock(
            return_value=0.40
        )  # High kill rate
        metrics_api.calculate_prediction_accuracy = AsyncMock(
            return_value=0.75
        )  # Low accuracy

        suggestions = await metrics_api.get_optimization_suggestions(persona_id)

        assert len(suggestions) > 0

        # Should suggest prediction calibration due to high kill rate
        calibration_suggestions = [
            s for s in suggestions if s["type"] == "prediction_calibration"
        ]
        assert len(calibration_suggestions) > 0
        assert "kill rate" in calibration_suggestions[0]["description"].lower()

        # Should suggest model tuning due to low accuracy
        tuning_suggestions = [s for s in suggestions if s["type"] == "model_tuning"]
        assert len(tuning_suggestions) > 0

    @pytest.mark.asyncio
    async def test_redis_caching_behavior(self, metrics_api, mock_redis):
        """Test Redis caching is used appropriately."""
        persona_id = "ai-jesus"

        # First call - should cache result
        await metrics_api.get_performance_summary(persona_id)

        # Verify cache set was called
        mock_redis.setex.assert_called()
        cache_key = mock_redis.setex.call_args[0][0]
        assert persona_id in cache_key
        assert "performance_summary" in cache_key

        # Second call with cached data
        cached_data = json.dumps({"total_variants": 5, "cached": True})
        mock_redis.get.return_value = cached_data

        result = await metrics_api.get_performance_summary(persona_id)
        assert result["cached"] is True

    @pytest.mark.asyncio
    async def test_error_handling_database_failure(self, metrics_api, mock_db):
        """Test error handling when database operations fail."""
        persona_id = "ai-jesus"

        # Simulate database error
        mock_db.fetch_all.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception) as exc_info:
            await metrics_api.get_active_variants(persona_id)

        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_performance_delta_edge_cases(self, metrics_api):
        """Test performance delta calculation edge cases."""
        # Zero prediction (should handle gracefully)
        delta = metrics_api.calculate_performance_delta(0.05, 0.0)
        assert delta == float("inf") or delta is None  # Implementation dependent

        # Negative values (shouldn't occur in real data but test robustness)
        delta = metrics_api.calculate_performance_delta(-0.01, 0.05)
        assert isinstance(delta, (int, float))

        # Equal values
        delta = metrics_api.calculate_performance_delta(0.06, 0.06)
        assert delta == 0.0

    @pytest.mark.asyncio
    async def test_get_recent_events_chronological_order(self, metrics_api, mock_db):
        """Test that recent events are returned in chronological order."""
        persona_id = "ai-jesus"

        # Mock events with different timestamps
        now = datetime.now()
        mock_events = [
            {"event_type": "early_kill", "timestamp": now - timedelta(minutes=10)},
            {
                "event_type": "performance_update",
                "timestamp": now - timedelta(minutes=5),
            },
            {"event_type": "variant_created", "timestamp": now - timedelta(minutes=15)},
        ]
        mock_db.fetch_all.return_value = mock_events

        result = await metrics_api.get_recent_events(persona_id)

        # Should be ordered by timestamp (most recent first)
        timestamps = [event["timestamp"] for event in result]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_concurrent_access_thread_safety(self, metrics_api):
        """Test thread safety with concurrent access."""
        import asyncio

        persona_ids = ["ai-jesus", "ai-buddha", "ai-socrates"]

        # Run multiple concurrent requests
        tasks = [
            metrics_api.get_performance_summary(persona_id)
            for persona_id in persona_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, dict)


class TestVariantMetricsAPIEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def metrics_api_minimal(self):
        """Create minimal VariantMetricsAPI for edge case testing."""
        with patch("services.dashboard_api.variant_metrics.get_db_connection"):
            with patch("services.dashboard_api.variant_metrics.get_redis_connection"):
                return VariantMetricsAPI()

    @pytest.mark.asyncio
    async def test_empty_persona_id(self, metrics_api_minimal):
        """Test handling of empty persona_id."""
        result = await metrics_api_minimal.get_live_metrics("")

        # Should return empty/default structure
        assert result["summary"]["total_variants"] == 0
        assert result["active_variants"] == []

    @pytest.mark.asyncio
    async def test_nonexistent_persona(self, metrics_api_minimal, mock_db):
        """Test handling of non-existent persona."""
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = []  # No data found

        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            return_value=mock_db,
        ):
            api = VariantMetricsAPI()
            result = await api.get_active_variants("nonexistent-persona")

        assert result == []

    @pytest.mark.asyncio
    async def test_malformed_database_data(self, metrics_api_minimal):
        """Test handling of malformed database responses."""
        mock_db = AsyncMock()
        # Return malformed data (missing required fields)
        mock_db.fetch_all.return_value = [
            {"id": "var_1"},  # Missing other required fields
            {"content": "test"},  # Missing ID
        ]

        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            return_value=mock_db,
        ):
            api = VariantMetricsAPI()
            result = await api.get_active_variants("test-persona")

        # Should handle gracefully and filter out malformed entries
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, metrics_api_minimal):
        """Test behavior when Redis is unavailable."""
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis connection failed")
        mock_redis.setex.side_effect = Exception("Redis connection failed")

        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = [{"id": "test", "total_variants": 1}]

        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            return_value=mock_db,
        ):
            with patch(
                "services.dashboard_api.variant_metrics.get_redis_connection",
                return_value=mock_redis,
            ):
                api = VariantMetricsAPI()

                # Should work without caching
                result = await api.get_performance_summary("test-persona")
                assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, metrics_api_minimal):
        """Test performance with large datasets."""
        import time

        # Create large mock dataset
        large_dataset = [
            {
                "id": f"var_{i}",
                "persona_id": "test-persona",
                "content": f"Test variant {i}",
                "predicted_er": 0.05 + (i % 10) * 0.001,
                "actual_er": 0.05 + (i % 8) * 0.002,
                "posted_at": datetime.now() - timedelta(hours=i % 24),
                "status": "active",
                "interaction_count": 100 + i,
                "view_count": 2000 + i * 10,
            }
            for i in range(1000)  # 1000 variants
        ]

        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = large_dataset

        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            return_value=mock_db,
        ):
            api = VariantMetricsAPI()

            start_time = time.time()
            result = await api.get_active_variants("test-persona")
            processing_time = time.time() - start_time

            # Should process within reasonable time (< 1 second)
            assert processing_time < 1.0
            assert len(result) == 1000
