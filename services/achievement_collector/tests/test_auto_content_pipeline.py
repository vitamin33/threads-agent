"""
Test suite for automatic content generation and publishing pipeline.

This tests the complete flow:
1. GitHub webhook receives PR merge notification
2. Auto-content generation is triggered 
3. Content includes serbyn.pro CTAs and UTM tracking
4. Content is published to all 6 platforms automatically
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAutoContentPipeline:
    """Test the automatic content generation and publishing pipeline"""

    @pytest.fixture
    def github_pr_merge_webhook_payload(self):
        """Sample GitHub webhook payload for PR merge"""
        return {
            "action": "closed",
            "number": 123,
            "pull_request": {
                "merged": True,
                "merged_at": "2024-01-15T14:30:00Z",
                "title": "feat: implement MLflow model registry with automated rollback",
                "body": "This PR adds automated model rollback capabilities using MLflow registry. Includes performance monitoring and SLO-based rollback triggers.\n\n## Changes\n- MLflow registry integration\n- Performance monitoring\n- Automated rollback logic\n- SLO threshold configuration\n\n## Impact\n- 99.5% model uptime\n- 60% reduction in manual interventions\n- $50k/year operational savings",
                "base": {"ref": "main"},
                "head": {"ref": "feat/mlflow-rollback"},
                "user": {"login": "vitamin33"},
                "labels": [{"name": "feature"}, {"name": "mlops"}],
                "files": [
                    {"filename": "services/ml_registry/rollback.py"},
                    {"filename": "tests/test_rollback.py"},
                ],
            },
            "repository": {
                "name": "threads-agent",
                "full_name": "vitamin33/threads-agent",
                "html_url": "https://github.com/vitamin33/threads-agent",
            },
        }

    @pytest.fixture
    def mock_auto_pipeline(self):
        """Mock auto content pipeline"""
        with patch(
            "services.achievement_collector.services.auto_content_pipeline.AutoContentPipeline"
        ) as mock:
            pipeline = AsyncMock()
            mock.return_value = pipeline
            yield pipeline

    def test_auto_content_pipeline_does_not_exist_yet(self):
        """FAILING TEST: AutoContentPipeline service doesn't exist yet"""
        # This test should fail because we haven't created the service yet
        with pytest.raises(ImportError):
            from services.achievement_collector.services.auto_content_pipeline import (
                AutoContentPipeline,
            )

    async def test_webhook_triggers_content_generation_on_pr_merge(
        self, github_pr_merge_webhook_payload, mock_auto_pipeline, db_session
    ):
        """FAILING TEST: Webhook should trigger auto-content generation for PR merges"""
        
        # This test will fail because the webhook doesn't trigger content generation yet
        client = TestClient(router)
        
        # Mock the pipeline trigger
        mock_auto_pipeline.should_generate_content.return_value = True
        mock_auto_pipeline.generate_and_publish.return_value = {
            "content_generated": True,
            "platforms_published": 6,
            "content_id": "content_123",
        }

        response = client.post(
            "/github",
            json=github_pr_merge_webhook_payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=test-signature",
            },
        )

        assert response.status_code == 200
        
        # Should trigger content generation for significant PR
        mock_auto_pipeline.should_generate_content.assert_called_once()
        mock_auto_pipeline.generate_and_publish.assert_called_once()
        
        response_data = response.json()
        assert response_data["achievement_created"] is True
        assert "content_generated" in response_data
        assert response_data["content_generated"] is True

    async def test_content_includes_serbyn_pro_cta_with_utm_tracking(self, mock_auto_pipeline):
        """FAILING TEST: Generated content should include serbyn.pro CTA with UTM tracking"""
        
        pipeline = AutoContentPipeline()
        
        achievement_data = {
            "title": "MLflow Model Registry Implementation",
            "description": "Automated model rollback with performance monitoring",
            "business_value": "60% reduction in manual interventions, $50k annual savings",
            "technical_details": {"technology": "MLflow", "impact": "99.5% uptime"},
            "category": "mlops",
        }
        
        request = ContentGenerationRequest(
            achievement_id=123,
            include_serbyn_pro_cta=True,
            utm_campaign="pr_automation",
            target_platforms=["devto", "linkedin", "medium", "github", "twitter", "threads"],
        )
        
        result = await pipeline.generate_content_with_cta(achievement_data, request)
        
        # Should include serbyn.pro CTA with UTM tracking
        assert "serbyn.pro" in result.content
        assert "utm_source=devto" in result.content or "utm_source=linkedin" in result.content
        assert "utm_campaign=pr_automation" in result.content
        assert "Currently seeking remote US AI/MLOps roles" in result.content

    async def test_publishes_to_all_six_platforms_automatically(self, mock_auto_pipeline):
        """FAILING TEST: Should publish to all 6 platforms automatically"""
        
        pipeline = AutoContentPipeline()
        
        publishing_request = PublishingRequest(
            content_id="content_123",
            platforms=["devto", "linkedin", "medium", "github", "twitter", "threads"],
            schedule_immediately=True,
        )
        
        result = await pipeline.publish_to_all_platforms(publishing_request)
        
        # Should publish to all 6 platforms
        assert result.total_platforms == 6
        assert result.successful_publications == 6
        assert len(result.published_urls) == 6
        
        # Should have different UTM parameters for each platform
        utm_sources = [url for url in result.published_urls if "utm_source=" in url]
        assert len(utm_sources) == 6

    async def test_filters_prs_that_should_not_generate_content(self, mock_auto_pipeline):
        """FAILING TEST: Should filter out trivial PRs that don't warrant content"""
        
        pipeline = AutoContentPipeline()
        
        # Trivial PR (typo fix)
        trivial_pr = {
            "title": "fix: typo in README.md",
            "body": "Fixed a typo",
            "files": [{"filename": "README.md"}],
            "labels": [{"name": "documentation"}],
        }
        
        # Significant PR (new feature)
        significant_pr = {
            "title": "feat: implement distributed model training",
            "body": "Adds distributed training with 80% speed improvement",
            "files": [
                {"filename": "services/ml_training/distributed.py"},
                {"filename": "tests/test_distributed.py"},
            ],
            "labels": [{"name": "feature"}, {"name": "performance"}],
        }
        
        assert pipeline.should_generate_content(trivial_pr) is False
        assert pipeline.should_generate_content(significant_pr) is True

    async def test_content_adapts_tone_for_different_platforms(self, mock_auto_pipeline):
        """FAILING TEST: Content should adapt tone for different platforms"""
        
        pipeline = AutoContentPipeline()
        
        achievement_data = {
            "title": "Cost Optimization: 40% AWS Reduction",
            "business_value": "$120k annual savings",
            "category": "cost-optimization",
        }
        
        # LinkedIn should be professional
        linkedin_content = await pipeline.generate_platform_content(
            achievement_data, platform="linkedin"
        )
        assert "professional achievement" in linkedin_content.lower()
        assert "🚀" not in linkedin_content  # Professional, minimal emojis
        
        # Dev.to should be technical
        devto_content = await pipeline.generate_platform_content(
            achievement_data, platform="devto"
        )
        assert "## Technical Implementation" in devto_content
        assert "Code Examples" in devto_content
        
        # Twitter should be concise thread
        twitter_content = await pipeline.generate_platform_content(
            achievement_data, platform="twitter"
        )
        assert isinstance(twitter_content, list)  # Thread format
        assert len(twitter_content[0]) <= 280  # Twitter character limit

    async def test_utm_tracking_parameters_are_unique_per_platform(self, mock_auto_pipeline):
        """FAILING TEST: Each platform should have unique UTM parameters"""
        
        pipeline = AutoContentPipeline()
        
        base_content = "Amazing MLOps achievement with business impact"
        
        platforms = ["devto", "linkedin", "medium", "github", "twitter", "threads"]
        utm_links = {}
        
        for platform in platforms:
            content_with_utm = await pipeline.add_utm_tracking(
                base_content, 
                platform=platform,
                campaign="pr_automation",
                content_type="case_study"
            )
            utm_links[platform] = content_with_utm
        
        # Each platform should have unique UTM source
        assert "utm_source=devto" in utm_links["devto"]
        assert "utm_source=linkedin" in utm_links["linkedin"]
        assert "utm_source=medium" in utm_links["medium"]
        assert "utm_source=github" in utm_links["github"]
        assert "utm_source=twitter" in utm_links["twitter"]
        assert "utm_source=threads" in utm_links["threads"]
        
        # All should have same campaign
        for content in utm_links.values():
            assert "utm_campaign=pr_automation" in content

    async def test_content_includes_call_to_action_for_hiring(self, mock_auto_pipeline):
        """FAILING TEST: Content should include clear hiring CTA"""
        
        pipeline = AutoContentPipeline()
        
        achievement_data = {
            "title": "AI Model Performance Optimization",
            "business_value": "300% inference speed improvement",
            "category": "ai-optimization",
        }
        
        content = await pipeline.generate_content_with_cta(
            achievement_data,
            ContentGenerationRequest(
                achievement_id=123,
                include_hiring_cta=True,
                target_role="MLOps Engineer",
                location_preference="Remote US",
            ),
        )
        
        # Should include hiring-focused CTA
        hiring_indicators = [
            "currently seeking",
            "remote us",
            "mlops engineer",
            "open to opportunities",
            "let's connect",
            "serbyn.pro",
        ]
        
        content_lower = content.content.lower()
        found_indicators = [indicator for indicator in hiring_indicators if indicator in content_lower]
        assert len(found_indicators) >= 3  # Should have multiple hiring signals


class TestContentQualityAndConversion:
    """Test content quality and conversion optimization"""

    async def test_content_follows_proven_viral_patterns(self):
        """FAILING TEST: Content should use proven engagement patterns"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            ContentOptimizer,
        )
        
        optimizer = ContentOptimizer()
        
        # Test content should use proven hooks
        hooks = await optimizer.generate_engaging_hooks(
            achievement_type="cost_optimization",
            business_impact="40% cost reduction",
        )
        
        # Should include proven patterns
        hook_patterns = [
            "here's how i",
            "most teams struggle",
            "3 mistakes i made",
            "after months of",
            "this saved us",
        ]
        
        assert any(pattern in hook.lower() for hook in hooks for pattern in hook_patterns)

    async def test_content_includes_social_proof_elements(self):
        """FAILING TEST: Content should include social proof for credibility"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            ContentOptimizer,
        )
        
        optimizer = ContentOptimizer()
        
        achievement_data = {
            "business_value": "$50k annual savings",
            "metrics": {"uptime": "99.5%", "interventions": "60% reduction"},
            "impact_score": 95,
        }
        
        content = await optimizer.add_social_proof(achievement_data)
        
        # Should include credibility elements
        proof_elements = [
            "$50k",  # Specific dollar amounts
            "99.5%",  # Specific percentages
            "60% reduction",  # Specific improvements
            "proven",  # Authority language
            "results",  # Outcome focus
        ]
        
        for element in proof_elements:
            assert element in content

    async def test_platform_specific_optimization_for_conversion(self):
        """FAILING TEST: Each platform should be optimized for its audience"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            PlatformOptimizer,
        )
        
        optimizer = PlatformOptimizer()
        
        base_achievement = {
            "title": "Machine Learning Pipeline Optimization",
            "business_value": "50% faster model training",
            "technical_details": {"framework": "PyTorch", "optimization": "distributed"},
        }
        
        # LinkedIn optimization (for recruiters/hiring managers)
        linkedin_content = await optimizer.optimize_for_platform(
            base_achievement, platform="linkedin"
        )
        assert "business impact" in linkedin_content.lower()
        assert "leadership" in linkedin_content.lower()
        assert len(linkedin_content) < 3000  # LinkedIn post length limit
        
        # Dev.to optimization (for developers/technical audience)
        devto_content = await optimizer.optimize_for_platform(
            base_achievement, platform="devto"
        )
        assert "## Code Examples" in devto_content
        assert "## Technical Implementation" in devto_content
        assert "PyTorch" in devto_content


class TestAIPoweredPREvaluation:
    """Test AI-powered PR evaluation system for intelligent content generation decisions"""

    @pytest.fixture
    def complex_technical_pr(self):
        """Complex technical PR that AI should identify as significant"""
        return {
            "pull_request": {
                "title": "refactor: database connection pooling",
                "body": "Refactored database connection pooling to use HikariCP with custom configurations. This change optimizes connection reuse patterns.",
                "labels": [{"name": "refactor"}],
                "files": [
                    {"filename": "src/database/pool.py", "changes": 150},
                    {"filename": "config/db.yaml", "changes": 20}
                ]
            }
        }

    @pytest.fixture
    def business_impact_pr(self):
        """PR with subtle business impact that AI should detect"""
        return {
            "pull_request": {
                "title": "update: cache invalidation strategy",
                "body": "Updated cache invalidation to reduce false cache hits. Implemented time-based and event-based invalidation patterns.",
                "labels": [{"name": "improvement"}],
                "files": [
                    {"filename": "src/cache/invalidation.py", "changes": 85}
                ]
            }
        }

    @pytest.fixture
    def trivial_pr(self):
        """Trivial PR that shouldn't generate content"""
        return {
            "pull_request": {
                "title": "fix: typo in variable name",
                "body": "Fixed typo in variable name from 'configuartion' to 'configuration'",
                "labels": [{"name": "typo"}],
                "files": [
                    {"filename": "src/config.py", "changes": 1}
                ]
            }
        }

    async def test_ai_significance_detector_identifies_complex_technical_achievement(self, complex_technical_pr):
        """FAILING TEST: AI should identify complex technical achievements that basic keyword matching misses"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        from unittest.mock import patch, AsyncMock
        
        evaluator = AIPoweredPREvaluator()
        
        # Mock the OpenAI API response for technical significance evaluation
        async def mock_create(*args, **kwargs):
            mock_response = AsyncMock()
            mock_response.choices = [
                AsyncMock(message=AsyncMock(content=json.dumps({
                    "score": 8.5,
                    "reasoning": "This PR demonstrates significant technical merit by implementing HikariCP connection pooling optimization. The refactoring shows deep understanding of database performance patterns and connection management best practices.",
                    "technical_merits": ["connection pooling optimization", "performance improvement", "architecture refactoring"]
                })))
            ]
            return mock_response
        
        with patch.object(evaluator.openai_client.chat.completions, 'create', side_effect=mock_create):
            # AI should detect this as technically significant despite lack of obvious keywords
            significance_score = await evaluator.evaluate_technical_significance(complex_technical_pr)
        
            # Should be scored as significant (score > 7.0 out of 10)
            assert significance_score.score > 7.0
            assert significance_score.reasoning is not None
            assert "connection pooling" in significance_score.reasoning.lower()
            assert "optimization" in significance_score.reasoning.lower()
            
            # Should identify specific technical merits
            assert significance_score.technical_merits is not None
            assert len(significance_score.technical_merits) >= 2

    async def test_ai_significance_detector_rejects_trivial_changes(self, trivial_pr):
        """FAILING TEST: AI should reject trivial changes that don't warrant content generation"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        from unittest.mock import patch, AsyncMock
        
        evaluator = AIPoweredPREvaluator()
        
        # Mock the OpenAI API response for trivial PR evaluation
        async def mock_create(*args, **kwargs):
            mock_response = AsyncMock()
            mock_response.choices = [
                AsyncMock(message=AsyncMock(content=json.dumps({
                    "score": 2.0,
                    "reasoning": "This is a trivial typo fix with minimal technical significance. No architecture, performance, or business impact considerations.",
                    "technical_merits": []
                })))
            ]
            return mock_response
        
        with patch.object(evaluator.openai_client.chat.completions, 'create', side_effect=mock_create):
            # AI should detect this as not significant
            significance_score = await evaluator.evaluate_technical_significance(trivial_pr)
            
            # Should be scored as not significant (score < 3.0 out of 10)
            assert significance_score.score < 3.0
            assert significance_score.reasoning is not None
            assert "typo" in significance_score.reasoning.lower()
            assert significance_score.technical_merits is None or len(significance_score.technical_merits) == 0

    async def test_ai_business_impact_analyzer_detects_hidden_value(self, business_impact_pr):
        """FAILING TEST: AI should detect business value that keyword matching misses"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        
        evaluator = AIPoweredPREvaluator()
        
        # AI should detect business impact in cache optimization
        business_impact = await evaluator.analyze_business_impact(business_impact_pr)
        
        # Should identify significant business value (score > 6.5 out of 10)
        assert business_impact.score > 6.5
        assert business_impact.reasoning is not None
        
        # Should identify specific business benefits
        expected_benefits = ["performance", "efficiency", "cost", "reliability"]
        reasoning_lower = business_impact.reasoning.lower()
        found_benefits = [benefit for benefit in expected_benefits if benefit in reasoning_lower]
        assert len(found_benefits) >= 2
        
        # Should have quantified impact potential
        assert business_impact.potential_savings is not None
        assert business_impact.roi_category in ["high", "medium", "low"]

    async def test_ai_business_impact_analyzer_identifies_cost_savings(self):
        """FAILING TEST: AI should identify potential cost savings from technical improvements"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        
        evaluator = AIPoweredPREvaluator()
        
        performance_pr = {
            "pull_request": {
                "title": "optimize: reduce API response times",
                "body": "Optimized database queries and added caching layer. Response times improved from 500ms to 100ms average.",
                "labels": [{"name": "performance"}],
                "files": [
                    {"filename": "src/api/optimization.py", "changes": 200}
                ]
            }
        }
        
        business_impact = await evaluator.analyze_business_impact(performance_pr)
        
        # Should identify high business value for performance improvements
        assert business_impact.score > 8.0
        assert business_impact.roi_category == "high"
        
        # Should identify specific cost savings opportunities
        assert "cost" in business_impact.reasoning.lower() or "savings" in business_impact.reasoning.lower()
        
        # Should quantify impact
        assert business_impact.potential_savings is not None
        assert "$" in business_impact.potential_savings or "%" in business_impact.potential_savings

    async def test_ai_professional_positioning_scorer_for_mlops_roles(self):
        """FAILING TEST: AI should score how well PR positions candidate for AI/MLOps roles"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        
        evaluator = AIPoweredPREvaluator()
        
        mlops_pr = {
            "pull_request": {
                "title": "implement: model versioning with MLflow registry",
                "body": "Added MLflow model registry integration with automated versioning, staging, and production deployment workflows. Includes A/B testing framework for model comparison.",
                "labels": [{"name": "mlops"}, {"name": "feature"}],
                "files": [
                    {"filename": "src/mlops/registry.py", "changes": 300},
                    {"filename": "src/mlops/ab_testing.py", "changes": 150}
                ]
            }
        }
        
        positioning_score = await evaluator.score_professional_positioning(
            mlops_pr, 
            target_role="MLOps Engineer",
            target_location="Remote US"
        )
        
        # Should score highly for MLOps positioning (score > 8.5 out of 10)
        assert positioning_score.score > 8.5
        assert positioning_score.role_alignment == "high"
        
        # Should identify relevant skills
        expected_skills = ["mlflow", "model versioning", "a/b testing", "deployment", "automation"]
        skills_found = [skill for skill in expected_skills if skill in positioning_score.relevant_skills]
        assert len(skills_found) >= 3
        
        # Should provide career positioning advice
        assert positioning_score.positioning_advice is not None
        assert len(positioning_score.positioning_advice) > 100

    async def test_ai_professional_positioning_scorer_rejects_irrelevant_work(self):
        """FAILING TEST: AI should score low for work that doesn't help with target role positioning"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        
        evaluator = AIPoweredPREvaluator()
        
        frontend_pr = {
            "pull_request": {
                "title": "update: button colors and spacing",
                "body": "Updated button colors to match brand guidelines and improved spacing for better UX.",
                "labels": [{"name": "ui"}, {"name": "design"}],
                "files": [
                    {"filename": "src/components/Button.css", "changes": 20}
                ]
            }
        }
        
        positioning_score = await evaluator.score_professional_positioning(
            frontend_pr,
            target_role="MLOps Engineer", 
            target_location="Remote US"
        )
        
        # Should score low for MLOps positioning (score < 3.0 out of 10)
        assert positioning_score.score < 3.0
        assert positioning_score.role_alignment == "low"
        
        # Should have minimal relevant skills
        assert len(positioning_score.relevant_skills) <= 1
        
        # Should suggest focusing on more relevant work
        assert "focus" in positioning_score.positioning_advice.lower() or "consider" in positioning_score.positioning_advice.lower()

    async def test_ai_content_potential_predictor_identifies_viral_elements(self):
        """FAILING TEST: AI should predict content potential based on engagement and conversion factors"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        
        evaluator = AIPoweredPREvaluator()
        
        viral_potential_pr = {
            "pull_request": {
                "title": "built: real-time AI fraud detection system",
                "body": "Built real-time fraud detection using transformer models. Reduced false positives by 85% and blocked $2M in fraudulent transactions. System processes 100k transactions/second with sub-50ms latency.",
                "labels": [{"name": "ai"}, {"name": "security"}],
                "files": [
                    {"filename": "src/fraud/detector.py", "changes": 500},
                    {"filename": "src/fraud/transformers.py", "changes": 300}
                ]
            }
        }
        
        content_potential = await evaluator.predict_content_potential(viral_potential_pr)
        
        # Should predict high content potential (score > 8.0 out of 10)
        assert content_potential.engagement_score > 8.0
        assert content_potential.conversion_score > 7.5
        
        # Should identify viral elements
        viral_elements = content_potential.viral_elements
        expected_elements = ["impressive_metrics", "business_impact", "technical_achievement", "problem_solving"]
        found_elements = [elem for elem in expected_elements if elem in viral_elements]
        assert len(found_elements) >= 3
        
        # Should predict audience appeal
        assert content_potential.target_audience is not None
        assert "engineers" in content_potential.target_audience.lower() or "developers" in content_potential.target_audience.lower()

    async def test_ai_content_potential_predictor_rejects_low_engagement_content(self):
        """FAILING TEST: AI should predict low content potential for boring technical work"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        
        evaluator = AIPoweredPREvaluator()
        
        boring_pr = {
            "pull_request": {
                "title": "refactor: extract method in utility class",
                "body": "Extracted a method in utility class to improve code organization. No functional changes.",
                "labels": [{"name": "refactor"}],
                "files": [
                    {"filename": "src/utils/helper.py", "changes": 15}
                ]
            }
        }
        
        content_potential = await evaluator.predict_content_potential(boring_pr)
        
        # Should predict low content potential (scores < 4.0 out of 10)
        assert content_potential.engagement_score < 4.0
        assert content_potential.conversion_score < 4.0
        
        # Should have minimal viral elements
        assert len(content_potential.viral_elements) <= 1
        
        # Should suggest content improvements or recommend skipping
        assert content_potential.recommendation in ["skip", "enhance", "combine_with_other_work"]

    async def test_ai_marketing_value_calculator_combines_all_scores(self):
        """FAILING TEST: AI should calculate overall marketing value combining all evaluation factors"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        
        evaluator = AIPoweredPREvaluator()
        
        high_value_pr = {
            "pull_request": {
                "title": "implement: distributed ML training with 90% cost reduction",
                "body": "Implemented distributed ML training pipeline using Ray. Reduced training costs by 90% while improving speed by 5x. Saved company $500k annually in compute costs.",
                "labels": [{"name": "mlops"}, {"name": "cost-optimization"}],
                "files": [
                    {"filename": "src/ml/distributed_training.py", "changes": 800},
                    {"filename": "src/ml/cost_optimizer.py", "changes": 200}
                ]
            }
        }
        
        marketing_value = await evaluator.calculate_marketing_value(
            high_value_pr,
            target_role="MLOps Engineer",
            target_location="Remote US"
        )
        
        # Should score very highly overall (score > 9.0 out of 10)
        assert marketing_value.overall_score > 9.0
        
        # Should have detailed breakdown
        assert marketing_value.technical_significance_score > 8.0
        assert marketing_value.business_impact_score > 9.0
        assert marketing_value.professional_positioning_score > 8.5
        assert marketing_value.content_potential_score > 8.0
        
        # Should provide actionable marketing strategy
        assert marketing_value.marketing_strategy is not None
        assert len(marketing_value.marketing_strategy) > 200
        
        # Should identify target platforms
        assert len(marketing_value.recommended_platforms) >= 3
        assert "linkedin" in marketing_value.recommended_platforms

    async def test_ai_evaluation_caching_avoids_duplicate_api_calls(self):
        """FAILING TEST: AI evaluator should cache results to avoid repeated API calls for same PRs"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIPoweredPREvaluator
        )
        from unittest.mock import patch, AsyncMock
        
        evaluator = AIPoweredPREvaluator()
        
        pr_data = {
            "pull_request": {
                "id": 12345,
                "title": "feat: add caching layer",
                "body": "Added Redis caching layer for improved performance",
                "labels": [{"name": "performance"}],
                "files": [{"filename": "src/cache.py", "changes": 100}]
            }
        }
        
        # Mock OpenAI API calls
        with patch.object(evaluator.openai_client.chat.completions, 'create') as mock_openai:
            mock_response = AsyncMock()
            mock_response.choices = [
                AsyncMock(message=AsyncMock(content='{"score": 7.5, "reasoning": "Good caching implementation", "technical_merits": ["caching"]}'))
            ]
            mock_openai.return_value = mock_response
            
            # First evaluation should call OpenAI
            result1 = await evaluator.evaluate_technical_significance(pr_data)
            assert mock_openai.call_count == 1
            
            # Second evaluation of same PR should use cache
            result2 = await evaluator.evaluate_technical_significance(pr_data)
            assert mock_openai.call_count == 1  # Should not increase
            
            # Results should be identical
            assert result1.score == result2.score
            assert result1.reasoning == result2.reasoning

    async def test_ai_powered_should_generate_content_replaces_keyword_matching(self, complex_technical_pr, trivial_pr):
        """FAILING TEST: should_generate_content() method should use AI evaluation instead of keyword matching"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AutoContentPipeline
        )
        
        pipeline = AutoContentPipeline()
        
        # Enable AI-powered evaluation
        pipeline.enable_ai_evaluation = True
        
        # Complex technical PR should be approved by AI (even without obvious keywords)
        should_generate_complex = await pipeline.should_generate_content_ai_powered(complex_technical_pr)
        assert should_generate_complex is True
        
        # Trivial PR should be rejected by AI
        should_generate_trivial = await pipeline.should_generate_content_ai_powered(trivial_pr)
        assert should_generate_trivial is False
        
        # Test backward compatibility - old method should still work
        old_result_complex = pipeline.should_generate_content(complex_technical_pr)
        old_result_trivial = pipeline.should_generate_content(trivial_pr)
        
        # AI should be more intelligent than keyword matching
        # Complex technical work might be missed by keywords but caught by AI
        assert should_generate_complex == True  # AI catches it
        # For trivial work, both should agree
        assert should_generate_trivial == old_result_trivial


class TestAIHiringManagerContentOptimization:
    """Test AI Hiring Manager Content Optimization Engine - designed to maximize job opportunity conversion rates"""

    @pytest.fixture
    def ai_hiring_manager_optimizer(self):
        """Mock AI Hiring Manager Content Optimizer"""
        with patch(
            "services.achievement_collector.services.auto_content_pipeline.AIHiringManagerContentOptimizer"
        ) as mock:
            optimizer = AsyncMock()
            mock.return_value = optimizer
            yield optimizer

    @pytest.fixture
    def sample_achievement_data(self):
        """Sample achievement data for testing optimization"""
        return {
            "title": "MLflow Model Registry with SLO-based Rollback",
            "description": "Implemented automated model rollback system using MLflow registry with SLO monitoring",
            "business_value": "$120k annual savings, 99.5% uptime, 60% reduction in manual interventions",
            "technical_details": {
                "technology": "MLflow, Kubernetes, Prometheus", 
                "implementation": "SLO-gated deployment pipeline",
                "impact": "Production-ready MLOps platform"
            },
            "category": "mlops",
            "impact_score": 95
        }

    async def test_hiring_manager_persona_analysis_returns_persona_insights(self, sample_achievement_data):
        """FAILING TEST: AI should analyze content through hiring manager personas (Anthropic, Notion, Stripe, etc.)"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIHiringManagerContentOptimizer
        )
        
        optimizer = AIHiringManagerContentOptimizer()
        
        # Should analyze content through multiple hiring manager personas
        persona_analysis = await optimizer.analyze_hiring_manager_personas(
            achievement_data=sample_achievement_data,
            target_companies=["Anthropic", "Notion", "Stripe", "OpenAI", "Scale AI"]
        )
        
        # Should return persona-specific insights
        assert "anthropic" in persona_analysis
        assert "notion" in persona_analysis  
        assert "stripe" in persona_analysis
        
        # Each persona should have specific insights
        anthropic_persona = persona_analysis["anthropic"]
        assert anthropic_persona.appeal_score >= 0.0 and anthropic_persona.appeal_score <= 10.0
        assert anthropic_persona.key_interests is not None
        assert len(anthropic_persona.optimization_suggestions) > 0
        
        # Should identify company-specific interests
        assert "ai safety" in str(anthropic_persona.key_interests).lower() or "responsible ai" in str(anthropic_persona.key_interests).lower()

    async def test_ai_hiring_keyword_optimization_for_job_search_seo(self, sample_achievement_data):
        """FAILING TEST: AI should optimize content with keywords that AI/MLOps hiring managers search for"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIHiringManagerContentOptimizer
        )
        
        optimizer = AIHiringManagerContentOptimizer()
        
        # Should optimize content for AI/MLOps job search SEO
        keyword_optimization = await optimizer.optimize_job_search_keywords(
            achievement_data=sample_achievement_data,
            target_roles=["MLOps Engineer", "AI Platform Engineer", "ML Infrastructure Engineer"]
        )
        
        # Should return optimized content with SEO keywords
        assert keyword_optimization.optimized_content is not None
        assert len(keyword_optimization.optimized_content) > len(sample_achievement_data.get("description", ""))
        
        # Should include high-value AI/MLOps keywords
        high_value_keywords = [
            "MLOps", "MLflow", "model registry", "SLO", "Kubernetes", 
            "ML infrastructure", "model deployment", "monitoring",
            "production ML", "scalable AI", "ML platform"
        ]
        
        content_lower = keyword_optimization.optimized_content.lower()
        found_keywords = [keyword for keyword in high_value_keywords if keyword.lower() in content_lower]
        assert len(found_keywords) >= 6  # Should include majority of relevant keywords
        
        # Should provide keyword density analysis
        assert keyword_optimization.keyword_analysis is not None
        assert keyword_optimization.seo_score >= 0.0 and keyword_optimization.seo_score <= 100.0

    async def test_hiring_manager_content_hooks_optimization(self, sample_achievement_data):
        """FAILING TEST: AI should generate content hooks that specifically resonate with technical hiring managers"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIHiringManagerContentOptimizer
        )
        
        optimizer = AIHiringManagerContentOptimizer()
        
        # Should generate hiring-manager-optimized hooks
        hook_optimization = await optimizer.optimize_hiring_manager_hooks(
            achievement_data=sample_achievement_data,
            target_audience="AI/MLOps hiring managers"
        )
        
        # Should return multiple hook variations
        assert len(hook_optimization.optimized_hooks) >= 3
        
        # Each hook should be optimized for hiring managers
        for hook in hook_optimization.optimized_hooks:
            assert len(hook.content) > 20  # Substantive hooks
            assert hook.hiring_manager_appeal_score >= 7.0  # High appeal
            
            # Should include authority-building elements
            authority_indicators = [
                "years", "experience", "production", "scale", "led", "built", 
                "delivered", "impact", "results", "proven", "expertise"
            ]
            hook_lower = hook.content.lower()
            found_authority = [indicator for indicator in authority_indicators if indicator in hook_lower]
            assert len(found_authority) >= 2  # Should have multiple authority signals
        
        # Should provide hook performance predictions
        assert hook_optimization.performance_prediction is not None
        assert hook_optimization.target_audience_fit >= 8.0

    async def test_company_specific_content_targeting(self, sample_achievement_data):
        """FAILING TEST: AI should create company-specific content variants (Anthropic, Notion, Stripe, etc.)"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIHiringManagerContentOptimizer
        )
        
        optimizer = AIHiringManagerContentOptimizer()
        
        # Should generate company-specific content variants
        company_targeting = await optimizer.generate_company_specific_variants(
            achievement_data=sample_achievement_data,
            target_companies=["Anthropic", "Notion", "Stripe", "OpenAI"]
        )
        
        # Should have variant for each company
        assert len(company_targeting.company_variants) == 4
        assert "anthropic" in company_targeting.company_variants
        assert "notion" in company_targeting.company_variants
        assert "stripe" in company_targeting.company_variants
        assert "openai" in company_targeting.company_variants
        
        # Each variant should be tailored to company values
        anthropic_variant = company_targeting.company_variants["anthropic"]
        assert "responsible" in anthropic_variant.content.lower() or "safety" in anthropic_variant.content.lower()
        assert anthropic_variant.company_alignment_score >= 8.0
        
        notion_variant = company_targeting.company_variants["notion"]
        assert "productivity" in notion_variant.content.lower() or "collaboration" in notion_variant.content.lower()
        
        stripe_variant = company_targeting.company_variants["stripe"]
        assert "scale" in stripe_variant.content.lower() or "reliability" in stripe_variant.content.lower()
        
        # Should provide targeting effectiveness metrics
        assert company_targeting.overall_targeting_score >= 8.0

    async def test_professional_authority_building_optimization(self, sample_achievement_data):
        """FAILING TEST: AI should optimize content to build professional authority that impresses hiring managers"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIHiringManagerContentOptimizer
        )
        
        optimizer = AIHiringManagerContentOptimizer()
        
        # Should optimize for authority building
        authority_optimization = await optimizer.optimize_professional_authority(
            achievement_data=sample_achievement_data,
            authority_focus="technical_leadership"
        )
        
        # Should enhance content with authority signals
        assert authority_optimization.authority_enhanced_content is not None
        
        # Should include specific authority elements
        authority_elements = [
            "leadership", "mentored", "architected", "designed", "led", "delivered",
            "scaled", "optimized", "reduced costs", "improved performance",
            "production experience", "enterprise", "mission-critical"
        ]
        
        content_lower = authority_optimization.authority_enhanced_content.lower()
        found_elements = [element for element in authority_elements if element in content_lower]
        assert len(found_elements) >= 4  # Should have multiple authority signals
        
        # Should quantify authority metrics
        assert authority_optimization.authority_score >= 8.5  # High authority score
        assert authority_optimization.credibility_indicators is not None
        assert len(authority_optimization.credibility_indicators) >= 3
        
        # Should include specific achievements that impress hiring managers
        impressive_achievements = ["$120k", "99.5%", "60%", "production", "scale"]
        found_achievements = [achievement for achievement in impressive_achievements if achievement in authority_optimization.authority_enhanced_content]
        assert len(found_achievements) >= 3

    async def test_hiring_manager_specific_cta_optimization(self, sample_achievement_data):
        """FAILING TEST: AI should optimize CTAs specifically for converting hiring managers into job opportunities"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIHiringManagerContentOptimizer
        )
        
        optimizer = AIHiringManagerContentOptimizer()
        
        # Should optimize CTAs for hiring manager conversion
        cta_optimization = await optimizer.optimize_hiring_manager_ctas(
            achievement_data=sample_achievement_data,
            target_roles=["MLOps Engineer", "AI Platform Engineer"],
            target_companies=["Anthropic", "Notion", "Stripe"]
        )
        
        # Should return multiple CTA variants
        assert len(cta_optimization.optimized_ctas) >= 3
        
        # Each CTA should be conversion-optimized
        for cta in cta_optimization.optimized_ctas:
            assert cta.conversion_score >= 8.0  # High conversion potential
            assert cta.hiring_manager_appeal >= 7.5  # Appeals to hiring managers
            
            # Should include strong conversion elements
            conversion_elements = [
                "let's discuss", "similar challenges", "open to opportunities",
                "delivering similar impact", "schedule a call", "portfolio",
                "proven results", "available for", "interested in"
            ]
            
            cta_lower = cta.content.lower()
            found_elements = [element for element in conversion_elements if element in cta_lower]
            assert len(found_elements) >= 2  # Should have conversion language
        
        # Should include professional portfolio links with UTM tracking
        best_cta = max(cta_optimization.optimized_ctas, key=lambda x: x.conversion_score)
        assert "serbyn.pro" in best_cta.content
        assert "utm_" in best_cta.content or "tracking" in str(vars(best_cta))  # UTM tracking

    async def test_integrated_hiring_manager_content_pipeline(self, sample_achievement_data):
        """FAILING TEST: AI should integrate all optimization components into a complete hiring-manager-optimized content piece"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AIHiringManagerContentOptimizer
        )
        
        optimizer = AIHiringManagerContentOptimizer()
        
        # Should generate fully optimized content for hiring managers
        complete_optimization = await optimizer.generate_complete_hiring_manager_optimized_content(
            achievement_data=sample_achievement_data,
            target_companies=["Anthropic", "Notion", "Stripe"],
            target_roles=["MLOps Engineer", "AI Platform Engineer"],
            platforms=["linkedin", "devto"]
        )
        
        # Should return comprehensive optimization result
        assert complete_optimization.optimized_content is not None
        assert len(complete_optimization.optimized_content) > 500  # Substantial content
        
        # Should have high conversion scores across all metrics
        assert complete_optimization.overall_conversion_score >= 95.0  # Very high conversion
        assert complete_optimization.hiring_manager_appeal_score >= 90.0
        assert complete_optimization.authority_score >= 85.0
        assert complete_optimization.seo_score >= 80.0
        
        # Should include all optimization components
        content_lower = complete_optimization.optimized_content.lower()
        
        # Keywords optimization
        mlops_keywords = ["mlops", "mlflow", "kubernetes", "monitoring", "slo"]
        found_keywords = [kw for kw in mlops_keywords if kw in content_lower]
        assert len(found_keywords) >= 3
        
        # Authority building
        authority_signals = ["production", "scale", "led", "delivered", "impact"]
        found_authority = [signal for signal in authority_signals if signal in content_lower]
        assert len(found_authority) >= 3
        
        # Business impact quantification
        business_metrics = ["$120k", "99.5%", "60%"]
        found_metrics = [metric for metric in business_metrics if metric in complete_optimization.optimized_content]
        assert len(found_metrics) >= 2
        
        # Professional CTA
        assert "serbyn.pro" in complete_optimization.optimized_content
        assert "utm_" in str(vars(complete_optimization)) or "tracking" in str(vars(complete_optimization))
        
        # Should provide detailed analytics
        assert complete_optimization.optimization_breakdown is not None
        assert len(complete_optimization.optimization_breakdown) >= 5

    async def test_ai_hiring_manager_optimizer_integration_with_existing_pipeline(self):
        """FAILING TEST: AI Hiring Manager Optimizer should integrate seamlessly with existing AutoContentPipeline"""
        
        from services.achievement_collector.services.auto_content_pipeline import (
            AutoContentPipeline,
            ContentGenerationRequest
        )
        
        pipeline = AutoContentPipeline()
        
        # Should have new hiring manager optimization parameter
        enhanced_request = ContentGenerationRequest(
            achievement_id=123,
            include_serbyn_pro_cta=True,
            include_hiring_cta=True,
            target_platforms=["linkedin", "devto"],
            target_role="MLOps Engineer",
            location_preference="Remote US",
            enable_hiring_manager_optimization=True,  # NEW PARAMETER
            target_companies=["Anthropic", "Notion", "Stripe"],  # NEW PARAMETER
            hiring_manager_focus="technical_leadership"  # NEW PARAMETER
        )
        
        achievement_data = {
            "title": "MLflow Model Registry with Automated Rollback",
            "description": "Built production MLOps system with automated model rollback",
            "business_value": "$120k annual savings, 99.5% uptime",
            "category": "mlops",
            "impact_score": 95
        }
        
        # Should use hiring manager optimization when enabled
        result = await pipeline.generate_content_with_cta(achievement_data, enhanced_request)
        
        # Should have significantly higher conversion score due to hiring manager optimization
        assert result.conversion_score >= 95.0  # Much higher than basic optimization
        
        # Content should include hiring manager optimization elements
        content_lower = result.content.lower()
        
        # Should have company-specific targeting
        company_indicators = ["anthropic", "notion", "stripe", "responsible", "productivity", "scale"]
        found_companies = [indicator for indicator in company_indicators if indicator in content_lower]
        assert len(found_companies) >= 1  # Should target at least one company
        
        # Should have enhanced authority building
        authority_enhancements = [
            "production mlops", "technical leadership", "enterprise scale",
            "delivered impact", "proven results", "led implementation"
        ]
        found_authority = [enhancement for enhancement in authority_enhancements if enhancement in content_lower]
        assert len(found_authority) >= 2
        
        # Should maintain backward compatibility
        basic_request = ContentGenerationRequest(
            achievement_id=124,
            enable_hiring_manager_optimization=False
        )
        
        basic_result = await pipeline.generate_content_with_cta(achievement_data, basic_request)
        assert basic_result.conversion_score < result.conversion_score  # Hiring manager optimization should be better