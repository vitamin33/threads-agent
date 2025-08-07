"""
LitmusChaos Kubernetes Operator Integration.

This module provides integration with LitmusChaos for running Kubernetes-native
chaos experiments through custom resources.
"""

import asyncio
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, List, Optional
from unittest.mock import Mock
import yaml


class ExperimentType(Enum):
    """Types of chaos experiments supported by LitmusChaos."""
    POD_DELETE = "pod-delete"
    NETWORK_PARTITION = "pod-network-partition"
    CPU_HOG = "pod-cpu-hog"
    MEMORY_HOG = "pod-memory-hog"
    DISK_FILL = "pod-disk-fill"


@dataclass
class ChaosExperiment:
    """Data class representing a chaos experiment configuration."""
    name: str
    experiment_type: ExperimentType
    namespace: str
    target_app: str
    chaos_duration: str
    chaos_interval: Optional[str] = "10s"
    force: Optional[str] = "false"
    
    def to_chaos_engine_spec(self) -> Dict[str, Any]:
        """
        Convert this experiment to a Kubernetes ChaosEngine specification.
        
        Returns:
            Dict: Kubernetes ChaosEngine custom resource specification
        """
        # Base ChaosEngine structure
        chaos_engine = {
            "apiVersion": "litmuschaos.io/v1alpha1",
            "kind": "ChaosEngine",
            "metadata": {
                "name": self.name,
                "namespace": "litmus"  # LitmusChaos operator namespace
            },
            "spec": {
                "appinfo": {
                    "appns": self.namespace,
                    "applabel": f"app={self.target_app}",
                    "appkind": "deployment"
                },
                "experiments": [{
                    "name": self.experiment_type.value,
                    "spec": {
                        "components": {
                            "env": [
                                {"name": "TOTAL_CHAOS_DURATION", "value": self.chaos_duration}
                            ]
                        }
                    }
                }]
            }
        }
        
        # Add experiment-specific environment variables
        env_vars = chaos_engine["spec"]["experiments"][0]["spec"]["components"]["env"]
        
        if self.chaos_interval:
            env_vars.append({"name": "CHAOS_INTERVAL", "value": self.chaos_interval})
        
        if self.force:
            env_vars.append({"name": "FORCE", "value": self.force})
        
        return chaos_engine


@dataclass 
class ChaosEngineSpec:
    """Specification for a ChaosEngine custom resource."""
    name: str
    namespace: str
    app_namespace: str
    app_label: str
    experiments: List[Dict[str, Any]]


class LitmusChaosManager:
    """
    Manager for LitmusChaos Kubernetes operator integration.
    
    This class handles creation, monitoring, and deletion of chaos experiments
    through the LitmusChaos operator using Kubernetes custom resources.
    """
    
    def __init__(self, k8s_client: Optional[Any] = None, namespace: str = "litmus"):
        """
        Initialize the LitmusChaos manager.
        
        Args:
            k8s_client: Kubernetes client for API operations
            namespace: Namespace where LitmusChaos operator is installed
        """
        self.k8s_client = k8s_client or Mock()
        self.namespace = namespace
        
        # LitmusChaos API configuration
        self.group = "litmuschaos.io"
        self.version = "v1alpha1"
        self.chaos_engine_plural = "chaosengines"
    
    async def create_chaos_experiment(
        self, 
        experiment_type: ExperimentType,
        experiment_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new chaos experiment using LitmusChaos.
        
        Args:
            experiment_type: Type of chaos experiment to create
            experiment_spec: Experiment configuration
            
        Returns:
            Dict: Created ChaosEngine resource
        """
        # Create ChaosExperiment object
        chaos_experiment = ChaosExperiment(
            name=experiment_spec["name"],
            experiment_type=experiment_type,
            namespace=experiment_spec.get("namespace", "default"),
            target_app=experiment_spec["target"].get("app_label", ""),
            chaos_duration=experiment_spec["target"].get("chaos_duration", "30s"),
            chaos_interval=experiment_spec["target"].get("chaos_interval", "10s"),
            force=experiment_spec["target"].get("force", "false")
        )
        
        # Convert to ChaosEngine specification
        chaos_engine_spec = chaos_experiment.to_chaos_engine_spec()
        
        # Handle network partition specific configuration
        if experiment_type == ExperimentType.NETWORK_PARTITION:
            env_vars = chaos_engine_spec["spec"]["experiments"][0]["spec"]["components"]["env"]
            
            if "network_interface" in experiment_spec["target"]:
                env_vars.append({
                    "name": "NETWORK_INTERFACE",
                    "value": experiment_spec["target"]["network_interface"]
                })
            
            if "destination_ips" in experiment_spec["target"]:
                env_vars.append({
                    "name": "DESTINATION_IPS", 
                    "value": experiment_spec["target"]["destination_ips"]
                })
        
        # Create the ChaosEngine in Kubernetes
        result = await self.k8s_client.create_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=self.namespace,
            plural=self.chaos_engine_plural,
            body=chaos_engine_spec
        )
        
        return result
    
    async def get_experiment_status(self, experiment_name: str) -> Dict[str, Any]:
        """
        Get the current status of a chaos experiment.
        
        Args:
            experiment_name: Name of the experiment to check
            
        Returns:
            Dict: ChaosEngine status information
        """
        result = await self.k8s_client.get_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=self.namespace,
            plural=self.chaos_engine_plural,
            name=experiment_name
        )
        
        return result
    
    async def delete_experiment(self, experiment_name: str) -> Dict[str, Any]:
        """
        Delete a chaos experiment.
        
        Args:
            experiment_name: Name of the experiment to delete
            
        Returns:
            Dict: Deletion result
        """
        result = await self.k8s_client.delete_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=self.namespace,
            plural=self.chaos_engine_plural,
            name=experiment_name
        )
        
        return result
    
    async def list_experiments(self) -> Dict[str, Any]:
        """
        List all chaos experiments in the namespace.
        
        Returns:
            Dict: List of ChaosEngine resources
        """
        result = await self.k8s_client.list_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=self.namespace,
            plural=self.chaos_engine_plural
        )
        
        return result
    
    async def wait_for_experiment_completion(
        self, 
        experiment_name: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Wait for a chaos experiment to complete.
        
        Args:
            experiment_name: Name of the experiment to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Dict: Final experiment status
        """
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            status = await self.get_experiment_status(experiment_name)
            
            if status.get("status", {}).get("phase") in ["Completed", "Failed", "Stopped"]:
                return status
            
            await asyncio.sleep(5)  # Check every 5 seconds
        
        raise TimeoutError(f"Experiment {experiment_name} did not complete within {timeout} seconds")
    
    def generate_chaos_engine_yaml(self, chaos_experiment: ChaosExperiment) -> str:
        """
        Generate YAML representation of a ChaosEngine for the experiment.
        
        Args:
            chaos_experiment: Experiment to convert to YAML
            
        Returns:
            str: YAML representation of the ChaosEngine
        """
        chaos_engine_spec = chaos_experiment.to_chaos_engine_spec()
        return yaml.dump(chaos_engine_spec, default_flow_style=False)