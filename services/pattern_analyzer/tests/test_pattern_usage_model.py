import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.pattern_analyzer.models import PatternUsage, Base


class TestPatternUsageModel:
    """Test the PatternUsage database model."""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_create_pattern_usage_record(self, db_session):
        """Test creating a pattern usage record."""
        # Arrange
        pattern = "Check out this {topic}!"
        persona_id = "test_persona_123"
        used_at = datetime.now()

        # Act
        usage = PatternUsage(
            pattern_id=pattern,
            persona_id=persona_id,
            post_id="test_post_123",
            used_at=used_at
        )
        db_session.add(usage)
        db_session.commit()

        # Assert
        saved_usage = db_session.query(PatternUsage).first()
        assert saved_usage is not None
        assert saved_usage.pattern_id == pattern
        assert saved_usage.persona_id == persona_id
        assert saved_usage.post_id == "test_post_123"
        assert saved_usage.used_at == used_at

    def test_query_pattern_usage_in_time_window(self, db_session):
        """Test querying pattern usage within a specific time window."""
        # Arrange
        from datetime import timedelta

        pattern = "Check out this {topic}!"
        persona_id = "test_persona_123"
        now = datetime.now()

        # Add usage records at different times
        for days_ago in [10, 8, 6, 4, 2, 0]:
            usage = PatternUsage(
                pattern_id=pattern,
                persona_id=persona_id,
                post_id=f"post_{days_ago}",
                used_at=now - timedelta(days=days_ago),
            )
            db_session.add(usage)

        db_session.commit()

        # Act - query for uses in last 7 days
        seven_days_ago = now - timedelta(days=7)
        recent_uses = (
            db_session.query(PatternUsage)
            .filter(
                PatternUsage.pattern_id == pattern,
                PatternUsage.persona_id == persona_id,
                PatternUsage.used_at > seven_days_ago,
            )
            .all()
        )

        # Assert
        assert len(recent_uses) == 4  # Days 0, 2, 4, and 6
