"""
Base registry interface and unified implementation.

This module provides the abstract base class for all model registries and
the main unified implementation that uses pluggable adapters.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union

from .configuration import RegistryConfig, load_unified_config
from .mlflow_client_manager import MLflowClientManager

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported model types across the platform."""
    PROMPT_TEMPLATE = "prompt_template"
    VLLM_MODEL = "vllm_model"  
    FINE_TUNED_MODEL = "fine_tuned_model"
    GENERAL_MODEL = "general_model"


class ModelStage(Enum):
    """Model deployment stages (unified from existing implementations)."""
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    
    # Additional stages from achievement_collector/mlops/model_registry.py
    TRAINING = "training"
    VALIDATION = "validation"
    TESTING = "testing"
    FAILED = "failed"


class ModelLoadState(Enum):
    """Model loading states for runtime management."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    ERROR = "error"


class ModelRegistryError(Exception):
    """Base exception for model registry operations."""
    pass


class ModelValidationError(ModelRegistryError):
    """Raised when model validation fails."""
    pass


class ModelNotFoundError(ModelRegistryError):
    """Raised when requested model is not found."""
    pass


class BaseModelRegistry(ABC):
    """
    Abstract base class for all model registries.
    
    This interface consolidates patterns from:
    - services/common/prompt_model_registry.py
    - services/achievement_collector/mlops/model_registry.py
    - services/vllm_service/model_registry.py
    """
    
    @abstractmethod
    async def register_model(
        self, 
        name: str,
        model_type: ModelType,
        metadata: Dict[str, Any],
        **kwargs
    ) -> str:
        """Register a model and return its ID."""
        pass
    
    @abstractmethod
    async def promote_model(
        self,
        model_id: str,
        target_stage: ModelStage,
        validation_results: Optional[Dict] = None
    ) -> bool:
        """Promote model through stages."""
        pass
    
    @abstractmethod
    async def get_model(
        self,
        model_identifier: Union[str, Dict[str, Any]]
    ) -> Optional[Any]:
        """Get model by ID or search criteria."""
        pass
    
    @abstractmethod
    async def list_models(
        self,
        model_type: Optional[ModelType] = None,
        stage: Optional[ModelStage] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """List models with optional filtering."""
        pass
    
    @abstractmethod
    async def compare_models(
        self,
        model_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple models."""
        pass
    
    @abstractmethod
    async def get_model_lineage(
        self,
        model_id: str
    ) -> Dict[str, Any]:
        """Get model lineage and dependencies."""
        pass


class UnifiedModelRegistry(BaseModelRegistry):
    """
    Unified registry with pluggable adapters.
    
    This consolidates functionality from multiple existing registries:
    - PromptModel from services/common/prompt_model_registry.py
    - ProductionModelRegistry from services/achievement_collector/mlops/model_registry.py
    - MultiModelRegistry from services/vllm_service/model_registry.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize unified registry."""
        self.config = RegistryConfig(config or load_unified_config())
        self.client_manager = MLflowClientManager(self.config.mlflow)
        self.adapters: Dict[ModelType, Any] = {}
        self._initialized = False
        
        # Initialize with default adapters
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register default adapters for known model types."""
        # Import adapters here to avoid circular imports
        try:
            from ..adapters.prompt_adapter import PromptAdapter
            self.register_adapter(ModelType.PROMPT_TEMPLATE, PromptAdapter)
        except ImportError:
            logger.warning("PromptAdapter not available")
        
        try:
            from ..adapters.vllm_adapter import VLLMAdapter
            self.register_adapter(ModelType.VLLM_MODEL, VLLMAdapter)
        except ImportError:
            logger.warning("VLLMAdapter not available")
        
        try:
            from ..adapters.fine_tuning_adapter import FineTuningAdapter
            self.register_adapter(ModelType.FINE_TUNED_MODEL, FineTuningAdapter)
        except ImportError:
            logger.warning("FineTuningAdapter not available")
    
    def register_adapter(self, model_type: ModelType, adapter_class):
        """Register a specialized adapter for a model type."""
        self.adapters[model_type] = adapter_class(self)
        logger.info(f"Registered adapter for {model_type.value}")
    
    def get_adapter(self, model_type: ModelType):
        """Get adapter for a specific model type."""
        if model_type not in self.adapters:
            raise ModelRegistryError(f"No adapter registered for {model_type.value}")
        return self.adapters[model_type]
    
    async def register_model(
        self, 
        name: str,
        model_type: ModelType,
        metadata: Dict[str, Any],
        **kwargs
    ) -> str:
        """Register a model using the appropriate adapter."""
        try:
            adapter = self.get_adapter(model_type)
            model_id = await adapter.register_model(name, metadata, **kwargs)
            
            # Log to MLflow if enabled
            if self.config.mlflow.enabled:
                await self._log_registration_event(model_id, model_type, metadata)
            
            logger.info(f"Successfully registered {model_type.value} model: {name} -> {model_id}")
            return model_id
            
        except Exception as e:
            logger.error(f"Failed to register model {name}: {e}")
            raise ModelRegistryError(f"Registration failed: {e}") from e
    
    async def promote_model(
        self,
        model_id: str,
        target_stage: ModelStage,
        validation_results: Optional[Dict] = None
    ) -> bool:
        """Promote model through stages."""
        try:
            # Get model info to determine type
            model_info = await self.get_model(model_id)
            if not model_info:
                raise ModelNotFoundError(f"Model not found: {model_id}")
            
            model_type = ModelType(model_info.get('type', 'general_model'))
            adapter = self.get_adapter(model_type)
            
            success = await adapter.promote_model(model_id, target_stage, validation_results)
            
            if success and self.config.mlflow.enabled:
                await self._log_promotion_event(model_id, target_stage, validation_results)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to promote model {model_id}: {e}")
            raise ModelRegistryError(f"Promotion failed: {e}") from e
    
    async def get_model(
        self,
        model_identifier: Union[str, Dict[str, Any]]
    ) -> Optional[Any]:
        """Get model by ID or search criteria."""
        # If it's a string ID, try to find it across all adapters
        if isinstance(model_identifier, str):
            for adapter in self.adapters.values():
                if hasattr(adapter, 'get_model'):
                    model = await adapter.get_model(model_identifier)
                    if model:
                        return model
            return None
        
        # If it's search criteria, delegate to appropriate adapter
        if isinstance(model_identifier, dict):
            model_type = model_identifier.get('type')
            if model_type:
                adapter = self.get_adapter(ModelType(model_type))
                return await adapter.get_model(model_identifier)
        
        return None
    
    async def list_models(
        self,
        model_type: Optional[ModelType] = None,
        stage: Optional[ModelStage] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """List models with optional filtering."""
        results = []
        
        # If model_type specified, query specific adapter
        if model_type:
            adapter = self.get_adapter(model_type)
            if hasattr(adapter, 'list_models'):
                models = await adapter.list_models(stage=stage, **filters)
                results.extend(models)
        else:
            # Query all adapters
            for adapter in self.adapters.values():
                if hasattr(adapter, 'list_models'):
                    try:
                        models = await adapter.list_models(stage=stage, **filters)
                        results.extend(models)
                    except Exception as e:
                        logger.warning(f"Adapter failed to list models: {e}")
        
        return results
    
    async def compare_models(
        self,
        model_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple models."""
        comparison_results = {}
        
        for model_id in model_ids:
            model_info = await self.get_model(model_id)
            if model_info:
                model_type = ModelType(model_info.get('type', 'general_model'))
                adapter = self.get_adapter(model_type)
                
                if hasattr(adapter, 'get_model_metrics'):
                    model_metrics = await adapter.get_model_metrics(model_id, metrics)
                    comparison_results[model_id] = {
                        'info': model_info,
                        'metrics': model_metrics,
                        'type': model_type.value
                    }
        
        return comparison_results
    
    async def get_model_lineage(
        self,
        model_id: str
    ) -> Dict[str, Any]:
        """Get model lineage and dependencies."""
        model_info = await self.get_model(model_id)
        if not model_info:
            raise ModelNotFoundError(f"Model not found: {model_id}")
        
        model_type = ModelType(model_info.get('type', 'general_model'))
        adapter = self.get_adapter(model_type)
        
        if hasattr(adapter, 'get_lineage'):
            return await adapter.get_lineage(model_id)
        
        # Default lineage information
        return {
            'model_id': model_id,
            'lineage': [],
            'dependencies': [],
            'created_at': model_info.get('created_at'),
            'created_by': model_info.get('created_by')
        }
    
    async def _log_registration_event(
        self,
        model_id: str,
        model_type: ModelType,
        metadata: Dict[str, Any]
    ):
        """Log model registration to MLflow."""
        try:
            client = await self.client_manager.get_client()
            
            # Log as MLflow event
            run_data = {
                'event_type': 'model_registration',
                'model_id': model_id,
                'model_type': model_type.value,
                'timestamp': datetime.now().isoformat(),
                **metadata
            }
            
            # Use experiment tracking if available
            experiment_name = self.config.mlflow.experiment_name or "model_registry_events"
            
            import mlflow
            mlflow.set_experiment(experiment_name)
            
            with mlflow.start_run():
                mlflow.log_params(run_data)
                mlflow.log_metric("registration_event", 1)
                
        except Exception as e:
            logger.warning(f"Failed to log registration event: {e}")
    
    async def _log_promotion_event(
        self,
        model_id: str,
        target_stage: ModelStage,
        validation_results: Optional[Dict]
    ):
        """Log model promotion to MLflow."""
        try:
            client = await self.client_manager.get_client()
            
            run_data = {
                'event_type': 'model_promotion',
                'model_id': model_id,
                'target_stage': target_stage.value,
                'timestamp': datetime.now().isoformat(),
            }
            
            if validation_results:
                run_data.update(validation_results)
            
            experiment_name = self.config.mlflow.experiment_name or "model_registry_events"
            
            import mlflow
            mlflow.set_experiment(experiment_name)
            
            with mlflow.start_run():
                mlflow.log_params(run_data)
                mlflow.log_metric("promotion_event", 1)
                if validation_results:
                    for metric, value in validation_results.items():
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(f"validation_{metric}", value)
                            
        except Exception as e:
            logger.warning(f"Failed to log promotion event: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all registered models and adapters."""
        return {
            'adapters': list(self.adapters.keys()),
            'config': {
                'mlflow_enabled': self.config.mlflow.enabled,
                'tracking_uri': self.config.mlflow.tracking_uri,
                'experiment_name': self.config.mlflow.experiment_name
            },
            'client_manager': {
                'active_clients': len(self.client_manager._clients) if hasattr(self.client_manager, '_clients') else 0
            }
        }