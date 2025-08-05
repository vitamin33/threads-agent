# /services/orchestrator/tests/test_comment_monitor.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List, Dict, Any

from services.orchestrator.comment_monitor import CommentMonitor, Comment


class TestCommentMonitor:
    """Test cases for CommentMonitor class following TDD methodology."""

    @pytest.fixture
    def mock_fake_threads_client(self):
        """Mock the fake_threads API client."""
        client = Mock()
        client.get_comments = AsyncMock()
        return client

    @pytest.fixture
    def mock_celery_client(self):
        """Mock Celery client for queuing tasks."""
        client = Mock()
        client.send_task = Mock()
        return client

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def comment_monitor(self, mock_fake_threads_client, mock_celery_client, mock_db_session):
        """Create CommentMonitor instance with mocked dependencies."""
        return CommentMonitor(
            fake_threads_client=mock_fake_threads_client,
            celery_client=mock_celery_client,
            db_session=mock_db_session
        )

    def test_start_monitoring_returns_monitoring_task_id(self, comment_monitor):
        """
        FAILING TEST: CommentMonitor.start_monitoring() should return a monitoring task ID.
        
        This test will fail because CommentMonitor class doesn't exist yet.
        """
        post_id = "post_123"
        
        result = comment_monitor.start_monitoring(post_id)
        
        assert result is not None
        assert isinstance(result, str)
        assert result.startswith("monitor_")

    def test_start_monitoring_calls_fake_threads_api(self, comment_monitor, mock_fake_threads_client):
        """
        FAILING TEST: start_monitoring should call fake_threads API to get comments.
        
        This test will fail because the method doesn't exist yet.
        """
        post_id = "post_123"
        mock_fake_threads_client.get_comments.return_value = []
        
        comment_monitor.start_monitoring(post_id)
        
        mock_fake_threads_client.get_comments.assert_called_once_with(post_id)

    def test_comment_deduplication_prevents_duplicate_processing(self, comment_monitor, mock_db_session):
        """
        FAILING TEST: Comments should be deduplicated by comment ID.
        
        This test will fail because comment deduplication logic doesn't exist yet.
        """
        post_id = "post_123"
        duplicate_comments = [
            {"id": "comment_1", "text": "Great post!", "author": "user1", "timestamp": "2024-01-01T10:00:00Z"},
            {"id": "comment_1", "text": "Great post!", "author": "user1", "timestamp": "2024-01-01T10:00:00Z"},  # Duplicate
            {"id": "comment_2", "text": "Nice work", "author": "user2", "timestamp": "2024-01-01T10:01:00Z"}
        ]
        
        # Create a mock that tracks which comment IDs have been queried
        call_count = {"comment_1": 0, "comment_2": 0}
        
        def mock_filter_first(filter_arg):
            # Create a result mock for the filter().first() chain  
            result_mock = Mock()
            
            # The filter creates a different result for each comment_id
            def first():
                # For this test, we want comment_1 to appear to exist in DB, comment_2 to not exist
                # Since we can't easily parse the SQLAlchemy filter, we'll check call order instead
                # First call should be comment_1 (exists), second call comment_1 again (exists), third call comment_2 (doesn't exist)
                call_count["total"] = call_count.get("total", 0) + 1
                if call_count["total"] <= 2:  # First two calls are for comment_1
                    return Mock(comment_id="comment_1")  # Simulate existing comment
                else:  # Third call is for comment_2
                    return None  # Simulate non-existing comment
            
            result_mock.first = first
            return result_mock

        mock_query = Mock()
        mock_query.filter = mock_filter_first
        mock_db_session.query.return_value = mock_query
        
        result = comment_monitor._deduplicate_comments(duplicate_comments)
        
        assert len(result) == 1  # Only comment_2 should remain
        assert result[0]["id"] == "comment_2"

    def test_rate_limiting_implements_exponential_backoff(self, comment_monitor):
        """
        FAILING TEST: Rate limiting should implement exponential backoff.
        
        This test will fail because rate limiting logic doesn't exist yet.
        """
        initial_delay = 1.0
        max_retries = 3
                
        delays = comment_monitor._calculate_backoff_delays(initial_delay, max_retries)
        
        assert len(delays) == max_retries
        assert delays[0] == 1.0  # First retry: 1 second
        assert delays[1] == 2.0  # Second retry: 2 seconds  
        assert delays[2] == 4.0  # Third retry: 4 seconds

    def test_comments_queued_to_celery_for_intent_analysis(self, comment_monitor, mock_celery_client):
        """
        FAILING TEST: New comments should be queued to Celery for intent analysis.
        
        This test will fail because queueing logic doesn't exist yet.
        """
        post_id = "post_123"
        comments = [
            {"id": "comment_1", "text": "Great post!", "author": "user1", "timestamp": "2024-01-01T10:00:00Z"},
            {"id": "comment_2", "text": "Nice work", "author": "user2", "timestamp": "2024-01-01T10:01:00Z"}
        ]
        
        comment_monitor._queue_comments_for_analysis(comments, post_id)
        
        assert mock_celery_client.send_task.call_count == 2
        expected_calls = [
            (("analyze_comment_intent",), {"args": [comments[0], post_id]}),
            (("analyze_comment_intent",), {"args": [comments[1], post_id]})
        ]
        actual_calls = [(call.args, call.kwargs) for call in mock_celery_client.send_task.call_args_list]
        assert actual_calls == expected_calls

    def test_raw_comments_stored_in_database(self, comment_monitor, mock_db_session):
        """
        FAILING TEST: Raw comments should be stored in database for analysis.
        
        This test will fail because database storage logic doesn't exist yet.
        """
        post_id = "post_123"
        comments = [
            {"id": "comment_1", "text": "Great post!", "author": "user1", "timestamp": "2024-01-01T10:00:00Z"}
        ]
        
        comment_monitor._store_comments_in_db(comments, post_id)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        # Verify the comment object was created with correct data
        added_comment = mock_db_session.add.call_args[0][0]
        assert added_comment.comment_id == "comment_1"
        assert added_comment.post_id == post_id
        assert added_comment.text == "Great post!"
        assert added_comment.author == "user1"