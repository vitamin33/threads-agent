"""Test AI Insights Integration

Tests the new AI insights storage and retrieval functionality.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from services.achievement_collector.services.pr_value_analyzer_integration import (
    PRValueAnalyzerIntegration,
)
from services.achievement_collector.utils.ai_insights_retriever import (
    AIInsightsRetriever,
)
from services.achievement_collector.db.models import Achievement


@pytest.fixture
def mock_pr_analysis_with_ai_insights():
    """Mock PR analysis data with AI insights."""
    return {
        "pr_number": "91",
        "timestamp": datetime.now().isoformat(),
        "business_metrics": {
            "throughput_improvement_percent": 140.0,
            "infrastructure_savings_estimate": 16680.0,
            "roi_year_one_percent": 1112.0,
            "developer_productivity_savings": 564480.0,
        },
        "technical_metrics": {
            "performance": {"peak_rps": 1200.0, "latency_ms": 150, "test_coverage": 87},
            "innovation_score": 10.0,
        },
        "achievement_tags": ["high_performance_implementation", "ai_ml_feature"],
        "kpis": {
            "overall_score": 8.6,
            "performance_score": 7.0,
            "quality_score": 8.7,
            "business_value_score": 10.0,
            "innovation_score": 10.0,
        },
        "future_impact": {
            "revenue_impact_3yr": 450000.0,
            "competitive_advantage": "high",
        },
    }


@pytest.fixture
def mock_achievement_file_with_ai_insights():
    """Mock achievement file with AI insights."""
    return {
        "pr_number": "91",
        "timestamp": datetime.now().isoformat(),
        "tags": ["high_performance_implementation"],
        "metrics": {"peak_rps": 1200.0, "test_coverage": 87},
        "kpis": {"overall_score": 8.6},
        "ai_insights": {
            "improvement_suggestions": [],
            "score_explanations": {
                "innovation": "exceptional technical complexity and novel approach",
                "performance": "good performance metrics provided",
                "quality": "excellent test coverage (87%)",
                "business": "strong business value with clear ROI",
            },
            "interview_talking_points": [
                "Achieved 1200 RPS - exceeding industry standards",
                "Delivered $16,680 annual infrastructure savings",
                "Implemented 87% test coverage",
                "1112% first-year ROI with 1.1 month payback",
            ],
            "article_suggestions": {
                "technical_deep_dives": [
                    "How We Achieved 1200+ RPS with Python and FastAPI",
                    "Building Production-Ready RAG Pipelines: A Complete Guide",
                ],
                "business_case_studies": [
                    "Case Study: 1112% ROI from Performance Optimization"
                ],
                "best_practices": [
                    "Achieving 87% Test Coverage in Production Microservices"
                ],
                "lessons_learned": [
                    "From Concept to Production: Building a High-Performance RAG System"
                ],
            },
            "portfolio_summary": "**High-Performance RAG Pipeline Implementation**\n\nLed the development...",
        },
        "calculation_methodology": {
            "roi_formula": "ROI = (Annual Savings - Total Investment) / Total Investment × 100"
        },
        "schema_version": "3.0",
    }


class TestAIInsightsIntegration:
    """Test AI insights storage and retrieval."""

    def test_extract_ai_insights_from_achievement_file(
        self, tmp_path, mock_achievement_file_with_ai_insights
    ):
        """Test extracting AI insights from achievement file."""
        # Create mock achievement file
        achievement_dir = tmp_path / ".achievements"
        achievement_dir.mkdir()
        achievement_file = achievement_dir / "pr_91_achievement.json"

        with open(achievement_file, "w") as f:
            json.dump(mock_achievement_file_with_ai_insights, f)

        # Test extraction
        integration = PRValueAnalyzerIntegration()
        with patch(
            "services.achievement_collector.services.pr_value_analyzer_integration.Path"
        ) as mock_path:
            mock_path.return_value = achievement_file

            insights = integration._extract_ai_insights_from_achievement_file("91")

            assert insights is not None
            assert "interview_talking_points" in insights
            assert len(insights["interview_talking_points"]) == 4
            assert "article_suggestions" in insights
            assert "portfolio_summary" in insights

    def test_create_achievement_with_ai_insights(
        self,
        mock_db_session,
        mock_pr_analysis_with_ai_insights,
        mock_achievement_file_with_ai_insights,
    ):
        """Test creating achievement with AI insights in metadata."""
        integration = PRValueAnalyzerIntegration()

        # Mock the file reading
        with patch.object(
            integration, "_extract_ai_insights_from_achievement_file"
        ) as mock_extract:
            mock_extract.return_value = mock_achievement_file_with_ai_insights[
                "ai_insights"
            ]

            # Mock the achievement creation
            with patch(
                "services.achievement_collector.api.routes.achievements.create_achievement_sync"
            ) as mock_create:
                mock_achievement = MagicMock()
                mock_achievement.metadata_json = {
                    "ai_insights": mock_achievement_file_with_ai_insights["ai_insights"]
                }
                mock_create.return_value = mock_achievement

                # Create achievement
                integration._create_enriched_achievement(
                    "91", mock_pr_analysis_with_ai_insights, mock_db_session
                )

                # Verify AI insights were included
                assert mock_create.called
                call_args = mock_create.call_args[0][1]  # Get AchievementCreate object
                assert "ai_insights" in call_args.metadata
                assert call_args.metadata["ai_insights"]["interview_talking_points"]

    def test_ai_insights_retriever(self, mock_db_session):
        """Test AI insights retriever functionality."""
        # Create mock achievement with AI insights
        achievement = Achievement(
            id=1,
            title="High-Impact PR #91",
            source_type="github_pr",
            source_id="PR-91",
            metadata_json={
                "ai_insights": {
                    "interview_talking_points": [
                        "Achieved 1200 RPS",
                        "87% test coverage",
                    ],
                    "article_suggestions": {
                        "technical_deep_dives": ["How We Achieved 1200+ RPS"]
                    },
                    "portfolio_summary": "Led development of RAG pipeline...",
                }
            },
        )

        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            achievement
        )

        retriever = AIInsightsRetriever()

        # Test getting interview points
        points = retriever.get_interview_talking_points(mock_db_session, "91")
        assert len(points) == 2
        assert "1200 RPS" in points[0]

        # Test getting article suggestions
        suggestions = retriever.get_article_suggestions(mock_db_session, "91")
        assert "technical_deep_dives" in suggestions
        assert len(suggestions["technical_deep_dives"]) == 1

        # Test getting portfolio summary
        summary = retriever.get_portfolio_summary(mock_db_session, "91")
        assert "RAG pipeline" in summary

    def test_generate_blog_post_outline(self, mock_db_session):
        """Test blog post outline generation."""
        achievement = Achievement(
            id=1,
            title="High-Performance RAG Implementation",
            description="Implemented production-ready RAG pipeline",
            source_type="github_pr",
            source_id="PR-91",
            metrics_after={
                "peak_rps": 1200,
                "latency_ms": 150,
                "test_coverage": 87,
                "roi_year_one_percent": 1112,
                "infrastructure_savings_estimate": 16680,
                "productivity_hours_saved": 3763,
            },
            skills_demonstrated=["Python", "FastAPI", "Kubernetes"],
            metadata_json={
                "ai_insights": {
                    "interview_talking_points": [
                        "Achieved 1200 RPS",
                        "87% test coverage",
                        "1112% ROI",
                    ],
                    "score_explanations": {
                        "innovation": "Novel RAG implementation",
                        "quality": "Comprehensive test coverage",
                    },
                    "article_suggestions": {
                        "technical_deep_dives": [
                            "Building RAG Pipelines",
                            "Performance at Scale",
                        ]
                    },
                }
            },
        )

        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            achievement
        )

        retriever = AIInsightsRetriever()
        outline = retriever.generate_blog_post_outline(mock_db_session, "91")

        # Verify outline contains key sections
        assert "# High-Performance RAG Implementation" in outline
        assert "## Key Achievements" in outline
        assert "- Achieved 1200 RPS" in outline
        assert "## Technical Deep Dive" in outline
        assert "**Throughput**: 1200 RPS" in outline
        assert "## Business Impact" in outline
        assert "**ROI**: 1112%" in outline
        assert "## Next Steps" in outline
        assert "- Building RAG Pipelines" in outline


class TestAPIEndpoints:
    """Test new API endpoints for AI insights."""

    @pytest.mark.asyncio
    async def test_get_pr_ai_insights_endpoint(self, test_client, mock_db_session):
        """Test /ai-insights/{pr_number} endpoint."""
        # Mock achievement with AI insights
        achievement = Achievement(
            id=1,
            title="PR #91",
            source_type="github_pr",
            source_id="PR-91",
            metrics_after={"overall_score": 8.6},
            metadata_json={
                "ai_insights": {
                    "interview_talking_points": ["Point 1", "Point 2"],
                    "article_suggestions": {
                        "technical_deep_dives": ["Article 1"],
                        "business_case_studies": ["Case 1", "Case 2"],
                    },
                    "portfolio_summary": "Summary text",
                }
            },
        )

        mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
            achievement
        )

        response = test_client.get("/pr-analysis/ai-insights/91")

        assert response.status_code == 200
        data = response.json()
        assert data["pr_number"] == "91"
        assert data["interview_points_count"] == 2
        assert data["article_suggestions_count"] == 3
        assert data["has_portfolio_summary"] is True

    @pytest.mark.asyncio
    async def test_get_all_article_ideas_endpoint(self, test_client, mock_db_session):
        """Test /article-ideas endpoint."""
        # Mock multiple achievements
        achievements = [
            Achievement(
                id=1,
                source_type="github_pr",
                source_id="PR-91",
                title="High-Performance RAG",
                impact_score=86,
                metadata_json={
                    "ai_insights": {
                        "article_suggestions": {
                            "technical_deep_dives": ["RAG at Scale"],
                            "business_case_studies": ["1000% ROI Story"],
                        }
                    }
                },
            ),
            Achievement(
                id=2,
                source_type="github_pr",
                source_id="PR-92",
                title="Kubernetes Optimization",
                impact_score=75,
                metadata_json={
                    "ai_insights": {
                        "article_suggestions": {
                            "technical_deep_dives": ["K8s Performance"],
                            "best_practices": ["Container Best Practices"],
                        }
                    }
                },
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.all.return_value = (
            achievements
        )

        response = test_client.get("/pr-analysis/article-ideas?min_score=7.0")

        assert response.status_code == 200
        data = response.json()
        assert data["total_achievements_analyzed"] == 2
        assert data["total_ideas"] == 4
        assert len(data["article_ideas"]["technical_deep_dives"]) == 2
        assert len(data["article_ideas"]["business_case_studies"]) == 1
        assert len(data["article_ideas"]["best_practices"]) == 1


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    return session


@pytest.fixture
def test_client():
    """Mock test client for API testing."""
    from fastapi.testclient import TestClient
    from services.achievement_collector.main import app

    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
