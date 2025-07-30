"""Test database performance and optimization requirements for CRA-299."""

import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from db.models import Achievement, PRAchievement


class TestDatabasePerformance:
    """Test database query performance meets sub-200ms requirement."""

    def test_achievement_query_by_category_performance(self, db_session):
        """Test that querying achievements by category completes in under 200ms."""
        # Given: A database with many achievements
        for i in range(1000):
            achievement = Achievement(
                title=f"Achievement {i}",
                description=f"Description {i}",
                category="feature" if i % 5 == 0 else "optimization",
                started_at=datetime.now(timezone.utc) - timedelta(days=30),
                completed_at=datetime.now(timezone.utc) - timedelta(days=29),
                duration_hours=8.0,
                source_type="github_pr",
                impact_score=50.0 + (i % 50),
            )
            db_session.add(achievement)
        db_session.commit()

        # When: Querying achievements by category
        start_time = time.time()
        results = (
            db_session.query(Achievement)
            .filter(Achievement.category == "feature")
            .all()
        )
        query_time = (time.time() - start_time) * 1000  # Convert to ms

        # Then: Query should complete in under 200ms
        assert query_time < 200, f"Query took {query_time}ms, expected < 200ms"
        assert len(results) == 200  # 1000 / 5 = 200 feature achievements

    def test_pr_achievement_join_query_performance(self, db_session):
        """Test that joining PR achievements with achievements completes in under 200ms."""
        # Given: Achievements with PR data
        for i in range(500):
            achievement = Achievement(
                title=f"PR Achievement {i}",
                description=f"PR Description {i}",
                category="feature",
                started_at=datetime.now(timezone.utc) - timedelta(days=30),
                completed_at=datetime.now(timezone.utc) - timedelta(days=29),
                duration_hours=8.0,
                source_type="github_pr",
                impact_score=70.0,
            )
            db_session.add(achievement)
            db_session.flush()

            pr_achievement = PRAchievement(
                achievement_id=achievement.id,
                pr_number=1000 + i,
                title=f"PR #{1000 + i}",
                merge_timestamp=datetime.now(timezone.utc) - timedelta(days=i % 30),
                author="test_user",
            )
            db_session.add(pr_achievement)
        db_session.commit()

        # When: Performing a join query
        start_time = time.time()
        results = (
            db_session.query(Achievement, PRAchievement)
            .join(PRAchievement, Achievement.id == PRAchievement.achievement_id)
            .filter(Achievement.impact_score > 60)
            .all()
        )
        query_time = (time.time() - start_time) * 1000

        # Then: Query should complete in under 200ms
        assert query_time < 200, f"Join query took {query_time}ms, expected < 200ms"
        assert len(results) == 500

    def test_date_range_query_performance(self, db_session):
        """Test that querying achievements by date range completes in under 200ms."""
        # Given: Achievements spread across time
        base_date = datetime.now(timezone.utc)
        for i in range(1000):
            achievement = Achievement(
                title=f"Dated Achievement {i}",
                description=f"Description {i}",
                category="optimization",
                started_at=base_date - timedelta(days=i % 365),
                completed_at=base_date - timedelta(days=(i % 365) - 1),
                duration_hours=8.0,
                source_type="git",
                impact_score=40.0,
            )
            db_session.add(achievement)
        db_session.commit()

        # When: Querying by date range
        start_date = base_date - timedelta(days=30)
        end_date = base_date

        start_time = time.time()
        db_session.query(Achievement).filter(
            Achievement.completed_at >= start_date,
            Achievement.completed_at <= end_date,
        ).all()
        query_time = (time.time() - start_time) * 1000

        # Then: Query should complete in under 200ms
        assert query_time < 200, (
            f"Date range query took {query_time}ms, expected < 200ms"
        )

    def test_portfolio_ready_query_performance(self, db_session):
        """Test that querying portfolio-ready achievements completes in under 200ms."""
        # Given: Mix of portfolio-ready and non-ready achievements
        for i in range(1000):
            achievement = Achievement(
                title=f"Portfolio Achievement {i}",
                description=f"Description {i}",
                category="feature",
                started_at=datetime.now(timezone.utc) - timedelta(days=30),
                completed_at=datetime.now(timezone.utc) - timedelta(days=29),
                duration_hours=8.0,
                source_type="github_pr",
                impact_score=60.0,
                portfolio_ready=i % 3 == 0,  # Every 3rd is portfolio ready
                display_priority=100 - (i % 100),
            )
            db_session.add(achievement)
        db_session.commit()

        # When: Querying portfolio-ready achievements ordered by priority
        start_time = time.time()
        results = (
            db_session.query(Achievement)
            .filter(Achievement.portfolio_ready.is_(True))
            .order_by(Achievement.display_priority.desc())
            .limit(50)
            .all()
        )
        query_time = (time.time() - start_time) * 1000

        # Then: Query should complete in under 200ms
        assert query_time < 200, (
            f"Portfolio query took {query_time}ms, expected < 200ms"
        )
        assert len(results) == 50

    def test_index_exists_on_critical_columns(self, db_session):
        """Test that proper indexes exist on performance-critical columns."""
        # When: Checking for indexes
        result = db_session.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='achievements'"
            )
        )
        index_names = [row[0] for row in result]

        # Then: Critical indexes should exist
        expected_indexes = [
            "idx_achievement_category",
            "idx_achievement_impact",
            "idx_achievement_date",
            "idx_achievement_portfolio",
        ]

        for expected_index in expected_indexes:
            assert any(expected_index in index for index in index_names), (
                f"Missing expected index: {expected_index}"
            )
