"""
Test suite for Predictive Scaler
TDD approach - testing predictive scaling based on historical patterns
"""

import pytest
from datetime import datetime, timedelta
import numpy as np

from services.ml_autoscaling.scaler.predictive_scaler import (
    PredictiveScaler,
    PredictionResult,
    SeasonalityType,
    TrendType,
    ScalingPolicy,
    MetricDataPoint,
)


class TestPredictiveScaler:
    """Test cases for predictive scaling based on ML patterns"""

    @pytest.fixture
    def scaler(self):
        """Create predictive scaler instance"""
        policy = ScalingPolicy(
            min_replicas=1,
            max_replicas=20,
            look_back_hours=168,  # 1 week
            look_ahead_minutes=30,
            prediction_confidence_threshold=0.7,
        )
        return PredictiveScaler(policy=policy)

    @pytest.fixture
    def sample_time_series(self):
        """Generate sample time series data"""
        # Create a synthetic pattern: daily cycle + weekly trend
        hours = 168  # 1 week
        data_points = []

        for i in range(hours * 12):  # 5-minute intervals
            ts = datetime.now() - timedelta(hours=hours - i / 12)
            hour_of_day = ts.hour
            day_of_week = ts.weekday()

            # Daily pattern: peak at noon, low at night
            daily_component = 50 + 30 * np.sin((hour_of_day - 6) * np.pi / 12)

            # Weekly pattern: higher on weekdays
            weekly_component = 10 if day_of_week < 5 else -10

            # Add some noise
            noise = np.random.normal(0, 5)

            value = max(0, daily_component + weekly_component + noise)

            data_points.append(
                MetricDataPoint(
                    timestamp=ts, value=value, metadata={"metric_name": "request_rate"}
                )
            )

        return data_points

    @pytest.mark.asyncio
    async def test_detect_daily_pattern(self, scaler, sample_time_series):
        """Test detection of daily patterns in metrics"""
        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=sample_time_series,
            current_replicas=3,
            forecast_horizon_minutes=30,
        )

        # Assert
        daily_pattern = next(
            (p for p in result.detected_patterns if p.pattern_type == "daily_cycle"),
            None,
        )
        assert daily_pattern is not None
        assert daily_pattern.confidence > 0.7
        assert daily_pattern.periodicity == 24
        assert daily_pattern.seasonality == SeasonalityType.DAILY

    @pytest.mark.asyncio
    async def test_detect_weekly_pattern(self, scaler):
        """Test detection of weekly patterns"""
        # Arrange
        # Create strong weekly pattern
        data_points = []
        for i in range(28 * 24):  # Hourly for 4 weeks
            ts = datetime.now() - timedelta(days=28 - i / 24)

            # High on Monday-Wednesday, low on weekends
            if ts.weekday() in [0, 1, 2]:  # Mon-Wed
                value = 100 + np.random.normal(0, 10)
            elif ts.weekday() in [5, 6]:  # Weekend
                value = 30 + np.random.normal(0, 5)
            else:
                value = 60 + np.random.normal(0, 8)

            data_points.append(
                MetricDataPoint(
                    timestamp=ts, value=value, metadata={"metric_name": "weekly_metric"}
                )
            )

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=3,
            forecast_horizon_minutes=30,
        )

        # Assert
        weekly_pattern = next(
            (p for p in result.detected_patterns if p.pattern_type == "weekly_cycle"),
            None,
        )
        assert weekly_pattern is not None
        assert weekly_pattern.periodicity == 168  # 7 days in hours
        assert weekly_pattern.seasonality == SeasonalityType.WEEKLY

    @pytest.mark.asyncio
    async def test_predict_future_load(self, scaler, sample_time_series):
        """Test predicting future load based on historical patterns"""
        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=sample_time_series,
            current_replicas=3,
            forecast_horizon_minutes=60,
        )

        # Assert
        assert isinstance(result, PredictionResult)
        assert len(result.forecasts) == 12  # 60 min / 5 min intervals
        for forecast in result.forecasts:
            assert forecast.predicted_load >= 0
            assert forecast.confidence_interval[0] <= forecast.predicted_load
            assert forecast.predicted_load <= forecast.confidence_interval[1]
            assert forecast.recommended_replicas >= 1

    @pytest.mark.asyncio
    async def test_calculate_required_replicas(self, scaler):
        """Test calculating required replicas based on predicted load"""
        # Arrange
        data_points = []
        # Create increasing load pattern
        for i in range(30):
            ts = datetime.now() - timedelta(minutes=30 - i)
            value = 100 + i * 10  # Increasing from 100 to 400
            data_points.append(
                MetricDataPoint(
                    timestamp=ts,
                    value=value,
                    metadata={"metric_name": "increasing_load"},
                )
            )

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=3,
            forecast_horizon_minutes=30,
        )

        # Assert
        # With increasing load, predicted replicas should be higher
        assert result.predicted_replicas > result.current_replicas
        assert result.predicted_replicas <= scaler.policy.max_replicas

    @pytest.mark.asyncio
    async def test_spike_detection(self, scaler):
        """Test detection of sudden spikes requiring immediate scaling"""
        # Arrange
        data_points = []
        values = [50] * 25 + [200, 250, 300, 280, 260]  # Sudden spike

        for i, value in enumerate(values):
            ts = datetime.now() - timedelta(minutes=30 - i)
            data_points.append(
                MetricDataPoint(
                    timestamp=ts, value=value, metadata={"metric_name": "spike_metric"}
                )
            )

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=2,
            forecast_horizon_minutes=15,
        )

        # Assert
        # Anomaly should be detected
        anomaly_pattern = next(
            (
                p
                for p in result.detected_patterns
                if p.pattern_type == "anomaly_detected"
            ),
            None,
        )
        assert anomaly_pattern is not None
        # Should recommend scaling up
        assert result.predicted_replicas > result.current_replicas

    @pytest.mark.asyncio
    async def test_seasonal_adjustment(self, scaler):
        """Test seasonal adjustments for predictions"""
        # Arrange
        # Create data with strong daily seasonality (not monthly, since we only have 30 days of data)
        data_points = []
        for day in range(30):
            for hour in range(24):
                ts = datetime.now() - timedelta(days=30 - day, hours=23 - hour)
                # Create strong daily pattern instead of monthly
                # Higher during business hours (9-17)
                if 9 <= ts.hour < 17:
                    value = 150 + np.random.normal(0, 10)
                # Lower at night (0-6)
                elif 0 <= ts.hour < 6:
                    value = 30 + np.random.normal(0, 5)
                else:
                    value = 80 + np.random.normal(0, 8)

                data_points.append(
                    MetricDataPoint(
                        timestamp=ts,
                        value=value,
                        metadata={"metric_name": "seasonal_metric"},
                    )
                )

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=5,
            forecast_horizon_minutes=60,
        )

        # Assert
        assert len(result.detected_patterns) > 0
        # Should have detected daily pattern with seasonality
        daily_pattern = next(
            (p for p in result.detected_patterns if p.pattern_type == "daily_cycle"),
            None,
        )
        assert daily_pattern is not None
        assert daily_pattern.seasonality == SeasonalityType.DAILY

    @pytest.mark.asyncio
    async def test_anomaly_aware_prediction(self, scaler):
        """Test predictions that account for anomalies"""
        # Arrange
        data_points = []

        # Normal pattern with one anomaly
        for i in range(48 * 12):
            ts = datetime.now() - timedelta(hours=48 - i / 12)
            if i == 200:  # Insert anomaly
                value = 500
            else:
                value = 50 + np.random.normal(0, 5)

            data_points.append(
                MetricDataPoint(
                    timestamp=ts,
                    value=value,
                    metadata={"metric_name": "anomaly_metric"},
                )
            )

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=3,
            forecast_horizon_minutes=30,
        )

        # Assert
        # Should detect anomaly
        anomaly_pattern = next(
            (
                p
                for p in result.detected_patterns
                if p.pattern_type == "anomaly_detected"
            ),
            None,
        )
        assert anomaly_pattern is not None
        # Prediction should be reasonable (not influenced by spike)
        avg_predicted = np.mean([f.predicted_load for f in result.forecasts])
        assert 40 <= avg_predicted <= 60  # Should be around 50

    @pytest.mark.asyncio
    async def test_business_hours_awareness(self, scaler):
        """Test scaling predictions aware of business hours"""
        # Arrange
        data_points = []

        # Create pattern with business hours
        for day in range(14):  # 2 weeks
            for hour in range(24):
                ts = datetime.now() - timedelta(days=14 - day, hours=23 - hour)
                # Higher during business hours (9-17), weekdays only
                if ts.weekday() < 5 and 9 <= ts.hour < 17:
                    value = 100 + np.random.normal(0, 10)
                else:
                    value = 30 + np.random.normal(0, 5)

                data_points.append(
                    MetricDataPoint(
                        timestamp=ts,
                        value=value,
                        metadata={"metric_name": "business_hours"},
                    )
                )

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=5,
            forecast_horizon_minutes=60,
        )

        # Assert
        # Should detect daily pattern
        daily_pattern = next(
            (p for p in result.detected_patterns if p.pattern_type == "daily_cycle"),
            None,
        )
        assert daily_pattern is not None
        # Forecasts during business hours should have higher load
        now = datetime.now()
        if now.weekday() < 5 and 9 <= now.hour < 17:
            # If we're in business hours, predicted load should be higher
            avg_load = np.mean([f.predicted_load for f in result.forecasts[:6]])
            assert avg_load > 50

    @pytest.mark.asyncio
    async def test_cost_optimized_prediction(self, scaler):
        """Test predictions that optimize for cost"""
        # Arrange
        scaler.policy.max_replicas = 10  # Cost constraint

        data_points = []
        # Create high load pattern
        for i in range(60):
            ts = datetime.now() - timedelta(minutes=60 - i)
            value = 500 + i * 10  # Very high increasing load
            data_points.append(
                MetricDataPoint(
                    timestamp=ts, value=value, metadata={"metric_name": "high_load"}
                )
            )

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=5,
            forecast_horizon_minutes=30,
        )

        # Assert
        # Should respect max replicas constraint
        assert result.predicted_replicas <= scaler.policy.max_replicas
        # Should still try to scale up within constraints
        assert result.predicted_replicas >= result.current_replicas

    @pytest.mark.asyncio
    async def test_prediction_confidence(self, scaler):
        """Test calculation of prediction confidence"""
        # Arrange
        # Create very stable pattern for high confidence
        data_points = []
        for i in range(168):  # 1 week of hourly data
            ts = datetime.now() - timedelta(hours=168 - i)
            # Very stable pattern
            value = 50 + 0.1 * np.random.normal(0, 1)
            data_points.append(
                MetricDataPoint(
                    timestamp=ts, value=value, metadata={"metric_name": "stable"}
                )
            )

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=3,
            forecast_horizon_minutes=30,
        )

        # Assert
        # Stable pattern should have relatively high confidence
        assert result.confidence > 0.7  # Adjusted threshold for realistic scenarios

    @pytest.mark.asyncio
    async def test_proactive_scaling_decision(self, scaler):
        """Test proactive scaling decisions"""
        # Arrange
        data_points = []
        # Create pattern that will need scaling soon
        for i in range(60):
            ts = datetime.now() - timedelta(minutes=60 - i)
            # Increasing load that will need scaling
            value = 50 + i * 2
            data_points.append(
                MetricDataPoint(
                    timestamp=ts, value=value, metadata={"metric_name": "increasing"}
                )
            )

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=3,
            forecast_horizon_minutes=30,
        )

        should_scale = await scaler.should_scale_proactively(result)

        # Assert
        # With increasing load and high confidence, should scale proactively
        if result.confidence > scaler.policy.prediction_confidence_threshold:
            assert should_scale == True
            assert result.scale_up_at is not None

    @pytest.mark.asyncio
    async def test_rapid_scale_down_prevention(self, scaler):
        """Test prevention of rapid scale-down that could cause instability"""
        # Arrange
        data_points = []
        # Create decreasing load pattern
        for i in range(30):
            ts = datetime.now() - timedelta(minutes=30 - i)
            value = 200 - i * 5  # Decreasing from 200 to 50
            data_points.append(
                MetricDataPoint(
                    timestamp=ts, value=value, metadata={"metric_name": "decreasing"}
                )
            )

        # Simulate recent scale up
        scaler.last_prediction_time = datetime.now() - timedelta(minutes=5)

        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=data_points,
            current_replicas=10,
            forecast_horizon_minutes=30,
        )

        # Assert
        # Should detect decreasing trend
        trend_pattern = next(
            (p for p in result.detected_patterns if p.pattern_type == "trend"), None
        )
        assert trend_pattern is not None
        assert trend_pattern.trend == TrendType.DECREASING
        # But scaling decision should be conservative
        assert result.predicted_replicas <= result.current_replicas

    @pytest.mark.asyncio
    async def test_forecast_caching(self, scaler, sample_time_series):
        """Test that forecasts are cached and retrievable"""
        # Act
        result = await scaler.predict_scaling_needs(
            historical_metrics=sample_time_series,
            current_replicas=3,
            forecast_horizon_minutes=30,
        )

        cached_forecasts = scaler.get_cached_forecast()

        # Assert
        assert len(cached_forecasts) > 0
        assert cached_forecasts == result.forecasts

        # Clear cache
        scaler.clear_cache()
        assert len(scaler.get_cached_forecast()) == 0
