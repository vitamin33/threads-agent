"""
Share Velocity Calculator - Measures speed of content spread.

Calculates peak sharing rate to identify viral momentum.
"""

from typing import Dict, Any


class ShareVelocityCalculator:
    """
    Calculates share velocity to measure how quickly content spreads.

    Uses peak hour sharing rate as the primary metric, with fallback
    to average shares per hour.
    """

    async def calculate(
        self, post_id: str, engagement_data: Dict[str, Any], timeframe: str
    ) -> float:
        """
        Calculate share velocity for a post.

        Args:
            post_id: Unique post identifier
            engagement_data: Dictionary containing engagement metrics
            timeframe: Time window for calculation

        Returns:
            Share velocity as shares per hour during peak period
        """
        hourly_breakdown = engagement_data.get("hourly_breakdown", [])

        if not hourly_breakdown:
            # Fallback: calculate simple shares per timeframe
            shares = engagement_data.get("shares", 0)
            hours = self.parse_timeframe_hours(timeframe)
            return float(shares / max(hours, 1))

        # Find peak sharing hour
        max_shares_per_hour = 0
        for hour_data in hourly_breakdown:
            shares_in_hour = hour_data.get("shares", 0)
            max_shares_per_hour = max(max_shares_per_hour, shares_in_hour)

        return float(max_shares_per_hour)

    def parse_timeframe_hours(self, timeframe: str) -> int:
        """
        Parse timeframe string to hours.

        Supports formats: "1h", "24h", "1d", "7d"
        """
        try:
            if timeframe.endswith("h"):
                return int(timeframe[:-1])
            elif timeframe.endswith("d"):
                return int(timeframe[:-1]) * 24
            else:
                return 1  # Default to 1 hour
        except (ValueError, AttributeError):
            return 1  # Default to 1 hour for invalid formats
