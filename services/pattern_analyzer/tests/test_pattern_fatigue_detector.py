import time
from datetime import datetime, timedelta

from services.pattern_analyzer.pattern_fatigue_detector import PatternFatigueDetector


class TestPatternFatigueDetector:
    """Test the PatternFatigueDetector class."""

    def test_pattern_not_fatigued_when_used_less_than_threshold(self) -> None:
        """Test that a pattern used fewer than 3 times in 7 days is not fatigued."""
        # Arrange
        detector = PatternFatigueDetector()
        pattern = "Check out this amazing {topic}!"
        persona_id = "test_persona_123"

        # Act
        is_fatigued = detector.is_pattern_fatigued(pattern, persona_id)

        # Assert
        assert is_fatigued is False

    def test_pattern_is_fatigued_when_used_three_times_in_past_week(self) -> None:
        """Test that a pattern used 3 times in past 7 days is fatigued."""
        # Arrange
        detector = PatternFatigueDetector()
        pattern = "Check out this amazing {topic}!"
        persona_id = "test_persona_123"

        # Record 3 uses in the past week
        now = datetime.now()
        detector.record_pattern_usage(pattern, persona_id, now - timedelta(days=6))
        detector.record_pattern_usage(pattern, persona_id, now - timedelta(days=3))
        detector.record_pattern_usage(pattern, persona_id, now - timedelta(days=1))

        # Act
        is_fatigued = detector.is_pattern_fatigued(pattern, persona_id)

        # Assert
        assert is_fatigued is True

    def test_pattern_usage_older_than_7_days_not_counted(self) -> None:
        """Test that pattern uses older than 7 days are not counted toward fatigue."""
        # Arrange
        detector = PatternFatigueDetector()
        pattern = "Check out this amazing {topic}!"
        persona_id = "test_persona_123"

        # Record 3 uses - 2 old, 1 recent
        now = datetime.now()
        detector.record_pattern_usage(
            pattern, persona_id, now - timedelta(days=10)
        )  # Too old
        detector.record_pattern_usage(
            pattern, persona_id, now - timedelta(days=8)
        )  # Too old
        detector.record_pattern_usage(
            pattern, persona_id, now - timedelta(days=1)
        )  # Recent

        # Act
        is_fatigued = detector.is_pattern_fatigued(pattern, persona_id)

        # Assert
        assert is_fatigued is False  # Only 1 recent use, not fatigued

    def test_get_freshness_score_for_unused_pattern(self) -> None:
        """Test that completely unused patterns get a high freshness score (novelty bonus)."""
        # Arrange
        detector = PatternFatigueDetector()
        pattern = "Never used before: {topic}"
        persona_id = "test_persona_123"

        # Act
        freshness_score = detector.get_freshness_score(pattern, persona_id)

        # Assert
        assert freshness_score == 1.0  # Maximum freshness for never-used pattern

    def test_get_freshness_score_decreases_with_usage(self) -> None:
        """Test that freshness score decreases as pattern usage increases."""
        # Arrange
        detector = PatternFatigueDetector()
        pattern = "Check this out: {topic}"
        persona_id = "test_persona_123"
        now = datetime.now()

        # Test with 0 uses
        assert detector.get_freshness_score(pattern, persona_id) == 1.0

        # Test with 1 use
        detector.record_pattern_usage(pattern, persona_id, now - timedelta(days=1))
        assert detector.get_freshness_score(pattern, persona_id) == 0.5

        # Test with 2 uses
        detector.record_pattern_usage(pattern, persona_id, now - timedelta(days=2))
        assert detector.get_freshness_score(pattern, persona_id) == 0.25

        # Test with 3 uses (fatigued)
        detector.record_pattern_usage(pattern, persona_id, now - timedelta(days=3))
        assert detector.get_freshness_score(pattern, persona_id) == 0.0

    def test_fatigue_check_latency_under_100ms(self) -> None:
        """Test that fatigue checking completes in under 100ms even with many patterns."""
        # Arrange
        detector = PatternFatigueDetector()
        persona_id = "test_persona_123"
        now = datetime.now()

        # Add many pattern usages
        for i in range(1000):
            pattern = f"Pattern {i}: {{topic}}"
            for j in range(3):
                detector.record_pattern_usage(
                    pattern, persona_id, now - timedelta(days=j)
                )

        # Act - measure time for fatigue check
        test_pattern = "Pattern 500: {topic}"
        start_time = time.time()
        is_fatigued = detector.is_pattern_fatigued(test_pattern, persona_id)
        end_time = time.time()

        # Assert
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 100, f"Latency {latency_ms:.2f}ms exceeds 100ms limit"
        assert is_fatigued is True  # Should be fatigued with 3 uses
