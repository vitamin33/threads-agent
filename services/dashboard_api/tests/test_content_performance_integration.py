"""
Integration tests for Content Performance Optimization System

Tests the integration between content performance optimization and existing
systems like revenue attribution dashboard, unified analytics, and auto content pipeline.

Following TDD principles - testing the complete feedback loop.
"""

import pytest
from datetime import datetime, timedelta

# Import existing systems
from ..revenue_attribution_dashboard import RevenueAttributionEngine
from ..unified_analytics import AnalyticsAggregationService, ConversionTracker
from ..ab_testing import ABTestingFramework, TestVariant

# Import our content performance system
from ..content_performance_optimization import (
    ContentPerformanceAnalyzer,
    AutomatedStrategyAdjuster,
)


class TestContentPerformanceIntegration:
    """Test integration between content performance optimization and existing systems"""

    @pytest.fixture
    def revenue_engine(self):
        """Create revenue attribution engine"""
        return RevenueAttributionEngine()

    @pytest.fixture
    def analytics_service(self):
        """Create analytics aggregation service"""
        return AnalyticsAggregationService()

    @pytest.fixture
    def conversion_tracker(self):
        """Create conversion tracker"""
        return ConversionTracker()

    @pytest.fixture
    def ab_testing_framework(self):
        """Create A/B testing framework"""
        return ABTestingFramework()

    @pytest.fixture
    def performance_analyzer(self):
        """Create content performance analyzer"""
        return ContentPerformanceAnalyzer()

    @pytest.fixture
    def strategy_adjuster(self):
        """Create automated strategy adjuster"""
        return AutomatedStrategyAdjuster()

    def test_revenue_attribution_integration_feeds_performance_analysis(
        self, revenue_engine, performance_analyzer
    ):
        """Test that revenue attribution data feeds into performance analysis"""

        # Set up revenue attribution tracking for content
        content_creation_result = revenue_engine.track_content_creation(
            {
                "content_id": "content_001",
                "platform": "linkedin",
                "content_type": "case_study",
                "topic": "mlops_cost_optimization",
                "creation_cost_hours": 2,
                "hourly_rate": 75,
                "utm_campaign": "performance_test",
            }
        )

        assert content_creation_result["success"] is True

        # Track traffic and conversions
        revenue_engine.track_content_traffic(
            {
                "visitor_id": "visitor_001",
                "source_content_id": "content_001",
                "utm_source": "linkedin",
                "utm_campaign": "performance_test",
            }
        )

        revenue_engine.track_lead_qualification(
            {
                "visitor_id": "visitor_001",
                "visitor_type": "hiring_manager",
                "hiring_manager_probability": 0.9,
                "company_name": "AI Corp",
                "is_target_company": True,
            }
        )

        revenue_engine.track_job_offer(
            {
                "visitor_id": "visitor_001",
                "company_name": "AI Corp",
                "position": "MLOps Engineer",
                "initial_offer_amount": 150000,
                "offer_status": "received",
            }
        )

        # Get attribution data and convert to performance analysis format
        attribution_result = revenue_engine.get_complete_attribution_chain(
            "content_001"
        )

        # Convert to content performance data format
        content_performance_data = [
            {
                "content_id": "content_001",
                "content_type": "case_study",
                "topic": "mlops_cost_optimization",
                "format": "case_study",
                "platform": "linkedin",
                "published_at": datetime.utcnow() - timedelta(days=1),
                "engagement_metrics": {
                    "views": attribution_result["total_visitors"]
                    * 10,  # Simulate view multiplier
                    "likes": 45,
                    "comments": 8,
                    "shares": 6,
                    "engagement_rate": 0.087,
                },
                "conversion_metrics": {
                    "profile_visits": attribution_result["total_visitors"],
                    "portfolio_clicks": 25,
                    "contact_inquiries": attribution_result["qualified_leads"],
                    "job_opportunities": attribution_result["job_offers"],
                },
                "business_metrics": {
                    "revenue_attributed": attribution_result["attributed_revenue"],
                    "cost_per_lead": attribution_result["content_creation_cost"]
                    / max(1, attribution_result["qualified_leads"]),
                    "roi_percentage": attribution_result["roi_percentage"],
                },
            }
        ]

        # Analyze performance using the converted data
        performance_result = performance_analyzer.analyze_content_type_performance(
            content_performance_data
        )

        # Verify integration worked
        assert len(performance_result["content_type_rankings"]) == 1
        ranking = performance_result["content_type_rankings"][0]
        assert ranking["content_type"] == "case_study"
        assert ranking["avg_job_opportunities"] == 1.0
        assert ranking["avg_revenue_attributed"] == 150000

    @pytest.mark.asyncio
    async def test_unified_analytics_integration_provides_multi_platform_data(
        self, analytics_service, conversion_tracker, performance_analyzer
    ):
        """Test that unified analytics provides multi-platform data for optimization"""

        # Track conversions across platforms
        linkedin_conversion = await conversion_tracker.track_conversion(
            {
                "source_platform": "linkedin",
                "content_url": "https://linkedin.com/posts/content_001",
                "visitor_id": "visitor_001",
                "timestamp": datetime.utcnow(),
            }
        )

        devto_conversion = await conversion_tracker.track_conversion(
            {
                "source_platform": "devto",
                "content_url": "https://dev.to/posts/content_002",
                "visitor_id": "visitor_002",
                "timestamp": datetime.utcnow(),
            }
        )

        # Track lead conversions
        linkedin_lead = await conversion_tracker.track_lead_conversion(
            {
                "source_conversion_id": linkedin_conversion["conversion_id"],
                "lead_type": "job_inquiry",
                "lead_quality": "high",
                "timestamp": datetime.utcnow(),
            }
        )

        devto_lead = await conversion_tracker.track_lead_conversion(
            {
                "source_conversion_id": devto_conversion["conversion_id"],
                "lead_type": "portfolio_visit",
                "lead_quality": "medium",
                "timestamp": datetime.utcnow(),
            }
        )

        # Get platform metrics
        platform_metrics = await analytics_service.collect_all_platform_metrics()

        # Simulate platform performance data for analysis
        content_performance_data = [
            {
                "content_id": "content_001",
                "content_type": "linkedin_post",
                "topic": "ai_infrastructure",
                "format": "case_study",
                "platform": "linkedin",
                "published_at": datetime.utcnow() - timedelta(days=2),
                "engagement_metrics": {
                    "views": 850,
                    "likes": 67,
                    "comments": 12,
                    "shares": 8,
                    "engagement_rate": 0.095,
                },
                "conversion_metrics": {
                    "profile_visits": 32,
                    "portfolio_clicks": 18,
                    "contact_inquiries": 3,
                    "job_opportunities": 1,
                },
                "business_metrics": {
                    "revenue_attributed": 140000,
                    "cost_per_lead": 50,
                    "roi_percentage": 180,
                },
            },
            {
                "content_id": "content_002",
                "content_type": "devto_article",
                "topic": "ai_infrastructure",
                "format": "tutorial",
                "platform": "devto",
                "published_at": datetime.utcnow() - timedelta(days=1),
                "engagement_metrics": {
                    "views": 1200,
                    "likes": 89,
                    "comments": 23,
                    "shares": 15,
                    "engagement_rate": 0.106,
                },
                "conversion_metrics": {
                    "profile_visits": 48,
                    "portfolio_clicks": 28,
                    "contact_inquiries": 4,
                    "job_opportunities": 2,
                },
                "business_metrics": {
                    "revenue_attributed": 180000,
                    "cost_per_lead": 40,
                    "roi_percentage": 225,
                },
            },
        ]

        # Analyze platform performance
        platform_analysis = performance_analyzer.analyze_platform_performance(
            content_performance_data
        )

        # Verify multi-platform analysis works
        assert len(platform_analysis["platform_rankings"]) == 2

        # DevTo should rank higher due to better metrics
        top_platform = platform_analysis["platform_rankings"][0]
        assert top_platform["platform"] == "devto"
        assert top_platform["conversion_metrics"]["job_opportunities"] == 2

    def test_ab_testing_integration_optimizes_content_variations(
        self, ab_testing_framework, performance_analyzer, strategy_adjuster
    ):
        """Test A/B testing integration for content variation optimization"""

        # Create A/B test for content variations
        variant_a = TestVariant(
            name="hook_authority",
            description="Authority-building hook with credentials",
            changes={"hook_style": "authority", "credentials_mentioned": True},
        )

        variant_b = TestVariant(
            name="hook_problem",
            description="Problem-solving hook with pain points",
            changes={"hook_style": "problem_solving", "pain_points_mentioned": True},
        )

        test_config = {
            "test_name": "content_hook_optimization",
            "traffic_split": 0.5,
            "success_metric": "job_inquiries",
            "minimum_sample_size": 100,
        }

        test_creation = ab_testing_framework.create_ab_test(
            [variant_a, variant_b], test_config
        )
        assert test_creation["success"] is True
        test_id = test_creation["test_id"]

        # Simulate visitors and conversions for both variants
        visitor_assignments = []
        for i in range(120):  # Above minimum sample size
            visitor_id = f"visitor_{i:03d}"
            assignment = ab_testing_framework.assign_visitor_to_group(
                test_id, visitor_id
            )
            visitor_assignments.append(assignment)

        # Simulate conversions - variant A (authority) performs better
        for assignment in visitor_assignments:
            variant = assignment["variant"]
            visitor_id = assignment["visitor_id"]

            # Authority variant converts better
            if (
                variant == "variant_a" and int(visitor_id.split("_")[1]) % 8 == 0
            ):  # 12.5% conversion
                ab_testing_framework.track_conversion(
                    {
                        "test_id": test_id,
                        "visitor_id": visitor_id,
                        "variant": variant,
                        "conversion_type": "job_inquiry",
                        "conversion_value": 1,
                    }
                )
            elif (
                variant == "variant_b" and int(visitor_id.split("_")[1]) % 12 == 0
            ):  # 8.3% conversion
                ab_testing_framework.track_conversion(
                    {
                        "test_id": test_id,
                        "visitor_id": visitor_id,
                        "variant": variant,
                        "conversion_type": "job_inquiry",
                        "conversion_value": 1,
                    }
                )

        # Analyze test results
        test_results = ab_testing_framework.calculate_test_results(test_id)

        # Create performance data based on A/B test results
        variant_a_performance = {
            "content_id": "variant_a_content",
            "content_type": "linkedin_post",
            "topic": "mlops_leadership",
            "format": "authority_showcase",
            "platform": "linkedin",
            "published_at": datetime.utcnow() - timedelta(days=1),
            "engagement_metrics": {
                "views": 800,
                "likes": 72,
                "comments": 15,
                "shares": 9,
                "engagement_rate": 0.12,
            },
            "conversion_metrics": {
                "profile_visits": 45,
                "portfolio_clicks": 28,
                "contact_inquiries": 8,
                "job_opportunities": 3,
            },
            "business_metrics": {
                "revenue_attributed": 180000,
                "cost_per_lead": 35,
                "roi_percentage": 257,
            },
        }

        variant_b_performance = {
            "content_id": "variant_b_content",
            "content_type": "linkedin_post",
            "topic": "mlops_leadership",
            "format": "problem_solving",
            "platform": "linkedin",
            "published_at": datetime.utcnow() - timedelta(days=1),
            "engagement_metrics": {
                "views": 750,
                "likes": 58,
                "comments": 11,
                "shares": 6,
                "engagement_rate": 0.10,
            },
            "conversion_metrics": {
                "profile_visits": 38,
                "portfolio_clicks": 22,
                "contact_inquiries": 5,
                "job_opportunities": 2,
            },
            "business_metrics": {
                "revenue_attributed": 120000,
                "cost_per_lead": 45,
                "roi_percentage": 167,
            },
        }

        # Analyze performance to identify winner
        performance_data = [variant_a_performance, variant_b_performance]
        format_analysis = performance_analyzer.analyze_format_performance(
            performance_data
        )

        # Verify A/B test integration identifies better performing variant
        assert len(format_analysis["format_rankings"]) == 2

        # Authority showcase should rank higher
        top_format = format_analysis["format_rankings"][0]
        assert top_format["format"] == "authority_showcase"
        assert top_format["conversion_effectiveness"] > 8.0

        # Use results to update strategy
        performance_analysis = {
            "best_performing_patterns": {
                "content_types": ["linkedin_post"],
                "topics": ["mlops_leadership"],
                "formats": ["authority_showcase"],  # Winner from A/B test
                "optimal_word_counts": {"linkedin": 280},
                "high_converting_ctas": ["portfolio_direct"],
            },
            "underperforming_patterns": {
                "content_types": [],
                "topics": [],
                "formats": ["problem_solving"],  # Loser from A/B test
            },
            "performance_thresholds": {
                "min_engagement_rate": 0.08,
                "min_conversion_rate": 0.04,
                "min_job_inquiries_per_month": 10,
            },
        }

        strategy_update = strategy_adjuster.auto_update_content_generation_parameters(
            performance_analysis
        )

        # Verify strategy was updated based on A/B test results
        assert "updated_parameters" in strategy_update
        parameters = strategy_update["updated_parameters"]

        # Authority showcase should get higher weight
        assert parameters["format_preferences"]["authority_showcase"] > 0.5
        assert parameters["format_preferences"]["problem_solving"] < 0.3

    def test_complete_feedback_loop_improves_content_strategy(
        self, revenue_engine, performance_analyzer, strategy_adjuster
    ):
        """Test complete feedback loop from content performance to strategy adjustment"""

        # Step 1: Track multiple content pieces with different performance levels
        content_performance_history = []

        # High-performing content (MLOps cost optimization)
        high_perf_content = {
            "content_id": "high_perf_001",
            "content_type": "devto_article",
            "topic": "mlops_cost_optimization",
            "format": "tutorial",
            "platform": "devto",
            "published_at": datetime.utcnow() - timedelta(days=5),
            "engagement_metrics": {
                "views": 2500,
                "likes": 198,
                "comments": 45,
                "shares": 32,
                "engagement_rate": 0.125,
            },
            "conversion_metrics": {
                "profile_visits": 125,
                "portfolio_clicks": 78,
                "contact_inquiries": 12,
                "job_opportunities": 5,
            },
            "business_metrics": {
                "revenue_attributed": 320000,
                "cost_per_lead": 25,
                "roi_percentage": 280,
            },
        }

        # Medium-performing content (AI infrastructure)
        medium_perf_content = {
            "content_id": "medium_perf_001",
            "content_type": "linkedin_post",
            "topic": "ai_infrastructure",
            "format": "case_study",
            "platform": "linkedin",
            "published_at": datetime.utcnow() - timedelta(days=3),
            "engagement_metrics": {
                "views": 1200,
                "likes": 89,
                "comments": 18,
                "shares": 12,
                "engagement_rate": 0.089,
            },
            "conversion_metrics": {
                "profile_visits": 58,
                "portfolio_clicks": 35,
                "contact_inquiries": 6,
                "job_opportunities": 2,
            },
            "business_metrics": {
                "revenue_attributed": 160000,
                "cost_per_lead": 40,
                "roi_percentage": 160,
            },
        }

        # Low-performing content (General programming)
        low_perf_content = {
            "content_id": "low_perf_001",
            "content_type": "twitter_thread",
            "topic": "general_programming",
            "format": "opinion_piece",
            "platform": "twitter",
            "published_at": datetime.utcnow() - timedelta(days=2),
            "engagement_metrics": {
                "views": 580,
                "likes": 32,
                "comments": 4,
                "shares": 2,
                "engagement_rate": 0.042,
            },
            "conversion_metrics": {
                "profile_visits": 18,
                "portfolio_clicks": 8,
                "contact_inquiries": 1,
                "job_opportunities": 0,
            },
            "business_metrics": {
                "revenue_attributed": 0,
                "cost_per_lead": 150,
                "roi_percentage": -25,
            },
        }

        content_performance_history = [
            high_perf_content,
            medium_perf_content,
            low_perf_content,
        ]

        # Step 2: Analyze performance across all dimensions
        content_type_analysis = performance_analyzer.analyze_content_type_performance(
            content_performance_history
        )
        topic_analysis = performance_analyzer.analyze_topic_performance(
            content_performance_history
        )
        format_analysis = performance_analyzer.analyze_format_performance(
            content_performance_history
        )
        platform_analysis = performance_analyzer.analyze_platform_performance(
            content_performance_history
        )
        insights = performance_analyzer.generate_performance_insights(
            content_performance_history
        )

        # Step 3: Create comprehensive performance analysis for strategy adjustment
        performance_analysis = {
            "best_performing_patterns": {
                "content_types": [
                    ranking["content_type"]
                    for ranking in content_type_analysis["content_type_rankings"][:2]
                ],
                "topics": [
                    ranking["topic"] for ranking in topic_analysis["topic_rankings"][:2]
                ],
                "formats": [
                    ranking["format"]
                    for ranking in format_analysis["format_rankings"][:2]
                ],
                "optimal_word_counts": {"devto": 1500, "linkedin": 280},
                "high_converting_ctas": ["portfolio_direct", "contact_consultation"],
            },
            "underperforming_patterns": {
                "content_types": ["twitter_thread"],
                "topics": ["general_programming"],
                "formats": ["opinion_piece"],
            },
            "performance_thresholds": {
                "min_engagement_rate": 0.08,
                "min_conversion_rate": 0.05,
                "min_job_inquiries_per_month": 15,
            },
        }

        # Step 4: Generate automated strategy adjustments
        strategy_update = strategy_adjuster.auto_update_content_generation_parameters(
            performance_analysis
        )

        # Step 5: Verify feedback loop creates actionable strategy improvements
        assert "updated_parameters" in strategy_update
        parameters = strategy_update["updated_parameters"]

        # Verify high-performing patterns get increased allocation
        assert parameters["content_type_weights"]["devto_article"] > 0.3
        assert parameters["topic_priorities"]["mlops_cost_optimization"] > 0.6
        assert parameters["format_preferences"]["tutorial"] > 0.5

        # Verify underperforming patterns get decreased allocation
        assert parameters["content_type_weights"]["twitter_thread"] < 0.2
        assert parameters["topic_priorities"]["general_programming"] < 0.3
        assert parameters["format_preferences"]["opinion_piece"] < 0.2

        # Verify platform allocation adjusts based on ROI
        assert parameters["platform_allocation"]["devto"] > 0.3  # Best performing
        assert parameters["platform_allocation"]["twitter"] < 0.2  # Worst performing

        # Step 6: Test that insights provide actionable recommendations
        assert "recommendations" in insights
        recommendations = insights["recommendations"]

        # Should recommend focusing on best performers
        assert any("devto" in rec.lower() for rec in recommendations)
        assert any("mlops_cost_optimization" in rec.lower() for rec in recommendations)

        # Step 7: Create current pipeline config for feedback loop testing
        current_pipeline_config = {
            "content_generation_weights": {
                "mlops_cost_optimization": 0.3,
                "ai_infrastructure": 0.4,
                "general_programming": 0.3,
            },
            "platform_distribution": {"linkedin": 0.4, "devto": 0.3, "twitter": 0.3},
            "quality_thresholds": {
                "min_authority_score": 7.0,
                "min_business_impact_score": 6.0,
            },
        }

        performance_feedback = {
            "topic_performance": {
                "mlops_cost_optimization": {
                    "conversion_rate": 0.15,
                    "job_inquiries": 20,
                },
                "ai_infrastructure": {"conversion_rate": 0.08, "job_inquiries": 8},
                "general_programming": {"conversion_rate": 0.02, "job_inquiries": 1},
            },
            "platform_performance": {
                "linkedin": {"roi": 160, "job_opportunities": 8},
                "devto": {"roi": 280, "job_opportunities": 15},
                "twitter": {"roi": 25, "job_opportunities": 2},
            },
        }

        # Step 8: Test complete feedback loop integration
        feedback_loop_result = strategy_adjuster.create_feedback_loop(
            current_pipeline_config, performance_feedback
        )

        # Verify feedback loop produces optimized configuration
        assert "optimized_pipeline_config" in feedback_loop_result
        optimized_config = feedback_loop_result["optimized_pipeline_config"]

        # MLOps should get highest weight due to best conversion rate
        assert (
            optimized_config["content_generation_weights"]["mlops_cost_optimization"]
            > 0.5
        )

        # DevTo should get highest allocation due to best ROI
        assert optimized_config["platform_distribution"]["devto"] > 0.4

        # Verify feedback integration summary
        assert "feedback_integration_summary" in feedback_loop_result
        summary = feedback_loop_result["feedback_integration_summary"]
        assert summary["performance_improvement_expected"] == "15-25%"

        # Verify optimization rationale
        assert "optimization_rationale" in feedback_loop_result
        rationale = feedback_loop_result["optimization_rationale"]
        assert "conversion rate" in rationale["topic_adjustments"]
        assert "ROI" in rationale["platform_adjustments"]
