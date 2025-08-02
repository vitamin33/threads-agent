"""
Advanced tests for GradualRolloutManager - Regression checking and health monitoring.

This continues the TDD approach for CRA-297 CI/CD Pipeline implementation.
Tests the advanced features like regression-based rollout blocking.

Author: TDD Implementation for CRA-297
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from services.common.gradual_rollout_manager import (
    GradualRolloutManager,
    RolloutStage,
    RolloutStatus,
)


class TestRegressionBasedRolloutControl:
    """Test regression-based rollout control."""

    def test_advance_stage_with_regression_data_blocks_on_regression(self):
        """
        TEST: advance_stage should block progression when regression is detected.

        This tests the core safety mechanism of the gradual rollout system.
        """
        detector = Mock()
        # Mock regression detection
        detector.detect_regression.return_value = Mock(
            is_regression=True,
            is_significant_change=True,
            p_value=0.01,
            effect_size=-0.8,
        )

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        # Provide historical and current data to trigger health check
        historical_data = [Mock(timestamp=datetime.now() - timedelta(days=1))]
        current_data = [Mock(timestamp=datetime.now())]

        # Try to advance stage with regression data - should fail
        result = manager.advance_stage(historical_data, current_data)

        assert result.success == False
        assert "regression detected" in result.error_message.lower()
        assert manager.current_stage == RolloutStage.CANARY_10  # Should not advance
        assert result.health_metrics is not None
        assert "p_value" in result.health_metrics

    def test_advance_stage_with_healthy_data_continues_progression(self):
        """
        TEST: advance_stage should continue when metrics are healthy.
        """
        detector = Mock()
        # Mock healthy metrics
        detector.detect_regression.return_value = Mock(
            is_regression=False, is_significant_change=False, p_value=0.6
        )

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        # Provide historical and current data
        historical_data = [Mock(timestamp=datetime.now() - timedelta(days=1))]
        current_data = [Mock(timestamp=datetime.now())]

        # Should be able to advance with healthy metrics
        result = manager.advance_stage(historical_data, current_data)

        assert result.success == True
        assert manager.current_stage == RolloutStage.CANARY_25
        assert result.error_message is None

    def test_advance_stage_without_data_skips_health_check(self):
        """
        TEST: advance_stage should skip health check when no data is provided.

        This ensures backward compatibility and allows manual advancement.
        """
        detector = Mock()
        # Mock regression that would block if checked
        detector.detect_regression.return_value = Mock(
            is_regression=True, is_significant_change=True, p_value=0.01
        )

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        # Advance without providing data - should succeed (skip health check)
        result = manager.advance_stage()

        assert result.success == True
        assert manager.current_stage == RolloutStage.CANARY_25
        # Detector should not be called without data
        detector.detect_regression.assert_not_called()

    def test_health_monitoring_integration_with_performance_detector(self):
        """
        TEST: Health monitoring should properly integrate with PerformanceRegressionDetector.
        """
        detector = Mock()
        # Configure detailed regression result
        detector.detect_regression.return_value = Mock(
            is_regression=False,
            is_significant_change=False,
            p_value=0.7,
            effect_size=0.1,
            baseline_mean=0.85,
            current_mean=0.86,
        )

        manager = GradualRolloutManager(detector)

        historical_data = [Mock(value=0.85, metric_name="accuracy")]
        current_data = [Mock(value=0.86, metric_name="accuracy")]

        health = manager.monitor_deployment_health(historical_data, current_data)

        # Verify detector was called with correct parameters
        detector.detect_regression.assert_called_once_with(
            historical_data, current_data, metric_name="performance_metric"
        )

        # Verify health result
        assert health.is_healthy == True
        assert health.regression_detected == False
        assert "p_value" in health.metrics_summary
        assert health.metrics_summary["p_value"] == 0.7


class TestRolloutStatusAndReporting:
    """Test advanced status reporting features."""

    def test_get_rollout_status_provides_comprehensive_state(self):
        """
        TEST: get_rollout_status should provide comprehensive current state.
        """
        detector = Mock()
        manager = GradualRolloutManager(detector)

        start_time = datetime.now()
        with patch("services.common.gradual_rollout_manager.datetime") as mock_datetime:
            mock_datetime.now.return_value = start_time
            manager.start_rollout("model_v2.0")

        status = manager.get_rollout_status()

        assert isinstance(status, RolloutStatus)
        assert status.current_stage == RolloutStage.CANARY_10
        assert status.traffic_percentage == 10
        assert status.model_version == "model_v2.0"
        assert status.start_time == start_time
        assert status.is_active == True
        assert status.is_timed_out == False

    def test_rollout_timeout_detection(self):
        """
        TEST: Should detect rollout timeouts based on stage timeout.
        """
        detector = Mock()
        manager = GradualRolloutManager(detector, stage_timeout_minutes=1)

        # Start rollout
        with patch("services.common.gradual_rollout_manager.datetime") as mock_datetime:
            start_time = datetime.now()
            mock_datetime.now.return_value = start_time
            manager.start_rollout("model_v2.0")

            # Check status after timeout period
            timeout_time = start_time + timedelta(minutes=2)
            mock_datetime.now.return_value = timeout_time

            status = manager.get_rollout_status()
            assert status.is_timed_out == True

    def test_rollout_result_contains_comprehensive_information(self):
        """
        TEST: RolloutResult should contain all required attributes.
        """
        detector = Mock()
        manager = GradualRolloutManager(detector)

        result = manager.start_rollout("model_v2.0")

        # Verify all expected attributes exist
        required_attributes = [
            "success",
            "stage",
            "traffic_percentage",
            "error_message",
            "timestamp",
            "health_metrics",
            "duration",
        ]

        for attr in required_attributes:
            assert hasattr(result, attr), f"RolloutResult missing attribute: {attr}"

        # Verify content
        assert result.success == True
        assert result.stage == RolloutStage.CANARY_10
        assert result.traffic_percentage == 10
        assert result.error_message is None
        assert isinstance(result.timestamp, datetime)
        assert result.duration >= 0


class TestRolloutEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""

    def test_cannot_start_rollout_when_already_active(self):
        """
        TEST: Should prevent starting rollout when one is already active.
        """
        detector = Mock()
        manager = GradualRolloutManager(detector)

        # Start first rollout
        result1 = manager.start_rollout("model_v2.0")
        assert result1.success == True

        # Try to start second rollout - should fail
        result2 = manager.start_rollout("model_v2.1")
        assert result2.success == False
        assert "already active" in result2.error_message.lower()

    def test_cannot_advance_stage_without_active_rollout(self):
        """
        TEST: Should prevent advancing stage without active rollout.
        """
        detector = Mock()
        manager = GradualRolloutManager(detector)

        # Try to advance without starting rollout
        result = manager.advance_stage()

        assert result.success == False
        assert "no active rollout" in result.error_message.lower()

    def test_cannot_advance_beyond_full_rollout(self):
        """
        TEST: Should prevent advancing beyond the final stage.

        Note: Once FULL_ROLLOUT is reached, the rollout becomes inactive,
        so attempting to advance gives "no active rollout" error.
        """
        detector = Mock()
        manager = GradualRolloutManager(detector)

        # Start and advance to full rollout
        manager.start_rollout("model_v2.0")
        manager.advance_stage()  # 25%
        manager.advance_stage()  # 50%
        manager.advance_stage()  # 100% (should mark as inactive)

        # Try to advance beyond full rollout - should fail because rollout is now inactive
        result = manager.advance_stage()

        assert result.success == False
        assert "no active rollout" in result.error_message.lower()

    def test_rollout_becomes_inactive_after_full_rollout(self):
        """
        TEST: Rollout should become inactive after reaching full rollout.
        """
        detector = Mock()
        manager = GradualRolloutManager(detector)

        # Start and advance to full rollout
        manager.start_rollout("model_v2.0")
        assert manager.is_active == True

        manager.advance_stage()  # 25%
        assert manager.is_active == True

        manager.advance_stage()  # 50%
        assert manager.is_active == True

        result = manager.advance_stage()  # 100%
        assert result.success == True
        assert manager.current_stage == RolloutStage.FULL_ROLLOUT
        assert manager.is_active == False  # Should become inactive


if __name__ == "__main__":
    pytest.main([__file__])
