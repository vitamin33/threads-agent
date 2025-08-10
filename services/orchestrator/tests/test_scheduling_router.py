"""
Test suite for Scheduling Management API Router (Phase 1 of Epic 14)

This tests the actual FastAPI router implementation using dependency injection
to mock database operations. Tests focus on endpoint behavior and validation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.orm import Session

from services.orchestrator.scheduling_router import router
from services.orchestrator.db import get_db_session
from services.orchestrator.db.models import ContentItem, ContentSchedule


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def app_with_router(mock_db):
    """FastAPI app with our router and mocked database."""
    app = FastAPI()
    app.include_router(router)

    # Override the database dependency
    app.dependency_overrides[get_db_session] = lambda: mock_db

    return app


@pytest.fixture
def client(app_with_router):
    """Test client with mocked dependencies."""
    return TestClient(app_with_router)


@pytest.fixture
def sample_content_item():
    """Sample content item for testing."""
    item = Mock(spec=ContentItem)
    item.id = 1
    item.title = "Advanced AI Development Techniques"
    item.content = "A comprehensive guide to modern AI development practices."
    item.content_type = "blog_post"
    item.author_id = "ai_expert_001"
    item.status = "draft"
    item.slug = None
    item.content_metadata = {}
    item.created_at = datetime.now(timezone.utc)
    item.updated_at = datetime.now(timezone.utc)
    return item


@pytest.fixture
def sample_schedule():
    """Sample schedule for testing."""
    schedule = Mock(spec=ContentSchedule)
    schedule.id = 1
    schedule.content_item_id = 1
    schedule.platform = "linkedin"
    schedule.scheduled_time = datetime.now(timezone.utc) + timedelta(hours=2)
    schedule.timezone_name = "UTC"
    schedule.status = "scheduled"
    schedule.retry_count = 0
    schedule.max_retries = 3
    schedule.next_retry_time = None
    schedule.platform_config = {}
    schedule.published_at = None
    schedule.error_message = None
    schedule.created_at = datetime.now(timezone.utc)
    schedule.updated_at = datetime.now(timezone.utc)
    return schedule


class TestContentManagementEndpoints:
    """Test content CRUD operations."""

    def test_create_content_item_success(self, client, mock_db, sample_content_item):
        """POST /api/v1/content should create content and return 201."""
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda obj: setattr(obj, "id", 1) or obj)
        mock_db.rollback = Mock()

        # Mock the created content item
        def mock_refresh(obj):
            obj.id = 1
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)

        mock_db.refresh.side_effect = mock_refresh

        # Test data
        content_data = {
            "title": "Advanced AI Development Techniques",
            "content": "A comprehensive guide to modern AI development practices.",
            "content_type": "blog_post",
            "author_id": "ai_expert_001",
        }

        response = client.post("/api/v1/content", json=content_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == content_data["title"]
        assert data["content"] == content_data["content"]
        assert data["status"] == "draft"

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_content_item_validation_error(self, client, mock_db):
        """POST /api/v1/content should return 422 for invalid data."""
        # Missing required field
        invalid_data = {
            "content": "Test content",
            "content_type": "blog_post",
            "author_id": "test_author",
            # Missing title
        }

        response = client.post("/api/v1/content", json=invalid_data)

        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_get_content_list_success(self, client, mock_db, sample_content_item):
        """GET /api/v1/content should return paginated content list."""
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_content_item]
        mock_query.count.return_value = 1

        mock_db.query.return_value = mock_query

        response = client.get("/api/v1/content")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_get_content_list_with_filters(self, client, mock_db, sample_content_item):
        """GET /api/v1/content should support filtering."""
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_content_item]
        mock_query.count.return_value = 1

        mock_db.query.return_value = mock_query

        response = client.get("/api/v1/content?status=draft&author_id=test_author")

        assert response.status_code == 200
        # Verify filters were applied (mock was called with filter)
        assert mock_query.filter.call_count >= 2  # At least 2 filters applied

    def test_get_content_item_by_id_success(self, client, mock_db, sample_content_item):
        """GET /api/v1/content/{id} should return content when exists."""
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_content_item
        mock_db.query.return_value = mock_query

        response = client.get("/api/v1/content/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == sample_content_item.title

    def test_get_content_item_by_id_not_found(self, client, mock_db):
        """GET /api/v1/content/{id} should return 404 when not exists."""
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        response = client.get("/api/v1/content/999")

        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["detail"].lower()

    def test_update_content_item_success(self, client, mock_db, sample_content_item):
        """PUT /api/v1/content/{id} should update content."""
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_content_item
        mock_db.query.return_value = mock_query
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        mock_db.rollback = Mock()

        update_data = {"title": "Updated AI Development Techniques", "status": "ready"}

        response = client.put("/api/v1/content/1", json=update_data)

        assert response.status_code == 200
        mock_db.commit.assert_called_once()

    def test_update_content_item_not_found(self, client, mock_db):
        """PUT /api/v1/content/{id} should return 404 when not exists."""
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        update_data = {"title": "Updated Title"}

        response = client.put("/api/v1/content/999", json=update_data)

        assert response.status_code == 404

    def test_delete_content_item_success(self, client, mock_db, sample_content_item):
        """DELETE /api/v1/content/{id} should delete content."""
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_content_item
        mock_db.query.return_value = mock_query
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        mock_db.rollback = Mock()

        response = client.delete("/api/v1/content/1")

        assert response.status_code == 204
        mock_db.delete.assert_called_once_with(sample_content_item)
        mock_db.commit.assert_called_once()

    def test_delete_content_item_not_found(self, client, mock_db):
        """DELETE /api/v1/content/{id} should return 404 when not exists."""
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        response = client.delete("/api/v1/content/999")

        assert response.status_code == 404


class TestSchedulingEndpoints:
    """Test scheduling operations."""

    def test_create_schedule_success(
        self, client, mock_db, sample_content_item, sample_schedule
    ):
        """POST /api/v1/schedules should create schedule."""
        # Mock content exists query
        content_query = Mock()
        content_query.filter.return_value = content_query
        content_query.first.return_value = sample_content_item

        # Mock schedule creation
        mock_db.query.return_value = content_query
        mock_db.add = Mock()
        mock_db.commit = Mock()

        def mock_refresh(obj):
            obj.id = 1
            obj.retry_count = 0
            obj.max_retries = 3
            obj.next_retry_time = None
            obj.published_at = None
            obj.error_message = None
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)

        mock_db.refresh = Mock(side_effect=mock_refresh)
        mock_db.rollback = Mock()

        schedule_data = {
            "content_item_id": 1,
            "platform": "linkedin",
            "scheduled_time": (
                datetime.now(timezone.utc) + timedelta(hours=2)
            ).isoformat(),
        }

        response = client.post("/api/v1/schedules", json=schedule_data)

        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["platform"] == "linkedin"
        assert data["status"] == "scheduled"

    def test_create_schedule_content_not_found(self, client, mock_db):
        """POST /api/v1/schedules should return 400 when content doesn't exist."""
        # Mock content not found
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        schedule_data = {
            "content_item_id": 999,
            "platform": "linkedin",
            "scheduled_time": (
                datetime.now(timezone.utc) + timedelta(hours=2)
            ).isoformat(),
        }

        response = client.post("/api/v1/schedules", json=schedule_data)

        assert response.status_code == 400
        error_data = response.json()
        assert "content" in error_data["detail"].lower()

    def test_create_schedule_validation_error(self, client, mock_db):
        """POST /api/v1/schedules should return 422 for past time."""
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        schedule_data = {
            "content_item_id": 1,
            "platform": "linkedin",
            "scheduled_time": past_time,
        }

        response = client.post("/api/v1/schedules", json=schedule_data)

        assert response.status_code == 422

    def test_get_schedules_calendar_success(self, client, mock_db, sample_schedule):
        """GET /api/v1/schedules/calendar should return calendar view."""
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_schedule]

        mock_db.query.return_value = mock_query

        response = client.get("/api/v1/schedules/calendar")

        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert "date_range" in data
        assert "grouped_by_date" in data

    def test_update_schedule_success(self, client, mock_db, sample_schedule):
        """PUT /api/v1/schedules/{id} should update schedule."""
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_schedule
        mock_db.query.return_value = mock_query
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        mock_db.rollback = Mock()

        update_data = {"platform": "twitter"}

        response = client.put("/api/v1/schedules/1", json=update_data)

        assert response.status_code == 200
        mock_db.commit.assert_called_once()

    def test_delete_schedule_success(self, client, mock_db, sample_schedule):
        """DELETE /api/v1/schedules/{id} should delete schedule."""
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_schedule
        mock_db.query.return_value = mock_query
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        mock_db.rollback = Mock()

        response = client.delete("/api/v1/schedules/1")

        assert response.status_code == 204
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()


class TestRealTimeStatusEndpoints:
    """Test real-time status endpoints."""

    def test_get_content_status_success(
        self, client, mock_db, sample_content_item, sample_schedule
    ):
        """GET /api/v1/content/{id}/status should return status."""
        # Mock content query
        content_query = Mock()
        content_query.filter.return_value = content_query
        content_query.first.return_value = sample_content_item

        # Mock schedules query
        schedule_query = Mock()
        schedule_query.filter.return_value = schedule_query
        schedule_query.all.return_value = [sample_schedule]

        # Setup query routing
        def mock_query(model):
            if model == ContentItem:
                return content_query
            elif model == ContentSchedule:
                return schedule_query
            return Mock()

        mock_db.query.side_effect = mock_query

        response = client.get("/api/v1/content/1/status")

        assert response.status_code == 200
        data = response.json()
        assert data["content_id"] == 1
        assert "status" in data
        assert "schedules" in data
        assert "publishing_progress" in data

    def test_get_content_status_not_found(self, client, mock_db):
        """GET /api/v1/content/{id}/status should return 404 when not exists."""
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        response = client.get("/api/v1/content/999/status")

        assert response.status_code == 404

    def test_get_upcoming_schedules_success(self, client, mock_db, sample_schedule):
        """GET /api/v1/schedules/upcoming should return upcoming schedules."""
        # Mock upcoming schedules query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_schedule]

        # Mock count queries
        mock_count_query = Mock()
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.count.return_value = 1

        # Route queries properly
        call_count = 0

        def mock_query_router(model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call for main query
                return mock_query
            else:  # Subsequent calls for counts
                return mock_count_query

        mock_db.query.side_effect = mock_query_router

        response = client.get("/api/v1/schedules/upcoming")

        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert "total" in data
        assert "next_24_hours" in data
        assert "next_week" in data

    def test_get_upcoming_schedules_with_filters(
        self, client, mock_db, sample_schedule
    ):
        """GET /api/v1/schedules/upcoming should support platform filtering."""
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_schedule]

        # Mock count query
        mock_count_query = Mock()
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.count.return_value = 1

        call_count = 0

        def mock_query_router(model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_query
            else:
                return mock_count_query

        mock_db.query.side_effect = mock_query_router

        response = client.get("/api/v1/schedules/upcoming?platform=linkedin&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["schedules"]) <= 10
