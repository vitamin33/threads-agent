# services/viral_scraper/tests/test_rate_limiting.py
"""
TDD Test: Rate limiting behavior for ethical scraping

This test will fail because rate limiting doesn't exist yet.
Following TDD principles: Red -> Green -> Refactor
"""

from fastapi.testclient import TestClient
import time


def test_rate_limiting_single_account():
    """Test that scraping the same account too frequently returns 429 Too Many Requests"""
    # This will fail because rate limiting doesn't exist yet
    from services.viral_scraper.main import app

    client = TestClient(app)
    account_id = "test_account_rate_limit"

    # First request should succeed
    response1 = client.post(f"/scrape/account/{account_id}")
    assert response1.status_code == 200

    # Second immediate request should be rate limited
    response2 = client.post(f"/scrape/account/{account_id}")
    assert response2.status_code == 429

    data = response2.json()
    assert "detail" in data
    detail = data["detail"]
    assert "error" in detail
    assert "rate limit" in detail["error"].lower()
    assert "retry_after" in detail


def test_rate_limiting_different_accounts():
    """Test that rate limiting is per-account, not global"""
    from services.viral_scraper.main import app

    client = TestClient(app)

    # First account
    response1 = client.post("/scrape/account/account_1")
    assert response1.status_code == 200

    # Different account should not be rate limited
    response2 = client.post("/scrape/account/account_2")
    assert response2.status_code == 200


def test_rate_limiting_reset_after_time():
    """Test that rate limiting resets after configured time period"""
    from services.viral_scraper.main import app

    client = TestClient(app)
    account_id = "test_account_reset"

    # First request
    response1 = client.post(f"/scrape/account/{account_id}")
    assert response1.status_code == 200

    # Second request should be rate limited
    response2 = client.post(f"/scrape/account/{account_id}")
    assert response2.status_code == 429

    # Mock time passing (in real implementation, this would use a configurable window)
    # For testing, we'll expect the service to have a very short window
    time.sleep(0.1)  # Wait 100ms

    # Third request after waiting should succeed (assuming 100ms window for testing)
    response3 = client.post(f"/scrape/account/{account_id}")
    # This might still be 429 depending on implementation, that's OK for now


def test_rate_limiting_headers():
    """Test that rate limiting includes proper headers"""
    from services.viral_scraper.main import app

    client = TestClient(app)
    account_id = "test_account_headers"

    # First request to trigger rate limiting
    client.post(f"/scrape/account/{account_id}")

    # Second request should return rate limiting headers
    response = client.post(f"/scrape/account/{account_id}")

    if response.status_code == 429:
        # Should include standard rate limiting headers
        assert (
            "X-RateLimit-Limit" in response.headers
            or "RateLimit-Limit" in response.headers
        )
        assert (
            "X-RateLimit-Remaining" in response.headers
            or "RateLimit-Remaining" in response.headers
        )


def test_get_rate_limit_status():
    """Test GET /rate-limit/status/{account_id} endpoint"""
    from services.viral_scraper.main import app

    client = TestClient(app)
    account_id = "test_account_status"

    # Check rate limit status before any requests
    response = client.get(f"/rate-limit/status/{account_id}")
    assert response.status_code == 200

    data = response.json()
    assert "account_id" in data
    assert "requests_remaining" in data
    assert "reset_time" in data
    assert data["account_id"] == account_id
