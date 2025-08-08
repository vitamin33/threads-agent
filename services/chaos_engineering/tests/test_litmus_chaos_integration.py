"""
Test cases for LitmusChaos Kubernetes operator integration.

This module tests the integration with LitmusChaos for Kubernetes-native chaos experiments.
"""

import pytest
from unittest.mock import Mock, AsyncMock

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from litmus_chaos_integration import (
    LitmusChaosManager,
    ChaosExperiment,
    ExperimentType,
)


class TestLitmusChaosManager:
    """Test cases for LitmusChaos integration manager."""

    @pytest.fixture
    def mock_k8s_client(self):
        """Mock Kubernetes client for testing."""
        client = Mock()
        client.create_namespaced_custom_object = AsyncMock()
        client.get_namespaced_custom_object = AsyncMock()
        client.delete_namespaced_custom_object = AsyncMock()
        client.list_namespaced_custom_object = AsyncMock()
        return client

    @pytest.fixture
    def litmus_manager(self, mock_k8s_client):
        """Create a LitmusChaos manager with mocked dependencies."""
        return LitmusChaosManager(k8s_client=mock_k8s_client, namespace="litmus")

    def test_litmus_chaos_manager_initialization(self, litmus_manager):
        """Test that LitmusChaos manager initializes correctly."""
        assert litmus_manager is not None
        assert hasattr(litmus_manager, "create_chaos_experiment")
        assert hasattr(litmus_manager, "namespace")
        assert litmus_manager.namespace == "litmus"

    @pytest.mark.asyncio
    async def test_create_pod_delete_chaos_experiment(
        self, litmus_manager, mock_k8s_client
    ):
        """Test creating a pod delete chaos experiment through LitmusChaos."""
        # Arrange
        experiment_spec = {
            "name": "pod-delete-test",
            "namespace": "default",
            "target": {
                "app_label": "orchestrator",
                "chaos_duration": "30s",
                "chaos_interval": "10s",
                "force": "false",
            },
        }

        mock_k8s_client.create_namespaced_custom_object.return_value = {
            "metadata": {"name": "pod-delete-test", "uid": "test-uid-123"},
            "status": {"phase": "Running"},
        }

        # Act
        result = await litmus_manager.create_chaos_experiment(
            ExperimentType.POD_DELETE, experiment_spec
        )

        # Assert
        assert result["metadata"]["name"] == "pod-delete-test"
        assert result["status"]["phase"] == "Running"

        # Verify the correct Kubernetes API calls were made
        mock_k8s_client.create_namespaced_custom_object.assert_called_once()
        call_args = mock_k8s_client.create_namespaced_custom_object.call_args

        assert call_args[1]["group"] == "litmuschaos.io"
        assert call_args[1]["version"] == "v1alpha1"
        assert call_args[1]["plural"] == "chaosengines"
        assert call_args[1]["namespace"] == "litmus"

    @pytest.mark.asyncio
    async def test_create_network_partition_chaos_experiment(
        self, litmus_manager, mock_k8s_client
    ):
        """Test creating a network partition chaos experiment."""
        # Arrange
        experiment_spec = {
            "name": "network-partition-test",
            "namespace": "default",
            "target": {
                "app_label": "celery-worker",
                "chaos_duration": "60s",
                "network_interface": "eth0",
                "destination_ips": "10.0.0.1,10.0.0.2",
            },
        }

        expected_chaos_engine = {
            "apiVersion": "litmuschaos.io/v1alpha1",
            "kind": "ChaosEngine",
            "metadata": {"name": "network-partition-test", "namespace": "litmus"},
            "spec": {
                "appinfo": {
                    "appns": "default",
                    "applabel": "app=celery-worker",
                    "appkind": "deployment",
                },
                "experiments": [
                    {
                        "name": "pod-network-partition",
                        "spec": {
                            "components": {
                                "env": [
                                    {"name": "TOTAL_CHAOS_DURATION", "value": "60s"},
                                    {"name": "NETWORK_INTERFACE", "value": "eth0"},
                                    {
                                        "name": "DESTINATION_IPS",
                                        "value": "10.0.0.1,10.0.0.2",
                                    },
                                ]
                            }
                        },
                    }
                ],
            },
        }

        # Act
        await litmus_manager.create_chaos_experiment(
            ExperimentType.NETWORK_PARTITION, experiment_spec
        )

        # Assert
        mock_k8s_client.create_namespaced_custom_object.assert_called_once()
        call_args = mock_k8s_client.create_namespaced_custom_object.call_args

        # Verify the body structure matches our expected ChaosEngine spec
        body = call_args[1]["body"]
        assert body["kind"] == "ChaosEngine"
        assert body["spec"]["appinfo"]["applabel"] == "app=celery-worker"
        assert body["spec"]["experiments"][0]["name"] == "pod-network-partition"

    @pytest.mark.asyncio
    async def test_get_chaos_experiment_status(self, litmus_manager, mock_k8s_client):
        """Test getting the status of a running chaos experiment."""
        # Arrange
        experiment_name = "test-experiment"
        expected_status = {
            "metadata": {"name": experiment_name},
            "status": {
                "phase": "Completed",
                "experimentStatus": {
                    "pod-delete": {"verdict": "Pass", "probeSuccessPercentage": "100"}
                },
            },
        }

        mock_k8s_client.get_namespaced_custom_object.return_value = expected_status

        # Act
        result = await litmus_manager.get_experiment_status(experiment_name)

        # Assert
        assert result["status"]["phase"] == "Completed"
        assert result["status"]["experimentStatus"]["pod-delete"]["verdict"] == "Pass"

        mock_k8s_client.get_namespaced_custom_object.assert_called_once_with(
            group="litmuschaos.io",
            version="v1alpha1",
            namespace="litmus",
            plural="chaosengines",
            name=experiment_name,
        )

    @pytest.mark.asyncio
    async def test_delete_chaos_experiment(self, litmus_manager, mock_k8s_client):
        """Test deleting a chaos experiment."""
        # Arrange
        experiment_name = "test-experiment-to-delete"
        mock_k8s_client.delete_namespaced_custom_object.return_value = {
            "status": "Success"
        }

        # Act
        result = await litmus_manager.delete_experiment(experiment_name)

        # Assert
        assert result["status"] == "Success"

        mock_k8s_client.delete_namespaced_custom_object.assert_called_once_with(
            group="litmuschaos.io",
            version="v1alpha1",
            namespace="litmus",
            plural="chaosengines",
            name=experiment_name,
        )

    @pytest.mark.asyncio
    async def test_list_all_chaos_experiments(self, litmus_manager, mock_k8s_client):
        """Test listing all chaos experiments in the namespace."""
        # Arrange
        expected_experiments = {
            "items": [
                {"metadata": {"name": "exp-1"}, "status": {"phase": "Running"}},
                {"metadata": {"name": "exp-2"}, "status": {"phase": "Completed"}},
            ]
        }

        mock_k8s_client.list_namespaced_custom_object.return_value = (
            expected_experiments
        )

        # Act
        result = await litmus_manager.list_experiments()

        # Assert
        assert len(result["items"]) == 2
        assert result["items"][0]["metadata"]["name"] == "exp-1"
        assert result["items"][1]["status"]["phase"] == "Completed"


class TestChaosExperiment:
    """Test cases for ChaosExperiment data class."""

    def test_chaos_experiment_creation(self):
        """Test creating a ChaosExperiment object."""
        experiment = ChaosExperiment(
            name="test-experiment",
            experiment_type=ExperimentType.POD_DELETE,
            namespace="default",
            target_app="test-app",
            chaos_duration="30s",
        )

        assert experiment.name == "test-experiment"
        assert experiment.experiment_type == ExperimentType.POD_DELETE
        assert experiment.namespace == "default"
        assert experiment.target_app == "test-app"
        assert experiment.chaos_duration == "30s"

    def test_chaos_experiment_to_chaos_engine_spec(self):
        """Test converting ChaosExperiment to Kubernetes ChaosEngine specification."""
        experiment = ChaosExperiment(
            name="pod-kill-test",
            experiment_type=ExperimentType.POD_DELETE,
            namespace="default",
            target_app="orchestrator",
            chaos_duration="45s",
            chaos_interval="15s",
        )

        chaos_engine = experiment.to_chaos_engine_spec()

        assert chaos_engine["kind"] == "ChaosEngine"
        assert chaos_engine["metadata"]["name"] == "pod-kill-test"
        assert chaos_engine["spec"]["appinfo"]["appns"] == "default"
        assert chaos_engine["spec"]["appinfo"]["applabel"] == "app=orchestrator"

        # Check experiment-specific configuration
        exp_spec = chaos_engine["spec"]["experiments"][0]
        assert exp_spec["name"] == "pod-delete"

        env_vars = {
            env["name"]: env["value"] for env in exp_spec["spec"]["components"]["env"]
        }
        assert env_vars["TOTAL_CHAOS_DURATION"] == "45s"
        assert env_vars["CHAOS_INTERVAL"] == "15s"


class TestExperimentType:
    """Test cases for ExperimentType enum."""

    def test_experiment_type_values(self):
        """Test that ExperimentType has all required experiment types."""
        assert hasattr(ExperimentType, "POD_DELETE")
        assert hasattr(ExperimentType, "NETWORK_PARTITION")
        assert hasattr(ExperimentType, "CPU_HOG")
        assert hasattr(ExperimentType, "MEMORY_HOG")
        assert hasattr(ExperimentType, "DISK_FILL")

        # Verify string values for YAML serialization
        assert ExperimentType.POD_DELETE.value == "pod-delete"
        assert ExperimentType.NETWORK_PARTITION.value == "pod-network-partition"
        assert ExperimentType.CPU_HOG.value == "pod-cpu-hog"
