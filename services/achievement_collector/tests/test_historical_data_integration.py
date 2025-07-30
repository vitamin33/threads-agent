"""Test historical data integration for CRA-299."""

import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, Achievement, PRAchievement


class TestHistoricalDataIntegration:
    """Test integration of historical PR data into the achievement system."""

    def test_historical_data_importer_exists(self):
        """Test that we have a historical data importer."""
        from db import historical_data_importer

        assert hasattr(historical_data_importer, "HistoricalDataImporter")

    def test_import_historical_pr_data(self):
        """Test importing historical PR data from analysis system."""
        from db.historical_data_importer import (
            HistoricalDataImporter,
        )

        # Given: Historical PR data in expected format
        historical_data = [
            {
                "pr_number": 1234,
                "title": "Add user authentication",
                "description": "Implemented JWT-based authentication",
                "author": "developer1",
                "merged_at": "2024-01-15T10:30:00Z",
                "files_changed": 15,
                "additions": 500,
                "deletions": 100,
                "business_value": {
                    "impact": "high",
                    "description": "Critical security feature",
                    "metrics": {"security_score": 95, "user_impact": "10000+ users"},
                },
                "code_analysis": {
                    "complexity": 45,
                    "test_coverage": 85.5,
                    "patterns": ["authentication", "jwt", "middleware"],
                },
            }
        ]

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Setup database
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            # When: Importing historical data
            importer = HistoricalDataImporter(f"sqlite:///{db_path}")
            result = importer.import_pr_data(historical_data)

            # Then: Data should be imported successfully
            assert result.success is True
            assert result.imported_count == 1
            assert result.failed_count == 0

            # Verify data in database
            Session = sessionmaker(bind=engine)
            session = Session()

            achievement = session.query(Achievement).first()
            assert achievement is not None
            assert achievement.title == "Add user authentication"
            assert achievement.source_type == "github_pr"
            assert achievement.source_id == "1234"

            pr_achievement = session.query(PRAchievement).first()
            assert pr_achievement is not None
            assert pr_achievement.pr_number == 1234

            session.close()
        finally:
            import os

            os.unlink(db_path)

    def test_validate_imported_data_integrity(self):
        """Test that imported data maintains integrity and completeness."""
        from db.historical_data_importer import (
            HistoricalDataImporter,
        )

        # Given: Historical data with various edge cases
        historical_data = [
            {
                "pr_number": 5678,
                "title": "Performance optimization",
                "author": "dev2",
                "merged_at": "2024-02-20T15:45:00Z",
                "files_changed": 8,
                "additions": 200,
                "deletions": 150,
                # Missing some optional fields
            },
            {
                "pr_number": 5679,
                "title": "Bug fix for memory leak",
                "author": "dev3",
                "merged_at": "2024-02-21T09:00:00Z",
                "files_changed": 3,
                "additions": 50,
                "deletions": 30,
                "business_value": {
                    "impact": "medium",
                    "description": "Fixes critical memory leak",
                },
            },
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            # When: Importing and validating
            importer = HistoricalDataImporter(f"sqlite:///{db_path}")
            importer.import_pr_data(historical_data)
            validation_result = importer.validate_imported_data()

            # Then: Validation should pass
            assert validation_result.is_valid is True
            assert validation_result.total_records == 2
            assert len(validation_result.issues) == 0
        finally:
            import os

            os.unlink(db_path)

    def test_import_with_deduplication(self):
        """Test that importing handles duplicates correctly."""
        from db.historical_data_importer import (
            HistoricalDataImporter,
        )

        # Given: Duplicate PR data
        historical_data = [
            {
                "pr_number": 9999,
                "title": "Initial implementation",
                "author": "dev1",
                "merged_at": "2024-03-01T10:00:00Z",
                "files_changed": 5,
                "additions": 100,
                "deletions": 0,
            }
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            importer = HistoricalDataImporter(f"sqlite:///{db_path}")

            # When: Importing the same data twice
            result1 = importer.import_pr_data(historical_data)
            result2 = importer.import_pr_data(historical_data)

            # Then: Second import should skip duplicates
            assert result1.imported_count == 1
            assert result2.imported_count == 0
            assert result2.skipped_count == 1

            # Verify only one record exists
            Session = sessionmaker(bind=engine)
            session = Session()
            pr_count = session.query(PRAchievement).count()
            assert pr_count == 1
            session.close()
        finally:
            import os

            os.unlink(db_path)

    def test_import_progress_tracking(self):
        """Test that import process tracks progress for large datasets."""
        from db.historical_data_importer import (
            HistoricalDataImporter,
        )

        # Given: Large dataset
        historical_data = []
        for i in range(100):
            historical_data.append(
                {
                    "pr_number": 10000 + i,
                    "title": f"PR {i}",
                    "author": f"dev{i % 5}",
                    "merged_at": f"2024-01-{(i % 28) + 1:02d}T10:00:00Z",
                    "files_changed": i % 20 + 1,
                    "additions": i * 10,
                    "deletions": i * 5,
                }
            )

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            # When: Importing with progress callback
            progress_updates = []

            def progress_callback(current, total, message):
                progress_updates.append((current, total, message))

            importer = HistoricalDataImporter(f"sqlite:///{db_path}")
            importer.import_pr_data(
                historical_data, progress_callback=progress_callback
            )

            # Then: Progress should be tracked
            assert len(progress_updates) > 0
            assert progress_updates[-1][0] == 100  # Final progress
            assert progress_updates[-1][1] == 100  # Total count
        finally:
            import os

            os.unlink(db_path)

    def test_import_error_recovery(self):
        """Test that import can recover from errors in individual records."""
        from db.historical_data_importer import (
            HistoricalDataImporter,
        )

        # Given: Mix of valid and invalid data
        historical_data = [
            {
                "pr_number": 8001,
                "title": "Valid PR",
                "author": "dev1",
                "merged_at": "2024-04-01T10:00:00Z",
                "files_changed": 5,
                "additions": 100,
                "deletions": 50,
            },
            {
                # Missing required fields
                "pr_number": 8002,
                "title": "Invalid PR - missing author",
            },
            {
                "pr_number": 8003,
                "title": "Another valid PR",
                "author": "dev2",
                "merged_at": "2024-04-02T11:00:00Z",
                "files_changed": 3,
                "additions": 75,
                "deletions": 25,
            },
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)

            # When: Importing with errors
            importer = HistoricalDataImporter(f"sqlite:///{db_path}")
            result = importer.import_pr_data(historical_data)

            # Then: Should import valid records and track errors
            assert result.imported_count == 2
            assert result.failed_count == 1
            assert len(result.errors) == 1
            assert "8002" in str(result.errors[0])
        finally:
            import os

            os.unlink(db_path)
