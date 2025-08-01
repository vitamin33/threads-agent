import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.pattern_analyzer.pattern_fatigue_detector import PatternFatigueDetector
from services.pattern_analyzer.pattern_extractor import PatternExtractor
from services.pattern_analyzer.models import PatternUsage, Base


class TestPatternAnalyzerIntegration:
    """Integration tests for the pattern analyzer service."""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_full_pattern_analysis_workflow(self, db_session):
        """Test the complete workflow: extract pattern, track usage, detect fatigue."""
        # Arrange
        extractor = PatternExtractor()
        detector = PatternFatigueDetector(db_session=db_session)
        persona_id = "viral_tech_tips"

        # Simulate content generation over time
        posts = [
            (
                "Just discovered this incredible Python library for data analysis!",
                datetime.now() - timedelta(days=6),
            ),
            (
                "Just discovered this incredible JavaScript framework for web development!",
                datetime.now() - timedelta(days=4),
            ),
            (
                "Just discovered this incredible Rust tool for systems programming!",
                datetime.now() - timedelta(days=2),
            ),
        ]

        # Act - Process each post
        for content, timestamp in posts:
            # Extract pattern
            pattern = extractor.extract_pattern(content)
            assert pattern is not None

            # Record usage
            detector.record_pattern_usage(pattern, persona_id, timestamp)

        # Check if pattern is fatigued after 3 uses
        pattern = (
            "Just discovered this incredible {language} {tool_type} for {purpose}!"
        )
        is_fatigued = detector.is_pattern_fatigued(pattern, persona_id)
        freshness_score = detector.get_freshness_score(pattern, persona_id)

        # Assert
        assert is_fatigued is True
        assert freshness_score == 0.0

        # Verify database state
        usage_count = (
            db_session.query(PatternUsage)
            .filter(PatternUsage.persona_id == persona_id)
            .count()
        )
        assert usage_count == 3

    def test_pattern_freshness_affects_selection(self, db_session):
        """Test that freshness scores can be used to weight pattern selection."""
        # Arrange
        detector = PatternFatigueDetector(db_session=db_session)
        persona_id = "viral_tech_tips"

        patterns = [
            "Check out this amazing {topic}!",
            "Just discovered {topic} - mind blown!",
            "You won't believe what {topic} can do!",
            "Here's why {topic} is revolutionary:",
        ]

        # Record different usage levels
        now = datetime.now()
        # Pattern 0: Used 3 times (fatigued)
        for i in range(3):
            detector.record_pattern_usage(
                patterns[0], persona_id, now - timedelta(days=i)
            )

        # Pattern 1: Used 2 times
        for i in range(2):
            detector.record_pattern_usage(
                patterns[1], persona_id, now - timedelta(days=i)
            )

        # Pattern 2: Used 1 time
        detector.record_pattern_usage(patterns[2], persona_id, now - timedelta(days=1))

        # Pattern 3: Never used

        # Act - Get freshness scores
        scores = [detector.get_freshness_score(p, persona_id) for p in patterns]

        # Assert
        assert scores[0] == 0.0  # Fatigued
        assert scores[1] == 0.25  # Used twice
        assert scores[2] == 0.5  # Used once
        assert scores[3] == 1.0  # Never used (novelty bonus)

        # Verify patterns are correctly identified as fatigued/fresh
        assert detector.is_pattern_fatigued(patterns[0], persona_id) is True
        assert detector.is_pattern_fatigued(patterns[1], persona_id) is False
        assert detector.is_pattern_fatigued(patterns[2], persona_id) is False
        assert detector.is_pattern_fatigued(patterns[3], persona_id) is False
