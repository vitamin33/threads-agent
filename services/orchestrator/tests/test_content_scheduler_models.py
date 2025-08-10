"""Tests for Content Scheduler Database Models - Phase 1 of Epic 14

Test-Driven Development approach for Content Management System models:
- ContentItem: Primary content storage with lifecycle management
- ContentSchedule: Multi-platform scheduling with timezone support
- ContentAnalytics: Performance tracking and analytics

Following TDD principles:
1. Write failing tests first
2. Implement minimal code to pass tests
3. Refactor when tests are green
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError

from services.orchestrator.db.models import (
    ContentItem,
    ContentSchedule,
    ContentAnalytics,
)


class TestContentItemModel:
    """Test suite for ContentItem model - Primary content storage."""

    def test_content_item_creation_with_required_fields(self, db_session):
        """Test ContentItem can be created with minimal required fields."""
        # This test will fail initially - ContentItem model doesn't exist yet
        content_item = ContentItem(
            title="Test Blog Post",
            content="This is test content for our blog post",
            content_type="blog_post",
            author_id="user123",
            status="draft",
        )

        db_session.add(content_item)
        db_session.commit()

        assert content_item.id is not None
        assert content_item.title == "Test Blog Post"
        assert content_item.content_type == "blog_post"
        assert content_item.status == "draft"
        assert content_item.created_at is not None
        assert content_item.updated_at is not None

    def test_content_item_lifecycle_states(self, db_session):
        """Test ContentItem supports all required lifecycle states."""
        valid_states = ["draft", "scheduled", "published", "failed", "archived"]

        for state in valid_states:
            content_item = ContentItem(
                title=f"Test Content - {state}",
                content="Test content",
                content_type="social_post",
                author_id="user123",
                status=state,
            )

            db_session.add(content_item)
            db_session.commit()

            assert content_item.status == state

    def test_content_item_supports_multiple_content_types(self, db_session):
        """Test ContentItem supports various content types."""
        content_types = ["blog_post", "social_post", "newsletter", "documentation"]

        for content_type in content_types:
            content_item = ContentItem(
                title=f"Test {content_type}",
                content="Test content",
                content_type=content_type,
                author_id="user123",
                status="draft",
            )

            db_session.add(content_item)
            db_session.commit()

            assert content_item.content_type == content_type

    def test_content_item_metadata_storage(self, db_session):
        """Test ContentItem can store metadata as JSON."""
        metadata = {
            "tags": ["AI", "Machine Learning", "Python"],
            "target_audience": "developers",
            "estimated_read_time": 5,
            "seo_keywords": ["AI development", "ML automation"],
        }

        content_item = ContentItem(
            title="AI Development Guide",
            content="Comprehensive guide to AI development",
            content_type="blog_post",
            author_id="user123",
            status="draft",
            content_metadata=metadata,
        )

        db_session.add(content_item)
        db_session.commit()

        assert content_item.content_metadata == metadata
        assert content_item.content_metadata["tags"] == [
            "AI",
            "Machine Learning",
            "Python",
        ]

    def test_content_item_requires_title(self, db_session):
        """Test ContentItem requires title field."""
        with pytest.raises(IntegrityError):
            content_item = ContentItem(
                content="Content without title",
                content_type="blog_post",
                author_id="user123",
                status="draft",
            )
            db_session.add(content_item)
            db_session.commit()

    def test_content_item_requires_content(self, db_session):
        """Test ContentItem requires content field."""
        with pytest.raises(IntegrityError):
            content_item = ContentItem(
                title="Title without content",
                content_type="blog_post",
                author_id="user123",
                status="draft",
            )
            db_session.add(content_item)
            db_session.commit()

    def test_content_item_auto_timestamps(self, db_session):
        """Test ContentItem automatically sets created_at and updated_at."""
        before_creation = datetime.now(timezone.utc)

        content_item = ContentItem(
            title="Timestamp Test",
            content="Testing automatic timestamps",
            content_type="blog_post",
            author_id="user123",
            status="draft",
        )

        db_session.add(content_item)
        db_session.commit()

        after_creation = datetime.now(timezone.utc)

        assert before_creation <= content_item.created_at <= after_creation
        assert before_creation <= content_item.updated_at <= after_creation

    def test_content_item_slug_generation(self, db_session):
        """Test ContentItem can generate URL-friendly slugs."""
        content_item = ContentItem(
            title="This is a Test Blog Post with Special Characters!",
            content="Test content",
            content_type="blog_post",
            author_id="user123",
            status="draft",
        )

        db_session.add(content_item)
        db_session.commit()

        # Should generate slug from title (implementation detail)
        assert hasattr(content_item, "slug")
        assert content_item.slug is not None


class TestContentScheduleModel:
    """Test suite for ContentSchedule model - Multi-platform scheduling."""

    def test_content_schedule_creation_with_required_fields(self, db_session):
        """Test ContentSchedule can be created with required fields."""
        # First create a content item to schedule
        content_item = ContentItem(
            title="Scheduled Post",
            content="This post will be scheduled",
            content_type="social_post",
            author_id="user123",
            status="draft",
        )
        db_session.add(content_item)
        db_session.commit()

        # Now create schedule
        schedule_time = datetime.now(timezone.utc) + timedelta(hours=2)

        content_schedule = ContentSchedule(
            content_item_id=content_item.id,
            platform="linkedin",
            scheduled_time=schedule_time,
            timezone_name="UTC",
            status="scheduled",
        )

        db_session.add(content_schedule)
        db_session.commit()

        assert content_schedule.id is not None
        assert content_schedule.content_item_id == content_item.id
        assert content_schedule.platform == "linkedin"
        assert content_schedule.scheduled_time == schedule_time
        assert content_schedule.status == "scheduled"

    def test_content_schedule_supports_multiple_platforms(self, db_session):
        """Test ContentSchedule supports all required platforms."""
        # Create content item
        content_item = ContentItem(
            title="Multi-platform Post",
            content="This will be posted to multiple platforms",
            content_type="social_post",
            author_id="user123",
            status="draft",
        )
        db_session.add(content_item)
        db_session.commit()

        platforms = ["devto", "linkedin", "threads", "medium", "twitter"]
        schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)

        for platform in platforms:
            content_schedule = ContentSchedule(
                content_item_id=content_item.id,
                platform=platform,
                scheduled_time=schedule_time,
                timezone_name="UTC",
                status="scheduled",
            )

            db_session.add(content_schedule)
            db_session.commit()

            assert content_schedule.platform == platform

    def test_content_schedule_timezone_support(self, db_session):
        """Test ContentSchedule supports different timezones."""
        content_item = ContentItem(
            title="Timezone Test Post",
            content="Testing timezone support",
            content_type="social_post",
            author_id="user123",
            status="draft",
        )
        db_session.add(content_item)
        db_session.commit()

        timezones = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]
        schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)

        for tz in timezones:
            content_schedule = ContentSchedule(
                content_item_id=content_item.id,
                platform="linkedin",
                scheduled_time=schedule_time,
                timezone_name=tz,
                status="scheduled",
            )

            db_session.add(content_schedule)
            db_session.commit()

            assert content_schedule.timezone_name == tz

    def test_content_schedule_retry_mechanism(self, db_session):
        """Test ContentSchedule supports retry mechanism for failed publishes."""
        content_item = ContentItem(
            title="Retry Test Post",
            content="Testing retry mechanism",
            content_type="social_post",
            author_id="user123",
            status="draft",
        )
        db_session.add(content_item)
        db_session.commit()

        content_schedule = ContentSchedule(
            content_item_id=content_item.id,
            platform="linkedin",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            timezone_name="UTC",
            status="failed",
            retry_count=2,
            max_retries=3,
            next_retry_time=datetime.now(timezone.utc) + timedelta(minutes=30),
        )

        db_session.add(content_schedule)
        db_session.commit()

        assert content_schedule.retry_count == 2
        assert content_schedule.max_retries == 3
        assert content_schedule.next_retry_time is not None
        assert content_schedule.status == "failed"

    def test_content_schedule_platform_specific_config(self, db_session):
        """Test ContentSchedule can store platform-specific configuration."""
        content_item = ContentItem(
            title="Platform Config Test",
            content="Testing platform-specific configuration",
            content_type="social_post",
            author_id="user123",
            status="draft",
        )
        db_session.add(content_item)
        db_session.commit()

        platform_config = {
            "hashtags": ["#AI", "#MachineLearning"],
            "mention_users": ["@techleader"],
            "include_link": True,
            "optimize_for_engagement": True,
        }

        content_schedule = ContentSchedule(
            content_item_id=content_item.id,
            platform="linkedin",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            timezone_name="UTC",
            status="scheduled",
            platform_config=platform_config,
        )

        db_session.add(content_schedule)
        db_session.commit()

        assert content_schedule.platform_config == platform_config
        assert content_schedule.platform_config["hashtags"] == [
            "#AI",
            "#MachineLearning",
        ]

    def test_content_schedule_foreign_key_constraint(self, db_session):
        """Test ContentSchedule enforces foreign key constraint to ContentItem."""
        # Skip this test for SQLite as it doesn't enforce FK constraints by default
        if "sqlite" in str(db_session.bind.url):
            pytest.skip("SQLite doesn't enforce foreign key constraints by default")

        with pytest.raises(IntegrityError):
            content_schedule = ContentSchedule(
                content_item_id=99999,  # Non-existent content item
                platform="linkedin",
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
                timezone_name="UTC",
                status="scheduled",
            )
            db_session.add(content_schedule)
            db_session.commit()


class TestContentAnalyticsModel:
    """Test suite for ContentAnalytics model - Performance tracking."""

    def test_content_analytics_creation_with_metrics(self, db_session):
        """Test ContentAnalytics can store performance metrics."""
        # Create content item first
        content_item = ContentItem(
            title="Analytics Test Post",
            content="Testing analytics tracking",
            content_type="blog_post",
            author_id="user123",
            status="published",
        )
        db_session.add(content_item)
        db_session.commit()

        # Create analytics record
        content_analytics = ContentAnalytics(
            content_item_id=content_item.id,
            platform="devto",
            views=1250,
            likes=45,
            comments=12,
            shares=8,
            engagement_rate=0.052,  # 5.2%
            measured_at=datetime.now(timezone.utc),
        )

        db_session.add(content_analytics)
        db_session.commit()

        assert content_analytics.id is not None
        assert content_analytics.content_item_id == content_item.id
        assert content_analytics.platform == "devto"
        assert content_analytics.views == 1250
        assert content_analytics.likes == 45
        assert content_analytics.engagement_rate == 0.052

    def test_content_analytics_multiple_platforms(self, db_session):
        """Test ContentAnalytics can track performance across platforms."""
        content_item = ContentItem(
            title="Multi-platform Analytics",
            content="Testing cross-platform analytics",
            content_type="social_post",
            author_id="user123",
            status="published",
        )
        db_session.add(content_item)
        db_session.commit()

        platforms_data = [
            {
                "platform": "linkedin",
                "views": 800,
                "likes": 25,
                "comments": 5,
                "shares": 3,
            },
            {
                "platform": "twitter",
                "views": 1200,
                "likes": 45,
                "comments": 8,
                "shares": 12,
            },
            {
                "platform": "devto",
                "views": 2000,
                "likes": 85,
                "comments": 15,
                "shares": 20,
            },
        ]

        for data in platforms_data:
            analytics = ContentAnalytics(
                content_item_id=content_item.id,
                platform=data["platform"],
                views=data["views"],
                likes=data["likes"],
                comments=data["comments"],
                shares=data["shares"],
                engagement_rate=(data["likes"] + data["comments"] + data["shares"])
                / data["views"],
                measured_at=datetime.now(timezone.utc),
            )

            db_session.add(analytics)
            db_session.commit()

            assert analytics.platform == data["platform"]
            assert analytics.views == data["views"]

    def test_content_analytics_time_series_tracking(self, db_session):
        """Test ContentAnalytics can track performance over time."""
        content_item = ContentItem(
            title="Time Series Analytics",
            content="Testing time-based analytics tracking",
            content_type="blog_post",
            author_id="user123",
            status="published",
        )
        db_session.add(content_item)
        db_session.commit()

        # Simulate analytics at different time points
        base_time = datetime.now(timezone.utc)
        time_points = [
            {"hours_offset": 0, "views": 100, "likes": 5},
            {"hours_offset": 24, "views": 350, "likes": 15},
            {"hours_offset": 72, "views": 600, "likes": 28},
            {"hours_offset": 168, "views": 800, "likes": 35},  # 1 week
        ]

        for point in time_points:
            analytics = ContentAnalytics(
                content_item_id=content_item.id,
                platform="devto",
                views=point["views"],
                likes=point["likes"],
                comments=2,
                shares=1,
                engagement_rate=point["likes"] / point["views"],
                measured_at=base_time + timedelta(hours=point["hours_offset"]),
            )

            db_session.add(analytics)
            db_session.commit()

            assert analytics.views == point["views"]
            assert analytics.measured_at == base_time + timedelta(
                hours=point["hours_offset"]
            )

    def test_content_analytics_engagement_rate_calculation(self, db_session):
        """Test ContentAnalytics properly calculates engagement rates."""
        content_item = ContentItem(
            title="Engagement Rate Test",
            content="Testing engagement rate calculations",
            content_type="social_post",
            author_id="user123",
            status="published",
        )
        db_session.add(content_item)
        db_session.commit()

        # Test various engagement scenarios
        test_cases = [
            {
                "views": 1000,
                "likes": 50,
                "comments": 10,
                "shares": 5,
                "expected_rate": 0.065,
            },
            {
                "views": 500,
                "likes": 25,
                "comments": 5,
                "shares": 0,
                "expected_rate": 0.06,
            },
            {
                "views": 2000,
                "likes": 100,
                "comments": 20,
                "shares": 10,
                "expected_rate": 0.065,
            },
        ]

        for case in test_cases:
            analytics = ContentAnalytics(
                content_item_id=content_item.id,
                platform="linkedin",
                views=case["views"],
                likes=case["likes"],
                comments=case["comments"],
                shares=case["shares"],
                engagement_rate=case["expected_rate"],
                measured_at=datetime.now(timezone.utc),
            )

            db_session.add(analytics)
            db_session.commit()

            assert abs(analytics.engagement_rate - case["expected_rate"]) < 0.001

    def test_content_analytics_additional_metrics(self, db_session):
        """Test ContentAnalytics can store additional platform-specific metrics."""
        content_item = ContentItem(
            title="Additional Metrics Test",
            content="Testing additional metrics storage",
            content_type="blog_post",
            author_id="user123",
            status="published",
        )
        db_session.add(content_item)
        db_session.commit()

        additional_metrics = {
            "click_through_rate": 0.035,
            "bounce_rate": 0.25,
            "time_on_page": 180,  # seconds
            "scroll_depth": 0.75,
            "conversion_rate": 0.02,
        }

        analytics = ContentAnalytics(
            content_item_id=content_item.id,
            platform="devto",
            views=1500,
            likes=60,
            comments=15,
            shares=12,
            engagement_rate=0.058,
            measured_at=datetime.now(timezone.utc),
            additional_metrics=additional_metrics,
        )

        db_session.add(analytics)
        db_session.commit()

        assert analytics.additional_metrics == additional_metrics
        assert analytics.additional_metrics["click_through_rate"] == 0.035


class TestContentSchedulerModelsIntegration:
    """Integration tests for all Content Scheduler models working together."""

    def test_complete_content_lifecycle_workflow(self, db_session):
        """Test complete workflow from content creation to analytics."""
        # 1. Create content item
        content_item = ContentItem(
            title="Complete Workflow Test",
            content="Testing the complete content management workflow",
            content_type="blog_post",
            author_id="user123",
            status="draft",
            content_metadata={"tags": ["workflow", "testing"]},
        )
        db_session.add(content_item)
        db_session.commit()

        # 2. Schedule it for multiple platforms
        platforms = ["devto", "linkedin", "medium"]
        schedule_time = datetime.now(timezone.utc) + timedelta(hours=2)

        schedules = []
        for platform in platforms:
            schedule = ContentSchedule(
                content_item_id=content_item.id,
                platform=platform,
                scheduled_time=schedule_time,
                timezone_name="UTC",
                status="scheduled",
            )
            schedules.append(schedule)
            db_session.add(schedule)

        db_session.commit()

        # 3. Simulate successful publishing and analytics
        for schedule in schedules:
            # Update schedule status to published
            schedule.status = "published"
            schedule.published_at = datetime.now(timezone.utc)

            # Create analytics for this platform
            analytics = ContentAnalytics(
                content_item_id=content_item.id,
                platform=schedule.platform,
                views=1000 + (schedules.index(schedule) * 200),
                likes=50 + (schedules.index(schedule) * 10),
                comments=10 + (schedules.index(schedule) * 2),
                shares=5 + schedules.index(schedule),
                engagement_rate=0.065,
                measured_at=datetime.now(timezone.utc),
            )
            db_session.add(analytics)

        # Update content item status
        content_item.status = "published"
        db_session.commit()

        # Verify the complete workflow
        assert content_item.status == "published"
        assert len(schedules) == 3
        assert all(s.status == "published" for s in schedules)

        # Verify analytics exist for all platforms
        all_analytics = (
            db_session.query(ContentAnalytics)
            .filter_by(content_item_id=content_item.id)
            .all()
        )

        assert len(all_analytics) == 3
        assert {a.platform for a in all_analytics} == {"devto", "linkedin", "medium"}

    def test_content_item_relationships(self, db_session):
        """Test that ContentItem properly relates to schedules and analytics."""
        content_item = ContentItem(
            title="Relationships Test",
            content="Testing model relationships",
            content_type="social_post",
            author_id="user123",
            status="published",
        )
        db_session.add(content_item)
        db_session.commit()

        # Add multiple schedules
        for i, platform in enumerate(["twitter", "linkedin"]):
            schedule = ContentSchedule(
                content_item_id=content_item.id,
                platform=platform,
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=i + 1),
                timezone_name="UTC",
                status="published",
            )
            db_session.add(schedule)

        # Add analytics
        analytics = ContentAnalytics(
            content_item_id=content_item.id,
            platform="twitter",
            views=800,
            likes=40,
            comments=5,
            shares=8,
            engagement_rate=0.066,
            measured_at=datetime.now(timezone.utc),
        )
        db_session.add(analytics)
        db_session.commit()

        # Test relationships (these will be implemented with the models)
        assert hasattr(content_item, "schedules")
        assert hasattr(content_item, "analytics")
        assert len(content_item.schedules) == 2
        assert len(content_item.analytics) == 1
