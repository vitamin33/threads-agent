"""
Tests for shared achievement models
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from services.common.models.achievement_models import (
    Achievement,
    AchievementCreate,
    AchievementUpdate,
    AchievementSummary,
    AchievementFilter,
    AchievementCategory,
    AchievementMetrics,
)


class TestAchievementMetrics:
    """Test AchievementMetrics model"""

    def test_valid_metrics(self):
        """Test creating valid metrics"""
        metrics = AchievementMetrics(
            time_saved_hours=10.5,
            cost_saved_dollars=5000,
            performance_improvement_percent=25.5,
            error_reduction_percent=90,
            custom={"custom_metric": 42.0},
        )

        assert metrics.time_saved_hours == 10.5
        assert metrics.cost_saved_dollars == 5000
        assert metrics.performance_improvement_percent == 25.5
        assert metrics.custom["custom_metric"] == 42.0

    def test_metric_constraints(self):
        """Test metric value constraints"""
        # Negative time saved should fail
        with pytest.raises(ValidationError):
            AchievementMetrics(time_saved_hours=-5)

        # Error reduction > 100% should fail
        with pytest.raises(ValidationError):
            AchievementMetrics(error_reduction_percent=150)

        # Performance improvement can be negative (regression)
        metrics = AchievementMetrics(performance_improvement_percent=-10)
        assert metrics.performance_improvement_percent == -10


class TestAchievement:
    """Test Achievement model"""

    @pytest.fixture
    def valid_achievement_data(self):
        """Valid achievement data for testing"""
        return {
            "id": 1,
            "title": "Implemented AI-Powered Content Pipeline",
            "description": "Built an automated content generation system that integrates achievements with documentation",
            "category": AchievementCategory.AUTOMATION,
            "impact_score": 92.5,
            "complexity_score": 85.0,
            "business_value": "Saves 15+ hours per week on content creation",
            "technical_details": {
                "architecture": "Microservices",
                "technologies": ["Python", "FastAPI", "LangGraph"],
            },
            "technologies_used": ["Python", "FastAPI", "OpenAI", "PostgreSQL"],
            "tags": ["AI", "Automation", "Content"],
            "portfolio_ready": True,
            "source_type": "github_pr",
            "source_id": "PR-123",
            "started_at": datetime.now() - timedelta(days=7),
            "completed_at": datetime.now() - timedelta(days=1),
            "created_at": datetime.now(),
        }

    def test_valid_achievement(self, valid_achievement_data):
        """Test creating a valid achievement"""
        achievement = Achievement(**valid_achievement_data)

        assert achievement.id == 1
        assert achievement.title == "Implemented AI-Powered Content Pipeline"
        assert achievement.impact_score == 92.5
        assert achievement.category == AchievementCategory.AUTOMATION
        assert len(achievement.technologies_used) == 4

        # Check auto-calculated duration
        assert achievement.duration_hours is not None
        assert achievement.duration_hours > 0

        # Check tag normalization
        assert all(tag.islower() for tag in achievement.tags)

    def test_achievement_validation(self):
        """Test achievement validation rules"""
        # Title too short
        with pytest.raises(ValidationError):
            Achievement(
                id=1,
                title="AI",
                description="A" * 20,
                category=AchievementCategory.AI_ML,
                impact_score=80,
                business_value="Test value",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                created_at=datetime.now(),
            )

        # Impact score out of range
        with pytest.raises(ValidationError):
            Achievement(
                id=1,
                title="Valid Title Here",
                description="A" * 20,
                category=AchievementCategory.AI_ML,
                impact_score=150,  # > 100
                business_value="Test value",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                created_at=datetime.now(),
            )

    def test_achievement_with_metrics(self, valid_achievement_data):
        """Test achievement with metrics"""
        metrics = AchievementMetrics(
            time_saved_hours=15, cost_saved_dollars=10000, users_impacted=500
        )

        valid_achievement_data["metrics"] = metrics
        achievement = Achievement(**valid_achievement_data)

        assert achievement.metrics.time_saved_hours == 15
        assert achievement.metrics.cost_saved_dollars == 10000
        assert achievement.metrics.users_impacted == 500


class TestAchievementCreate:
    """Test AchievementCreate model"""

    def test_valid_create(self):
        """Test creating achievement create request"""
        create_data = AchievementCreate(
            title="New AI Feature Implementation",
            description="Implemented a new AI-powered feature that improves user experience significantly",
            category=AchievementCategory.FEATURE,
            impact_score=85,
            business_value="Increases user engagement by 30%",
            started_at=datetime.now() - timedelta(days=5),
            completed_at=datetime.now(),
        )

        assert create_data.title == "New AI Feature Implementation"
        assert create_data.portfolio_ready is True  # Default value
        assert create_data.complexity_score == 50.0  # Default value

    def test_create_with_all_fields(self):
        """Test create with all optional fields"""
        metrics = AchievementMetrics(time_saved_hours=20)

        create_data = AchievementCreate(
            title="Complete Feature with Metrics",
            description="A comprehensive feature implementation with full metrics and details",
            category=AchievementCategory.FEATURE,
            impact_score=90,
            complexity_score=75,
            business_value="Major improvement in system efficiency",
            technical_details={"framework": "FastAPI"},
            technologies_used=["Python", "Redis"],
            metrics=metrics,
            tags=["optimization", "performance"],
            source_type="linear",
            source_id="ENG-1234",
            started_at=datetime.now() - timedelta(days=3),
            completed_at=datetime.now(),
            metadata={"custom": "data"},
        )

        assert create_data.complexity_score == 75
        assert len(create_data.technologies_used) == 2
        assert create_data.metrics.time_saved_hours == 20


class TestAchievementUpdate:
    """Test AchievementUpdate model"""

    def test_partial_update(self):
        """Test partial update with only some fields"""
        update_data = AchievementUpdate(title="Updated Title", impact_score=95)

        assert update_data.title == "Updated Title"
        assert update_data.impact_score == 95
        assert update_data.description is None
        assert update_data.category is None

    def test_update_validation(self):
        """Test update validation"""
        # Invalid impact score
        with pytest.raises(ValidationError):
            AchievementUpdate(impact_score=120)

        # Title too short
        with pytest.raises(ValidationError):
            AchievementUpdate(title="Hi")


class TestAchievementFilter:
    """Test AchievementFilter model"""

    def test_default_filter(self):
        """Test default filter values"""
        filter_obj = AchievementFilter()

        assert filter_obj.page == 1
        assert filter_obj.page_size == 20
        assert filter_obj.sort_by == "completed_at"
        assert filter_obj.sort_order == "desc"
        assert filter_obj.portfolio_ready_only is False

    def test_complex_filter(self):
        """Test filter with multiple criteria"""
        filter_obj = AchievementFilter(
            categories=[AchievementCategory.AI_ML, AchievementCategory.AUTOMATION],
            min_impact_score=80,
            max_impact_score=100,
            portfolio_ready_only=True,
            tags=["ai", "optimization"],
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            page=2,
            page_size=50,
        )

        assert len(filter_obj.categories) == 2
        assert filter_obj.min_impact_score == 80
        assert filter_obj.portfolio_ready_only is True
        assert filter_obj.page == 2
        assert filter_obj.page_size == 50

    def test_date_validation(self):
        """Test date range validation"""
        # End date before start date should fail
        with pytest.raises(ValidationError):
            AchievementFilter(
                start_date=datetime.now(), end_date=datetime.now() - timedelta(days=1)
            )

    def test_company_filter(self):
        """Test company-specific filtering"""
        filter_obj = AchievementFilter(
            company_keywords=["scalability", "performance", "api"],
            search_query="microservices architecture",
        )

        assert len(filter_obj.company_keywords) == 3
        assert filter_obj.search_query == "microservices architecture"


class TestAchievementSummary:
    """Test AchievementSummary model"""

    def test_summary_creation(self):
        """Test creating achievement summary"""
        summary = AchievementSummary(
            id=1,
            title="AI Pipeline Implementation",
            category=AchievementCategory.AI_ML,
            impact_score=88.5,
            business_value="Significant time savings",
            tags=["ai", "automation"],
            completed_at=datetime.now(),
            portfolio_ready=True,
        )

        assert summary.id == 1
        assert summary.impact_score == 88.5
        assert len(summary.tags) == 2
        assert summary.portfolio_ready is True

    def test_summary_json_serialization(self):
        """Test JSON serialization of summary"""
        summary = AchievementSummary(
            id=1,
            title="Test Achievement",
            category=AchievementCategory.FEATURE,
            impact_score=75,
            business_value="Test value",
            tags=[],
            completed_at=datetime.now(),
            portfolio_ready=False,
        )

        # Should serialize without errors
        json_data = summary.model_dump_json()
        assert "Test Achievement" in json_data
        assert "completed_at" in json_data


class TestAchievementCategory:
    """Test AchievementCategory enum"""

    def test_all_categories(self):
        """Test all category values are accessible"""
        categories = [
            AchievementCategory.FEATURE,
            AchievementCategory.BUGFIX,
            AchievementCategory.PERFORMANCE,
            AchievementCategory.AI_ML,
            AchievementCategory.DEVOPS,
        ]

        assert all(isinstance(cat, AchievementCategory) for cat in categories)
        assert AchievementCategory.AI_ML.value == "ai_ml"
        assert AchievementCategory.FEATURE.value == "feature"
