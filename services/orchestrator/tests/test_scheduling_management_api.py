"""
Test suite for Scheduling Management API endpoints (Phase 1 of Epic 14)

This follows TDD methodology - all tests are written first and should FAIL
before implementation begins.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# These imports will fail initially - that's expected in TDD
from services.orchestrator.main import app
from services.orchestrator.db.models import ContentItem, ContentSchedule, ContentAnalytics


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_content_item_data():
    """Sample content item for testing."""
    return {
        "title": "Advanced AI Development Techniques",
        "content": "A comprehensive guide to modern AI development practices and techniques that every developer should know.",
        "content_type": "blog_post",
        "author_id": "ai_expert_001",
        "status": "draft",
        "content_metadata": {
            "tags": ["AI", "Development", "Machine Learning"],
            "estimated_read_time": 8,
            "target_audience": "developers"
        }
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for testing."""
    return {
        "platform": "linkedin",
        "scheduled_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "timezone_name": "UTC",
        "platform_config": {
            "hashtags": ["#AI", "#TechLeadership"],
            "mention_users": ["@techleader"]
        }
    }


class TestContentManagementEndpoints:
    """Test content CRUD operations."""

    def test_create_content_item_returns_201_with_id(self, client, sample_content_item_data):
        """POST /api/v1/content should create new content and return 201 with ID."""
        # This will fail - endpoint doesn't exist yet
        response = client.post("/api/v1/content", json=sample_content_item_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == sample_content_item_data["title"]
        assert data["content"] == sample_content_item_data["content"]
        assert data["status"] == "draft"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_content_item_requires_title(self, client, sample_content_item_data):
        """POST /api/v1/content should return 422 when title is missing."""
        invalid_data = sample_content_item_data.copy()
        del invalid_data["title"]
        
        response = client.post("/api/v1/content", json=invalid_data)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "title" in str(error_data)

    def test_create_content_item_requires_content(self, client, sample_content_item_data):
        """POST /api/v1/content should return 422 when content is missing."""
        invalid_data = sample_content_item_data.copy()
        del invalid_data["content"]
        
        response = client.post("/api/v1/content", json=invalid_data)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "content" in str(error_data)

    def test_get_content_list_returns_200_with_pagination(self, client):
        """GET /api/v1/content should return paginated list of content."""
        response = client.get("/api/v1/content")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert isinstance(data["items"], list)

    def test_get_content_list_supports_filtering_by_status(self, client):
        """GET /api/v1/content should support filtering by status."""
        response = client.get("/api/v1/content?status=draft")
        
        assert response.status_code == 200
        data = response.json()
        # All returned items should have draft status
        for item in data["items"]:
            assert item["status"] == "draft"

    def test_get_content_list_supports_filtering_by_author(self, client):
        """GET /api/v1/content should support filtering by author_id."""
        response = client.get("/api/v1/content?author_id=test_author")
        
        assert response.status_code == 200
        data = response.json()
        # All returned items should have the specified author
        for item in data["items"]:
            assert item["author_id"] == "test_author"

    def test_get_content_by_id_returns_200_when_exists(self, client, sample_content_item_data):
        """GET /api/v1/content/{id} should return content when it exists."""
        # First create content
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/content/{content_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content_id
        assert data["title"] == sample_content_item_data["title"]

    def test_get_content_by_id_returns_404_when_not_exists(self, client):
        """GET /api/v1/content/{id} should return 404 when content doesn't exist."""
        response = client.get("/api/v1/content/99999")
        
        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["detail"].lower()

    def test_update_content_item_returns_200_with_updated_data(self, client, sample_content_item_data):
        """PUT /api/v1/content/{id} should update content and return updated data."""
        # First create content
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        # Update the content
        update_data = {
            "title": "Updated AI Development Techniques",
            "status": "ready"
        }
        
        response = client.put(f"/api/v1/content/{content_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content_id
        assert data["title"] == update_data["title"]
        assert data["status"] == update_data["status"]
        # Original content should remain unchanged
        assert data["content"] == sample_content_item_data["content"]

    def test_update_content_item_returns_404_when_not_exists(self, client):
        """PUT /api/v1/content/{id} should return 404 when content doesn't exist."""
        update_data = {"title": "Updated Title"}
        
        response = client.put("/api/v1/content/99999", json=update_data)
        
        assert response.status_code == 404

    def test_delete_content_item_returns_204(self, client, sample_content_item_data):
        """DELETE /api/v1/content/{id} should delete content and return 204."""
        # First create content
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        # Delete the content
        response = client.delete(f"/api/v1/content/{content_id}")
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/content/{content_id}")
        assert get_response.status_code == 404

    def test_delete_content_item_returns_404_when_not_exists(self, client):
        """DELETE /api/v1/content/{id} should return 404 when content doesn't exist."""
        response = client.delete("/api/v1/content/99999")
        
        assert response.status_code == 404


class TestSchedulingManagementEndpoints:
    """Test scheduling operations."""

    def test_create_schedule_returns_201_with_schedule_data(self, client, sample_content_item_data, sample_schedule_data):
        """POST /api/v1/schedules should create schedule and return 201."""
        # First create content
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        # Create schedule for the content
        schedule_data = sample_schedule_data.copy()
        schedule_data["content_item_id"] = content_id
        
        response = client.post("/api/v1/schedules", json=schedule_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["content_item_id"] == content_id
        assert data["platform"] == sample_schedule_data["platform"]
        assert data["status"] == "scheduled"
        assert "created_at" in data

    def test_create_schedule_validates_content_exists(self, client, sample_schedule_data):
        """POST /api/v1/schedules should return 400 when content_item_id doesn't exist."""
        schedule_data = sample_schedule_data.copy()
        schedule_data["content_item_id"] = 99999  # Non-existent content
        
        response = client.post("/api/v1/schedules", json=schedule_data)
        
        assert response.status_code == 400
        error_data = response.json()
        assert "content" in error_data["detail"].lower()

    def test_create_schedule_validates_future_time(self, client, sample_content_item_data, sample_schedule_data):
        """POST /api/v1/schedules should return 400 when scheduled_time is in the past."""
        # First create content
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        # Try to schedule in the past
        schedule_data = sample_schedule_data.copy()
        schedule_data["content_item_id"] = content_id
        schedule_data["scheduled_time"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        response = client.post("/api/v1/schedules", json=schedule_data)
        
        assert response.status_code == 400
        error_data = response.json()
        assert "future" in error_data["detail"].lower()

    def test_get_schedules_calendar_returns_200_with_schedule_data(self, client):
        """GET /api/v1/schedules/calendar should return calendar view of schedules."""
        response = client.get("/api/v1/schedules/calendar")
        
        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert "date_range" in data
        assert isinstance(data["schedules"], list)

    def test_get_schedules_calendar_supports_date_range_filtering(self, client):
        """GET /api/v1/schedules/calendar should support date range filtering."""
        start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        end_date = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = client.get(f"/api/v1/schedules/calendar?start_date={start_date}&end_date={end_date}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["date_range"]["start"] == start_date
        assert data["date_range"]["end"] == end_date

    def test_update_schedule_returns_200_with_updated_data(self, client, sample_content_item_data, sample_schedule_data):
        """PUT /api/v1/schedules/{id} should update schedule and return updated data."""
        # Create content and schedule
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        schedule_data = sample_schedule_data.copy()
        schedule_data["content_item_id"] = content_id
        
        schedule_response = client.post("/api/v1/schedules", json=schedule_data)
        schedule_id = schedule_response.json()["id"]
        
        # Update the schedule
        update_data = {
            "scheduled_time": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
            "platform": "twitter"
        }
        
        response = client.put(f"/api/v1/schedules/{schedule_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == schedule_id
        assert data["platform"] == update_data["platform"]

    def test_update_schedule_returns_404_when_not_exists(self, client):
        """PUT /api/v1/schedules/{id} should return 404 when schedule doesn't exist."""
        update_data = {"platform": "twitter"}
        
        response = client.put("/api/v1/schedules/99999", json=update_data)
        
        assert response.status_code == 404

    def test_delete_schedule_returns_204(self, client, sample_content_item_data, sample_schedule_data):
        """DELETE /api/v1/schedules/{id} should cancel schedule and return 204."""
        # Create content and schedule
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        schedule_data = sample_schedule_data.copy()
        schedule_data["content_item_id"] = content_id
        
        schedule_response = client.post("/api/v1/schedules", json=schedule_data)
        schedule_id = schedule_response.json()["id"]
        
        # Delete the schedule
        response = client.delete(f"/api/v1/schedules/{schedule_id}")
        
        assert response.status_code == 204

    def test_delete_schedule_returns_404_when_not_exists(self, client):
        """DELETE /api/v1/schedules/{id} should return 404 when schedule doesn't exist."""
        response = client.delete("/api/v1/schedules/99999")
        
        assert response.status_code == 404


class TestRealTimeStatusEndpoints:
    """Test real-time status monitoring."""

    def test_get_content_status_returns_200_with_status_data(self, client, sample_content_item_data):
        """GET /api/v1/content/{id}/status should return publishing status."""
        # Create content
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/content/{content_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "content_id" in data
        assert "status" in data
        assert "schedules" in data
        assert "publishing_progress" in data
        assert isinstance(data["schedules"], list)

    def test_get_content_status_returns_404_when_not_exists(self, client):
        """GET /api/v1/content/{id}/status should return 404 when content doesn't exist."""
        response = client.get("/api/v1/content/99999/status")
        
        assert response.status_code == 404

    def test_get_upcoming_schedules_returns_200_with_schedule_list(self, client):
        """GET /api/v1/schedules/upcoming should return upcoming scheduled content."""
        response = client.get("/api/v1/schedules/upcoming")
        
        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert "total" in data
        assert isinstance(data["schedules"], list)

    def test_get_upcoming_schedules_supports_limit_parameter(self, client):
        """GET /api/v1/schedules/upcoming should support limit parameter."""
        response = client.get("/api/v1/schedules/upcoming?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["schedules"]) <= 5

    def test_get_upcoming_schedules_supports_platform_filtering(self, client):
        """GET /api/v1/schedules/upcoming should support platform filtering."""
        response = client.get("/api/v1/schedules/upcoming?platform=linkedin")
        
        assert response.status_code == 200
        data = response.json()
        # All returned schedules should be for LinkedIn
        for schedule in data["schedules"]:
            assert schedule["platform"] == "linkedin"


class TestValidationAndErrorHandling:
    """Test validation and error scenarios."""

    def test_invalid_content_type_returns_422(self, client, sample_content_item_data):
        """POST /api/v1/content should return 422 for invalid content_type."""
        invalid_data = sample_content_item_data.copy()
        invalid_data["content_type"] = "invalid_type"
        
        response = client.post("/api/v1/content", json=invalid_data)
        
        assert response.status_code == 422

    def test_invalid_platform_returns_422(self, client, sample_content_item_data, sample_schedule_data):
        """POST /api/v1/schedules should return 422 for invalid platform."""
        # Create content first
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        invalid_schedule = sample_schedule_data.copy()
        invalid_schedule["content_item_id"] = content_id
        invalid_schedule["platform"] = "invalid_platform"
        
        response = client.post("/api/v1/schedules", json=invalid_schedule)
        
        assert response.status_code == 422

    def test_invalid_timezone_returns_422(self, client, sample_content_item_data, sample_schedule_data):
        """POST /api/v1/schedules should return 422 for invalid timezone."""
        # Create content first
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        invalid_schedule = sample_schedule_data.copy()
        invalid_schedule["content_item_id"] = content_id  
        invalid_schedule["timezone_name"] = "Invalid/Timezone"
        
        response = client.post("/api/v1/schedules", json=invalid_schedule)
        
        assert response.status_code == 422

    def test_malformed_json_returns_422(self, client):
        """API should return 422 for malformed JSON."""
        response = client.post(
            "/api/v1/content", 
            data='{"title": "Test", invalid json}',
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization (basic setup for JWT)."""

    @pytest.mark.skip(reason="JWT authentication not implemented yet")
    def test_unauthenticated_request_returns_401(self, client):
        """API should return 401 for unauthenticated requests."""
        response = client.get("/api/v1/content")
        
        assert response.status_code == 401

    @pytest.mark.skip(reason="JWT authentication not implemented yet")
    def test_invalid_token_returns_401(self, client):
        """API should return 401 for invalid JWT token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/content", headers=headers)
        
        assert response.status_code == 401

    @pytest.mark.skip(reason="Authorization not implemented yet")
    def test_unauthorized_user_cannot_modify_others_content(self, client):
        """Users should not be able to modify content they don't own."""
        # This test will be implemented when user ownership is added
        pass


# Integration tests that require database
@pytest.mark.e2e
class TestSchedulingManagementIntegration:
    """Integration tests using real database operations."""

    def test_end_to_end_content_lifecycle(self, client, sample_content_item_data, sample_schedule_data):
        """Test complete content lifecycle: create -> schedule -> publish -> analyze."""
        # 1. Create content
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        assert create_response.status_code == 201
        content_id = create_response.json()["id"]
        
        # 2. Schedule content
        schedule_data = sample_schedule_data.copy()
        schedule_data["content_item_id"] = content_id
        
        schedule_response = client.post("/api/v1/schedules", json=schedule_data)
        assert schedule_response.status_code == 201
        schedule_id = schedule_response.json()["id"]
        
        # 3. Check status
        status_response = client.get(f"/api/v1/content/{content_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert len(status_data["schedules"]) == 1
        assert status_data["schedules"][0]["id"] == schedule_id
        
        # 4. Verify in calendar
        calendar_response = client.get("/api/v1/schedules/calendar")
        assert calendar_response.status_code == 200
        calendar_data = calendar_response.json()
        schedule_found = any(s["id"] == schedule_id for s in calendar_data["schedules"])
        assert schedule_found
        
        # 5. Update content
        update_data = {"status": "ready"}
        update_response = client.put(f"/api/v1/content/{content_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "ready"

    def test_cascade_delete_schedules_when_content_deleted(self, client, sample_content_item_data, sample_schedule_data):
        """Deleting content should cascade delete its schedules."""
        # Create content and schedule
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        schedule_data = sample_schedule_data.copy()
        schedule_data["content_item_id"] = content_id
        
        schedule_response = client.post("/api/v1/schedules", json=schedule_data)
        schedule_id = schedule_response.json()["id"]
        
        # Delete content
        delete_response = client.delete(f"/api/v1/content/{content_id}")
        assert delete_response.status_code == 204
        
        # Verify schedules are also deleted
        calendar_response = client.get("/api/v1/schedules/calendar")
        calendar_data = calendar_response.json()
        schedule_found = any(s["id"] == schedule_id for s in calendar_data["schedules"])
        assert not schedule_found

    def test_concurrent_schedule_creation_for_same_content(self, client, sample_content_item_data, sample_schedule_data):
        """Multiple schedules can be created for the same content on different platforms."""
        # Create content
        create_response = client.post("/api/v1/content", json=sample_content_item_data)
        content_id = create_response.json()["id"]
        
        # Create multiple schedules for different platforms
        platforms = ["linkedin", "twitter", "facebook"]
        schedule_ids = []
        
        for platform in platforms:
            schedule_data = sample_schedule_data.copy()
            schedule_data["content_item_id"] = content_id
            schedule_data["platform"] = platform
            schedule_data["scheduled_time"] = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
            
            response = client.post("/api/v1/schedules", json=schedule_data)
            assert response.status_code == 201
            schedule_ids.append(response.json()["id"])
        
        # Verify all schedules exist
        status_response = client.get(f"/api/v1/content/{content_id}/status")
        status_data = status_response.json()
        assert len(status_data["schedules"]) == 3
        
        returned_schedule_ids = [s["id"] for s in status_data["schedules"]]
        assert set(schedule_ids) == set(returned_schedule_ids)