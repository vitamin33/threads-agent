"""
Unified vLLM Model Registry.

This module replaces the original model_registry.py and provides a clean
interface to the unified model registry infrastructure while preserving
all vLLM-specific functionality.

Key Features:
- Leverages unified model registry infrastructure
- Maintains backward compatibility with existing vLLM service code
- Provides vLLM-specific convenience functions
- Integrates seamlessly with existing MLflow infrastructure
"""

import logging
from typing import Dict, List, Optional, Any, Union

# Import from unified model registry
from services.common.model_registry import (
    get_unified_registry,
    ModelType,
    ModelStage,
    ModelLoadState,
)

from services.common.model_registry.adapters.vllm_adapter import (
    VLLMAdapter,
    ContentType,
    VLLMModelConfig,
)

logger = logging.getLogger(__name__)

# Global registry instance for backward compatibility
_vllm_registry_instance: Optional["VLLMModelRegistry"] = None


class VLLMModelRegistry:
    """
    vLLM Model Registry using unified infrastructure.

    This class provides a vLLM-specific interface to the unified model registry
    while maintaining backward compatibility with existing code.
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize vLLM model registry."""
        self.unified_registry = get_unified_registry(config)

        # Ensure vLLM adapter is registered
        if ModelType.VLLM_MODEL not in self.unified_registry.adapters:
            vllm_adapter = VLLMAdapter(self.unified_registry)
            self.unified_registry.register_adapter(ModelType.VLLM_MODEL, vllm_adapter)

        self.vllm_adapter = self.unified_registry.get_adapter(ModelType.VLLM_MODEL)

    @property
    def models(self) -> Dict[str, VLLMModelConfig]:
        """Get all vLLM model configurations."""
        return self.vllm_adapter.models

    @property
    def loaded_models(self) -> Dict[str, Any]:
        """Get loaded model instances."""
        return self.vllm_adapter.loaded_models

    @property
    def memory_usage(self) -> Dict[str, float]:
        """Get current memory usage by model."""
        return self.vllm_adapter.memory_usage

    @property
    def total_memory_gb(self) -> float:
        """Get total available memory."""
        return self.vllm_adapter.total_memory_gb

    @property
    def memory_threshold(self) -> float:
        """Get memory safety threshold."""
        return self.vllm_adapter.memory_threshold

    # Convenience methods for backward compatibility

    def get_model_config(self, model_id: str) -> Optional[VLLMModelConfig]:
        """Get configuration for a specific model."""
        return self.vllm_adapter.models.get(model_id)

    def get_models_by_content_type(
        self, content_type: ContentType
    ) -> List[VLLMModelConfig]:
        """Get models that support a specific content type."""
        return [
            model
            for model in self.vllm_adapter.models.values()
            if content_type in model.content_types
        ]

    def get_model_for_content_type(
        self, content_type: ContentType
    ) -> Optional[VLLMModelConfig]:
        """Get the best model for a specific content type."""
        return self.vllm_adapter.get_model_for_content_type(content_type)

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage by model."""
        return self.vllm_adapter.memory_usage.copy()

    def get_total_memory_usage(self) -> float:
        """Get total memory usage across all loaded models."""
        return sum(self.vllm_adapter.memory_usage.values())

    def get_available_memory(self) -> float:
        """Get available memory for new models."""
        used_memory = self.get_total_memory_usage()
        max_usable = self.total_memory_gb * self.memory_threshold
        return max(0, max_usable - used_memory)

    def can_load_model(
        self, model_id: str, optimization_level: str = "optimized"
    ) -> bool:
        """Check if a model can be loaded given current memory constraints."""
        model_config = self.get_model_config(model_id)
        if not model_config:
            return False

        if model_config.load_state == ModelLoadState.LOADED:
            return True  # Already loaded

        required_memory = model_config.memory_requirements.get_target_memory(
            optimization_level
        )
        available_memory = self.get_available_memory()

        return available_memory >= required_memory

    def get_models_to_unload_for_memory(self, required_memory: float) -> List[str]:
        """Get models that should be unloaded to free up required memory."""
        return self.vllm_adapter._get_models_to_unload_for_memory(required_memory)

    def update_model_state(
        self, model_id: str, state: ModelLoadState, **kwargs
    ) -> None:
        """Update model state and metadata."""
        if model_id not in self.vllm_adapter.models:
            logger.warning(f"Unknown model ID: {model_id}")
            return

        model_config = self.vllm_adapter.models[model_id]
        model_config.load_state = state

        # Update additional metadata
        if "load_time" in kwargs:
            model_config.load_time = kwargs["load_time"]

        if "error_count" in kwargs:
            model_config.error_count = kwargs["error_count"]

        if state == ModelLoadState.LOADED:
            from datetime import datetime

            model_config.last_used = datetime.now()

        # Update memory usage
        if "memory_usage" in kwargs:
            self.vllm_adapter.memory_usage[model_id] = kwargs["memory_usage"]
        elif state == ModelLoadState.UNLOADED:
            self.vllm_adapter.memory_usage.pop(model_id, None)

    def get_loading_priority_order(self) -> List[str]:
        """Get the order in which models should be loaded."""
        # Sort models by priority
        models_by_priority = sorted(
            self.vllm_adapter.models.items(), key=lambda x: x[1].priority
        )
        return [model_id for model_id, _ in models_by_priority]

    def get_apple_silicon_optimization(
        self, preset: str = "balanced"
    ) -> Dict[str, Any]:
        """Get Apple Silicon optimization settings for a preset."""
        # Default presets (could be loaded from config)
        presets = {
            "maximum_performance": {
                "gpu_memory_utilization": 0.9,
                "cpu_offload_layers": 0,
                "quantization": "fp16",
            },
            "balanced": {
                "gpu_memory_utilization": 0.8,
                "cpu_offload_layers": 2,
                "quantization": "fp16",
            },
            "memory_optimized": {
                "gpu_memory_utilization": 0.7,
                "cpu_offload_layers": 4,
                "quantization": "int8",
            },
        }

        return presets.get(preset, presets.get("balanced", {}))

    def get_content_routing_config(self, content_type: ContentType) -> Dict[str, Any]:
        """Get routing configuration for a content type."""
        # Default routing configuration
        routing_config = {
            ContentType.TWITTER: {
                "primary": ["mistral_7b", "llama_3b"],
                "fallback": ["phi_mini"],
                "max_tokens": 280,
            },
            ContentType.LINKEDIN: {
                "primary": ["llama_8b", "qwen_7b"],
                "fallback": ["mistral_7b"],
                "max_tokens": 3000,
            },
            ContentType.TECHNICAL_ARTICLES: {
                "primary": ["qwen_7b", "llama_8b"],
                "fallback": ["mistral_7b"],
                "max_tokens": 10000,
            },
            ContentType.CODE_DOCUMENTATION: {
                "primary": ["qwen_7b"],
                "fallback": ["llama_8b", "phi_mini"],
                "max_tokens": 5000,
            },
            ContentType.GENERAL: {
                "primary": ["llama_8b"],
                "fallback": ["qwen_7b", "mistral_7b"],
                "max_tokens": 2048,
            },
        }

        return routing_config.get(content_type, {})

    async def log_to_mlflow(
        self,
        model_id: str,
        metrics: Dict[str, float],
        parameters: Dict[str, Any] = None,
    ) -> None:
        """Log metrics and parameters to MLflow."""
        try:
            # Use unified registry's MLflow integration
            await self.unified_registry._log_registration_event(
                model_id, ModelType.VLLM_MODEL, {**(parameters or {}), **metrics}
            )

        except Exception as e:
            logger.warning(f"Failed to log to MLflow: {e}")

    def get_model_summary(self) -> Dict[str, Any]:
        """Get a summary of all models and their current states."""
        memory_summary = self.vllm_adapter.get_memory_summary()

        summary = {
            "total_models": len(self.vllm_adapter.models),
            "loaded_models": len(
                [
                    m
                    for m in self.vllm_adapter.models.values()
                    if m.load_state == ModelLoadState.LOADED
                ]
            ),
            **memory_summary,
            "models": {},
        }

        for model_id, model_config in self.vllm_adapter.models.items():
            summary["models"][model_id] = {
                "name": model_config.name,
                "display_name": model_config.display_name,
                "state": model_config.load_state.value,
                "priority": model_config.priority,
                "memory_usage_gb": self.vllm_adapter.memory_usage.get(model_id, 0),
                "content_types": [ct.value for ct in model_config.content_types],
                "last_used": model_config.last_used.isoformat()
                if model_config.last_used
                else None,
                "load_time": model_config.load_time,
                "error_count": model_config.error_count,
            }

        return summary

    def validate_configuration(self) -> List[str]:
        """Validate the configuration and return any errors."""
        errors = []

        # Check total memory requirements
        total_min_memory = sum(
            model.memory_requirements.minimum_gb
            for model in self.vllm_adapter.models.values()
        )

        if total_min_memory > self.total_memory_gb * self.memory_threshold:
            errors.append(
                f"Total minimum memory requirement ({total_min_memory:.1f}GB) exceeds available memory ({self.total_memory_gb * self.memory_threshold:.1f}GB)"
            )

        # Check model priorities are unique
        priorities = [model.priority for model in self.vllm_adapter.models.values()]
        if len(priorities) != len(set(priorities)):
            errors.append("Model priorities must be unique")

        # Check content type routing
        for content_type in ContentType:
            routing = self.get_content_routing_config(content_type)
            if routing:
                primary_models = routing.get("primary", [])
                for model_id in primary_models:
                    if model_id not in self.vllm_adapter.models:
                        errors.append(
                            f"Unknown model '{model_id}' in routing for '{content_type.value}'"
                        )

        return errors

    # Async methods for compatibility with unified registry

    async def load_model(self, model_id: str) -> bool:
        """Load a model asynchronously."""
        return await self.vllm_adapter.load_model(model_id)

    async def unload_model(self, model_id: str) -> bool:
        """Unload a model asynchronously."""
        return await self.vllm_adapter.unload_model(model_id)

    async def register_model(
        self, name: str, metadata: Dict[str, Any], **kwargs
    ) -> str:
        """Register a new model."""
        return await self.unified_registry.register_model(
            name, ModelType.VLLM_MODEL, metadata, **kwargs
        )

    async def promote_model(
        self,
        model_id: str,
        target_stage: ModelStage,
        validation_results: Optional[Dict] = None,
    ) -> bool:
        """Promote a model through stages."""
        return await self.unified_registry.promote_model(
            model_id, target_stage, validation_results
        )


# Global functions for backward compatibility


def get_model_registry(config_path: Optional[str] = None) -> VLLMModelRegistry:
    """Get the global vLLM model registry instance."""
    global _vllm_registry_instance

    if _vllm_registry_instance is None:
        config = None
        if config_path:
            # Load config from path if provided
            import yaml

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

        _vllm_registry_instance = VLLMModelRegistry(config)

    return _vllm_registry_instance


def reset_model_registry() -> None:
    """Reset the global model registry instance (for testing)."""
    global _vllm_registry_instance
    _vllm_registry_instance = None


# Convenience functions for backward compatibility


def get_model_config(model_id: str) -> Optional[VLLMModelConfig]:
    """Get configuration for a specific model."""
    return get_model_registry().get_model_config(model_id)


def get_model_for_content_type(
    content_type: Union[ContentType, str],
) -> Optional[VLLMModelConfig]:
    """Get the best model for a specific content type."""
    if isinstance(content_type, str):
        content_type = ContentType(content_type)
    return get_model_registry().get_model_for_content_type(content_type)


def get_models_by_priority() -> List[VLLMModelConfig]:
    """Get all models sorted by priority."""
    registry = get_model_registry()
    return sorted(registry.vllm_adapter.models.values(), key=lambda m: m.priority)
