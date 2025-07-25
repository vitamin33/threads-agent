# Test Achievement CRUD Operations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Base
from services.achievement_collector.main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def sample_achievement_data():
    """Sample achievement data for tests"""
    return {
        "title": "Implemented CI Pipeline Optimization",
        "description": "Reduced CI build time from 25 minutes to 5 minutes",
        "category": "optimization",
        "started_at": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "duration_hours": 20,
        "source_type": "manual",
        "tags": ["ci/cd", "optimization", "github-actions"],
        "skills_demonstrated": ["DevOps", "GitHub Actions", "Docker"],
    }


def test_create_achievement(sample_achievement_data):
    """Test creating a new achievement"""
    response = client.post("/achievements/", json=sample_achievement_data)

    assert response.status_code == 200
    data = response.json()

    assert data["title"] == sample_achievement_data["title"]
    assert data["category"] == sample_achievement_data["category"]
    assert data["id"] is not None
    assert data["impact_score"] == 0.0  # Default value
    assert data["portfolio_ready"] is False  # Default value


def test_list_achievements(sample_achievement_data):
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
    assert len(data["items"]) == 3
    assert data["total"] >= 5
    assert data["page"] == 1
    assert data["per_page"] == 3


def test_get_achievement(sample_achievement_data):
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


def test_update_achievement(sample_achievement_data):
    """Test updating an achievement"""
    # Create achievement
    create_response = client.post("/achievements/", json=sample_achievement_data)
    achievement_id = create_response.json()["id"]

    # Update achievement
    update_data = {
        "impact_score": 85.5,
        "business_value": 50000,
        "portfolio_ready": True,
        "ai_summary": "Successfully optimized CI pipeline, reducing build times by 80%",
    }

    response = client.put(f"/achievements/{achievement_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["impact_score"] == 85.5
    assert float(data["business_value"]) == 50000.0
    assert data["portfolio_ready"] is True
    assert data["ai_summary"] == update_data["ai_summary"]


def test_delete_achievement(sample_achievement_data):
    """Test deleting an achievement"""
    # Create achievement
    create_response = client.post("/achievements/", json=sample_achievement_data)
    achievement_id = create_response.json()["id"]

    # Delete achievement
    response = client.delete(f"/achievements/{achievement_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # Verify it's deleted
    get_response = client.get(f"/achievements/{achievement_id}")
    assert get_response.status_code == 404


def test_achievement_stats():
    """Test achievement statistics endpoint"""
    response = client.get("/achievements/stats/summary")
    assert response.status_code == 200

    data = response.json()
    assert "total_achievements" in data
    assert "total_value_generated" in data
    assert "total_time_saved_hours" in data
    assert "average_impact_score" in data
    assert "by_category" in data


def test_filter_achievements_by_category(sample_achievement_data):
    """Test filtering achievements by category"""
    # Create achievements with different categories
    categories = ["feature", "optimization", "bugfix"]

    for category in categories:
        achievement_data = sample_achievement_data.copy()
        achievement_data["category"] = category
        achievement_data["title"] = f"{category} achievement"
        client.post("/achievements/", json=achievement_data)

    # Filter by category
    response = client.get("/achievements/?category=optimization")
    assert response.status_code == 200

    data = response.json()
    for item in data["items"]:
        assert item["category"] == "optimization"


def test_search_achievements(sample_achievement_data):
    """Test searching achievements"""
    # Create achievements with searchable content
    search_terms = ["Python optimization", "Docker deployment", "API refactoring"]

    for term in search_terms:
        achievement_data = sample_achievement_data.copy()
        achievement_data["title"] = term
        client.post("/achievements/", json=achievement_data)

    # Search
    response = client.get("/achievements/?search=Docker")
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) >= 1
    assert "Docker" in data["items"][0]["title"]
