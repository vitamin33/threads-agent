"""
Test cases for Chaos Engineering CLI tools.

This module tests the command-line interface for managing chaos experiments.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, call
from click.testing import CliRunner
import json
import yaml
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from chaos_cli import (
    cli,
    run_experiment,
    list_experiments,
    get_experiment_status,
    stop_experiment,
    create_experiment_from_yaml
)


class TestChaosCLI:
    """Test cases for the main chaos engineering CLI."""

    @pytest.fixture
    def runner(self):
        """Create a Click CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_executor(self):
        """Mock chaos experiment executor."""
        executor = Mock()
        executor.execute_experiment = AsyncMock()
        executor.emergency_stop = AsyncMock()
        return executor

    @pytest.fixture  
    def mock_litmus_manager(self):
        """Mock LitmusChaos manager."""
        manager = Mock()
        manager.create_chaos_experiment = AsyncMock()
        manager.get_experiment_status = AsyncMock()
        manager.list_experiments = AsyncMock()
        manager.delete_experiment = AsyncMock()
        return manager

    def test_cli_main_command_shows_help(self, runner):
        """Test that the main CLI command shows help information."""
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'Chaos Engineering CLI' in result.output
        assert 'run' in result.output
        assert 'list' in result.output  
        assert 'status' in result.output
        assert 'stop' in result.output

    @patch('chaos_cli.ChaosExperimentExecutor')
    def test_run_pod_kill_experiment_command(self, mock_executor_class, runner):
        """Test running a pod kill experiment via CLI."""
        # Arrange
        mock_executor = Mock()
        mock_result = Mock()
        mock_result.experiment_name = "test-pod-kill"
        mock_result.status = Mock(value="COMPLETED")
        mock_result.execution_time = 45.2
        mock_result.safety_checks_passed = True
        mock_result.actions_performed = ["pod_kill", "health_check"]
        mock_result.error_message = None
        mock_result.to_dict.return_value = {}
        mock_executor.execute_experiment = AsyncMock(return_value=mock_result)
        mock_executor_class.return_value = mock_executor

        # Act
        result = runner.invoke(cli, [
            'run',
            '--type', 'pod_kill',
            '--name', 'test-pod-kill',
            '--namespace', 'default',
            '--target-app', 'orchestrator',
            '--duration', '30'
        ])

        # Assert  
        assert result.exit_code == 0
        assert 'Experiment test-pod-kill completed with status: COMPLETED' in result.output
        assert 'Execution time: 45.2 seconds' in result.output
        assert 'Safety checks: PASSED' in result.output

    @patch('chaos_cli.ChaosExperimentExecutor')
    def test_run_experiment_with_json_config(self, mock_executor_class, runner):
        """Test running experiment with JSON configuration file."""
        # Arrange
        config_data = {
            "name": "network-chaos-test",
            "type": "network_partition",
            "target": {
                "namespace": "default",
                "app_label": "celery-worker"
            },
            "duration": 60
        }

        mock_executor = Mock()
        mock_result = Mock()
        mock_result.experiment_name = "network-chaos-test"
        mock_result.status = Mock(value="COMPLETED")
        mock_result.execution_time = 65.1
        mock_result.safety_checks_passed = True
        mock_result.actions_performed = ["network_partition", "health_check"]
        mock_result.error_message = None
        mock_result.to_dict.return_value = {}
        mock_executor.execute_experiment = AsyncMock(return_value=mock_result)
        mock_executor_class.return_value = mock_executor

        # Act - using temporary file
        with runner.isolated_filesystem():
            with open('config.json', 'w') as f:
                json.dump(config_data, f)
            
            result = runner.invoke(cli, [
                'run',
                '--config', 'config.json'
            ])

        # Assert
        assert result.exit_code == 0
        assert 'network-chaos-test' in result.output
        mock_executor.execute_experiment.assert_called_once()

    @patch('chaos_cli.LitmusChaosManager')
    def test_list_experiments_command(self, mock_litmus_class, runner):
        """Test listing all chaos experiments."""
        # Arrange
        mock_manager = Mock()
        mock_manager.list_experiments = AsyncMock(return_value={
            "items": [
                {
                    "metadata": {"name": "exp-1", "creationTimestamp": "2024-01-01T10:00:00Z"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "exp-2", "creationTimestamp": "2024-01-01T11:00:00Z"},
                    "status": {"phase": "Completed"}
                }
            ]
        })
        mock_litmus_class.return_value = mock_manager

        # Act
        result = runner.invoke(cli, ['list'])

        # Assert
        assert result.exit_code == 0
        assert 'exp-1' in result.output
        assert 'exp-2' in result.output
        assert 'Running' in result.output
        assert 'Completed' in result.output

    @patch('chaos_cli.LitmusChaosManager')
    def test_get_experiment_status_command(self, mock_litmus_class, runner):
        """Test getting status of a specific experiment."""
        # Arrange
        experiment_name = "test-experiment"
        mock_manager = Mock()
        mock_manager.get_experiment_status = AsyncMock(return_value={
            "metadata": {"name": experiment_name},
            "status": {
                "phase": "Completed",
                "experimentStatus": {
                    "pod-delete": {
                        "verdict": "Pass",
                        "probeSuccessPercentage": "100"
                    }
                }
            }
        })
        mock_litmus_class.return_value = mock_manager

        # Act
        result = runner.invoke(cli, ['status', experiment_name])

        # Assert
        assert result.exit_code == 0
        assert experiment_name in result.output
        assert 'Completed' in result.output
        assert 'Pass' in result.output
        assert '100' in result.output

    @patch('chaos_cli.ChaosExperimentExecutor')
    def test_stop_experiment_command(self, mock_executor_class, runner):
        """Test stopping a running experiment via emergency stop."""
        # Arrange
        mock_executor = Mock()
        mock_executor.emergency_stop = AsyncMock()
        mock_executor_class.return_value = mock_executor

        # Act
        result = runner.invoke(cli, ['stop', 'test-experiment'])

        # Assert
        assert result.exit_code == 0
        assert 'Emergency stop triggered' in result.output
        mock_executor.emergency_stop.assert_called_once()

    def test_create_experiment_from_yaml_command(self, runner):
        """Test creating experiment from YAML configuration."""
        # Arrange
        yaml_config = """
        apiVersion: litmuschaos.io/v1alpha1
        kind: ChaosEngine
        metadata:
          name: cpu-stress-test
          namespace: litmus
        spec:
          appinfo:
            appns: default
            applabel: app=orchestrator
            appkind: deployment
          experiments:
          - name: pod-cpu-hog
            spec:
              components:
                env:
                - name: TOTAL_CHAOS_DURATION
                  value: "60s"
                - name: CPU_CORES
                  value: "1"
        """

        # Act
        with runner.isolated_filesystem():
            with open('chaos-experiment.yaml', 'w') as f:
                f.write(yaml_config)
            
            result = runner.invoke(cli, [
                'create',
                '--yaml', 'chaos-experiment.yaml'
            ])

        # Assert
        assert result.exit_code == 0
        assert 'cpu-stress-test' in result.output

    def test_run_experiment_with_invalid_type_shows_error(self, runner):
        """Test that invalid experiment type shows appropriate error."""
        result = runner.invoke(cli, [
            'run',
            '--type', 'invalid_type',
            '--name', 'test',
            '--namespace', 'default',
            '--target-app', 'app',
            '--duration', '30'
        ])

        assert result.exit_code != 0
        assert 'Invalid experiment type' in result.output

    def test_run_experiment_without_required_args_shows_error(self, runner):
        """Test that missing required arguments show error."""
        result = runner.invoke(cli, ['run'])

        assert result.exit_code != 0

    @patch('chaos_cli.LitmusChaosManager')
    def test_list_experiments_with_output_format_json(self, mock_litmus_class, runner):
        """Test listing experiments with JSON output format."""
        # Arrange
        experiments_data = {
            "items": [
                {
                    "metadata": {"name": "exp-1"},
                    "status": {"phase": "Running"}
                }
            ]
        }
        
        mock_manager = Mock()
        mock_manager.list_experiments = AsyncMock(return_value=experiments_data)
        mock_litmus_class.return_value = mock_manager

        # Act
        result = runner.invoke(cli, ['list', '--output', 'json'])

        # Assert
        assert result.exit_code == 0
        # Verify JSON output
        output_data = json.loads(result.output)
        assert len(output_data["items"]) == 1
        assert output_data["items"][0]["metadata"]["name"] == "exp-1"

    def test_cli_version_command(self, runner):
        """Test that version command works correctly."""
        result = runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        assert 'Chaos Engineering CLI' in result.output
        assert 'version' in result.output.lower()


class TestCLIHelpers:
    """Test cases for CLI helper functions."""

    @pytest.mark.asyncio
    async def test_run_experiment_helper_function(self):
        """Test the run_experiment helper function."""
        # Arrange
        mock_executor = Mock()
        mock_result = Mock(
            experiment_name="test",
            status=Mock(value="COMPLETED"),
            execution_time=30.0,
            safety_checks_passed=True
        )
        mock_executor.execute_experiment = AsyncMock(return_value=mock_result)

        experiment_config = {
            "name": "test",
            "type": "pod_kill",
            "duration": 30
        }

        # Act
        result = await run_experiment(mock_executor, experiment_config)

        # Assert
        assert result.experiment_name == "test"
        assert result.status.value == "COMPLETED"
        mock_executor.execute_experiment.assert_called_once_with(experiment_config)

    @pytest.mark.asyncio
    async def test_list_experiments_helper_function(self):
        """Test the list_experiments helper function."""
        # Arrange
        mock_manager = Mock()
        expected_result = {"items": [{"metadata": {"name": "exp-1"}}]}
        mock_manager.list_experiments = AsyncMock(return_value=expected_result)

        # Act
        result = await list_experiments(mock_manager)

        # Assert
        assert result == expected_result
        mock_manager.list_experiments.assert_called_once()

    @pytest.mark.asyncio  
    async def test_get_experiment_status_helper_function(self):
        """Test the get_experiment_status helper function."""
        # Arrange
        experiment_name = "test-exp"
        mock_manager = Mock()
        expected_status = {
            "metadata": {"name": experiment_name},
            "status": {"phase": "Running"}
        }
        mock_manager.get_experiment_status = AsyncMock(return_value=expected_status)

        # Act
        result = await get_experiment_status(mock_manager, experiment_name)

        # Assert
        assert result == expected_status
        mock_manager.get_experiment_status.assert_called_once_with(experiment_name)

    @pytest.mark.asyncio
    async def test_stop_experiment_helper_function(self):
        """Test the stop_experiment helper function."""
        # Arrange
        experiment_name = "test-exp"
        mock_executor = Mock()
        mock_executor.emergency_stop = AsyncMock()

        # Act
        await stop_experiment(mock_executor, experiment_name)

        # Assert
        mock_executor.emergency_stop.assert_called_once()

    def test_create_experiment_from_yaml_helper_function(self):
        """Test parsing YAML experiment configuration."""
        # Arrange
        yaml_content = """
        apiVersion: litmuschaos.io/v1alpha1
        kind: ChaosEngine
        metadata:
          name: test-experiment
        spec:
          appinfo:
            appns: default
            applabel: app=test
        """

        # Act
        result = create_experiment_from_yaml(yaml_content)

        # Assert
        assert result["kind"] == "ChaosEngine"
        assert result["metadata"]["name"] == "test-experiment"
        assert result["spec"]["appinfo"]["appns"] == "default"