"""Minimal test for unified analytics functionality"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime


class TestUnifiedAnalytics:
    """Test unified analytics module directly"""

    def test_analytics_aggregation_service_exists(self):
        """Test that AnalyticsAggregationService class exists"""
        import sys
        import os
        # Add parent directory to path for imports
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from unified_analytics import AnalyticsAggregationService
        
        service = AnalyticsAggregationService()
        assert service is not None
        assert hasattr(service, 'collect_all_platform_metrics')
        assert hasattr(service, 'calculate_conversion_summary')

    def test_conversion_tracker_exists(self):
        """Test that ConversionTracker class exists"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from unified_analytics import ConversionTracker
        
        tracker = ConversionTracker()
        assert tracker is not None
        assert hasattr(tracker, 'track_conversion')
        assert hasattr(tracker, 'track_lead_conversion')

    @pytest.mark.asyncio
    async def test_collect_all_platform_metrics_returns_expected_structure(self):
        """Test that collect_all_platform_metrics returns expected data structure"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from unified_analytics import AnalyticsAggregationService
        
        service = AnalyticsAggregationService()
        metrics = await service.collect_all_platform_metrics()
        
        # Should return dict with platform data
        assert isinstance(metrics, dict)
        
        # Should have all expected platforms
        expected_platforms = ["linkedin", "twitter", "medium", "github", "threads", "devto"]
        for platform in expected_platforms:
            assert platform in metrics
            
            platform_data = metrics[platform]
            assert "metrics" in platform_data
            assert "conversion_data" in platform_data
            assert "collected_at" in platform_data

    @pytest.mark.asyncio
    async def test_calculate_conversion_summary_aggregates_data(self):
        """Test that conversion summary aggregates data correctly"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from unified_analytics import AnalyticsAggregationService
        
        service = AnalyticsAggregationService()
        
        # Mock platform data
        mock_data = {
            "linkedin": {
                "conversion_data": {"serbyn_pro_visits": 50, "job_inquiries": 5}
            },
            "twitter": {
                "conversion_data": {"serbyn_pro_visits": 25, "job_inquiries": 2}
            }
        }
        
        summary = await service.calculate_conversion_summary(mock_data)
        
        assert summary["total_serbyn_pro_visits"] == 75
        assert summary["total_job_inquiries"] == 7
        assert "overall_conversion_rate" in summary
        assert "best_converting_platform" in summary

    @pytest.mark.asyncio
    async def test_track_conversion_creates_conversion_record(self):
        """Test that track_conversion creates a conversion record"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from unified_analytics import ConversionTracker
        
        tracker = ConversionTracker()
        
        conversion_event = {
            "source_platform": "linkedin",
            "content_url": "https://linkedin.com/posts/test-123",
            "visitor_ip": "192.168.1.1",
            "timestamp": datetime.utcnow().isoformat(),
            "destination_url": "https://serbyn.pro"
        }
        
        result = await tracker.track_conversion(conversion_event)
        
        assert result["success"] is True
        assert "conversion_id" in result
        assert result["platform"] == "linkedin"

    @pytest.mark.asyncio 
    async def test_track_lead_conversion_links_to_original_conversion(self):
        """Test that lead conversion links back to original conversion"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from unified_analytics import ConversionTracker
        
        tracker = ConversionTracker()
        
        # First create a conversion
        conversion_event = {
            "source_platform": "linkedin",
            "content_url": "https://linkedin.com/posts/test-123",
            "visitor_ip": "192.168.1.1",
            "timestamp": datetime.utcnow().isoformat(),
            "destination_url": "https://serbyn.pro"
        }
        
        conversion_result = await tracker.track_conversion(conversion_event)
        conversion_id = conversion_result["conversion_id"]
        
        # Now track a lead conversion
        lead_event = {
            "visitor_ip": "192.168.1.1",
            "source_conversion_id": conversion_id,
            "lead_type": "job_inquiry",
            "contact_method": "email",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        lead_result = await tracker.track_lead_conversion(lead_event)
        
        assert lead_result["success"] is True
        assert "lead_id" in lead_result
        assert lead_result["attributed_platform"] == "linkedin"