"""Tests for viral pattern engine FastAPI service."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from services.viral_pattern_engine.main import app


class TestViralPatternEngineAPI:
    """Test cases for the FastAPI service endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_viral_post_data(self):
        """Sample viral post data for testing."""
        return {
            "content": "Just discovered this incredible Python library that automates 90% of my data analysis!",
            "account_id": "test_user",
            "post_url": "https://threads.net/test/post1",
            "timestamp": datetime.now().isoformat(),
            "likes": 1500,
            "comments": 300,
            "shares": 150,
            "engagement_rate": 0.85,
            "performance_percentile": 95.0,
        }

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "service": "viral_pattern_engine",
        }

    def test_extract_patterns_endpoint(self, client, sample_viral_post_data):
        """Test pattern extraction endpoint."""
        response = client.post("/extract-patterns", json=sample_viral_post_data)

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "hook_patterns" in data
        assert "emotion_patterns" in data
        assert "structure_patterns" in data
        assert "engagement_score" in data
        assert "pattern_strength" in data

        # Check that patterns were detected
        assert len(data["hook_patterns"]) > 0
        assert data["engagement_score"] == 0.85

    def test_extract_patterns_invalid_data(self, client):
        """Test pattern extraction with invalid data."""
        invalid_data = {"content": "test"}  # Missing required fields

        response = client.post("/extract-patterns", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_analyze_batch_endpoint(self, client, sample_viral_post_data):
        """Test batch analysis endpoint."""
        batch_data = {"posts": [sample_viral_post_data, sample_viral_post_data]}

        response = client.post("/analyze-batch", json=batch_data)

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert len(data["results"]) == 2
        assert "summary" in data

        # Check summary statistics
        summary = data["summary"]
        assert "total_posts" in summary
        assert "average_pattern_strength" in summary
        assert summary["total_posts"] == 2

    def test_get_pattern_types_endpoint(self, client):
        """Test endpoint that returns available pattern types."""
        response = client.get("/pattern-types")

        assert response.status_code == 200
        data = response.json()

        assert "hook_patterns" in data
        assert "emotion_patterns" in data

        # Check that it includes expected pattern types
        hook_types = data["hook_patterns"]
        assert "discovery" in hook_types
        assert "statistical" in hook_types
        assert "curiosity_gap" in hook_types
