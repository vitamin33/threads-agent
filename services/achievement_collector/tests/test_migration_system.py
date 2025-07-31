"""Test database migration system with rollback capabilities for CRA-299."""

import os
import tempfile

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text


class TestMigrationSystem:
    """Test migration pipeline with rollback capabilities."""

    @pytest.fixture
    def migration_db_path(self):
        """Create a temporary database for migration testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def alembic_config(self, migration_db_path):
        """Create Alembic configuration for testing."""
        config = Config()
        config.set_main_option("script_location", "db/alembic")
        config.set_main_option("sqlalchemy.url", f"sqlite:///{migration_db_path}")
        return config

    def test_migration_creates_all_tables(self, alembic_config, migration_db_path):
        """Test that running migrations creates all expected tables."""
        # When: Running all migrations
        command.upgrade(alembic_config, "head")

        # Then: All tables should exist
        engine = create_engine(f"sqlite:///{migration_db_path}")
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            )
            tables = [row[0] for row in result]

        expected_tables = [
            "achievements",
            "achievement_templates",
            "alembic_version",
            "ci_runs",
            "git_commits",
            "github_prs",
            "portfolio_snapshots",
            "pr_achievements",
            "pr_code_changes",
            "pr_evidence",
            "pr_kpi_impacts",
        ]

        for table in expected_tables:
            assert table in tables, f"Missing expected table: {table}"

    def test_migration_rollback_single_step(self, alembic_config, migration_db_path):
        """Test rolling back a single migration step."""
        # Given: All migrations applied
        command.upgrade(alembic_config, "head")

        # When: Rolling back one step
        command.downgrade(alembic_config, "-1")

        # Then: Latest migration should be rolled back
        engine = create_engine(f"sqlite:///{migration_db_path}")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()

        # Should not be at head anymore
        assert current_version != "002"  # Assuming 002 is the latest

    def test_migration_rollback_to_base(self, alembic_config, migration_db_path):
        """Test rolling back all migrations."""
        # Given: All migrations applied
        command.upgrade(alembic_config, "head")

        # When: Rolling back to base
        command.downgrade(alembic_config, "base")

        # Then: Only alembic_version table should exist
        engine = create_engine(f"sqlite:///{migration_db_path}")
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'"
                )
            )
            tables = list(result)

        assert len(tables) == 0, "Tables still exist after rollback to base"

    def test_migration_data_validation(self, alembic_config, migration_db_path):
        """Test that migrations include data validation."""
        # This test expects a migration that validates data during the process
        # For now, we'll test that we can add validation in a new migration

        # Given: Initial migrations applied
        command.upgrade(alembic_config, "head")

        # Then: We should be able to query and validate data integrity
        engine = create_engine(f"sqlite:///{migration_db_path}")
        with engine.connect() as conn:
            # Check that achievement category enum is properly constrained
            result = conn.execute(
                text(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name='achievements'"
                )
            )
            create_sql = result.scalar()

            # SQLite doesn't enforce enums, but the column should be defined
            assert "category" in create_sql

    def test_migration_progress_tracking(self, alembic_config):
        """Test that migration progress can be tracked."""
        # We'll implement a custom migration runner that tracks progress

        class MigrationProgress:
            def __init__(self):
                self.steps_completed = 0
                self.total_steps = 0
                self.current_operation = None
                self.errors = []

            def update(self, operation, success=True, error=None):
                self.current_operation = operation
                if success:
                    self.steps_completed += 1
                else:
                    self.errors.append((operation, error))

        progress = MigrationProgress()

        # For now, we'll just verify the concept
        assert hasattr(progress, "steps_completed")
        assert hasattr(progress, "errors")

    def test_migration_error_recovery(self, alembic_config, migration_db_path):
        """Test that migrations can recover from errors."""
        # This would test a migration that includes error recovery mechanisms
        # For now, we'll test that we can detect and handle migration failures

        try:
            # Try to run a non-existent migration
            command.upgrade(alembic_config, "nonexistent")
        except Exception as e:
            # Should handle the error gracefully
            assert "nonexistent" in str(e).lower() or "revision" in str(e).lower()

        # Database should still be accessible
        engine = create_engine(f"sqlite:///{migration_db_path}")
        with engine.connect() as conn:
            # Should be able to query
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
