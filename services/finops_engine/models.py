"""
Database models for FinOps Engine cost attribution system.

Defines the PostCostAnalysis model for storing per-post cost data
with high accuracy and complete audit trail requirements.

Also includes statistical models for anomaly detection.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
import statistics

Base = declarative_base()


class StatisticalModel:
    """
    Basic statistical anomaly detection using z-score calculation.

    Maintains a sliding window of data points and calculates anomaly scores
    based on standard deviation from the mean.
    """

    def __init__(self, window_size: int = 100, threshold: float = 2.0):
        """Initialize with configurable window size and threshold."""
        self.window_size = window_size
        self.threshold = threshold
        self.data_points: List[float] = []

    def add_data_point(self, value: float) -> None:
        """Add a data point, maintaining sliding window."""
        self.data_points.append(value)
        if len(self.data_points) > self.window_size:
            self.data_points.pop(0)

    def calculate_anomaly_score(self, value: float) -> float:
        """Calculate z-score based anomaly score."""
        if len(self.data_points) < 2:
            return 0.0

        try:
            mean = statistics.mean(self.data_points)
            std_dev = statistics.stdev(self.data_points)

            if std_dev == 0:
                return float("inf") if value != mean else 0.0

            z_score = abs(value - mean) / std_dev
            return z_score
        except (statistics.StatisticsError, ZeroDivisionError):
            return 0.0

    def is_anomaly(self, value: float) -> bool:
        """Determine if value is an anomaly based on threshold."""
        score = self.calculate_anomaly_score(value)
        return score > self.threshold

    def get_statistics(self) -> Dict[str, float]:
        """Get basic statistics from current data."""
        if len(self.data_points) < 1:
            return {"mean": 0.0, "std_dev": 0.0, "count": 0}

        mean = statistics.mean(self.data_points)
        std_dev = (
            statistics.stdev(self.data_points) if len(self.data_points) > 1 else 0.0
        )

        return {"mean": mean, "std_dev": std_dev, "count": len(self.data_points)}


class TrendModel:
    """
    Trend-based anomaly detection for engagement metrics.

    Tracks hourly averages and detects significant trend breaks.
    """

    def __init__(self, lookback_hours: int = 24, trend_threshold: float = 0.5):
        """Initialize with configurable lookback period and threshold."""
        self.lookback_hours = lookback_hours
        self.trend_threshold = trend_threshold
        self.hourly_data: List[tuple[datetime, float]] = []

    def add_hourly_data(self, timestamp: datetime, value: float) -> None:
        """Add hourly data point, cleaning up old entries."""
        cutoff_time = datetime.now() - timedelta(hours=self.lookback_hours)

        # Clean up old data
        self.hourly_data = [
            (ts, val) for ts, val in self.hourly_data if ts >= cutoff_time
        ]

        # Add new data point
        self.hourly_data.append((timestamp, value))

    def calculate_baseline(self) -> float:
        """Calculate baseline average from historical data."""
        if len(self.hourly_data) == 0:
            return 0.0

        values = [val for _, val in self.hourly_data]
        return statistics.mean(values)

    def detect_trend_break(self, current_value: float) -> bool:
        """Detect if current value represents a trend break."""
        if len(self.hourly_data) == 0:
            return False

        baseline = self.calculate_baseline()
        if baseline == 0:
            return False

        drop_percentage = (baseline - current_value) / baseline
        return drop_percentage > self.trend_threshold

    def get_trend_metrics(self) -> Dict[str, Any]:
        """Get trend analysis metrics."""
        return {
            "baseline": self.calculate_baseline(),
            "data_points": len(self.hourly_data),
            "lookback_hours": self.lookback_hours,
        }


class SeasonalModel:
    """
    Weekly seasonal pattern detection.

    Tracks weekly patterns and provides seasonal baselines.
    """

    def __init__(self, period_hours: int = 168, anomaly_threshold: float = 0.3):
        """Initialize with configurable period (default 7 days * 24 hours)."""
        self.period_hours = period_hours
        self.anomaly_threshold = anomaly_threshold
        # Initialize array for each hour in the period
        self.seasonal_data: List[List[float]] = [[] for _ in range(period_hours)]

    def add_seasonal_data(self, timestamp: datetime, value: float) -> None:
        """Add data point to appropriate seasonal slot."""
        # Calculate hour index within the period
        if self.period_hours == 168:  # Weekly pattern
            # Get day of week (0=Monday) and hour
            day_of_week = timestamp.weekday()
            hour_of_day = timestamp.hour
            hour_index = day_of_week * 24 + hour_of_day
        else:  # Daily or other pattern
            hour_index = timestamp.hour % self.period_hours

        self.seasonal_data[hour_index].append(value)

    def get_seasonal_baseline(self, timestamp: datetime) -> float:
        """Get seasonal baseline for given timestamp."""
        if self.period_hours == 168:  # Weekly pattern
            day_of_week = timestamp.weekday()
            hour_of_day = timestamp.hour
            hour_index = day_of_week * 24 + hour_of_day
        else:  # Daily or other pattern
            hour_index = timestamp.hour % self.period_hours

        if len(self.seasonal_data[hour_index]) == 0:
            return 0.0

        return statistics.mean(self.seasonal_data[hour_index])

    def is_seasonal_anomaly(self, timestamp: datetime, value: float) -> bool:
        """Detect if value is anomalous for this time period."""
        baseline = self.get_seasonal_baseline(timestamp)
        if baseline == 0:
            return False

        drop_percentage = (baseline - value) / baseline
        return drop_percentage > self.anomaly_threshold

    def get_seasonal_metrics(self) -> Dict[str, Any]:
        """Get seasonal pattern metrics."""
        total_points = sum(len(hour_data) for hour_data in self.seasonal_data)
        hours_with_data = sum(
            1 for hour_data in self.seasonal_data if len(hour_data) > 0
        )

        return {
            "period_hours": self.period_hours,
            "total_data_points": total_points,
            "hours_with_data": hours_with_data,
        }


class FatigueModel:
    """
    Pattern fatigue detection.

    Tracks pattern usage over time and calculates fatigue scores.
    """

    def __init__(
        self,
        decay_factor: float = 0.95,
        fatigue_threshold: float = 0.7,
        max_history_days: int = 30,
    ):
        """Initialize with configurable decay and threshold."""
        self.decay_factor = decay_factor
        self.fatigue_threshold = fatigue_threshold
        self.max_history_days = max_history_days
        self.pattern_usage: Dict[str, List[datetime]] = {}

    def record_pattern_usage(self, pattern_id: str, timestamp: datetime) -> None:
        """Record usage of a pattern."""
        if pattern_id not in self.pattern_usage:
            self.pattern_usage[pattern_id] = []

        self.pattern_usage[pattern_id].append(timestamp)

    def calculate_fatigue_score(self, pattern_id: str) -> float:
        """Calculate fatigue score for a pattern."""
        if (
            pattern_id not in self.pattern_usage
            or len(self.pattern_usage[pattern_id]) == 0
        ):
            return 0.0

        now = datetime.now()
        total_score = 0.0

        for usage_time in self.pattern_usage[pattern_id]:
            hours_ago = (now - usage_time).total_seconds() / 3600
            # Apply exponential decay based on time
            decay_multiplier = self.decay_factor**hours_ago
            total_score += decay_multiplier

        return min(total_score, 1.0)  # Cap at 1.0

    def is_pattern_fatigued(self, pattern_id: str) -> bool:
        """Check if pattern is fatigued."""
        score = self.calculate_fatigue_score(pattern_id)
        return score > self.fatigue_threshold

    def get_fatigue_metrics(self) -> Dict[str, Any]:
        """Get fatigue metrics for all patterns."""
        pattern_scores = {}
        fatigued_count = 0

        for pattern_id in self.pattern_usage.keys():
            score = self.calculate_fatigue_score(pattern_id)
            pattern_scores[pattern_id] = score
            if score > self.fatigue_threshold:
                fatigued_count += 1

        return {
            "total_patterns": len(self.pattern_usage),
            "fatigued_patterns": fatigued_count,
            "pattern_scores": pattern_scores,
        }

    def cleanup_old_usage(self) -> None:
        """Clean up old usage data beyond max_history_days."""
        cutoff_time = datetime.now() - timedelta(days=self.max_history_days)

        for pattern_id in self.pattern_usage:
            self.pattern_usage[pattern_id] = [
                usage_time
                for usage_time in self.pattern_usage[pattern_id]
                if usage_time >= cutoff_time
            ]


class PostCostAnalysis(Base):
    """
    Database model for storing per-post cost attribution data.

    Supports 95% accuracy target with complete audit trail for
    tracking costs from generation through publication.
    """

    __tablename__ = "post_cost_analysis"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core cost attribution fields
    post_id = Column(String(255), nullable=False, index=True)
    cost_type = Column(String(100), nullable=False, index=True)
    cost_amount = Column(Float, nullable=False)

    # Metadata for audit trail and accuracy calculation
    cost_metadata = Column(JSONB, nullable=True)
    accuracy_score = Column(Float, nullable=False, default=0.95)

    # Timestamps for audit trail
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Create composite indexes for performance
    __table_args__ = (
        Index("idx_post_cost_analysis_post_id_created", "post_id", "created_at"),
        Index("idx_post_cost_analysis_cost_type_created", "cost_type", "created_at"),
    )
