"""Tests for unified analytics dashboard that aggregates all platform metrics"""

import pytest
from fastapi.testclient import TestClient

# This will fail initially since we haven't implemented the unified dashboard yet
# pytest.importorskip("dashboard_api.unified_analytics")  # Comment out for now to test endpoints


class TestUnifiedAnalyticsDashboard:
    """Test unified analytics dashboard functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        import sys
        import os

        # Add the parent directory to sys.path
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from main import app

        return TestClient(app)

    def test_unified_dashboard_endpoint_exists(self, client):
        """Test that unified analytics dashboard endpoint exists"""
        response = client.get("/api/analytics/unified")

        # Should not return 404 (endpoint should exist)
        assert response.status_code != 404

    def test_get_unified_metrics_returns_all_platforms(self, client):
        """Test that unified metrics endpoint returns data from all platforms"""
        response = client.get("/api/analytics/unified")

        assert response.status_code == 200
        data = response.json()

        # Should contain metrics from all platforms
        assert "platforms" in data
        platforms = data["platforms"]

        expected_platforms = [
            "linkedin",
            "twitter",
            "medium",
            "github",
            "threads",
            "devto",
        ]
        for platform in expected_platforms:
            assert platform in platforms

        # Each platform should have metrics and conversion data
        for platform, metrics in platforms.items():
            assert "metrics" in metrics
            assert "conversion_data" in metrics
            assert "last_updated" in metrics

    def test_get_conversion_summary_aggregates_all_platforms(self, client):
        """Test that conversion summary aggregates data from all platforms"""
        response = client.get("/api/analytics/conversion-summary")

        assert response.status_code == 200
        data = response.json()

        # Should have aggregated conversion metrics
        assert "total_serbyn_pro_visits" in data
        assert "total_job_inquiries" in data
        assert "best_converting_platform" in data
        assert "overall_conversion_rate" in data
        assert "platform_breakdown" in data

        # Platform breakdown should show per-platform conversions
        breakdown = data["platform_breakdown"]
        assert isinstance(breakdown, dict)
        for platform, conversion_data in breakdown.items():
            assert "serbyn_pro_visits" in conversion_data
            assert "job_inquiries" in conversion_data
            assert "conversion_rate" in conversion_data

    def test_get_roi_analysis_calculates_content_marketing_roi(self, client):
        """Test that ROI analysis calculates return on content marketing investment"""
        response = client.get("/api/analytics/roi-analysis")

        assert response.status_code == 200
        data = response.json()

        # Should calculate ROI metrics
        assert "total_content_pieces" in data
        assert "total_engagement" in data
        assert "estimated_time_investment_hours" in data
        assert "lead_generation_value" in data
        assert "roi_percentage" in data
        assert "cost_per_lead" in data
        assert "recommendations" in data

        # Recommendations should be actionable
        recommendations = data["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    def test_get_platform_performance_ranking(self, client):
        """Test that platform performance ranking shows which platforms perform best"""
        response = client.get("/api/analytics/platform-ranking")

        assert response.status_code == 200
        data = response.json()

        # Should rank platforms by performance
        assert "ranking" in data
        assert "criteria" in data

        ranking = data["ranking"]
        assert isinstance(ranking, list)

        # Each platform should have ranking metrics
        for platform_data in ranking:
            assert "platform" in platform_data
            assert "rank" in platform_data
            assert "score" in platform_data
            assert "engagement_rate" in platform_data
            assert "conversion_rate" in platform_data
            assert "reach" in platform_data

    @pytest.mark.asyncio
    async def test_websocket_real_time_analytics_updates(self, client):
        """Test that WebSocket provides real-time analytics updates"""
        # This test would normally use WebSocket client, but for TDD we'll test the endpoint exists
        response = client.get("/api/analytics/websocket-info")

        assert response.status_code == 200
        data = response.json()

        # Should provide WebSocket connection info
        assert "websocket_url" in data
        assert "supported_events" in data

        supported_events = data["supported_events"]
        expected_events = [
            "platform_metrics_update",
            "conversion_event",
            "roi_recalculation",
            "new_lead_generated",
        ]

        for event in expected_events:
            assert event in supported_events


class TestAnalyticsDataAggregation:
    """Test the analytics data aggregation service"""

    @pytest.fixture
    def aggregation_service(self):
        """Create analytics aggregation service"""
        # This will fail until we implement it
        from dashboard_api.unified_analytics import AnalyticsAggregationService

        return AnalyticsAggregationService()

    @pytest.mark.asyncio
    async def test_collect_all_platform_metrics(self, aggregation_service):
        """Test that service can collect metrics from all platforms"""
        metrics = await aggregation_service.collect_all_platform_metrics()

        assert isinstance(metrics, dict)

        # Should have data from all platforms
        expected_platforms = [
            "linkedin",
            "twitter",
            "medium",
            "github",
            "threads",
            "devto",
        ]
        for platform in expected_platforms:
            assert platform in metrics

            platform_data = metrics[platform]
            assert "metrics" in platform_data
            assert "conversion_data" in platform_data
            assert "collected_at" in platform_data

    @pytest.mark.asyncio
    async def test_calculate_conversion_rates(self, aggregation_service):
        """Test conversion rate calculation across platforms"""
        mock_metrics = {
            "linkedin": {
                "metrics": {"profile_views": 1000},
                "conversion_data": {"serbyn_pro_visits": 50, "job_inquiries": 5},
            },
            "twitter": {
                "metrics": {"impressions": 5000},
                "conversion_data": {"serbyn_pro_visits": 25, "job_inquiries": 2},
            },
        }

        conversion_summary = await aggregation_service.calculate_conversion_summary(
            mock_metrics
        )

        assert "total_serbyn_pro_visits" in conversion_summary
        assert conversion_summary["total_serbyn_pro_visits"] == 75
        assert "total_job_inquiries" in conversion_summary
        assert conversion_summary["total_job_inquiries"] == 7
        assert "overall_conversion_rate" in conversion_summary

    @pytest.mark.asyncio
    async def test_identify_best_performing_platform(self, aggregation_service):
        """Test identification of best performing platform"""
        mock_metrics = {
            "linkedin": {
                "conversion_data": {"job_inquiries": 5, "serbyn_pro_visits": 50}
            },
            "twitter": {
                "conversion_data": {"job_inquiries": 2, "serbyn_pro_visits": 25}
            },
        }

        best_platform = await aggregation_service.identify_best_platform(mock_metrics)

        assert best_platform == "linkedin"  # Higher job inquiries


class TestConversionTracking:
    """Test conversion tracking from content to leads"""

    @pytest.fixture
    def conversion_tracker(self):
        """Create conversion tracking service"""
        # This will fail until we implement it
        from dashboard_api.unified_analytics import ConversionTracker

        return ConversionTracker()

    @pytest.mark.asyncio
    async def test_track_content_to_website_conversion(self, conversion_tracker):
        """Test tracking conversions from content to serbyn.pro"""
        conversion_event = {
            "source_platform": "linkedin",
            "content_url": "https://linkedin.com/posts/vitaliiserbyn-post-123",
            "visitor_ip": "192.168.1.1",
            "timestamp": "2025-01-15T10:30:00Z",
            "destination_url": "https://serbyn.pro",
        }

        result = await conversion_tracker.track_conversion(conversion_event)

        assert result["success"] is True
        assert "conversion_id" in result
        assert result["platform"] == "linkedin"

    @pytest.mark.asyncio
    async def test_track_website_to_lead_conversion(self, conversion_tracker):
        """Test tracking conversions from website visit to job inquiry"""
        lead_event = {
            "visitor_ip": "192.168.1.1",
            "source_conversion_id": "conv_123",
            "lead_type": "job_inquiry",
            "contact_method": "email",
            "timestamp": "2025-01-15T11:00:00Z",
        }

        result = await conversion_tracker.track_lead_conversion(lead_event)

        assert result["success"] is True
        assert "lead_id" in result
        assert (
            result["attributed_platform"] == "linkedin"
        )  # Should link back to original source

    @pytest.mark.asyncio
    async def test_calculate_attribution_chain(self, conversion_tracker):
        """Test calculating full attribution chain from content to lead"""
        chain = await conversion_tracker.get_attribution_chain("lead_123")

        assert "content_source" in chain
        assert "platform" in chain
        assert "content_url" in chain
        assert "website_visit_timestamp" in chain
        assert "lead_conversion_timestamp" in chain
        assert "total_conversion_time_hours" in chain
