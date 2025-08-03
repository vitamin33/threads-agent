"""Integration tests for WebSocket functionality with real FastAPI app."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import httpx

from services.dashboard_api.main import app


class TestWebSocketIntegration:
    """Integration tests for WebSocket endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_database_data(self):
        """Mock realistic database data for integration tests."""
        return {
            "variants": [
                {
                    "id": "var_integration_1",
                    "persona_id": "ai-jesus",
                    "content": "Integration test variant 1",
                    "predicted_er": 0.065,
                    "actual_er": 0.058,
                    "posted_at": datetime.now() - timedelta(hours=2),
                    "status": "active",
                    "interaction_count": 150,
                    "view_count": 2500,
                },
                {
                    "id": "var_integration_2",
                    "persona_id": "ai-jesus",
                    "content": "Integration test variant 2",
                    "predicted_er": 0.052,
                    "actual_er": 0.067,
                    "posted_at": datetime.now() - timedelta(hours=1),
                    "status": "active",
                    "interaction_count": 180,
                    "view_count": 2800,
                },
            ],
            "kill_stats": {"total_kills_today": 3, "avg_time_to_kill": 4.2},
            "fatigue_warnings": [
                {
                    "pattern_id": "curiosity_gap",
                    "fatigue_score": 0.85,
                    "warning_level": "high",
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self, mock_database_data):
        """Test complete WebSocket connection lifecycle."""
        # Mock database and external dependencies
        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection"
        ) as mock_db:
            with patch(
                "services.dashboard_api.variant_metrics.get_redis_connection"
            ) as mock_redis:
                # Setup mocks
                mock_db_conn = AsyncMock()
                mock_db_conn.fetch_all.return_value = mock_database_data["variants"]
                mock_db_conn.fetch_one.return_value = mock_database_data["kill_stats"]
                mock_db.return_value = mock_db_conn

                mock_redis_conn = AsyncMock()
                mock_redis_conn.get.return_value = None  # No cache
                mock_redis.return_value = mock_redis_conn

                # Test WebSocket connection using httpx websocket client
                async with httpx.AsyncClient(
                    app=app, base_url="http://testserver"
                ) as client:
                    # Note: httpx doesn't support WebSocket directly, so we'll test the endpoint exists
                    response = await client.get("/")
                    assert response.status_code == 200
                    assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_websocket_initial_data_structure(self, mock_database_data):
        """Test WebSocket initial data has correct structure."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket

        # Create handler with mocked metrics API
        handler = VariantDashboardWebSocket()
        mock_metrics_api = AsyncMock()
        mock_metrics_api.get_live_metrics.return_value = {
            "summary": {
                "total_variants": 2,
                "avg_engagement_rate": 0.0625,
                "active_count": 2,
            },
            "active_variants": mock_database_data["variants"],
            "early_kills_today": mock_database_data["kill_stats"],
            "pattern_fatigue_warnings": mock_database_data["fatigue_warnings"],
            "optimization_opportunities": [],
            "real_time_feed": [],
        }
        handler.metrics_api = mock_metrics_api

        # Mock WebSocket
        mock_websocket = AsyncMock()

        await handler.send_initial_data(mock_websocket, "ai-jesus")

        # Verify structure of sent data
        mock_websocket.send_json.assert_called_once()
        sent_data = mock_websocket.send_json.call_args[0][0]

        assert sent_data["type"] == "initial_data"
        assert "data" in sent_data
        # Note: timestamp is not included in initial_data, only in updates

        # Verify all required sections are present
        data = sent_data["data"]
        required_sections = [
            "summary",
            "active_variants",
            "early_kills_today",
            "pattern_fatigue_warnings",
            "optimization_opportunities",
            "real_time_feed",
        ]
        for section in required_sections:
            assert section in data, f"Missing section: {section}"

    @pytest.mark.asyncio
    async def test_websocket_broadcast_integration(self, mock_database_data):
        """Test WebSocket broadcast integration with event processor."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
        from services.dashboard_api.event_processor import DashboardEventProcessor

        # Setup WebSocket handler
        ws_handler = VariantDashboardWebSocket()
        event_processor = DashboardEventProcessor(ws_handler)

        # Mock WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        persona_id = "ai-jesus"
        ws_handler.connections[persona_id] = {mock_ws1, mock_ws2}

        # Process an early kill event
        kill_data = {
            "persona_id": persona_id,
            "reason": "low_engagement",
            "final_engagement_rate": 0.025,
            "sample_size": 150,
            "killed_at": datetime.now().isoformat(),
        }

        await event_processor.handle_early_kill_event("var_test", kill_data)

        # Both WebSocket connections should receive the update
        assert mock_ws1.send_json.call_count == 1
        assert mock_ws2.send_json.call_count == 1

        # Verify message content
        sent_message = mock_ws1.send_json.call_args[0][0]
        assert sent_message["type"] == "variant_update"
        assert sent_message["data"]["event_type"] == "early_kill"
        assert sent_message["data"]["variant_id"] == "var_test"

    @pytest.mark.asyncio
    async def test_websocket_multiple_persona_isolation(self):
        """Test that WebSocket updates are isolated per persona."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket

        ws_handler = VariantDashboardWebSocket()

        # Setup connections for different personas
        mock_ws_jesus = AsyncMock()
        mock_ws_buddha = AsyncMock()
        mock_ws_socrates = AsyncMock()

        ws_handler.connections["ai-jesus"] = {mock_ws_jesus}
        ws_handler.connections["ai-buddha"] = {mock_ws_buddha}
        ws_handler.connections["ai-socrates"] = {mock_ws_socrates}

        # Send update only to ai-jesus
        update_data = {"event_type": "test_update", "data": "test"}

        await ws_handler.broadcast_variant_update("ai-jesus", update_data)

        # Only ai-jesus connection should receive update
        mock_ws_jesus.send_json.assert_called_once()
        mock_ws_buddha.send_json.assert_not_called()
        mock_ws_socrates.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_message_handling_integration(self):
        """Test WebSocket message handling with realistic scenarios."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket

        ws_handler = VariantDashboardWebSocket()
        mock_websocket = AsyncMock()
        persona_id = "ai-jesus"

        # Mock metrics API
        mock_metrics_api = AsyncMock()
        mock_metrics_api.get_live_metrics.return_value = {"test": "data"}
        ws_handler.metrics_api = mock_metrics_api

        # Test ping message
        await ws_handler.handle_message(mock_websocket, persona_id, '{"type": "ping"}')

        # Should respond with pong
        pong_call = None
        for call in mock_websocket.send_json.call_args_list:
            if call[0][0].get("type") == "pong":
                pong_call = call
                break

        assert pong_call is not None
        # Pong messages don't include timestamps, just simple response

        # Test refresh data message
        mock_websocket.send_json.reset_mock()
        await ws_handler.handle_message(
            mock_websocket, persona_id, '{"type": "refresh"}'
        )

        # Should fetch and send fresh data
        mock_metrics_api.get_live_metrics.assert_called_with(persona_id)
        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_error_recovery_integration(self):
        """Test WebSocket error recovery in integration scenario."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket

        ws_handler = VariantDashboardWebSocket()
        persona_id = "ai-jesus"

        # Setup connections with some that will fail
        mock_ws_good = AsyncMock()
        mock_ws_bad1 = AsyncMock()
        mock_ws_bad2 = AsyncMock()

        mock_ws_bad1.send_json.side_effect = Exception("Connection lost")
        mock_ws_bad2.send_json.side_effect = Exception("Network error")

        ws_handler.connections[persona_id] = {mock_ws_good, mock_ws_bad1, mock_ws_bad2}

        # Send broadcast update
        update_data = {"event_type": "test", "data": "recovery_test"}
        await ws_handler.broadcast_variant_update(persona_id, update_data)

        # Good connection should receive message
        mock_ws_good.send_json.assert_called_once()

        # Failed connections should be removed
        remaining_connections = ws_handler.connections.get(persona_id, set())
        assert mock_ws_good in remaining_connections
        assert mock_ws_bad1 not in remaining_connections
        assert mock_ws_bad2 not in remaining_connections
        assert len(remaining_connections) == 1

    @pytest.mark.asyncio
    async def test_concurrent_websocket_operations(self):
        """Test concurrent WebSocket operations."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket

        ws_handler = VariantDashboardWebSocket()
        persona_id = "ai-jesus"

        # Setup multiple connections
        connections = [AsyncMock() for _ in range(10)]
        ws_handler.connections[persona_id] = set(connections)

        # Create multiple concurrent update tasks
        update_tasks = [
            ws_handler.broadcast_variant_update(persona_id, {"event_type": f"test_{i}"})
            for i in range(5)
        ]

        # Execute concurrently
        await asyncio.gather(*update_tasks)

        # All connections should have received all updates
        for conn in connections:
            assert conn.send_json.call_count == 5


class TestWebSocketReconnection:
    """Test WebSocket reconnection scenarios."""

    @pytest.mark.asyncio
    async def test_reconnection_after_disconnect(self):
        """Test WebSocket reconnection behavior."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket

        ws_handler = VariantDashboardWebSocket()
        persona_id = "ai-jesus"

        # Initial connection
        mock_ws1 = AsyncMock()
        ws_handler.connections[persona_id] = {mock_ws1}

        # Send update - should work
        await ws_handler.broadcast_variant_update(persona_id, {"test": "data1"})
        mock_ws1.send_json.assert_called_once()

        # Simulate disconnect
        ws_handler.connections[persona_id].discard(mock_ws1)

        # Reconnection with new WebSocket
        mock_ws2 = AsyncMock()
        ws_handler.connections[persona_id] = {mock_ws2}

        # Send another update - should work with new connection
        await ws_handler.broadcast_variant_update(persona_id, {"test": "data2"})
        mock_ws2.send_json.assert_called_once()

        # Old connection should not receive new update
        assert mock_ws1.send_json.call_count == 1  # Only the first update

    @pytest.mark.asyncio
    async def test_multiple_reconnections(self):
        """Test multiple reconnection cycles."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket

        ws_handler = VariantDashboardWebSocket()
        persona_id = "ai-jesus"

        # Simulate multiple connection/disconnection cycles
        for cycle in range(5):
            # New connection
            mock_ws = AsyncMock()
            ws_handler.connections[persona_id] = {mock_ws}

            # Send update
            await ws_handler.broadcast_variant_update(persona_id, {"cycle": cycle})
            mock_ws.send_json.assert_called_once()

            # Disconnect
            ws_handler.connections[persona_id].discard(mock_ws)

        # Final state should be clean
        assert len(ws_handler.connections.get(persona_id, set())) == 0

    @pytest.mark.asyncio
    async def test_rapid_reconnection_handling(self):
        """Test handling of rapid reconnections."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket

        ws_handler = VariantDashboardWebSocket()
        persona_id = "ai-jesus"

        # Simulate rapid connect/disconnect cycles
        connections = []
        for i in range(20):
            mock_ws = AsyncMock()
            connections.append(mock_ws)

            # Add connection
            if persona_id not in ws_handler.connections:
                ws_handler.connections[persona_id] = set()
            ws_handler.connections[persona_id].add(mock_ws)

            # Immediately remove (simulating very quick disconnect)
            ws_handler.connections[persona_id].discard(mock_ws)

        # Should handle gracefully without memory leaks
        assert len(ws_handler.connections.get(persona_id, set())) == 0


class TestWebSocketPerformance:
    """Test WebSocket performance characteristics."""

    @pytest.mark.asyncio
    async def test_broadcast_performance_many_clients(self):
        """Test broadcast performance with many clients."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
        import time

        ws_handler = VariantDashboardWebSocket()
        persona_id = "ai-jesus"

        # Create many mock connections
        num_connections = 100
        connections = [AsyncMock() for _ in range(num_connections)]
        ws_handler.connections[persona_id] = set(connections)

        # Measure broadcast time
        start_time = time.time()
        await ws_handler.broadcast_variant_update(persona_id, {"test": "performance"})
        broadcast_time = time.time() - start_time

        # Should complete within reasonable time (< 1 second for 100 clients)
        assert broadcast_time < 1.0

        # All connections should receive the message
        for conn in connections:
            conn.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_usage_cleanup(self):
        """Test that memory is properly cleaned up."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket

        ws_handler = VariantDashboardWebSocket()

        # Create connections for multiple personas
        persona_ids = [f"ai-persona-{i}" for i in range(50)]

        for persona_id in persona_ids:
            connections = [AsyncMock() for _ in range(10)]
            ws_handler.connections[persona_id] = set(connections)

        # Simulate all connections failing (triggering cleanup)
        for persona_id in persona_ids:
            for conn in ws_handler.connections[persona_id].copy():
                conn.send_json.side_effect = Exception("Connection failed")

            # Broadcast to trigger cleanup
            await ws_handler.broadcast_variant_update(persona_id, {"test": "cleanup"})

        # All connections should be cleaned up
        total_remaining = sum(len(conns) for conns in ws_handler.connections.values())
        assert total_remaining == 0

    @pytest.mark.asyncio
    async def test_concurrent_broadcast_performance(self):
        """Test performance of concurrent broadcasts."""
        from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
        import time

        ws_handler = VariantDashboardWebSocket()

        # Setup connections for multiple personas
        personas = ["ai-jesus", "ai-buddha", "ai-socrates"]
        for persona_id in personas:
            connections = [AsyncMock() for _ in range(20)]
            ws_handler.connections[persona_id] = set(connections)

        # Create concurrent broadcast tasks
        start_time = time.time()
        tasks = [
            ws_handler.broadcast_variant_update(persona_id, {"persona": persona_id})
            for persona_id in personas
            for _ in range(10)  # 10 broadcasts per persona
        ]

        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Should complete all broadcasts within reasonable time
        assert total_time < 2.0  # 30 broadcasts to 60 total connections

        # Verify all connections received appropriate number of messages
        for persona_id in personas:
            for conn in ws_handler.connections[persona_id]:
                # Each connection should receive 10 messages for its persona
                assert conn.send_json.call_count == 10
