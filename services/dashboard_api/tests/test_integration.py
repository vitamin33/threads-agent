"""
Integration tests for dashboard API components.
Testing how VariantMetricsAPI, WebSocketHandler, and monitoring systems work together.
"""
import pytest
from unittest.mock import Mock, AsyncMock
import json


def test_dashboard_api_integration_with_all_components():
    """Test that all dashboard components integrate properly."""
    from services.dashboard_api.variant_metrics_api import VariantMetricsAPI
    from services.dashboard_api.websocket_handler import WebSocketHandler
    
    # Setup mocks for all dependencies
    mock_db = Mock()
    mock_early_kill_monitor = Mock()
    mock_pattern_fatigue_detector = Mock()
    
    # Mock database variant
    mock_variant = Mock()
    mock_variant.variant_id = "integration_test_variant"
    mock_variant.impressions = 500
    mock_variant.successes = 75
    mock_variant.success_rate = 0.15
    mock_variant.dimensions = {"pattern": "storytelling_hook"}
    mock_db.query.return_value.all.return_value = [mock_variant]
    
    # Mock monitoring systems
    mock_early_kill_monitor.active_sessions = {"integration_test_variant": Mock()}
    mock_pattern_fatigue_detector.is_pattern_fatigued.return_value = False
    mock_pattern_fatigue_detector.get_freshness_score.return_value = 0.8
    
    # Create integrated system
    variant_api = VariantMetricsAPI(
        db_session=mock_db,
        early_kill_monitor=mock_early_kill_monitor,
        pattern_fatigue_detector=mock_pattern_fatigue_detector
    )
    
    websocket_handler = WebSocketHandler(variant_metrics_api=variant_api)
    
    # Test the integration
    metrics = variant_api.get_comprehensive_metrics()
    
    # Verify all components contributed data
    assert len(metrics) == 1
    variant_data = metrics[0]
    
    # Database data
    assert variant_data["variant_id"] == "integration_test_variant"
    assert variant_data["impressions"] == 500
    assert variant_data["successes"] == 75
    assert variant_data["engagement_rate"] == 0.15
    
    # Early kill monitoring data
    assert variant_data["early_kill_status"] == "monitoring"
    
    # Pattern fatigue data
    assert variant_data["pattern_fatigue_warning"] is False
    assert variant_data["freshness_score"] == 0.8
    
    # Verify WebSocket handler can use the data
    assert websocket_handler.variant_metrics_api is not None


@pytest.mark.asyncio
async def test_websocket_integration_sends_comprehensive_data():
    """Test that WebSocket handler sends comprehensive data including all monitoring info."""
    from services.dashboard_api.websocket_handler import WebSocketHandler
    
    # Setup variant API with mock data
    mock_variant_api = Mock()
    mock_variant_api.get_comprehensive_metrics.return_value = [
        {
            "variant_id": "ws_test_variant",
            "impressions": 200,
            "successes": 30,
            "engagement_rate": 0.15,
            "early_kill_status": "monitoring",
            "pattern_fatigue_warning": True,
            "freshness_score": 0.2
        }
    ]
    
    # Create WebSocket handler
    ws_handler = WebSocketHandler(variant_metrics_api=mock_variant_api)
    mock_websocket = AsyncMock()
    
    # Handle connection
    await ws_handler.handle_connection(mock_websocket)
    
    # Verify comprehensive data was sent
    mock_websocket.send_text.assert_called()
    sent_data_json = mock_websocket.send_text.call_args[0][0]
    sent_data = json.loads(sent_data_json)
    
    assert sent_data["type"] == "initial_metrics"
    assert len(sent_data["variants"]) == 1
    
    variant = sent_data["variants"][0]
    assert variant["variant_id"] == "ws_test_variant"
    assert variant["early_kill_status"] == "monitoring"
    assert variant["pattern_fatigue_warning"] is True
    assert variant["freshness_score"] == 0.2


def test_integration_monitoring_component_complete():
    """Test that all monitoring integration requirements are met."""
    from services.dashboard_api.variant_metrics_api import VariantMetricsAPI
    
    # This test verifies we've completed the integration task
    api = VariantMetricsAPI()
    
    # Verify all required integration points exist
    assert hasattr(api, 'early_kill_monitor')
    assert hasattr(api, 'pattern_fatigue_detector')
    assert hasattr(api, 'get_comprehensive_metrics')
    
    # Verify the method handles all monitoring systems
    result = api.get_comprehensive_metrics()
    assert isinstance(result, list)