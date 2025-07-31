from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from services.pattern_analyzer.models import PatternUsage


class PatternFatigueDetector:
    """Detects pattern fatigue based on usage over a rolling 7-day window."""

    def __init__(self, db_session: Optional[Session] = None):
        # Use database if provided, otherwise use in-memory storage
        self.db_session = db_session
        self._use_in_memory = db_session is None
        if self._use_in_memory:
            # In-memory storage as fallback
            # Structure: {(pattern, persona_id): [timestamp1, timestamp2, ...]}
            self._usage_history: Dict[Tuple[str, str], List[datetime]] = defaultdict(
                list
            )
            self._pattern_usage: List[Dict[str, Any]] = []  # For compatibility with get_recent_pattern_usage

    def record_pattern_usage(
        self, pattern: str, persona_id: str, timestamp: datetime
    ) -> None:
        """
        Record that a pattern was used by a persona at a specific time.

        Args:
            pattern: The pattern that was used
            persona_id: The persona that used it
            timestamp: When the pattern was used
        """
        if self.db_session:
            # Use database
            usage = PatternUsage(
                pattern_id=pattern,
                persona_id=persona_id,
                post_id=f"post_{timestamp.timestamp()}",  # Placeholder post_id
                used_at=timestamp,
            )
            self.db_session.add(usage)
            self.db_session.commit()
        else:
            # Use in-memory storage
            key = (pattern, persona_id)
            self._usage_history[key].append(timestamp)
            # Also store in alternate format for get_recent_pattern_usage
            self._pattern_usage.append(
                {"pattern_id": pattern, "persona_id": persona_id, "used_at": timestamp}
            )

    def is_pattern_fatigued(self, pattern: str, persona_id: str) -> bool:
        """
        Check if a pattern is fatigued (used 3+ times in past 7 days).

        Args:
            pattern: The pattern string to check
            persona_id: The persona ID to check against

        Returns:
            True if the pattern is fatigued, False otherwise
        """
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)

        if self.db_session:
            # Query database
            recent_uses = (
                self.db_session.query(PatternUsage)
                .filter(
                    PatternUsage.pattern_id == pattern,
                    PatternUsage.persona_id == persona_id,
                    PatternUsage.used_at > seven_days_ago,
                )
                .count()
            )
        else:
            # Use in-memory storage
            key = (pattern, persona_id)
            if key not in self._usage_history:
                return False

            recent_uses = sum(
                1
                for timestamp in self._usage_history[key]
                if timestamp > seven_days_ago
            )

        return recent_uses >= 3

    def get_freshness_score(self, pattern: str, persona_id: str) -> float:
        """
        Calculate freshness score for a pattern (0.0 to 1.0).

        Unused patterns get 1.0 (novelty bonus).
        Recently used patterns get lower scores.

        Args:
            pattern: The pattern to score
            persona_id: The persona to check against

        Returns:
            Freshness score between 0.0 (heavily used) and 1.0 (never used)
        """
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)

        if self.db_session:
            # Query database
            recent_uses = (
                self.db_session.query(PatternUsage)
                .filter(
                    PatternUsage.pattern_id == pattern,
                    PatternUsage.persona_id == persona_id,
                    PatternUsage.used_at > seven_days_ago,
                )
                .count()
            )
        else:
            # Use in-memory storage
            key = (pattern, persona_id)
            if key not in self._usage_history:
                return 1.0  # Maximum freshness for never-used patterns

            recent_uses = sum(
                1
                for timestamp in self._usage_history[key]
                if timestamp > seven_days_ago
            )

        # Calculate score: 1.0 for 0 uses, 0.0 for 3+ uses
        if recent_uses >= 3:
            return 0.0
        elif recent_uses == 2:
            return 0.25
        elif recent_uses == 1:
            return 0.5
        else:
            return 1.0

    def get_recent_pattern_usage(
        self, persona_id: str, days: int = 7
    ) -> Dict[str, int]:
        """
        Get all patterns used by a persona in the last N days with usage counts.

        Args:
            persona_id: The persona to check
            days: Number of days to look back

        Returns:
            Dictionary mapping patterns to usage counts
        """
        now = datetime.now()
        cutoff_time = now - timedelta(days=days)

        if self.db_session:
            # Database query
            results = (
                self.db_session.query(
                    PatternUsage.pattern_id,
                    func.count(PatternUsage.id).label("usage_count"),
                )
                .filter(
                    PatternUsage.persona_id == persona_id,
                    PatternUsage.used_at >= cutoff_time,
                )
                .group_by(PatternUsage.pattern_id)
                .all()
            )

            return {pattern: count for pattern, count in results}
        else:
            # For in-memory storage, calculate from raw data
            pattern_counts = {}

            for (pattern, pid), timestamps in self._usage_history.items():
                if pid == persona_id:
                    recent_count = sum(1 for ts in timestamps if ts > cutoff_time)
                    if recent_count > 0:
                        pattern_counts[pattern] = recent_count

            return pattern_counts
