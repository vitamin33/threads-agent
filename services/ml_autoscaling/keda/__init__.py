"""
KEDA autoscaling module for ML workloads
"""

from .scaled_object_generator import (
    KEDAScaledObjectGenerator,
    ScalingTrigger,
    ScalingTarget,
    TriggerType,
    MetricType,
)

__all__ = [
    "KEDAScaledObjectGenerator",
    "ScalingTrigger",
    "ScalingTarget",
    "TriggerType",
    "MetricType",
]
