"""
Enhanced configuration for ML/AI workloads - Production best practices.

This demonstrates understanding of ML infrastructure requirements
for MLOps Engineer / AI Platform roles.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass
import json


@dataclass
class MLModelConfig:
    """Configuration for ML model serving."""

    model_name: str
    model_version: str
    batch_size: int = 32
    max_sequence_length: int = 512
    device: str = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu"
    quantization: bool = False
    optimization_level: str = "O1"  # For mixed precision training


class AIInfraConfig:
    """
    Production-grade configuration for AI/ML infrastructure.
    Demonstrates best practices for MLOps roles.
    """

    def __init__(self):
        """Initialize from environment with intelligent defaults."""
        # Model Registry Configuration (MLflow, W&B, etc.)
        self.model_registry_uri = os.getenv("MODEL_REGISTRY_URI", "http://mlflow:5000")

        # Vector Database Configuration (Qdrant, Pinecone, Weaviate)
        self.vector_db_url = os.getenv("VECTOR_DB_URL", "http://qdrant:6333")

        # GPU Resource Management
        self.gpu_memory_fraction = float(os.getenv("GPU_MEMORY_FRACTION", "0.8"))

        # Distributed Training Configuration
        self.distributed_backend = os.getenv(
            "DISTRIBUTED_BACKEND",
            "nccl",  # For multi-GPU training
        )

        # Feature Store Configuration
        self.feature_store_url = os.getenv("FEATURE_STORE_URL", "http://feast:6565")

        # Model Serving Configuration
        self.serving_config = {
            "max_batch_size": int(os.getenv("MAX_BATCH_SIZE", "32")),
            "max_latency_ms": int(os.getenv("MAX_LATENCY_MS", "100")),
            "enable_batching": os.getenv("ENABLE_BATCHING", "true").lower() == "true",
            "cache_embeddings": os.getenv("CACHE_EMBEDDINGS", "true").lower() == "true",
        }

        # LLM-Specific Configuration
        self.llm_config = {
            "provider": os.getenv("LLM_PROVIDER", "openai"),
            "model": os.getenv("LLM_MODEL", "gpt-4"),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2048")),
            "request_timeout": int(os.getenv("LLM_TIMEOUT", "30")),
            "retry_attempts": int(os.getenv("LLM_RETRY_ATTEMPTS", "3")),
            "rate_limit_rpm": int(os.getenv("LLM_RATE_LIMIT_RPM", "60")),
        }

        # Monitoring & Observability
        self.metrics_config = {
            "enable_prometheus": os.getenv("ENABLE_PROMETHEUS", "true").lower()
            == "true",
            "enable_tracing": os.getenv("ENABLE_TRACING", "true").lower() == "true",
            "jaeger_endpoint": os.getenv("JAEGER_ENDPOINT", "http://jaeger:14268"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }

        # Cost Optimization Settings
        self.cost_optimization = {
            "enable_spot_instances": os.getenv("ENABLE_SPOT", "true").lower() == "true",
            "enable_autoscaling": os.getenv("ENABLE_AUTOSCALING", "true").lower()
            == "true",
            "min_replicas": int(os.getenv("MIN_REPLICAS", "1")),
            "max_replicas": int(os.getenv("MAX_REPLICAS", "10")),
            "target_gpu_utilization": float(os.getenv("TARGET_GPU_UTIL", "0.7")),
        }

    def get_model_serving_config(self, model_name: str) -> Dict[str, Any]:
        """Get model-specific serving configuration."""
        # This could be extended to fetch from a config service
        base_config = self.serving_config.copy()

        # Model-specific overrides
        model_overrides = os.getenv(f"MODEL_CONFIG_{model_name.upper()}")
        if model_overrides:
            base_config.update(json.loads(model_overrides))

        return base_config

    def get_kubernetes_resources(
        self, workload_type: str = "inference"
    ) -> Dict[str, Any]:
        """
        Get Kubernetes resource requirements based on workload type.
        Demonstrates understanding of ML workload resource planning.
        """
        resources = {
            "inference": {
                "requests": {
                    "memory": os.getenv("INFERENCE_MEMORY_REQUEST", "2Gi"),
                    "cpu": os.getenv("INFERENCE_CPU_REQUEST", "1"),
                    "nvidia.com/gpu": os.getenv("INFERENCE_GPU_REQUEST", "0"),
                },
                "limits": {
                    "memory": os.getenv("INFERENCE_MEMORY_LIMIT", "4Gi"),
                    "cpu": os.getenv("INFERENCE_CPU_LIMIT", "2"),
                    "nvidia.com/gpu": os.getenv("INFERENCE_GPU_LIMIT", "1"),
                },
            },
            "training": {
                "requests": {
                    "memory": os.getenv("TRAINING_MEMORY_REQUEST", "8Gi"),
                    "cpu": os.getenv("TRAINING_CPU_REQUEST", "4"),
                    "nvidia.com/gpu": os.getenv("TRAINING_GPU_REQUEST", "1"),
                },
                "limits": {
                    "memory": os.getenv("TRAINING_MEMORY_LIMIT", "16Gi"),
                    "cpu": os.getenv("TRAINING_CPU_LIMIT", "8"),
                    "nvidia.com/gpu": os.getenv("TRAINING_GPU_LIMIT", "2"),
                },
            },
            "embedding": {
                "requests": {
                    "memory": os.getenv("EMBEDDING_MEMORY_REQUEST", "4Gi"),
                    "cpu": os.getenv("EMBEDDING_CPU_REQUEST", "2"),
                },
                "limits": {
                    "memory": os.getenv("EMBEDDING_MEMORY_LIMIT", "8Gi"),
                    "cpu": os.getenv("EMBEDDING_CPU_LIMIT", "4"),
                },
            },
        }

        return resources.get(workload_type, resources["inference"])

    def validate_config(self) -> bool:
        """Validate configuration for production readiness."""
        validations = []

        # Check critical endpoints
        if self.llm_config["provider"] == "openai":
            validations.append(bool(os.getenv("OPENAI_API_KEY")))

        # Check resource limits make sense
        validations.append(
            self.cost_optimization["min_replicas"]
            <= self.cost_optimization["max_replicas"]
        )

        # Check GPU configuration
        if os.getenv("CUDA_VISIBLE_DEVICES"):
            validations.append(0 < self.gpu_memory_fraction <= 1.0)

        return all(validations)

    def export_helm_values(self) -> Dict[str, Any]:
        """Export configuration as Helm values for GitOps."""
        return {
            "ml": {
                "modelRegistry": {"uri": self.model_registry_uri},
                "vectorDB": {"url": self.vector_db_url},
                "serving": self.serving_config,
                "llm": self.llm_config,
                "monitoring": self.metrics_config,
                "costOptimization": self.cost_optimization,
            }
        }


# Global instance for easy import
ai_config = AIInfraConfig()


# Helper functions for common patterns
def get_model_serving_endpoint(model_name: str) -> str:
    """Get the serving endpoint for a specific model."""
    base_url = os.getenv("MODEL_SERVING_BASE_URL", "http://model-serving:8080")
    return f"{base_url}/v1/models/{model_name}/predict"


def get_embedding_service_config() -> Dict[str, Any]:
    """Get configuration for embedding service."""
    return {
        "model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "dimension": int(os.getenv("EMBEDDING_DIM", "384")),
        "batch_size": int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
        "cache_enabled": os.getenv("EMBEDDING_CACHE", "true").lower() == "true",
    }


def get_rag_pipeline_config() -> Dict[str, Any]:
    """Get configuration for RAG (Retrieval-Augmented Generation) pipeline."""
    return {
        "retriever": {
            "top_k": int(os.getenv("RAG_TOP_K", "10")),
            "similarity_threshold": float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7")),
        },
        "reranker": {
            "enabled": os.getenv("RAG_RERANKER_ENABLED", "true").lower() == "true",
            "model": os.getenv(
                "RAG_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
            ),
        },
        "generator": {
            "model": os.getenv("RAG_GENERATOR_MODEL", "gpt-3.5-turbo"),
            "max_context_length": int(os.getenv("RAG_MAX_CONTEXT", "4096")),
        },
    }
