"""
Unified configuration management for model registry.

Consolidates configuration patterns from:
- services/common/mlflow_model_registry_config.py
- services/vllm_service/config/multi_model_config.yaml
- Various other configuration approaches
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None


@dataclass
class MLflowConfig:
    """MLflow configuration (consolidated from existing patterns)."""
    enabled: bool = True
    tracking_uri: str = "http://localhost:5000"
    registry_uri: Optional[str] = None
    experiment_name: str = "unified_model_registry"
    auto_log: bool = True
    
    def __post_init__(self):
        """Process configuration after initialization."""
        # Use environment variables if available
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", self.tracking_uri)
        self.registry_uri = os.getenv("MLFLOW_REGISTRY_URI", self.registry_uri or self.tracking_uri)
        self.enabled = os.getenv("MLFLOW_ENABLED", str(self.enabled)).lower() == "true"


@dataclass
class CachingConfig:
    """Caching configuration for performance optimization."""
    enabled: bool = True
    ttl_seconds: int = 3600
    max_cache_size: int = 1000
    backend: str = "memory"  # memory, redis, file


@dataclass
class ValidationConfig:
    """Validation configuration."""
    enabled: bool = True
    strict_mode: bool = False
    validate_on_registration: bool = True
    validate_on_promotion: bool = True


@dataclass
class PerformanceConfig:
    """Performance optimization configuration."""
    async_operations: bool = True
    batch_size: int = 100
    connection_pool_size: int = 10
    max_concurrent_operations: int = 50


@dataclass
class RegistryConfig:
    """Unified registry configuration."""
    mlflow: MLflowConfig = field(default_factory=MLflowConfig)
    caching: CachingConfig = field(default_factory=CachingConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Additional settings
    log_level: str = "INFO"
    registry_name: str = "unified_model_registry"
    enable_metrics: bool = True
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        """Initialize from dictionary configuration."""
        if config_dict is None:
            config_dict = {}
        
        # Initialize sub-configurations
        self.mlflow = MLflowConfig(**config_dict.get('mlflow', {}))
        self.caching = CachingConfig(**config_dict.get('caching', {}))
        self.validation = ValidationConfig(**config_dict.get('validation', {}))
        self.performance = PerformanceConfig(**config_dict.get('performance', {}))
        
        # Set top-level settings
        self.log_level = config_dict.get('log_level', 'INFO')
        self.registry_name = config_dict.get('registry_name', 'unified_model_registry')
        self.enable_metrics = config_dict.get('enable_metrics', True)


def load_unified_config() -> Dict[str, Any]:
    """
    Load unified configuration from multiple sources.
    
    Priority order:
    1. Environment variables
    2. Project-specific config file
    3. Default configuration
    """
    config = {}
    
    # 1. Load default configuration
    config.update(_get_default_config())
    
    # 2. Load from config file if it exists
    config_file = _find_config_file()
    if config_file:
        file_config = _load_config_file(config_file)
        config.update(file_config)
    
    # 3. Override with environment variables
    env_config = _load_from_environment()
    config.update(env_config)
    
    return config


def _get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        'mlflow': {
            'enabled': True,
            'tracking_uri': 'http://localhost:5000',
            'experiment_name': 'unified_model_registry',
            'auto_log': True
        },
        'caching': {
            'enabled': True,
            'ttl_seconds': 3600,
            'max_cache_size': 1000,
            'backend': 'memory'
        },
        'validation': {
            'enabled': True,
            'strict_mode': False,
            'validate_on_registration': True,
            'validate_on_promotion': True
        },
        'performance': {
            'async_operations': True,
            'batch_size': 100,
            'connection_pool_size': 10,
            'max_concurrent_operations': 50
        },
        'log_level': 'INFO',
        'registry_name': 'unified_model_registry',
        'enable_metrics': True
    }


def _find_config_file() -> Optional[Path]:
    """Find configuration file in common locations."""
    potential_locations = [
        Path.cwd() / "model_registry_config.yaml",
        Path.cwd() / "config" / "model_registry.yaml",
        Path(__file__).parent.parent / "config" / "unified_registry.yaml",
        Path.home() / ".model_registry" / "config.yaml"
    ]
    
    for location in potential_locations:
        if location.exists():
            return location
    
    return None


def _load_config_file(config_file: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not YAML_AVAILABLE:
        import logging
        logging.warning("PyYAML not available, cannot load config file")
        return {}
        
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        import logging
        logging.warning(f"Failed to load config file {config_file}: {e}")
        return {}


def _load_from_environment() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}
    
    # MLflow configuration
    mlflow_config = {}
    if 'MLFLOW_TRACKING_URI' in os.environ:
        mlflow_config['tracking_uri'] = os.environ['MLFLOW_TRACKING_URI']
    if 'MLFLOW_REGISTRY_URI' in os.environ:
        mlflow_config['registry_uri'] = os.environ['MLFLOW_REGISTRY_URI']
    if 'MLFLOW_EXPERIMENT_NAME' in os.environ:
        mlflow_config['experiment_name'] = os.environ['MLFLOW_EXPERIMENT_NAME']
    if 'MLFLOW_ENABLED' in os.environ:
        mlflow_config['enabled'] = os.environ['MLFLOW_ENABLED'].lower() == 'true'
    
    if mlflow_config:
        config['mlflow'] = mlflow_config
    
    # Caching configuration
    caching_config = {}
    if 'MODEL_REGISTRY_CACHE_ENABLED' in os.environ:
        caching_config['enabled'] = os.environ['MODEL_REGISTRY_CACHE_ENABLED'].lower() == 'true'
    if 'MODEL_REGISTRY_CACHE_TTL' in os.environ:
        try:
            caching_config['ttl_seconds'] = int(os.environ['MODEL_REGISTRY_CACHE_TTL'])
        except ValueError:
            pass
    
    if caching_config:
        config['caching'] = caching_config
    
    # Performance configuration
    performance_config = {}
    if 'MODEL_REGISTRY_ASYNC' in os.environ:
        performance_config['async_operations'] = os.environ['MODEL_REGISTRY_ASYNC'].lower() == 'true'
    if 'MODEL_REGISTRY_BATCH_SIZE' in os.environ:
        try:
            performance_config['batch_size'] = int(os.environ['MODEL_REGISTRY_BATCH_SIZE'])
        except ValueError:
            pass
    
    if performance_config:
        config['performance'] = performance_config
    
    # Top-level configuration
    if 'MODEL_REGISTRY_LOG_LEVEL' in os.environ:
        config['log_level'] = os.environ['MODEL_REGISTRY_LOG_LEVEL']
    if 'MODEL_REGISTRY_NAME' in os.environ:
        config['registry_name'] = os.environ['MODEL_REGISTRY_NAME']
    
    return config


def get_registry_config(config_dict: Dict[str, Any] = None) -> RegistryConfig:
    """Get registry configuration instance."""
    if config_dict is None:
        config_dict = load_unified_config()
    
    return RegistryConfig(config_dict)


def create_config_template(output_path: str = "model_registry_config.yaml"):
    """Create a configuration template file."""
    template_config = {
        '# Unified Model Registry Configuration': None,
        'mlflow': {
            'enabled': True,
            'tracking_uri': 'http://localhost:5000',
            'registry_uri': None,  # Will default to tracking_uri
            'experiment_name': 'unified_model_registry',
            'auto_log': True
        },
        'caching': {
            'enabled': True,
            'ttl_seconds': 3600,
            'max_cache_size': 1000,
            'backend': 'memory'  # memory, redis, file
        },
        'validation': {
            'enabled': True,
            'strict_mode': False,
            'validate_on_registration': True,
            'validate_on_promotion': True
        },
        'performance': {
            'async_operations': True,
            'batch_size': 100,
            'connection_pool_size': 10,
            'max_concurrent_operations': 50
        },
        'log_level': 'INFO',
        'registry_name': 'unified_model_registry',
        'enable_metrics': True
    }
    
    # Remove comment key
    template_config.pop('# Unified Model Registry Configuration')
    
    with open(output_path, 'w') as f:
        f.write("# Unified Model Registry Configuration\n\n")
        yaml.dump(template_config, f, default_flow_style=False, indent=2)
    
    print(f"Configuration template created: {output_path}")


# Legacy compatibility functions for existing code
def configure_mlflow_with_registry():
    """Legacy compatibility function."""
    from .mlflow_client_manager import get_mlflow_client_manager
    manager = get_mlflow_client_manager()
    return manager.configure_mlflow()


def get_mlflow_client():
    """Legacy compatibility function."""
    from .mlflow_client_manager import get_mlflow_client_manager
    manager = get_mlflow_client_manager()
    return manager.get_client()