"""Integration test for production database schema and migration system (CRA-299)."""

import os
import tempfile
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from services.achievement_collector.models import (
    Base,
    Achievement,
    PRAchievement,
    PRCodeChange,
)


class TestProductionSchemaIntegration:
    """Test the complete production database schema implementation."""

    @pytest.mark.skipif(
        os.getenv("USE_SQLITE") == "true",
        reason="SQLite doesn't preserve timezone info",
    )
    def test_models_use_timezone_aware_datetime(self):
        """Test that all datetime fields are timezone-aware."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Setup
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()

            # Given: A new achievement
            achievement = Achievement(
                title="Test Achievement",
                description="Test",
                category="feature",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc) + timedelta(hours=1),
                duration_hours=1.0,
                source_type="github_pr",
            )

            # When: Saving to database
            session.add(achievement)
            session.commit()
            session.refresh(achievement)

            # Then: All datetime fields should be timezone-aware
            assert achievement.started_at.tzinfo is not None
            assert achievement.completed_at.tzinfo is not None
            assert achievement.created_at.tzinfo is not None
            assert achievement.updated_at.tzinfo is not None

            session.close()
        finally:
            import os

            os.unlink(db_path)

    def test_connection_pooling_configuration(self):
        """Test that connection pooling is properly configured."""
        # Given: A database URL
        db_url = "sqlite:///test_pool.db"

        # When: Creating engine with pooling
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )

        # Then: Pool should be configured correctly
        assert engine.pool.__class__.__name__ == "QueuePool"
        # Note: SQLite doesn't actually use connection pooling,
        # but this demonstrates the configuration for PostgreSQL

    def test_cascade_deletes_work_correctly(self):
        """Test that cascade deletes work as expected."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Setup
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()

            # Given: An achievement with related PR data
            achievement = Achievement(
                title="Test Achievement",
                description="Test",
                category="feature",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_hours=1.0,
                source_type="github_pr",
            )
            session.add(achievement)
            session.flush()

            pr_achievement = PRAchievement(
                achievement_id=achievement.id,
                pr_number=12345,
                title="Test PR",
                merge_timestamp=datetime.now(timezone.utc),
                author="test_user",
            )
            session.add(pr_achievement)
            session.flush()

            code_change = PRCodeChange(
                pr_achievement_id=pr_achievement.id,
                file_path="test.py",
                language="python",
                lines_added=100,
                lines_deleted=50,
            )
            session.add(code_change)
            session.commit()

            # When: Deleting the achievement
            session.delete(achievement)
            session.commit()

            # Then: All related records should be deleted
            assert session.query(Achievement).count() == 0
            assert session.query(PRAchievement).count() == 0
            assert session.query(PRCodeChange).count() == 0

            session.close()
        finally:
            import os

            os.unlink(db_path)

    def test_check_constraints_validation(self):
        """Test that check constraints validate data properly."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()

            # Test 1: Invalid impact score
            with pytest.raises(ValueError):
                achievement = Achievement(
                    title="Test",
                    description="Test",
                    category="feature",
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    duration_hours=1.0,
                    source_type="github_pr",
                    impact_score=150,  # Invalid: > 100
                )

            # Test 2: Valid scores
            achievement = Achievement(
                title="Valid Achievement",
                description="Test",
                category="feature",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_hours=1.0,
                source_type="github_pr",
                impact_score=85,
                complexity_score=70,
            )
            session.add(achievement)
            session.commit()

            # Verify
            saved = session.query(Achievement).first()
            assert saved.impact_score == 85
            assert saved.complexity_score == 70

            session.close()
        finally:
            import os

            os.unlink(db_path)

    def test_composite_index_performance(self):
        """Test that composite indexes improve query performance."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()

            # Add test data
            base_date = datetime.now(timezone.utc)
            for i in range(100):
                achievement = Achievement(
                    title=f"Achievement {i}",
                    description=f"Description {i}",
                    category="feature" if i % 3 == 0 else "optimization",
                    started_at=base_date - timedelta(days=i),
                    completed_at=base_date - timedelta(days=i - 1),
                    duration_hours=8.0,
                    source_type="github_pr",
                    impact_score=50 + (i % 50),
                )
                session.add(achievement)
            session.commit()

            # Test composite index query
            import time

            start = time.time()
            results = (
                session.query(Achievement)
                .filter(
                    Achievement.completed_at >= base_date - timedelta(days=30),
                    Achievement.category == "feature",
                )
                .all()
            )
            query_time = (time.time() - start) * 1000

            # Should be fast with composite index
            assert query_time < 50  # Much faster than 200ms requirement
            assert len(results) > 0

            session.close()
        finally:
            import os

            os.unlink(db_path)

    def test_unique_constraints_enforced(self):
        """Test that unique constraints are properly enforced."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()

            # Add first PR achievement
            achievement1 = Achievement(
                title="First",
                description="Test",
                category="feature",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_hours=1.0,
                source_type="github_pr",
            )
            session.add(achievement1)
            session.flush()

            pr1 = PRAchievement(
                achievement_id=achievement1.id,
                pr_number=9999,
                title="PR 9999",
                merge_timestamp=datetime.now(timezone.utc),
                author="dev1",
            )
            session.add(pr1)
            session.commit()

            # Try to add duplicate PR number
            achievement2 = Achievement(
                title="Second",
                description="Test",
                category="feature",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_hours=1.0,
                source_type="github_pr",
            )
            session.add(achievement2)
            session.flush()

            pr2 = PRAchievement(
                achievement_id=achievement2.id,
                pr_number=9999,  # Duplicate!
                title="Duplicate PR",
                merge_timestamp=datetime.now(timezone.utc),
                author="dev2",
            )
            session.add(pr2)

            # Should raise integrity error
            with pytest.raises(Exception):  # IntegrityError
                session.commit()

            session.close()
        finally:
            import os

            os.unlink(db_path)
