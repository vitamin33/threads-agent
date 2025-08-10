"""
Test suite for KEDA ScaledObject Generator
Following TDD approach - tests written before implementation
"""

import pytest
import yaml

# This import will fail initially (TDD) - we'll implement it next
from services.ml_autoscaling.keda.scaled_object_generator import (
    KEDAScaledObjectGenerator,
    ScalingTrigger,
    ScalingTarget,
    TriggerType,
)


class TestKEDAScaledObjectGenerator:
    """Test cases for KEDA ScaledObject generation"""

    @pytest.fixture
    def generator(self):
        """Create a KEDA generator instance"""
        return KEDAScaledObjectGenerator()

    def test_create_basic_scaled_object(self, generator):
        """Test creating a basic ScaledObject for Celery workers"""
        # Arrange
        target = ScalingTarget(
            name="celery-worker",
            kind="Deployment",
            min_replicas=2,
            max_replicas=10,
        )

        # Act
        scaled_object = generator.create_scaled_object(
            name="celery-worker-scaler",
            namespace="default",
            target=target,
        )

        # Assert
        assert scaled_object["apiVersion"] == "keda.sh/v1alpha1"
        assert scaled_object["kind"] == "ScaledObject"
        assert scaled_object["metadata"]["name"] == "celery-worker-scaler"
        assert scaled_object["spec"]["minReplicaCount"] == 2
        assert scaled_object["spec"]["maxReplicaCount"] == 10
        assert scaled_object["spec"]["scaleTargetRef"]["name"] == "celery-worker"

    def test_add_rabbitmq_trigger(self, generator):
        """Test adding RabbitMQ queue-based trigger"""
        # Arrange
        target = ScalingTarget("celery-worker", "Deployment", 2, 20)
        trigger = ScalingTrigger(
            type=TriggerType.RABBITMQ,
            metadata={
                "queueName": "celery",
                "queueLength": "5",
                "hostFromEnv": "RABBITMQ_URL",
            },
        )

        # Act
        scaled_object = generator.create_scaled_object(
            name="celery-scaler",
            namespace="default",
            target=target,
            triggers=[trigger],
        )

        # Assert
        assert len(scaled_object["spec"]["triggers"]) == 1
        rabbitmq_trigger = scaled_object["spec"]["triggers"][0]
        assert rabbitmq_trigger["type"] == "rabbitmq"
        assert rabbitmq_trigger["metadata"]["queueName"] == "celery"
        assert rabbitmq_trigger["metadata"]["queueLength"] == "5"

    def test_add_prometheus_metrics_trigger(self, generator):
        """Test adding Prometheus metrics-based trigger"""
        # Arrange
        target = ScalingTarget("vllm-service", "Deployment", 1, 5)
        trigger = ScalingTrigger(
            type=TriggerType.PROMETHEUS,
            metadata={
                "serverAddress": "http://prometheus:9090",
                "metricName": "vllm_inference_latency_p95",
                "threshold": "500",
                "query": "histogram_quantile(0.95, rate(vllm_request_duration_seconds_bucket[5m]))",
            },
        )

        # Act
        scaled_object = generator.create_scaled_object(
            name="vllm-scaler",
            namespace="default",
            target=target,
            triggers=[trigger],
        )

        # Assert
        prometheus_trigger = scaled_object["spec"]["triggers"][0]
        assert prometheus_trigger["type"] == "prometheus"
        assert prometheus_trigger["metadata"]["threshold"] == "500"
        assert "histogram_quantile" in prometheus_trigger["metadata"]["query"]

    def test_multiple_triggers_combination(self, generator):
        """Test combining multiple triggers for advanced scaling"""
        # Arrange
        target = ScalingTarget("ml-worker", "Deployment", 2, 15)

        queue_trigger = ScalingTrigger(
            type=TriggerType.RABBITMQ,
            metadata={"queueName": "ml-tasks", "queueLength": "10"},
        )

        latency_trigger = ScalingTrigger(
            type=TriggerType.PROMETHEUS,
            metadata={
                "serverAddress": "http://prometheus:9090",
                "metricName": "ml_inference_latency",
                "threshold": "1000",
            },
        )

        cpu_trigger = ScalingTrigger(
            type=TriggerType.CPU, metadata={"type": "Utilization", "value": "70"}
        )

        # Act
        scaled_object = generator.create_scaled_object(
            name="ml-worker-scaler",
            namespace="ml-system",
            target=target,
            triggers=[queue_trigger, latency_trigger, cpu_trigger],
        )

        # Assert
        assert len(scaled_object["spec"]["triggers"]) == 3
        trigger_types = [t["type"] for t in scaled_object["spec"]["triggers"]]
        assert "rabbitmq" in trigger_types
        assert "prometheus" in trigger_types
        assert "cpu" in trigger_types

    def test_scale_to_zero_configuration(self, generator):
        """Test scale-to-zero configuration for GPU workloads"""
        # Arrange
        target = ScalingTarget(
            name="gpu-inference",
            kind="Deployment",
            min_replicas=0,  # Scale to zero
            max_replicas=4,
        )

        trigger = ScalingTrigger(
            type=TriggerType.PROMETHEUS,
            metadata={
                "serverAddress": "http://prometheus:9090",
                "metricName": "gpu_inference_requests",
                "threshold": "1",  # Scale up from zero when any request
            },
        )

        # Act
        scaled_object = generator.create_scaled_object(
            name="gpu-scaler",
            namespace="ml-gpu",
            target=target,
            triggers=[trigger],
            idle_replica_count=0,  # Explicitly set to zero
            cooldown_period=60,
        )

        # Assert
        assert scaled_object["spec"]["minReplicaCount"] == 0
        assert scaled_object["spec"]["idleReplicaCount"] == 0
        assert scaled_object["spec"]["cooldownPeriod"] == 60

    def test_advanced_scaling_behavior(self, generator):
        """Test advanced scaling behavior configuration"""
        # Arrange
        target = ScalingTarget("orchestrator", "Deployment", 3, 20)

        behavior = {
            "scaleUp": {
                "stabilizationWindowSeconds": 30,
                "policies": [
                    {"type": "Percent", "value": 100, "periodSeconds": 15},
                    {"type": "Pods", "value": 4, "periodSeconds": 15},
                ],
            },
            "scaleDown": {
                "stabilizationWindowSeconds": 300,
                "policies": [
                    {"type": "Percent", "value": 50, "periodSeconds": 60},
                ],
            },
        }

        # Act
        scaled_object = generator.create_scaled_object(
            name="orchestrator-scaler",
            namespace="default",
            target=target,
            scaling_behavior=behavior,
        )

        # Assert
        assert "behavior" in scaled_object["spec"]["advanced"]
        scale_up = scaled_object["spec"]["advanced"]["behavior"]["scaleUp"]
        assert scale_up["stabilizationWindowSeconds"] == 30
        assert len(scale_up["policies"]) == 2

        scale_down = scaled_object["spec"]["advanced"]["behavior"]["scaleDown"]
        assert scale_down["stabilizationWindowSeconds"] == 300

    def test_gpu_aware_scaling(self, generator):
        """Test GPU-aware scaling configuration"""
        # Arrange
        target = ScalingTarget(
            name="vllm-gpu-service",
            kind="Deployment",
            min_replicas=0,
            max_replicas=4,
        )

        gpu_trigger = ScalingTrigger(
            type=TriggerType.PROMETHEUS,
            metadata={
                "serverAddress": "http://prometheus:9090",
                "metricName": "gpu_utilization_percent",
                "threshold": "80",
                "query": "avg(gpu_utilization_percent{job='vllm-service'})",
            },
        )

        # Act
        scaled_object = generator.create_scaled_object(
            name="vllm-gpu-scaler",
            namespace="ml-gpu",
            target=target,
            triggers=[gpu_trigger],
            pod_template_annotations={
                "nvidia.com/gpu": "1",
                "node-selector": "gpu-node",
            },
        )

        # Assert
        assert scaled_object["spec"]["triggers"][0]["metadata"]["threshold"] == "80"
        assert (
            "gpu_utilization_percent"
            in scaled_object["spec"]["triggers"][0]["metadata"]["query"]
        )

    def test_cost_optimized_scaling(self, generator):
        """Test cost-optimized scaling with spot instance preferences"""
        # Arrange
        target = ScalingTarget("ml-training", "Job", 1, 10)

        cost_trigger = ScalingTrigger(
            type=TriggerType.EXTERNAL,
            metadata={
                "scalerAddress": "cost-optimizer:8080",
                "metricName": "spot_instance_availability",
                "threshold": "0.7",  # Scale when spot price < 70% of on-demand
            },
        )

        # Act
        scaled_object = generator.create_scaled_object(
            name="cost-optimized-scaler",
            namespace="ml-training",
            target=target,
            triggers=[cost_trigger],
            pod_template_annotations={
                "scheduler.alpha.kubernetes.io/preferredDuringScheduling": "spot-instances",
                "cost-optimizer/max-price": "0.7",
            },
        )

        # Assert
        assert scaled_object["spec"]["triggers"][0]["type"] == "external"
        assert (
            "spot_instance_availability"
            in scaled_object["spec"]["triggers"][0]["metadata"]["metricName"]
        )

    def test_yaml_generation(self, generator):
        """Test generating valid YAML output"""
        # Arrange
        target = ScalingTarget("test-deployment", "Deployment", 1, 5)

        # Act
        scaled_object = generator.create_scaled_object(
            name="test-scaler",
            namespace="default",
            target=target,
        )
        yaml_output = generator.to_yaml(scaled_object)

        # Assert
        assert isinstance(yaml_output, str)
        parsed = yaml.safe_load(yaml_output)
        assert parsed["kind"] == "ScaledObject"
        assert parsed["metadata"]["name"] == "test-scaler"

    def test_validation_errors(self, generator):
        """Test validation of invalid configurations"""
        # Act & Assert
        with pytest.raises(
            ValueError,
            match="max_replicas must be greater than or equal to min_replicas",
        ):
            invalid_target = ScalingTarget(
                name="invalid",
                kind="Deployment",
                min_replicas=10,  # Min > Max
                max_replicas=5,
            )

    @pytest.mark.parametrize(
        "trigger_type,expected_fields",
        [
            (TriggerType.RABBITMQ, ["queueName", "queueLength"]),
            (TriggerType.PROMETHEUS, ["serverAddress", "metricName", "threshold"]),
            (TriggerType.CPU, ["type", "value"]),
            (TriggerType.MEMORY, ["type", "value"]),
        ],
    )
    def test_trigger_validation(self, generator, trigger_type, expected_fields):
        """Test validation of trigger configurations"""
        # Arrange
        target = ScalingTarget("test", "Deployment", 1, 5)

        # Invalid trigger with missing required fields
        invalid_trigger = ScalingTrigger(
            type=trigger_type,
            metadata={},  # Empty metadata
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Missing required fields"):
            generator.validate_trigger(invalid_trigger, expected_fields)
