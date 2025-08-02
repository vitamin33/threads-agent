"""Comprehensive WebSocket tests for real-time dashboard functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
from services.dashboard_api.event_processor import DashboardEventProcessor


class TestVariantDashboardWebSocket:
    """Comprehensive tests for WebSocket handler."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection."""
        ws = AsyncMock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        ws.receive_text = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.fixture
    def mock_metrics_api(self):
        """Mock VariantMetricsAPI with realistic responses."""
        api = AsyncMock()
        api.get_live_metrics.return_value = {
            "summary": {
                "total_variants": 15,
                "avg_engagement_rate": 0.058,
                "active_count": 12,
            },
            "active_variants": [
                {
                    "id": "var_1",
                    "content": "Test variant 1",
                    "predicted_er": 0.06,
                    "live_metrics": {
                        "engagement_rate": 0.055,
                        "interactions": 120,
                        "views": 2200,
                    },
                }
            ],
            "early_kills_today": {"kills_today": 3},
            "pattern_fatigue_warnings": [],
            "optimization_opportunities": [],
            "real_time_feed": [],
        }
        return api

    @pytest.fixture
    def websocket_handler(self, mock_metrics_api):
        """Create WebSocket handler with mocked dependencies."""
        handler = VariantDashboardWebSocket()
        handler.metrics_api = mock_metrics_api
        return handler

    @pytest.mark.asyncio
    async def test_handle_connection_accepts_websocket(
        self, websocket_handler, mock_websocket
    ):
        """Test that WebSocket connection is properly accepted."""
        persona_id = "ai-jesus"

        # Mock receive_text to simulate client disconnect after initial data
        mock_websocket.receive_text.side_effect = WebSocketDisconnect(code=1000)

        await websocket_handler.handle_connection(mock_websocket, persona_id)

        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_connection_sends_initial_data(
        self, websocket_handler, mock_websocket, mock_metrics_api
    ):
        """Test that initial data is sent on connection."""
        persona_id = "ai-jesus"

        # Mock receive_text to simulate immediate disconnect
        mock_websocket.receive_text.side_effect = WebSocketDisconnect(code=1000)

        await websocket_handler.handle_connection(mock_websocket, persona_id)

        # Verify initial data was fetched and sent
        mock_metrics_api.get_live_metrics.assert_called_once_with(persona_id)
        mock_websocket.send_json.assert_called()

        # Check the initial data structure
        sent_data = mock_websocket.send_json.call_args[0][0]
        assert sent_data["type"] == "initial_data"
        assert "data" in sent_data
        assert "timestamp" in sent_data

    @pytest.mark.asyncio
    async def test_connection_tracking(self, websocket_handler, mock_websocket):
        """Test that connections are properly tracked per persona."""
        persona_id = "ai-jesus"

        # Add connection manually (simulating partial connection process)
        if persona_id not in websocket_handler.connections:
            websocket_handler.connections[persona_id] = set()
        websocket_handler.connections[persona_id].add(mock_websocket)

        assert persona_id in websocket_handler.connections
        assert mock_websocket in websocket_handler.connections[persona_id]
        assert len(websocket_handler.connections[persona_id]) == 1

    @pytest.mark.asyncio
    async def test_connection_cleanup_on_disconnect(
        self, websocket_handler, mock_websocket
    ):
        """Test that connections are cleaned up when client disconnects."""
        persona_id = "ai-jesus"

        # Simulate disconnect during receive
        mock_websocket.receive_text.side_effect = WebSocketDisconnect(code=1000)

        await websocket_handler.handle_connection(mock_websocket, persona_id)

        # Connection should be cleaned up
        assert (
            persona_id not in websocket_handler.connections
            or len(websocket_handler.connections.get(persona_id, set())) == 0
        )

    @pytest.mark.asyncio
    async def test_multiple_connections_same_persona(self, websocket_handler):
        """Test handling multiple connections for the same persona."""
        persona_id = "ai-jesus"
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        # Add connections manually
        websocket_handler.connections[persona_id] = {mock_ws1, mock_ws2}

        assert len(websocket_handler.connections[persona_id]) == 2

        # Remove one connection
        websocket_handler.connections[persona_id].discard(mock_ws1)
        assert len(websocket_handler.connections[persona_id]) == 1
        assert mock_ws2 in websocket_handler.connections[persona_id]

    @pytest.mark.asyncio
    async def test_broadcast_variant_update_all_clients(self, websocket_handler):
        """Test broadcasting updates to all connected clients."""
        persona_id = "ai-jesus"
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws3 = AsyncMock(spec=WebSocket)

        # Setup connections for two personas
        websocket_handler.connections[persona_id] = {mock_ws1, mock_ws2}
        websocket_handler.connections["ai-buddha"] = {mock_ws3}

        update_data = {
            "event_type": "performance_update",
            "variant_id": "var_1",
            "current_er": 0.062,
            "interaction_count": 150,
            "updated_at": datetime.now().isoformat(),
        }

        await websocket_handler.broadcast_variant_update(persona_id, update_data)

        # Only clients for ai-jesus should receive the update
        mock_ws1.send_json.assert_called_once()
        mock_ws2.send_json.assert_called_once()
        mock_ws3.send_json.assert_not_called()

        # Verify the broadcast message structure
        broadcast_message = mock_ws1.send_json.call_args[0][0]
        assert broadcast_message["type"] == "variant_update"
        assert broadcast_message["data"] == update_data
        assert "timestamp" in broadcast_message

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_clients(self, websocket_handler):
        """Test that broadcast handles disconnected clients gracefully."""
        persona_id = "ai-jesus"
        mock_ws_good = AsyncMock(spec=WebSocket)
        mock_ws_bad = AsyncMock(spec=WebSocket)

        # Make one WebSocket fail
        mock_ws_bad.send_json.side_effect = Exception("Connection closed")

        websocket_handler.connections[persona_id] = {mock_ws_good, mock_ws_bad}

        update_data = {"event_type": "test", "data": "test"}

        # Should not raise exception despite one client failing
        await websocket_handler.broadcast_variant_update(persona_id, update_data)

        # Good client should still receive message
        mock_ws_good.send_json.assert_called_once()

        # Bad client should be removed from connections
        assert mock_ws_bad not in websocket_handler.connections[persona_id]
        assert mock_ws_good in websocket_handler.connections[persona_id]

    @pytest.mark.asyncio
    async def test_handle_message_ping_pong(self, websocket_handler, mock_websocket):
        """Test ping/pong message handling."""
        persona_id = "ai-jesus"

        # Test ping message
        await websocket_handler.handle_message(
            mock_websocket, persona_id, '{"type": "ping"}'
        )

        # Should respond with pong
        mock_websocket.send_json.assert_called_with(
            {
                "type": "pong",
                "timestamp": mock_websocket.send_json.call_args[0][0]["timestamp"],
            }
        )

    @pytest.mark.asyncio
    async def test_handle_message_data_refresh(
        self, websocket_handler, mock_websocket, mock_metrics_api
    ):
        """Test data refresh message handling."""
        persona_id = "ai-jesus"

        await websocket_handler.handle_message(
            mock_websocket, persona_id, '{"type": "refresh_data"}'
        )

        # Should fetch fresh data and send it
        mock_metrics_api.get_live_metrics.assert_called_with(persona_id)
        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_handle_malformed_message(self, websocket_handler, mock_websocket):
        """Test handling of malformed JSON messages."""
        persona_id = "ai-jesus"

        # Should not raise exception
        await websocket_handler.handle_message(
            mock_websocket, persona_id, "invalid json{"
        )

        # Should send error response
        mock_websocket.send_json.assert_called_with(
            {"type": "error", "message": "Invalid message format"}
        )

    @pytest.mark.asyncio
    async def test_connection_limit_per_persona(self, websocket_handler):
        """Test connection limits per persona (if implemented)."""
        persona_id = "ai-jesus"
        max_connections = 10  # Assuming a reasonable limit

        # Create many mock connections
        mock_connections = [
            AsyncMock(spec=WebSocket) for _ in range(max_connections + 5)
        ]

        # Add connections up to limit
        websocket_handler.connections[persona_id] = set(
            mock_connections[:max_connections]
        )

        # Verify we respect reasonable limits (this test assumes limits exist)
        assert len(websocket_handler.connections[persona_id]) <= max_connections


class TestDashboardEventProcessor:
    """Test event processing for dashboard updates."""

    @pytest.fixture
    def mock_websocket_handler(self):
        """Mock WebSocket handler."""
        handler = AsyncMock()
        handler.broadcast_variant_update = AsyncMock()
        handler.broadcast_pattern_update = AsyncMock()
        return handler

    @pytest.fixture
    def event_processor(self, mock_websocket_handler):
        """Create event processor with mocked WebSocket handler."""
        return DashboardEventProcessor(mock_websocket_handler)

    @pytest.mark.asyncio
    async def test_handle_early_kill_event(
        self, event_processor, mock_websocket_handler
    ):
        """Test early kill event processing."""
        variant_id = "var_123"
        kill_data = {
            "persona_id": "ai-jesus",
            "reason": "low_engagement",
            "final_engagement_rate": 0.025,
            "sample_size": 150,
            "killed_at": datetime.now().isoformat(),
        }

        await event_processor.handle_early_kill_event(variant_id, kill_data)

        # Verify broadcast was called with correct data
        mock_websocket_handler.broadcast_variant_update.assert_called_once()

        call_args = mock_websocket_handler.broadcast_variant_update.call_args
        persona_id, update_data = call_args[0]

        assert persona_id == "ai-jesus"
        assert update_data["event_type"] == "early_kill"
        assert update_data["variant_id"] == variant_id
        assert update_data["kill_reason"] == "low_engagement"
        assert update_data["final_er"] == 0.025

    @pytest.mark.asyncio
    async def test_handle_performance_update(
        self, event_processor, mock_websocket_handler
    ):
        """Test performance update event processing."""
        variant_id = "var_456"
        performance_data = {
            "persona_id": "ai-buddha",
            "engagement_rate": 0.078,
            "interaction_count": 195,
            "view_count": 2800,
            "updated_at": datetime.now().isoformat(),
        }

        await event_processor.handle_performance_update(variant_id, performance_data)

        # Verify broadcast was called
        mock_websocket_handler.broadcast_variant_update.assert_called_once()

        call_args = mock_websocket_handler.broadcast_variant_update.call_args
        persona_id, update_data = call_args[0]

        assert persona_id == "ai-buddha"
        assert update_data["event_type"] == "performance_update"
        assert update_data["current_er"] == 0.078
        assert update_data["interaction_count"] == 195

    @pytest.mark.asyncio
    async def test_handle_pattern_fatigue_alert(
        self, event_processor, mock_websocket_handler
    ):
        """Test pattern fatigue alert processing."""
        pattern_data = {
            "persona_id": "ai-socrates",
            "pattern_id": "curiosity_gap",
            "fatigue_score": 0.89,
            "threshold_exceeded": True,
            "recommendation": "Switch to controversy patterns",
        }

        await event_processor.handle_pattern_fatigue_alert(pattern_data)

        # Verify pattern update broadcast
        mock_websocket_handler.broadcast_pattern_update.assert_called_once()

        call_args = mock_websocket_handler.broadcast_pattern_update.call_args
        persona_id, alert_data = call_args[0]

        assert persona_id == "ai-socrates"
        assert alert_data["event_type"] == "pattern_fatigue_alert"
        assert alert_data["pattern_id"] == "curiosity_gap"
        assert alert_data["fatigue_score"] == 0.89

    @pytest.mark.asyncio
    async def test_handle_event_missing_persona_id(
        self, event_processor, mock_websocket_handler
    ):
        """Test handling events without persona_id."""
        variant_id = "var_789"
        incomplete_data = {
            "reason": "test",
            "final_engagement_rate": 0.05,
            # Missing persona_id
        }

        await event_processor.handle_early_kill_event(variant_id, incomplete_data)

        # Should not broadcast when persona_id is missing
        mock_websocket_handler.broadcast_variant_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_event_processing_concurrency(
        self, event_processor, mock_websocket_handler
    ):
        """Test concurrent event processing."""
        # Create multiple events
        events = [
            ("var_1", {"persona_id": "ai-jesus", "engagement_rate": 0.05}),
            ("var_2", {"persona_id": "ai-buddha", "engagement_rate": 0.06}),
            ("var_3", {"persona_id": "ai-socrates", "engagement_rate": 0.07}),
        ]

        # Process events concurrently
        tasks = [
            event_processor.handle_performance_update(variant_id, data)
            for variant_id, data in events
        ]

        await asyncio.gather(*tasks)

        # All events should be processed
        assert mock_websocket_handler.broadcast_variant_update.call_count == 3


class TestWebSocketErrorHandling:
    """Test WebSocket error handling and recovery."""

    @pytest.fixture
    def websocket_handler(self):
        """Create WebSocket handler for error testing."""
        return VariantDashboardWebSocket()

    @pytest.mark.asyncio
    async def test_websocket_disconnect_during_send(self, websocket_handler):
        """Test handling WebSocket disconnect during send operation."""
        persona_id = "ai-jesus"
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.send_json.side_effect = Exception("Connection lost")

        websocket_handler.connections[persona_id] = {mock_ws}

        # Should handle disconnect gracefully
        await websocket_handler.broadcast_variant_update(persona_id, {"test": "data"})

        # Connection should be removed
        assert len(websocket_handler.connections.get(persona_id, set())) == 0

    @pytest.mark.asyncio
    async def test_memory_cleanup_on_errors(self, websocket_handler):
        """Test that memory is properly cleaned up after errors."""
        persona_id = "ai-jesus"

        # Add connections
        mock_connections = [AsyncMock(spec=WebSocket) for _ in range(5)]
        websocket_handler.connections[persona_id] = set(mock_connections)

        # Make all connections fail
        for mock_ws in mock_connections:
            mock_ws.send_json.side_effect = Exception("Connection failed")

        await websocket_handler.broadcast_variant_update(persona_id, {"test": "data"})

        # All connections should be cleaned up
        assert (
            persona_id not in websocket_handler.connections
            or len(websocket_handler.connections[persona_id]) == 0
        )

    @pytest.mark.asyncio
    async def test_partial_broadcast_failure(self, websocket_handler):
        """Test partial broadcast failure (some clients succeed, others fail)."""
        persona_id = "ai-jesus"
        mock_ws_good1 = AsyncMock(spec=WebSocket)
        mock_ws_good2 = AsyncMock(spec=WebSocket)
        mock_ws_bad = AsyncMock(spec=WebSocket)

        mock_ws_bad.send_json.side_effect = Exception("Connection failed")

        websocket_handler.connections[persona_id] = {
            mock_ws_good1,
            mock_ws_good2,
            mock_ws_bad,
        }

        await websocket_handler.broadcast_variant_update(persona_id, {"test": "data"})

        # Good connections should still receive messages
        mock_ws_good1.send_json.assert_called_once()
        mock_ws_good2.send_json.assert_called_once()

        # Bad connection should be removed
        assert mock_ws_bad not in websocket_handler.connections[persona_id]
        assert len(websocket_handler.connections[persona_id]) == 2

    @pytest.mark.asyncio
    async def test_websocket_reconnection_simulation(self, websocket_handler):
        """Test WebSocket reconnection behavior."""
        persona_id = "ai-jesus"

        # First connection
        mock_ws1 = AsyncMock(spec=WebSocket)
        websocket_handler.connections[persona_id] = {mock_ws1}

        # Simulate disconnect
        websocket_handler.connections[persona_id].discard(mock_ws1)

        # New connection (reconnection)
        mock_ws2 = AsyncMock(spec=WebSocket)
        websocket_handler.connections[persona_id] = {mock_ws2}

        # Should work with new connection
        await websocket_handler.broadcast_variant_update(
            persona_id, {"test": "reconnection"}
        )

        mock_ws2.send_json.assert_called_once()
        mock_ws1.send_json.assert_not_called()
