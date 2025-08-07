"""Simple route test to debug 404 issue"""

from fastapi.testclient import TestClient
from services.orchestrator.main import app


def test_health_route_works():
    """Test that basic routes work"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_content_route_exists():
    """Test that the content route exists"""
    client = TestClient(app)
    # Just check if the route exists with invalid data first
    response = client.post("/api/v1/content", json={})
    # Should get validation error (422), not 404
    assert response.status_code != 404