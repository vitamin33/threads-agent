# services/viral_scraper/tests/test_scraping_endpoints.py
"""
TDD Test: Scraping endpoints for viral content scraper

This test will fail because the scraping endpoints don't exist yet.
Following TDD principles: Red -> Green -> Refactor
"""

from fastapi.testclient import TestClient


def test_scrape_account_endpoint():
    """Test POST /scrape/account/{account_id} endpoint to trigger scraping"""
    # This will fail because the endpoint doesn't exist yet
    from services.viral_scraper.main import app

    client = TestClient(app)

    account_id = "viral_account_123"
    response = client.post(f"/scrape/account/{account_id}")

    assert response.status_code == 200

    data = response.json()
    assert "task_id" in data
    assert "account_id" in data
    assert data["account_id"] == account_id
    assert data["status"] == "queued"


def test_scrape_account_with_options():
    """Test scraping with optional parameters like max_posts and days_back"""
    from services.viral_scraper.main import app
    import uuid

    client = TestClient(app)

    # Use unique account ID to avoid rate limiting from other tests
    account_id = f"viral_account_{uuid.uuid4().hex[:8]}"
    scrape_request = {
        "max_posts": 100,
        "days_back": 7,
        "min_performance_percentile": 99.0,
    }

    response = client.post(f"/scrape/account/{account_id}", json=scrape_request)

    assert response.status_code == 200

    data = response.json()
    assert "task_id" in data
    assert data["account_id"] == account_id
    assert data["max_posts"] == 100
    assert data["days_back"] == 7


def test_scrape_account_invalid_account_id():
    """Test scraping with invalid account_id returns proper error"""
    from services.viral_scraper.main import app

    client = TestClient(app)

    # Empty account_id should be invalid
    response = client.post("/scrape/account/")

    assert response.status_code == 404  # Not found due to missing path param


def test_get_scraping_task_status():
    """Test GET /scrape/tasks/{task_id}/status endpoint"""
    from services.viral_scraper.main import app

    client = TestClient(app)

    task_id = "test_task_123"
    response = client.get(f"/scrape/tasks/{task_id}/status")

    assert response.status_code == 200

    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["task_id"] == task_id
    # Status should be one of: queued, running, completed, failed
    assert data["status"] in ["queued", "running", "completed", "failed"]
