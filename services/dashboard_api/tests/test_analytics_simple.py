"""Simple tests for unified analytics dashboard endpoints"""

import pytest
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient


class TestAnalyticsEndpoints:
    """Test the analytics API endpoints directly"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)

    def test_unified_analytics_endpoint_exists(self, client):
        """Test that unified analytics endpoint exists and returns 200"""
        response = client.get("/api/analytics/unified")
        
        # Should return 200, not 404
        assert response.status_code == 200
        
        data = response.json()
        assert "platforms" in data

    def test_conversion_summary_endpoint_exists(self, client):
        """Test that conversion summary endpoint exists and returns 200"""
        response = client.get("/api/analytics/conversion-summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have conversion metrics
        assert "total_serbyn_pro_visits" in data
        assert "total_job_inquiries" in data
        assert "best_converting_platform" in data

    def test_roi_analysis_endpoint_exists(self, client):
        """Test that ROI analysis endpoint exists and returns 200"""
        response = client.get("/api/analytics/roi-analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have ROI metrics
        assert "roi_percentage" in data
        assert "cost_per_lead" in data
        assert "recommendations" in data

    def test_platform_ranking_endpoint_exists(self, client):
        """Test that platform ranking endpoint exists and returns 200"""
        response = client.get("/api/analytics/platform-ranking")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have ranking data
        assert "ranking" in data
        assert "criteria" in data

    def test_websocket_info_endpoint_exists(self, client):
        """Test that WebSocket info endpoint exists and returns 200"""
        response = client.get("/api/analytics/websocket-info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have WebSocket info
        assert "websocket_url" in data
        assert "supported_events" in data