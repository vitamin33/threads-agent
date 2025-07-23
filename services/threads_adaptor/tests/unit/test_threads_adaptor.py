# services/threads_adaptor/tests/unit/test_threads_adaptor.py
"""Unit tests for threads_adaptor service."""

import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from services.threads_adaptor.main import EngagementMetrics, app


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("THREADS_APP_ID", "test_app_id")
    monkeypatch.setenv("THREADS_APP_SECRET", "test_secret")
    monkeypatch.setenv("THREADS_ACCESS_TOKEN", "test_token")
    monkeypatch.setenv("THREADS_USER_ID", "test_user_id")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_ping(self, client):
        """Test /ping endpoint."""
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"pong": True}

    def test_health_missing_credentials(self, client):
        """Test /health when credentials are missing."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "Missing Threads API credentials" in data["reason"]

    @patch("services.threads_adaptor.main.rate_limited_call")
    def test_health_with_credentials(self, mock_rate_limited, client, mock_env):
        """Test /health with valid credentials."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_rate_limited.return_value = asyncio.Future()
        mock_rate_limited.return_value.set_result(mock_response)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @patch("services.threads_adaptor.main.rate_limited_call")
    def test_health_api_error(self, mock_rate_limited, client, mock_env):
        """Test /health when API returns error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_rate_limited.return_value = asyncio.Future()
        mock_rate_limited.return_value.set_result(mock_response)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "API returned 401" in data["reason"]


class TestPublishEndpoint:
    """Test post publishing functionality."""

    def test_publish_no_credentials(self, client):
        """Test publishing without credentials."""
        post_data = {
            "topic": "test",
            "content": "Test content",
            "persona_id": "ai-jesus",
        }
        response = client.post("/publish", json=post_data)
        assert response.status_code == 503
        assert response.json()["detail"] == "Threads API not configured"

    @patch("services.threads_adaptor.main.rate_limited_call")
    @patch("services.threads_adaptor.main.SessionLocal")
    def test_publish_success(self, mock_session, mock_rate_limited, client, mock_env):
        """Test successful post publishing."""
        # Mock API responses
        create_response = Mock()
        create_response.json.return_value = {"id": "media_123"}

        publish_response = Mock()
        publish_response.json.return_value = {"id": "thread_123"}

        # Set up async mock
        async def mock_calls(*args, **kwargs):
            if "threads_publish" in str(args):
                return publish_response
            return create_response

        mock_rate_limited.side_effect = mock_calls

        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db

        post_data = {
            "topic": "AI",
            "content": "Test post about AI",
            "persona_id": "ai-jesus",
        }

        response = client.post("/publish", json=post_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert data["thread_id"] == "thread_123"
        assert "threads.net" in data["permalink"]

        # Verify database interaction
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("services.threads_adaptor.main.rate_limited_call")
    def test_publish_api_error(self, mock_rate_limited, client, mock_env):
        """Test publishing when API returns error."""
        # Mock error response
        error_response = Mock()
        error_response.json.return_value = {
            "error": {"message": "Invalid access token"}
        }

        async def mock_error(*args, **kwargs):
            return error_response

        mock_rate_limited.side_effect = mock_error

        post_data = {
            "topic": "test",
            "content": "Test content",
            "persona_id": "ai-jesus",
        }

        response = client.post("/publish", json=post_data)
        assert response.status_code == 400
        assert "Invalid access token" in response.json()["detail"]


class TestMetricsEndpoints:
    """Test engagement metrics functionality."""

    @patch("services.threads_adaptor.main.fetch_post_metrics")
    def test_get_post_metrics(self, mock_fetch, client):
        """Test fetching metrics for a specific post."""
        # Mock metrics
        mock_metrics = EngagementMetrics(
            likes_count=100,
            comments_count=10,
            shares_count=5,
            impressions_count=1000,
            engagement_rate=0.115,
            followers_count=500,
        )
        mock_fetch.return_value = asyncio.Future()
        mock_fetch.return_value.set_result(mock_metrics)

        response = client.get("/metrics/thread_123")
        assert response.status_code == 200
        data = response.json()
        assert data["likes_count"] == 100
        assert data["comments_count"] == 10
        assert data["engagement_rate"] == 0.115

    @patch("services.threads_adaptor.main.SessionLocal")
    def test_refresh_metrics(self, mock_session, client):
        """Test refreshing metrics for all posts."""
        # Mock database posts
        mock_post1 = Mock()
        mock_post1.thread_id = "thread_1"
        mock_post1.persona_id = "ai-jesus"
        mock_post1.published_at = datetime.utcnow()

        mock_post2 = Mock()
        mock_post2.thread_id = "thread_2"
        mock_post2.persona_id = "ai-elon"
        mock_post2.published_at = datetime.utcnow()

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_post1,
            mock_post2,
        ]
        mock_session.return_value = mock_db

        response = client.post("/refresh-metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "refreshing"
        assert "2 posts" in data["message"]


class TestListPublished:
    """Test listing published posts."""

    @patch("services.threads_adaptor.main.SessionLocal")
    def test_list_published(self, mock_session, client, mock_env):
        """Test listing published posts with metrics."""
        # Mock database posts
        mock_post = Mock()
        mock_post.thread_id = "thread_123"
        mock_post.persona_id = "ai-jesus"
        mock_post.content = "Test content"
        mock_post.published_at = datetime.utcnow()
        mock_post.likes_count = 50
        mock_post.comments_count = 5
        mock_post.shares_count = 2
        mock_post.impressions_count = 500
        mock_post.engagement_rate = 0.114

        mock_db = Mock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_post
        ]
        mock_session.return_value = mock_db

        response = client.get("/published")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        post = data[0]
        assert post["thread_id"] == "thread_123"
        assert post["persona_id"] == "ai-jesus"
        assert post["engagement"]["likes"] == 50
        assert post["engagement"]["engagement_rate"] == 0.114
        assert "threads.net" in post["permalink"]


class TestFetchPostMetrics:
    """Test the fetch_post_metrics function."""

    @patch("httpx.AsyncClient")
    @patch("services.threads_adaptor.main.rate_limited_call")
    async def test_fetch_metrics_success(self, mock_rate_limited, mock_client_class):
        """Test successful metrics fetching."""
        from services.threads_adaptor.main import fetch_post_metrics

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"name": "likes", "values": [{"value": 100}]},
                {"name": "replies", "values": [{"value": 10}]},
                {"name": "reposts", "values": [{"value": 5}]},
                {"name": "impressions", "values": [{"value": 1000}]},
                {"name": "followers_count", "values": [{"value": 500}]},
            ]
        }

        async def mock_call(*args, **kwargs):
            return mock_response

        mock_rate_limited.side_effect = mock_call

        # Need to set env vars for this test
        import os

        os.environ["THREADS_ACCESS_TOKEN"] = "test_token"

        metrics = await fetch_post_metrics("thread_123")
        assert metrics.likes_count == 100
        assert metrics.comments_count == 10
        assert metrics.shares_count == 5
        assert metrics.impressions_count == 1000
        assert metrics.engagement_rate == 0.115  # (100+10+5)/1000

    async def test_fetch_metrics_no_token(self):
        """Test metrics fetching without access token."""
        # Clear access token
        import os

        from services.threads_adaptor.main import fetch_post_metrics

        os.environ.pop("THREADS_ACCESS_TOKEN", None)

        metrics = await fetch_post_metrics("thread_123")
        assert metrics.likes_count == 0
        assert metrics.engagement_rate == 0.0
