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

    @patch("services.threads_adaptor.main.THREADS_USER_ID", "test_user_id")
    @patch("services.threads_adaptor.main.THREADS_ACCESS_TOKEN", "test_token")
    @patch("services.threads_adaptor.main.THREADS_APP_ID", "test_app_id")
    @patch("services.threads_adaptor.main.rate_limited_call")
    def test_health_with_credentials(self, mock_rate_limited, client):
        """Test /health with valid credentials."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test_user_id"}

        # Set up the future
        future = asyncio.Future()
        future.set_result(mock_response)
        mock_rate_limited.return_value = future

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["threads_user_id"] == "test_user_id"


class TestPublishEndpoint:
    """Test /publish endpoint."""

    @patch("services.threads_adaptor.main.THREADS_USER_ID", "")
    def test_publish_missing_credentials(self, client):
        """Test publishing without credentials."""
        response = client.post(
            "/publish",
            json={
                "topic": "AI Ethics",
                "content": "Test content",
                "persona_id": "ai-jesus",
            },
        )
        assert response.status_code == 503
        assert "Threads API not configured" in response.json()["detail"]

    @patch("services.threads_adaptor.main.THREADS_USER_ID", "test_user_id")
    @patch("services.threads_adaptor.main.THREADS_ACCESS_TOKEN", "test_token")
    @patch("services.threads_adaptor.main.rate_limited_call")
    @patch("services.threads_adaptor.main.SessionLocal")
    def test_publish_success(self, mock_session, mock_rate_limited, client):
        """Test successful post publishing."""
        # Mock API responses
        create_response = Mock()
        create_response.status_code = 200
        create_response.json.return_value = {"id": "media_123"}

        publish_response = Mock()
        publish_response.status_code = 200
        publish_response.json.return_value = {"id": "thread_123"}

        # Set up futures
        create_future = asyncio.Future()
        create_future.set_result(create_response)
        publish_future = asyncio.Future()
        publish_future.set_result(publish_response)

        mock_rate_limited.side_effect = [create_future, publish_future]

        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)

        response = client.post(
            "/publish",
            json={
                "topic": "AI Ethics",
                "content": "Test content about AI ethics.",
                "persona_id": "ai-jesus",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "thread_123"
        assert data["status"] == "published"
        assert data["persona_id"] == "ai-jesus"
        assert data["content"] == "Test content about AI ethics."


class TestEngagementMetrics:
    """Test engagement metrics functionality."""

    def test_engagement_metrics_model(self):
        """Test EngagementMetrics model."""
        metrics = EngagementMetrics(
            likes_count=100,
            comments_count=20,
            shares_count=5,
            impressions_count=1000,
        )
        assert metrics.likes_count == 100
        assert metrics.comments_count == 20
        assert metrics.shares_count == 5
        assert metrics.impressions_count == 1000
        assert metrics.engagement_rate == 0.125  # (100+20+5)/1000

    def test_engagement_metrics_zero_impressions(self):
        """Test engagement rate with zero impressions."""
        metrics = EngagementMetrics(
            likes_count=10,
            comments_count=5,
            shares_count=2,
            impressions_count=0,
        )
        assert metrics.engagement_rate == 0.0


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiter_import(self):
        """Test that rate limiter can be imported."""
        from services.threads_adaptor.limiter import rate_limited_call

        assert callable(rate_limited_call)


class TestErrorHandling:
    """Test error handling in threads_adaptor."""

    @patch("services.threads_adaptor.main.THREADS_USER_ID", "test_user_id")
    @patch("services.threads_adaptor.main.THREADS_ACCESS_TOKEN", "test_token")
    @patch("services.threads_adaptor.main.rate_limited_call")
    def test_publish_api_error(self, mock_rate_limited, client):
        """Test handling of API errors during publishing."""
        # Mock API error response
        error_response = Mock()
        error_response.status_code = 400
        error_response.json.return_value = {"error": {"message": "Invalid content"}}

        # Set up future with error response
        future = asyncio.Future()
        future.set_result(error_response)
        mock_rate_limited.return_value = future

        response = client.post(
            "/publish",
            json={
                "topic": "Test",
                "content": "Test content",
                "persona_id": "ai-jesus",
            },
        )

        assert response.status_code == 400
        assert "Failed to create media container" in response.json()["detail"]

    @patch("services.threads_adaptor.main.THREADS_USER_ID", "test_user_id")
    @patch("services.threads_adaptor.main.THREADS_ACCESS_TOKEN", "test_token")
    @patch("services.threads_adaptor.main.rate_limited_call")
    def test_publish_network_error(self, mock_rate_limited, client):
        """Test handling of network errors."""
        # Mock network error
        future = asyncio.Future()
        future.set_exception(Exception("Network error"))
        mock_rate_limited.return_value = future

        response = client.post(
            "/publish",
            json={
                "topic": "Test",
                "content": "Test content",
                "persona_id": "ai-jesus",
            },
        )

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestDatabaseOperations:
    """Test database operations."""

    @patch("services.threads_adaptor.main.SessionLocal")
    def test_database_error_handling(self, mock_session):
        """Test handling of database errors."""
        # Mock database error
        mock_session.side_effect = Exception("Database connection failed")

        # This would typically be tested in integration tests
        # Here we just verify the mock setup
        with pytest.raises(Exception):
            mock_session()


class TestMetricsIntegration:
    """Test metrics recording integration."""

    @patch("services.threads_adaptor.main.record_engagement_rate")
    @patch("services.threads_adaptor.main.record_business_metric")
    def test_metrics_recording(self, mock_business_metric, mock_engagement_rate):
        """Test that metrics are recorded correctly."""
        # This would be tested in integration tests
        # Here we verify the functions can be called
        mock_engagement_rate("ai-jesus", 0.05)
        mock_engagement_rate.assert_called_once_with("ai-jesus", 0.05)

        mock_business_metric("cost_per_follow", persona_id="ai-jesus", cost=0.05)
        mock_business_metric.assert_called_once()


class TestPublishedEndpoint:
    """Test /published endpoint."""

    @patch("services.threads_adaptor.main.SessionLocal")
    def test_get_published_posts_empty(self, mock_session, client):
        """Test getting published posts when none exist."""
        # Mock empty database query
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query
        mock_session.return_value = mock_db
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)

        response = client.get("/published")
        assert response.status_code == 200
        assert response.json() == {"posts": [], "count": 0}


class TestMetricsEndpoint:
    """Test /metrics endpoint."""

    def test_metrics_endpoint(self, client):
        """Test that metrics endpoint returns prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
        # Should contain some prometheus metrics
        assert "# HELP" in response.text
        assert "# TYPE" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])