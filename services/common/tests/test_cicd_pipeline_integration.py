"""
Integration test for complete CI/CD Pipeline components.

This demonstrates how all CRA-297 CI/CD Pipeline components work together:
1. PromptTestRunner - Tests prompt templates
2. PerformanceRegressionDetector - Detects performance issues
3. GradualRolloutManager - Manages gradual rollout (10% → 100%)
4. RollbackController - Handles automatic rollback on issues

Author: TDD Implementation for CRA-297
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from services.common.prompt_test_runner import (
    PromptTestRunner, TestCase, TestSuite, ValidationRule
)
from services.common.performance_regression_detector import (
    PerformanceRegressionDetector, PerformanceData, MetricType
)
from services.common.gradual_rollout_manager import (
    GradualRolloutManager, RolloutStage
)
from services.common.rollback_controller import (
    RollbackController, RollbackTrigger
)


class TestCICDPipelineIntegration:
    """Integration tests for complete CI/CD pipeline."""

    @pytest.fixture
    def pipeline_components(self):
        """Set up all pipeline components for integration testing."""
        # Mock external dependencies
        mock_prompt_model = Mock()
        mock_prompt_model.render.return_value = "Hello, World!"
        mock_prompt_model.name = "test_model"
        mock_prompt_model.version = "v1.0"
        
        mock_model_registry = Mock()
        mock_model_registry.rollback_to_model.return_value = Mock(success=True)
        
        # Create pipeline components
        test_runner = PromptTestRunner(mock_prompt_model)
        regression_detector = PerformanceRegressionDetector()
        rollout_manager = GradualRolloutManager(regression_detector)
        rollback_controller = RollbackController(regression_detector, mock_model_registry)
        
        return {
            'test_runner': test_runner,
            'regression_detector': regression_detector,
            'rollout_manager': rollout_manager,
            'rollback_controller': rollback_controller,
            'mock_model_registry': mock_model_registry,
            'mock_prompt_model': mock_prompt_model
        }

    def test_successful_cicd_pipeline_flow(self, pipeline_components):
        """
        Test complete successful CI/CD pipeline flow:
        1. Test new prompt template
        2. Start gradual rollout
        3. Monitor performance
        4. Complete rollout if healthy
        """
        components = pipeline_components
        test_runner = components['test_runner']
        rollout_manager = components['rollout_manager']
        rollback_controller = components['rollback_controller']
        
        # Step 1: Test prompt template
        test_suite = TestSuite(
            name="Pre-deployment Tests",
            test_cases=[
                TestCase(
                    name="basic_functionality",
                    input_data={"name": "World"},
                    expected_output="Hello, World!",
                    validation_rules=["exact_match"]
                )
            ]
        )
        test_runner.test_suite = test_suite
        
        test_results = test_runner.run_test_suite()
        assert len(test_results) == 1
        assert test_results[0].passed == True
        
        # Step 2: Start gradual rollout
        rollout_result = rollout_manager.start_rollout("model_v2.0")
        assert rollout_result.success == True
        assert rollout_manager.current_stage == RolloutStage.CANARY_10
        
        # Step 3: Start monitoring for rollback
        monitor_result = rollback_controller.start_monitoring("model_v2.0", "model_v1.9")
        assert monitor_result.success == True
        
        # Step 4: Progress through rollout stages with healthy metrics
        # Generate healthy performance data
        historical_data = self._generate_performance_data(baseline_mean=0.85, count=20)
        current_data = self._generate_performance_data(baseline_mean=0.86, count=15)  # Slightly better
        
        # Advance through rollout stages
        for expected_stage in [RolloutStage.CANARY_25, RolloutStage.CANARY_50, RolloutStage.FULL_ROLLOUT]:
            # Check health before advancing
            health = rollback_controller.check_health(historical_data, current_data)
            assert health.is_healthy == True
            assert health.triggers_rollback == False
            
            # Check for automatic rollback triggers (should be None for healthy metrics)
            auto_rollback = rollback_controller.trigger_automatic_rollback_if_needed(
                historical_data, current_data
            )
            assert auto_rollback is None  # No rollback needed
            
            # Advance rollout stage
            advance_result = rollout_manager.advance_stage(historical_data, current_data)
            assert advance_result.success == True
            assert rollout_manager.current_stage == expected_stage
        
        # Verify final state
        assert rollout_manager.current_stage == RolloutStage.FULL_ROLLOUT
        assert rollout_manager.is_active == False  # Completed
        
        status = rollback_controller.get_rollback_status()
        assert status.rollback_count == 0  # No rollbacks occurred

    def test_cicd_pipeline_with_performance_regression_and_rollback(self, pipeline_components):
        """
        Test CI/CD pipeline with performance regression triggering rollback:
        1. Start rollout successfully
        2. Detect performance regression during canary
        3. Trigger automatic rollback
        4. Verify rollback execution
        """
        components = pipeline_components
        rollout_manager = components['rollout_manager']
        rollback_controller = components['rollback_controller']
        mock_registry = components['mock_model_registry']
        
        # Step 1: Start rollout and monitoring
        rollout_result = rollout_manager.start_rollout("model_v2.0")
        assert rollout_result.success == True
        
        monitor_result = rollback_controller.start_monitoring("model_v2.0", "model_v1.9")
        assert monitor_result.success == True
        
        # Step 2: Generate performance regression data
        historical_data = self._generate_performance_data(baseline_mean=0.85, count=20)
        # Simulating performance regression - significantly worse performance
        regression_data = self._generate_performance_data(baseline_mean=0.75, count=15)
        
        # Step 3: Try to advance rollout - should be blocked by regression
        advance_result = rollout_manager.advance_stage(historical_data, regression_data)
        assert advance_result.success == False
        assert "regression detected" in advance_result.error_message.lower()
        assert rollout_manager.current_stage == RolloutStage.CANARY_10  # Should not advance
        
        # Step 4: Check automatic rollback trigger
        auto_rollback = rollback_controller.trigger_automatic_rollback_if_needed(
            historical_data, regression_data
        )
        assert auto_rollback is not None
        assert auto_rollback.success == True
        assert auto_rollback.trigger == RollbackTrigger.PERFORMANCE_REGRESSION
        
        # Verify rollback was executed
        mock_registry.rollback_to_model.assert_called_once_with("model_v1.9")
        
        # Verify rollback history
        history = rollback_controller.get_rollback_history()
        assert len(history) == 1
        assert history[0].trigger == RollbackTrigger.PERFORMANCE_REGRESSION
        assert history[0].success == True

    def test_manual_rollback_during_rollout(self, pipeline_components):
        """
        Test manual rollback capability during rollout:
        1. Start normal rollout
        2. Trigger manual rollback for business reasons
        3. Verify rollback execution and history
        """
        components = pipeline_components
        rollout_manager = components['rollout_manager']
        rollback_controller = components['rollback_controller']
        mock_registry = components['mock_model_registry']
        
        # Start rollout and monitoring
        rollout_manager.start_rollout("model_v2.0")
        rollback_controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Advance to 25% stage
        historical_data = self._generate_performance_data(baseline_mean=0.85, count=20)
        current_data = self._generate_performance_data(baseline_mean=0.86, count=15)
        
        advance_result = rollout_manager.advance_stage(historical_data, current_data)
        assert advance_result.success == True
        assert rollout_manager.current_stage == RolloutStage.CANARY_25
        
        # Trigger manual rollback
        rollback_result = rollback_controller.execute_manual_rollback(
            "Business decision: rollback due to user feedback"
        )
        
        assert rollback_result.success == True
        assert rollback_result.trigger == RollbackTrigger.MANUAL
        assert rollback_result.reason == "Business decision: rollback due to user feedback"
        assert rollback_result.duration < 30.0  # Meets performance requirement
        
        # Verify rollback execution
        mock_registry.rollback_to_model.assert_called_once_with("model_v1.9")
        
        # Verify history tracking
        history = rollback_controller.get_rollback_history()
        assert len(history) == 1
        assert history[0].trigger == RollbackTrigger.MANUAL
        assert "user feedback" in history[0].reason

    def test_end_to_end_pipeline_performance_requirements(self, pipeline_components):
        """
        Test that the entire pipeline meets performance requirements:
        1. Test execution time
        2. Rollback time
        3. Health check latency
        """
        components = pipeline_components
        test_runner = components['test_runner']
        rollout_manager = components['rollout_manager']
        rollback_controller = components['rollback_controller']
        
        # Test suite execution performance
        test_suite = TestSuite(
            name="Performance Tests",
            test_cases=[
                TestCase(
                    name="performance_test",
                    input_data={"name": "Test"},
                    expected_output="Hello, Test!",
                    validation_rules=["max_execution_time:1.0"]  # 1 second max
                )
            ]
        )
        test_runner.test_suite = test_suite
        
        start_time = time.time()
        test_results = test_runner.run_test_suite()
        test_duration = time.time() - start_time
        
        assert test_results[0].passed == True
        assert test_duration < 5.0  # Should be very fast
        
        # Rollout performance
        rollout_manager.start_rollout("model_v2.0")
        rollback_controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Health check performance
        historical_data = self._generate_performance_data(baseline_mean=0.85, count=10)
        current_data = self._generate_performance_data(baseline_mean=0.86, count=10)
        
        start_time = time.time()
        health = rollback_controller.check_health(historical_data, current_data)
        health_check_duration = time.time() - start_time
        
        assert health.is_healthy == True
        assert health_check_duration < 2.0  # Health checks should be fast
        
        # Rollback performance (critical requirement: <30 seconds)
        start_time = time.time()
        rollback_result = rollback_controller.execute_manual_rollback("Performance test")
        rollback_duration = time.time() - start_time
        
        assert rollback_result.success == True
        assert rollback_duration < 30.0  # Meets requirement
        assert rollback_result.duration < 30.0

    def test_pipeline_error_handling_and_recovery(self, pipeline_components):
        """
        Test error handling and recovery throughout the pipeline:
        1. Handle test failures gracefully
        2. Handle regression detector errors
        3. Handle rollback failures
        """
        components = pipeline_components
        test_runner = components['test_runner']
        rollback_controller = components['rollback_controller']
        mock_registry = components['mock_model_registry']
        mock_model = components['mock_prompt_model']
        
        # Test error handling in test runner
        mock_model.render.side_effect = Exception("Template rendering failed")
        
        test_suite = TestSuite(
            name="Error Handling Tests",
            test_cases=[
                TestCase(
                    name="error_test",
                    input_data={"name": "Test"},
                    expected_output="Hello, Test!",
                    validation_rules=["exact_match"]
                )
            ]
        )
        test_runner.test_suite = test_suite
        
        test_results = test_runner.run_test_suite()
        assert len(test_results) == 1
        assert test_results[0].passed == False
        assert "failed" in test_results[0].error.lower()
        
        # Test rollback failure handling
        mock_registry.rollback_to_model.side_effect = Exception("Registry connection failed")
        
        rollback_controller.start_monitoring("model_v2.0", "model_v1.9")
        rollback_result = rollback_controller.execute_manual_rollback("Test rollback failure")
        
        assert rollback_result.success == False
        assert "Registry connection failed" in rollback_result.error_message
        
        # Verify error was recorded in history
        history = rollback_controller.get_rollback_history()
        assert len(history) == 1
        assert history[0].success == False
        assert "Registry connection failed" in history[0].error_message

    def _generate_performance_data(self, baseline_mean: float, count: int, 
                                 std_dev: float = 0.05) -> list:
        """Generate synthetic performance data for testing."""
        import random
        import numpy as np
        
        np.random.seed(42)  # For reproducible tests
        values = np.random.normal(baseline_mean, std_dev, count)
        
        return [
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=i),
                metric_name="deployment_health",  # Match what RollbackController expects
                value=float(val),
                metadata={"test_data": True}
            )
            for i, val in enumerate(values)
        ]


if __name__ == "__main__":
    pytest.main([__file__])