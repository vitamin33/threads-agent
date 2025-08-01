"""
Engagement Trajectory Calculator - Measures engagement acceleration/deceleration.

Analyzes trend in engagement rate over time to predict viral potential.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class EngagementTrajectoryCalculator:
    """
    Calculates engagement trajectory to identify if content is gaining
    or losing momentum over time.

    Positive values indicate accelerating engagement.
    Negative values indicate decelerating engagement.
    """

    async def calculate(
        self, post_id: str, engagement_data: Dict[str, Any], timeframe: str
    ) -> float:
        """
        Calculate engagement trajectory for a post.

        Uses linear regression on hourly engagement rates to determine trend.

        Args:
            post_id: Unique post identifier
            engagement_data: Dictionary containing engagement metrics
            timeframe: Time window for calculation

        Returns:
            Trajectory score (-100 to 100), where positive = accelerating
        """
        hourly_breakdown = engagement_data.get("hourly_breakdown", [])

        if len(hourly_breakdown) < 3:
            # Need at least 3 data points for meaningful trajectory
            return 0.0

        # Calculate engagement rate for each hour
        hourly_rates = []
        for hour_data in hourly_breakdown:
            total_engagement = (
                hour_data.get("likes", 0)
                + hour_data.get("comments", 0)
                + hour_data.get("shares", 0)
            )
            views = hour_data.get("views", 1)  # Avoid division by zero
            engagement_rate = total_engagement / views
            hourly_rates.append(engagement_rate)

        # Calculate linear regression slope (trajectory)
        trajectory = self.calculate_trend_slope(hourly_rates)

        # Normalize to -100 to 100 scale
        # Multiply by 1000 to make small slopes more visible
        normalized_trajectory = trajectory * 1000

        # Cap at bounds
        return max(-100.0, min(100.0, normalized_trajectory))

    def calculate_trend_slope(self, values: List[float]) -> float:
        """
        Calculate linear regression slope for trend analysis.

        Args:
            values: List of values to analyze

        Returns:
            Slope of the trend line
        """
        n = len(values)
        if n < 2:
            return 0.0

        # Create x values (hour indices)
        x = list(range(n))

        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        # Calculate slope using least squares
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        return numerator / denominator
