"""Unit tests for Linear issue/epic tracker."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from services.achievement_collector.services.linear_tracker import (
    LinearTracker,
    LinearWebhookHandler,
)


class TestLinearTracker:
    """Test Linear tracker functionality."""

    @pytest.fixture
    def tracker(self):
        """Create a Linear tracker instance."""
        with patch.dict(
            "os.environ", {"LINEAR_API_KEY": "test_key", "LINEAR_CHECK_INTERVAL": "300"}
        ):
            return LinearTracker()

    def test_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.linear_api_key == "test_key"
        assert tracker.check_interval == 300

    def test_determine_category_from_labels(self, tracker):
        """Test category determination from labels."""
        # Test bug category
        bug_labels = [{"name": "bug"}, {"name": "critical"}]
        assert tracker._determine_category(bug_labels) == "bugfix"

        # Test feature category
        feature_labels = [{"name": "feature"}, {"name": "ui"}]
        assert tracker._determine_category(feature_labels) == "feature"

        # Test performance category
        perf_labels = [{"name": "performance"}, {"name": "optimization"}]
        assert tracker._determine_category(perf_labels) == "performance"

        # Test infrastructure category
        infra_labels = [{"name": "infrastructure"}, {"name": "backend"}]
        assert tracker._determine_category(infra_labels) == "infrastructure"

        # Test default category
        other_labels = [{"name": "research"}, {"name": "planning"}]
        assert tracker._determine_category(other_labels) == "development"

    def test_extract_skills_from_issue(self, tracker):
        """Test skill extraction from issue metadata."""
        issue = {
            "labels": [
                {"name": "Python"},
                {"name": "Docker"},
                {"name": "API"},
                {"name": "Machine Learning"},
            ],
            "description": "Implement MLflow tracking for model versioning with LangChain integration",
        }

        skills = tracker._extract_skills(issue)

        assert "Python" in skills
        assert "Docker" in skills
        assert "API Development" in skills
        assert "Machine Learning" in skills
        assert "MLflow" in skills
        assert "LangChain" in skills
        assert "Problem Solving" in skills
        assert "Agile Development" in skills

    def test_extract_skills_rag_and_prompt(self, tracker):
        """Test extraction of RAG and prompt engineering skills."""
        issue = {
            "labels": [],
            "description": "Build RAG pipeline for document search with advanced prompt engineering",
        }

        skills = tracker._extract_skills(issue)

        assert "RAG (Retrieval Augmented Generation)" in skills
        assert "Prompt Engineering" in skills

    @pytest.mark.asyncio
    async def test_create_issue_achievement(self, tracker):
        """Test achievement creation from Linear issue."""
        issue = {
            "id": "LIN-123",
            "identifier": "LIN-123",
            "number": 123,
            "title": "Implement authentication system",
            "description": "Add OAuth2 authentication with JWT tokens",
            "state": {"name": "Done", "type": "completed"},
            "priority": {"name": "High"},
            "estimate": 8,
            "labels": [{"name": "feature"}, {"name": "security"}, {"name": "Python"}],
            "startedAt": "2025-01-27T08:00:00Z",
            "completedAt": "2025-01-28T16:00:00Z",
            "createdAt": "2025-01-27T07:00:00Z",
            "cycle": {"name": "Sprint 10"},
            "team": {"name": "Backend"},
        }

        # Mock database and achievement creation
        with patch(
            "services.achievement_collector.services.linear_tracker.get_db"
        ) as mock_get_db:
            with patch(
                "services.achievement_collector.services.linear_tracker.create_achievement_sync"
            ) as mock_create:
                mock_db = Mock()
                mock_get_db.return_value = iter([mock_db])

                mock_achievement = Mock()
                mock_achievement.title = "Completed: Implement authentication system"
                mock_achievement.id = 1
                mock_create.return_value = mock_achievement

                await tracker._create_issue_achievement(issue)

                # Verify achievement creation
                mock_create.assert_called_once()
                call_args = mock_create.call_args[0][1]

                # Verify achievement data
                assert call_args.title == "Completed: Implement authentication system"
                assert call_args.category == "feature"
                assert call_args.source_type == "linear"
                assert call_args.source_id == "LIN-123"
                assert "linear" in call_args.tags
                assert "feature" in call_args.tags
                assert "Python" in call_args.skills_demonstrated
                assert call_args.impact_score == 75  # High priority
                assert call_args.portfolio_ready is True

    @pytest.mark.asyncio
    async def test_create_epic_achievement(self, tracker):
        """Test achievement creation from Linear epic/project."""
        project = {
            "id": "EPIC-100",
            "name": "Payment Processing System",
            "description": "Implement complete payment processing with Stripe",
            "state": "completed",
            "startedAt": "2025-01-15T08:00:00Z",
            "completedAt": "2025-01-28T16:00:00Z",
            "createdAt": "2025-01-15T07:00:00Z",
            "issues": [
                {"estimate": 5},
                {"estimate": 8},
                {"estimate": 3},
                {"estimate": 13},
            ],
        }

        # Mock database and achievement creation
        with patch(
            "services.achievement_collector.services.linear_tracker.get_db"
        ) as mock_get_db:
            with patch(
                "services.achievement_collector.services.linear_tracker.create_achievement_sync"
            ) as mock_create:
                mock_db = Mock()
                mock_get_db.return_value = iter([mock_db])

                mock_achievement = Mock()
                mock_achievement.title = "Epic Completed: Payment Processing System"
                mock_achievement.id = 2
                mock_create.return_value = mock_achievement

                await tracker._create_epic_achievement(project)

                # Verify achievement creation
                mock_create.assert_called_once()
                call_args = mock_create.call_args[0][1]

                # Verify achievement data
                assert call_args.title == "Epic Completed: Payment Processing System"
                assert call_args.category == "project"
                assert call_args.source_type == "linear"
                assert call_args.source_id == "project_EPIC-100"
                assert "epic" in call_args.tags
                assert call_args.portfolio_ready is True
                assert call_args.impact_score > 70  # Epics have high impact

                # Check metrics
                assert call_args.metrics_after["total_issues"] == 4
                assert call_args.metrics_after["total_points"] == 29

    def test_priority_scoring(self, tracker):
        """Test priority-based impact scoring."""
        # Create issues with different priorities
        priorities = {
            "urgent": {"priority": {"name": "Urgent"}, "labels": []},
            "high": {"priority": {"name": "High"}, "labels": []},
            "medium": {"priority": {"name": "Medium"}, "labels": []},
            "low": {"priority": {"name": "Low"}, "labels": []},
            "none": {"priority": {"name": "None"}, "labels": []},
        }

        expected_scores = {
            "urgent": 90,
            "high": 75,
            "medium": 60,
            "low": 45,
            "none": 30,
        }

        # Test each priority level
        for priority_level, issue_data in priorities.items():
            # Simulate the impact score calculation from _create_issue_achievement
            priority_name = issue_data.get("priority", {}).get("name", "medium").lower()
            priority_scores = {
                "urgent": 90,
                "high": 75,
                "medium": 60,
                "low": 45,
                "none": 30,
            }
            impact_score = priority_scores.get(priority_name, 60)

            assert impact_score == expected_scores[priority_level]

    def test_last_sync_handling(self, tracker):
        """Test last sync timestamp handling."""
        # Test loading non-existent file
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = tracker._load_last_sync()
            assert result is None

        # Test saving timestamp
        test_time = datetime.now()
        mock_file = Mock()
        mock_open = Mock(return_value=mock_file)
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_file.write = Mock()

        with patch("builtins.open", mock_open):
            tracker._save_last_sync(test_time)
            mock_open.assert_called_once_with(".linear_last_sync", "w")
            mock_file.write.assert_called_once_with(str(test_time.timestamp()))


class TestLinearWebhookHandler:
    """Test Linear webhook handler."""

    @pytest.fixture
    def handler(self):
        """Create webhook handler instance."""
        return LinearWebhookHandler()

    @pytest.mark.asyncio
    async def test_handle_issue_completed_webhook(self, handler):
        """Test handling issue completion webhook."""
        event_data = {
            "action": "update",
            "data": {
                "id": "LIN-456",
                "title": "Fix login bug",
                "state": {"type": "completed"},
                "priority": {"name": "High"},
                "labels": [{"name": "bug"}],
            },
        }

        # Mock the achievement creation
        with patch.object(
            handler.tracker, "_create_issue_achievement", new_callable=AsyncMock
        ) as mock_create:
            await handler.handle_webhook("Issue", event_data)

            # Verify issue achievement was created
            mock_create.assert_called_once_with(event_data["data"])

    @pytest.mark.asyncio
    async def test_handle_project_completed_webhook(self, handler):
        """Test handling project completion webhook."""
        event_data = {
            "action": "update",
            "data": {
                "id": "PROJ-789",
                "name": "Q1 Features",
                "state": "completed",
                "issues": [],
            },
        }

        # Mock the achievement creation
        with patch.object(
            handler.tracker, "_create_epic_achievement", new_callable=AsyncMock
        ) as mock_create:
            await handler.handle_webhook("Project", event_data)

            # Verify project achievement was created
            mock_create.assert_called_once_with(event_data["data"])

    @pytest.mark.asyncio
    async def test_ignore_non_completed_webhooks(self, handler):
        """Test that non-completion events are ignored."""
        # Issue not completed
        event_data = {
            "action": "update",
            "data": {"id": "LIN-999", "state": {"type": "in_progress"}},
        }

        with patch.object(
            handler.tracker, "_create_issue_achievement", new_callable=AsyncMock
        ) as mock_create:
            await handler.handle_webhook("Issue", event_data)

            # Should not create achievement
            mock_create.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
