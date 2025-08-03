"""
Pattern Fatigue Calculator - Measures content pattern overuse.

Tracks how often similar patterns are used to prevent audience fatigue.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PatternFatigueCalculator:
    """
    Calculates pattern fatigue score to prevent overuse of content patterns.

    Score ranges from 0.0 (fresh) to 1.0 (highly fatigued).
    """

    def __init__(self) -> None:
        """Initialize with decay configuration."""
        self.decay_factor = 0.95  # How quickly fatigue decays
        self.lookback_days = 7  # How far back to check pattern usage
        self.usage_threshold = 3  # Uses per week before fatigue sets in

    async def calculate(
        self, post_id: str, engagement_data: Dict[str, Any], timeframe: str
    ) -> float:
        """
        Calculate pattern fatigue score for a post.

        Args:
            post_id: Unique post identifier
            engagement_data: Dictionary containing engagement metrics
            timeframe: Time window for calculation

        Returns:
            Fatigue score (0.0 = fresh, 1.0 = highly fatigued)
        """
        # Get pattern ID from engagement data
        pattern_id = engagement_data.get("pattern_id")

        if not pattern_id:
            # No pattern identified, assume fresh
            return 0.0

        # In production, this would query the database for pattern usage history
        # For now, we'll simulate based on pattern characteristics
        pattern_usage_count = await self._get_pattern_usage_count(pattern_id)

        # Calculate base fatigue score
        if pattern_usage_count <= self.usage_threshold:
            base_fatigue = 0.0
        else:
            # Linear increase in fatigue after threshold
            excess_usage = pattern_usage_count - self.usage_threshold
            base_fatigue = min(excess_usage * 0.2, 1.0)  # 20% fatigue per excess use

        # Apply decay factor based on time since last use
        days_since_last_use = await self._get_days_since_last_use(pattern_id)
        decay_multiplier = self.decay_factor**days_since_last_use

        # Calculate final fatigue score
        fatigue_score = base_fatigue * decay_multiplier

        return min(max(fatigue_score, 0.0), 1.0)  # Ensure 0-1 range

    async def _get_pattern_usage_count(self, pattern_id: str) -> int:
        """
        Get pattern usage count in the lookback period.

        In production, this would query the database.
        """
        # Simulate pattern usage based on pattern ID hash
        # This is a placeholder for actual database query
        hash_value = hash(pattern_id) % 10
        return hash_value

    async def _get_days_since_last_use(self, pattern_id: str) -> int:
        """
        Get days since pattern was last used.

        In production, this would query the database.
        """
        # Simulate days since last use
        # This is a placeholder for actual database query
        hash_value = hash(pattern_id) % 7
        return hash_value
