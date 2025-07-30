"""Test database backup and recovery procedures for CRA-299."""

import os
import tempfile
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, Achievement


class TestDatabaseBackup:
    """Test backup and recovery procedures for production data protection."""

    def test_backup_manager_exists(self):
        """Test that we have a backup manager module."""
        from db import backup_manager

        assert hasattr(backup_manager, "BackupManager")

    def test_create_database_backup(self):
        """Test creating a full database backup."""
        from db.backup_manager import BackupManager

        # Given: A database with data
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Setup database with test data
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            Session = sessionmaker(bind=engine)
            session = Session()

            for i in range(5):
                achievement = Achievement(
                    title=f"Achievement {i}",
                    description=f"Description {i}",
                    category="feature",
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    duration_hours=8.0,
                    source_type="github_pr",
                )
                session.add(achievement)
            session.commit()
            session.close()

            # When: Creating backup
            backup_manager = BackupManager(f"sqlite:///{db_path}")
            backup_path = backup_manager.create_backup()

            # Then: Backup should exist and be valid
            assert backup_path is not None
            assert os.path.exists(backup_path)
            assert os.path.getsize(backup_path) > 0

            # Verify backup contains data
            backup_engine = create_engine(f"sqlite:///{backup_path}")
            BackupSession = sessionmaker(bind=backup_engine)
            backup_session = BackupSession()

            backup_count = backup_session.query(Achievement).count()
            assert backup_count == 5

            backup_session.close()

            # Cleanup
            os.unlink(backup_path)
        finally:
            os.unlink(db_path)

    def test_restore_from_backup(self):
        """Test restoring database from backup."""
        from db.backup_manager import BackupManager

        # Given: A backup file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            original_db_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            restore_db_path = f.name

        try:
            # Create original database with data
            engine = create_engine(f"sqlite:///{original_db_path}")
            Base.metadata.create_all(engine)

            Session = sessionmaker(bind=engine)
            session = Session()

            achievement = Achievement(
                title="Original Achievement",
                description="This should be restored",
                category="feature",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_hours=8.0,
                source_type="github_pr",
                impact_score=85.0,
            )
            session.add(achievement)
            session.commit()
            session.close()

            # Create backup
            backup_manager = BackupManager(f"sqlite:///{original_db_path}")
            backup_path = backup_manager.create_backup()

            # When: Restoring to new database
            restore_manager = BackupManager(f"sqlite:///{restore_db_path}")
            success = restore_manager.restore_from_backup(backup_path)

            # Then: Restore should succeed
            assert success is True

            # Verify restored data
            restore_engine = create_engine(f"sqlite:///{restore_db_path}")
            RestoreSession = sessionmaker(bind=restore_engine)
            restore_session = RestoreSession()

            restored_achievement = restore_session.query(Achievement).first()
            assert restored_achievement is not None
            assert restored_achievement.title == "Original Achievement"
            assert restored_achievement.impact_score == 85.0

            restore_session.close()

            # Cleanup
            os.unlink(backup_path)
        finally:
            os.unlink(original_db_path)
            os.unlink(restore_db_path)

    def test_backup_with_compression(self):
        """Test creating compressed backups for storage efficiency."""
        from db.backup_manager import BackupManager

        # Given: A database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            # When: Creating compressed backup
            backup_manager = BackupManager(f"sqlite:///{db_path}")
            backup_path = backup_manager.create_backup(compress=True)

            # Then: Backup should be compressed
            assert backup_path is not None
            assert backup_path.endswith(".gz")
            assert os.path.exists(backup_path)

            # Cleanup
            os.unlink(backup_path)
        finally:
            os.unlink(db_path)

    def test_backup_rotation(self):
        """Test that old backups are rotated to save space."""
        from db.backup_manager import BackupManager

        # Given: A database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            backup_manager = BackupManager(f"sqlite:///{db_path}", max_backups=3)

            # When: Creating more backups than the limit
            backup_paths = []
            for i in range(5):
                backup_path = backup_manager.create_backup()
                backup_paths.append(backup_path)

            # Then: Only the latest backups should exist
            existing_backups = backup_manager.list_backups()
            assert len(existing_backups) == 3

            # First two backups should be deleted
            assert not os.path.exists(backup_paths[0])
            assert not os.path.exists(backup_paths[1])

            # Last three should exist
            assert os.path.exists(backup_paths[2])
            assert os.path.exists(backup_paths[3])
            assert os.path.exists(backup_paths[4])

            # Cleanup
            for path in backup_paths[2:]:
                if os.path.exists(path):
                    os.unlink(path)
        finally:
            os.unlink(db_path)

    def test_backup_metadata(self):
        """Test that backups include metadata for tracking."""
        from db.backup_manager import BackupManager

        # Given: A database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            # When: Creating backup with metadata
            backup_manager = BackupManager(f"sqlite:///{db_path}")
            backup_path = backup_manager.create_backup(
                description="Pre-migration backup"
            )

            # Then: Should be able to retrieve metadata
            metadata = backup_manager.get_backup_metadata(backup_path)
            assert metadata is not None
            assert metadata["description"] == "Pre-migration backup"
            assert "timestamp" in metadata
            assert "size" in metadata
            assert "checksum" in metadata

            # Cleanup
            os.unlink(backup_path)
        finally:
            os.unlink(db_path)
