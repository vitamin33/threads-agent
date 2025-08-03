"""Tests for error handling in viral pattern engine."""

import pytest
from fastapi.testclient import TestClient
from services.viral_pattern_engine.main import app


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_extract_patterns_malformed_json(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/extract-patterns",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_extract_patterns_missing_fields(self, client):
        """Test handling of missing required fields."""
        incomplete_data = {
            "content": "test content"
            # Missing required fields like account_id, timestamp, etc.
        }

        response = client.post("/extract-patterns", json=incomplete_data)
        assert response.status_code == 422

    def test_analyze_batch_empty_posts(self, client):
        """Test batch analysis with empty posts list."""
        response = client.post("/analyze-batch", json={"posts": []})

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["total_posts"] == 0
        assert data["summary"]["average_pattern_strength"] == 0.0
