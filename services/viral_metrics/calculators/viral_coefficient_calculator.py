"""
Viral Coefficient Calculator - Measures secondary engagement generation.

Formula: (Shares + Comments) / Views * 100
Indicates how much additional engagement each view generates.
"""

from typing import Dict, Any


class ViralCoefficientCalculator:
    """
    Calculates viral coefficient to measure content's ability to generate
    secondary engagement through shares and comments.

    A higher viral coefficient indicates content that spreads organically
    and generates discussions.
    """

    def __init__(self) -> None:
        """Initialize calculator with configuration."""
        self.max_coefficient = 50.0  # Cap at 50% to prevent outliers

    async def calculate(
        self, post_id: str, engagement_data: Dict[str, Any], timeframe: str
    ) -> float:
        """
        Calculate viral coefficient for a post.

        Args:
            post_id: Unique post identifier
            engagement_data: Dictionary containing engagement metrics
            timeframe: Time window for calculation (not used in basic formula)

        Returns:
            Viral coefficient as percentage (0-50)
        """
        views = engagement_data.get("views", 0)
        shares = engagement_data.get("shares", 0)
        comments = engagement_data.get("comments", 0)

        # Avoid division by zero
        if views == 0:
            return 0.0

        # Calculate viral coefficient
        viral_coefficient = ((shares + comments) / views) * 100

        # Cap at reasonable maximum to prevent outliers
        return float(min(viral_coefficient, self.max_coefficient))
