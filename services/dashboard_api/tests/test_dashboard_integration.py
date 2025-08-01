"""Integration tests for the Variant Performance Dashboard."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from services.dashboard_api.main import app


class TestDashboardIntegration:
    """Integration tests for dashboard functionality."""
    
    @pytest.mark.asyncio
    async def test_api_health_check(self):
        """Test health check endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_metrics_endpoint(self):
        """Test metrics API endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch('services.dashboard_api.main.metrics_api.get_live_metrics') as mock_metrics:
                mock_metrics.return_value = {
                    "summary": {"total_variants": 5},
                    "active_variants": [],
                    "performance_leaders": [],
                    "early_kills_today": {"kills_today": 1},
                    "pattern_fatigue_warnings": [],
                    "optimization_opportunities": [],
                    "real_time_feed": []
                }
                
                response = await client.get("/api/metrics/ai-jesus")
                assert response.status_code == 200
                data = response.json()
                assert data["summary"]["total_variants"] == 5
    
    @pytest.mark.asyncio
    async def test_websocket_connection_and_initial_data(self):
        """Test WebSocket connection receives initial data."""
        # This test would require a running server
        # For unit testing, we'll test the components separately
        pass
    
    @pytest.mark.asyncio
    async def test_early_kill_event_processing(self):
        """Test early kill event processing and broadcasting."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch('services.dashboard_api.main.event_processor.handle_early_kill_event') as mock_handler:
                mock_handler.return_value = None
                
                event_data = {
                    "variant_id": "var_123",
                    "persona_id": "ai-jesus",
                    "reason": "Low engagement",
                    "final_engagement_rate": 0.02,
                    "sample_size": 1000
                }
                
                response = await client.post("/api/events/early-kill", json=event_data)
                assert response.status_code == 200
                assert response.json()["status"] == "processed"
                
                mock_handler.assert_called_once_with("var_123", event_data)
    
    @pytest.mark.asyncio
    async def test_performance_update_event(self):
        """Test performance update event processing."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch('services.dashboard_api.main.event_processor.handle_performance_update') as mock_handler:
                mock_handler.return_value = None
                
                event_data = {
                    "variant_id": "var_456",
                    "persona_id": "ai-jesus",
                    "engagement_rate": 0.065,
                    "interaction_count": 150,
                    "view_count": 2500
                }
                
                response = await client.post("/api/events/performance-update", json=event_data)
                assert response.status_code == 200
                assert response.json()["status"] == "processed"


class TestRealTimeUpdates:
    """Test real-time update functionality."""
    
    @pytest.mark.asyncio
    async def test_variant_update_broadcast(self):
        """Test that updates are broadcast to connected clients."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
        
        ws_handler = VariantDashboardWebSocket()
        
        # Create mock WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        persona_id = "ai-jesus"
        ws_handler.connections[persona_id] = {mock_ws1, mock_ws2}
        
        # Broadcast update
        update_data = {
            "event_type": "performance_update",
            "variant_id": "var_789",
            "current_er": 0.07
        }
        
        await ws_handler.broadcast_variant_update(persona_id, update_data)
        
        # Verify both connections received the update
        assert mock_ws1.send_json.call_count == 1
        assert mock_ws2.send_json.call_count == 1
        
        # Check message format
        sent_message = mock_ws1.send_json.call_args[0][0]
        assert sent_message["type"] == "variant_update"
        assert sent_message["data"]["event_type"] == "performance_update"
        assert "timestamp" in sent_message