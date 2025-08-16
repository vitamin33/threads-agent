"""
Tests for Content Performance Optimization System

This module tests the content performance optimization system that creates
a feedback loop to continuously improve content quality and conversion rates.

Following TDD principles - writing failing tests first, then implementing
the minimal code to make them pass.
"""

import pytest
from datetime import datetime, timedelta

# Import will fail initially - this is expected in TDD
from content_performance_optimization import (
    ContentPerformanceAnalyzer,
    PlatformOptimizer,
    EngagementPatternDetector,
    ConversionOptimizer,
    PredictiveContentScorer,
    AutomatedStrategyAdjuster,
)


class TestContentPerformanceAnalyzer:
    """Test the content performance analyzer component"""

    @pytest.fixture
    def analyzer(self):
        """Create a content performance analyzer instance"""
        return ContentPerformanceAnalyzer()

    @pytest.fixture
    def sample_content_data(self):
        """Sample content performance data for testing"""
        return [
            {
                "content_id": "post_001",
                "content_type": "linkedin_post",
                "topic": "mlops_cost_optimization",
                "format": "case_study",
                "platform": "linkedin",
                "published_at": datetime.utcnow() - timedelta(days=7),
                "engagement_metrics": {
                    "views": 1500,
                    "likes": 120,
                    "comments": 25,
                    "shares": 15,
                    "engagement_rate": 0.08,
                },
                "conversion_metrics": {
                    "profile_visits": 85,
                    "portfolio_clicks": 32,
                    "contact_inquiries": 5,
                    "job_opportunities": 2,
                },
                "business_metrics": {
                    "revenue_attributed": 150000,  # Job offer amount
                    "cost_per_lead": 50,
                    "roi_percentage": 200,
                },
            },
            {
                "content_id": "post_002",
                "content_type": "twitter_thread",
                "topic": "ai_infrastructure",
                "format": "technical_breakdown",
                "platform": "twitter",
                "published_at": datetime.utcnow() - timedelta(days=5),
                "engagement_metrics": {
                    "views": 850,
                    "likes": 45,
                    "comments": 8,
                    "shares": 12,
                    "engagement_rate": 0.053,
                },
                "conversion_metrics": {
                    "profile_visits": 25,
                    "portfolio_clicks": 8,
                    "contact_inquiries": 1,
                    "job_opportunities": 0,
                },
                "business_metrics": {
                    "revenue_attributed": 0,
                    "cost_per_lead": 75,
                    "roi_percentage": -15,
                },
            },
            {
                "content_id": "post_003",
                "content_type": "devto_article",
                "topic": "mlops_cost_optimization",
                "format": "tutorial",
                "platform": "devto",
                "published_at": datetime.utcnow() - timedelta(days=3),
                "engagement_metrics": {
                    "views": 2200,
                    "likes": 180,
                    "comments": 45,
                    "shares": 25,
                    "engagement_rate": 0.114,
                },
                "conversion_metrics": {
                    "profile_visits": 120,
                    "portfolio_clicks": 65,
                    "contact_inquiries": 8,
                    "job_opportunities": 3,
                },
                "business_metrics": {
                    "revenue_attributed": 225000,
                    "cost_per_lead": 35,
                    "roi_percentage": 320,
                },
            },
        ]

    def test_analyze_content_type_performance_returns_ranking_by_conversion(
        self, analyzer, sample_content_data
    ):
        """Test that analyzer ranks content types by conversion performance"""

        # This test will fail initially - that's expected in TDD
        result = analyzer.analyze_content_type_performance(sample_content_data)

        # Should return ranking of content types by conversion effectiveness
        assert "content_type_rankings" in result
        assert (
            len(result["content_type_rankings"]) == 3
        )  # linkedin_post, twitter_thread, devto_article

        # devto_article should rank highest due to best conversion metrics
        top_performing = result["content_type_rankings"][0]
        assert top_performing["content_type"] == "devto_article"
        assert top_performing["conversion_score"] > 8.0  # High score
        assert top_performing["avg_job_opportunities"] == 3.0
        assert top_performing["avg_revenue_attributed"] == 225000

    def test_analyze_topic_performance_identifies_best_performing_topics(
        self, analyzer, sample_content_data
    ):
        """Test that analyzer identifies which topics drive most conversions"""

        result = analyzer.analyze_topic_performance(sample_content_data)

        # Should identify mlops_cost_optimization as top topic
        assert "topic_rankings" in result
        assert (
            len(result["topic_rankings"]) == 2
        )  # mlops_cost_optimization, ai_infrastructure

        top_topic = result["topic_rankings"][0]
        assert top_topic["topic"] == "mlops_cost_optimization"
        assert (
            top_topic["total_job_opportunities"] == 5
        )  # 2 + 3 from linkedin and devto posts
        assert top_topic["avg_conversion_rate"] > 0.05
        assert top_topic["total_revenue_attributed"] == 375000  # 150k + 225k

    def test_analyze_format_performance_ranks_formats_by_effectiveness(
        self, analyzer, sample_content_data
    ):
        """Test that analyzer ranks content formats by engagement and conversion"""

        result = analyzer.analyze_format_performance(sample_content_data)

        assert "format_rankings" in result
        assert (
            len(result["format_rankings"]) == 3
        )  # case_study, technical_breakdown, tutorial

        # Tutorial should rank highest
        top_format = result["format_rankings"][0]
        assert top_format["format"] == "tutorial"
        assert top_format["avg_engagement_rate"] > 0.1
        assert top_format["conversion_effectiveness"] > 8.0

    def test_analyze_platform_performance_compares_platform_effectiveness(
        self, analyzer, sample_content_data
    ):
        """Test that analyzer compares performance across platforms"""

        result = analyzer.analyze_platform_performance(sample_content_data)

        assert "platform_rankings" in result
        assert len(result["platform_rankings"]) == 3  # linkedin, twitter, devto

        # DevTo should rank highest for conversion
        top_platform = result["platform_rankings"][0]
        assert top_platform["platform"] == "devto"
        assert top_platform["conversion_metrics"]["job_opportunities"] == 3
        assert top_platform["roi_score"] > 8.0

    def test_generate_performance_insights_provides_actionable_recommendations(
        self, analyzer, sample_content_data
    ):
        """Test that analyzer generates actionable insights for content strategy"""

        result = analyzer.generate_performance_insights(sample_content_data)

        # Should provide clear recommendations
        assert "insights" in result
        assert "recommendations" in result
        assert "optimization_opportunities" in result

        insights = result["insights"]
        assert "best_performing_combination" in insights
        assert (
            insights["best_performing_combination"]["content_type"] == "devto_article"
        )
        assert (
            insights["best_performing_combination"]["topic"]
            == "mlops_cost_optimization"
        )
        assert insights["best_performing_combination"]["format"] == "tutorial"

        # Should have specific recommendations
        recommendations = result["recommendations"]
        assert len(recommendations) >= 3
        assert any("focus on devto" in rec.lower() for rec in recommendations)
        assert any("mlops_cost_optimization" in rec.lower() for rec in recommendations)

    def test_calculate_content_performance_score_weights_conversion_heavily(
        self, analyzer, sample_content_data
    ):
        """Test that performance score calculation weights business metrics appropriately"""

        content_item = sample_content_data[2]  # DevTo article with best performance
        score = analyzer.calculate_content_performance_score(content_item)

        # Should return high score for content with good conversion metrics
        assert score > 8.5  # High performance score
        assert isinstance(score, float)
        assert 0 <= score <= 10

    def test_identify_underperforming_content_flags_low_conversion_content(
        self, analyzer, sample_content_data
    ):
        """Test that analyzer identifies content that needs improvement"""

        result = analyzer.identify_underperforming_content(sample_content_data)

        assert "underperforming_content" in result
        assert len(result["underperforming_content"]) >= 1

        # Twitter thread should be flagged as underperforming
        underperforming = result["underperforming_content"][0]
        assert underperforming["content_id"] == "post_002"
        assert underperforming["performance_issues"] is not None
        assert underperforming["improvement_suggestions"] is not None


class TestPlatformOptimizer:
    """Test the platform-specific optimization engine"""

    @pytest.fixture
    def optimizer(self):
        """Create a platform optimizer instance"""
        return PlatformOptimizer()

    def test_optimize_content_strategy_for_platform_adjusts_based_on_performance(
        self, optimizer
    ):
        """Test that optimizer adjusts content strategy per platform based on performance data"""

        platform_performance = {
            "linkedin": {
                "best_content_types": ["case_study", "achievement_showcase"],
                "best_topics": ["mlops_cost_optimization", "ai_leadership"],
                "optimal_posting_times": ["09:00", "17:00"],
                "engagement_patterns": {
                    "peak_engagement_hours": [9, 17],
                    "best_content_length": "medium",  # 150-300 words
                    "most_engaging_formats": ["numbered_lists", "case_studies"],
                },
                "conversion_insights": {
                    "best_cta_types": ["portfolio_link", "contact_direct"],
                    "optimal_hook_styles": ["authority_building", "problem_solving"],
                },
            }
        }

        result = optimizer.optimize_content_strategy_for_platform(
            "linkedin", platform_performance["linkedin"]
        )

        # Should return optimized strategy
        assert "optimized_strategy" in result
        strategy = result["optimized_strategy"]

        assert strategy["recommended_content_types"] == [
            "case_study",
            "achievement_showcase",
        ]
        assert strategy["recommended_topics"] == [
            "mlops_cost_optimization",
            "ai_leadership",
        ]
        assert strategy["optimal_posting_schedule"] == ["09:00", "17:00"]
        assert strategy["content_optimization"] is not None

    def test_adjust_posting_schedule_optimizes_timing_based_on_engagement(
        self, optimizer
    ):
        """Test that optimizer adjusts posting schedule based on engagement patterns"""

        engagement_data = {
            "hourly_engagement": {
                "09:00": 0.08,
                "12:00": 0.05,
                "17:00": 0.12,
                "20:00": 0.07,
            },
            "daily_engagement": {
                "monday": 0.09,
                "tuesday": 0.11,
                "wednesday": 0.10,
                "thursday": 0.08,
                "friday": 0.06,
            },
        }

        result = optimizer.adjust_posting_schedule("linkedin", engagement_data)

        assert "optimized_schedule" in result
        schedule = result["optimized_schedule"]

        # Should recommend 17:00 as top time (highest engagement)
        assert schedule["primary_posting_time"] == "17:00"
        assert schedule["secondary_posting_time"] == "09:00"
        assert schedule["best_days"] == ["tuesday", "wednesday", "monday"]


class TestEngagementPatternDetector:
    """Test the engagement pattern detection component"""

    @pytest.fixture
    def detector(self):
        """Create an engagement pattern detector instance"""
        return EngagementPatternDetector()

    def test_detect_high_engagement_patterns_identifies_viral_elements(self, detector):
        """Test that detector identifies what content elements drive highest engagement"""

        content_data = [
            {
                "content_id": "post_001",
                "content_elements": {
                    "has_numbers": True,
                    "has_specific_metrics": True,
                    "hook_type": "problem_solving",
                    "includes_code": False,
                    "includes_images": True,
                    "word_count": 250,
                    "cta_type": "portfolio_link",
                },
                "engagement_metrics": {
                    "engagement_rate": 0.12,
                    "share_rate": 0.02,
                    "comment_quality_score": 8.5,
                },
            },
            {
                "content_id": "post_002",
                "content_elements": {
                    "has_numbers": False,
                    "has_specific_metrics": False,
                    "hook_type": "generic",
                    "includes_code": True,
                    "includes_images": False,
                    "word_count": 500,
                    "cta_type": "generic",
                },
                "engagement_metrics": {
                    "engagement_rate": 0.04,
                    "share_rate": 0.005,
                    "comment_quality_score": 5.2,
                },
            },
        ]

        result = detector.detect_high_engagement_patterns(content_data)

        assert "engagement_patterns" in result
        patterns = result["engagement_patterns"]

        # Should identify that numbers and specific metrics drive engagement
        assert any(pattern["element"] == "has_specific_metrics" for pattern in patterns)
        assert any(pattern["element"] == "problem_solving_hook" for pattern in patterns)

        # Should provide engagement correlation scores
        metrics_pattern = next(
            p for p in patterns if p["element"] == "has_specific_metrics"
        )
        assert metrics_pattern["engagement_correlation"] > 0.7


class TestConversionOptimizer:
    """Test the conversion optimization component"""

    @pytest.fixture
    def optimizer(self):
        """Create a conversion optimizer instance"""
        return ConversionOptimizer()

    def test_optimize_for_lead_generation_focuses_on_conversion_elements(
        self, optimizer
    ):
        """Test that optimizer focuses on elements that drive lead generation"""

        conversion_data = {
            "content_performance": [
                {
                    "content_id": "post_001",
                    "conversion_elements": {
                        "cta_type": "portfolio_direct",
                        "authority_signals": ["5+ years", "production scale"],
                        "business_impact_mentioned": True,
                        "specific_results": ["$120k savings", "40% improvement"],
                    },
                    "conversion_metrics": {
                        "portfolio_clicks": 45,
                        "contact_inquiries": 8,
                        "job_opportunities": 3,
                    },
                }
            ]
        }

        result = optimizer.optimize_for_lead_generation(conversion_data)

        assert "conversion_optimization" in result
        optimization = result["conversion_optimization"]

        assert "high_converting_elements" in optimization
        assert "recommended_cta_strategy" in optimization
        assert "authority_building_tactics" in optimization

    def test_optimize_for_job_inquiries_prioritizes_hiring_manager_appeal(
        self, optimizer
    ):
        """Test that optimizer specifically targets hiring manager conversion"""

        job_inquiry_data = {
            "successful_conversions": [
                {
                    "content_elements": {
                        "mentioned_company_challenges": True,
                        "demonstrated_leadership": True,
                        "included_team_impact": True,
                        "used_hiring_manager_keywords": [
                            "MLOps",
                            "scale",
                            "infrastructure",
                        ],
                    },
                    "outcome": {
                        "hiring_manager_engagement": True,
                        "job_inquiry_received": True,
                        "interview_scheduled": True,
                    },
                }
            ]
        }

        result = optimizer.optimize_for_job_inquiries(job_inquiry_data)

        assert "job_inquiry_optimization" in result
        optimization = result["job_inquiry_optimization"]

        assert "hiring_manager_focused_elements" in optimization
        assert "high_value_keywords" in optimization
        assert "leadership_positioning_tactics" in optimization


class TestPredictiveContentScorer:
    """Test the predictive content scoring component"""

    @pytest.fixture
    def scorer(self):
        """Create a predictive content scorer instance"""
        return PredictiveContentScorer()

    def test_predict_content_performance_estimates_engagement_before_publishing(
        self, scorer
    ):
        """Test that scorer predicts content performance before publishing"""

        content_draft = {
            "content_type": "linkedin_post",
            "topic": "mlops_cost_optimization",
            "format": "case_study",
            "content_elements": {
                "has_specific_metrics": True,
                "includes_business_impact": True,
                "word_count": 280,
                "authority_signals": 3,
                "cta_quality": "high",
            },
            "historical_context": {
                "similar_content_avg_performance": 0.08,
                "topic_trend_score": 8.5,
                "author_authority_score": 7.8,
            },
        }

        result = scorer.predict_content_performance(content_draft)

        assert "predicted_performance" in result
        prediction = result["predicted_performance"]

        assert "engagement_score" in prediction
        assert "conversion_score" in prediction
        assert "viral_potential" in prediction
        assert "confidence_interval" in prediction

        # Should predict high performance for optimized content
        assert prediction["engagement_score"] > 7.0
        assert prediction["conversion_score"] > 6.0


class TestAutomatedStrategyAdjuster:
    """Test the automated content strategy adjustment component"""

    @pytest.fixture
    def adjuster(self):
        """Create an automated strategy adjuster instance"""
        return AutomatedStrategyAdjuster()

    def test_auto_update_content_generation_parameters_adjusts_based_on_performance(
        self, adjuster
    ):
        """Test that adjuster automatically updates content generation parameters"""

        performance_analysis = {
            "best_performing_patterns": {
                "content_types": ["devto_article", "linkedin_post"],
                "topics": ["mlops_cost_optimization", "ai_infrastructure"],
                "formats": ["tutorial", "case_study"],
                "optimal_word_counts": {"linkedin": 250, "devto": 1500},
                "high_converting_ctas": ["portfolio_direct", "contact_consultation"],
            },
            "underperforming_patterns": {
                "content_types": ["twitter_thread"],
                "topics": ["general_programming"],
                "formats": ["opinion_piece"],
            },
            "performance_thresholds": {
                "min_engagement_rate": 0.06,
                "min_conversion_rate": 0.03,
                "min_job_inquiries_per_month": 8,
            },
        }

        result = adjuster.auto_update_content_generation_parameters(
            performance_analysis
        )

        assert "updated_parameters" in result
        parameters = result["updated_parameters"]

        assert "content_type_weights" in parameters
        assert "topic_priorities" in parameters
        assert "format_preferences" in parameters
        assert "platform_allocation" in parameters

        # Should increase weight for high-performing content types
        assert parameters["content_type_weights"]["devto_article"] > 0.3
        assert parameters["content_type_weights"]["linkedin_post"] > 0.3

        # Should decrease weight for underperforming content types
        assert parameters["content_type_weights"]["twitter_thread"] < 0.2

    def test_create_feedback_loop_integrates_performance_data_into_content_pipeline(
        self, adjuster
    ):
        """Test that adjuster creates feedback loop from performance to content generation"""

        current_pipeline_config = {
            "content_generation_weights": {
                "mlops": 0.4,
                "ai_infrastructure": 0.3,
                "general_tech": 0.3,
            },
            "platform_distribution": {"linkedin": 0.4, "devto": 0.3, "twitter": 0.3},
            "quality_thresholds": {
                "min_authority_score": 7.0,
                "min_business_impact_score": 6.0,
            },
        }

        performance_feedback = {
            "topic_performance": {
                "mlops": {"conversion_rate": 0.12, "job_inquiries": 15},
                "ai_infrastructure": {"conversion_rate": 0.08, "job_inquiries": 8},
                "general_tech": {"conversion_rate": 0.03, "job_inquiries": 2},
            },
            "platform_performance": {
                "linkedin": {"roi": 250, "job_opportunities": 12},
                "devto": {"roi": 320, "job_opportunities": 18},
                "twitter": {"roi": 45, "job_opportunities": 3},
            },
        }

        result = adjuster.create_feedback_loop(
            current_pipeline_config, performance_feedback
        )

        assert "optimized_pipeline_config" in result
        config = result["optimized_pipeline_config"]

        # Should increase MLOps weight due to high performance
        assert config["content_generation_weights"]["mlops"] > 0.5

        # Should increase DevTo allocation due to best ROI
        assert config["platform_distribution"]["devto"] > 0.4

        # Should decrease Twitter allocation due to poor performance
        assert config["platform_distribution"]["twitter"] < 0.2

        assert "feedback_integration_summary" in result
        assert "optimization_rationale" in result
