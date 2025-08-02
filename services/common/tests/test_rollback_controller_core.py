"""
Core tests for RollbackController - Essential functionality.

This focuses on the most critical RollbackController features for CRA-297.
Simplified test suite to verify core rollback functionality works.

Author: TDD Implementation for CRA-297
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from services.common.rollback_controller import (
    RollbackController,
    RollbackTrigger,
    RollbackError,
    RollbackStatus,
    RollbackResult,
    RollbackEvent,
    HealthCheck
)


class TestRollbackControllerCore:
    """Test core RollbackController functionality."""

    def test_initialization_and_basic_properties(self):
        """Test proper initialization with all required properties."""
        detector = Mock()
        registry = Mock()
        controller = RollbackController(detector, registry)
        
        assert controller.performance_detector == detector
        assert controller.model_registry == registry
        assert controller.is_monitoring == False
        assert controller.rollback_threshold_seconds == 30.0
        assert isinstance(controller.rollback_history, list)
        assert len(controller.rollback_history) == 0

    def test_start_and_stop_monitoring(self):
        """Test monitoring lifecycle."""
        detector = Mock()
        registry = Mock()
        controller = RollbackController(detector, registry)
        
        # Start monitoring
        result = controller.start_monitoring("model_v2.0", "model_v1.9")
        
        assert result.success == True
        assert controller.is_monitoring == True
        assert controller.current_model == "model_v2.0"
        assert controller.fallback_model == "model_v1.9"
        assert controller.monitoring_start_time is not None
        
        # Stop monitoring
        controller.stop_monitoring()
        assert controller.is_monitoring == False
        assert controller.current_model is None
        assert controller.fallback_model is None

    def test_health_check_with_regression_detection(self):
        """Test health checking with performance regression."""
        detector = Mock()
        registry = Mock()
        
        # Mock regression detection
        detector.detect_regression.return_value = Mock(
            is_regression=True,
            is_significant_change=True,
            p_value=0.01,
            effect_size=-0.8
        )
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        historical_data = [Mock(timestamp=datetime.now() - timedelta(days=1))]
        current_data = [Mock(timestamp=datetime.now())]
        
        health = controller.check_health(historical_data, current_data)
        
        assert isinstance(health, HealthCheck)
        assert health.is_healthy == False
        assert health.triggers_rollback == True
        assert RollbackTrigger.PERFORMANCE_REGRESSION in health.detected_issues
        assert health.has_sufficient_data == True
        assert controller.last_health_check is not None
        
        # Verify detector was called
        detector.detect_regression.assert_called_once()

    def test_manual_rollback_execution(self):
        """Test manual rollback with successful execution."""
        detector = Mock()
        registry = Mock()
        
        # Mock successful rollback in registry
        registry.rollback_to_model.return_value = Mock(success=True)
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        result = controller.execute_manual_rollback("Performance issues reported")
        
        assert result.success == True
        assert result.trigger == RollbackTrigger.MANUAL
        assert result.reason == "Performance issues reported"
        assert result.from_model == "model_v2.0"
        assert result.to_model == "model_v1.9"
        assert result.duration >= 0
        
        # Verify registry was called
        registry.rollback_to_model.assert_called_once_with("model_v1.9")
        
        # Verify history was recorded
        history = controller.get_rollback_history()
        assert len(history) == 1
        assert history[0].success == True
        assert history[0].trigger == RollbackTrigger.MANUAL

    def test_automatic_rollback_on_regression(self):
        """Test automatic rollback when regression is detected."""
        detector = Mock()
        registry = Mock()
        
        # Mock regression detection and successful rollback
        detector.detect_regression.return_value = Mock(
            is_regression=True,
            is_significant_change=True,
            p_value=0.01
        )
        registry.rollback_to_model.return_value = Mock(success=True)
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        historical_data = [Mock()]
        current_data = [Mock()]
        
        result = controller.trigger_automatic_rollback_if_needed(historical_data, current_data)
        
        assert result is not None
        assert result.success == True
        assert result.trigger == RollbackTrigger.PERFORMANCE_REGRESSION
        assert "Automatic rollback triggered" in result.reason
        
        # Verify both detector and registry were called
        detector.detect_regression.assert_called_once()
        registry.rollback_to_model.assert_called_once()

    def test_rollback_performance_requirement(self):
        """Test that rollback completes within performance requirement."""
        detector = Mock()
        registry = Mock()
        
        # Mock fast rollback
        registry.rollback_to_model.return_value = Mock(success=True)
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        start_time = time.time()
        result = controller.execute_manual_rollback("Performance test")
        end_time = time.time()
        
        actual_duration = end_time - start_time
        
        # Should complete quickly (well under 30 seconds)
        assert actual_duration < 5.0  # Should be very fast in tests
        assert result.duration < 30.0  # Meets requirement
        assert result.duration >= 0  # Sanity check

    def test_error_handling_on_registry_failure(self):
        """Test graceful error handling when registry fails."""
        detector = Mock()
        registry = Mock()
        
        # Mock registry failure
        registry.rollback_to_model.side_effect = Exception("Registry connection failed")
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        result = controller.execute_manual_rollback("Test rollback")
        
        assert result.success == False
        assert "Registry connection failed" in result.error_message
        assert result.trigger == RollbackTrigger.MANUAL
        
        # Verify error was recorded in history
        history = controller.get_rollback_history()
        assert len(history) == 1
        assert history[0].success == False
        assert "Registry connection failed" in history[0].error_message

    def test_status_reporting(self):
        """Test comprehensive status reporting."""
        detector = Mock()
        registry = Mock()
        controller = RollbackController(detector, registry)
        
        # Test status before monitoring
        status = controller.get_rollback_status()
        assert status.is_monitoring == False
        assert status.current_model is None
        assert status.rollback_count == 0
        
        # Start monitoring and test status
        controller.start_monitoring("model_v2.0", "model_v1.9")
        status = controller.get_rollback_status()
        
        assert status.is_monitoring == True
        assert status.current_model == "model_v2.0"
        assert status.fallback_model == "model_v1.9"
        assert status.monitoring_start_time is not None
        assert status.rollback_count == 0

    def test_no_rollback_without_monitoring(self):
        """Test that rollback is prevented when not monitoring."""
        detector = Mock()
        registry = Mock()
        controller = RollbackController(detector, registry)
        
        # Try manual rollback without monitoring
        result = controller.execute_manual_rollback("Test rollback")
        
        assert result.success == False
        assert "not monitoring" in result.error_message.lower()
        
        # Try automatic rollback without monitoring
        result = controller.trigger_automatic_rollback_if_needed([], [])
        assert result is None  # Should return None when not monitoring

    def test_health_check_handles_insufficient_data(self):
        """Test health check behavior with insufficient data."""
        detector = Mock()
        registry = Mock()
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Test with empty data
        health = controller.check_health([], [])
        
        assert health.is_healthy == False
        assert health.triggers_rollback == False  # Conservative - don't auto-rollback on data issues
        assert health.has_sufficient_data == False
        assert RollbackTrigger.HEALTH_CHECK_FAILURE in health.detected_issues
        
        # Verify detector was not called with insufficient data
        detector.detect_regression.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])