"""
Integration tests for the complete Traffic Driver system.

This tests the end-to-end integration of UTM tracking, lead scoring,
conversion funnel tracking, A/B testing, and analytics aggregation.
"""

import pytest
import sys

sys.path.append(
    "/Users/vitaliiserbyn/development/wt-a3-analytics/services/dashboard_api"
)

from traffic_driver_integration import (
    TrafficDriverService,
    ContentToJobOpportunityPipeline,
)


class TestTrafficDriverIntegration:
    """Test the complete traffic driver integration"""

    @pytest.mark.asyncio
    async def test_complete_visitor_tracking_flow(self):
        """Test complete flow from content click to analytics"""
        service = TrafficDriverService()

        # Simulate visitor from LinkedIn content
        visitor_data = {
            "visitor_id": "test_visitor_001",
            "referrer_url": "https://serbyn.pro/portfolio?utm_source=linkedin&utm_medium=social&utm_campaign=pr_automation&utm_content=mlops_case_study",
            "current_url": "https://serbyn.pro/portfolio",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Test Browser)",
        }

        # Track visitor from content
        tracking_result = await service.track_visitor_from_content(visitor_data)

        assert tracking_result["success"] == True
        assert tracking_result["platform"] == "linkedin"
        assert tracking_result["campaign"] == "pr_automation"
        assert "utm_tracking" in tracking_result

        # Track page behavior
        behavior_data = {
            "visitor_id": "test_visitor_001",
            "page_url": "https://serbyn.pro/portfolio",
            "time_on_page_seconds": 240,
            "scroll_depth_percent": 90,
            "utm_source": "linkedin",
        }

        behavior_result = await service.track_page_behavior(behavior_data)

        assert behavior_result["success"] == True
        assert behavior_result["lead_score"]["total_score"] > 0
        assert behavior_result["lead_score"]["hiring_manager_probability"] > 0.5

        # Simulate job inquiry
        inquiry_data = {
            "visitor_id": "test_visitor_001",
            "source_page": "https://serbyn.pro/contact",
            "inquiry_details": {
                "company": "TechCorp",
                "position": "Senior MLOps Engineer",
                "budget_range": "$160k-180k",
            },
            "estimated_value": 170000,
        }

        inquiry_result = await service.track_job_inquiry(inquiry_data)

        assert inquiry_result["success"] == True
        assert inquiry_result["conversion_tracked"] == True
        assert inquiry_result["attribution"]["platform"] == "linkedin"
        assert inquiry_result["estimated_value"] > 0

    @pytest.mark.asyncio
    async def test_conversion_analytics_generation(self):
        """Test analytics and insights generation"""
        service = TrafficDriverService()

        # Generate some test data first
        await self._generate_test_conversion_data(service)

        # Get analytics
        analytics = await service.get_conversion_analytics()

        assert "platform_analytics" in analytics
        assert "conversion_funnel" in analytics
        assert "ab_test_results" in analytics
        assert "roi_analysis" in analytics
        assert "optimization_recommendations" in analytics

        # Check conversion funnel metrics
        funnel_metrics = analytics["conversion_funnel"]["metrics"]
        assert funnel_metrics["content_clicks"] > 0
        assert funnel_metrics["website_visits"] > 0

        # Check ROI analysis
        roi_analysis = analytics["roi_analysis"]
        assert "total_estimated_value" in roi_analysis
        assert "roi_percentage" in roi_analysis
        assert "cost_per_lead" in roi_analysis

    @pytest.mark.asyncio
    async def test_ab_test_creation_and_tracking(self):
        """Test A/B test creation and conversion tracking"""
        service = TrafficDriverService()

        # Create A/B test
        test_config = {
            "test_type": "contact_cta",
            "test_name": "contact_optimization",
            "traffic_split": 0.5,
            "success_metric": "job_inquiry_conversion",
            "minimum_sample_size": 50,
        }

        test_result = await service.create_conversion_optimization_test(test_config)

        assert test_result["success"] == True
        assert test_result["variants_created"] == 2

        # Test visitor assignment
        visitor_data = {
            "visitor_id": "ab_test_visitor",
            "referrer_url": "https://serbyn.pro/portfolio?utm_source=devto&utm_campaign=technical_content",
            "current_url": "https://serbyn.pro/portfolio",
        }

        tracking_result = await service.track_visitor_from_content(visitor_data)

        assert tracking_result["success"] == True
        assert len(tracking_result["ab_assignments"]) > 0

    async def _generate_test_conversion_data(self, service: TrafficDriverService):
        """Generate test conversion data for analytics testing"""

        # Simulate multiple visitors and conversions
        test_visitors = [
            {
                "visitor_id": f"test_visitor_{i}",
                "referrer_url": f"https://serbyn.pro/portfolio?utm_source={'linkedin' if i % 2 == 0 else 'devto'}&utm_campaign=pr_automation",
                "current_url": "https://serbyn.pro/portfolio",
            }
            for i in range(5)
        ]

        for visitor_data in test_visitors:
            # Track visitor
            await service.track_visitor_from_content(visitor_data)

            # Track behavior
            behavior_data = {
                "visitor_id": visitor_data["visitor_id"],
                "page_url": "https://serbyn.pro/portfolio",
                "time_on_page_seconds": 180,
                "scroll_depth_percent": 80,
                "utm_source": "linkedin"
                if "linkedin" in visitor_data["referrer_url"]
                else "devto",
            }
            await service.track_page_behavior(behavior_data)

            # Simulate some inquiries (50% conversion rate)
            if int(visitor_data["visitor_id"].split("_")[-1]) % 2 == 0:
                inquiry_data = {
                    "visitor_id": visitor_data["visitor_id"],
                    "source_page": "https://serbyn.pro/contact",
                    "inquiry_details": {
                        "company": "TestCorp",
                        "position": "MLOps Engineer",
                        "budget_range": "$150k+",
                    },
                    "estimated_value": 160000,
                }
                await service.track_job_inquiry(inquiry_data)


class TestContentToJobOpportunityPipeline:
    """Test the complete content to job opportunity pipeline"""

    @pytest.mark.asyncio
    async def test_content_visitor_processing(self):
        """Test processing a visitor from content through the pipeline"""
        pipeline = ContentToJobOpportunityPipeline()

        visitor_data = {
            "visitor_id": "pipeline_test_visitor",
            "referrer_url": "https://serbyn.pro/portfolio?utm_source=linkedin&utm_medium=social&utm_campaign=pr_automation",
            "current_url": "https://serbyn.pro/portfolio",
            "ip_address": "192.168.1.200",
        }

        result = await pipeline.process_content_visitor(visitor_data)

        assert result["visitor_tracked"] == True
        assert result["platform"] == "linkedin"
        assert result["campaign"] == "pr_automation"
        assert "lead_score" in result
        assert result["conversion_potential"] >= 0.0
        assert result["conversion_potential"] <= 1.0

    @pytest.mark.asyncio
    async def test_campaign_performance_analytics(self):
        """Test campaign performance analytics generation"""
        pipeline = ContentToJobOpportunityPipeline()

        # Generate some test data
        test_visitors = [
            {
                "visitor_id": f"campaign_visitor_{i}",
                "referrer_url": "https://serbyn.pro/portfolio?utm_source=linkedin&utm_campaign=campaign_test",
                "current_url": "https://serbyn.pro/portfolio",
            }
            for i in range(3)
        ]

        for visitor_data in test_visitors:
            await pipeline.process_content_visitor(visitor_data)

        # Get performance metrics
        performance = await pipeline.get_campaign_performance()

        assert "platform_analytics" in performance
        assert "conversion_funnel" in performance
        assert "roi_analysis" in performance
        assert "optimization_recommendations" in performance

        # Check that we have recommendations
        recommendations = performance["optimization_recommendations"]
        assert len(recommendations) > 0
        assert any(
            "content" in rec.lower() or "optimization" in rec.lower()
            for rec in recommendations
        )
