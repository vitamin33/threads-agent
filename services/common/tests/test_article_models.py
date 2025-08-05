"""
Tests for shared article and content models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from services.common.models.article_models import (
    ArticleType,
    Platform,
    InsightScore,
    ArticleMetadata,
    ArticleContent,
    ContentRequest,
    ContentResponse,
)


class TestArticleType:
    """Test ArticleType enum"""

    def test_article_types(self):
        """Test all article type values"""
        assert ArticleType.TUTORIAL.value == "tutorial"
        assert ArticleType.CASE_STUDY.value == "case_study"
        assert ArticleType.TECHNICAL_DEEP_DIVE.value == "technical_deep_dive"

        # Verify we have all expected types
        expected_types = [
            "tutorial",
            "case_study",
            "technical_deep_dive",
            "architecture_overview",
            "best_practices",
            "performance_optimization",
        ]

        actual_types = [t.value for t in ArticleType]
        for expected in expected_types:
            assert expected in actual_types


class TestPlatform:
    """Test Platform enum"""

    def test_platforms(self):
        """Test all platform values"""
        assert Platform.LINKEDIN.value == "linkedin"
        assert Platform.DEVTO.value == "devto"
        assert Platform.MEDIUM.value == "medium"

        # Test all platforms are accessible
        platforms = [p.value for p in Platform]
        assert "github" in platforms
        assert "twitter" in platforms


class TestInsightScore:
    """Test InsightScore model"""

    def test_valid_score(self):
        """Test creating valid insight score"""
        score = InsightScore(
            overall_score=8.5,
            technical_depth=9.0,
            business_value=8.0,
            clarity=8.5,
            originality=7.5,
            platform_relevance=9.0,
            engagement_potential=8.0,
            strengths=["Clear examples", "Good structure"],
            improvements=["Add more visuals"],
        )

        assert score.overall_score == 8.5
        assert score.technical_depth == 9.0
        assert len(score.strengths) == 2

    def test_score_constraints(self):
        """Test score value constraints"""
        # Score > 10 should fail
        with pytest.raises(ValidationError):
            InsightScore(
                overall_score=11,
                technical_depth=8,
                business_value=8,
                clarity=8,
                originality=8,
                platform_relevance=8,
                engagement_potential=8,
            )

        # Negative score should fail
        with pytest.raises(ValidationError):
            InsightScore(
                overall_score=-1,
                technical_depth=8,
                business_value=8,
                clarity=8,
                originality=8,
                platform_relevance=8,
                engagement_potential=8,
            )

    def test_overall_score_validation(self):
        """Test overall score auto-adjustment"""
        # If overall score is way off from components, it should adjust
        score = InsightScore(
            overall_score=2.0,  # Way too low given components
            technical_depth=8.0,
            business_value=8.0,
            clarity=8.0,
            originality=8.0,
            platform_relevance=8.0,
            engagement_potential=8.0,
        )

        # Overall should be adjusted to be closer to component average
        assert score.overall_score == 8.0  # Average of components


class TestArticleMetadata:
    """Test ArticleMetadata model"""

    def test_default_metadata(self):
        """Test metadata with default values"""
        metadata = ArticleMetadata()

        assert metadata.source_type == "achievement"
        assert metadata.published is False
        assert metadata.views == 0
        assert isinstance(metadata.generated_at, datetime)
        assert metadata.keywords == []

    def test_complete_metadata(self):
        """Test metadata with all fields"""
        metadata = ArticleMetadata(
            source_type="codebase",
            source_id="src/main.py",
            achievement_id=123,
            generation_time_seconds=45.5,
            model_used="gpt-4",
            prompt_tokens=1500,
            completion_tokens=2000,
            word_count=1200,
            reading_time_minutes=6,
            code_snippets_count=5,
            keywords=["python", "fastapi", "async"],
            categories=["backend", "api"],
            published=True,
            published_at=datetime.now(),
            published_url="https://dev.to/user/article",
            views=150,
            likes=25,
            comments=5,
            custom={"featured": True},
        )

        assert metadata.source_type == "codebase"
        assert metadata.achievement_id == 123
        assert metadata.word_count == 1200
        assert metadata.views == 150
        assert metadata.custom["featured"] is True


class TestArticleContent:
    """Test ArticleContent model"""

    @pytest.fixture
    def valid_article_data(self):
        """Valid article content data"""
        return {
            "article_type": ArticleType.CASE_STUDY,
            "platform": Platform.LINKEDIN,
            "title": "How We Reduced API Latency by 80% Using Smart Caching",
            "subtitle": "A deep dive into our caching strategy",
            "content": "In this case study, we'll explore how our team successfully reduced API latency from 500ms to under 100ms through intelligent caching strategies. The journey began when we noticed increasing user complaints about slow response times...",
        }

    def test_valid_article(self, valid_article_data):
        """Test creating valid article content"""
        article = ArticleContent(**valid_article_data)

        assert article.article_type == ArticleType.CASE_STUDY
        assert article.platform == Platform.LINKEDIN
        assert article.title == "How We Reduced API Latency by 80% Using Smart Caching"
        assert len(article.content) > 100

    def test_article_validation(self):
        """Test article validation rules"""
        # Title too short
        with pytest.raises(ValidationError):
            ArticleContent(
                article_type=ArticleType.TUTORIAL,
                platform=Platform.DEVTO,
                title="Short",
                content="A" * 100,
            )

        # Content too short
        with pytest.raises(ValidationError):
            ArticleContent(
                article_type=ArticleType.TUTORIAL,
                platform=Platform.DEVTO,
                title="Valid Title Here",
                content="Too short",
            )

    def test_article_with_sections(self, valid_article_data):
        """Test article with structured sections"""
        valid_article_data["sections"] = [
            {"heading": "Introduction", "content": "Overview of the problem"},
            {"heading": "Solution", "content": "Our caching approach"},
            {"heading": "Results", "content": "Performance improvements"},
        ]
        valid_article_data["code_snippets"] = [
            {
                "language": "python",
                "code": "cache = Redis()",
                "description": "Initialize cache",
            }
        ]

        article = ArticleContent(**valid_article_data)

        assert len(article.sections) == 3
        assert article.sections[0]["heading"] == "Introduction"
        assert len(article.code_snippets) == 1
        assert article.code_snippets[0]["language"] == "python"

    def test_tag_normalization(self, valid_article_data):
        """Test tag normalization"""
        valid_article_data["tags"] = ["Python", "CACHING", " optimization "]

        article = ArticleContent(**valid_article_data)

        assert article.tags == ["python", "caching", "optimization"]

    def test_formatted_content(self, valid_article_data):
        """Test platform-specific formatting"""
        valid_article_data["formatted_content"] = {
            "markdown": "# How We Reduced API Latency\n\n...",
            "html": "<h1>How We Reduced API Latency</h1><p>...</p>",
        }

        article = ArticleContent(**valid_article_data)

        assert "markdown" in article.formatted_content
        assert "html" in article.formatted_content


class TestContentRequest:
    """Test ContentRequest model"""

    def test_minimal_request(self):
        """Test minimal content request"""
        request = ContentRequest(
            article_types=[ArticleType.TUTORIAL], platforms=[Platform.DEVTO]
        )

        assert len(request.article_types) == 1
        assert len(request.platforms) == 1
        assert request.auto_publish is False
        assert request.quality_threshold == 7.0

    def test_achievement_based_request(self):
        """Test request for achievement-based content"""
        request = ContentRequest(
            achievement_ids=[1, 2, 3],
            article_types=[ArticleType.CASE_STUDY, ArticleType.LESSONS_LEARNED],
            platforms=[Platform.LINKEDIN, Platform.MEDIUM],
            auto_publish=True,
            quality_threshold=8.0,
            target_company="notion",
            target_audience="engineering leaders",
            tone="technical",
        )

        assert len(request.achievement_ids) == 3
        assert request.target_company == "notion"
        assert request.tone == "technical"
        assert request.auto_publish is True

    def test_request_validation(self):
        """Test request validation"""
        # Invalid tone
        with pytest.raises(ValidationError):
            ContentRequest(
                article_types=[ArticleType.TUTORIAL],
                platforms=[Platform.DEVTO],
                tone="funny",  # Not in allowed values
            )

        # Quality threshold out of range
        with pytest.raises(ValidationError):
            ContentRequest(
                article_types=[ArticleType.TUTORIAL],
                platforms=[Platform.DEVTO],
                quality_threshold=11,
            )


class TestContentResponse:
    """Test ContentResponse model"""

    @pytest.fixture
    def sample_articles(self):
        """Sample articles for response"""
        return [
            ArticleContent(
                article_type=ArticleType.TUTORIAL,
                platform=Platform.DEVTO,
                title="Getting Started with FastAPI",
                content="FastAPI is a modern web framework..." + "x" * 100,
            ),
            ArticleContent(
                article_type=ArticleType.CASE_STUDY,
                platform=Platform.LINKEDIN,
                title="How We Built a Scalable API",
                content="In this case study..." + "x" * 100,
            ),
        ]

    def test_successful_response(self, sample_articles):
        """Test successful content response"""
        response = ContentResponse(
            request_id="req_123",
            status="success",
            articles=sample_articles,
            total_generated=2,
            average_quality_score=8.5,
            highest_quality_article_id="art_1",
            generation_time_seconds=45.3,
            total_tokens_used=3500,
            estimated_cost_usd=0.15,
            recommendations=["Consider adding more code examples"],
        )

        assert response.status == "success"
        assert response.total_generated == 2
        assert len(response.articles) == 2
        assert response.average_quality_score == 8.5
        assert response.estimated_cost_usd == 0.15

    def test_partial_response(self, sample_articles):
        """Test partial success response"""
        response = ContentResponse(
            request_id="req_124",
            status="partial",
            articles=sample_articles[:1],  # Only one article
            total_generated=1,
            average_quality_score=7.0,
            generation_time_seconds=30.0,
            total_tokens_used=2000,
            estimated_cost_usd=0.08,
            publishing_errors=[
                {"platform": "medium", "error": "Authentication failed"}
            ],
        )

        assert response.status == "partial"
        assert len(response.articles) == 1
        assert len(response.publishing_errors) == 1

    def test_response_with_publishing(self, sample_articles):
        """Test response with auto-publishing results"""
        response = ContentResponse(
            request_id="req_125",
            status="success",
            articles=sample_articles,
            total_generated=2,
            average_quality_score=9.0,
            generation_time_seconds=50.0,
            total_tokens_used=4000,
            estimated_cost_usd=0.18,
            published_count=2,
            recommendations=[],
        )

        assert response.published_count == 2
        assert response.publishing_errors == []
