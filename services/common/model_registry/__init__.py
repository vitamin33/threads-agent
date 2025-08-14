"""
Unified Model Registry for threads-agent project.

This package provides a consolidated approach to model registration, versioning,
and lifecycle management across all model types (prompts, vLLM, fine-tuned, etc.).

Key Features:
- Single source of truth for model management
- Pluggable adapter architecture for specialization
- Built-in MLflow integration with optimized client pooling
- Comprehensive validation and configuration management
- Performance optimizations (caching, async operations, batching)

Usage:
    from services.common.model_registry import get_unified_registry, ModelType
    
    registry = get_unified_registry()
    await registry.register_model("my-model", ModelType.VLLM_MODEL, config=config)
"""

from .core.base_registry import (
    ModelType,
    ModelStage, 
    ModelLoadState,
    BaseModelRegistry,
    UnifiedModelRegistry
)

from .core.configuration import (
    RegistryConfig,
    load_unified_config,
    get_registry_config
)

from .core.mlflow_client_manager import (
    MLflowClientManager,
    get_mlflow_client_manager
)

# Global registry instance
_unified_registry = None

def get_unified_registry(config: dict = None) -> UnifiedModelRegistry:
    """Get the global unified model registry instance."""
    global _unified_registry
    
    if _unified_registry is None:
        _unified_registry = UnifiedModelRegistry(config)
    
    return _unified_registry

def reset_unified_registry():
    """Reset the global registry instance (for testing)."""
    global _unified_registry
    _unified_registry = None

__all__ = [
    'ModelType',
    'ModelStage', 
    'ModelLoadState',
    'BaseModelRegistry',
    'UnifiedModelRegistry',
    'RegistryConfig',
    'get_unified_registry',
    'reset_unified_registry',
    'load_unified_config',
    'get_registry_config',
    'MLflowClientManager',
    'get_mlflow_client_manager'
]