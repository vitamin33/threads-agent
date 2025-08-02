"""
Test for dashboard API endpoints.
Following TDD - write failing tests first.
"""

from fastapi.testclient import TestClient


def test_get_variant_metrics_endpoint_exists():
    """Test that /dashboard/variants endpoint exists and returns basic structure."""
    # This test will fail until we create the endpoint
    from services.dashboard_api.main import app

    client = TestClient(app)
    response = client.get("/dashboard/variants")

    assert response.status_code == 200
    data = response.json()
    assert "variants" in data
    assert isinstance(data["variants"], list)


def test_get_variant_metrics_returns_expected_fields():
    """Test that variant metrics include required fields."""
    from services.dashboard_api.main import app

    client = TestClient(app)
    response = client.get("/dashboard/variants")

    assert response.status_code == 200
    data = response.json()

    # If we have variants, they should have these required fields
    if data["variants"]:
        variant = data["variants"][0]
        required_fields = [
            "variant_id",
            "engagement_rate",
            "impressions",
            "successes",
            "early_kill_status",
            "pattern_fatigue_warning",
        ]
        for field in required_fields:
            assert field in variant, f"Missing required field: {field}"
