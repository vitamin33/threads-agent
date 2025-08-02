# services/orchestrator/tests/test_viral_metrics_integration.py
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.orchestrator.main import app


@pytest.fixture
def client():
    """Create test client for orchestrator"""
    return TestClient(app)


class TestViralMetricsIntegration:
    """Integration tests for viral metrics collection in orchestrator"""

    def test_calculate_viral_coefficient_endpoint_exists(self, client):
        """Test that viral coefficient calculation endpoint exists"""
        response = client.post(
            "/viral-metrics/calculate",
            json={"shares": 10, "comments": 20, "views": 1000},
        )
        # Should return 200, not 404 (endpoint exists)
        assert response.status_code == 200

    def test_calculate_viral_coefficient_returns_correct_value(self, client):
        """Test viral coefficient calculation returns correct value"""
        response = client.post(
            "/viral-metrics/calculate",
            json={"shares": 10, "comments": 20, "views": 1000},
        )

        assert response.status_code == 200
        data = response.json()
        assert "viral_coefficient" in data
        assert data["viral_coefficient"] == 3.0  # (10 + 20) / 1000 * 100

    def test_calculate_viral_coefficient_with_metadata(self, client):
        """Test viral coefficient calculation with metadata"""
        response = client.post(
            "/viral-metrics/calculate",
            json={
                "shares": 15,
                "comments": 25,
                "views": 2000,
                "post_id": "post_123",
                "timestamp": "2024-01-01T12:00:00Z",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["viral_coefficient"] == 2.0  # (15 + 25) / 2000 * 100
        assert "metadata" in data
        assert data["metadata"]["post_id"] == "post_123"
        assert data["metadata"]["timestamp"] == "2024-01-01T12:00:00Z"

    def test_batch_calculate_viral_coefficients_endpoint(self, client):
        """Test batch viral coefficient calculation endpoint"""
        metrics_data = [
            {"shares": 10, "comments": 20, "views": 1000},
            {"shares": 5, "comments": 15, "views": 500},
            {"shares": 0, "comments": 10, "views": 100},
        ]

        response = client.post(
            "/viral-metrics/batch-calculate", json={"metrics_data": metrics_data}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3
        assert data["results"][0] == 3.0
        assert data["results"][1] == 4.0
        assert data["results"][2] == 10.0

    def test_batch_calculate_with_skip_invalid(self, client):
        """Test batch calculation with skip_invalid option"""
        metrics_data = [
            {"shares": 10, "comments": 20, "views": 1000},  # Valid
            {"shares": 5, "comments": 15, "views": 0},  # Invalid - zero views
            {"shares": 0, "comments": 10, "views": 100},  # Valid
        ]

        response = client.post(
            "/viral-metrics/batch-calculate",
            json={"metrics_data": metrics_data, "skip_invalid": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2  # Only valid entries
        assert data["results"][0] == 3.0
        assert data["results"][1] == 10.0

    def test_get_viral_metrics_stats_endpoint(self, client):
        """Test getting viral metrics calculation statistics"""
        # First perform some calculations to generate stats
        client.post(
            "/viral-metrics/calculate",
            json={"shares": 10, "comments": 20, "views": 1000},
        )
        client.post(
            "/viral-metrics/calculate", json={"shares": 5, "comments": 15, "views": 500}
        )

        # Then get stats
        response = client.get("/viral-metrics/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_calculations" in data
        assert "average_viral_coefficient" in data
        assert "min_viral_coefficient" in data
        assert "max_viral_coefficient" in data
        assert data["total_calculations"] >= 2

    def test_reset_viral_metrics_stats_endpoint(self, client):
        """Test resetting viral metrics statistics"""
        # First perform calculation
        client.post(
            "/viral-metrics/calculate",
            json={"shares": 10, "comments": 20, "views": 1000},
        )

        # Reset stats
        response = client.delete("/viral-metrics/stats")
        assert response.status_code == 200

        # Check stats are reset
        response = client.get("/viral-metrics/stats")
        data = response.json()
        assert data["total_calculations"] == 0

    def test_viral_coefficient_validation_errors(self, client):
        """Test validation errors for viral coefficient calculation"""
        # Test zero views
        response = client.post(
            "/viral-metrics/calculate", json={"shares": 10, "comments": 20, "views": 0}
        )
        assert response.status_code == 422  # Validation error

        # Test negative shares
        response = client.post(
            "/viral-metrics/calculate",
            json={"shares": -1, "comments": 20, "views": 1000},
        )
        assert response.status_code == 422  # Validation error

    def test_viral_coefficient_missing_fields(self, client):
        """Test missing required fields"""
        response = client.post(
            "/viral-metrics/calculate",
            json={"shares": 10, "comments": 20},  # Missing views
        )
        assert response.status_code == 422  # Validation error
