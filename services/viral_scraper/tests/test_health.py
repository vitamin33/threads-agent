# services/viral_scraper/tests/test_health.py
"""
TDD Test: Basic viral scraper service structure and health endpoint

This test will fail because the service doesn't exist yet.
Following TDD principles: Red -> Green -> Refactor
"""

from fastapi.testclient import TestClient


def test_viral_scraper_health_endpoint():
    """Test that viral scraper service has a health endpoint that returns healthy status"""
    # This will fail because main.py doesn't exist yet
    from services.viral_scraper.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "viral-scraper"}


def test_viral_scraper_app_title():
    """Test that the FastAPI app has correct title and description"""
    from services.viral_scraper.main import app

    assert app.title == "viral-scraper"
    assert "Viral content scraper service" in app.description
