# Test Achievement CRUD Operations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from services.achievement_collector.db.config import get_db
from services.achievement_collector.main import app


@pytest.fixture
def sample_achievement_data():
    """Sample achievement data for tests"""
    return {
        "title": "Implemented CI Pipeline Optimization",
        "description": "Reduced CI build time from 25 minutes to 5 minutes",
        "category": "optimization",
        "started_at": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "source_type": "manual",
        "tags": ["ci/cd", "optimization", "github-actions"],
        "skills_demonstrated": ["DevOps", "GitHub Actions", "Docker"],
    }


@pytest.fixture
def client(db_session):
    """Create test client with database session override."""

    def override():
        yield db_session

    app.dependency_overrides[get_db] = override

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


def test_create_achievement(client, sample_achievement_data):
    """Test creating a new achievement"""
    response = client.post("/achievements/", json=sample_achievement_data)

    assert response.status_code == 200
    data = response.json()

    assert data["title"] == sample_achievement_data["title"]
    assert data["category"] == sample_achievement_data["category"]
    assert data["id"] is not None
    assert data["impact_score"] == 0.0  # Default value
    assert data["portfolio_ready"] is False  # Default value


def test_list_achievements(client, sample_achievement_data):
    """Test listing achievements with pagination"""
    # Create a few achievements
    for i in range(5):
        achievement_data = sample_achievement_data.copy()
        achievement_data["title"] = f"Achievement {i}"
        client.post("/achievements/", json=achievement_data)

    # Test pagination
    response = client.get("/achievements/?page=1&per_page=3")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 5
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["per_page"] == 3


def test_get_achievement(client, sample_achievement_data):
    """Test getting a specific achievement"""
    # Create achievement
    create_response = client.post("/achievements/", json=sample_achievement_data)
    achievement_id = create_response.json()["id"]

    # Get achievement
    response = client.get(f"/achievements/{achievement_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == achievement_id
    assert data["title"] == sample_achievement_data["title"]


def test_update_achievement(client, sample_achievement_data):
    """Test updating an achievement"""
    # Create achievement
    create_response = client.post("/achievements/", json=sample_achievement_data)
    achievement_id = create_response.json()["id"]

    # Update achievement
    update_data = {
        "impact_score": 85.5,
        "complexity_score": 75.0,
        "business_value": "$50000 annual savings",
        "portfolio_ready": True,
    }

    response = client.put(f"/achievements/{achievement_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["impact_score"] == 85.5
    assert data["complexity_score"] == 75.0
    assert data["business_value"] == "$50000 annual savings"
    assert data["portfolio_ready"] is True


def test_delete_achievement(client, sample_achievement_data):
    """Test deleting an achievement"""
    # Create achievement
    create_response = client.post("/achievements/", json=sample_achievement_data)
    achievement_id = create_response.json()["id"]

    # Delete achievement
    response = client.delete(f"/achievements/{achievement_id}")
    assert response.status_code == 200

    # Verify it's deleted
    get_response = client.get(f"/achievements/{achievement_id}")
    assert get_response.status_code == 404


def test_search_achievements(client, sample_achievement_data):
    """Test searching achievements"""
    # Create achievements with different tags
    for tag in ["python", "docker", "kubernetes"]:
        data = sample_achievement_data.copy()
        data["title"] = f"Achievement with {tag}"
        data["tags"] = [tag]
        client.post("/achievements/", json=data)

    # Search by text
    response = client.get("/achievements/?search=docker")
    assert response.status_code == 200
    data = response.json()
    assert any("docker" in item["title"].lower() for item in data["items"])


def test_filter_by_category(client, sample_achievement_data):
    """Test filtering achievements by category"""
    categories = ["feature", "optimization", "bugfix"]

    for category in categories:
        data = sample_achievement_data.copy()
        data["category"] = category
        data["title"] = f"{category} achievement"
        client.post("/achievements/", json=data)

    # Filter by category
    response = client.get("/achievements/?category=optimization")
    assert response.status_code == 200
    data = response.json()
    assert all(item["category"] == "optimization" for item in data["items"])


def test_portfolio_ready_filter(client, sample_achievement_data):
    """Test filtering portfolio-ready achievements"""
    # Create mix of portfolio-ready and not ready
    for i, ready in enumerate([True, False, True, False]):
        data = sample_achievement_data.copy()
        data["title"] = f"Achievement {i}"
        create_response = client.post("/achievements/", json=data)

        if ready:
            achievement_id = create_response.json()["id"]
            client.put(
                f"/achievements/{achievement_id}", json={"portfolio_ready": True}
            )

    # Filter portfolio ready
    response = client.get("/achievements/?portfolio_ready=true")
    assert response.status_code == 200
    data = response.json()
    assert all(item["portfolio_ready"] is True for item in data["items"])


def test_phase2_threads_integration(client):
    """Test Phase 2: Threads viral post tracking"""
    post_data = {
        "hook": "Amazing CI optimization techniques!",
        "engagement_rate": 0.08,  # 8% engagement (viral)
        "views": 10000,
        "likes": 800,
        "shares": 200,
    }

    response = client.post("/threads/track", json=post_data)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "created"
    assert "achievement_id" in data

    # Verify achievement was created
    achievement_response = client.get(f"/achievements/{data['achievement_id']}")
    assert achievement_response.status_code == 200
    achievement = achievement_response.json()
    assert "Viral Post" in achievement["title"]
    assert achievement["category"] == "content"
    assert achievement["source_type"] == "threads"


def test_phase2_non_viral_post(client):
    """Test that non-viral posts are not tracked"""
    post_data = {
        "hook": "Regular post",
        "engagement_rate": 0.02,  # 2% engagement (not viral)
        "views": 100,
        "likes": 2,
        "shares": 0,
    }

    response = client.post("/threads/track", json=post_data)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "skipped"
    assert data["reason"] == "Below viral threshold"
