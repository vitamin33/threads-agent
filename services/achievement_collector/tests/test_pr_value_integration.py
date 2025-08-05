"""Tests for PR Value Analyzer Integration."""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from services.achievement_collector.services.pr_value_analyzer_integration import (
    PRValueAnalyzerIntegration,
)


@pytest.fixture
def integration():
    """Create PRValueAnalyzerIntegration instance."""
    return PRValueAnalyzerIntegration()


@pytest.fixture
def mock_analysis_result():
    """Mock PR analysis result."""
    return {
        "pr_number": "123",
        "timestamp": datetime.now().isoformat(),
        "business_metrics": {
            "throughput_improvement_percent": 150.5,
            "infrastructure_savings_estimate": 80000,
            "user_experience_score": 9,
            "roi_year_one_percent": 234,
            "payback_period_months": 5.1,
        },
        "technical_metrics": {
            "performance": {
                "peak_rps": 673.9,
                "latency_ms": 50,
                "success_rate": 100,
                "test_coverage": 95,
            },
            "code_metrics": {
                "files_changed": 25,
                "lines_added": 1500,
                "lines_deleted": 200,
                "code_churn": 1700,
            },
            "innovation_score": 8.5,
        },
        "achievement_tags": [
            "high_performance_implementation",
            "cost_optimization",
            "kubernetes_deployment",
            "production_ready",
        ],
        "kpis": {
            "performance_score": 6.739,
            "quality_score": 9.5,
            "business_value_score": 7.8,
            "innovation_score": 8.5,
            "overall_score": 8.1,
        },
        "future_impact": {
            "revenue_impact_3yr": 425000,
            "competitive_advantage": "high",
            "market_differentiation": "performance_leader",
        },
    }


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock()
    db.query.return_value.filter_by.return_value.first.return_value = None
    db.commit = Mock()
    db.refresh = Mock()
    return db


class TestPRValueAnalyzerIntegration:
    """Test PR Value Analyzer Integration."""

    @pytest.mark.asyncio
    async def test_analyze_and_create_achievement_success(
        self, integration, mock_analysis_result, mock_db
    ):
        """Test successful PR analysis and achievement creation."""
        with patch.object(
            integration, "_run_pr_analyzer", new_callable=AsyncMock
        ) as mock_run:
            with patch(
                "services.achievement_collector.services.pr_value_analyzer_integration.get_db"
            ) as mock_get_db:
                with patch(
                    "services.achievement_collector.services.pr_value_analyzer_integration.create_achievement_sync"
                ) as mock_create:
                    mock_run.return_value = mock_analysis_result
                    mock_get_db.return_value = iter([mock_db])
                    mock_achievement = Mock(id=1)
                    mock_create.return_value = mock_achievement

                    result = await integration.analyze_and_create_achievement("123")

                    assert result == mock_achievement
                    mock_run.assert_called_once_with("123")
                    mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_below_threshold(
        self, integration, mock_analysis_result, mock_db
    ):
        """Test PR analysis below score threshold."""
        mock_analysis_result["kpis"]["overall_score"] = 5.0  # Below threshold

        with patch.object(
            integration, "_run_pr_analyzer", new_callable=AsyncMock
        ) as mock_run:
            with patch(
                "services.achievement_collector.services.pr_value_analyzer_integration.get_db"
            ) as mock_get_db:
                mock_run.return_value = mock_analysis_result
                mock_get_db.return_value = iter([mock_db])

                result = await integration.analyze_and_create_achievement("123")

                assert result is None

    @pytest.mark.asyncio
    async def test_update_existing_achievement(
        self, integration, mock_analysis_result, mock_db
    ):
        """Test updating existing achievement with enriched metrics."""
        existing_achievement = Mock(
            id=1,
            metrics_after={"files_changed": 25},
            metadata={},
            tags=["pr-123"],
            portfolio_ready=False,
        )
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            existing_achievement
        )

        with patch.object(
            integration, "_run_pr_analyzer", new_callable=AsyncMock
        ) as mock_run:
            with patch.object(
                integration, "_update_achievement_metrics", new_callable=AsyncMock
            ) as mock_update:
                with patch(
                    "services.achievement_collector.services.pr_value_analyzer_integration.get_db"
                ) as mock_get_db:
                    mock_run.return_value = mock_analysis_result
                    mock_get_db.return_value = iter([mock_db])
                    mock_update.return_value = existing_achievement

                    result = await integration.analyze_and_create_achievement("123")

                    assert result == existing_achievement
                    mock_update.assert_called_once_with(
                        existing_achievement, mock_analysis_result, mock_db
                    )

    def test_determine_impact_level(self, integration):
        """Test impact level determination."""
        assert integration._determine_impact_level(9.5, {}) == "🌟 Exceptional Impact"
        assert integration._determine_impact_level(8.5, {}) == "🚀 High Impact"
        assert integration._determine_impact_level(7.5, {}) == "💪 Significant Impact"
        assert integration._determine_impact_level(6.5, {}) == "✅ Good Impact"
        assert integration._determine_impact_level(5.0, {}) == "📈 Moderate Impact"

    def test_determine_category(self, integration):
        """Test category determination from tags."""
        assert (
            integration._determine_category(["high_performance_implementation"])
            == "optimization"
        )
        assert (
            integration._determine_category(["cost_optimization"]) == "infrastructure"
        )
        assert (
            integration._determine_category(["kubernetes_deployment"])
            == "infrastructure"
        )
        assert integration._determine_category(["ai_ml_feature"]) == "feature"
        assert integration._determine_category(["production_ready"]) == "deployment"
        assert integration._determine_category(["unknown"]) == "development"

    def test_extract_skills(self, integration, mock_analysis_result):
        """Test skill extraction from analysis."""
        skills = integration._extract_skills(mock_analysis_result)

        assert "Performance Optimization" in skills
        assert "Cost Management" in skills
        assert "Kubernetes" in skills
        assert "High-Performance Systems" in skills  # Because RPS > 500
        assert "Test-Driven Development" in skills  # Because coverage > 90%
        assert "Git" in skills
        assert len(skills) <= 15

    def test_generate_enriched_description(self, integration, mock_analysis_result):
        """Test enriched description generation."""
        description = integration._generate_enriched_description(
            "123", mock_analysis_result
        )

        assert "673.9 RPS" in description
        assert "<50ms latency" in description
        assert "$80,000" in description
        assert "234% first-year ROI" in description
        assert "25 files" in description
        assert "$425,000" in description

    @pytest.mark.asyncio
    async def test_run_pr_analyzer_success(self, integration):
        """Test running PR analyzer script."""
        mock_result = {"test": "data"}

        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        json.dumps(mock_result)
                    )
                    mock_run.return_value.returncode = 0

                    result = await integration._run_pr_analyzer("123")

                    assert result == mock_result

    @pytest.mark.asyncio
    async def test_create_enriched_achievement_comprehensive(
        self, integration, mock_analysis_result, mock_db
    ):
        """Test comprehensive achievement creation with all metrics."""
        with patch(
            "services.achievement_collector.services.pr_value_analyzer_integration.create_achievement_sync"
        ) as mock_create:
            await integration._create_enriched_achievement(
                "123", mock_analysis_result, mock_db
            )

            # Verify the call was made
            mock_create.assert_called_once()

            # Get the achievement data that was passed
            achievement_data = mock_create.call_args[0][1]

            # Verify all metrics were included
            metrics = achievement_data.metrics_after
            assert metrics["throughput_improvement_percent"] == 150.5
            assert metrics["infrastructure_savings_estimate"] == 80000
            assert metrics["user_experience_score"] == 9
            assert metrics["roi_year_one_percent"] == 234
            assert metrics["peak_rps"] == 673.9
            assert metrics["latency_ms"] == 50
            assert metrics["overall_score"] == 8.1

            # Verify tags
            assert "pr-123" in achievement_data.tags
            assert "score-8" in achievement_data.tags
            assert "high_performance_implementation" in achievement_data.tags

            # Verify portfolio readiness
            assert achievement_data.portfolio_ready is True  # Score is 8.1

            # Verify metadata
            assert achievement_data.metadata["pr_number"] == "123"
            assert "value_analysis" in achievement_data.metadata
            assert "future_impact" in achievement_data.metadata
