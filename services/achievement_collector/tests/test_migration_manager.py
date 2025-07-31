"""Test migration manager for production database schema CRA-299."""

import os
import tempfile
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, Achievement


class TestMigrationManager:
    """Test the migration manager for production requirements."""

    def test_migration_manager_exists(self):
        """Test that we have a migration manager module."""
        from db import migration_manager

        assert hasattr(migration_manager, "MigrationManager")

    def test_migration_manager_can_validate_schema(self):
        """Test that migration manager can validate database schema."""
        from db.migration_manager import MigrationManager

        # Given: A migration manager
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            manager = MigrationManager(f"sqlite:///{db_path}")

            # When: Validating schema
            is_valid, errors = manager.validate_schema()

            # Then: Should return validation results
            assert isinstance(is_valid, bool)
            assert isinstance(errors, list)
        finally:
            os.unlink(db_path)

    def test_migration_manager_tracks_progress(self):
        """Test that migration manager tracks migration progress."""
        from db.migration_manager import MigrationManager

        # Given: A migration manager
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            manager = MigrationManager(f"sqlite:///{db_path}")

            # When: Running migrations
            progress = manager.run_migrations_with_progress()

            # Then: Should track progress
            assert hasattr(progress, "total_steps")
            assert hasattr(progress, "completed_steps")
            assert hasattr(progress, "current_operation")
            assert hasattr(progress, "errors")
        finally:
            os.unlink(db_path)

    def test_migration_manager_supports_rollback(self):
        """Test that migration manager supports rollback operations."""
        from db.migration_manager import MigrationManager

        # Given: A migration manager with applied migrations
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            manager = MigrationManager(f"sqlite:///{db_path}")
            manager.run_migrations_with_progress()

            # When: Rolling back
            success = manager.rollback_migration("001_add_pr_achievement_tables")

            # Then: Should successfully rollback
            assert success is True
        finally:
            os.unlink(db_path)

    def test_migration_manager_creates_backup(self):
        """Test that migration manager creates database backup before migrations."""
        from db.migration_manager import MigrationManager

        # Given: A migration manager
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            manager = MigrationManager(f"sqlite:///{db_path}")

            # When: Creating backup
            backup_path = manager.create_backup()

            # Then: Backup should exist
            assert backup_path is not None
            assert os.path.exists(backup_path)

            # Cleanup backup
            if os.path.exists(backup_path):
                os.unlink(backup_path)
        finally:
            os.unlink(db_path)

    def test_migration_manager_validates_data_integrity(self):
        """Test that migration manager validates data integrity after migration."""
        from db.migration_manager import MigrationManager

        # Given: A database with data
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            # Add test data
            Session = sessionmaker(bind=engine)
            session = Session()

            achievement = Achievement(
                title="Test Achievement",
                description="Test Description",
                category="feature",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_hours=8.0,
                source_type="github_pr",
            )
            session.add(achievement)
            session.commit()
            session.close()

            # When: Running validation
            manager = MigrationManager(f"sqlite:///{db_path}")
            is_valid, report = manager.validate_data_integrity()

            # Then: Should validate successfully
            assert is_valid is True
            assert "achievements" in report
            assert report["achievements"]["count"] == 1
        finally:
            os.unlink(db_path)

    def test_migration_manager_handles_connection_pooling(self):
        """Test that migration manager properly configures connection pooling."""
        from db.migration_manager import MigrationManager

        # Given: A migration manager
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            manager = MigrationManager(
                f"sqlite:///{db_path}", pool_size=10, max_overflow=20
            )

            # Then: Should have proper pool configuration
            assert manager.engine.pool.size() == 10
            assert manager.engine.pool.overflow() == -10  # SQLite doesn't use overflow
        finally:
            os.unlink(db_path)
