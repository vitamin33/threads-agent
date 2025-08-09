"""
Unit Tests for Achievement Collector Integration (Feature 25-3)

These are focused unit tests that test the achievement integration functionality
directly without going through the full FastAPI app startup process.

This avoids external service dependencies while still testing our TDD implementation.
"""

import pytest
from datetime import datetime, timezone, timedelta

from services.orchestrator.achievement_integration import (
    AchievementCollectorClient,
    AchievementContentSelector,
    AchievementContentGenerator,
    AchievementContentRequested,
    AchievementContentGenerated,
    AchievementPerformanceTracker,
    AchievementFeedbackService,
    AchievementWebSocketClient,
)


class TestAchievementCollectorClientUnit:
    """Unit tests for Achievement Collector HTTP client."""

    @pytest.mark.asyncio
    async def test_get_achievements_returns_mock_data(self):
        """Test that get_achievements returns expected mock data structure."""
        client = AchievementCollectorClient("http://test-url:8080")

        result = await client.get_achievements(
            category="development", min_impact_score=80.0
        )

        assert isinstance(result, dict)
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) == 2
        assert result["items"][0]["id"] == 1
        assert result["items"][0]["impact_score"] == 95.0
        assert result["items"][1]["id"] == 2
        assert result["items"][1]["impact_score"] == 90.0

    @pytest.mark.asyncio
    async def test_get_stats_returns_expected_structure(self):
        """Test that get_stats returns expected statistics structure."""
        client = AchievementCollectorClient("http://test-url:8080")

        result = await client.get_stats()

        assert isinstance(result, dict)
        assert "total_achievements" in result
        assert "total_value_generated" in result
        assert "by_category" in result
        assert result["total_achievements"] == 150
        assert result["total_value_generated"] == 125000.0
        assert len(result["by_category"]) == 3

    @pytest.mark.asyncio
    async def test_track_usage_returns_success(self):
        """Test that track_usage returns success response."""
        client = AchievementCollectorClient("http://test-url:8080")

        usage_data = {
            "achievement_ids": [1, 2, 3],
            "content_id": 123,
            "performance_metrics": {"engagement_rate": 0.08},
        }

        result = await client.track_usage(usage_data)

        assert result["status"] == "tracked"
        assert result["id"] == 456


class TestAchievementContentSelectorUnit:
    """Unit tests for achievement content selection logic."""

    def test_select_top_achievements_filters_by_criteria(self):
        """Test that achievements are filtered based on selection criteria."""
        selector = AchievementContentSelector()

        achievements = [
            {"id": 1, "impact_score": 95.0, "business_value": 5000.0},
            {"id": 2, "impact_score": 90.0, "business_value": 3000.0},
            {
                "id": 3,
                "impact_score": 75.0,
                "business_value": 8000.0,
            },  # Below impact threshold
            {
                "id": 4,
                "impact_score": 85.0,
                "business_value": 1000.0,
            },  # Below business value threshold
        ]

        criteria = {
            "max_achievements": 3,
            "min_impact_score": 80.0,
            "min_business_value": 2000.0,
        }

        selected = selector.select_top_achievements(achievements, criteria)

        # Should filter out achievements 3 and 4
        assert len(selected) == 2
        assert selected[0]["id"] in [1, 2]
        assert selected[1]["id"] in [1, 2]
        assert all(a["impact_score"] >= 80.0 for a in selected)
        assert all(a["business_value"] >= 2000.0 for a in selected)

    def test_select_top_achievements_limits_count(self):
        """Test that selection respects max_achievements limit."""
        selector = AchievementContentSelector()

        achievements = [
            {"id": i, "impact_score": 90.0, "business_value": 5000.0}
            for i in range(1, 11)  # 10 achievements
        ]

        criteria = {
            "max_achievements": 3,
            "min_impact_score": 80.0,
            "min_business_value": 1000.0,
        }

        selected = selector.select_top_achievements(achievements, criteria)

        assert len(selected) <= 3

    def test_filter_by_company_context_includes_security_for_fintech(self):
        """Test company context filtering prioritizes relevant achievements."""
        selector = AchievementContentSelector()

        achievements = [
            {"id": 1, "category": "development", "tags": ["python", "api"]},
            {"id": 2, "category": "security", "tags": ["authentication", "encryption"]},
            {"id": 3, "category": "frontend", "tags": ["react", "ui"]},
            {"id": 4, "category": "documentation", "tags": ["readme", "docs"]},
        ]

        company_context = {
            "industry": "fintech",
            "tech_stack": ["python", "react"],
            "priorities": ["security", "performance"],
            "excluded_categories": ["documentation"],
        }

        filtered = selector.filter_by_company_context(achievements, company_context)

        # Should exclude documentation
        doc_achievements = [a for a in filtered if a["category"] == "documentation"]
        assert len(doc_achievements) == 0

        # Should include security (high priority for fintech)
        security_achievements = [a for a in filtered if a["category"] == "security"]
        assert len(security_achievements) > 0

        # Should include tech stack matches
        tech_matches = [
            a
            for a in filtered
            if any(tag in company_context["tech_stack"] for tag in a["tags"])
        ]
        assert len(tech_matches) > 0


class TestAchievementContentGeneratorUnit:
    """Unit tests for achievement-based content generation."""

    def test_generate_content_templates_creates_title_and_body(self):
        """Test content generation creates expected structure."""
        generator = AchievementContentGenerator()

        achievements = [
            {
                "id": 1,
                "title": "Database Performance Optimization",
                "impact_score": 95.0,
                "time_saved_hours": 40.0,
                "metrics_before": {"avg_query_time_ms": 2000},
                "metrics_after": {"avg_query_time_ms": 500},
            }
        ]

        config = {
            "content_type": "blog_post",
            "target_platform": "linkedin",
            "include_metrics": True,
        }

        result = generator.generate_content_templates(achievements, config)

        assert "title" in result
        assert "body" in result
        assert "hook" in result
        assert "templates" in result

        # Should include metrics from achievements
        assert "75%" in result["body"]  # Performance improvement
        assert "40" in result["body"] or "hours" in result["body"]  # Time saved

    def test_generate_content_handles_empty_achievements(self):
        """Test content generation handles empty achievements list."""
        generator = AchievementContentGenerator()

        result = generator.generate_content_templates([], {})

        assert result["title"] == "My Recent Achievements"
        assert "highlights" in result["body"]
        assert result["hook"] == "Just completed some great work!"
        assert len(result["templates"]) == 0

    def test_generate_weekly_digest_groups_by_category(self):
        """Test weekly digest generation groups achievements by category."""
        generator = AchievementContentGenerator()

        achievements = [
            {
                "id": 1,
                "title": "API Optimization",
                "category": "development",
                "impact_score": 90.0,
            },
            {
                "id": 2,
                "title": "Security Audit",
                "category": "security",
                "impact_score": 95.0,
            },
        ]

        config = {
            "week_start": datetime.now(timezone.utc) - timedelta(days=7),
            "week_end": datetime.now(timezone.utc),
            "group_by_category": True,
        }

        result = generator.generate_weekly_digest(achievements, config)

        assert "achievements_by_category" in result
        assert "total_impact" in result
        assert "summary" in result
        assert result["total_impact"] == 185.0
        assert len(result["achievements_by_category"]) == 2
        assert "development" in result["achievements_by_category"]
        assert "security" in result["achievements_by_category"]


class TestAchievementPerformanceTrackerUnit:
    """Unit tests for achievement performance tracking."""

    def test_track_achievement_content_performance_calculates_score(self):
        """Test performance tracking calculates performance score correctly."""
        tracker = AchievementPerformanceTracker()

        content = {"content_id": 123, "achievement_ids": [1, 2, 3]}

        metrics = {
            "engagement_rate": 0.095,  # High engagement
            "reach": 2200,
            "likes": 150,
        }

        result = tracker.track_achievement_content_performance(content, metrics)

        assert result["tracked"] is True
        assert result["feedback_sent"] is True
        assert result["performance_score"] == "high"  # Above 0.08 threshold
        assert result["content_id"] == 123
        assert result["achievement_ids"] == [1, 2, 3]

    def test_track_achievement_content_performance_medium_score(self):
        """Test performance tracking identifies medium performance."""
        tracker = AchievementPerformanceTracker()

        content = {"content_id": 456, "achievement_ids": [4, 5]}
        metrics = {"engagement_rate": 0.06}  # Medium engagement

        result = tracker.track_achievement_content_performance(content, metrics)

        assert result["performance_score"] == "medium"

    def test_track_achievement_content_performance_low_score(self):
        """Test performance tracking identifies low performance."""
        tracker = AchievementPerformanceTracker()

        content = {"content_id": 789, "achievement_ids": [6]}
        metrics = {"engagement_rate": 0.03}  # Low engagement

        result = tracker.track_achievement_content_performance(content, metrics)

        assert result["performance_score"] == "low"


class TestAchievementFeedbackServiceUnit:
    """Unit tests for achievement feedback service."""

    def test_send_performance_feedback_high_rating(self):
        """Test feedback service correctly rates high performance."""
        service = AchievementFeedbackService()

        performance_data = {
            "achievement_ids": [1, 2, 3],
            "content_performance": {
                "engagement_rate": 0.095,  # High performance
                "reach": 2200,
            },
            "usage_context": {
                "platform": "linkedin",
                "content_type": "achievement_highlight",
            },
        }

        result = service.send_performance_feedback(performance_data)

        assert result["status"] == "sent"
        assert result["performance_rating"] == "high"
        assert "feedback_id" in result
        assert result["achievement_ids"] == [1, 2, 3]

    def test_send_performance_feedback_medium_rating(self):
        """Test feedback service correctly rates medium performance."""
        service = AchievementFeedbackService()

        performance_data = {
            "achievement_ids": [4, 5],
            "content_performance": {
                "engagement_rate": 0.06  # Medium performance
            },
        }

        result = service.send_performance_feedback(performance_data)

        assert result["performance_rating"] == "medium"


class TestAchievementWebSocketClientUnit:
    """Unit tests for WebSocket achievement updates."""

    @pytest.mark.asyncio
    async def test_listen_for_updates_yields_achievement_created(self):
        """Test WebSocket client yields achievement created updates."""
        client = AchievementWebSocketClient("ws://test-url:8080/ws")

        updates = []
        async for update in client.listen_for_updates():
            updates.append(update)
            break  # Just get the first update for testing

        assert len(updates) == 1
        assert updates[0]["type"] == "achievement_created"
        assert updates[0]["data"]["id"] == 123
        assert updates[0]["data"]["title"] == "New Achievement"


class TestAchievementEventContractsUnit:
    """Unit tests for achievement event contract models."""

    def test_achievement_content_requested_event_creation(self):
        """Test AchievementContentRequested event can be created with valid data."""
        payload = {
            "content_id": 123,
            "author_id": "test_author",
            "content_type": "blog_post",
            "target_platform": "linkedin",
            "company_context": "tech_startup",
            "achievement_filters": {"category": "development"},
            "max_achievements": 5,
            "priority_threshold": 75.0,
            "requested_at": datetime.now(timezone.utc),
        }

        event = AchievementContentRequested(**payload)

        assert event.content_id == 123
        assert event.author_id == "test_author"
        assert event.target_platform == "linkedin"
        assert event.max_achievements == 5
        assert event.priority_threshold == 75.0

    def test_achievement_content_generated_event_creation(self):
        """Test AchievementContentGenerated event can be created with valid data."""
        payload = {
            "content_id": 123,
            "achievement_ids": [1, 2, 3],
            "generated_content": {
                "title": "My Achievements",
                "body": "Here are my accomplishments...",
            },
            "content_templates": [
                {"template_type": "highlight", "content": "Achievement template"}
            ],
            "performance_prediction": {
                "predicted_engagement_rate": 0.08,
                "confidence_score": 0.85,
            },
            "usage_metrics": {"achievements_selected": 3, "generation_time_ms": 2300},
            "generated_at": datetime.now(timezone.utc),
        }

        event = AchievementContentGenerated(**payload)

        assert event.content_id == 123
        assert len(event.achievement_ids) == 3
        assert "title" in event.generated_content
        assert len(event.content_templates) == 1
        assert event.performance_prediction["confidence_score"] == 0.85
