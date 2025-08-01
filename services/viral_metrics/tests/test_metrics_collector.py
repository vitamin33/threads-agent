"""
Comprehensive test suite for ViralMetricsCollector following TDD principles.
Tests all viral metric calculators and real-time collection requirements.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from services.viral_metrics.metrics_collector import ViralMetricsCollector
from services.viral_metrics.calculators.viral_coefficient_calculator import (
    ViralCoefficientCalculator,
)
from services.viral_metrics.calculators.scroll_stop_rate_calculator import (
    ScrollStopRateCalculator,
)
from services.viral_metrics.calculators.share_velocity_calculator import (
    ShareVelocityCalculator,
)
from services.viral_metrics.calculators.reply_depth_calculator import (
    ReplyDepthCalculator,
)
from services.viral_metrics.calculators.engagement_trajectory_calculator import (
    EngagementTrajectoryCalculator,
)
from services.viral_metrics.calculators.pattern_fatigue_calculator import (
    PatternFatigueCalculator,
)


class TestViralMetricsCollector:
    """Test suite for the main metrics collector."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock external dependencies."""
        with (
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient"
            ) as prom_mock,
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection"
            ) as redis_mock,
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection"
            ) as db_mock,
        ):
            # Setup mock returns
            redis_instance = Mock()
            redis_instance.setex = AsyncMock()
            redis_instance.get = AsyncMock(return_value=None)
            redis_mock.return_value = redis_instance

            db_instance = Mock()
            db_instance.execute = AsyncMock()
            db_mock.return_value = db_instance

            prom_instance = Mock()
            prom_instance.gauge.return_value.set = Mock()
            prom_mock.return_value = prom_instance

            yield {
                "prometheus": prom_instance,
                "redis": redis_instance,
                "db": db_instance,
            }

    @pytest.fixture
    def sample_engagement_data(self):
        """Sample engagement data for testing."""
        return {
            "post_id": "test_post_123",
            "persona_id": "ai_jesus",
            "views": 1000,
            "impressions": 1200,
            "engaged_views": 800,
            "likes": 150,
            "comments": 50,
            "shares": 80,
            "saves": 20,
            "click_throughs": 30,
            "view_duration_avg": 15.5,
            "hourly_breakdown": [
                {"hour": 0, "shares": 10, "views": 100, "likes": 15, "comments": 5},
                {"hour": 1, "shares": 25, "views": 200, "likes": 30, "comments": 10},
                {"hour": 2, "shares": 45, "views": 300, "likes": 50, "comments": 15},
            ],
            "demographic_data": {
                "age_groups": {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2}
            },
        }

    @pytest.mark.asyncio
    async def test_collect_viral_metrics_calculates_all_metrics(
        self, mock_dependencies, sample_engagement_data
    ):
        """Test that all viral metrics are calculated correctly."""
        collector = ViralMetricsCollector()

        # Mock the engagement data fetch
        with patch.object(
            collector, "get_engagement_data", return_value=sample_engagement_data
        ):
            metrics = await collector.collect_viral_metrics("test_post_123", "3h")

        # Verify all metrics are present
        assert "viral_coefficient" in metrics
        assert "scroll_stop_rate" in metrics
        assert "share_velocity" in metrics
        assert "reply_depth" in metrics
        assert "engagement_trajectory" in metrics
        assert "pattern_fatigue" in metrics

        # Verify metric values are correct
        assert metrics["viral_coefficient"] == pytest.approx(
            13.0, abs=0.1
        )  # (80+50)/1000 * 100
        assert metrics["scroll_stop_rate"] == pytest.approx(
            66.67, abs=0.1
        )  # 800/1200 * 100
        assert metrics["share_velocity"] == 45.0  # Peak hour shares

    @pytest.mark.asyncio
    async def test_metrics_emitted_to_prometheus(
        self, mock_dependencies, sample_engagement_data
    ):
        """Test that metrics are properly emitted to Prometheus."""
        collector = ViralMetricsCollector()

        with patch.object(
            collector, "get_engagement_data", return_value=sample_engagement_data
        ):
            await collector.collect_viral_metrics("test_post_123", "3h")

        # Verify Prometheus gauge was called for each metric
        prom_client = mock_dependencies["prometheus"]
        assert prom_client.gauge.call_count >= 6  # At least 6 metrics

        # Verify gauge.set was called with correct labels
        gauge_calls = prom_client.gauge.return_value.set.call_args_list
        for call in gauge_calls:
            labels = call[1]["labels"]
            assert labels["post_id"] == "test_post_123"
            assert labels["persona_id"] == "ai_jesus"

    @pytest.mark.asyncio
    async def test_metrics_cached_in_redis(
        self, mock_dependencies, sample_engagement_data
    ):
        """Test that metrics are cached in Redis with correct TTL."""
        collector = ViralMetricsCollector()

        with patch.object(
            collector, "get_engagement_data", return_value=sample_engagement_data
        ):
            metrics = await collector.collect_viral_metrics("test_post_123", "3h")

        # Verify Redis setex was called
        redis_client = mock_dependencies["redis"]
        redis_client.setex.assert_called()

        # Check TTL is 300 seconds (5 minutes)
        call_args = redis_client.setex.call_args
        assert call_args[0][1] == 300  # TTL

        # Verify cached data structure
        cached_data = json.loads(call_args[0][2])
        assert cached_data == metrics

    @pytest.mark.asyncio
    async def test_metrics_stored_in_database(
        self, mock_dependencies, sample_engagement_data
    ):
        """Test that metrics are stored in database for historical tracking."""
        collector = ViralMetricsCollector()

        with patch.object(
            collector, "get_engagement_data", return_value=sample_engagement_data
        ):
            await collector.collect_viral_metrics("test_post_123", "3h")

        # Verify database execute was called
        db_client = mock_dependencies["db"]
        db_client.execute.assert_called()

        # Check the SQL query contains correct table
        call_args = db_client.execute.call_args
        sql_query = call_args[0][0]
        assert "viral_metrics" in sql_query

    @pytest.mark.asyncio
    async def test_collection_time_under_60_seconds(
        self, mock_dependencies, sample_engagement_data
    ):
        """Test that metrics collection completes within 60 seconds SLA."""
        collector = ViralMetricsCollector()

        with patch.object(
            collector, "get_engagement_data", return_value=sample_engagement_data
        ):
            start_time = asyncio.get_event_loop().time()
            await collector.collect_viral_metrics("test_post_123", "3h")
            elapsed_time = asyncio.get_event_loop().time() - start_time

        # Should complete well under 60 seconds (typically < 1 second)
        assert elapsed_time < 60.0

    @pytest.mark.asyncio
    async def test_handles_calculator_failures_gracefully(
        self, mock_dependencies, sample_engagement_data
    ):
        """Test that individual calculator failures don't crash the entire collection."""
        collector = ViralMetricsCollector()

        # Mock one calculator to fail
        with patch.object(
            collector.calculators["viral_coefficient"],
            "calculate",
            side_effect=Exception("Calculator error"),
        ):
            with patch.object(
                collector, "get_engagement_data", return_value=sample_engagement_data
            ):
                metrics = await collector.collect_viral_metrics("test_post_123", "3h")

        # Other metrics should still be calculated
        assert metrics["viral_coefficient"] == 0.0  # Failed metric defaults to 0
        assert metrics["scroll_stop_rate"] > 0  # Other metrics still calculated
        assert len(metrics) == 6  # All metrics present


class TestViralCoefficientCalculator:
    """Test suite for viral coefficient calculation."""

    @pytest.mark.asyncio
    async def test_calculates_viral_coefficient_correctly(self):
        """Test viral coefficient formula: (Shares + Comments) / Views * 100."""
        calculator = ViralCoefficientCalculator()

        engagement_data = {"views": 1000, "shares": 80, "comments": 50}

        result = await calculator.calculate("test_post", engagement_data, "1h")

        # (80 + 50) / 1000 * 100 = 13.0
        assert result == 13.0

    @pytest.mark.asyncio
    async def test_handles_zero_views(self):
        """Test that zero views returns 0 coefficient."""
        calculator = ViralCoefficientCalculator()

        engagement_data = {"views": 0, "shares": 10, "comments": 5}

        result = await calculator.calculate("test_post", engagement_data, "1h")
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_caps_at_maximum_50_percent(self):
        """Test that viral coefficient is capped at 50% to prevent outliers."""
        calculator = ViralCoefficientCalculator()

        engagement_data = {
            "views": 100,
            "shares": 40,
            "comments": 20,  # Would be 60% without cap
        }

        result = await calculator.calculate("test_post", engagement_data, "1h")
        assert result == 50.0


class TestScrollStopRateCalculator:
    """Test suite for scroll-stop rate calculation."""

    @pytest.mark.asyncio
    async def test_calculates_scroll_stop_rate_correctly(self):
        """Test scroll-stop rate formula: Engaged Views / Total Impressions * 100."""
        calculator = ScrollStopRateCalculator()

        engagement_data = {"impressions": 1200, "engaged_views": 800}

        result = await calculator.calculate("test_post", engagement_data, "1h")

        # 800 / 1200 * 100 = 66.67
        assert result == pytest.approx(66.67, abs=0.01)

    @pytest.mark.asyncio
    async def test_handles_zero_impressions(self):
        """Test that zero impressions returns 0 rate."""
        calculator = ScrollStopRateCalculator()

        engagement_data = {"impressions": 0, "engaged_views": 0}

        result = await calculator.calculate("test_post", engagement_data, "1h")
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_caps_at_100_percent(self):
        """Test that rate cannot exceed 100%."""
        calculator = ScrollStopRateCalculator()

        engagement_data = {
            "impressions": 100,
            "engaged_views": 150,  # Data error scenario
        }

        result = await calculator.calculate("test_post", engagement_data, "1h")
        assert result == 100.0


class TestShareVelocityCalculator:
    """Test suite for share velocity calculation."""

    @pytest.mark.asyncio
    async def test_calculates_peak_hour_velocity(self):
        """Test that share velocity finds peak sharing hour."""
        calculator = ShareVelocityCalculator()

        engagement_data = {
            "shares": 80,
            "hourly_breakdown": [
                {"hour": 0, "shares": 10},
                {"hour": 1, "shares": 25},
                {"hour": 2, "shares": 45},  # Peak hour
            ],
        }

        result = await calculator.calculate("test_post", engagement_data, "3h")
        assert result == 45.0

    @pytest.mark.asyncio
    async def test_fallback_calculation_without_hourly_data(self):
        """Test fallback to simple shares per timeframe."""
        calculator = ShareVelocityCalculator()

        engagement_data = {"shares": 60, "hourly_breakdown": []}

        result = await calculator.calculate("test_post", engagement_data, "3h")

        # 60 shares / 3 hours = 20 shares/hour
        assert result == 20.0

    @pytest.mark.asyncio
    async def test_parse_timeframe_correctly(self):
        """Test timeframe parsing for different formats."""
        calculator = ShareVelocityCalculator()

        assert calculator.parse_timeframe_hours("1h") == 1
        assert calculator.parse_timeframe_hours("24h") == 24
        assert calculator.parse_timeframe_hours("1d") == 24
        assert calculator.parse_timeframe_hours("7d") == 168
        assert calculator.parse_timeframe_hours("invalid") == 1  # Default


class TestEngagementTrajectoryCalculator:
    """Test suite for engagement trajectory calculation."""

    @pytest.mark.asyncio
    async def test_calculates_positive_trajectory(self):
        """Test detection of accelerating engagement."""
        calculator = EngagementTrajectoryCalculator()

        engagement_data = {
            "hourly_breakdown": [
                {"hour": 0, "likes": 10, "comments": 5, "shares": 5, "views": 100},
                {"hour": 1, "likes": 20, "comments": 10, "shares": 10, "views": 150},
                {"hour": 2, "likes": 40, "comments": 20, "shares": 20, "views": 200},
            ]
        }

        result = await calculator.calculate("test_post", engagement_data, "3h")

        # Should be positive (accelerating engagement)
        assert result > 0

    @pytest.mark.asyncio
    async def test_calculates_negative_trajectory(self):
        """Test detection of decelerating engagement."""
        calculator = EngagementTrajectoryCalculator()

        engagement_data = {
            "hourly_breakdown": [
                {"hour": 0, "likes": 40, "comments": 20, "shares": 20, "views": 100},
                {"hour": 1, "likes": 20, "comments": 10, "shares": 10, "views": 150},
                {"hour": 2, "likes": 10, "comments": 5, "shares": 5, "views": 200},
            ]
        }

        result = await calculator.calculate("test_post", engagement_data, "3h")

        # Should be negative (decelerating engagement)
        assert result < 0

    @pytest.mark.asyncio
    async def test_requires_minimum_data_points(self):
        """Test that trajectory needs at least 3 hours of data."""
        calculator = EngagementTrajectoryCalculator()

        engagement_data = {
            "hourly_breakdown": [
                {"hour": 0, "likes": 10, "comments": 5, "shares": 5, "views": 100}
            ]
        }

        result = await calculator.calculate("test_post", engagement_data, "1h")
        assert result == 0.0  # Not enough data

    @pytest.mark.asyncio
    async def test_trajectory_capped_at_bounds(self):
        """Test that trajectory is normalized to -100 to 100 scale."""
        calculator = EngagementTrajectoryCalculator()

        # Create extreme trajectory data
        engagement_data = {
            "hourly_breakdown": [
                {
                    "hour": i,
                    "likes": i * 1000,
                    "comments": i * 500,
                    "shares": i * 500,
                    "views": 100,
                }
                for i in range(10)
            ]
        }

        result = await calculator.calculate("test_post", engagement_data, "10h")

        # Should be capped at 100
        assert -100 <= result <= 100


class TestReplyDepthCalculator:
    """Test suite for reply depth calculation."""

    @pytest.mark.asyncio
    async def test_calculates_average_thread_depth(self):
        """Test calculation of average conversation depth."""
        calculator = ReplyDepthCalculator()

        # Mock thread data
        thread_data = [
            {
                "id": "1",
                "replies": [
                    {
                        "id": "1.1",
                        "replies": [
                            {"id": "1.1.1", "replies": []}  # Depth 3
                        ],
                    }
                ],
            },
            {
                "id": "2",
                "replies": [
                    {"id": "2.1", "replies": []}  # Depth 2
                ],
            },
        ]

        with patch.object(calculator, "get_comment_threads", return_value=thread_data):
            result = await calculator.calculate("test_post", {}, "1h")

        # Average of depth 3 and depth 2 = 2.5
        assert result == 2.5

    @pytest.mark.asyncio
    async def test_handles_no_replies(self):
        """Test posts with no comment threads."""
        calculator = ReplyDepthCalculator()

        with patch.object(calculator, "get_comment_threads", return_value=[]):
            result = await calculator.calculate("test_post", {}, "1h")

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_calculates_deep_nested_threads(self):
        """Test calculation of deeply nested conversation threads."""
        calculator = ReplyDepthCalculator()

        # Create deeply nested thread
        def create_nested_thread(depth):
            if depth == 0:
                return {"id": f"thread_{depth}", "replies": []}
            return {
                "id": f"thread_{depth}",
                "replies": [create_nested_thread(depth - 1)],
            }

        thread_data = [create_nested_thread(10)]  # 10 levels deep

        with patch.object(calculator, "get_comment_threads", return_value=thread_data):
            result = await calculator.calculate("test_post", {}, "1h")

        assert result == 11.0  # Root + 10 nested levels = 11 total depth


class TestPatternFatigueCalculator:
    """Test suite for pattern fatigue calculation."""

    @pytest.mark.asyncio
    async def test_calculates_pattern_fatigue_score(self):
        """Test basic pattern fatigue calculation."""
        calculator = PatternFatigueCalculator()

        # This will be implemented based on pattern usage history
        engagement_data = {"post_id": "test_post", "pattern_id": "question_hook"}

        result = await calculator.calculate("test_post", engagement_data, "7d")

        # Score should be between 0 and 1
        assert 0.0 <= result <= 1.0
