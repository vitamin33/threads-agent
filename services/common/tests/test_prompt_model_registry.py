"""
Comprehensive tests for PromptModel Registry wrapper class.

This test file follows strict TDD practices and covers all requirements:
- Registering new prompt templates as models
- Versioning prompt templates
- Promoting models between stages (dev/staging/prod)
- Tracking model lineage
- Comparing different model versions
- Validating models before registration
"""

import pytest
import os
from unittest.mock import Mock, patch

# Import the class we'll be implementing (will fail initially - TDD!)
try:
    from services.common.prompt_model_registry import (
        PromptModel,
        ModelValidationError,
        ModelStage,
    )
except ImportError:
    # Expected to fail on first run - this is TDD!
    pass


class TestPromptModelRegistryBasics:
    """Test basic PromptModel functionality."""

    @pytest.fixture
    def mock_mlflow_client(self):
        """Mock MLflow client for testing."""
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            yield mock_client.return_value

    def test_prompt_model_initialization_with_required_params(self, mock_mlflow_client):
        """Test PromptModel can be initialized with required parameters."""
        # This will fail - we haven't implemented PromptModel yet
        model = PromptModel(
            name="test-prompt-model", template="Hello {name}!", version="1.0.0"
        )

        assert model.name == "test-prompt-model"
        assert model.template == "Hello {name}!"
        assert model.version == "1.0.0"
        assert model.stage == ModelStage.DEV  # Default stage

    def test_prompt_model_initialization_with_all_params(self, mock_mlflow_client):
        """Test PromptModel initialization with all parameters."""
        metadata = {"author": "test_user", "purpose": "greeting"}

        model = PromptModel(
            name="advanced-prompt",
            template="Advanced {greeting} for {name}!",
            version="2.1.0",
            stage=ModelStage.STAGING,
            metadata=metadata,
        )

        assert model.name == "advanced-prompt"
        assert model.template == "Advanced {greeting} for {name}!"
        assert model.version == "2.1.0"
        assert model.stage == ModelStage.STAGING
        assert model.metadata == metadata

    def test_prompt_model_invalid_template_raises_validation_error(
        self, mock_mlflow_client
    ):
        """Test that invalid template raises ModelValidationError."""
        with pytest.raises(ModelValidationError, match="Template cannot be empty"):
            PromptModel(
                name="test-model",
                template="",  # Empty template should fail validation
                version="1.0.0",
            )


class TestPromptModelRegistration:
    """Test model registration functionality."""

    @pytest.fixture
    def mock_mlflow_client(self):
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            client_instance = mock_client.return_value
            client_instance.create_registered_model.return_value = Mock(
                name="test-model"
            )
            client_instance.create_model_version.return_value = Mock(version="1")
            yield client_instance

    @pytest.fixture
    def sample_prompt_model(self, mock_mlflow_client):
        return PromptModel(
            name="test-prompt-model",
            template="Hello {name}! Welcome to {platform}.",
            version="1.0.0",
            metadata={"author": "test_user"},
        )

    def test_register_new_model_creates_registered_model(
        self, mock_mlflow_client, sample_prompt_model
    ):
        """Test registering a new model creates it in MLflow registry."""
        sample_prompt_model.register()

        # Should create the registered model
        mock_mlflow_client.create_registered_model.assert_called_once_with(
            name="test-prompt-model",
            description="Prompt template model: test-prompt-model",
        )

    def test_register_new_model_creates_model_version(
        self, mock_mlflow_client, sample_prompt_model
    ):
        """Test registration creates a model version with template and metadata."""
        sample_prompt_model.register()

        # Should create model version with template content
        mock_mlflow_client.create_model_version.assert_called_once()
        args, kwargs = mock_mlflow_client.create_model_version.call_args

        assert kwargs["name"] == "test-prompt-model"
        assert kwargs["source"] is not None  # Should have temporary artifact path
        assert kwargs["tags"]["template"] == "Hello {name}! Welcome to {platform}."
        assert kwargs["tags"]["version"] == "1.0.0"
        assert kwargs["tags"]["author"] == "test_user"

    def test_register_existing_model_creates_new_version(
        self, mock_mlflow_client, sample_prompt_model
    ):
        """Test registering existing model creates new version."""
        # Simulate model already exists
        from mlflow.exceptions import RestException

        mock_mlflow_client.create_registered_model.side_effect = RestException(
            {"error_code": "RESOURCE_ALREADY_EXISTS", "message": "Model already exists"}
        )

        sample_prompt_model.register()

        # Should still create model version even if model exists
        mock_mlflow_client.create_model_version.assert_called_once()

    def test_register_with_validation_failure_raises_error(self, mock_mlflow_client):
        """Test registration fails if model validation fails."""
        # Create model with valid template first, then change it to invalid for testing
        invalid_model = PromptModel(
            name="test-model",
            template="Valid template {name}",  # Start with valid template
            version="1.0.0",
        )
        # Manually set invalid template to test validation during registration
        invalid_model.template = "Invalid template with {unclosed_bracket"

        with pytest.raises(ModelValidationError, match="Invalid template format"):
            invalid_model.register()


class TestPromptModelStagePromotion:
    """Test model stage promotion workflow (dev → staging → prod)."""

    @pytest.fixture
    def mock_mlflow_client(self):
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            client_instance = mock_client.return_value
            client_instance.get_latest_versions.return_value = [
                Mock(version="1", current_stage="None")
            ]
            yield client_instance

    @pytest.fixture
    def registered_model(self, mock_mlflow_client):
        model = PromptModel(
            name="promotion-test-model",
            template="Test {content}",
            version="1.0.0",
            stage=ModelStage.DEV,
        )
        model._model_version = "1"  # Simulate registered model
        return model

    def test_promote_to_staging_updates_stage(
        self, mock_mlflow_client, registered_model
    ):
        """Test promoting model from dev to staging."""
        registered_model.promote_to_staging()

        assert registered_model.stage == ModelStage.STAGING
        mock_mlflow_client.transition_model_version_stage.assert_called_once_with(
            name="promotion-test-model", version="1", stage="staging"
        )

    def test_promote_to_production_updates_stage(
        self, mock_mlflow_client, registered_model
    ):
        """Test promoting model from staging to production."""
        registered_model.stage = ModelStage.STAGING
        registered_model.promote_to_production()

        assert registered_model.stage == ModelStage.PRODUCTION
        mock_mlflow_client.transition_model_version_stage.assert_called_once_with(
            name="promotion-test-model", version="1", stage="production"
        )

    def test_promote_from_dev_to_production_fails(
        self, mock_mlflow_client, registered_model
    ):
        """Test that promoting directly from dev to production fails."""
        with pytest.raises(
            ModelValidationError, match="Cannot promote directly from dev to production"
        ):
            registered_model.promote_to_production()

    def test_promote_unregistered_model_fails(self, mock_mlflow_client):
        """Test that promoting unregistered model fails."""
        unregistered_model = PromptModel(
            name="unregistered-model", template="Test {content}", version="1.0.0"
        )

        with pytest.raises(
            ModelValidationError, match="Model must be registered before promotion"
        ):
            unregistered_model.promote_to_staging()


class TestPromptModelValidation:
    """Test automated model validation before registration."""

    @pytest.fixture
    def mock_mlflow_client(self):
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            yield mock_client.return_value

    def test_validate_template_syntax_success(self, mock_mlflow_client):
        """Test validation passes for valid template syntax."""
        model = PromptModel(
            name="valid-model",
            template="Hello {name}! Your {item} is ready.",
            version="1.0.0",
        )

        # Should not raise exception
        result = model.validate()
        assert result is True

    def test_validate_template_with_unclosed_bracket_fails(self, mock_mlflow_client):
        """Test validation fails for template with unclosed bracket."""
        with pytest.raises(ModelValidationError, match="Invalid template format"):
            PromptModel(
                name="invalid-model",
                template="Hello {name! Missing closing bracket.",
                version="1.0.0",
            )

    def test_validate_template_with_unknown_formatter_fails(self, mock_mlflow_client):
        """Test validation fails for template with invalid formatter."""
        with pytest.raises(ModelValidationError, match="Invalid template format"):
            PromptModel(
                name="invalid-model",
                template="Hello {name:invalidformat}!",
                version="1.0.0",
            )

    def test_validate_empty_name_fails(self, mock_mlflow_client):
        """Test validation fails for empty model name."""
        with pytest.raises(ModelValidationError, match="Model name cannot be empty"):
            PromptModel(name="", template="Valid template", version="1.0.0")

    def test_validate_invalid_version_format_fails(self, mock_mlflow_client):
        """Test validation fails for invalid version format."""
        with pytest.raises(ModelValidationError, match="Invalid version format"):
            PromptModel(
                name="test-model", template="Valid template", version="not.a.version"
            )

    def test_validate_template_variables_consistency(self, mock_mlflow_client):
        """Test validation checks template variable consistency."""
        model = PromptModel(
            name="test-model",
            template="Hello {name}! Your {item} costs {price}.",
            version="1.0.0",
        )

        # Should extract variables correctly
        variables = model.get_template_variables()
        assert set(variables) == {"name", "item", "price"}


class TestPromptModelComparison:
    """Test model comparison capabilities."""

    @pytest.fixture
    def mock_mlflow_client(self):
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            yield mock_client.return_value

    @pytest.fixture
    def model_v1(self, mock_mlflow_client):
        return PromptModel(
            name="comparison-model",
            template="Hello {name}!",
            version="1.0.0",
            metadata={"author": "user1", "complexity": "low"},
        )

    @pytest.fixture
    def model_v2(self, mock_mlflow_client):
        return PromptModel(
            name="comparison-model",
            template="Hello {name}! Welcome to our {service}!",
            version="2.0.0",
            metadata={"author": "user2", "complexity": "medium"},
        )

    def test_compare_models_returns_differences(self, model_v1, model_v2):
        """Test comparing two model versions returns differences."""
        comparison = model_v1.compare_with(model_v2)

        assert comparison["version_diff"]["old"] == "1.0.0"
        assert comparison["version_diff"]["new"] == "2.0.0"
        assert comparison["template_diff"]["variables_added"] == ["service"]
        assert comparison["metadata_diff"]["complexity"]["old"] == "low"
        assert comparison["metadata_diff"]["complexity"]["new"] == "medium"

    def test_compare_models_identifies_template_changes(self, model_v1, model_v2):
        """Test comparison identifies template content changes."""
        comparison = model_v1.compare_with(model_v2)

        assert "Hello {name}!" in comparison["template_diff"]["old"]
        assert (
            "Hello {name}! Welcome to our {service}!"
            in comparison["template_diff"]["new"]
        )

    def test_compare_same_model_returns_no_differences(self, model_v1):
        """Test comparing model with itself returns no differences."""
        comparison = model_v1.compare_with(model_v1)

        assert comparison["version_diff"] is None
        assert comparison["template_diff"]["variables_added"] == []
        assert comparison["template_diff"]["variables_removed"] == []

    def test_compare_models_with_different_names_fails(
        self, model_v1, mock_mlflow_client
    ):
        """Test comparing models with different names fails."""
        different_model = PromptModel(
            name="different-model", template="Different template", version="1.0.0"
        )

        with pytest.raises(
            ModelValidationError, match="Cannot compare models with different names"
        ):
            model_v1.compare_with(different_model)


class TestPromptModelLineageTracking:
    """Test model lineage tracking functionality."""

    @pytest.fixture
    def mock_mlflow_client(self):
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            client_instance = mock_client.return_value
            client_instance.search_model_versions.return_value = [
                Mock(
                    version="1",
                    tags={"parent_version": None, "created_at": "2024-01-01"},
                ),
                Mock(
                    version="2",
                    tags={"parent_version": "1", "created_at": "2024-01-02"},
                ),
                Mock(
                    version="3",
                    tags={"parent_version": "2", "created_at": "2024-01-03"},
                ),
            ]
            yield client_instance

    @pytest.fixture
    def lineage_model(self, mock_mlflow_client):
        model = PromptModel(
            name="lineage-test-model", template="Test template v3", version="3.0.0"
        )
        model._model_version = "3"
        return model

    def test_get_lineage_returns_version_history(
        self, mock_mlflow_client, lineage_model
    ):
        """Test getting model lineage returns complete version history."""
        lineage = lineage_model.get_lineage()

        assert len(lineage) == 3
        assert lineage[0]["version"] == "1"
        assert lineage[1]["version"] == "2"
        assert lineage[2]["version"] == "3"
        assert lineage[1]["parent_version"] == "1"
        assert lineage[2]["parent_version"] == "2"

    def test_get_lineage_includes_creation_timestamps(
        self, mock_mlflow_client, lineage_model
    ):
        """Test lineage includes creation timestamps."""
        lineage = lineage_model.get_lineage()

        assert lineage[0]["created_at"] == "2024-01-01"
        assert lineage[1]["created_at"] == "2024-01-02"
        assert lineage[2]["created_at"] == "2024-01-03"

    def test_get_parent_version_returns_immediate_parent(
        self, mock_mlflow_client, lineage_model
    ):
        """Test getting immediate parent version."""
        parent = lineage_model.get_parent_version()

        assert parent is not None
        assert parent.version == "2.0.0"

    def test_get_parent_version_for_root_returns_none(self, mock_mlflow_client):
        """Test getting parent for root version returns None."""
        root_model = PromptModel(
            name="lineage-test-model", template="Root template", version="1.0.0"
        )
        root_model._model_version = "1"

        parent = root_model.get_parent_version()
        assert parent is None


class TestPromptModelUtilityMethods:
    """Test utility methods for PromptModel."""

    @pytest.fixture
    def mock_mlflow_client(self):
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            yield mock_client.return_value

    def test_get_template_variables_extracts_all_variables(self, mock_mlflow_client):
        """Test extracting all variables from template."""
        model = PromptModel(
            name="variable-test",
            template="Hello {name}! Your order {order_id} for {item} costs ${price:.2f}.",
            version="1.0.0",
        )

        variables = model.get_template_variables()
        assert set(variables) == {"name", "order_id", "item", "price"}

    def test_render_template_with_variables(self, mock_mlflow_client):
        """Test rendering template with provided variables."""
        model = PromptModel(
            name="render-test",
            template="Hello {name}! Your {item} costs ${price:.2f}.",
            version="1.0.0",
        )

        rendered = model.render(name="John", item="coffee", price=4.50)
        assert rendered == "Hello John! Your coffee costs $4.50."

    def test_render_template_missing_variables_raises_error(self, mock_mlflow_client):
        """Test rendering with missing variables raises error."""
        model = PromptModel(
            name="render-test",
            template="Hello {name}! Your {item} costs ${price:.2f}.",
            version="1.0.0",
        )

        with pytest.raises(ModelValidationError, match="Missing required variables"):
            model.render(name="John")  # Missing item and price

    def test_to_dict_returns_complete_model_info(self, mock_mlflow_client):
        """Test converting model to dictionary."""
        metadata = {"author": "test_user", "purpose": "greeting"}
        model = PromptModel(
            name="dict-test",
            template="Hello {name}!",
            version="1.0.0",
            stage=ModelStage.STAGING,
            metadata=metadata,
        )

        model_dict = model.to_dict()

        assert model_dict["name"] == "dict-test"
        assert model_dict["template"] == "Hello {name}!"
        assert model_dict["version"] == "1.0.0"
        assert model_dict["stage"] == "staging"
        assert model_dict["metadata"] == metadata
        assert "created_at" in model_dict


class TestModelStageEnum:
    """Test ModelStage enum functionality."""

    def test_model_stage_values(self):
        """Test ModelStage enum has correct values."""
        assert ModelStage.DEV.value == "dev"
        assert ModelStage.STAGING.value == "staging"
        assert ModelStage.PRODUCTION.value == "production"

    def test_model_stage_string_conversion(self):
        """Test ModelStage string conversion."""
        assert str(ModelStage.DEV) == "dev"
        assert str(ModelStage.STAGING) == "staging"
        assert str(ModelStage.PRODUCTION) == "production"


class TestModelValidationErrorException:
    """Test ModelValidationError exception."""

    def test_model_validation_error_message(self):
        """Test ModelValidationError carries correct message."""
        error_msg = "Invalid template format"
        error = ModelValidationError(error_msg)

        assert str(error) == error_msg
        assert isinstance(error, Exception)


class TestPromptModelEdgeCasesAndErrors:
    """Test edge cases and error conditions for PromptModel."""

    @pytest.fixture
    def mock_mlflow_client(self):
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            yield mock_client.return_value

    def test_whitespace_only_name_fails(self, mock_mlflow_client):
        """Test that whitespace-only name fails validation."""
        with pytest.raises(ModelValidationError, match="Model name cannot be empty"):
            PromptModel(
                name="   \t\n   ",  # Only whitespace
                template="Valid template",
                version="1.0.0",
            )

    def test_whitespace_only_template_fails(self, mock_mlflow_client):
        """Test that whitespace-only template fails validation."""
        with pytest.raises(ModelValidationError, match="Template cannot be empty"):
            PromptModel(
                name="test-model",
                template="   \t\n   ",  # Only whitespace
                version="1.0.0",
            )

    def test_complex_nested_brackets_validation(self, mock_mlflow_client):
        """Test validation with complex nested bracket scenarios."""
        # Valid nested brackets should work
        model = PromptModel(
            name="complex-template",
            template="Config: {config[database][host]} Port: {config[database][port]}",
            version="1.0.0",
        )
        assert model.template is not None

    def test_special_characters_in_template(self, mock_mlflow_client):
        """Test template with special characters and unicode."""
        model = PromptModel(
            name="unicode-model",
            template="Welcome {user}! 🎉 Price: {price}€ (αβγ) {emoji_var}",
            version="1.0.0",
        )

        rendered = model.render(user="João", price=100, emoji_var="🚀")
        assert "João" in rendered
        assert "🎉" in rendered
        assert "100€" in rendered

    def test_extremely_long_template(self, mock_mlflow_client):
        """Test handling of extremely long templates."""
        long_template = (
            "Long template: " + "A very long sentence. " * 1000 + "End with {variable}."
        )

        model = PromptModel(
            name="long-template-model", template=long_template, version="1.0.0"
        )

        rendered = model.render(variable="test")
        assert "End with test." in rendered
        assert len(rendered) > 20000

    def test_version_with_leading_zeros(self, mock_mlflow_client):
        """Test version format with leading zeros."""
        # Leading zeros should be valid but unusual
        model = PromptModel(
            name="zero-version", template="Test template {var}", version="01.02.03"
        )
        assert model.version == "01.02.03"

    def test_version_boundary_cases(self, mock_mlflow_client):
        """Test version format boundary cases."""
        # Very high version numbers
        model = PromptModel(
            name="high-version", template="Test template {var}", version="999.999.999"
        )
        assert model.version == "999.999.999"

        # Zero versions
        model_zero = PromptModel(
            name="zero-version", template="Test template {var}", version="0.0.0"
        )
        assert model_zero.version == "0.0.0"

    def test_template_with_no_variables(self, mock_mlflow_client):
        """Test template with no variables at all."""
        model = PromptModel(
            name="no-vars-model",
            template="This is a static template with no variables.",
            version="1.0.0",
        )

        variables = model.get_template_variables()
        assert len(variables) == 0

        rendered = model.render()
        assert rendered == "This is a static template with no variables."

    def test_template_with_duplicate_variables(self, mock_mlflow_client):
        """Test template with duplicate variable names."""
        model = PromptModel(
            name="duplicate-vars",
            template="Hello {name}! Nice to meet you, {name}. Your order ID is {name}.",
            version="1.0.0",
        )

        variables = model.get_template_variables()
        # Should only return unique variables
        assert variables == ["name"]

        rendered = model.render(name="John")
        assert rendered == "Hello John! Nice to meet you, John. Your order ID is John."

    def test_template_with_empty_variable_names(self, mock_mlflow_client):
        """Test template with empty variable names."""
        with pytest.raises(ModelValidationError, match="Invalid template format"):
            PromptModel(
                name="empty-var-model",
                template="Invalid template with {} empty variable",
                version="1.0.0",
            )

    def test_metadata_with_none_values(self, mock_mlflow_client):
        """Test metadata handling with None values."""
        model = PromptModel(
            name="none-metadata",
            template="Test {var}",
            version="1.0.0",
            metadata={"key1": None, "key2": "value", "key3": None},
        )

        assert model.metadata["key1"] is None
        assert model.metadata["key2"] == "value"
        assert model.metadata["key3"] is None

    def test_metadata_with_complex_data_types(self, mock_mlflow_client):
        """Test metadata with complex data types."""
        complex_metadata = {
            "list_data": [1, 2, 3],
            "dict_data": {"nested": {"deep": "value"}},
            "tuple_data": (1, 2, 3),
            "boolean": True,
            "float": 3.14159,
            "none_value": None,
        }

        model = PromptModel(
            name="complex-metadata",
            template="Test {var}",
            version="1.0.0",
            metadata=complex_metadata,
        )

        assert model.metadata["list_data"] == [1, 2, 3]
        assert model.metadata["dict_data"]["nested"]["deep"] == "value"
        assert model.metadata["boolean"] is True

    def test_register_with_mlflow_connection_error(self, mock_mlflow_client):
        """Test registration when MLflow server is unreachable."""
        from mlflow.exceptions import MlflowException

        mock_mlflow_client.create_registered_model.side_effect = MlflowException(
            "Connection failed"
        )

        model = PromptModel(
            name="connection-test", template="Test {var}", version="1.0.0"
        )

        with pytest.raises(MlflowException):
            model.register()

    def test_register_with_permission_denied(self, mock_mlflow_client):
        """Test registration when user lacks permissions."""
        from mlflow.exceptions import RestException

        mock_mlflow_client.create_model_version.side_effect = RestException(
            {"error_code": "PERMISSION_DENIED", "message": "User lacks permission"}
        )

        model = PromptModel(
            name="permission-test", template="Test {var}", version="1.0.0"
        )

        with pytest.raises(RestException):
            model.register()

    def test_promote_with_stage_transition_failure(self, mock_mlflow_client):
        """Test promotion when stage transition fails."""
        from mlflow.exceptions import RestException

        mock_mlflow_client.transition_model_version_stage.side_effect = RestException(
            {
                "error_code": "INVALID_STATE",
                "message": "Cannot transition to this stage",
            }
        )

        model = PromptModel(
            name="transition-test", template="Test {var}", version="1.0.0"
        )
        model._model_version = "1"

        with pytest.raises(RestException):
            model.promote_to_staging()

    def test_compare_models_with_very_different_templates(self, mock_mlflow_client):
        """Test comparison between drastically different models."""
        model1 = PromptModel(
            name="compare-test",
            template="Simple {greeting}",
            version="1.0.0",
            metadata={"type": "simple"},
        )

        model2 = PromptModel(
            name="compare-test",
            template="Complex {greeting} to {user} about {topic} with {details} and {timestamp}",
            version="2.0.0",
            metadata={
                "type": "complex",
                "features": ["multi-var"],
                "deprecated": False,
            },
        )

        comparison = model1.compare_with(model2)

        # Should detect all added variables
        assert set(comparison["template_diff"]["variables_added"]) == {
            "user",
            "topic",
            "details",
            "timestamp",
        }
        assert comparison["template_diff"]["variables_removed"] == []

        # Should detect metadata changes
        assert "type" in comparison["metadata_diff"]
        assert comparison["metadata_diff"]["type"]["old"] == "simple"
        assert comparison["metadata_diff"]["type"]["new"] == "complex"

    def test_get_lineage_with_malformed_data(self, mock_mlflow_client):
        """Test lineage retrieval with malformed MLflow data."""
        # Mock MLflow returning malformed version data
        mock_mlflow_client.search_model_versions.return_value = [
            Mock(version="invalid", tags={}),  # Missing required tags
            Mock(version="2", tags={"parent_version": "invalid"}),
            Mock(version="not_a_number", tags={"parent_version": None}),
        ]

        model = PromptModel(
            name="malformed-lineage", template="Test {var}", version="1.0.0"
        )

        # Should handle malformed data gracefully
        lineage = model.get_lineage()
        assert isinstance(lineage, list)
        # Implementation should handle invalid version numbers

    def test_render_with_format_specifier_edge_cases(self, mock_mlflow_client):
        """Test rendering with various format specifiers."""
        model = PromptModel(
            name="format-test",
            template="Price: ${price:.2f}, Count: {count:d}, Percent: {percent:.1%}, Name: {name:>10}",
            version="1.0.0",
        )

        rendered = model.render(price=19.999, count=42, percent=0.856, name="John")

        assert "$20.00" in rendered  # Rounded price
        assert "Count: 42" in rendered
        assert "85.6%" in rendered
        assert "      John" in rendered  # Right-aligned name

    def test_template_variables_with_format_specifiers(self, mock_mlflow_client):
        """Test variable extraction ignores format specifiers."""
        model = PromptModel(
            name="format-vars-test",
            template="Value: {number:.2f}, Text: {text:>10}, Hex: {hex_val:x}",
            version="1.0.0",
        )

        variables = model.get_template_variables()
        assert set(variables) == {"number", "text", "hex_val"}

    def test_concurrent_model_creation_race_condition(self, mock_mlflow_client):
        """Test handling of race condition during model creation."""
        from mlflow.exceptions import RestException

        # Simulate race condition: first call succeeds, second fails with "already exists"
        side_effects = [
            None,  # First model creation succeeds
            RestException(
                {"error_code": "RESOURCE_ALREADY_EXISTS", "message": "Model exists"}
            ),
        ]
        mock_mlflow_client.create_registered_model.side_effect = side_effects

        model1 = PromptModel(
            name="race-condition-test", template="Test {var}", version="1.0.0"
        )

        model2 = PromptModel(
            name="race-condition-test", template="Test {var}", version="1.0.1"
        )

        # Both should handle the situation gracefully
        model1.register()
        model2.register()  # Should handle "already exists" error


class TestPromptModelMemoryAndResourceUsage:
    """Test memory usage and resource handling edge cases."""

    @pytest.fixture
    def mock_mlflow_client(self):
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            yield mock_client.return_value

    def test_large_metadata_handling(self, mock_mlflow_client):
        """Test handling of very large metadata objects."""
        # Create large metadata object
        large_metadata = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}

        model = PromptModel(
            name="large-metadata-test",
            template="Test {var}",
            version="1.0.0",
            metadata=large_metadata,
        )

        assert len(model.metadata) == 1000
        assert model.metadata["key_500"] == "value_500" * 100

    def test_template_with_many_variables(self, mock_mlflow_client):
        """Test template with a large number of variables."""
        # Create template with many variables
        variables = [f"var_{i}" for i in range(100)]
        template = "Template: " + " ".join([f"{{{var}}}" for var in variables])

        model = PromptModel(name="many-vars-test", template=template, version="1.0.0")

        extracted_vars = model.get_template_variables()
        assert len(extracted_vars) == 100
        assert set(extracted_vars) == set(variables)

    def test_repeated_model_operations(self, mock_mlflow_client):
        """Test repeated operations don't cause memory leaks."""
        model = PromptModel(
            name="repeated-ops-test", template="Test {var}", version="1.0.0"
        )

        # Perform many operations
        for i in range(100):
            _ = model.get_template_variables()
            model.to_dict()
            model.validate()

        # Operations should still work correctly
        assert model.get_template_variables() == ["var"]


# Integration test class (marked as e2e)
@pytest.mark.e2e
class TestPromptModelRegistryIntegration:
    """Integration tests for PromptModel Registry with real MLflow server."""

    @pytest.fixture(scope="class")
    def mlflow_server_setup(self):
        """Set up MLflow server for integration testing."""
        import tempfile
        import os
        from services.common.mlflow_model_registry_config import (
            configure_mlflow_with_registry,
        )

        # Create temporary directory for MLflow artifacts
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variables for test MLflow server
            os.environ["MLFLOW_TRACKING_URI"] = f"file://{temp_dir}/mlruns"
            os.environ["MLFLOW_REGISTRY_URI"] = f"file://{temp_dir}/mlruns"

            # Configure MLflow
            config = configure_mlflow_with_registry()

            yield config

            # Cleanup
            if "MLFLOW_TRACKING_URI" in os.environ:
                del os.environ["MLFLOW_TRACKING_URI"]
            if "MLFLOW_REGISTRY_URI" in os.environ:
                del os.environ["MLFLOW_REGISTRY_URI"]

    @pytest.mark.skipif(
        os.getenv("MLFLOW_TRACKING_URI") is None,
        reason="Requires MLflow server (set MLFLOW_TRACKING_URI to run)",
    )
    def test_full_model_lifecycle_integration(self, mlflow_server_setup):
        """Test complete model lifecycle: register → promote → compare → track lineage."""
        from services.common.prompt_model_registry import PromptModel, ModelStage

        # Create initial model version
        import time
        unique_name = f"integration-test-model-{int(time.time())}"
        model_v1 = PromptModel(
            name=unique_name,
            template="Hello {name}! Welcome to {service}.",
            version="1.0.0",
            metadata={"author": "integration_test", "purpose": "testing"},
        )

        # Test registration
        model_v1.register()
        assert model_v1._model_version is not None

        # Test promotion to staging
        model_v1.promote_to_staging()
        assert model_v1.stage == ModelStage.STAGING

        # Test promotion to production
        model_v1.promote_to_production()
        assert model_v1.stage == ModelStage.PRODUCTION

        # Create second version
        model_v2 = PromptModel(
            name=unique_name,
            template="Hello {name}! Welcome to our {service}. Your session ID is {session_id}.",
            version="2.0.0",
            metadata={"author": "integration_test", "purpose": "enhanced_testing"},
        )

        model_v2.register()

        # Test comparison
        comparison = model_v1.compare_with(model_v2)
        assert comparison["version_diff"]["old"] == "1.0.0"
        assert comparison["version_diff"]["new"] == "2.0.0"
        assert "session_id" in comparison["template_diff"]["variables_added"]

        # Test lineage tracking
        lineage = model_v2.get_lineage()
        assert len(lineage) >= 2  # Should have at least 2 versions

        # Test template rendering
        rendered = model_v2.render(
            name="TestUser", service="MLflow", session_id="12345"
        )
        assert "TestUser" in rendered
        assert "MLflow" in rendered
        assert "12345" in rendered

    @pytest.mark.skipif(
        os.getenv("MLFLOW_TRACKING_URI") is None,
        reason="Requires MLflow server (set MLFLOW_TRACKING_URI to run)",
    )
    def test_concurrent_model_operations_integration(self, mlflow_server_setup):
        """Test concurrent model operations don't interfere with each other."""
        import threading
        from services.common.prompt_model_registry import PromptModel

        results = []
        errors = []

        def create_and_register_model(model_id):
            """Create and register a model in a separate thread."""
            try:
                model = PromptModel(
                    name=f"concurrent-test-model-{model_id}",
                    template=f"Hello {{name}}! This is model {model_id}.",
                    version="1.0.0",
                    metadata={"thread_id": model_id},
                )

                model.register()
                model.promote_to_staging()

                # Verify model was created correctly
                assert model._model_version is not None
                assert model.stage.value == "staging"

                results.append(f"Model {model_id} created successfully")

            except Exception as e:
                errors.append(f"Model {model_id} failed: {str(e)}")

        # Create multiple threads to test concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_and_register_model, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout

        # Verify results
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 5, (
            f"Expected 5 successful operations, got {len(results)}"
        )

    def test_model_persistence_and_retrieval_integration(self, mlflow_server_setup):
        """Test that models persist correctly and can be retrieved."""
        from services.common.prompt_model_registry import PromptModel
        from services.common.mlflow_model_registry_config import get_mlflow_client

        # Create and register a model
        original_model = PromptModel(
            name="persistence-test-model",
            template="Test persistence with {variable} and {another_var}.",
            version="1.0.0",
            metadata={"test_type": "persistence", "created_by": "integration_test"},
        )

        original_model.register()

        # Retrieve model information from MLflow directly
        client = get_mlflow_client()
        model_versions = client.search_model_versions("name='persistence-test-model'")

        assert len(model_versions) >= 1

        # Verify model data was stored correctly
        latest_version = model_versions[0]
        assert (
            latest_version.tags["template"]
            == "Test persistence with {variable} and {another_var}."
        )
        assert latest_version.tags["version"] == "1.0.0"
        assert latest_version.tags["test_type"] == "persistence"

    @pytest.mark.skipif(
        os.getenv("MLFLOW_TRACKING_URI") is None,
        reason="Requires MLflow server (set MLFLOW_TRACKING_URI to run)",
    )
    def test_model_registry_error_handling_integration(self, mlflow_server_setup):
        """Test error handling with real MLflow operations."""
        from services.common.prompt_model_registry import (
            PromptModel,
            ModelValidationError,
        )

        # Test duplicate model registration (should work - new version)
        model1 = PromptModel(
            name="error-handling-test", template="First version {var}", version="1.0.0"
        )

        model2 = PromptModel(
            name="error-handling-test", template="Second version {var}", version="2.0.0"
        )

        # Both should register successfully
        model1.register()
        model2.register()

        # Test promotion workflow validation
        model3 = PromptModel(
            name="promotion-error-test", template="Test {var}", version="1.0.0"
        )

        model3.register()

        # Should not be able to promote directly to production
        with pytest.raises(
            ModelValidationError, match="Cannot promote directly from dev to production"
        ):
            model3.promote_to_production()

        # Should work through proper workflow
        model3.promote_to_staging()
        model3.promote_to_production()  # Should work now

    @pytest.mark.skipif(
        os.getenv("MLFLOW_TRACKING_URI") is None,
        reason="Requires MLflow server (set MLFLOW_TRACKING_URI to run)",
    )
    def test_large_scale_model_operations_integration(self, mlflow_server_setup):
        """Test operations with multiple models and versions."""
        from services.common.prompt_model_registry import PromptModel

        models_created = []

        # Create multiple models with multiple versions each
        for model_idx in range(3):
            model_name = f"large-scale-test-{model_idx}-{int(time.time())}"

            for version_idx in range(3):
                model = PromptModel(
                    name=model_name,
                    template=f"Model {model_idx} version {version_idx}: {{data}}",
                    version=f"{version_idx + 1}.0.0",
                    metadata={"model_idx": model_idx, "version_idx": version_idx},
                )

                model.register()
                models_created.append(model)

        assert len(models_created) == 9  # 3 models × 3 versions

        # Test lineage for one of the models
        lineage = models_created[-1].get_lineage()
        assert len(lineage) >= 3  # Should have 3 versions

        # Test comparison between first and last version of a model
        first_version = models_created[0]  # Model 0, version 1.0.0
        last_version = models_created[2]  # Model 0, version 3.0.0

        comparison = first_version.compare_with(last_version)
        assert comparison["version_diff"]["old"] == "1.0.0"
        assert comparison["version_diff"]["new"] == "3.0.0"

    def test_template_validation_integration_with_mlflow(self, mlflow_server_setup):
        """Test template validation during actual MLflow operations."""
        from services.common.prompt_model_registry import (
            PromptModel,
            ModelValidationError,
        )

        # Test that invalid templates are caught before MLflow operations
        with pytest.raises(ModelValidationError):
            invalid_model = PromptModel(
                name="invalid-template-test",
                template="Invalid {template with unclosed bracket",
                version="1.0.0",
            )
            invalid_model.register()

        # Test that valid complex templates work
        complex_model = PromptModel(
            name="complex-template-test",
            template="""
            Multi-line template with:
            - Name: {name}
            - Price: ${price:.2f}
            - Items: {items}
            - Special chars: αβγ 🎉
            """,
            version="1.0.0",
        )

        complex_model.register()

        # Test rendering the complex template
        rendered = complex_model.render(
            name="Test Product", price=29.99, items="item1, item2, item3"
        )

        assert "Test Product" in rendered
        assert "$29.99" in rendered
        assert "item1, item2, item3" in rendered


class TestPromptModelPerformanceAndConcurrency:
    """Test performance characteristics and concurrent access scenarios."""

    @pytest.fixture
    def mock_mlflow_client(self):
        with patch(
            "services.common.prompt_model_registry.get_mlflow_client"
        ) as mock_client:
            client_instance = mock_client.return_value
            client_instance.create_registered_model.return_value = Mock(
                name="test-model"
            )
            client_instance.create_model_version.return_value = Mock(version="1")
            yield client_instance

    def test_template_validation_performance(self, mock_mlflow_client):
        """Test template validation performance with various template sizes."""
        import time

        # Test small template performance
        start_time = time.time()
        small_model = PromptModel(
            name="small-template-perf", template="Hello {name}!", version="1.0.0"
        )
        small_time = time.time() - start_time

        # Test medium template performance
        medium_template = "Medium template: " + " ".join(
            [f"{{var_{i}}}" for i in range(50)]
        )
        start_time = time.time()
        medium_model = PromptModel(
            name="medium-template-perf", template=medium_template, version="1.0.0"
        )
        medium_time = time.time() - start_time

        # Test large template performance
        large_template = "Large template: " + " ".join(
            [f"{{var_{i}}}" for i in range(500)]
        )
        start_time = time.time()
        large_model = PromptModel(
            name="large-template-perf", template=large_template, version="1.0.0"
        )
        large_time = time.time() - start_time

        # Validation should complete within reasonable time
        assert small_time < 0.1  # 100ms
        assert medium_time < 0.5  # 500ms
        assert large_time < 2.0  # 2 seconds

        # All models should be valid
        assert small_model.validate()
        assert medium_model.validate()
        assert large_model.validate()

    def test_concurrent_model_creation(self, mock_mlflow_client):
        """Test creating multiple models concurrently."""
        import threading
        import time

        results = []
        errors = []

        def create_model(model_id):
            """Create a model in a separate thread."""
            try:
                start_time = time.time()
                model = PromptModel(
                    name=f"concurrent-model-{model_id}",
                    template=f"Hello {{name}}! Model {model_id} at your service.",
                    version="1.0.0",
                    metadata={"model_id": model_id, "created_by": "thread"},
                )
                creation_time = time.time() - start_time

                results.append(
                    {
                        "model_id": model_id,
                        "creation_time": creation_time,
                        "template_vars": len(model.get_template_variables()),
                    }
                )
            except Exception as e:
                errors.append(f"Model {model_id}: {str(e)}")

        # Create 10 models concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_model, args=(i,))
            threads.append(thread)

        start_time = time.time()

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Verify all models were created successfully
        assert len(errors) == 0, f"Errors in concurrent creation: {errors}"
        assert len(results) == 10

        # Performance check - should complete within reasonable time
        assert total_time < 5.0  # 5 seconds for 10 models

        # Check individual creation times
        avg_creation_time = sum(r["creation_time"] for r in results) / len(results)
        assert avg_creation_time < 0.5  # Average under 500ms per model

    def test_concurrent_model_operations(self, mock_mlflow_client):
        """Test concurrent operations on the same model."""
        import threading
        import time

        # Create a base model
        base_model = PromptModel(
            name="concurrent-ops-test",
            template="Base template with {variable} and {another_var}",
            version="1.0.0",
            metadata={"test": "concurrent_operations"},
        )

        results = []
        errors = []

        def perform_operations(operation_id):
            """Perform various operations on the model."""
            try:
                start_time = time.time()

                # Perform different operations
                operations_results = {}

                # Template variable extraction
                operations_results["variables"] = base_model.get_template_variables()

                # Validation
                operations_results["validation"] = base_model.validate()

                # Dictionary conversion
                operations_results["dict"] = base_model.to_dict()

                # Template rendering
                operations_results["rendered"] = base_model.render(
                    variable=f"value_{operation_id}",
                    another_var=f"another_{operation_id}",
                )

                operation_time = time.time() - start_time

                results.append(
                    {
                        "operation_id": operation_id,
                        "operation_time": operation_time,
                        "results": operations_results,
                    }
                )

            except Exception as e:
                errors.append(f"Operation {operation_id}: {str(e)}")

        # Run 20 concurrent operations
        threads = []
        for i in range(20):
            thread = threading.Thread(target=perform_operations, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify all operations completed successfully
        assert len(errors) == 0, f"Errors in concurrent operations: {errors}"
        assert len(results) == 20

        # Check that all operations produced consistent results
        first_variables = results[0]["results"]["variables"]
        for result in results:
            assert result["results"]["variables"] == first_variables
            assert result["results"]["validation"] is True
            assert f"value_{result['operation_id']}" in result["results"]["rendered"]

    def test_memory_usage_with_large_operations(self, mock_mlflow_client):
        """Test memory usage during large-scale operations."""
        import gc

        # Create many models to test memory usage
        models = []

        for i in range(100):
            model = PromptModel(
                name=f"memory-test-{i}",
                template=f"Template {i} with {{var1}} and {{var2}} and {{var3}}",
                version="1.0.0",
                metadata={"index": i, "data": f"test_data_{i}" * 10},  # Some bulk data
            )
            models.append(model)

        # Perform operations on all models
        for model in models:
            variables = model.get_template_variables()
            assert len(variables) == 3

            rendered = model.render(var1="a", var2="b", var3="c")
            assert "Template" in rendered

            model_dict = model.to_dict()
            assert "name" in model_dict

        # Force garbage collection
        del models
        gc.collect()

        # Test should complete without memory issues

    def test_template_rendering_performance(self, mock_mlflow_client):
        """Test performance of template rendering with various complexities."""
        import time

        # Simple template
        simple_model = PromptModel(
            name="simple-render-perf", template="Hello {name}!", version="1.0.0"
        )

        # Complex template with many variables
        complex_template = "Complex: " + " - ".join([f"{{var_{i}}}" for i in range(20)])
        complex_model = PromptModel(
            name="complex-render-perf", template=complex_template, version="1.0.0"
        )

        # Template with format specifiers
        format_model = PromptModel(
            name="format-render-perf",
            template="Price: ${price:.2f}, Count: {count:d}, Percent: {percent:.1%}",
            version="1.0.0",
        )

        # Test simple rendering performance
        start_time = time.time()
        for _ in range(1000):
            simple_model.render(name="TestUser")
        simple_time = time.time() - start_time

        # Test complex rendering performance
        complex_vars = {f"var_{i}": f"value_{i}" for i in range(20)}
        start_time = time.time()
        for _ in range(100):
            complex_model.render(**complex_vars)
        complex_time = time.time() - start_time

        # Test format rendering performance
        start_time = time.time()
        for _ in range(1000):
            format_model.render(price=19.99, count=42, percent=0.856)
        format_time = time.time() - start_time

        # Performance assertions
        assert simple_time < 1.0  # 1000 simple renders in under 1 second
        assert complex_time < 2.0  # 100 complex renders in under 2 seconds
        assert format_time < 1.0  # 1000 format renders in under 1 second

    def test_model_comparison_performance(self, mock_mlflow_client):
        """Test performance of model comparison operations."""
        import time

        # Create models with different complexity levels
        simple_model1 = PromptModel(
            name="comparison-perf-test",
            template="Simple {greeting}",
            version="1.0.0",
            metadata={"type": "simple"},
        )

        simple_model2 = PromptModel(
            name="comparison-perf-test",
            template="Simple {greeting} to {user}",
            version="2.0.0",
            metadata={"type": "simple", "enhanced": True},
        )

        # Complex models
        complex_vars = [f"var_{i}" for i in range(50)]
        complex_template1 = "Complex: " + " ".join(
            [f"{{{var}}}" for var in complex_vars[:25]]
        )
        complex_template2 = "Complex: " + " ".join(
            [f"{{{var}}}" for var in complex_vars]
        )

        complex_model1 = PromptModel(
            name="complex-comparison-test",
            template=complex_template1,
            version="1.0.0",
            metadata={"complexity": "medium", "vars": 25},
        )

        complex_model2 = PromptModel(
            name="complex-comparison-test",
            template=complex_template2,
            version="2.0.0",
            metadata={"complexity": "high", "vars": 50, "enhanced": True},
        )

        # Test simple comparison performance
        start_time = time.time()
        for _ in range(100):
            comparison = simple_model1.compare_with(simple_model2)
            assert "user" in comparison["template_diff"]["variables_added"]
        simple_comparison_time = time.time() - start_time

        # Test complex comparison performance
        start_time = time.time()
        for _ in range(10):
            comparison = complex_model1.compare_with(complex_model2)
            assert len(comparison["template_diff"]["variables_added"]) == 25
        complex_comparison_time = time.time() - start_time

        # Performance assertions
        assert simple_comparison_time < 1.0  # 100 simple comparisons in under 1 second
        assert (
            complex_comparison_time < 2.0
        )  # 10 complex comparisons in under 2 seconds

    @pytest.mark.e2e
    @pytest.mark.skipif(
        os.getenv("MLFLOW_TRACKING_URI") is None,
        reason="Requires MLflow server (set MLFLOW_TRACKING_URI to run)",
    )
    def test_stress_test_with_real_mlflow(self):
        """Stress test with real MLflow operations (requires e2e environment)."""
        import tempfile
        import os
        import threading
        import time
        from services.common.mlflow_model_registry_config import (
            configure_mlflow_with_registry,
        )
        from services.common.prompt_model_registry import PromptModel

        # Set up temporary MLflow environment
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["MLFLOW_TRACKING_URI"] = f"file://{temp_dir}/mlruns"
            os.environ["MLFLOW_REGISTRY_URI"] = f"file://{temp_dir}/mlruns"

            configure_mlflow_with_registry()

            results = []
            errors = []

            def stress_test_worker(worker_id):
                """Worker function for stress testing."""
                try:
                    # Create multiple models per worker
                    for model_idx in range(5):
                        model_name = f"stress-test-{worker_id}-{model_idx}"

                        model = PromptModel(
                            name=model_name,
                            template=f"Stress test model {worker_id}-{model_idx}: {{data}} and {{info}}",
                            version="1.0.0",
                            metadata={"worker_id": worker_id, "model_idx": model_idx},
                        )

                        # Register model
                        start_time = time.time()
                        model.register()
                        register_time = time.time() - start_time

                        # Promote to staging
                        start_time = time.time()
                        model.promote_to_staging()
                        promote_time = time.time() - start_time

                        results.append(
                            {
                                "worker_id": worker_id,
                                "model_idx": model_idx,
                                "register_time": register_time,
                                "promote_time": promote_time,
                            }
                        )

                except Exception as e:
                    errors.append(f"Worker {worker_id}: {str(e)}")

            # Run stress test with multiple workers
            threads = []
            num_workers = 5

            start_time = time.time()

            for worker_id in range(num_workers):
                thread = threading.Thread(target=stress_test_worker, args=(worker_id,))
                threads.append(thread)
                thread.start()

            # Wait for all workers to complete
            for thread in threads:
                thread.join(timeout=60)  # 60 second timeout

            total_time = time.time() - start_time

            # Clean up environment variables
            if "MLFLOW_TRACKING_URI" in os.environ:
                del os.environ["MLFLOW_TRACKING_URI"]
            if "MLFLOW_REGISTRY_URI" in os.environ:
                del os.environ["MLFLOW_REGISTRY_URI"]

            # Verify stress test results
            assert len(errors) == 0, f"Stress test errors: {errors}"
            assert len(results) == num_workers * 5  # 5 workers × 5 models each

            # Performance checks
            assert total_time < 30.0  # Should complete within 30 seconds

            avg_register_time = sum(r["register_time"] for r in results) / len(results)
            avg_promote_time = sum(r["promote_time"] for r in results) / len(results)

            assert avg_register_time < 2.0  # Average registration under 2 seconds
            assert avg_promote_time < 1.0  # Average promotion under 1 second
