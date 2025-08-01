"""
Tests for WebSocket handler for real-time dashboard updates.
Following TDD - write failing tests first.
"""
import pytest
from unittest.mock import Mock, AsyncMock
import json


def test_websocket_handler_exists():
    """Test that WebSocketHandler class exists."""
    # This will fail until we create the class
    from services.dashboard_api.websocket_handler import WebSocketHandler
    
    handler = WebSocketHandler()
    assert handler is not None


@pytest.mark.asyncio
async def test_websocket_handler_accepts_connections():
    """Test that WebSocket handler can accept connections."""
    from services.dashboard_api.websocket_handler import WebSocketHandler
    
    handler = WebSocketHandler()
    mock_websocket = AsyncMock()
    
    # This should handle the connection without error
    await handler.handle_connection(mock_websocket)
    
    # Verify websocket.accept was called
    mock_websocket.accept.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_handler_sends_initial_metrics():
    """Test that handler sends initial variant metrics on connection."""
    from services.dashboard_api.websocket_handler import WebSocketHandler
    
    # Mock dependencies
    mock_variant_api = Mock()
    mock_variant_api.get_comprehensive_metrics.return_value = [
        {
            "variant_id": "test_1",
            "engagement_rate": 0.15,
            "impressions": 100,
            "early_kill_status": "monitoring"
        }
    ]
    
    handler = WebSocketHandler(variant_metrics_api=mock_variant_api)
    mock_websocket = AsyncMock()
    
    # Handle connection
    await handler.handle_connection(mock_websocket)
    
    # Verify initial metrics were sent
    mock_websocket.send_text.assert_called()
    
    # Get the sent data
    sent_calls = mock_websocket.send_text.call_args_list
    assert len(sent_calls) > 0
    
    # Parse the sent JSON
    sent_data = json.loads(sent_calls[0][0][0])
    assert sent_data["type"] == "initial_metrics"
    assert "variants" in sent_data
    assert len(sent_data["variants"]) == 1


@pytest.mark.asyncio
async def test_websocket_handler_broadcasts_updates():
    """Test that handler can broadcast updates to all connected clients."""
    from services.dashboard_api.websocket_handler import WebSocketHandler
    
    handler = WebSocketHandler()
    
    # Mock multiple websocket connections
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()
    
    # Simulate connections
    await handler.handle_connection(mock_ws1)
    await handler.handle_connection(mock_ws2)
    
    # Broadcast update
    update_data = {
        "type": "metrics_update",
        "variant_id": "test_1",
        "new_engagement_rate": 0.20
    }
    
    await handler.broadcast_update(update_data)
    
    # Verify both connections received the update
    mock_ws1.send_text.assert_called_with(json.dumps(update_data))
    mock_ws2.send_text.assert_called_with(json.dumps(update_data))


@pytest.mark.asyncio
async def test_websocket_handler_removes_disconnected_clients():
    """Test that handler properly handles client disconnections."""
    from services.dashboard_api.websocket_handler import WebSocketHandler
    
    handler = WebSocketHandler()
    mock_websocket = AsyncMock()
    
    # Simulate connection
    await handler.handle_connection(mock_websocket)
    
    # Simulate disconnection by raising exception on send
    mock_websocket.send_text.side_effect = Exception("Connection closed")
    
    # Try to broadcast - should handle the exception gracefully
    await handler.broadcast_update({"type": "test"})
    
    # Handler should have removed the disconnected client
    # Next broadcast should not attempt to send to the disconnected client
    mock_websocket.send_text.side_effect = None  # Reset
    await handler.broadcast_update({"type": "test2"})
    
    # Should only be called once (the failed attempt), not twice
    assert mock_websocket.send_text.call_count == 1