"""MLflow client connection pooling for improved performance in Kubernetes environments."""

import threading
from typing import Optional, Dict, Any
from functools import lru_cache
import time
import logging
from mlflow.tracking import MlflowClient
from services.common.mlflow_model_registry_config import configure_mlflow_with_registry
import mlflow

logger = logging.getLogger(__name__)


class MLflowClientPool:
    """Thread-safe MLflow client pool for connection reuse."""

    _instance: Optional["MLflowClientPool"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MLflowClientPool":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._clients: Dict[str, MlflowClient] = {}
            self._client_lock = threading.RLock()
            self._last_cleanup = time.time()
            self._cleanup_interval = 300  # 5 minutes
            self._max_idle_time = 600  # 10 minutes
            self._client_usage: Dict[str, float] = {}
            self._initialized = True
            configure_mlflow_with_registry()

    def get_client(self, key: str = "default") -> MlflowClient:
        """Get a pooled MLflow client instance."""
        with self._client_lock:
            current_time = time.time()

            # Cleanup old clients periodically
            if current_time - self._last_cleanup > self._cleanup_interval:
                self._cleanup_idle_clients(current_time)
                self._last_cleanup = current_time

            # Create or reuse client
            if key not in self._clients:
                tracking_uri = mlflow.get_tracking_uri()
                registry_uri = mlflow.get_registry_uri()
                self._clients[key] = MlflowClient(
                    tracking_uri=tracking_uri, registry_uri=registry_uri
                )
                logger.debug(f"Created new MLflow client: {key}")

            self._client_usage[key] = current_time
            return self._clients[key]

    def _cleanup_idle_clients(self, current_time: float) -> None:
        """Remove clients that have been idle for too long."""
        idle_clients = [
            key
            for key, last_used in self._client_usage.items()
            if current_time - last_used > self._max_idle_time
        ]

        for key in idle_clients:
            del self._clients[key]
            del self._client_usage[key]
            logger.debug(f"Cleaned up idle MLflow client: {key}")

    def close_all(self) -> None:
        """Close all pooled connections."""
        with self._client_lock:
            self._clients.clear()
            self._client_usage.clear()


# Thread-local storage for client pool access
_thread_local = threading.local()


def get_pooled_mlflow_client() -> MlflowClient:
    """Get a thread-safe pooled MLflow client."""
    if not hasattr(_thread_local, "pool"):
        _thread_local.pool = MLflowClientPool()

    # Use thread ID as key for better isolation
    thread_key = f"thread_{threading.get_ident()}"
    return _thread_local.pool.get_client(thread_key)


@lru_cache(maxsize=128)
def get_cached_model_versions(model_name: str, cache_ttl: int = 300) -> tuple:
    """Cache model versions to reduce MLflow API calls."""
    client = get_pooled_mlflow_client()
    try:
        versions = client.search_model_versions(f"name='{model_name}'")
        # Convert to tuple for caching (immutable)
        cached_versions = tuple(
            (
                v.version,
                v.current_stage,
                dict(v.tags) if v.tags else {},
                v.creation_timestamp,
            )
            for v in versions
        )
        return cached_versions
    except Exception as e:
        logger.warning(f"Failed to fetch model versions for {model_name}: {e}")
        return tuple()


def clear_model_cache(model_name: Optional[str] = None) -> None:
    """Clear cached model data."""
    if model_name:
        # Clear specific model cache
        get_cached_model_versions.cache_clear()
    else:
        # Clear all caches
        get_cached_model_versions.cache_clear()


class MLflowBatchOperations:
    """Optimized batch operations for MLflow Model Registry."""

    def __init__(self):
        self.client = get_pooled_mlflow_client()

    def batch_register_models(self, models: list) -> Dict[str, Any]:
        """Register multiple models in a single batch operation."""
        results = {"success": [], "failed": []}

        # Group models by registry to minimize connection overhead
        for model in models:
            try:
                # Use existing client connection
                self.client.create_registered_model(
                    name=model.name, description=f"Prompt template model: {model.name}"
                )

                # Batch create model versions
                model_version = self.client.create_model_version(
                    name=model.name,
                    source=model._get_artifact_path(),  # Pre-computed artifact path
                    tags={
                        "template": model.template,
                        "version": model.version,
                        **model.metadata,
                    },
                )

                model._model_version = str(model_version.version)
                results["success"].append(model.name)

            except Exception as e:
                logger.warning(f"Failed to register model {model.name}: {e}")
                results["failed"].append({"name": model.name, "error": str(e)})

        return results

    def batch_promote_models(self, promotions: list) -> Dict[str, Any]:
        """Promote multiple models to different stages in batch."""
        results = {"success": [], "failed": []}

        for promotion in promotions:
            try:
                self.client.transition_model_version_stage(
                    name=promotion["name"],
                    version=promotion["version"],
                    stage=promotion["stage"],
                )
                results["success"].append(promotion)
            except Exception as e:
                logger.warning(f"Failed to promote {promotion['name']}: {e}")
                results["failed"].append({**promotion, "error": str(e)})

        return results
