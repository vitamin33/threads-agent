import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.pattern_analyzer.pattern_fatigue_detector import PatternFatigueDetector
from services.pattern_analyzer.models import PatternUsage, Base


class TestPatternFatigueDetectorWithDB:
    """Test PatternFatigueDetector with database integration."""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_detector_with_database_backend(self, db_session):
        """Test that PatternFatigueDetector can use database for persistence."""
        # Arrange
        detector = PatternFatigueDetector(db_session=db_session)
        pattern = "Check out this amazing {topic}!"
        persona_id = "test_persona_123"
        now = datetime.now()

        # Record uses via detector
        detector.record_pattern_usage(pattern, persona_id, now - timedelta(days=6))
        detector.record_pattern_usage(pattern, persona_id, now - timedelta(days=3))
        detector.record_pattern_usage(pattern, persona_id, now - timedelta(days=1))

        # Act - create new detector instance with same session to test persistence
        new_detector = PatternFatigueDetector(db_session=db_session)
        is_fatigued = new_detector.is_pattern_fatigued(pattern, persona_id)

        # Assert
        assert is_fatigued is True

        # Verify data is in database
        usage_count = (
            db_session.query(PatternUsage)
            .filter(
                PatternUsage.pattern_id == pattern,
                PatternUsage.persona_id == persona_id,
            )
            .count()
        )
        assert usage_count == 3
