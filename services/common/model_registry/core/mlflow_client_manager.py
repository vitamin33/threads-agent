"""
Unified MLflow client management.

Consolidates and optimizes client pooling from:
- services/common/mlflow_client_pool.py
- services/common/mlflow_model_registry_config.py
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Global manager instance
_client_manager_instance: Optional['MLflowClientManager'] = None
_manager_lock = threading.Lock()


class MLflowClientManager:
    """
    Unified MLflow client manager with connection pooling and configuration.
    
    Consolidates functionality from:
    - MLflowClientPool
    - mlflow_model_registry_config functions
    """
    
    def __init__(self, config: Any = None):
        """Initialize client manager with configuration."""
        self.config = config
        self._clients: Dict[str, Any] = {}
        self._client_lock = threading.RLock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        self._max_idle_time = 600  # 10 minutes
        self._client_usage: Dict[str, float] = {}
        self._configured = False
        
        # Configure MLflow on initialization
        self.configure_mlflow()
    
    def configure_mlflow(self):
        """Configure MLflow with registry support."""
        if self._configured:
            return
        
        try:
            import mlflow
            
            # Get configuration
            tracking_uri = "http://localhost:5000"
            registry_uri = None
            auto_log = True
            
            if self.config:
                tracking_uri = self.config.tracking_uri
                registry_uri = self.config.registry_uri
                auto_log = self.config.auto_log
            
            # Set tracking URI
            if tracking_uri:
                mlflow.set_tracking_uri(tracking_uri)
                logger.info(f"Set MLflow tracking URI: {tracking_uri}")
            
            # Set registry URI (defaults to tracking URI if not specified)
            if registry_uri:
                mlflow.set_registry_uri(registry_uri)
                logger.info(f"Set MLflow registry URI: {registry_uri}")
            elif tracking_uri:
                mlflow.set_registry_uri(tracking_uri)
            
            # Enable autologging if configured
            if auto_log:
                try:
                    mlflow.autolog(log_models=True, log_input_examples=True, silent=True)
                    logger.debug("MLflow autologging enabled")
                except Exception as e:
                    logger.warning(f"Failed to enable MLflow autologging: {e}")
            
            self._configured = True
            logger.info("MLflow client manager configured successfully")
            
        except ImportError:
            logger.warning("MLflow not available, client manager will use mock mode")
        except Exception as e:
            logger.error(f"Failed to configure MLflow: {e}")
    
    def get_client(self, key: str = "default"):
        """Get a pooled MLflow client instance."""
        with self._client_lock:
            current_time = time.time()
            
            # Cleanup old clients periodically
            if current_time - self._last_cleanup > self._cleanup_interval:
                self._cleanup_idle_clients(current_time)
                self._last_cleanup = current_time
            
            # Create or reuse client
            if key not in self._clients:
                self._clients[key] = self._create_client()
                logger.debug(f"Created new MLflow client: {key}")
            
            # Update usage tracking
            self._client_usage[key] = current_time
            
            return self._clients[key]
    
    async def get_client_async(self, key: str = "default"):
        """Get client in async context."""
        # Run the sync operation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_client, key)
    
    def _create_client(self):
        """Create a new MLflow client."""
        try:
            from mlflow.tracking import MlflowClient
            
            # Get current MLflow configuration
            import mlflow
            tracking_uri = mlflow.get_tracking_uri()
            registry_uri = mlflow.get_registry_uri()
            
            # Create client with current configuration
            client = MlflowClient(
                tracking_uri=tracking_uri,
                registry_uri=registry_uri
            )
            
            return client
            
        except ImportError:
            # Return mock client if MLflow not available
            return MockMLflowClient()
        except Exception as e:
            logger.error(f"Failed to create MLflow client: {e}")
            return MockMLflowClient()
    
    def _cleanup_idle_clients(self, current_time: float):
        """Clean up idle clients to free resources."""
        clients_to_remove = []
        
        for key, last_used in self._client_usage.items():
            if current_time - last_used > self._max_idle_time:
                clients_to_remove.append(key)
        
        for key in clients_to_remove:
            self._clients.pop(key, None)
            self._client_usage.pop(key, None)
            logger.debug(f"Cleaned up idle client: {key}")
    
    def test_connection(self) -> bool:
        """Test if MLflow connection is working."""
        try:
            client = self.get_client()
            
            # Try a simple operation
            if hasattr(client, 'search_registered_models'):
                client.search_registered_models(max_results=1)
                return True
            else:
                # Mock client
                return False
                
        except Exception as e:
            logger.warning(f"MLflow connection test failed: {e}")
            return False
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get information about the MLflow registry setup."""
        try:
            import mlflow
            
            tracking_uri = mlflow.get_tracking_uri()
            registry_uri = mlflow.get_registry_uri()
            
            info = {
                "tracking_uri": tracking_uri,
                "registry_uri": registry_uri,
                "connection_test": self.test_connection(),
                "active_clients": len(self._clients),
                "configured": self._configured
            }
            
            # Determine backend store type
            if tracking_uri:
                if "postgresql" in tracking_uri:
                    info["backend_store"] = "postgresql"
                elif "mysql" in tracking_uri:
                    info["backend_store"] = "mysql"
                elif "sqlite" in tracking_uri:
                    info["backend_store"] = "sqlite"
                elif tracking_uri.startswith("file:"):
                    info["backend_store"] = "file"
                else:
                    info["backend_store"] = "unknown"
            
            return info
            
        except ImportError:
            return {
                "error": "MLflow not available",
                "configured": False,
                "connection_test": False
            }
        except Exception as e:
            return {
                "error": str(e),
                "configured": self._configured,
                "connection_test": False
            }
    
    def create_or_get_registered_model(self, name: str, description: Optional[str] = None) -> str:
        """Create a registered model or get it if it already exists."""
        try:
            client = self.get_client()
            
            # Try to create the model
            try:
                client.create_registered_model(name=name, description=description)
                logger.info(f"Created registered model: {name}")
            except Exception:
                # Model already exists
                logger.debug(f"Using existing registered model: {name}")
            
            return name
            
        except Exception as e:
            logger.error(f"Failed to create/get registered model {name}: {e}")
            raise
    
    def cleanup(self):
        """Clean up all clients and resources."""
        with self._client_lock:
            self._clients.clear()
            self._client_usage.clear()
            logger.info("MLflow client manager cleaned up")


class MockMLflowClient:
    """Mock MLflow client for environments where MLflow is not available."""
    
    def search_registered_models(self, max_results=None):
        """Mock search registered models."""
        return []
    
    def create_registered_model(self, name, description=None):
        """Mock create registered model."""
        logger.debug(f"Mock: Created registered model {name}")
        return {"name": name, "description": description}
    
    def get_registered_model(self, name):
        """Mock get registered model."""
        return {"name": name, "latest_versions": []}
    
    def search_model_versions(self, filter_string=None):
        """Mock search model versions."""
        return []
    
    def transition_model_version_stage(self, name, version, stage):
        """Mock transition model version stage."""
        logger.debug(f"Mock: Transitioned {name} v{version} to {stage}")
        return {"name": name, "version": version, "current_stage": stage}


def get_mlflow_client_manager(config: Any = None) -> MLflowClientManager:
    """Get the global MLflow client manager instance."""
    global _client_manager_instance
    
    if _client_manager_instance is None:
        with _manager_lock:
            if _client_manager_instance is None:
                _client_manager_instance = MLflowClientManager(config)
    
    return _client_manager_instance


def reset_mlflow_client_manager():
    """Reset the global client manager (for testing)."""
    global _client_manager_instance
    
    with _manager_lock:
        if _client_manager_instance:
            _client_manager_instance.cleanup()
        _client_manager_instance = None