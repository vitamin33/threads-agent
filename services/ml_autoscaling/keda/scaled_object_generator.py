"""
KEDA ScaledObject Generator for ML Workloads
Implements intelligent autoscaling configurations for ML infrastructure
"""

import yaml
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, List, Optional


class TriggerType(Enum):
    """Supported KEDA trigger types"""
    RABBITMQ = "rabbitmq"
    PROMETHEUS = "prometheus"
    CPU = "cpu"
    MEMORY = "memory"
    EXTERNAL = "external"
    CRON = "cron"


class MetricType(Enum):
    """Metric types for scaling decisions"""
    UTILIZATION = "Utilization"
    AVERAGE_VALUE = "AverageValue"
    VALUE = "Value"


@dataclass
class ScalingTarget:
    """Target resource for scaling"""
    name: str
    kind: str = "Deployment"
    min_replicas: int = 1
    max_replicas: int = 10

    def __post_init__(self):
        """Validate scaling target configuration"""
        if self.min_replicas < 0:
            raise ValueError("min_replicas must be non-negative")
        if self.max_replicas < self.min_replicas:
            raise ValueError("max_replicas must be greater than or equal to min_replicas")
        if self.min_replicas > self.max_replicas:
            raise ValueError("min_replicas cannot be greater than max_replicas")


@dataclass
class ScalingTrigger:
    """Scaling trigger configuration"""
    type: TriggerType
    metadata: Dict[str, Any]
    name: Optional[str] = None
    metric_type: Optional[MetricType] = None
    authentication_ref: Optional[Dict[str, str]] = None


class KEDAScaledObjectGenerator:
    """
    Generator for KEDA ScaledObjects optimized for ML workloads
    
    This class creates KEDA configurations that enable:
    - Queue-based scaling for Celery workers
    - Latency-based scaling for inference services
    - GPU-aware scaling for ML models
    - Cost-optimized scaling with spot instances
    """

    def __init__(self):
        """Initialize the KEDA generator"""
        self.api_version = "keda.sh/v1alpha1"
        self.kind = "ScaledObject"

    def create_scaled_object(
        self,
        name: str,
        namespace: str,
        target: ScalingTarget,
        triggers: Optional[List[ScalingTrigger]] = None,
        polling_interval: int = 30,
        cooldown_period: int = 300,
        idle_replica_count: Optional[int] = None,
        scaling_behavior: Optional[Dict[str, Any]] = None,
        pod_template_annotations: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a KEDA ScaledObject configuration
        
        Args:
            name: Name of the ScaledObject
            namespace: Kubernetes namespace
            target: Scaling target configuration
            triggers: List of scaling triggers
            polling_interval: How often KEDA polls metrics (seconds)
            cooldown_period: Wait time before scaling down (seconds)
            idle_replica_count: Replicas when idle (for scale-to-zero)
            scaling_behavior: Advanced scaling behavior
            pod_template_annotations: Annotations for pods (e.g., GPU)
        
        Returns:
            Dict representing the ScaledObject YAML
        """
        # Validate target
        if target.min_replicas > target.max_replicas:
            raise ValueError("min_replicas cannot be greater than max_replicas")

        scaled_object = {
            "apiVersion": self.api_version,
            "kind": self.kind,
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": {
                    "app.kubernetes.io/managed-by": "keda",
                    "ml-autoscaling/enabled": "true",
                }
            },
            "spec": {
                "scaleTargetRef": {
                    "name": target.name,
                    "kind": target.kind,
                },
                "minReplicaCount": target.min_replicas,
                "maxReplicaCount": target.max_replicas,
                "pollingInterval": polling_interval,
                "cooldownPeriod": cooldown_period,
            }
        }

        # Add idle replica count if specified (for scale-to-zero)
        if idle_replica_count is not None:
            scaled_object["spec"]["idleReplicaCount"] = idle_replica_count

        # Add triggers
        if triggers:
            scaled_object["spec"]["triggers"] = [
                self._build_trigger(trigger) for trigger in triggers
            ]

        # Add advanced scaling behavior
        if scaling_behavior:
            scaled_object["spec"]["advanced"] = {
                "behavior": scaling_behavior
            }

        # Add pod template annotations (for GPU nodes, spot instances, etc.)
        if pod_template_annotations:
            scaled_object["metadata"]["annotations"] = pod_template_annotations

        return scaled_object

    def _build_trigger(self, trigger: ScalingTrigger) -> Dict[str, Any]:
        """Build a trigger configuration"""
        trigger_config = {
            "type": trigger.type.value,
            "metadata": trigger.metadata,
        }

        if trigger.name:
            trigger_config["name"] = trigger.name

        if trigger.authentication_ref:
            trigger_config["authenticationRef"] = trigger.authentication_ref

        return trigger_config

    def validate_trigger(self, trigger: ScalingTrigger, required_fields: List[str]) -> None:
        """
        Validate that a trigger has required fields
        
        Args:
            trigger: Trigger to validate
            required_fields: List of required metadata fields
        
        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = [
            field for field in required_fields 
            if field not in trigger.metadata
        ]
        
        if missing_fields:
            raise ValueError(
                f"Missing required fields for {trigger.type.value} trigger: {missing_fields}"
            )

    def create_celery_worker_scaler(
        self,
        name: str = "celery-worker-scaler",
        namespace: str = "default",
        min_replicas: int = 2,
        max_replicas: int = 20,
        queue_threshold: int = 5,
        latency_threshold: int = 10,
    ) -> Dict[str, Any]:
        """
        Create a specialized ScaledObject for Celery workers
        
        Combines queue depth and task latency for optimal scaling
        """
        target = ScalingTarget(
            name="celery-worker",
            kind="Deployment",
            min_replicas=min_replicas,
            max_replicas=max_replicas,
        )

        triggers = [
            # Scale based on RabbitMQ queue depth
            ScalingTrigger(
                type=TriggerType.RABBITMQ,
                metadata={
                    "queueName": "celery",
                    "queueLength": str(queue_threshold),
                    "hostFromEnv": "RABBITMQ_URL",
                }
            ),
            # Scale based on task processing latency
            ScalingTrigger(
                type=TriggerType.PROMETHEUS,
                metadata={
                    "serverAddress": "http://prometheus:9090",
                    "metricName": "celery_task_duration_seconds",
                    "threshold": str(latency_threshold),
                    "query": "avg(rate(celery_task_duration_seconds[5m]))",
                }
            ),
        ]

        behavior = {
            "scaleUp": {
                "stabilizationWindowSeconds": 30,
                "policies": [
                    {"type": "Percent", "value": 100, "periodSeconds": 15},
                    {"type": "Pods", "value": 4, "periodSeconds": 15},
                ],
                "selectPolicy": "Max",  # Use most aggressive scale-up
            },
            "scaleDown": {
                "stabilizationWindowSeconds": 300,
                "policies": [
                    {"type": "Percent", "value": 50, "periodSeconds": 60},
                ],
            },
        }

        return self.create_scaled_object(
            name=name,
            namespace=namespace,
            target=target,
            triggers=triggers,
            scaling_behavior=behavior,
            cooldown_period=60,  # Faster scale-down for cost optimization
        )

    def create_vllm_gpu_scaler(
        self,
        name: str = "vllm-gpu-scaler",
        namespace: str = "ml-inference",
        min_replicas: int = 0,  # Scale to zero when not used
        max_replicas: int = 4,
        latency_threshold_ms: int = 500,
        gpu_utilization_threshold: int = 80,
    ) -> Dict[str, Any]:
        """
        Create a GPU-aware ScaledObject for vLLM service
        
        Optimizes for:
        - Scale-to-zero to save GPU costs
        - Latency-based scaling for user experience
        - GPU utilization monitoring
        """
        target = ScalingTarget(
            name="vllm-service",
            kind="Deployment",
            min_replicas=min_replicas,
            max_replicas=max_replicas,
        )

        triggers = [
            # Scale based on inference latency
            ScalingTrigger(
                type=TriggerType.PROMETHEUS,
                metadata={
                    "serverAddress": "http://prometheus:9090",
                    "metricName": "vllm_inference_latency_p95",
                    "threshold": str(latency_threshold_ms),
                    "query": f"histogram_quantile(0.95, rate(vllm_request_duration_seconds_bucket[5m])) * 1000",
                }
            ),
            # Scale based on request rate
            ScalingTrigger(
                type=TriggerType.PROMETHEUS,
                metadata={
                    "serverAddress": "http://prometheus:9090",
                    "metricName": "vllm_requests_per_second",
                    "threshold": "10",
                    "query": "rate(vllm_requests_total[1m])",
                }
            ),
        ]

        # Add GPU utilization trigger if not scaling to zero
        if min_replicas > 0:
            triggers.append(
                ScalingTrigger(
                    type=TriggerType.PROMETHEUS,
                    metadata={
                        "serverAddress": "http://prometheus:9090",
                        "metricName": "gpu_utilization_percent",
                        "threshold": str(gpu_utilization_threshold),
                        "query": f"avg(gpu_utilization_percent{{job='vllm-service'}})",
                    }
                )
            )

        return self.create_scaled_object(
            name=name,
            namespace=namespace,
            target=target,
            triggers=triggers,
            idle_replica_count=0 if min_replicas == 0 else None,
            cooldown_period=300,  # 5 minutes for GPU instances
            pod_template_annotations={
                "nvidia.com/gpu": "1",
                "node-selector": "gpu-node",
                "scheduler.alpha.kubernetes.io/prefer-spot": "true",
            },
        )

    def create_ml_training_scaler(
        self,
        name: str = "ml-training-scaler",
        namespace: str = "ml-training",
        min_replicas: int = 0,
        max_replicas: int = 10,
    ) -> Dict[str, Any]:
        """
        Create a ScaledObject for ML training jobs
        
        Uses cron-based scaling for scheduled training
        """
        target = ScalingTarget(
            name="training-worker",
            kind="Deployment",
            min_replicas=min_replicas,
            max_replicas=max_replicas,
        )

        triggers = [
            # Scale based on training queue
            ScalingTrigger(
                type=TriggerType.PROMETHEUS,
                metadata={
                    "serverAddress": "http://prometheus:9090",
                    "metricName": "ml_training_jobs_pending",
                    "threshold": "1",
                    "query": "ml_training_jobs_pending",
                }
            ),
            # Schedule-based scaling for nightly training
            ScalingTrigger(
                type=TriggerType.CRON,
                metadata={
                    "timezone": "UTC",
                    "start": "0 2 * * *",  # 2 AM UTC
                    "end": "0 6 * * *",    # 6 AM UTC
                    "desiredReplicas": "5",
                }
            ),
        ]

        return self.create_scaled_object(
            name=name,
            namespace=namespace,
            target=target,
            triggers=triggers,
            idle_replica_count=0,
            cooldown_period=600,  # 10 minutes for training jobs
        )

    def to_yaml(self, scaled_object: Dict[str, Any]) -> str:
        """Convert ScaledObject dict to YAML string"""
        return yaml.dump(scaled_object, default_flow_style=False, sort_keys=False)

    def save_to_file(self, scaled_object: Dict[str, Any], filepath: str) -> None:
        """Save ScaledObject to YAML file"""
        with open(filepath, 'w') as f:
            yaml.dump(scaled_object, f, default_flow_style=False, sort_keys=False)