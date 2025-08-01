"""Tests for VariantMetricsAPI - written first following TDD practices."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from services.dashboard_api.variant_metrics import VariantMetricsAPI


class TestVariantMetricsAPI:
    """Test suite for VariantMetricsAPI following TDD."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis connection."""
        redis = AsyncMock()
        return redis

    @pytest.fixture
    def mock_performance_monitor(self):
        """Mock PerformanceMonitor."""
        monitor = AsyncMock()
        return monitor

    @pytest.fixture
    def metrics_api(self, mock_db, mock_redis, mock_performance_monitor):
        """Create VariantMetricsAPI instance with mocks."""
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            with patch('services.dashboard_api.variant_metrics.get_redis_connection', return_value=mock_redis):
                with patch('services.dashboard_api.variant_metrics.PerformanceMonitor', return_value=mock_performance_monitor):
                    return VariantMetricsAPI()

    @pytest.mark.asyncio
    async def test_get_live_metrics_returns_complete_structure(self, metrics_api):
        """Test that get_live_metrics returns all required data fields."""
        persona_id = "ai-jesus"
        
        # Mock the individual method calls
        metrics_api.get_performance_summary = AsyncMock(return_value={"total_variants": 10})
        metrics_api.get_active_variants = AsyncMock(return_value=[])
        metrics_api.get_top_performers = AsyncMock(return_value=[])
        metrics_api.get_kill_statistics = AsyncMock(return_value={"kills_today": 2})
        metrics_api.get_fatigue_warnings = AsyncMock(return_value=[])
        metrics_api.get_optimization_suggestions = AsyncMock(return_value=[])
        metrics_api.get_recent_events = AsyncMock(return_value=[])
        
        result = await metrics_api.get_live_metrics(persona_id)
        
        assert "summary" in result
        assert "active_variants" in result
        assert "performance_leaders" in result
        assert "early_kills_today" in result
        assert "pattern_fatigue_warnings" in result
        assert "optimization_opportunities" in result
        assert "real_time_feed" in result

    @pytest.mark.asyncio
    async def test_get_active_variants_includes_live_performance(self, metrics_api, mock_db):
        """Test that active variants include real-time performance data."""
        persona_id = "ai-jesus"
        now = datetime.now()
        
        # Mock database response
        mock_variants = [
            {
                "id": "var_1",
                "content": "Test content for variant 1",
                "predicted_er": 0.06,
                "posted_at": now - timedelta(hours=1),
                "current_er": 0.055,
                "interaction_count": 100,
                "status": "active"
            }
        ]
        mock_db.fetch_all.return_value = mock_variants
        
        # Mock performance data
        metrics_api.get_variant_performance = AsyncMock(return_value={
            "engagement_rate": 0.055,
            "views": 2000,
            "interactions": 110
        })
        
        result = await metrics_api.get_active_variants(persona_id)
        
        assert len(result) == 1
        variant = result[0]
        assert variant["id"] == "var_1"
        assert "live_metrics" in variant
        assert "time_since_post" in variant
        assert "performance_vs_prediction" in variant

    @pytest.mark.asyncio
    async def test_get_optimization_suggestions_high_kill_rate(self, metrics_api):
        """Test optimization suggestions when kill rate is high."""
        persona_id = "ai-jesus"
        
        # Mock methods
        metrics_api.get_recent_variants = AsyncMock(return_value=[])
        metrics_api.calculate_early_kill_rate = AsyncMock(return_value=0.35)  # 35% kill rate
        
        suggestions = await metrics_api.get_optimization_suggestions(persona_id)
        
        # Should have suggestion about high kill rate
        kill_rate_suggestions = [s for s in suggestions if s["type"] == "prediction_calibration"]
        assert len(kill_rate_suggestions) == 1
        assert "High Early Kill Rate" in kill_rate_suggestions[0]["title"]

    @pytest.mark.asyncio
    async def test_calculate_performance_delta(self, metrics_api):
        """Test performance delta calculation."""
        actual_er = 0.055
        predicted_er = 0.06
        
        delta = metrics_api.calculate_performance_delta(actual_er, predicted_er)
        
        assert delta == pytest.approx(-0.083, rel=0.01)  # -8.3% relative to prediction

    @pytest.mark.asyncio
    async def test_get_kill_statistics(self, metrics_api, mock_db):
        """Test early kill statistics retrieval."""
        persona_id = "ai-jesus"
        
        mock_db.fetch_one.return_value = {
            "total_kills": 5,
            "avg_time_to_kill": 3.5
        }
        
        result = await metrics_api.get_kill_statistics(persona_id)
        
        assert result["kills_today"] == 5
        assert result["avg_time_to_kill_minutes"] == 3.5


class TestWebSocketIntegration:
    """Test WebSocket functionality for real-time updates."""

    @pytest.mark.asyncio
    async def test_websocket_sends_initial_data(self):
        """Test that WebSocket sends initial dashboard data on connection."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
        
        ws_handler = VariantDashboardWebSocket()
        mock_websocket = AsyncMock()
        
        # Mock metrics API
        with patch.object(ws_handler, 'metrics_api') as mock_metrics_api:
            mock_metrics_api.get_live_metrics = AsyncMock(return_value={
                "summary": {"total_variants": 10},
                "active_variants": []
            })
            
            # Simulate connection (partial execution)
            await ws_handler.send_initial_data(mock_websocket, "ai-jesus")
            
            # Verify initial data was sent
            mock_websocket.send_json.assert_called_once()
            sent_data = mock_websocket.send_json.call_args[0][0]
            assert sent_data["type"] == "initial_data"
            assert "data" in sent_data

    @pytest.mark.asyncio
    async def test_broadcast_variant_update(self):
        """Test broadcasting updates to connected clients."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
        
        ws_handler = VariantDashboardWebSocket()
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        # Add connections
        persona_id = "ai-jesus"
        ws_handler.connections[persona_id] = {mock_websocket1, mock_websocket2}
        
        # Broadcast update
        update_data = {
            "event_type": "performance_update",
            "variant_id": "var_1",
            "current_er": 0.055
        }
        
        await ws_handler.broadcast_variant_update(persona_id, update_data)
        
        # Both clients should receive update
        assert mock_websocket1.send_json.call_count == 1
        assert mock_websocket2.send_json.call_count == 1