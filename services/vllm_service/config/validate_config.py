#!/usr/bin/env python3
"""
Configuration validation script for multi-model vLLM deployment.

This script validates the multi_model_config.yaml file to ensure:
- All required fields are present
- Memory requirements are realistic for Apple Silicon M4 Max
- Model configurations are valid
- Content type routing is properly configured
- MLflow integration settings are correct

Usage:
    python validate_config.py
    python validate_config.py --config-path /path/to/config.yaml
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any


class ConfigValidator:
    """Validates multi-model configuration."""

    def __init__(self, config_path: str):
        """Initialize validator with config path."""
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_config(self) -> bool:
        """Load and parse configuration file."""
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
            return True
        except Exception as e:
            self.errors.append(f"Failed to load config file: {e}")
            return False

    def validate(self) -> bool:
        """Run all validation checks."""
        if not self.load_config():
            return False

        # Run validation checks
        self._validate_basic_structure()
        self._validate_models()
        self._validate_resource_management()
        self._validate_content_routing()
        self._validate_apple_silicon_config()
        self._validate_mlflow_integration()
        self._validate_memory_constraints()

        return len(self.errors) == 0

    def _validate_basic_structure(self) -> None:
        """Validate basic configuration structure."""
        required_sections = [
            "version",
            "platform",
            "total_memory_gb",
            "memory_safety_threshold",
            "models",
            "resource_management",
            "content_routing",
            "apple_silicon",
        ]

        for section in required_sections:
            if section not in self.config:
                self.errors.append(f"Missing required section: {section}")

        # Validate platform
        if self.config.get("platform") != "apple-silicon-m4-max":
            self.warnings.append(
                "Configuration is optimized for apple-silicon-m4-max platform"
            )

        # Validate memory settings
        total_memory = self.config.get("total_memory_gb", 0)
        if total_memory < 16:
            self.errors.append(
                f"Total memory ({total_memory}GB) too low for multi-model deployment"
            )
        elif total_memory != 36:
            self.warnings.append(f"Expected 36GB for M4 Max, got {total_memory}GB")

        # Validate memory threshold
        threshold = self.config.get("memory_safety_threshold", 0)
        if not 0.5 <= threshold <= 0.95:
            self.errors.append(
                f"Memory safety threshold ({threshold}) should be between 0.5 and 0.95"
            )

    def _validate_models(self) -> None:
        """Validate model configurations."""
        models = self.config.get("models", {})

        if not models:
            self.errors.append("No models configured")
            return

        if len(models) != 5:
            self.warnings.append(
                f"Expected 5 models for multi-model deployment, got {len(models)}"
            )

        expected_models = {
            "llama_8b": "meta-llama/Llama-3.1-8B-Instruct",
            "qwen_7b": "Qwen/Qwen2.5-7B-Instruct",
            "mistral_7b": "mistralai/Mistral-7B-Instruct-v0.3",
            "llama_3b": "meta-llama/Llama-3.1-3B-Instruct",
            "phi_mini": "microsoft/Phi-3.5-mini-instruct",
        }

        priorities = []

        for model_id, model_config in models.items():
            # Validate required fields
            required_fields = [
                "name",
                "display_name",
                "memory_requirements",
                "content_types",
                "priority",
                "optimization",
                "performance",
            ]

            for field in required_fields:
                if field not in model_config:
                    self.errors.append(
                        f"Model {model_id} missing required field: {field}"
                    )

            # Check expected model names
            if model_id in expected_models:
                expected_name = expected_models[model_id]
                actual_name = model_config.get("name", "")
                if actual_name != expected_name:
                    self.warnings.append(
                        f"Model {model_id} name mismatch: expected {expected_name}, got {actual_name}"
                    )

            # Validate memory requirements
            mem_req = model_config.get("memory_requirements", {})
            required_mem_fields = ["base_gb", "optimized_gb", "minimum_gb"]

            for field in required_mem_fields:
                if field not in mem_req:
                    self.errors.append(
                        f"Model {model_id} missing memory requirement: {field}"
                    )
                elif (
                    not isinstance(mem_req[field], (int, float)) or mem_req[field] <= 0
                ):
                    self.errors.append(
                        f"Model {model_id} invalid memory requirement {field}: {mem_req[field]}"
                    )

            # Validate memory requirement ordering
            if all(field in mem_req for field in required_mem_fields):
                base = mem_req["base_gb"]
                optimized = mem_req["optimized_gb"]
                minimum = mem_req["minimum_gb"]

                if not (minimum <= optimized <= base):
                    self.errors.append(
                        f"Model {model_id} memory requirements not ordered: minimum <= optimized <= base"
                    )

            # Validate priority
            priority = model_config.get("priority")
            if priority is not None:
                if not isinstance(priority, int) or priority < 1:
                    self.errors.append(f"Model {model_id} invalid priority: {priority}")
                else:
                    priorities.append(priority)

            # Validate optimization config
            optimization = model_config.get("optimization", {})
            valid_quantizations = ["fp16", "int8", "int4"]
            quant = optimization.get("quantization")
            if quant and quant not in valid_quantizations:
                self.errors.append(f"Model {model_id} invalid quantization: {quant}")

            # Validate performance config
            performance = model_config.get("performance", {})
            if "target_latency_ms" in performance:
                latency = performance["target_latency_ms"]
                if not isinstance(latency, int) or latency <= 0:
                    self.errors.append(
                        f"Model {model_id} invalid target latency: {latency}"
                    )
                elif latency > 100:
                    self.warnings.append(
                        f"Model {model_id} high target latency: {latency}ms"
                    )

        # Check priority uniqueness
        if len(priorities) != len(set(priorities)):
            self.errors.append("Model priorities must be unique")

    def _validate_resource_management(self) -> None:
        """Validate resource management configuration."""
        resource_mgmt = self.config.get("resource_management", {})

        # Validate concurrent models limit
        concurrent_limit = resource_mgmt.get("concurrent_models_limit", 0)
        if concurrent_limit < 1 or concurrent_limit > 5:
            self.errors.append(
                f"Concurrent models limit ({concurrent_limit}) should be between 1 and 5"
            )

        # Validate loading/unloading orders
        models = set(self.config.get("models", {}).keys())

        loading_order = resource_mgmt.get("loading_order", [])
        if set(loading_order) != models:
            self.errors.append("Loading order must include all configured models")

        unloading_order = resource_mgmt.get("unloading_order", [])
        if set(unloading_order) != models:
            self.errors.append("Unloading order must include all configured models")

    def _validate_content_routing(self) -> None:
        """Validate content type routing configuration."""
        content_routing = self.config.get("content_routing", {})
        models = set(self.config.get("models", {}).keys())

        expected_content_types = [
            "twitter",
            "linkedin",
            "technical_articles",
            "code_documentation",
            "general",
        ]

        for content_type in expected_content_types:
            if content_type not in content_routing:
                self.warnings.append(
                    f"Missing routing configuration for content type: {content_type}"
                )
                continue

            routing = content_routing[content_type]

            # Validate primary models
            primary = routing.get("primary", [])
            for model_id in primary:
                if model_id not in models:
                    self.errors.append(
                        f"Unknown model '{model_id}' in {content_type} primary routing"
                    )

            # Validate fallback models
            fallback = routing.get("fallback", [])
            for model_id in fallback:
                if model_id not in models:
                    self.errors.append(
                        f"Unknown model '{model_id}' in {content_type} fallback routing"
                    )

            # Validate max tokens
            max_tokens = routing.get("max_tokens")
            if max_tokens and (not isinstance(max_tokens, int) or max_tokens <= 0):
                self.errors.append(
                    f"Invalid max_tokens for {content_type}: {max_tokens}"
                )

    def _validate_apple_silicon_config(self) -> None:
        """Validate Apple Silicon specific configuration."""
        apple_silicon = self.config.get("apple_silicon", {})

        # Validate presets
        presets = apple_silicon.get("presets", {})
        expected_presets = ["maximum_performance", "balanced", "memory_optimized"]

        for preset in expected_presets:
            if preset not in presets:
                self.warnings.append(f"Missing Apple Silicon preset: {preset}")
                continue

            preset_config = presets[preset]

            # Validate GPU memory utilization
            gpu_util = preset_config.get("gpu_memory_utilization")
            if gpu_util and (not 0.1 <= gpu_util <= 1.0):
                self.errors.append(
                    f"Invalid GPU memory utilization in {preset}: {gpu_util}"
                )

    def _validate_mlflow_integration(self) -> None:
        """Validate MLflow integration configuration."""
        mlflow_config = self.config.get("mlflow_integration", {})

        if not mlflow_config.get("enabled", False):
            self.warnings.append("MLflow integration is disabled")
            return

        # Check experiment name
        experiment_name = mlflow_config.get("experiment_name")
        if not experiment_name:
            self.errors.append(
                "MLflow experiment name is required when integration is enabled"
            )

        # Validate metrics configuration
        metrics = mlflow_config.get("metrics", {})
        expected_metric_categories = ["performance", "quality", "cost"]

        for category in expected_metric_categories:
            if category not in metrics:
                self.warnings.append(f"Missing MLflow metrics category: {category}")

    def _validate_memory_constraints(self) -> None:
        """Validate memory constraints and feasibility."""
        models = self.config.get("models", {})
        total_memory = self.config.get("total_memory_gb", 36)
        threshold = self.config.get("memory_safety_threshold", 0.85)
        concurrent_limit = self.config.get("resource_management", {}).get(
            "concurrent_models_limit", 3
        )

        available_memory = total_memory * threshold

        # Check if all models can fit individually
        for model_id, model_config in models.items():
            mem_req = model_config.get("memory_requirements", {})
            minimum_memory = mem_req.get("minimum_gb", 0)

            if minimum_memory > available_memory:
                self.errors.append(
                    f"Model {model_id} minimum memory ({minimum_memory}GB) exceeds available memory ({available_memory}GB)"
                )

        # Check concurrent model scenarios
        model_memories = []
        for model_config in models.values():
            mem_req = model_config.get("memory_requirements", {})
            model_memories.append(mem_req.get("optimized_gb", 0))

        # Sort by memory (largest first) and check if top N models can fit
        model_memories.sort(reverse=True)
        top_n_memory = sum(model_memories[:concurrent_limit])

        if top_n_memory > available_memory:
            self.warnings.append(
                f"Top {concurrent_limit} largest models require {top_n_memory:.1f}GB, but only {available_memory:.1f}GB available"
            )

        # Check minimum memory scenario
        min_memories = []
        for model_config in models.values():
            mem_req = model_config.get("memory_requirements", {})
            min_memories.append(mem_req.get("minimum_gb", 0))

        min_memories.sort(reverse=True)
        min_concurrent_memory = sum(min_memories[:concurrent_limit])

        if min_concurrent_memory > available_memory:
            self.errors.append(
                f"Even minimum memory requirements for {concurrent_limit} models ({min_concurrent_memory:.1f}GB) exceed available memory"
            )

    def print_results(self) -> None:
        """Print validation results."""
        print(f"Configuration validation for: {self.config_path}")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ Configuration is valid!")
        elif not self.errors:
            print(f"\n✅ Configuration is valid (with {len(self.warnings)} warnings)")
        else:
            print(
                f"\n❌ Configuration validation failed with {len(self.errors)} errors"
            )


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate multi-model vLLM configuration"
    )
    parser.add_argument(
        "--config-path",
        default=None,
        help="Path to configuration file (default: auto-detect)",
    )

    args = parser.parse_args()

    # Determine config path
    if args.config_path:
        config_path = args.config_path
    else:
        # Auto-detect config path
        current_dir = Path(__file__).parent
        config_path = current_dir / "multi_model_config.yaml"

        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            print(
                "Please specify --config-path or ensure multi_model_config.yaml exists"
            )
            sys.exit(1)

    # Run validation
    validator = ConfigValidator(str(config_path))
    is_valid = validator.validate()
    validator.print_results()

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
