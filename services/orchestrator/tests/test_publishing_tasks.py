"""
Tests for Celery Publishing Tasks.

This module tests the async publishing infrastructure including:
- Celery task definitions and execution
- Retry mechanisms with exponential backoff
- Status updates in ContentSchedule model
- Error handling and logging
- Integration with publishing engine
"""

from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from services.orchestrator.publishing.tasks import (
    publish_content_task,
    publish_scheduled_content_task,
    retry_failed_publication_task,
)
from services.orchestrator.publishing.adapters.base import PublishingResult
from services.orchestrator.db.models import ContentItem, ContentSchedule


class TestPublishingTasks:
    """Test Celery tasks for async publishing."""

    @patch("services.orchestrator.publishing.tasks.get_db_session")
    @patch("services.orchestrator.publishing.tasks.PublishingEngine")
    def test_publish_content_task_success(self, mock_engine_class, mock_get_db):
        """Test successful content publishing task."""
        # This will fail - task doesn't exist yet
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock content schedule
        mock_schedule = Mock(spec=ContentSchedule)
        mock_schedule.id = 1
        mock_schedule.platform = "dev.to"
        mock_schedule.status = "scheduled"
        mock_schedule.platform_config = {"api_key": "test_key"}
        mock_schedule.content_item = Mock(spec=ContentItem)

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_schedule
        )

        # Mock publishing engine
        mock_engine = Mock()
        mock_engine.publish_to_platform = AsyncMock(
            return_value=PublishingResult(
                success=True,
                platform="dev.to",
                external_id="12345",
                url="https://dev.to/article/12345",
            )
        )
        mock_engine_class.return_value = mock_engine

        # Execute task
        result = publish_content_task(schedule_id=1)

        # Verify results
        assert result["success"] is True
        assert result["platform"] == "dev.to"
        assert result["external_id"] == "12345"

        # Verify schedule was updated
        assert mock_schedule.status == "published"
        assert mock_schedule.published_at is not None
        mock_db.commit.assert_called_once()

    @patch("services.orchestrator.publishing.tasks.get_db_session")
    @patch("services.orchestrator.publishing.tasks.PublishingEngine")
    @patch(
        "services.orchestrator.publishing.tasks.retry_failed_publication_task.apply_async"
    )
    def test_publish_content_task_failure_with_retry(
        self, mock_apply_async, mock_engine_class, mock_get_db
    ):
        """Test content publishing task failure triggers retry."""
        # This will fail - retry logic doesn't exist yet
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock content schedule
        mock_schedule = Mock(spec=ContentSchedule)
        mock_schedule.id = 1
        mock_schedule.retry_count = 0
        mock_schedule.max_retries = 3
        mock_schedule.platform = "dev.to"
        mock_schedule.status = "scheduled"
        mock_schedule.content_item = Mock(spec=ContentItem)

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_schedule
        )

        # Mock publishing engine to fail
        mock_engine = Mock()
        mock_engine.publish_to_platform = AsyncMock(
            return_value=PublishingResult(
                success=False,
                platform="dev.to",
                error_message="API Error: Rate limit exceeded",
            )
        )
        mock_engine_class.return_value = mock_engine

        # Execute task
        result = publish_content_task(schedule_id=1)

        # Verify results
        assert result["success"] is False
        assert "retry_scheduled" in result

        # Verify retry was scheduled
        assert mock_schedule.retry_count == 1
        assert mock_schedule.status == "retry_scheduled"
        assert mock_schedule.next_retry_time is not None
        mock_db.commit.assert_called_once()

        # Verify async retry task was scheduled
        mock_apply_async.assert_called_once()

    @patch("services.orchestrator.publishing.tasks.get_db_session")
    def test_publish_scheduled_content_task_finds_due_content(self, mock_get_db):
        """Test that scheduled content task finds and processes due content."""
        # This will fail - scheduled task doesn't exist yet
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock due schedules
        now = datetime.now(timezone.utc)
        mock_schedule1 = Mock(spec=ContentSchedule)
        mock_schedule1.id = 1
        mock_schedule1.scheduled_time = now - timedelta(minutes=5)  # 5 minutes overdue

        mock_schedule2 = Mock(spec=ContentSchedule)
        mock_schedule2.id = 2
        mock_schedule2.scheduled_time = now - timedelta(minutes=2)  # 2 minutes overdue

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_schedule1,
            mock_schedule2,
        ]

        # Mock the publish_content_task
        with patch(
            "services.orchestrator.publishing.tasks.publish_content_task.delay"
        ) as mock_delay:
            result = publish_scheduled_content_task()

            # Verify results
            assert result["processed_count"] == 2
            assert result["scheduled_count"] == 2

            # Verify individual tasks were scheduled
            assert mock_delay.call_count == 2
            mock_delay.assert_any_call(schedule_id=1)
            mock_delay.assert_any_call(schedule_id=2)

    @patch("services.orchestrator.publishing.tasks.get_db_session")
    @patch("services.orchestrator.publishing.tasks.PublishingEngine")
    def test_retry_failed_publication_task(self, mock_engine_class, mock_get_db):
        """Test retry mechanism for failed publications."""
        # This will fail - retry task doesn't exist yet
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock failed schedule
        mock_schedule = Mock(spec=ContentSchedule)
        mock_schedule.id = 1
        mock_schedule.retry_count = 1
        mock_schedule.max_retries = 3
        mock_schedule.platform = "dev.to"
        mock_schedule.status = "retry_scheduled"
        mock_schedule.next_retry_time = datetime.now(timezone.utc) - timedelta(
            minutes=5
        )
        mock_schedule.content_item = Mock(spec=ContentItem)

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_schedule
        )

        # Mock successful retry
        mock_engine = Mock()
        mock_engine.publish_to_platform = AsyncMock(
            return_value=PublishingResult(
                success=True,
                platform="dev.to",
                external_id="12345",
                url="https://dev.to/article/12345",
            )
        )
        mock_engine_class.return_value = mock_engine

        # Execute retry task
        result = retry_failed_publication_task(schedule_id=1)

        # Verify success after retry
        assert result["success"] is True
        assert result["retry_attempt"] == 2  # Was attempt 1, now 2
        assert mock_schedule.status == "published"
        assert mock_schedule.published_at is not None

    def test_exponential_backoff_calculation(self):
        """Test that retry delays use exponential backoff."""
        # This will fail - backoff calculation doesn't exist yet
        from services.orchestrator.publishing.tasks import calculate_retry_delay

        # Test backoff progression: 1min, 2min, 4min, 8min, etc.
        assert calculate_retry_delay(0) == 60  # 1 minute
        assert calculate_retry_delay(1) == 120  # 2 minutes
        assert calculate_retry_delay(2) == 240  # 4 minutes
        assert calculate_retry_delay(3) == 480  # 8 minutes

        # Test maximum backoff (e.g., 1 hour)
        assert calculate_retry_delay(10) <= 3600  # Max 1 hour

    @patch("services.orchestrator.publishing.tasks.get_db_session")
    def test_publish_content_task_schedule_not_found(self, mock_get_db):
        """Test task handles missing schedule gracefully."""
        # This will fail - error handling doesn't exist yet
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock schedule not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute task
        result = publish_content_task(schedule_id=999)

        # Verify error handling
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @patch("services.orchestrator.publishing.tasks.get_db_session")
    @patch("services.orchestrator.publishing.tasks.PublishingEngine")
    def test_max_retries_exceeded(self, mock_engine_class, mock_get_db):
        """Test that schedules with exceeded max retries are marked as failed."""
        # This will fail - max retry handling doesn't exist yet
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock schedule with max retries exceeded
        mock_schedule = Mock(spec=ContentSchedule)
        mock_schedule.id = 1
        mock_schedule.retry_count = 3
        mock_schedule.max_retries = 3
        mock_schedule.platform = "dev.to"
        mock_schedule.status = "retry_scheduled"
        mock_schedule.content_item = Mock(spec=ContentItem)

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_schedule
        )

        # Mock publishing engine to fail again
        mock_engine = Mock()
        mock_engine.publish_to_platform = AsyncMock(
            return_value=PublishingResult(
                success=False, platform="dev.to", error_message="Persistent API Error"
            )
        )
        mock_engine_class.return_value = mock_engine

        # Execute task
        result = publish_content_task(schedule_id=1)

        # Verify failure handling
        assert result["success"] is False
        assert mock_schedule.status == "failed"
        assert mock_schedule.error_message == "Persistent API Error"
        mock_db.commit.assert_called_once()
