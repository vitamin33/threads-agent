"""
Integration tests for shared models working together
"""

import pytest
from datetime import datetime, timedelta

from services.common.models.achievement_models import (
    Achievement,
    AchievementCategory,
    AchievementMetrics,
    AchievementFilter,
)
from services.common.models.article_models import (
    ArticleType,
    Platform,
    ArticleContent,
    ArticleMetadata,
    ContentRequest,
    ContentResponse,
    InsightScore,
)


class TestAchievementToArticleFlow:
    """Test the complete flow from achievement to article generation"""

    @pytest.fixture
    def sample_achievement(self):
        """Create a sample achievement"""
        return Achievement(
            id=1,
            title="Implemented Real-time Analytics Dashboard",
            description="Built a comprehensive real-time analytics dashboard that processes 1M+ events per second",
            category=AchievementCategory.FEATURE,
            impact_score=92.0,
            complexity_score=88.0,
            business_value="Reduced decision-making time by 70%, increased revenue by $2M annually",
            technical_details={
                "architecture": "Event-driven microservices",
                "technologies": ["Kafka", "ClickHouse", "React", "WebSockets"],
                "challenges": ["Scale", "Real-time processing", "Data consistency"],
            },
            technologies_used=["Python", "TypeScript", "Kafka", "ClickHouse"],
            metrics=AchievementMetrics(
                time_saved_hours=40,
                revenue_impact_dollars=2000000,
                performance_improvement_percent=300,
                users_impacted=10000,
            ),
            tags=["real-time", "analytics", "dashboard", "scalability"],
            portfolio_ready=True,
            source_type="github_pr",
            source_id="PR-456",
            started_at=datetime.now() - timedelta(days=30),
            completed_at=datetime.now() - timedelta(days=5),
            created_at=datetime.now() - timedelta(days=5),
        )

    def test_achievement_to_content_request(self, sample_achievement):
        """Test converting achievement to content request"""
        # Create content request based on achievement
        request = ContentRequest(
            achievement_ids=[sample_achievement.id],
            article_types=[
                ArticleType.CASE_STUDY,  # High impact → case study
                ArticleType.TECHNICAL_DEEP_DIVE,  # Complex technical details
                ArticleType.ARCHITECTURE_OVERVIEW,  # Architecture mentioned
            ],
            platforms=[Platform.LINKEDIN, Platform.DEVTO, Platform.MEDIUM],
            auto_publish=False,
            quality_threshold=8.0,
            target_audience="engineering leaders and architects",
            context={
                "achievement_score": sample_achievement.impact_score,
                "key_metrics": {
                    "revenue_impact": sample_achievement.metrics.revenue_impact_dollars,
                    "users_impacted": sample_achievement.metrics.users_impacted,
                },
            },
        )

        assert len(request.achievement_ids) == 1
        assert len(request.article_types) == 3
        assert request.context["achievement_score"] == 92.0

    def test_generate_articles_from_achievement(self, sample_achievement):
        """Test generating multiple articles from achievement"""
        articles = []

        # Generate case study for LinkedIn
        case_study = ArticleContent(
            article_type=ArticleType.CASE_STUDY,
            platform=Platform.LINKEDIN,
            title=f"Case Study: {sample_achievement.title}",
            subtitle="How we built a system processing 1M+ events/second",
            content=f"""
            When faced with the challenge of providing real-time insights to our users,
            we embarked on building a comprehensive analytics dashboard. This case study
            explores our journey from concept to a production system handling over 1 million
            events per second.
            
            **The Challenge**
            {sample_achievement.description}
            
            **Business Impact**
            {sample_achievement.business_value}
            
            **Technical Approach**
            We leveraged {", ".join(sample_achievement.technologies_used)} to build
            an event-driven architecture that could scale horizontally...
            """
            + "x" * 500,  # Ensure minimum content length
            tags=sample_achievement.tags + ["case-study"],
            metadata=ArticleMetadata(
                achievement_id=sample_achievement.id,
                source_type="achievement",
                word_count=850,
                reading_time_minutes=4,
                code_snippets_count=3,
            ),
        )
        articles.append(case_study)

        # Generate technical deep dive for Dev.to
        tech_dive = ArticleContent(
            article_type=ArticleType.TECHNICAL_DEEP_DIVE,
            platform=Platform.DEVTO,
            title="Building a Real-time Analytics System: Technical Deep Dive",
            content="""
            ## Introduction
            
            In this technical deep dive, we'll explore the architecture and implementation
            details of our real-time analytics dashboard that processes over 1 million events
            per second.
            
            ## Architecture Overview
            
            ```mermaid
            graph LR
                A[Event Sources] --> B[Kafka]
                B --> C[Stream Processors]
                C --> D[ClickHouse]
                D --> E[API Layer]
                E --> F[React Dashboard]
            ```
            
            ## Key Technologies
            
            - **Kafka**: Event streaming backbone
            - **ClickHouse**: Real-time analytics database
            - **React + WebSockets**: Live dashboard updates
            
            ## Implementation Details...
            """
            + "x" * 1000,
            code_snippets=[
                {
                    "language": "python",
                    "code": "# Kafka consumer example\nconsumer = KafkaConsumer('events')",
                    "description": "Event consumer setup",
                }
            ],
            tags=["technical", "architecture", "real-time", "tutorial"],
            metadata=ArticleMetadata(
                achievement_id=sample_achievement.id,
                word_count=1500,
                reading_time_minutes=7,
                code_snippets_count=8,
            ),
        )
        articles.append(tech_dive)

        assert len(articles) == 2
        assert all(
            article.metadata.achievement_id == sample_achievement.id
            for article in articles
        )
        assert articles[0].platform == Platform.LINKEDIN
        assert articles[1].platform == Platform.DEVTO

    def test_content_response_with_quality_scores(self, sample_achievement):
        """Test creating content response with quality assessments"""
        # Create articles (simplified)
        articles = [
            ArticleContent(
                article_type=ArticleType.CASE_STUDY,
                platform=Platform.LINKEDIN,
                title="Real-time Analytics Case Study",
                content="Detailed case study content..." + "x" * 200,
            )
        ]

        # Create response with quality scores
        response = ContentResponse(
            request_id="req_achievement_1",
            status="success",
            articles=articles,
            total_generated=1,
            average_quality_score=8.5,
            highest_quality_article_id="article_1",
            generation_time_seconds=35.2,
            total_tokens_used=2500,
            estimated_cost_usd=0.10,
            recommendations=[
                "Add more specific performance metrics",
                "Include architecture diagrams",
                "Expand on lessons learned section",
            ],
        )

        assert response.status == "success"
        assert response.average_quality_score == 8.5
        assert len(response.recommendations) == 3


class TestCompanyTargetedContent:
    """Test generating company-specific content from achievements"""

    @pytest.fixture
    def ml_achievements(self):
        """Create ML/AI focused achievements"""
        return [
            Achievement(
                id=10,
                title="Built ML Model Serving Infrastructure",
                description="Implemented scalable ML model serving with A/B testing",
                category=AchievementCategory.AI_ML,
                impact_score=88.0,
                business_value="Reduced model deployment time from days to minutes",
                technologies_used=["Python", "TensorFlow", "Kubernetes", "MLflow"],
                tags=["ml", "infrastructure", "deployment"],
                portfolio_ready=True,
                started_at=datetime.now() - timedelta(days=60),
                completed_at=datetime.now() - timedelta(days=30),
                created_at=datetime.now(),
            ),
            Achievement(
                id=11,
                title="Implemented RAG-based Documentation Assistant",
                description="Built AI assistant for technical documentation using RAG",
                category=AchievementCategory.AI_ML,
                impact_score=85.0,
                business_value="Improved developer productivity by 40%",
                technologies_used=["Python", "LangChain", "Pinecone", "OpenAI"],
                tags=["ai", "rag", "llm", "documentation"],
                portfolio_ready=True,
                started_at=datetime.now() - timedelta(days=45),
                completed_at=datetime.now() - timedelta(days=20),
                created_at=datetime.now(),
            ),
        ]

    def test_filter_achievements_for_anthropic(self, ml_achievements):
        """Test filtering achievements for Anthropic (AI safety focus)"""
        # Create filter for Anthropic-relevant achievements
        filter_obj = AchievementFilter(
            categories=[AchievementCategory.AI_ML],
            tags=["ai", "llm", "safety", "monitoring"],
            company_keywords=["safety", "responsible", "ethical", "alignment"],
            min_impact_score=80.0,
            portfolio_ready_only=True,
        )

        # The RAG assistant would be relevant (responsible AI use)
        relevant = [
            a for a in ml_achievements if any(tag in ["ai", "llm"] for tag in a.tags)
        ]
        assert len(relevant) == 1
        assert relevant[0].id == 11

    def test_generate_anthropic_targeted_article(self, ml_achievements):
        """Test generating Anthropic-targeted content"""
        achievement = ml_achievements[1]  # RAG assistant

        article = ArticleContent(
            article_type=ArticleType.BEST_PRACTICES,
            platform=Platform.MEDIUM,
            title="Building Responsible AI: Lessons from Implementing a RAG-based Assistant",
            subtitle="How we ensured safety and reliability in our AI documentation system",
            content=f"""
            As AI systems become more prevalent in software development, ensuring they
            operate safely and reliably becomes paramount. In this article, I'll share
            our experience building a RAG-based documentation assistant with a focus on
            responsible AI practices.
            
            ## The Safety-First Approach
            
            When we set out to build our documentation assistant, we established several
            key principles:
            
            1. **Grounded Responses**: Using RAG to ensure factual accuracy
            2. **Transparent Limitations**: Clear communication of what the AI can't do
            3. **Human-in-the-loop**: Maintaining human oversight for critical decisions
            
            ## Implementation Details
            
            {achievement.description}
            
            ## Measuring Success Responsibly
            
            Beyond traditional metrics, we tracked:
            - Factual accuracy rate: 98.5%
            - User trust scores
            - Instances where the AI correctly declined to answer
            
            ## Lessons Learned
            
            Building AI systems that are both powerful and responsible requires...
            """
            + "x" * 500,
            tags=["ai-safety", "responsible-ai", "best-practices", "rag"],
            metadata=ArticleMetadata(
                achievement_id=achievement.id,
                custom={
                    "target_company": "anthropic",
                    "focus_areas": ["safety", "reliability", "transparency"],
                },
            ),
        )

        assert article.article_type == ArticleType.BEST_PRACTICES
        assert "responsible" in article.title.lower()
        assert article.metadata.custom["target_company"] == "anthropic"


class TestContentQualityAssessment:
    """Test quality assessment integration"""

    def test_insight_score_for_article(self):
        """Test creating insight scores for generated articles"""
        article = ArticleContent(
            article_type=ArticleType.CASE_STUDY,
            platform=Platform.LINKEDIN,
            title="Scaling to 1M Users: Our Journey",
            content="Comprehensive case study..." + "x" * 500,
        )

        # Create quality assessment
        score = InsightScore(
            overall_score=8.5,
            technical_depth=9.0,  # Deep technical content
            business_value=8.5,  # Clear business impact
            clarity=8.0,  # Well structured
            originality=7.5,  # Some unique insights
            platform_relevance=9.0,  # Perfect for LinkedIn
            engagement_potential=8.5,  # Should drive engagement
            strengths=[
                "Excellent technical depth with concrete examples",
                "Clear business value proposition",
                "Well-suited for LinkedIn professional audience",
            ],
            improvements=[
                "Add more visual elements (charts/diagrams)",
                "Include specific metrics on cost savings",
            ],
        )

        assert score.overall_score == 8.5
        assert score.platform_relevance == 9.0
        assert len(score.strengths) == 3
        assert len(score.improvements) == 2

    def test_quality_threshold_filtering(self):
        """Test filtering articles by quality threshold"""
        articles_with_scores = [
            (
                ArticleContent(
                    article_type=ArticleType.TUTORIAL,
                    platform=Platform.DEVTO,
                    title=f"Tutorial {i}",
                    content="Tutorial content..." + "x" * 100,
                ),
                6.5 + i * 0.5,
            )
            for i in range(5)
        ]

        # Filter by quality threshold of 8.0
        quality_threshold = 8.0
        high_quality = [
            (article, score)
            for article, score in articles_with_scores
            if score >= quality_threshold
        ]

        assert len(high_quality) == 2  # Only the last 2 meet threshold
        assert all(score >= 8.0 for _, score in high_quality)
