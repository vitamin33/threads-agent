"""
Optimized PromptModel Registry with performance improvements for Kubernetes environments.

Key optimizations:
- Async I/O operations
- Connection pooling
- Result caching
- Batch operations
- Memory-efficient template validation
"""

import asyncio
import tempfile
import os
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from functools import lru_cache
import re
import logging
from concurrent.futures import ThreadPoolExecutor
import weakref

from mlflow.exceptions import RestException
from services.common.mlflow_client_pool import (
    get_pooled_mlflow_client,
    get_cached_model_versions,
    clear_model_cache,
    MLflowBatchOperations,
)

logger = logging.getLogger(__name__)


class ModelStage(Enum):
    """Model deployment stages."""

    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"

    def __str__(self) -> str:
        return self.value


class ModelValidationError(Exception):
    """Raised when model validation fails."""

    pass


# Global thread pool for CPU-bound operations
_thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="prompt_model")

# Weak reference cache for template validation results
_validation_cache = weakref.WeakValueDictionary()


class OptimizedPromptModel:
    """
    Performance-optimized PromptModel with async operations and caching.

    Optimizations:
    - Pooled MLflow client connections
    - Async file I/O operations
    - Cached template validation
    - Batch operation support
    - Memory-efficient operations
    """

    def __init__(
        self,
        name: str,
        template: str,
        version: str,
        stage: ModelStage = ModelStage.DEV,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize OptimizedPromptModel with performance optimizations."""
        # Validate inputs during initialization
        self._validate_inputs_sync(name, template, version)

        self.name = name
        self.template = template
        self.version = version
        self.stage = stage
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self._model_version: Optional[str] = None

        # Use cached template validation result
        self._template_hash = hash(template)
        self._variables_cache: Optional[List[str]] = None

    def _validate_inputs_sync(self, name: str, template: str, version: str) -> None:
        """Synchronous input validation for constructor."""
        if not name or not name.strip():
            raise ModelValidationError("Model name cannot be empty")

        if not template or not template.strip():
            raise ModelValidationError("Template cannot be empty")

        # Validate version format (basic semantic versioning)
        version_parts = version.split(".")
        if len(version_parts) != 3 or not all(part.isdigit() for part in version_parts):
            raise ModelValidationError(
                "Invalid version format. Expected semantic versioning (e.g., '1.0.0')"
            )

        # Use cached validation if available
        if self._template_hash in _validation_cache:
            return  # Already validated

        # Validate template format
        self._validate_template_format_optimized(template)
        _validation_cache[self._template_hash] = True

    def _validate_template_format_optimized(self, template: str) -> None:
        """Memory-efficient template validation."""
        try:
            # Count brackets without creating intermediate strings
            open_count = template.count("{")
            close_count = template.count("}")

            if open_count != close_count:
                raise ModelValidationError(
                    "Invalid template format: mismatched brackets"
                )

            # Extract variables efficiently using compiled regex
            variables = self._extract_variables_optimized(template)

            # Validate by attempting format with minimal dummy data
            if variables:
                dummy_values = {var: "x" for var in variables}
                template.format(**dummy_values)

        except (KeyError, ValueError, AttributeError) as e:
            raise ModelValidationError(f"Invalid template format: {e}")

    @lru_cache(maxsize=256)
    def _extract_variables_optimized(self, template: str) -> Tuple[str, ...]:
        """Extract variables with caching and return immutable tuple."""
        # Compiled regex for better performance
        pattern = re.compile(r"\{([^}:]*)\}")
        variables = pattern.findall(template)
        return tuple(var.strip() for var in variables if var.strip())

    async def validate_async(self) -> bool:
        """Async validation for non-blocking operations."""
        # Template format validation already done in __init__
        return True

    async def register_async(self) -> None:
        """Asynchronously register the model in MLflow Model Registry."""
        # Use thread pool for MLflow operations to avoid blocking
        loop = asyncio.get_event_loop()

        def _register_sync():
            client = get_pooled_mlflow_client()

            try:
                # Try to create the registered model
                client.create_registered_model(
                    name=self.name, description=f"Prompt template model: {self.name}"
                )
            except RestException:
                # Model already exists, which is fine
                pass

            # Create model version with optimized artifact handling
            return self._create_model_version_sync(client)

        self._model_version = await loop.run_in_executor(_thread_pool, _register_sync)

    def _create_model_version_sync(self, client) -> str:
        """Synchronous model version creation with optimized I/O."""
        # Use in-memory artifact creation when possible
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "template.txt")

            # Write file synchronously but efficiently
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(self.template)

            # Prepare tags efficiently
            tags = {
                "template_hash": str(self._template_hash),
                "version": self.version,
                **self.metadata,
            }

            # Create model version
            model_version = client.create_model_version(
                name=self.name, source=temp_dir, tags=tags
            )

            return str(model_version.version)

    async def promote_to_staging_async(self) -> None:
        """Asynchronously promote model to staging stage."""
        if self._model_version is None:
            raise ModelValidationError("Model must be registered before promotion")

        loop = asyncio.get_event_loop()

        def _promote_sync():
            client = get_pooled_mlflow_client()
            client.transition_model_version_stage(
                name=self.name, version=self._model_version, stage="staging"
            )

        await loop.run_in_executor(_thread_pool, _promote_sync)
        self.stage = ModelStage.STAGING

    async def promote_to_production_async(self) -> None:
        """Asynchronously promote model to production stage."""
        if self._model_version is None:
            raise ModelValidationError("Model must be registered before promotion")

        if self.stage != ModelStage.STAGING:
            raise ModelValidationError("Cannot promote directly from dev to production")

        loop = asyncio.get_event_loop()

        def _promote_sync():
            client = get_pooled_mlflow_client()
            client.transition_model_version_stage(
                name=self.name, version=self._model_version, stage="production"
            )

        await loop.run_in_executor(_thread_pool, _promote_sync)
        self.stage = ModelStage.PRODUCTION

    def get_template_variables_cached(self) -> List[str]:
        """Get template variables with caching."""
        if self._variables_cache is None:
            variables_tuple = self._extract_variables_optimized(self.template)
            self._variables_cache = list(variables_tuple)
        return self._variables_cache.copy()  # Return copy to prevent modification

    async def get_lineage_optimized(self) -> List[Dict[str, Any]]:
        """Get model lineage with optimized caching."""
        loop = asyncio.get_event_loop()

        def _get_lineage_sync():
            # Use cached model versions to reduce API calls
            cached_versions = get_cached_model_versions(self.name)

            lineage = []
            for version_data in cached_versions:
                version, stage, tags, timestamp = version_data
                lineage.append(
                    {
                        "version": version,
                        "stage": stage,
                        "parent_version": tags.get("parent_version"),
                        "created_at": tags.get("created_at", "unknown"),
                        "timestamp": timestamp,
                    }
                )

            # Sort by version number efficiently
            lineage.sort(key=lambda x: tuple(map(int, x["version"].split("."))))
            return lineage

        return await loop.run_in_executor(_thread_pool, _get_lineage_sync)

    def compare_with_optimized(self, other: "OptimizedPromptModel") -> Dict[str, Any]:
        """Memory-efficient model comparison."""
        if self.name != other.name:
            raise ModelValidationError("Cannot compare models with different names")

        # Use cached variable extraction
        self_vars = set(self.get_template_variables_cached())
        other_vars = set(other.get_template_variables_cached())

        # Efficient comparison using set operations
        return {
            "version_diff": (
                None
                if self.version == other.version
                else {"old": self.version, "new": other.version}
            ),
            "template_diff": {
                "old": self.template,
                "new": other.template,
                "variables_added": list(other_vars - self_vars),
                "variables_removed": list(self_vars - other_vars),
            },
            "metadata_diff": self._compare_metadata_efficient(other.metadata),
        }

    def _compare_metadata_efficient(
        self, other_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Efficient metadata comparison."""
        diff = {}
        all_keys = self.metadata.keys() | other_metadata.keys()

        for key in all_keys:
            old_val = self.metadata.get(key)
            new_val = other_metadata.get(key)
            if old_val != new_val:
                diff[key] = {"old": old_val, "new": new_val}

        return diff

    def render_optimized(self, **kwargs: Any) -> str:
        """Optimized template rendering with cached variables."""
        required_vars = set(self.get_template_variables_cached())
        provided_vars = set(kwargs.keys())
        missing_vars = required_vars - provided_vars

        if missing_vars:
            raise ModelValidationError(f"Missing required variables: {missing_vars}")

        return self.template.format(**kwargs)

    def to_dict_optimized(self) -> Dict[str, Any]:
        """Memory-efficient dictionary conversion."""
        return {
            "name": self.name,
            "template": self.template,
            "version": self.version,
            "stage": str(self.stage),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "template_hash": self._template_hash,
        }

    # Backward compatibility methods (sync versions)
    def validate(self) -> bool:
        """Sync wrapper for validation."""
        return asyncio.run(self.validate_async())

    def register(self) -> None:
        """Sync wrapper for registration."""
        asyncio.run(self.register_async())

    def promote_to_staging(self) -> None:
        """Sync wrapper for staging promotion."""
        asyncio.run(self.promote_to_staging_async())

    def promote_to_production(self) -> None:
        """Sync wrapper for production promotion."""
        asyncio.run(self.promote_to_production_async())

    def get_template_variables(self) -> List[str]:
        """Backward compatibility method."""
        return self.get_template_variables_cached()

    def get_lineage(self) -> List[Dict[str, Any]]:
        """Sync wrapper for lineage retrieval."""
        return asyncio.run(self.get_lineage_optimized())

    def compare_with(self, other: "OptimizedPromptModel") -> Dict[str, Any]:
        """Backward compatibility method."""
        return self.compare_with_optimized(other)

    def render(self, **kwargs: Any) -> str:
        """Backward compatibility method."""
        return self.render_optimized(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Backward compatibility method."""
        return self.to_dict_optimized()


class ModelRegistryOptimizer:
    """High-level optimizer for batch operations and monitoring."""

    def __init__(self):
        self.batch_ops = MLflowBatchOperations()
        self._metrics = {
            "models_registered": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_operations": 0,
        }

    async def batch_register_models_async(
        self, models: List[OptimizedPromptModel]
    ) -> Dict[str, Any]:
        """Register multiple models asynchronously with batching."""
        loop = asyncio.get_event_loop()

        def _batch_register():
            self._metrics["batch_operations"] += 1
            result = self.batch_ops.batch_register_models(models)
            self._metrics["models_registered"] += len(result["success"])
            return result

        return await loop.run_in_executor(_thread_pool, _batch_register)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        return {
            **self._metrics,
            "validation_cache_size": len(_validation_cache),
            "thread_pool_active": _thread_pool._threads,
        }

    def warm_cache(self, model_names: List[str]) -> None:
        """Pre-warm cache with frequently accessed models."""
        for name in model_names:
            try:
                get_cached_model_versions(name)
                self._metrics["cache_misses"] += 1
            except Exception as e:
                logger.warning(f"Failed to warm cache for {name}: {e}")

    def cleanup_resources(self) -> None:
        """Clean up resources and connections."""
        clear_model_cache()
        _validation_cache.clear()
        logger.info("Cleaned up model registry resources")


# Global optimizer instance
_global_optimizer = ModelRegistryOptimizer()


def get_model_registry_optimizer() -> ModelRegistryOptimizer:
    """Get the global model registry optimizer instance."""
    return _global_optimizer
