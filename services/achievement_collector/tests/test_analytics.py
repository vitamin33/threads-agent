"""
Tests for Phase 3.1 Advanced Analytics features.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from services.achievement_collector.analytics.career_predictor import (
    CareerPrediction,
    CareerPredictor,
    SkillProgression,
)
from services.achievement_collector.analytics.industry_benchmark import (
    IndustryBenchmark,
    IndustryBenchmarker,
)
from services.achievement_collector.analytics.performance_dashboard import (
    DashboardMetrics,
    PerformanceDashboard,
)
from services.achievement_collector.db.models import Achievement
from services.achievement_collector.main import app


@pytest.fixture
def sample_achievements():
    """Generate sample achievements for testing."""
    achievements = []
    for i in range(10):
        achievements.append(
            Achievement(
                title=f"Achievement {i + 1}",
                description=f"Description for achievement {i + 1}",
                category="optimization" if i % 2 == 0 else "feature",
                impact_score=60 + i * 5,
                complexity_score=50 + i * 3,
                skills_demonstrated=["Python", "AWS", "Docker"]
                if i % 2 == 0
                else ["React", "TypeScript"],
                completed_at=datetime.utcnow() - timedelta(days=30 * (10 - i)),
                started_at=datetime.utcnow() - timedelta(days=30 * (10 - i) + 7),
                duration_hours=(7 * 8),  # 7 days * 8 hours
                source_type="manual",
                source_id=f"test_{i}",
            )
        )
    return achievements


class TestCareerPredictor:
    """Test career prediction functionality."""

    def test_skill_progression_analysis(self, sample_achievements):
        """Test skill progression calculation."""
        predictor = CareerPredictor()
        progressions = predictor._analyze_skill_progression(sample_achievements)

        assert "Python" in progressions
        assert "React" in progressions

        python_prog = progressions["Python"]
        assert isinstance(python_prog, SkillProgression)
        assert python_prog.skill_name == "Python"
        assert 0 <= python_prog.current_level <= 10
        assert python_prog.growth_rate != 0

    def test_career_velocity_calculation(self, sample_achievements):
        """Test career velocity calculation."""
        predictor = CareerPredictor()
        velocity = predictor._calculate_career_velocity(sample_achievements)

        assert isinstance(velocity, float)
        assert 0.5 <= velocity <= 3.0  # Within bounds

    @pytest.mark.asyncio
    async def test_predict_career_trajectory(self, db_session, sample_achievements):
        """Test career trajectory prediction."""
        predictor = CareerPredictor()

        # Mock AI response by patching the client
        with patch.object(predictor.ai_analyzer, "client") as mock_client:
            # Mock the OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = str(
                {
                    "predictions": [
                        {
                            "next_role": "Senior Software Engineer",
                            "confidence": 0.85,
                            "timeline_months": 12,
                            "required_skills": ["System Design", "Leadership"],
                            "recommended_achievements": ["Lead a major project"],
                            "salary_range": [120000, 150000],
                            "market_demand": "high",
                        }
                    ]
                }
            )

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # Add achievements to mock session
            for achievement in sample_achievements:
                db_session.add(achievement)
            db_session.commit()

            predictions = await predictor.predict_career_trajectory(db_session)

            assert len(predictions) == 1
            assert predictions[0].next_role == "Senior Software Engineer"
            assert predictions[0].confidence == 0.85
            assert predictions[0].timeline_months == 12

    def test_skill_market_value(self):
        """Test skill market value calculation."""
        predictor = CareerPredictor()

        assert predictor._get_skill_market_value("AI/ML") == 0.9
        assert predictor._get_skill_market_value("Python") == 0.7
        assert predictor._get_skill_market_value("Unknown") == 0.5

    def test_skill_trending_check(self):
        """Test skill trending status."""
        predictor = CareerPredictor()

        assert predictor._is_skill_trending("AI/ML") is True
        assert predictor._is_skill_trending("Python") is False
        assert predictor._is_skill_trending("LLM") is True


class TestIndustryBenchmarker:
    """Test industry benchmarking functionality."""

    def test_calculate_user_metrics(self, sample_achievements):
        """Test user metrics calculation."""
        benchmarker = IndustryBenchmarker()
        metrics = benchmarker._calculate_user_metrics(sample_achievements, 365)

        assert "achievements_per_month" in metrics
        assert "average_impact_score" in metrics
        assert "skill_diversity" in metrics
        assert metrics["skill_diversity"] == 5  # Python, AWS, Docker, React, TypeScript

    def test_percentile_calculation(self):
        """Test percentile rank calculation."""
        benchmarker = IndustryBenchmarker()
        percentiles = {10: 1.0, 25: 2.0, 50: 3.0, 75: 4.0, 90: 5.0}

        assert benchmarker._calculate_percentile(0.5, percentiles) < 10
        assert benchmarker._calculate_percentile(2.5, percentiles) == pytest.approx(
            37, rel=5
        )
        assert benchmarker._calculate_percentile(6.0, percentiles) > 90

    def test_benchmark_metric(self):
        """Test single metric benchmarking."""
        benchmarker = IndustryBenchmarker()
        benchmark = benchmarker._benchmark_metric("achievements_per_month", 3.5)

        assert isinstance(benchmark, IndustryBenchmark)
        assert benchmark.metric_name == "achievements_per_month"
        assert benchmark.your_value == 3.5
        assert benchmark.percentile > 50
        assert benchmark.trend in ["improving", "stable", "declining"]
        assert len(benchmark.recommendation) > 0

    @pytest.mark.asyncio
    async def test_compensation_benchmark(self):
        """Test compensation benchmarking."""
        benchmarker = IndustryBenchmarker()

        result = await benchmarker.benchmark_compensation(
            role="Senior Software Engineer",
            years_experience=5,
            skills=["Python", "AWS", "Kubernetes"],
            location="San Francisco",
            achievements_count=20,
        )

        assert result.role == "Senior Software Engineer"
        assert result.your_estimated_value > 100000
        assert result.market_low < result.market_median < result.market_high
        assert 0 <= result.percentile <= 100
        assert "base_salary" in result.factors

    def test_skill_market_analysis(self):
        """Test skill market data analysis."""
        benchmarker = IndustryBenchmarker()
        market_data = benchmarker.analyze_skill_market(["AI/ML", "Python"])

        assert len(market_data) == 2
        ai_data = next(s for s in market_data if s.skill_name == "AI/ML")
        assert ai_data.demand_level > ai_data.supply_level
        assert ai_data.future_outlook in ["declining", "stable", "growing", "explosive"]


class TestPerformanceDashboard:
    """Test performance dashboard functionality."""

    def test_dashboard_metrics_generation(self, db_session, sample_achievements):
        """Test complete dashboard metrics generation."""
        dashboard = PerformanceDashboard()

        # Clear any existing achievements first
        from ..db.models import Achievement

        db_session.query(Achievement).delete()
        db_session.commit()

        # Add achievements to session
        for achievement in sample_achievements:
            db_session.add(achievement)
        db_session.commit()

        metrics = dashboard.generate_dashboard_metrics(db_session)

        assert isinstance(metrics, DashboardMetrics)
        assert metrics.total_achievements == 10
        assert metrics.average_impact > 0
        assert len(metrics.achievement_timeline) > 0
        assert len(metrics.skill_radar) > 0
        assert metrics.percentile_rank > 0

    def test_timeline_generation(self, sample_achievements):
        """Test achievement timeline generation."""
        dashboard = PerformanceDashboard()
        timeline = dashboard._generate_achievement_timeline(sample_achievements)

        assert len(timeline) > 0
        assert all(hasattr(t, "timestamp") for t in timeline)
        assert all(hasattr(t, "value") for t in timeline)

    def test_skill_radar_generation(self, sample_achievements):
        """Test skill radar data generation."""
        dashboard = PerformanceDashboard()
        radar_data = dashboard._generate_skill_radar(sample_achievements)

        assert len(radar_data) > 0
        assert all(0 <= s.current_level <= 10 for s in radar_data)
        assert all(-1 <= s.growth_trend <= 1 for s in radar_data)

    def test_milestone_identification(self, sample_achievements):
        """Test career milestone identification."""
        dashboard = PerformanceDashboard()
        milestones = dashboard._identify_career_milestones(sample_achievements)

        assert len(milestones) > 0
        high_impact_milestones = [
            m for m in milestones if m.impact in ["high", "critical"]
        ]
        assert len(high_impact_milestones) > 0

    def test_executive_summary(self, db_session, sample_achievements):
        """Test executive summary generation."""
        dashboard = PerformanceDashboard()

        # Clear any existing achievements first
        from ..db.models import Achievement

        db_session.query(Achievement).delete()
        db_session.commit()

        # Add achievements to session
        for achievement in sample_achievements:
            db_session.add(achievement)
        db_session.commit()

        summary = dashboard.generate_executive_summary(db_session)

        assert "overview" in summary
        assert "highlights" in summary
        assert "growth_metrics" in summary
        assert "recommendations" in summary
        assert summary["overview"]["total_achievements"] == 10


class TestAnalyticsAPI:
    """Test analytics API endpoints."""

    @pytest.fixture
    def client(self, db_session):
        """Create test client with database override."""

        def override():
            yield db_session

        from services.achievement_collector.db.config import get_db

        app.dependency_overrides[get_db] = override

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()

    def test_career_prediction_endpoint(self, client, sample_achievements, db_session):
        """Test career prediction API endpoint."""
        # Add sample achievements
        for achievement in sample_achievements:
            db_session.add(achievement)
        db_session.commit()

        # Create mock predictions
        mock_predictions = [
            CareerPrediction(
                next_role="Tech Lead",
                confidence=0.8,
                timeline_months=18,
                required_skills=["Architecture", "Mentoring"],
                recommended_achievements=["Design system architecture"],
                salary_range=(150000, 180000),
                market_demand="high",
            )
        ]

        with patch(
            "services.achievement_collector.api.routes.analytics.career_predictor.predict_career_trajectory"
        ) as mock_predict:
            mock_predict.return_value = mock_predictions

            response = client.get("/analytics/career-prediction")
            assert response.status_code == 200
            data = response.json()
            assert "predictions" in data
            assert len(data["predictions"]) > 0

    def test_industry_benchmark_endpoint(self, client, sample_achievements, db_session):
        """Test industry benchmark API endpoint."""
        # Add sample achievements
        for achievement in sample_achievements:
            db_session.add(achievement)
        db_session.commit()

        response = client.get("/analytics/industry-benchmark")
        assert response.status_code == 200
        data = response.json()
        assert "benchmarks" in data
        assert len(data["benchmarks"]) > 0

    def test_compensation_benchmark_endpoint(self, client):
        """Test compensation benchmark API endpoint."""
        payload = {
            "role": "Software Engineer",
            "years_experience": 3,
            "skills": ["Python", "React"],
            "location": "Remote",
            "achievements_count": 15,
        }

        response = client.post("/analytics/compensation-benchmark", json=payload)
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert "your_estimated_value" in data
        assert "percentile" in data

    def test_dashboard_metrics_endpoint(self, client, sample_achievements, db_session):
        """Test dashboard metrics API endpoint."""
        # Clear any existing achievements first
        from services.achievement_collector.db.models import Achievement

        db_session.query(Achievement).delete()
        db_session.commit()

        # Add sample achievements
        for achievement in sample_achievements:
            db_session.add(achievement)
        db_session.commit()

        response = client.get("/analytics/dashboard-metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_achievements" in data
        assert "achievement_timeline" in data
        assert "skill_radar" in data

    def test_trending_skills_endpoint(self, client):
        """Test trending skills API endpoint."""
        response = client.get("/analytics/trending-skills")
        assert response.status_code == 200
        data = response.json()
        assert "trending_skills" in data
        assert "recommendations" in data
        assert len(data["trending_skills"]) > 0
