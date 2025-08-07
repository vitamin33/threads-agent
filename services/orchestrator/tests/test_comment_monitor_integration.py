# /services/orchestrator/tests/test_comment_monitor_integration.py
import pytest
import httpx
from unittest.mock import Mock, patch
from typing import Dict, Any

from services.orchestrator.comment_monitor import CommentMonitor, Comment


class TestCommentMonitorIntegration:
    """Integration tests for CommentMonitor with fake_threads service."""

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
    def fake_threads_client(self):
        """Create a real HTTP client for fake_threads service."""
        return httpx.Client(base_url="http://fake-threads:8080")

    @pytest.fixture
    def comment_monitor_with_http(
        self, fake_threads_client, mock_celery_client, mock_db_session
    ):
        """Create CommentMonitor with real HTTP client."""
        return CommentMonitor(
            fake_threads_client=fake_threads_client,
            celery_client=mock_celery_client,
            db_session=mock_db_session,
        )

    def test_end_to_end_comment_monitoring_flow(
        self, mock_celery_client, mock_db_session
    ):
        """
        Integration test: Complete comment monitoring flow from API to database.

        This test simulates the full pipeline:
        1. Create comments via fake_threads API
        2. Monitor comments via CommentMonitor
        3. Verify deduplication works
        4. Verify comments are queued for analysis
        5. Verify comments are stored in database
        """
        # Mock the HTTP calls to fake_threads
        mock_comments_response = [
            {
                "id": "comment_1",
                "post_id": "post_123",
                "text": "Great post!",
                "author": "user1",
                "timestamp": "2024-01-01T10:00:00Z",
            },
            {
                "id": "comment_2",
                "post_id": "post_123",
                "text": "Nice work!",
                "author": "user2",
                "timestamp": "2024-01-01T10:01:00Z",
            },
        ]

        # Mock HTTP client that returns our test comments
        mock_http_client = Mock()
        mock_http_client.get.return_value.json.return_value = mock_comments_response
        mock_http_client.get.return_value.status_code = 200

        # Mock database - no existing comments
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None  # No existing comments
        mock_db_session.query.return_value = mock_query

        # Create CommentMonitor with mocked dependencies
        comment_monitor = CommentMonitor(
            fake_threads_client=mock_http_client,
            celery_client=mock_celery_client,
            db_session=mock_db_session,
        )

        post_id = "post_123"

        # Execute the monitoring process
        result = comment_monitor.process_comments_for_post(post_id)

        # Verify API was called
        mock_http_client.get.assert_called_once_with(f"/posts/{post_id}/comments")

        # Verify comments were queued for analysis (2 comments)
        assert mock_celery_client.send_task.call_count == 2

        # Verify comments were stored in database (2 add calls)
        assert mock_db_session.add.call_count == 2
        mock_db_session.commit.assert_called_once()

        # Verify return value indicates success
        assert result["status"] == "success"
        assert result["processed_count"] == 2
        assert result["queued_count"] == 2
        assert result["stored_count"] == 2

    def test_comment_monitoring_with_existing_comments_deduplication(
        self, mock_celery_client, mock_db_session
    ):
        """
        Test that existing comments are properly deduplicated.
        """
        # Mock HTTP response with duplicate and new comments
        mock_comments_response = [
            {
                "id": "comment_1",
                "post_id": "post_123",
                "text": "Great post!",
                "author": "user1",
                "timestamp": "2024-01-01T10:00:00Z",
            },
            {
                "id": "comment_2",
                "post_id": "post_123",
                "text": "Nice work!",
                "author": "user2",
                "timestamp": "2024-01-01T10:01:00Z",
            },
        ]

        mock_http_client = Mock()
        mock_http_client.get.return_value.json.return_value = mock_comments_response
        mock_http_client.get.return_value.status_code = 200

        # Mock database - comment_1 already exists, comment_2 doesn't
        call_count = {"total": 0}

        def mock_filter_chain(filter_expr):
            result_mock = Mock()

            def first():
                call_count["total"] += 1
                # First call is for comment_1 (should exist), second is for comment_2 (shouldn't exist)
                if call_count["total"] == 1:
                    return Mock(comment_id="comment_1")  # comment_1 exists in DB
                else:
                    return None  # comment_2 doesn't exist in DB

            result_mock.first = first
            return result_mock

        mock_query = Mock()
        mock_query.filter.side_effect = mock_filter_chain
        mock_db_session.query.return_value = mock_query

        comment_monitor = CommentMonitor(
            fake_threads_client=mock_http_client,
            celery_client=mock_celery_client,
            db_session=mock_db_session,
        )

        post_id = "post_123"
        result = comment_monitor.process_comments_for_post(post_id)

        # Only comment_2 should be processed (comment_1 was deduplicated)
        assert mock_celery_client.send_task.call_count == 1
        assert mock_db_session.add.call_count == 1

        assert result["status"] == "success"
        assert result["processed_count"] == 1  # Only comment_2
        assert result["queued_count"] == 1
        assert result["stored_count"] == 1

    def test_comment_monitoring_handles_api_errors_gracefully(
        self, mock_celery_client, mock_db_session
    ):
        """
        Test that CommentMonitor handles API errors gracefully.
        """
        # Mock HTTP client that raises an exception
        mock_http_client = Mock()
        mock_http_client.get.side_effect = httpx.RequestError("Connection failed")

        comment_monitor = CommentMonitor(
            fake_threads_client=mock_http_client,
            celery_client=mock_celery_client,
            db_session=mock_db_session,
        )

        post_id = "post_123"
        result = comment_monitor.process_comments_for_post(post_id)

        # Should handle error gracefully
        assert result["status"] == "error"
        assert "Connection failed" in result["error"]

        # No comments should be processed
        mock_celery_client.send_task.assert_not_called()
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
