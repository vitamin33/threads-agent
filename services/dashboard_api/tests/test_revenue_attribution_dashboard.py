"""
Tests for Revenue Attribution Dashboard functionality.

Testing the complete pipeline from content creation to job offers,
measuring ROI of the automated marketing system.

Following TDD principles - creating comprehensive failing tests first.
"""

from datetime import datetime, timedelta


class TestContentToRevenueAttribution:
    """Test tracking the complete chain from content to revenue"""

    def test_track_content_to_job_offer_attribution_chain(self):
        """
        Test that we can track a complete attribution chain from LinkedIn post to job offer.

        This is the fundamental test - if a LinkedIn post leads to engagement,
        then to a lead, then through interviews to a job offer, we should be able
        to track the complete attribution and calculate ROI.
        """
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Step 1: Content is published with tracking
        content_data = {
            "content_id": "linkedin_post_001",
            "platform": "linkedin",
            "content_type": "technical_post",
            "topic": "MLOps cost optimization",
            "utm_campaign": "mlops_expertise_showcase",
            "published_at": datetime.utcnow(),
            "creation_cost_hours": 2.5,
            "hourly_rate": 100,  # $250 creation cost
        }

        content_result = engine.track_content_creation(content_data)
        assert content_result["success"] is True
        assert content_result["content_id"] == "linkedin_post_001"
        assert content_result["tracking_enabled"] is True

        # Step 2: Content generates traffic with UTM tracking
        visitor_data = {
            "visitor_id": "visitor_12345",
            "source_content_id": "linkedin_post_001",
            "utm_source": "linkedin",
            "utm_campaign": "mlops_expertise_showcase",
            "timestamp": datetime.utcnow(),
        }

        traffic_result = engine.track_content_traffic(visitor_data)
        assert traffic_result["attribution_linked"] is True
        assert traffic_result["source_content_id"] == "linkedin_post_001"

        # Step 3: Lead scoring identifies hiring manager
        lead_data = {
            "visitor_id": "visitor_12345",
            "visitor_type": "hiring_manager",
            "hiring_manager_probability": 0.85,
            "company_name": "Netflix",
            "is_target_company": True,
        }

        lead_result = engine.track_lead_qualification(lead_data)
        assert lead_result["qualified_lead"] is True
        assert lead_result["attribution_chain_active"] is True

        # Step 4: Interview pipeline progression
        interview_progression = [
            {
                "stage": "initial_contact",
                "timestamp": datetime.utcnow(),
                "status": "completed",
            },
            {
                "stage": "phone_screen",
                "timestamp": datetime.utcnow() + timedelta(days=3),
                "status": "completed",
            },
            {
                "stage": "technical_interview",
                "timestamp": datetime.utcnow() + timedelta(days=10),
                "status": "completed",
            },
        ]

        for stage in interview_progression:
            interview_result = engine.track_interview_stage("visitor_12345", stage)
            assert interview_result["attribution_maintained"] is True

        # Step 5: Job offer received
        offer_data = {
            "visitor_id": "visitor_12345",
            "company_name": "Netflix",
            "position": "Senior MLOps Engineer",
            "initial_offer_amount": 180000,
            "offer_date": datetime.utcnow() + timedelta(days=15),
            "offer_status": "received",
        }

        offer_result = engine.track_job_offer(offer_data)
        assert offer_result["revenue_attributed"] is True
        assert offer_result["source_content_id"] == "linkedin_post_001"

        # Step 6: Calculate complete attribution chain
        attribution_chain = engine.get_complete_attribution_chain("linkedin_post_001")

        assert attribution_chain["content_id"] == "linkedin_post_001"
        assert attribution_chain["platform"] == "linkedin"
        assert attribution_chain["total_visitors"] == 1
        assert attribution_chain["qualified_leads"] == 1
        assert attribution_chain["job_offers"] == 1
        assert attribution_chain["revenue_amount"] == 180000
        assert attribution_chain["content_creation_cost"] == 250
        assert (
            attribution_chain["roi_percentage"] == ((180000 - 250) / 250) * 100
        )  # 71,890% ROI
        assert (
            attribution_chain["attribution_confidence"] >= 0.95
        )  # High confidence in direct attribution

    def test_attribution_chain_handles_multiple_touchpoints(self):
        """
        Test attribution when visitor engages with multiple content pieces
        before converting to job offer. Should attribute correctly.
        """
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Create multiple content pieces
        linkedin_post = {
            "content_id": "linkedin_post_002",
            "platform": "linkedin",
            "topic": "Kubernetes MLOps",
            "utm_campaign": "k8s_expertise",
            "published_at": datetime.utcnow() - timedelta(days=5),
        }

        devto_article = {
            "content_id": "devto_article_001",
            "platform": "devto",
            "topic": "MLOps Cost Optimization",
            "utm_campaign": "cost_optimization_series",
            "published_at": datetime.utcnow() - timedelta(days=3),
        }

        engine.track_content_creation(linkedin_post)
        engine.track_content_creation(devto_article)

        # Visitor engages with both pieces
        visitor_id = "visitor_67890"

        # First touchpoint: LinkedIn
        engine.track_content_traffic(
            {
                "visitor_id": visitor_id,
                "source_content_id": "linkedin_post_002",
                "utm_source": "linkedin",
                "timestamp": datetime.utcnow() - timedelta(days=2),
            }
        )

        # Second touchpoint: Dev.to
        engine.track_content_traffic(
            {
                "visitor_id": visitor_id,
                "source_content_id": "devto_article_001",
                "utm_source": "devto",
                "timestamp": datetime.utcnow() - timedelta(days=1),
            }
        )

        # Lead qualification and job offer
        engine.track_lead_qualification(
            {
                "visitor_id": visitor_id,
                "visitor_type": "hiring_manager",
                "company_name": "Google",
            }
        )

        engine.track_job_offer(
            {
                "visitor_id": visitor_id,
                "company_name": "Google",
                "initial_offer_amount": 220000,
                "offer_date": datetime.utcnow(),
            }
        )

        # Check attribution distribution
        linkedin_attribution = engine.get_complete_attribution_chain(
            "linkedin_post_002"
        )
        devto_attribution = engine.get_complete_attribution_chain("devto_article_001")

        # Should use attribution model (first-touch, last-touch, or linear)
        assert linkedin_attribution["attributed_revenue"] > 0
        assert devto_attribution["attributed_revenue"] > 0
        assert (
            linkedin_attribution["attributed_revenue"]
            + devto_attribution["attributed_revenue"]
            == 220000
        )


class TestPlatformROIAnalysis:
    """Test platform-specific ROI analysis and comparison"""

    def test_platform_roi_analysis_compares_linkedin_vs_devto_effectiveness(self):
        """
        Test that we can compare ROI across platforms to identify
        which platforms generate the highest-value opportunities.
        """
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Create content on both platforms with different results
        platform_results = engine.analyze_platform_roi(
            platforms=["linkedin", "devto", "medium"],
            date_range={
                "start_date": datetime.utcnow() - timedelta(days=30),
                "end_date": datetime.utcnow(),
            },
        )

        assert "linkedin" in platform_results
        assert "devto" in platform_results
        assert "medium" in platform_results

        # Each platform should have comprehensive ROI metrics
        linkedin_roi = platform_results["linkedin"]
        assert "total_content_pieces" in linkedin_roi
        assert "total_visitors" in linkedin_roi
        assert "qualified_leads" in linkedin_roi
        assert "job_offers" in linkedin_roi
        assert "total_revenue" in linkedin_roi
        assert "content_creation_cost" in linkedin_roi
        assert "roi_percentage" in linkedin_roi
        assert "cost_per_lead" in linkedin_roi
        assert "cost_per_offer" in linkedin_roi
        assert "average_offer_amount" in linkedin_roi
        assert "conversion_rate_traffic_to_lead" in linkedin_roi
        assert "conversion_rate_lead_to_offer" in linkedin_roi

    def test_platform_effectiveness_ranking(self):
        """Test ranking platforms by effectiveness for job generation"""
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Create content on different platforms with varying success
        # LinkedIn - high performing
        engine.track_content_creation(
            {
                "content_id": "linkedin_high_performer",
                "platform": "linkedin",
                "creation_cost_hours": 1,
                "hourly_rate": 100,
            }
        )

        # Dev.to - medium performing
        engine.track_content_creation(
            {
                "content_id": "devto_medium_performer",
                "platform": "devto",
                "creation_cost_hours": 2,
                "hourly_rate": 100,
            }
        )

        # Simulate different performance levels
        # LinkedIn: 1 visitor → 1 offer ($200k)
        engine.track_content_traffic(
            {
                "visitor_id": "linkedin_visitor",
                "source_content_id": "linkedin_high_performer",
                "utm_source": "linkedin",
            }
        )
        engine.track_lead_qualification(
            {"visitor_id": "linkedin_visitor", "visitor_type": "hiring_manager"}
        )
        engine.track_job_offer(
            {"visitor_id": "linkedin_visitor", "initial_offer_amount": 200000}
        )

        # Dev.to: 1 visitor → 1 offer ($150k)
        engine.track_content_traffic(
            {
                "visitor_id": "devto_visitor",
                "source_content_id": "devto_medium_performer",
                "utm_source": "devto",
            }
        )
        engine.track_lead_qualification(
            {"visitor_id": "devto_visitor", "visitor_type": "hiring_manager"}
        )
        engine.track_job_offer(
            {"visitor_id": "devto_visitor", "initial_offer_amount": 150000}
        )

        platform_ranking = engine.get_platform_effectiveness_ranking(
            metric="revenue_per_content_piece"
        )

        assert len(platform_ranking) > 0
        assert all("platform" in p for p in platform_ranking)
        assert all("metric_value" in p for p in platform_ranking)
        assert all("rank" in p for p in platform_ranking)

        # Should be sorted by effectiveness
        ranks = [p["rank"] for p in platform_ranking]
        assert ranks == sorted(ranks)

        # LinkedIn should rank higher (200k vs 150k revenue per content piece)
        linkedin_ranking = next(
            p for p in platform_ranking if p["platform"] == "linkedin"
        )
        devto_ranking = next(p for p in platform_ranking if p["platform"] == "devto")
        assert (
            linkedin_ranking["rank"] < devto_ranking["rank"]
        )  # Lower rank number = better


class TestInterviewPipelineTracking:
    """Test tracking leads through the complete interview pipeline"""

    def test_interview_pipeline_tracks_complete_funnel(self):
        """
        Test tracking leads through: Lead Generation → Phone Screen → Technical
        Interview → Final Interview → Offer → Acceptance
        """
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        visitor_id = "visitor_pipeline_test"

        # Track lead through complete pipeline
        pipeline_stages = [
            {"stage": "lead_generated", "timestamp": datetime.utcnow()},
            {
                "stage": "initial_contact",
                "timestamp": datetime.utcnow() + timedelta(days=1),
            },
            {
                "stage": "phone_screen_scheduled",
                "timestamp": datetime.utcnow() + timedelta(days=3),
            },
            {
                "stage": "phone_screen_completed",
                "timestamp": datetime.utcnow() + timedelta(days=5),
            },
            {
                "stage": "technical_interview_scheduled",
                "timestamp": datetime.utcnow() + timedelta(days=8),
            },
            {
                "stage": "technical_interview_completed",
                "timestamp": datetime.utcnow() + timedelta(days=10),
            },
            {
                "stage": "final_interview_scheduled",
                "timestamp": datetime.utcnow() + timedelta(days=12),
            },
            {
                "stage": "final_interview_completed",
                "timestamp": datetime.utcnow() + timedelta(days=14),
            },
            {
                "stage": "offer_received",
                "timestamp": datetime.utcnow() + timedelta(days=16),
            },
            {
                "stage": "offer_accepted",
                "timestamp": datetime.utcnow() + timedelta(days=18),
            },
        ]

        for stage_data in pipeline_stages:
            result = engine.track_interview_stage(visitor_id, stage_data)
            assert result["success"] is True
            assert result["stage"] == stage_data["stage"]

        # Get complete pipeline analysis
        pipeline_analysis = engine.get_interview_pipeline_analysis(visitor_id)

        assert pipeline_analysis["total_stages"] == 10
        assert pipeline_analysis["current_stage"] == "offer_accepted"
        assert pipeline_analysis["pipeline_completion_rate"] == 1.0
        assert pipeline_analysis["total_pipeline_duration_days"] == 18
        assert "stage_durations" in pipeline_analysis
        assert "conversion_rates_by_stage" in pipeline_analysis

    def test_pipeline_conversion_rates_calculation(self):
        """Test calculation of conversion rates at each pipeline stage"""
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Simulate multiple leads at different stages
        pipeline_data = [
            {
                "visitor_id": "lead_1",
                "stages": [
                    "lead_generated",
                    "phone_screen_completed",
                    "technical_interview_completed",
                    "offer_received",
                ],
            },  # Offer but no acceptance
            {
                "visitor_id": "lead_2",
                "stages": ["lead_generated", "phone_screen_completed"],
            },  # Phone screen only
            {"visitor_id": "lead_3", "stages": ["lead_generated"]},  # Lead only
            {
                "visitor_id": "lead_4",
                "stages": [
                    "lead_generated",
                    "phone_screen_completed",
                    "technical_interview_completed",
                    "offer_received",
                    "offer_accepted",
                ],
            },  # Full pipeline with acceptance
            {
                "visitor_id": "lead_5",
                "stages": [
                    "lead_generated",
                    "phone_screen_completed",
                    "technical_interview_completed",
                ],
            },  # Technical interview only
        ]

        for lead in pipeline_data:
            for stage in lead["stages"]:
                engine.track_interview_stage(
                    lead["visitor_id"], {"stage": stage, "timestamp": datetime.utcnow()}
                )

        conversion_analysis = engine.calculate_pipeline_conversion_rates()

        # 5 leads generated, 4 reached phone screen = 80% conversion
        assert conversion_analysis["lead_generated_to_phone_screen"] == 0.8

        # 4 reached phone screen, 3 reached technical interview = 75% conversion
        assert conversion_analysis["phone_screen_to_technical_interview"] == 0.75

        # 3 reached technical interview, 2 reached offer = 66.67% conversion (2/3)
        assert (
            abs(
                conversion_analysis["technical_interview_to_offer"] - 0.6666666666666666
            )
            < 0.001
        )

        # 2 offers, 1 accepted = 50% conversion
        assert conversion_analysis["offer_to_acceptance"] == 0.5


class TestSalaryNegotiationTracking:
    """Test tracking salary offers and negotiation outcomes"""

    def test_salary_negotiation_tracking_records_full_process(self):
        """
        Test tracking: Initial Offer → Negotiation → Counter Offer → Final Acceptance
        """
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        visitor_id = "salary_negotiation_test"

        # Initial offer
        initial_offer_result = engine.track_salary_offer(
            visitor_id,
            {
                "offer_type": "initial",
                "company_name": "Meta",
                "position": "Senior MLOps Engineer",
                "base_salary": 170000,
                "equity_value": 50000,
                "bonus": 25000,
                "total_compensation": 245000,
                "offer_date": datetime.utcnow(),
            },
        )

        assert initial_offer_result["offer_tracked"] is True
        assert initial_offer_result["negotiation_status"] == "pending"

        # Counter offer negotiation
        counter_result = engine.track_salary_negotiation(
            visitor_id,
            {
                "negotiation_type": "counter_offer",
                "requested_base_salary": 190000,
                "requested_equity_value": 60000,
                "requested_total_compensation": 275000,
                "justification": "Market rate analysis + MLOps expertise premium",
                "negotiation_date": datetime.utcnow() + timedelta(days=2),
            },
        )

        assert counter_result["negotiation_tracked"] is True

        # Final offer acceptance
        final_result = engine.track_salary_offer(
            visitor_id,
            {
                "offer_type": "final",
                "company_name": "Meta",
                "base_salary": 185000,
                "equity_value": 55000,
                "bonus": 30000,
                "total_compensation": 270000,
                "offer_date": datetime.utcnow() + timedelta(days=5),
                "acceptance_status": "accepted",
            },
        )

        assert final_result["offer_tracked"] is True
        assert final_result["negotiation_status"] == "completed"

        # Get negotiation analysis
        negotiation_analysis = engine.get_salary_negotiation_analysis(visitor_id)

        assert negotiation_analysis["initial_offer"] == 245000
        assert negotiation_analysis["final_offer"] == 270000
        assert negotiation_analysis["negotiation_increase"] == 25000
        assert (
            negotiation_analysis["negotiation_percentage"] == (25000 / 245000) * 100
        )  # ~10.2%
        assert negotiation_analysis["negotiation_success"] is True
        assert negotiation_analysis["days_to_completion"] == 5

    def test_salary_benchmarking_analysis(self):
        """Test analysis of salary offers against market benchmarks"""
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Track multiple offers for benchmarking
        offers_data = [
            {
                "company": "Google",
                "position": "Senior MLOps Engineer",
                "total_comp": 280000,
            },
            {
                "company": "Meta",
                "position": "Senior MLOps Engineer",
                "total_comp": 270000,
            },
            {
                "company": "Netflix",
                "position": "Senior MLOps Engineer",
                "total_comp": 300000,
            },
            {"company": "Uber", "position": "MLOps Engineer", "total_comp": 240000},
        ]

        for offer_data in offers_data:
            engine.track_salary_offer(
                f"visitor_{offer_data['company']}",
                {
                    "offer_type": "final",
                    "company_name": offer_data["company"],
                    "position": offer_data["position"],
                    "total_compensation": offer_data["total_comp"],
                    "acceptance_status": "accepted",
                },
            )

        benchmark_analysis = engine.get_salary_benchmark_analysis(
            position="Senior MLOps Engineer"
        )

        assert benchmark_analysis["position"] == "Senior MLOps Engineer"
        assert (
            benchmark_analysis["total_offers"] == 3
        )  # Excluding Uber (different level)
        assert (
            benchmark_analysis["average_compensation"] == 283333
        )  # (280k + 270k + 300k) / 3
        assert benchmark_analysis["median_compensation"] == 280000
        assert benchmark_analysis["min_compensation"] == 270000
        assert benchmark_analysis["max_compensation"] == 300000
        assert "compensation_range" in benchmark_analysis


class TestCostAnalysisAndROI:
    """Test comprehensive cost analysis and ROI calculation"""

    def test_roi_calculation_includes_all_cost_components(self):
        """
        Test ROI calculation including: Content creation cost, platform costs,
        tool subscriptions, opportunity costs vs revenue generated.
        """
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Track costs for a content campaign
        campaign_costs = {
            "campaign_id": "mlops_expertise_q1_2024",
            "content_creation_hours": 40,  # 1 hour per day for 40 days
            "hourly_rate": 100,  # $4000 content creation
            "platform_advertising_spend": 500,  # LinkedIn ads
            "tool_subscriptions": 200,  # Analytics tools
            "opportunity_cost": 1000,  # Time that could be spent on consulting
            "total_campaign_cost": 5700,
        }

        cost_result = engine.track_campaign_costs(campaign_costs)
        assert cost_result["costs_tracked"] is True
        assert cost_result["total_cost"] == 5700

        # Track revenue generated from campaign
        campaign_revenue = [
            {
                "company": "Netflix",
                "total_compensation": 300000,
                "attributed_percentage": 0.8,
            },  # 240k attributed
            {
                "company": "Google",
                "total_compensation": 280000,
                "attributed_percentage": 0.6,
            },  # 168k attributed
            {
                "company": "Meta",
                "total_compensation": 270000,
                "attributed_percentage": 0.3,
            },  # 81k attributed
        ]

        total_attributed_revenue = 0
        for revenue in campaign_revenue:
            attributed_amount = (
                revenue["total_compensation"] * revenue["attributed_percentage"]
            )
            total_attributed_revenue += attributed_amount

            engine.track_attributed_revenue(
                campaign_costs["campaign_id"],
                {
                    "company": revenue["company"],
                    "total_compensation": revenue["total_compensation"],
                    "attributed_revenue": attributed_amount,
                },
            )

        # Calculate ROI
        roi_analysis = engine.calculate_campaign_roi(campaign_costs["campaign_id"])

        expected_revenue = 240000 + 168000 + 81000  # 489k
        expected_roi = ((expected_revenue - 5700) / 5700) * 100  # ~8,484% ROI

        assert roi_analysis["total_costs"] == 5700
        assert roi_analysis["total_attributed_revenue"] == expected_revenue
        assert roi_analysis["net_profit"] == expected_revenue - 5700
        assert roi_analysis["roi_percentage"] == expected_roi
        assert roi_analysis["revenue_multiple"] == expected_revenue / 5700  # ~85.8x
        assert (
            roi_analysis["payback_period_days"] <= 90
        )  # Should payback within 3 months

    def test_cost_per_acquisition_analysis(self):
        """Test calculation of cost per lead and cost per job offer"""
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Simulate campaign with costs and results
        campaign_id = "cost_analysis_test"

        engine.track_campaign_costs(
            {"campaign_id": campaign_id, "total_campaign_cost": 10000}
        )

        # Track leads and offers
        campaign_results = {
            "total_leads": 50,
            "qualified_leads": 20,
            "job_offers": 3,
            "accepted_offers": 2,
        }

        for i in range(campaign_results["total_leads"]):
            engine.track_campaign_lead(campaign_id, f"lead_{i}")

        for i in range(campaign_results["job_offers"]):
            engine.track_campaign_offer(campaign_id, f"offer_{i}")

        cpa_analysis = engine.calculate_cost_per_acquisition(campaign_id)

        assert cpa_analysis["cost_per_lead"] == 200  # $10k / 50 leads
        assert cpa_analysis["cost_per_qualified_lead"] == 500  # $10k / 20 qualified
        assert cpa_analysis["cost_per_offer"] == 3333  # $10k / 3 offers (rounded)
        assert cpa_analysis["cost_per_acceptance"] == 5000  # $10k / 2 acceptances


class TestPredictiveRevenueAnalytics:
    """Test forecasting revenue based on content performance patterns"""

    def test_revenue_forecasting_based_on_content_patterns(self):
        """
        Test predicting future revenue based on historical content performance
        and current pipeline activity.
        """
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Historical performance data for forecasting
        historical_data = {
            "monthly_content_pieces": 20,
            "average_engagement_rate": 0.05,  # 5% of viewers engage meaningfully
            "lead_conversion_rate": 0.15,  # 15% of engaged users become leads
            "offer_conversion_rate": 0.20,  # 20% of leads get job offers
            "average_offer_amount": 260000,
            "monthly_cost": 8000,
        }

        # Current pipeline state
        current_pipeline = {
            "active_leads": 25,
            "leads_in_phone_screen": 8,
            "leads_in_technical_interview": 5,
            "leads_in_final_interview": 3,
            "pending_offers": 2,
        }

        forecast = engine.generate_revenue_forecast(
            historical_data=historical_data,
            current_pipeline=current_pipeline,
            forecast_months=6,
        )

        assert "monthly_forecast" in forecast
        assert len(forecast["monthly_forecast"]) == 6

        # Check first month forecast structure
        month_1 = forecast["monthly_forecast"][0]
        assert "month" in month_1
        assert "predicted_offers" in month_1
        assert "predicted_revenue" in month_1
        assert "confidence_interval" in month_1
        assert "pipeline_conversion_revenue" in month_1
        assert "new_content_revenue" in month_1

        # Total forecast summary
        assert "total_predicted_revenue" in forecast
        assert "total_predicted_offers" in forecast
        assert "predicted_roi" in forecast
        assert "forecast_confidence" in forecast

        # Revenue should be realistic based on inputs
        total_predicted = forecast["total_predicted_revenue"]
        assert total_predicted > 500000  # Should predict meaningful revenue
        assert total_predicted < 5000000  # But not unrealistically high

    def test_content_performance_optimization_recommendations(self):
        """Test generating recommendations for content strategy optimization"""
        from revenue_attribution_dashboard import RevenueAttributionEngine

        engine = RevenueAttributionEngine()

        # Analyze content performance patterns
        content_analysis = {
            "high_performing_topics": [
                "MLOps cost optimization",
                "Kubernetes automation",
            ],
            "high_performing_platforms": ["linkedin", "devto"],
            "optimal_posting_times": ["Tuesday 9AM", "Thursday 2PM"],
            "best_content_formats": ["technical_tutorial", "case_study"],
        }

        optimization_recommendations = (
            engine.generate_content_optimization_recommendations(content_analysis)
        )

        assert "topic_recommendations" in optimization_recommendations
        assert "platform_strategy" in optimization_recommendations
        assert "posting_schedule" in optimization_recommendations
        assert "content_format_mix" in optimization_recommendations
        assert "predicted_improvement" in optimization_recommendations

        # Should include specific actionable recommendations
        platform_strategy = optimization_recommendations["platform_strategy"]
        assert "focus_platforms" in platform_strategy
        assert "linkedin" in platform_strategy["focus_platforms"]
        assert "resource_allocation" in platform_strategy
