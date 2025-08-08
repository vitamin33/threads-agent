"""
Test cases for Chaos Engineering Experiment Executor.

This module tests the basic functionality of chaos experiment execution,
focusing on safety controls and proper experiment lifecycle management.
"""

import pytest
from unittest.mock import Mock, AsyncMock
import asyncio

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from chaos_experiment_executor import (
    ChaosExperimentExecutor,
    ExperimentResult,
    ExperimentState,
)


class TestChaosExperimentExecutor:
    """Test cases for the main chaos experiment executor."""

    @pytest.fixture
    def mock_prometheus_client(self):
        """Mock Prometheus client for metrics collection."""
        return Mock()

    @pytest.fixture
    def mock_circuit_breaker(self):
        """Mock circuit breaker for safety controls."""
        breaker = Mock()
        breaker.is_open = False
        breaker.call = AsyncMock()
        return breaker

    @pytest.fixture
    def executor(self, mock_prometheus_client, mock_circuit_breaker):
        """Create a chaos experiment executor with mocked dependencies."""
        return ChaosExperimentExecutor(
            prometheus_client=mock_prometheus_client,
            circuit_breaker=mock_circuit_breaker,
            safety_threshold=0.8,  # 80% success rate threshold
        )

    def test_chaos_experiment_executor_initialization(self, executor):
        """Test that chaos experiment executor initializes correctly."""
        assert executor is not None
        assert hasattr(executor, "execute_experiment")
        assert hasattr(executor, "safety_threshold")
        assert executor.safety_threshold == 0.8

    @pytest.mark.asyncio
    async def test_execute_pod_kill_experiment_returns_success_result(self, executor):
        """
        Test that executing a pod kill experiment returns a successful result.

        This test should FAIL initially because the experiment executor doesn't exist yet.
        """
        # Arrange
        experiment_config = {
            "name": "kill-orchestrator-pod",
            "type": "pod_kill",
            "target": {"namespace": "default", "app_label": "orchestrator"},
            "duration": 30,
            "rollback_timeout": 60,
        }

        # Act
        result = await executor.execute_experiment(experiment_config)

        # Assert
        assert result.status == ExperimentState.COMPLETED
        assert result.experiment_name == "kill-orchestrator-pod"
        assert result.execution_time > 0
        assert result.safety_checks_passed is True
        assert "pod_kill" in result.actions_performed

    @pytest.mark.asyncio
    async def test_execute_experiment_with_safety_violation_returns_failed_result(
        self, executor
    ):
        """Test that experiment execution returns failed result when safety thresholds are violated."""
        # Arrange
        experiment_config = {
            "name": "unsafe-experiment",
            "type": "network_partition",
            "target": {"namespace": "default"},
            "duration": 60,
        }

        # Mock safety check failure
        executor._check_system_health = AsyncMock(return_value=0.5)  # Below threshold

        # Act
        result = await executor.execute_experiment(experiment_config)

        # Assert
        assert result.status == ExperimentState.FAILED
        assert result.safety_checks_passed is False
        assert "Safety threshold violation" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_experiment_updates_prometheus_metrics(
        self, executor, mock_prometheus_client
    ):
        """Test that executing an experiment updates Prometheus metrics correctly."""
        # Arrange
        experiment_config = {
            "name": "test-metrics-experiment",
            "type": "cpu_stress",
            "target": {"namespace": "default", "app_label": "celery-worker"},
            "duration": 15,
        }

        # Act
        result = await executor.execute_experiment(experiment_config)

        # Assert
        assert mock_prometheus_client.inc.called
        assert mock_prometheus_client.observe.called

        # Check that the correct metrics were called
        metric_calls = [
            call[0][0] for call in mock_prometheus_client.inc.call_args_list
        ]
        assert "chaos_experiments_total" in metric_calls
        assert "chaos_experiments_success_total" in metric_calls

    @pytest.mark.asyncio
    async def test_emergency_stop_during_experiment_execution(self, executor):
        """Test that emergency stop functionality works during experiment execution."""
        # Arrange
        experiment_config = {
            "name": "long-running-experiment",
            "type": "memory_pressure",
            "target": {"namespace": "default"},
            "duration": 300,  # 5 minutes
        }

        # Start experiment in background
        experiment_task = asyncio.create_task(
            executor.execute_experiment(experiment_config)
        )

        # Wait a bit then trigger emergency stop
        await asyncio.sleep(0.1)
        await executor.emergency_stop()

        # Wait for experiment to complete
        result = await experiment_task

        # Assert
        assert result.status == ExperimentState.EMERGENCY_STOPPED
        assert result.execution_time < 300  # Stopped early
        assert "emergency_stop" in result.actions_performed


class TestExperimentResult:
    """Test cases for the ExperimentResult data class."""

    def test_experiment_result_creation_with_required_fields(self):
        """Test that ExperimentResult can be created with required fields."""
        result = ExperimentResult(
            experiment_name="test-experiment",
            status=ExperimentState.COMPLETED,
            execution_time=45.2,
            safety_checks_passed=True,
            actions_performed=["pod_kill", "health_check"],
        )

        assert result.experiment_name == "test-experiment"
        assert result.status == ExperimentState.COMPLETED
        assert result.execution_time == 45.2
        assert result.safety_checks_passed is True
        assert len(result.actions_performed) == 2

    def test_experiment_result_to_dict_conversion(self):
        """Test that ExperimentResult can be converted to dictionary."""
        result = ExperimentResult(
            experiment_name="dict-test",
            status=ExperimentState.FAILED,
            execution_time=12.5,
            safety_checks_passed=False,
            actions_performed=["network_delay"],
            error_message="Connection timeout",
        )

        result_dict = result.to_dict()

        assert result_dict["experiment_name"] == "dict-test"
        assert result_dict["status"] == "FAILED"
        assert result_dict["execution_time"] == 12.5
        assert result_dict["safety_checks_passed"] is False
        assert result_dict["error_message"] == "Connection timeout"


class TestExperimentState:
    """Test cases for the ExperimentState enum."""

    def test_experiment_state_values(self):
        """Test that ExperimentState has all required values."""
        assert hasattr(ExperimentState, "PENDING")
        assert hasattr(ExperimentState, "RUNNING")
        assert hasattr(ExperimentState, "COMPLETED")
        assert hasattr(ExperimentState, "FAILED")
        assert hasattr(ExperimentState, "EMERGENCY_STOPPED")

        # Test enum values are strings for JSON serialization
        assert isinstance(ExperimentState.PENDING.value, str)
        assert isinstance(ExperimentState.RUNNING.value, str)
