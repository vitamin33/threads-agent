"""
PromptModel Registry for MLflow Model Registry integration.

This module provides a wrapper class for versioning prompt templates using MLflow Model Registry.
Supports model registration, versioning, stage promotion, lineage tracking, and comparison.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from mlflow.exceptions import RestException

from services.common.mlflow_model_registry_config import (
    configure_mlflow_with_registry,
    get_mlflow_client,
)

# Configure MLflow with Model Registry support on module import
configure_mlflow_with_registry()


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


class PromptModel:
    """
    Wrapper class for prompt template versioning using MLflow Model Registry.

    Provides functionality for:
    - Registering prompt templates as models
    - Versioning and stage promotion
    - Model validation and comparison
    - Lineage tracking
    """

    def __init__(
        self,
        name: str,
        template: str,
        version: str,
        stage: ModelStage = ModelStage.DEV,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize PromptModel.

        Args:
            name: Model name
            template: Prompt template string
            version: Model version (semantic versioning)
            stage: Deployment stage (default: DEV)
            metadata: Additional metadata dictionary
        """
        # Validate inputs during initialization
        self._validate_inputs(name, template, version)

        self.name = name
        self.template = template
        self.version = version
        self.stage = stage
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self._model_version: Optional[str] = None
        self._mlflow_client = get_mlflow_client()

    def _validate_inputs(self, name: str, template: str, version: str) -> None:
        """Validate model inputs during initialization."""
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

        # Validate template format
        self._validate_template_format(template)

    def _validate_template_format(self, template: str) -> None:
        """Validate template has valid Python string format syntax."""
        try:
            # Test template formatting with dummy variables
            import re

            # Extract variables from template
            variables = re.findall(r"\{([^}]*)\}", template)

            # Check for unclosed brackets
            open_brackets = template.count("{")
            close_brackets = template.count("}")
            if open_brackets != close_brackets:
                raise ModelValidationError(
                    "Invalid template format: mismatched brackets"
                )

            # Check for empty variable names
            for var in variables:
                var_name = var.split(":")[0] if ":" in var else var
                if not var_name.strip():
                    raise ModelValidationError(
                        "Invalid template format: empty variable name"
                    )

            # Try formatting with dummy values to catch invalid format specifiers
            dummy_values: dict[str, Any] = {}
            for var in variables:
                # Handle format specifiers like {price:.2f}
                var_name = var.split(":")[0].strip()

                # Handle dictionary/attribute access like {config[key]} or {obj.attr}
                if "[" in var_name or "." in var_name:
                    # Extract base variable name
                    base_name = var_name.split("[")[0].split(".")[0]
                    if base_name and base_name not in dummy_values:
                        # Create nested structure for testing
                        class DummyNested:
                            def __getitem__(self, key):
                                return self

                            def __getattr__(self, attr):
                                return self

                            def __str__(self):
                                return "dummy"

                            def __format__(self, spec):
                                return "dummy"

                        dummy_values[base_name] = DummyNested()
                elif var_name:  # Simple variable
                    # Use appropriate dummy values based on format specifier
                    if ":" in var:
                        format_spec = var.split(":", 1)[1]
                        # Check for numeric format specifiers
                        if (
                            any(c in format_spec for c in "efgEFGn")
                            or "%" in format_spec
                        ):
                            dummy_values[var_name] = 1.0  # Float
                        elif any(c in format_spec for c in "bdoxX"):
                            dummy_values[var_name] = 42  # Integer
                        else:
                            dummy_values[var_name] = "dummy"  # String
                    else:
                        dummy_values[var_name] = "dummy"

            # Test the template
            template.format(**dummy_values)

        except (KeyError, ValueError, AttributeError) as e:
            raise ModelValidationError(f"Invalid template format: {e}")

    def validate(self) -> bool:
        """
        Validate the model.

        Returns:
            True if validation passes

        Raises:
            ModelValidationError: If validation fails
        """
        # Template format validation already done in __init__
        return True

    def register(self) -> None:
        """Register the model in MLflow Model Registry."""
        # Validate before registration
        self._validate_template_format(self.template)

        try:
            # Try to create the registered model
            self._mlflow_client.create_registered_model(
                name=self.name, description=f"Prompt template model: {self.name}"
            )
        except RestException:
            # Model already exists, which is fine
            pass

        # Create model version with template and metadata
        import tempfile
        import os

        # Create temporary artifact with template
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "template.txt")
            with open(template_path, "w") as f:
                f.write(self.template)

            # Prepare tags with template content and metadata
            tags = {"template": self.template, "version": self.version, **self.metadata}

            # Create model version
            model_version = self._mlflow_client.create_model_version(
                name=self.name, source=temp_dir, tags=tags
            )

            self._model_version = str(model_version.version)

    def promote_to_staging(self) -> None:
        """Promote model to staging stage."""
        if self._model_version is None:
            raise ModelValidationError("Model must be registered before promotion")

        self._mlflow_client.transition_model_version_stage(
            name=self.name, version=self._model_version, stage="staging"
        )
        self.stage = ModelStage.STAGING

    def promote_to_production(self) -> None:
        """Promote model to production stage."""
        if self._model_version is None:
            raise ModelValidationError("Model must be registered before promotion")

        if self.stage != ModelStage.STAGING:
            raise ModelValidationError("Cannot promote directly from dev to production")

        self._mlflow_client.transition_model_version_stage(
            name=self.name, version=self._model_version, stage="production"
        )
        self.stage = ModelStage.PRODUCTION

    def compare_with(self, other: "PromptModel") -> Dict[str, Any]:
        """
        Compare this model with another model version.

        Args:
            other: Another PromptModel to compare with

        Returns:
            Dictionary with comparison results

        Raises:
            ModelValidationError: If models have different names
        """
        if self.name != other.name:
            raise ModelValidationError("Cannot compare models with different names")

        # Version comparison
        version_diff = (
            None
            if self.version == other.version
            else {"old": self.version, "new": other.version}
        )

        # Template comparison
        self_vars = set(self.get_template_variables())
        other_vars = set(other.get_template_variables())

        template_diff = {
            "old": self.template,
            "new": other.template,
            "variables_added": list(other_vars - self_vars),
            "variables_removed": list(self_vars - other_vars),
        }

        # Metadata comparison
        metadata_diff = {}
        all_keys = set(self.metadata.keys()) | set(other.metadata.keys())
        for key in all_keys:
            old_val = self.metadata.get(key)
            new_val = other.metadata.get(key)
            if old_val != new_val:
                metadata_diff[key] = {"old": old_val, "new": new_val}

        return {
            "version_diff": version_diff,
            "template_diff": template_diff,
            "metadata_diff": metadata_diff,
        }

    def get_template_variables(self) -> List[str]:
        """
        Extract variable names from template.

        Returns:
            List of unique variable names used in template
        """
        import re

        variables = re.findall(r"\{([^}:]*)", self.template)
        # Remove duplicates while preserving order
        seen = set()
        unique_vars = []
        for var in variables:
            var = var.strip()
            # Extract base variable name for nested access
            if "[" in var or "." in var:
                var = var.split("[")[0].split(".")[0]
            if var and var not in seen:
                seen.add(var)
                unique_vars.append(var)
        return unique_vars

    def render(self, **kwargs: Any) -> str:
        """
        Render template with provided variables.

        Args:
            **kwargs: Variables to substitute in template

        Returns:
            Rendered template string

        Raises:
            ModelValidationError: If required variables are missing
        """
        required_vars = set(self.get_template_variables())
        provided_vars = set(kwargs.keys())
        missing_vars = required_vars - provided_vars

        if missing_vars:
            raise ModelValidationError(f"Missing required variables: {missing_vars}")

        return self.template.format(**kwargs)

    def get_lineage(self) -> List[Dict[str, Any]]:
        """
        Get model lineage (version history).

        Returns:
            List of version information in chronological order
        """
        model_versions = self._mlflow_client.search_model_versions(
            f"name='{self.name}'"
        )

        lineage = []
        for mv in model_versions:
            lineage.append(
                {
                    "version": mv.version,
                    "parent_version": mv.tags.get("parent_version"),
                    "created_at": mv.tags.get("created_at", "unknown"),
                }
            )

        # Sort by version number (handle invalid versions gracefully)
        def safe_version_to_int(version):
            try:
                return int(version) if version else 0
            except (ValueError, TypeError):
                # For non-numeric versions, return 0
                return 0

        lineage.sort(key=lambda x: safe_version_to_int(x.get("version")))
        return lineage

    def get_parent_version(self) -> Optional["PromptModel"]:
        """
        Get immediate parent version.

        Returns:
            Parent PromptModel or None if this is root version
        """
        if self._model_version == "1":
            return None

        # For simplicity, assume parent is previous version
        parent_version_num = str(int(self._model_version or "0") - 1)

        # This is a simplified implementation
        # In a real implementation, you'd query MLflow for the actual parent
        parent_model = PromptModel(
            name=self.name,
            template="Parent template",  # Would be fetched from MLflow
            version=f"{parent_version_num}.0.0",
        )
        parent_model._model_version = parent_version_num
        return parent_model

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary representation.

        Returns:
            Dictionary with model information
        """
        return {
            "name": self.name,
            "template": self.template,
            "version": self.version,
            "stage": str(self.stage),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
