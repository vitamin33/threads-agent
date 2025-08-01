from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from services.pattern_analyzer.pattern_fatigue_detector import PatternFatigueDetector
from services.pattern_analyzer.pattern_extractor import PatternExtractor


class PatternAnalyzerService:
    """Main service class for pattern analysis functionality."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize the service with optional database session."""
        self.detector = PatternFatigueDetector(db_session=db_session)
        self.extractor = PatternExtractor()

    def check_pattern_fatigue(self, pattern: str, persona_id: str) -> Dict[str, Any]:
        """
        Check if a pattern is fatigued and get its freshness score.

        Args:
            pattern: The pattern to check
            persona_id: The persona to check against

        Returns:
            Dictionary with fatigue status and freshness score
        """
        is_fatigued = self.detector.is_pattern_fatigued(pattern, persona_id)
        freshness_score = self.detector.get_freshness_score(pattern, persona_id)

        return {
            "pattern": pattern,
            "is_fatigued": is_fatigued,
            "freshness_score": freshness_score,
        }

    def get_pattern_freshness(self, persona_id: str, pattern: str) -> float:
        """
        Get freshness score for a pattern.

        Args:
            persona_id: The persona to check
            pattern: The pattern to check

        Returns:
            Freshness score between 0.0 and 1.0
        """
        return self.detector.get_freshness_score(pattern, persona_id)

    def get_recent_patterns(self, persona_id: str, days: int = 7) -> Dict[str, int]:
        """
        Get recently used patterns for a persona.

        Args:
            persona_id: The persona to check
            days: Number of days to look back

        Returns:
            Dictionary mapping patterns to usage counts
        """
        return self.detector.get_recent_pattern_usage(persona_id, days)
