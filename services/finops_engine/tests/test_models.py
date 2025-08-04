"""
Test suite for statistical anomaly detection models.

Tests for StatisticalModel, TrendModel, SeasonalModel, and FatigueModel
following TDD methodology with comprehensive edge case coverage.
"""

from datetime import datetime, timedelta
import math

# Import the models we're going to implement
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import StatisticalModel, TrendModel, SeasonalModel, FatigueModel


class TestStatisticalModel:
    """Test suite for basic statistical anomaly detection."""

    def test_statistical_model_initialization(self):
        """Test StatisticalModel initializes with default window size."""
        model = StatisticalModel()
        assert model.window_size == 100  # Default window size
        assert model.threshold == 2.0  # Default z-score threshold
        assert len(model.data_points) == 0

    def test_statistical_model_custom_initialization(self):
        """Test StatisticalModel with custom parameters."""
        model = StatisticalModel(window_size=50, threshold=3.0)
        assert model.window_size == 50
        assert model.threshold == 3.0
        assert len(model.data_points) == 0

    def test_add_data_point_normal_case(self):
        """Test adding data points to the model."""
        model = StatisticalModel(window_size=3)
        model.add_data_point(10.0)
        model.add_data_point(12.0)
        model.add_data_point(11.0)

        assert len(model.data_points) == 3
        assert model.data_points == [10.0, 12.0, 11.0]

    def test_sliding_window_behavior(self):
        """Test that data points slide out when window size is exceeded."""
        model = StatisticalModel(window_size=2)
        model.add_data_point(1.0)
        model.add_data_point(2.0)
        model.add_data_point(3.0)  # Should push out 1.0

        assert len(model.data_points) == 2
        assert model.data_points == [2.0, 3.0]

    def test_calculate_anomaly_score_insufficient_data(self):
        """Test anomaly detection with insufficient data."""
        model = StatisticalModel()
        model.add_data_point(10.0)

        score = model.calculate_anomaly_score(15.0)
        assert score == 0.0  # Should return 0 for insufficient data

    def test_calculate_anomaly_score_zero_std_deviation(self):
        """Test anomaly detection when all data points are identical."""
        model = StatisticalModel()
        for _ in range(5):
            model.add_data_point(10.0)

        score = model.calculate_anomaly_score(10.0)
        assert score == 0.0  # No anomaly when value matches constant data

        score = model.calculate_anomaly_score(15.0)
        assert score == float("inf")  # Infinite anomaly score for different value

    def test_calculate_anomaly_score_normal_case(self):
        """Test normal anomaly score calculation."""
        model = StatisticalModel()
        data_points = [10.0, 12.0, 8.0, 11.0, 9.0]
        for point in data_points:
            model.add_data_point(point)

        # Test value close to mean (should have low score)
        score = model.calculate_anomaly_score(10.0)
        assert 0 <= score < model.threshold

        # Test outlier value (should have high score)
        score = model.calculate_anomaly_score(20.0)
        assert score > model.threshold

    def test_is_anomaly_detection(self):
        """Test anomaly detection boolean result."""
        model = StatisticalModel(threshold=2.0)
        data_points = [10.0, 12.0, 8.0, 11.0, 9.0]
        for point in data_points:
            model.add_data_point(point)

        assert not model.is_anomaly(10.0)  # Normal value
        assert model.is_anomaly(20.0)  # Anomaly value
        assert not model.is_anomaly(9.5)  # Border normal value

    def test_get_statistics(self):
        """Test getting basic statistics from the model."""
        model = StatisticalModel()
        data_points = [10.0, 12.0, 8.0, 11.0, 9.0]
        for point in data_points:
            model.add_data_point(point)

        stats = model.get_statistics()
        assert "mean" in stats
        assert "std_dev" in stats
        assert "count" in stats
        assert stats["count"] == 5
        assert abs(stats["mean"] - 10.0) < 0.1
        assert stats["std_dev"] > 0


class TestTrendModel:
    """Test suite for trend-based anomaly detection."""

    def test_trend_model_initialization(self):
        """Test TrendModel initializes with default parameters."""
        model = TrendModel()
        assert model.lookback_hours == 24
        assert model.trend_threshold == 0.5  # 50% drop threshold
        assert len(model.hourly_data) == 0

    def test_trend_model_custom_initialization(self):
        """Test TrendModel with custom parameters."""
        model = TrendModel(lookback_hours=48, trend_threshold=0.3)
        assert model.lookback_hours == 48
        assert model.trend_threshold == 0.3

    def test_add_hourly_data_normal_case(self):
        """Test adding hourly data points."""
        model = TrendModel()
        timestamp = datetime.now()
        model.add_hourly_data(timestamp, 100.0)

        assert len(model.hourly_data) == 1
        assert model.hourly_data[0] == (timestamp, 100.0)

    def test_hourly_data_cleanup_old_entries(self):
        """Test that old hourly data gets cleaned up."""
        model = TrendModel(lookback_hours=1)
        now = datetime.now()
        old_time = now - timedelta(hours=2)

        model.add_hourly_data(old_time, 50.0)
        model.add_hourly_data(now, 100.0)

        # Should only keep recent data
        assert len(model.hourly_data) == 1
        assert model.hourly_data[0][1] == 100.0

    def test_calculate_baseline_insufficient_data(self):
        """Test baseline calculation with insufficient data."""
        model = TrendModel()
        baseline = model.calculate_baseline()
        assert baseline == 0.0

    def test_calculate_baseline_normal_case(self):
        """Test normal baseline calculation."""
        model = TrendModel()
        now = datetime.now()

        # Add 5 hours of data
        for i in range(5):
            timestamp = now - timedelta(hours=i)
            model.add_hourly_data(timestamp, 100.0 + i * 10)

        baseline = model.calculate_baseline()
        assert baseline > 0
        assert abs(baseline - 120.0) < 10  # Should be around average

    def test_detect_trend_break_insufficient_data(self):
        """Test trend break detection with insufficient data."""
        model = TrendModel()
        is_break = model.detect_trend_break(50.0)
        assert not is_break

    def test_detect_trend_break_normal_case(self):
        """Test normal trend break detection."""
        model = TrendModel(trend_threshold=0.5)
        now = datetime.now()

        # Add baseline data (average ~100)
        for i in range(10):
            timestamp = now - timedelta(hours=i)
            model.add_hourly_data(timestamp, 100.0)

        # Test normal value (no break)
        assert not model.detect_trend_break(95.0)

        # Test significant drop (should detect break)
        assert model.detect_trend_break(40.0)  # 60% drop

    def test_get_trend_metrics(self):
        """Test getting trend metrics."""
        model = TrendModel()
        now = datetime.now()

        for i in range(3):
            timestamp = now - timedelta(hours=i)
            model.add_hourly_data(timestamp, 100.0 + i * 5)

        metrics = model.get_trend_metrics()
        assert "baseline" in metrics
        assert "data_points" in metrics
        assert "lookback_hours" in metrics
        assert metrics["data_points"] == 3


class TestSeasonalModel:
    """Test suite for weekly seasonal pattern detection."""

    def test_seasonal_model_initialization(self):
        """Test SeasonalModel initializes with default parameters."""
        model = SeasonalModel()
        assert model.period_hours == 168  # 7 days * 24 hours
        assert len(model.seasonal_data) == 168
        assert all(values == [] for values in model.seasonal_data)

    def test_seasonal_model_custom_initialization(self):
        """Test SeasonalModel with custom period."""
        model = SeasonalModel(period_hours=24)  # Daily pattern
        assert model.period_hours == 24
        assert len(model.seasonal_data) == 24

    def test_add_seasonal_data_normal_case(self):
        """Test adding seasonal data points."""
        model = SeasonalModel(period_hours=24)
        timestamp = datetime(2023, 1, 1, 14, 0)  # Sunday 2PM

        model.add_seasonal_data(timestamp, 100.0)
        hour_index = 14  # 2PM = hour 14
        assert len(model.seasonal_data[hour_index]) == 1
        assert model.seasonal_data[hour_index][0] == 100.0

    def test_add_seasonal_data_multiple_weeks(self):
        """Test adding data across multiple weeks."""
        model = SeasonalModel(period_hours=168)
        base_time = datetime(2023, 1, 1, 10, 0)  # Sunday 10AM

        # Add data for same hour across different weeks
        for week in range(3):
            timestamp = base_time + timedelta(weeks=week)
            model.add_seasonal_data(timestamp, 100.0 + week * 10)

        hour_index = 6 * 24 + 10  # Sunday (weekday 6) 10AM = hour 154 in weekly pattern
        assert len(model.seasonal_data[hour_index]) == 3
        assert model.seasonal_data[hour_index] == [100.0, 110.0, 120.0]

    def test_get_seasonal_baseline_no_data(self):
        """Test seasonal baseline with no historical data."""
        model = SeasonalModel()
        timestamp = datetime.now()
        baseline = model.get_seasonal_baseline(timestamp)
        assert baseline == 0.0

    def test_get_seasonal_baseline_normal_case(self):
        """Test normal seasonal baseline calculation."""
        model = SeasonalModel(period_hours=24)
        target_time = datetime(2023, 1, 8, 15, 0)  # Sunday 3PM

        # Add historical data for 3PM slot
        hour_15_data = [90.0, 100.0, 110.0, 95.0, 105.0]
        model.seasonal_data[15] = hour_15_data

        baseline = model.get_seasonal_baseline(target_time)
        expected_avg = sum(hour_15_data) / len(hour_15_data)
        assert abs(baseline - expected_avg) < 0.1

    def test_is_seasonal_anomaly_insufficient_data(self):
        """Test seasonal anomaly detection with insufficient data."""
        model = SeasonalModel()
        timestamp = datetime.now()
        assert not model.is_seasonal_anomaly(timestamp, 50.0)

    def test_is_seasonal_anomaly_normal_case(self):
        """Test normal seasonal anomaly detection."""
        model = SeasonalModel(period_hours=24, anomaly_threshold=0.3)
        target_time = datetime(2023, 1, 8, 15, 0)

        # Set up baseline data (average = 100)
        model.seasonal_data[15] = [95.0, 100.0, 105.0, 100.0, 100.0]

        # Test normal value
        assert not model.is_seasonal_anomaly(target_time, 102.0)

        # Test anomaly value (70% of baseline)
        assert model.is_seasonal_anomaly(target_time, 65.0)

    def test_get_seasonal_metrics(self):
        """Test getting seasonal pattern metrics."""
        model = SeasonalModel(period_hours=24)

        # Add some data
        model.seasonal_data[10] = [100.0, 110.0, 90.0]
        model.seasonal_data[14] = [80.0, 85.0]

        metrics = model.get_seasonal_metrics()
        assert "period_hours" in metrics
        assert "total_data_points" in metrics
        assert "hours_with_data" in metrics
        assert metrics["period_hours"] == 24
        assert metrics["total_data_points"] == 5
        assert metrics["hours_with_data"] == 2


class TestFatigueModel:
    """Test suite for pattern fatigue detection."""

    def test_fatigue_model_initialization(self):
        """Test FatigueModel initializes with default parameters."""
        model = FatigueModel()
        assert model.decay_factor == 0.95
        assert model.fatigue_threshold == 0.7
        assert len(model.pattern_usage) == 0

    def test_fatigue_model_custom_initialization(self):
        """Test FatigueModel with custom parameters."""
        model = FatigueModel(decay_factor=0.9, fatigue_threshold=0.8)
        assert model.decay_factor == 0.9
        assert model.fatigue_threshold == 0.8

    def test_record_pattern_usage_new_pattern(self):
        """Test recording usage of a new pattern."""
        model = FatigueModel()
        timestamp = datetime.now()

        model.record_pattern_usage("hook_type_1", timestamp)
        assert "hook_type_1" in model.pattern_usage
        assert len(model.pattern_usage["hook_type_1"]) == 1

    def test_record_pattern_usage_existing_pattern(self):
        """Test recording multiple uses of same pattern."""
        model = FatigueModel()
        now = datetime.now()

        model.record_pattern_usage("hook_type_1", now)
        model.record_pattern_usage("hook_type_1", now + timedelta(hours=1))

        assert len(model.pattern_usage["hook_type_1"]) == 2

    def test_calculate_fatigue_score_no_usage(self):
        """Test fatigue calculation for unused pattern."""
        model = FatigueModel()
        score = model.calculate_fatigue_score("unused_pattern")
        assert score == 0.0

    def test_calculate_fatigue_score_single_usage(self):
        """Test fatigue calculation for single pattern usage."""
        model = FatigueModel()
        now = datetime.now()

        model.record_pattern_usage("pattern_1", now)
        score = model.calculate_fatigue_score("pattern_1")

        # Should be ~1.0 for single recent use (no decay applied)
        assert 0.9 <= score <= 1.0

    def test_calculate_fatigue_score_multiple_usage(self):
        """Test fatigue calculation for heavy pattern usage."""
        model = FatigueModel(decay_factor=0.8)
        now = datetime.now()

        # Record multiple recent uses
        for i in range(5):
            timestamp = now - timedelta(hours=i)
            model.record_pattern_usage("overused_pattern", timestamp)

        score = model.calculate_fatigue_score("overused_pattern")
        assert score > 0.5  # Should show significant fatigue

    def test_calculate_fatigue_score_with_decay(self):
        """Test that older usage has less impact due to decay."""
        model = FatigueModel(decay_factor=0.5)
        now = datetime.now()

        # Record old usage
        old_time = now - timedelta(days=7)
        model.record_pattern_usage("pattern_1", old_time)

        # Record recent usage
        model.record_pattern_usage("pattern_1", now)

        score = model.calculate_fatigue_score("pattern_1")

        # Recent usage should dominate due to decay
        assert score > 0.0
        # But shouldn't be as high as if both were recent

    def test_is_pattern_fatigued_normal_case(self):
        """Test pattern fatigue detection."""
        model = FatigueModel(fatigue_threshold=0.6)
        now = datetime.now()

        # Light usage with higher threshold - not fatigued
        model = FatigueModel(fatigue_threshold=1.1)  # Higher than single use score
        model.record_pattern_usage("light_pattern", now)
        assert not model.is_pattern_fatigued("light_pattern")

        # Heavy usage - fatigued (use original model with lower threshold)
        heavy_model = FatigueModel(fatigue_threshold=0.6)
        for i in range(10):
            timestamp = now - timedelta(hours=i * 0.5)
            heavy_model.record_pattern_usage("heavy_pattern", timestamp)

        assert heavy_model.is_pattern_fatigued("heavy_pattern")

    def test_get_fatigue_metrics(self):
        """Test getting fatigue metrics for all patterns."""
        model = FatigueModel()
        now = datetime.now()

        # Record usage for multiple patterns
        model.record_pattern_usage("pattern_1", now)
        model.record_pattern_usage("pattern_2", now)
        model.record_pattern_usage("pattern_1", now - timedelta(hours=1))

        metrics = model.get_fatigue_metrics()
        assert "total_patterns" in metrics
        assert "fatigued_patterns" in metrics
        assert "pattern_scores" in metrics
        assert metrics["total_patterns"] == 2
        assert "pattern_1" in metrics["pattern_scores"]
        assert "pattern_2" in metrics["pattern_scores"]

    def test_cleanup_old_usage_data(self):
        """Test cleanup of old usage data."""
        model = FatigueModel(max_history_days=1)
        now = datetime.now()
        old_time = now - timedelta(days=2)

        # Record old and new usage
        model.record_pattern_usage("pattern_1", old_time)
        model.record_pattern_usage("pattern_1", now)

        # Trigger cleanup
        model.cleanup_old_usage()

        # Should only keep recent usage
        assert len(model.pattern_usage["pattern_1"]) == 1
        assert model.pattern_usage["pattern_1"][0] == now


class TestModelsIntegration:
    """Integration tests showing how models work together."""

    def test_multi_model_anomaly_detection(self):
        """Test using multiple models together for comprehensive anomaly detection."""
        # Initialize all models
        statistical = StatisticalModel(threshold=2.0)
        trend = TrendModel(trend_threshold=0.4)
        seasonal = SeasonalModel(period_hours=24)
        fatigue = FatigueModel(
            fatigue_threshold=4.0
        )  # High threshold to avoid fatigue in this test

        # Simulate normal operational data
        now = datetime.now()
        base_value = 100.0

        # Add historical data to all models
        for i in range(48):  # 48 hours of data
            timestamp = now - timedelta(hours=i)
            value = base_value + (i % 12) * 5  # Some variation

            statistical.add_data_point(value)
            trend.add_hourly_data(timestamp, value)
            seasonal.add_seasonal_data(timestamp, value)

        # Record some pattern usage for fatigue model
        for i in range(3):
            fatigue.record_pattern_usage("common_hook", now - timedelta(hours=i * 8))

        # Test current value against all models
        current_value = 105.0
        current_time = now

        statistical_anomaly = statistical.is_anomaly(current_value)
        trend_break = trend.detect_trend_break(current_value)
        seasonal_anomaly = seasonal.is_seasonal_anomaly(current_time, current_value)
        pattern_fatigued = fatigue.is_pattern_fatigued("common_hook")

        # Normal value should not trigger any anomalies
        assert not statistical_anomaly
        assert not trend_break
        assert not seasonal_anomaly
        assert not pattern_fatigued

    def test_extreme_anomaly_multi_model_detection(self):
        """Test that extreme anomalies are caught by multiple models."""
        statistical = StatisticalModel(threshold=1.5)
        trend = TrendModel(trend_threshold=0.3)

        # Set up normal baseline
        now = datetime.now()
        for i in range(24):
            timestamp = now - timedelta(hours=i)
            normal_value = 100.0
            statistical.add_data_point(normal_value)
            trend.add_hourly_data(timestamp, normal_value)

        # Test extreme anomaly
        extreme_value = 20.0  # 80% drop

        statistical_anomaly = statistical.is_anomaly(extreme_value)
        trend_break = trend.detect_trend_break(extreme_value)

        # Extreme anomaly should be caught by both models
        assert statistical_anomaly
        assert trend_break

    def test_edge_case_empty_models(self):
        """Test that empty models handle edge cases gracefully."""
        statistical = StatisticalModel()
        trend = TrendModel()
        seasonal = SeasonalModel()
        fatigue = FatigueModel()

        # All methods should handle empty state gracefully
        assert not statistical.is_anomaly(100.0)
        assert not trend.detect_trend_break(100.0)
        assert not seasonal.is_seasonal_anomaly(datetime.now(), 100.0)
        assert not fatigue.is_pattern_fatigued("any_pattern")

    def test_models_with_extreme_values(self):
        """Test models handle extreme values appropriately."""
        extreme_values = [float("inf"), float("-inf"), 0, -1000000, 1000000]

        # Models should handle extreme values without crashing
        for value in extreme_values:
            if not math.isinf(value):
                # Test with finite extreme values
                statistical = StatisticalModel()
                statistical.add_data_point(100.0)  # Add some normal data first
                try:
                    result = statistical.is_anomaly(value)
                    assert isinstance(result, bool)
                except (ValueError, OverflowError):
                    # Some extreme cases may raise expected exceptions
                    pass
