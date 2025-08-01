"""
Scroll-Stop Rate Calculator - Measures content's ability to stop scrolling.

Formula: Engaged Views / Total Impressions * 100
Indicates how effectively content captures attention.
"""

from typing import Dict, Any


class ScrollStopRateCalculator:
    """
    Calculates scroll-stop rate to measure how effectively content
    stops users from scrolling past.

    Engaged views are those where users spend >3 seconds viewing the content.
    """

    async def calculate(
        self, post_id: str, engagement_data: Dict[str, Any], timeframe: str
    ) -> float:
        """
        Calculate scroll-stop rate for a post.

        Args:
            post_id: Unique post identifier
            engagement_data: Dictionary containing engagement metrics
            timeframe: Time window for calculation

        Returns:
            Scroll-stop rate as percentage (0-100)
        """
        total_impressions = engagement_data.get("impressions", 0)
        engaged_views = engagement_data.get("engaged_views", 0)

        # Avoid division by zero
        if total_impressions == 0:
            return 0.0

        # Calculate scroll-stop rate
        scroll_stop_rate = (engaged_views / total_impressions) * 100

        # Cap at 100% (in case of data inconsistencies)
        return min(scroll_stop_rate, 100.0)
