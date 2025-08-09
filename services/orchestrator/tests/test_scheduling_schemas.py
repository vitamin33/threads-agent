"""
Test suite for Scheduling Management API Pydantic schemas (Phase 1 of Epic 14)

This follows TDD methodology - schemas are tested first before implementation.
Testing schemas independently allows us to define the API contract first.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

# These imports will fail initially - that's expected in TDD
# We'll create these schemas step by step following the failing tests
try:
    from services.orchestrator.scheduling_schemas import (
        ContentItemCreate,
        ContentItemResponse,
        ContentItemUpdate,
        ContentScheduleCreate,
        ContentScheduleResponse,
        ContentScheduleUpdate,
        ContentStatusResponse,
        UpcomingSchedulesResponse,
        CalendarViewResponse,
        PaginatedContentResponse,
        ContentStatus,
        PlatformType,
        ContentType,
    )
except ImportError:
    # Expected failure - schemas don't exist yet
    pytest.skip("Scheduling schemas not implemented yet", allow_module_level=True)


class TestContentItemSchemas:
    """Test content item Pydantic schemas."""

    def test_content_item_create_requires_title(self):
        """ContentItemCreate should require title field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentItemCreate(
                content="Test content",
                content_type="blog_post",
                author_id="test_author",
            )

        error_data = exc_info.value.errors()
        assert any(error["loc"] == ("title",) for error in error_data)

    def test_content_item_create_requires_content(self):
        """ContentItemCreate should require content field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentItemCreate(
                title="Test Title", content_type="blog_post", author_id="test_author"
            )

        error_data = exc_info.value.errors()
        assert any(error["loc"] == ("content",) for error in error_data)

    def test_content_item_create_requires_content_type(self):
        """ContentItemCreate should require content_type field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentItemCreate(
                title="Test Title", content="Test content", author_id="test_author"
            )

        error_data = exc_info.value.errors()
        assert any(error["loc"] == ("content_type",) for error in error_data)

    def test_content_item_create_requires_author_id(self):
        """ContentItemCreate should require author_id field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentItemCreate(
                title="Test Title", content="Test content", content_type="blog_post"
            )

        error_data = exc_info.value.errors()
        assert any(error["loc"] == ("author_id",) for error in error_data)

    def test_content_item_create_valid_data(self):
        """ContentItemCreate should accept valid data."""
        item = ContentItemCreate(
            title="Advanced AI Development Techniques",
            content="A comprehensive guide to modern AI development practices.",
            content_type="blog_post",
            author_id="ai_expert_001",
            content_metadata={"tags": ["AI", "Development"], "estimated_read_time": 8},
        )

        assert item.title == "Advanced AI Development Techniques"
        assert item.content_type == "blog_post"
        assert item.author_id == "ai_expert_001"
        assert item.status == "draft"  # Should default to draft
        assert item.content_metadata["tags"] == ["AI", "Development"]

    def test_content_item_create_defaults_status_to_draft(self):
        """ContentItemCreate should default status to 'draft'."""
        item = ContentItemCreate(
            title="Test Title",
            content="Test content",
            content_type="blog_post",
            author_id="test_author",
        )

        assert item.status == "draft"

    def test_content_item_create_validates_content_type(self):
        """ContentItemCreate should validate content_type against allowed values."""
        with pytest.raises(ValidationError) as exc_info:
            ContentItemCreate(
                title="Test Title",
                content="Test content",
                content_type="invalid_type",
                author_id="test_author",
            )

        error_data = exc_info.value.errors()
        assert any("invalid_type" in str(error) for error in error_data)

    def test_content_item_create_validates_status(self):
        """ContentItemCreate should validate status against allowed values."""
        with pytest.raises(ValidationError) as exc_info:
            ContentItemCreate(
                title="Test Title",
                content="Test content",
                content_type="blog_post",
                author_id="test_author",
                status="invalid_status",
            )

        error_data = exc_info.value.errors()
        assert any("invalid_status" in str(error) for error in error_data)

    def test_content_item_response_includes_timestamps(self):
        """ContentItemResponse should include created_at and updated_at."""
        now = datetime.now(timezone.utc)

        response = ContentItemResponse(
            id=1,
            title="Test Title",
            content="Test content",
            content_type="blog_post",
            author_id="test_author",
            status="draft",
            created_at=now,
            updated_at=now,
        )

        assert response.id == 1
        assert response.created_at == now
        assert response.updated_at == now

    def test_content_item_update_all_fields_optional(self):
        """ContentItemUpdate should make all fields optional."""
        # Should not raise validation error with no fields
        update = ContentItemUpdate()
        assert update is not None

        # Should accept partial updates
        update = ContentItemUpdate(title="New Title")
        assert update.title == "New Title"
        assert update.content is None
        assert update.status is None


class TestContentScheduleSchemas:
    """Test content schedule Pydantic schemas."""

    def test_content_schedule_create_requires_content_item_id(self):
        """ContentScheduleCreate should require content_item_id."""
        with pytest.raises(ValidationError) as exc_info:
            ContentScheduleCreate(
                platform="linkedin",
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
            )

        error_data = exc_info.value.errors()
        assert any(error["loc"] == ("content_item_id",) for error in error_data)

    def test_content_schedule_create_requires_platform(self):
        """ContentScheduleCreate should require platform."""
        with pytest.raises(ValidationError) as exc_info:
            ContentScheduleCreate(
                content_item_id=1,
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
            )

        error_data = exc_info.value.errors()
        assert any(error["loc"] == ("platform",) for error in error_data)

    def test_content_schedule_create_requires_scheduled_time(self):
        """ContentScheduleCreate should require scheduled_time."""
        with pytest.raises(ValidationError) as exc_info:
            ContentScheduleCreate(content_item_id=1, platform="linkedin")

        error_data = exc_info.value.errors()
        assert any(error["loc"] == ("scheduled_time",) for error in error_data)

    def test_content_schedule_create_validates_platform(self):
        """ContentScheduleCreate should validate platform against allowed values."""
        with pytest.raises(ValidationError) as exc_info:
            ContentScheduleCreate(
                content_item_id=1,
                platform="invalid_platform",
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
            )

        error_data = exc_info.value.errors()
        assert any("invalid_platform" in str(error) for error in error_data)

    def test_content_schedule_create_defaults_timezone_to_utc(self):
        """ContentScheduleCreate should default timezone_name to UTC."""
        schedule = ContentScheduleCreate(
            content_item_id=1,
            platform="linkedin",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
        )

        assert schedule.timezone_name == "UTC"

    def test_content_schedule_create_defaults_status_to_scheduled(self):
        """ContentScheduleCreate should default status to 'scheduled'."""
        schedule = ContentScheduleCreate(
            content_item_id=1,
            platform="linkedin",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
        )

        assert schedule.status == "scheduled"

    def test_content_schedule_create_accepts_platform_config(self):
        """ContentScheduleCreate should accept platform_config as dict."""
        config = {
            "hashtags": ["#AI", "#TechLeadership"],
            "mention_users": ["@techleader"],
        }

        schedule = ContentScheduleCreate(
            content_item_id=1,
            platform="linkedin",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
            platform_config=config,
        )

        assert schedule.platform_config == config

    def test_content_schedule_response_includes_retry_fields(self):
        """ContentScheduleResponse should include retry mechanism fields."""
        now = datetime.now(timezone.utc)

        response = ContentScheduleResponse(
            id=1,
            content_item_id=1,
            platform="linkedin",
            scheduled_time=now + timedelta(hours=2),
            timezone_name="UTC",
            status="scheduled",
            retry_count=0,
            max_retries=3,
            created_at=now,
            updated_at=now,
        )

        assert response.retry_count == 0
        assert response.max_retries == 3
        assert response.next_retry_time is None

    def test_content_schedule_update_validates_status_transitions(self):
        """ContentScheduleUpdate should validate status transitions."""
        # Valid status updates should work
        update = ContentScheduleUpdate(status="published")
        assert update.status == "published"

        # Invalid status should fail
        with pytest.raises(ValidationError):
            ContentScheduleUpdate(status="invalid_status")


class TestResponseSchemas:
    """Test response schemas."""

    def test_content_status_response_structure(self):
        """ContentStatusResponse should have proper structure."""
        now = datetime.now(timezone.utc)

        status = ContentStatusResponse(
            content_id=1,
            status="draft",
            schedules=[],
            publishing_progress={
                "total_platforms": 2,
                "published_platforms": 0,
                "failed_platforms": 0,
                "scheduled_platforms": 2,
            },
            last_updated=now,
        )

        assert status.content_id == 1
        assert status.status == "draft"
        assert isinstance(status.schedules, list)
        assert status.publishing_progress["total_platforms"] == 2

    def test_paginated_content_response_structure(self):
        """PaginatedContentResponse should have proper pagination structure."""
        response = PaginatedContentResponse(items=[], total=0, page=1, size=20, pages=1)

        assert response.items == []
        assert response.total == 0
        assert response.page == 1
        assert response.size == 20
        assert response.pages == 1

    def test_upcoming_schedules_response_structure(self):
        """UpcomingSchedulesResponse should have proper structure."""
        response = UpcomingSchedulesResponse(
            schedules=[], total=0, next_24_hours=0, next_week=0
        )

        assert response.schedules == []
        assert response.total == 0
        assert response.next_24_hours == 0
        assert response.next_week == 0

    def test_calendar_view_response_structure(self):
        """CalendarViewResponse should have proper structure."""
        start_date = datetime.now(timezone.utc).date()
        end_date = start_date + timedelta(days=7)

        response = CalendarViewResponse(
            schedules=[],
            date_range={"start": start_date.isoformat(), "end": end_date.isoformat()},
            grouped_by_date={},
        )

        assert response.schedules == []
        assert "start" in response.date_range
        assert "end" in response.date_range
        assert isinstance(response.grouped_by_date, dict)


class TestEnumSchemas:
    """Test enum schemas."""

    def test_content_status_enum_values(self):
        """ContentStatus enum should have expected values."""
        # These should be valid
        assert ContentStatus.DRAFT == "draft"
        assert ContentStatus.READY == "ready"
        assert ContentStatus.SCHEDULED == "scheduled"
        assert ContentStatus.PUBLISHED == "published"
        assert ContentStatus.FAILED == "failed"

    def test_platform_type_enum_values(self):
        """PlatformType enum should have expected values."""
        # These should be valid
        assert PlatformType.LINKEDIN == "linkedin"
        assert PlatformType.TWITTER == "twitter"
        assert PlatformType.FACEBOOK == "facebook"
        assert PlatformType.INSTAGRAM == "instagram"
        assert PlatformType.DEVTO == "devto"
        assert PlatformType.MEDIUM == "medium"

    def test_content_type_enum_values(self):
        """ContentType enum should have expected values."""
        # These should be valid
        assert ContentType.BLOG_POST == "blog_post"
        assert ContentType.SOCIAL_POST == "social_post"
        assert ContentType.ARTICLE == "article"
        assert ContentType.NEWSLETTER == "newsletter"
        assert ContentType.VIDEO_SCRIPT == "video_script"


class TestValidationLogic:
    """Test custom validation logic."""

    def test_scheduled_time_must_be_future(self):
        """scheduled_time should be validated to be in the future."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)

        with pytest.raises(ValidationError) as exc_info:
            ContentScheduleCreate(
                content_item_id=1, platform="linkedin", scheduled_time=past_time
            )

        error_data = exc_info.value.errors()
        assert any("future" in str(error).lower() for error in error_data)

    def test_timezone_validation(self):
        """timezone_name should be validated against valid timezone names."""
        with pytest.raises(ValidationError) as exc_info:
            ContentScheduleCreate(
                content_item_id=1,
                platform="linkedin",
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
                timezone_name="Invalid/Timezone",
            )

        error_data = exc_info.value.errors()
        assert any("timezone" in str(error).lower() for error in error_data)

    def test_content_length_validation(self):
        """Content should have reasonable length limits."""
        # Title should not be empty or too long
        with pytest.raises(ValidationError):
            ContentItemCreate(
                title="",  # Empty title
                content="Test content",
                content_type="blog_post",
                author_id="test_author",
            )

        with pytest.raises(ValidationError):
            ContentItemCreate(
                title="x" * 501,  # Too long title (assuming 500 char limit)
                content="Test content",
                content_type="blog_post",
                author_id="test_author",
            )

    def test_content_metadata_json_validation(self):
        """content_metadata should accept valid JSON structures."""
        valid_metadata = {
            "tags": ["AI", "Development"],
            "estimated_read_time": 8,
            "target_audience": "developers",
            "seo_keywords": ["AI", "machine learning"],
        }

        item = ContentItemCreate(
            title="Test Title",
            content="Test content",
            content_type="blog_post",
            author_id="test_author",
            content_metadata=valid_metadata,
        )

        assert item.content_metadata == valid_metadata
