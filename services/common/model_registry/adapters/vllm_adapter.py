"""
vLLM Model Registry Adapter.

This adapter provides vLLM-specific model management functionality within
the unified model registry framework. It consolidates and refactors the
functionality from services/vllm_service/model_registry.py while leveraging
the unified infrastructure.

Key Features:
- Apple Silicon optimization and memory management
- Multi-model concurrent serving with content type routing
- Dynamic model loading/unloading based on memory constraints
- Integration with unified MLflow tracking
- Content type routing (Twitter, LinkedIn, technical articles)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

from ..core.base_registry import (
    ModelStage,
    ModelLoadState,
    ModelRegistryError,
)

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content types for model routing."""

    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TECHNICAL_ARTICLES = "technical_articles"
    CODE_DOCUMENTATION = "code_documentation"
    GENERAL = "general"
    SPEED = "speed"
    LIGHTWEIGHT = "lightweight"


@dataclass
class MemoryRequirements:
    """Memory requirements for a model."""

    base_gb: float
    optimized_gb: float
    minimum_gb: float

    def get_target_memory(self, optimization_level: str = "optimized") -> float:
        """Get target memory based on optimization level."""
        if optimization_level == "maximum_performance":
            return self.base_gb
        elif optimization_level == "balanced":
            return self.optimized_gb
        elif optimization_level == "memory_optimized":
            return self.minimum_gb
        else:
            return self.optimized_gb


@dataclass
class OptimizationConfig:
    """Optimization configuration for Apple Silicon."""

    quantization: str = "fp16"
    backend: str = "metal"
    tensor_parallel: bool = False
    speculative_decoding: bool = False
    kv_cache_dtype: str = "fp8"
    mixed_precision: bool = False
    dynamic_batching: bool = False
    aggressive_caching: bool = False
    model_pruning: bool = False

    def to_vllm_kwargs(self) -> Dict[str, Any]:
        """Convert to vLLM initialization kwargs."""
        kwargs = {
            "dtype": self.quantization,
            "device": "mps" if self.backend == "metal" else "cpu",
            "tensor_parallel_size": 1,  # Single GPU for Apple Silicon
            "enable_prefix_caching": True,
            "use_v2_block_manager": True,
        }

        if self.kv_cache_dtype:
            kwargs["kv_cache_dtype"] = self.kv_cache_dtype

        if self.speculative_decoding:
            kwargs["speculative_model"] = None  # Can be configured per model

        return kwargs


@dataclass
class PerformanceTargets:
    """Performance targets for a model."""

    target_latency_ms: int
    max_tokens_per_request: int
    concurrent_requests: int
    tokens_per_second_target: Optional[int] = None


@dataclass
class VLLMModelConfig:
    """Configuration for a single vLLM model."""

    name: str
    display_name: str
    memory_requirements: MemoryRequirements
    content_types: List[ContentType]
    priority: int
    optimization: OptimizationConfig
    performance: PerformanceTargets
    model_id: str = field(default="")
    load_state: ModelLoadState = field(default=ModelLoadState.UNLOADED)
    last_used: Optional[datetime] = field(default=None)
    load_time: Optional[float] = field(default=None)
    error_count: int = field(default=0)

    def __post_init__(self):
        """Post-initialization processing."""
        if not self.model_id:
            self.model_id = self.name.replace("/", "_").replace("-", "_").lower()

        # Convert string content types to enum
        if self.content_types and isinstance(self.content_types[0], str):
            self.content_types = [ContentType(ct) for ct in self.content_types]


class VLLMAdapter:
    """
    vLLM model registry adapter for the unified registry.

    This adapter handles vLLM-specific concerns:
    - Apple Silicon optimization
    - Memory-aware model management
    - Content type routing
    - Dynamic loading/unloading
    """

    def __init__(self, unified_registry):
        """Initialize vLLM adapter."""
        self.registry = unified_registry
        self.models: Dict[str, VLLMModelConfig] = {}
        self.loaded_models: Dict[str, Any] = {}  # Actual vLLM model instances
        self.memory_usage: Dict[str, float] = {}
        self.total_memory_gb = 36.0  # M4 Max default
        self.memory_threshold = 0.85

        # Load vLLM-specific configuration
        self._load_vllm_config()

    def _load_vllm_config(self):
        """Load vLLM-specific configuration."""
        config_path = self._find_vllm_config_file()
        if config_path and YAML_AVAILABLE:
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)

                # Extract basic settings
                self.total_memory_gb = config.get("total_memory_gb", 36.0)
                self.memory_threshold = config.get("memory_safety_threshold", 0.85)

                # Load model configurations
                self._load_model_configs(config.get("models", {}))

                logger.info(f"Loaded vLLM configuration for {len(self.models)} models")

            except Exception as e:
                logger.error(f"Failed to load vLLM configuration: {e}")
                self._load_default_models()
        else:
            logger.warning("No vLLM configuration file found, using defaults")
            self._load_default_models()

    def _find_vllm_config_file(self) -> Optional[Path]:
        """Find vLLM configuration file."""
        potential_locations = [
            Path.cwd()
            / "services"
            / "vllm_service"
            / "config"
            / "multi_model_config.yaml",
            Path(__file__).parent.parent.parent.parent
            / "vllm_service"
            / "config"
            / "multi_model_config.yaml",
            Path.cwd() / "multi_model_config.yaml",
        ]

        for location in potential_locations:
            if location.exists():
                return location

        return None

    def _load_model_configs(self, models_config: Dict[str, Any]):
        """Load individual model configurations."""
        for model_id, model_data in models_config.items():
            try:
                # Create memory requirements
                mem_req = MemoryRequirements(**model_data["memory_requirements"])

                # Create optimization config
                opt_config = OptimizationConfig(**model_data["optimization"])

                # Create performance targets
                perf_targets = PerformanceTargets(**model_data["performance"])

                # Create model config
                model_config = VLLMModelConfig(
                    name=model_data["name"],
                    display_name=model_data["display_name"],
                    memory_requirements=mem_req,
                    content_types=model_data["content_types"],
                    priority=model_data["priority"],
                    optimization=opt_config,
                    performance=perf_targets,
                    model_id=model_id,
                )

                self.models[model_id] = model_config

            except Exception as e:
                logger.error(f"Failed to load config for model {model_id}: {e}")

    def _load_default_models(self):
        """Load default model configurations for the 5 target models."""
        default_models = {
            "llama_8b": {
                "name": "meta-llama/Llama-3.1-8B-Instruct",
                "display_name": "Llama 3.1 8B Instruct",
                "memory_requirements": {
                    "base_gb": 16.0,
                    "optimized_gb": 12.0,
                    "minimum_gb": 10.0,
                },
                "content_types": ["general", "linkedin", "technical_articles"],
                "priority": 1,
                "optimization": {"quantization": "fp16", "backend": "metal"},
                "performance": {
                    "target_latency_ms": 40,
                    "max_tokens_per_request": 2048,
                    "concurrent_requests": 3,
                },
            },
            "qwen_7b": {
                "name": "Qwen/Qwen2.5-7B-Instruct",
                "display_name": "Qwen 2.5 7B Instruct",
                "memory_requirements": {
                    "base_gb": 14.0,
                    "optimized_gb": 10.0,
                    "minimum_gb": 8.0,
                },
                "content_types": ["technical_articles", "code_documentation"],
                "priority": 2,
                "optimization": {"quantization": "fp16", "backend": "metal"},
                "performance": {
                    "target_latency_ms": 35,
                    "max_tokens_per_request": 4096,
                    "concurrent_requests": 3,
                },
            },
            "mistral_7b": {
                "name": "mistralai/Mistral-7B-Instruct-v0.3",
                "display_name": "Mistral 7B Instruct v0.3",
                "memory_requirements": {
                    "base_gb": 14.0,
                    "optimized_gb": 10.0,
                    "minimum_gb": 8.0,
                },
                "content_types": ["twitter", "general"],
                "priority": 3,
                "optimization": {"quantization": "fp16", "backend": "metal"},
                "performance": {
                    "target_latency_ms": 30,
                    "max_tokens_per_request": 1024,
                    "concurrent_requests": 4,
                },
            },
            "llama_3b": {
                "name": "meta-llama/Llama-3.1-3B-Instruct",
                "display_name": "Llama 3.1 3B Instruct",
                "memory_requirements": {
                    "base_gb": 6.0,
                    "optimized_gb": 4.0,
                    "minimum_gb": 3.0,
                },
                "content_types": ["twitter", "speed"],
                "priority": 4,
                "optimization": {"quantization": "fp16", "backend": "metal"},
                "performance": {
                    "target_latency_ms": 20,
                    "max_tokens_per_request": 512,
                    "concurrent_requests": 8,
                },
            },
            "phi_mini": {
                "name": "microsoft/Phi-3.5-mini-instruct",
                "display_name": "Phi 3.5 Mini Instruct",
                "memory_requirements": {
                    "base_gb": 8.0,
                    "optimized_gb": 6.0,
                    "minimum_gb": 4.0,
                },
                "content_types": ["lightweight", "general"],
                "priority": 5,
                "optimization": {"quantization": "int8", "backend": "metal"},
                "performance": {
                    "target_latency_ms": 15,
                    "max_tokens_per_request": 1024,
                    "concurrent_requests": 6,
                },
            },
        }

        self._load_model_configs(default_models)

    async def register_model(
        self, name: str, metadata: Dict[str, Any], **kwargs
    ) -> str:
        """Register a vLLM model."""
        # For vLLM models, we typically register configurations rather than actual model files
        model_id = kwargs.get(
            "model_id", name.replace("/", "_").replace("-", "_").lower()
        )

        # Create model configuration from metadata
        config = VLLMModelConfig(
            name=name,
            display_name=metadata.get("display_name", name),
            memory_requirements=MemoryRequirements(
                **metadata.get(
                    "memory_requirements",
                    {"base_gb": 8.0, "optimized_gb": 6.0, "minimum_gb": 4.0},
                )
            ),
            content_types=[
                ContentType(ct) for ct in metadata.get("content_types", ["general"])
            ],
            priority=metadata.get("priority", 99),
            optimization=OptimizationConfig(**metadata.get("optimization", {})),
            performance=PerformanceTargets(
                **metadata.get(
                    "performance",
                    {
                        "target_latency_ms": 50,
                        "max_tokens_per_request": 1024,
                        "concurrent_requests": 1,
                    },
                )
            ),
            model_id=model_id,
        )

        self.models[model_id] = config

        # Log to unified MLflow if enabled
        if self.registry.config.mlflow.enabled:
            await self._log_vllm_registration(model_id, config)

        logger.info(f"Registered vLLM model: {name} -> {model_id}")
        return model_id

    async def promote_model(
        self,
        model_id: str,
        target_stage: ModelStage,
        validation_results: Optional[Dict] = None,
    ) -> bool:
        """Promote a vLLM model through stages."""
        if model_id not in self.models:
            raise ModelRegistryError(f"vLLM model not found: {model_id}")

        config = self.models[model_id]

        # For vLLM models, promotion means changing load state or deployment configuration
        if target_stage == ModelStage.PRODUCTION:
            # Load the model if not already loaded
            success = await self.load_model(model_id)
            if success:
                config.load_state = ModelLoadState.LOADED
                logger.info(f"Promoted vLLM model {model_id} to production (loaded)")
                return True
        elif target_stage == ModelStage.STAGING:
            # Validate model configuration
            validation_success = await self._validate_model_config(model_id)
            if validation_success:
                logger.info(f"Promoted vLLM model {model_id} to staging")
                return True
        elif target_stage == ModelStage.DEPRECATED:
            # Unload the model
            await self.unload_model(model_id)
            config.load_state = ModelLoadState.UNLOADED
            logger.info(f"Deprecated vLLM model {model_id} (unloaded)")
            return True

        return False

    async def get_model(
        self, model_identifier: Union[str, Dict[str, Any]]
    ) -> Optional[VLLMModelConfig]:
        """Get vLLM model configuration."""
        if isinstance(model_identifier, str):
            return self.models.get(model_identifier)

        # Search by criteria
        for model_config in self.models.values():
            if all(
                getattr(model_config, key, None) == value
                for key, value in model_identifier.items()
                if hasattr(model_config, key)
            ):
                return model_config

        return None

    async def list_models(
        self, stage: Optional[ModelStage] = None, **filters
    ) -> List[Dict[str, Any]]:
        """List vLLM models with optional filtering."""
        results = []

        for model_id, config in self.models.items():
            # Apply stage filter
            if (
                stage
                and stage == ModelStage.PRODUCTION
                and config.load_state != ModelLoadState.LOADED
            ):
                continue
            if (
                stage
                and stage == ModelStage.DEPRECATED
                and config.load_state != ModelLoadState.UNLOADED
            ):
                continue

            # Apply other filters
            if filters:
                if "content_type" in filters:
                    content_type = ContentType(filters["content_type"])
                    if content_type not in config.content_types:
                        continue

                if "priority_max" in filters:
                    if config.priority > filters["priority_max"]:
                        continue

            model_info = {
                "id": model_id,
                "name": config.name,
                "display_name": config.display_name,
                "type": "vllm_model",
                "load_state": config.load_state.value,
                "priority": config.priority,
                "content_types": [ct.value for ct in config.content_types],
                "memory_usage_gb": self.memory_usage.get(model_id, 0),
                "last_used": config.last_used.isoformat() if config.last_used else None,
                "performance_targets": {
                    "target_latency_ms": config.performance.target_latency_ms,
                    "max_tokens_per_request": config.performance.max_tokens_per_request,
                },
            }

            results.append(model_info)

        return results

    async def load_model(self, model_id: str) -> bool:
        """Load a vLLM model into memory."""
        if model_id not in self.models:
            raise ModelRegistryError(f"Model configuration not found: {model_id}")

        config = self.models[model_id]

        if config.load_state == ModelLoadState.LOADED:
            return True  # Already loaded

        # Check memory constraints
        required_memory = config.memory_requirements.optimized_gb
        if not self._can_load_model_memory(required_memory):
            # Try to free up memory
            models_to_unload = self._get_models_to_unload_for_memory(required_memory)
            for unload_id in models_to_unload:
                await self.unload_model(unload_id)

        if not self._can_load_model_memory(required_memory):
            logger.error(f"Insufficient memory to load model {model_id}")
            return False

        try:
            config.load_state = ModelLoadState.LOADING
            start_time = asyncio.get_event_loop().time()

            # Simulate model loading (in real implementation, this would load vLLM model)
            await asyncio.sleep(0.1)  # Simulate loading time

            # Update state
            config.load_state = ModelLoadState.LOADED
            config.load_time = asyncio.get_event_loop().time() - start_time
            config.last_used = datetime.now()
            config.error_count = 0

            # Track memory usage
            self.memory_usage[model_id] = required_memory

            logger.info(f"Successfully loaded vLLM model: {model_id}")
            return True

        except Exception as e:
            config.load_state = ModelLoadState.ERROR
            config.error_count += 1
            logger.error(f"Failed to load vLLM model {model_id}: {e}")
            return False

    async def unload_model(self, model_id: str) -> bool:
        """Unload a vLLM model from memory."""
        if model_id not in self.models:
            return False

        config = self.models[model_id]

        if config.load_state != ModelLoadState.LOADED:
            return True  # Already unloaded

        try:
            config.load_state = ModelLoadState.UNLOADING

            # Simulate model unloading
            await asyncio.sleep(0.05)

            # Update state
            config.load_state = ModelLoadState.UNLOADED
            self.memory_usage.pop(model_id, None)

            # Remove from loaded models
            self.loaded_models.pop(model_id, None)

            logger.info(f"Successfully unloaded vLLM model: {model_id}")
            return True

        except Exception as e:
            config.load_state = ModelLoadState.ERROR
            logger.error(f"Failed to unload vLLM model {model_id}: {e}")
            return False

    def get_model_for_content_type(
        self, content_type: ContentType
    ) -> Optional[VLLMModelConfig]:
        """Get the best model for a specific content type."""
        # Find models that support this content type and are loaded
        available_models = [
            model
            for model in self.models.values()
            if content_type in model.content_types
            and model.load_state == ModelLoadState.LOADED
        ]

        if available_models:
            # Return highest priority (lowest number) model
            return min(available_models, key=lambda m: m.priority)

        return None

    def _can_load_model_memory(self, required_memory: float) -> bool:
        """Check if model can be loaded given memory constraints."""
        current_usage = sum(self.memory_usage.values())
        available_memory = (
            self.total_memory_gb * self.memory_threshold
        ) - current_usage
        return available_memory >= required_memory

    def _get_models_to_unload_for_memory(self, required_memory: float) -> List[str]:
        """Get models that should be unloaded to free up required memory."""
        current_usage = sum(self.memory_usage.values())
        max_usable = self.total_memory_gb * self.memory_threshold
        available = max_usable - current_usage

        if available >= required_memory:
            return []

        need_to_free = required_memory - available

        # Get loaded models sorted by priority (higher priority = lower number = keep longer)
        loaded_models = [
            (model_id, config)
            for model_id, config in self.models.items()
            if config.load_state == ModelLoadState.LOADED
        ]

        # Sort by priority (higher number = unload first)
        loaded_models.sort(key=lambda x: x[1].priority, reverse=True)

        models_to_unload = []
        freed_memory = 0.0

        for model_id, config in loaded_models:
            if freed_memory >= need_to_free:
                break

            models_to_unload.append(model_id)
            freed_memory += self.memory_usage.get(model_id, 0)

        return models_to_unload

    async def _validate_model_config(self, model_id: str) -> bool:
        """Validate model configuration."""
        if model_id not in self.models:
            return False

        config = self.models[model_id]

        # Basic validation checks
        if not config.name or not config.display_name:
            return False

        if config.memory_requirements.minimum_gb <= 0:
            return False

        if config.priority < 1:
            return False

        return True

    async def _log_vllm_registration(self, model_id: str, config: VLLMModelConfig):
        """Log vLLM model registration to MLflow."""
        try:
            client = await self.registry.client_manager.get_client_async()

            # Use MLflow to log model registration
            import mlflow

            experiment_name = f"vllm_models_{self.registry.config.registry_name}"
            mlflow.set_experiment(experiment_name)

            with mlflow.start_run():
                # Log model metadata
                mlflow.log_param("model_name", config.name)
                mlflow.log_param("model_id", model_id)
                mlflow.log_param("display_name", config.display_name)
                mlflow.log_param("priority", config.priority)
                mlflow.log_param(
                    "content_types", ",".join([ct.value for ct in config.content_types])
                )

                # Log memory requirements
                mlflow.log_param("memory_base_gb", config.memory_requirements.base_gb)
                mlflow.log_param(
                    "memory_optimized_gb", config.memory_requirements.optimized_gb
                )
                mlflow.log_param(
                    "memory_minimum_gb", config.memory_requirements.minimum_gb
                )

                # Log performance targets
                mlflow.log_param(
                    "target_latency_ms", config.performance.target_latency_ms
                )
                mlflow.log_param(
                    "max_tokens_per_request", config.performance.max_tokens_per_request
                )
                mlflow.log_param(
                    "concurrent_requests", config.performance.concurrent_requests
                )

                # Log optimization settings
                mlflow.log_param("quantization", config.optimization.quantization)
                mlflow.log_param("backend", config.optimization.backend)

                # Log metrics
                mlflow.log_metric("registration_timestamp", datetime.now().timestamp())

        except Exception as e:
            logger.warning(f"Failed to log vLLM registration to MLflow: {e}")

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get memory usage summary."""
        total_used = sum(self.memory_usage.values())
        max_usable = self.total_memory_gb * self.memory_threshold

        return {
            "total_memory_gb": self.total_memory_gb,
            "memory_threshold": self.memory_threshold,
            "max_usable_gb": max_usable,
            "current_usage_gb": total_used,
            "available_gb": max_usable - total_used,
            "utilization_percent": (total_used / max_usable) * 100
            if max_usable > 0
            else 0,
            "loaded_models": len(
                [
                    m
                    for m in self.models.values()
                    if m.load_state == ModelLoadState.LOADED
                ]
            ),
            "total_models": len(self.models),
        }
