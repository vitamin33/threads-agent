# services/viral_scraper/tests/test_viral_posts_endpoint.py
"""
TDD Test: GET /viral-posts endpoint to retrieve scraped content

This test will fail because the endpoint doesn't exist yet.
Following TDD principles: Red -> Green -> Refactor
"""

from fastapi.testclient import TestClient


def test_get_viral_posts_endpoint():
    """Test GET /viral-posts endpoint returns list of viral posts"""
    # This will fail because the endpoint doesn't exist yet
    from services.viral_scraper.main import app

    client = TestClient(app)
    response = client.get("/viral-posts")

    assert response.status_code == 200

    data = response.json()
    assert "posts" in data
    assert "total_count" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["posts"], list)


def test_get_viral_posts_with_filters():
    """Test GET /viral-posts with query parameters for filtering"""
    from services.viral_scraper.main import app

    client = TestClient(app)

    # Test with account_id filter
    response = client.get(
        "/viral-posts?account_id=test_account&limit=10&min_engagement_rate=0.1"
    )

    assert response.status_code == 200

    data = response.json()
    assert "posts" in data
    assert data["page_size"] <= 10


def test_get_viral_posts_top_1_percent_only():
    """Test GET /viral-posts with top_1_percent_only filter"""
    from services.viral_scraper.main import app

    client = TestClient(app)

    response = client.get("/viral-posts?top_1_percent_only=true")

    assert response.status_code == 200

    data = response.json()
    assert "posts" in data
    # All returned posts should be in top 1% (performance_percentile > 99)
    for post in data["posts"]:
        assert post["performance_percentile"] > 99.0


def test_get_viral_posts_pagination():
    """Test GET /viral-posts supports pagination"""
    from services.viral_scraper.main import app

    client = TestClient(app)

    # Test page 1
    response1 = client.get("/viral-posts?page=1&limit=5")
    assert response1.status_code == 200
    data1 = response1.json()

    # Test page 2
    response2 = client.get("/viral-posts?page=2&limit=5")
    assert response2.status_code == 200
    data2 = response2.json()

    # Both should have same structure
    for data in [data1, data2]:
        assert "posts" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page_size"] == 5


def test_get_viral_posts_by_account():
    """Test GET /viral-posts/{account_id} endpoint for specific account"""
    from services.viral_scraper.main import app

    client = TestClient(app)

    account_id = "test_account_123"
    response = client.get(f"/viral-posts/{account_id}")

    assert response.status_code == 200

    data = response.json()
    assert "account_id" in data
    assert "posts" in data
    assert data["account_id"] == account_id
    assert isinstance(data["posts"], list)
