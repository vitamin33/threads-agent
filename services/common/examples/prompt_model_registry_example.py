#!/usr/bin/env python3
"""
Example usage of the PromptModel Registry for CRA-296.

This demonstrates the complete workflow for managing prompt templates with MLflow Model Registry:
- Creating and registering prompt models
- Version management and stage promotion
- Model comparison and validation
- Lineage tracking
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from services.common.prompt_model_registry import PromptModel, ModelValidationError


def main():
    """Demonstrate PromptModel Registry features."""
    print("🚀 PromptModel Registry Demo - CRA-296 Implementation")
    print("=" * 60)

    # 1. Create a new prompt model
    print("\n1. Creating a new prompt model...")
    greeting_model = PromptModel(
        name="greeting-prompt",
        template="Hello {name}! Welcome to {platform}. Your {role} privileges are now active.",
        version="1.0.0",
        metadata={
            "author": "ai-team",
            "purpose": "user onboarding",
            "complexity": "low",
        },
    )
    # Mock MLflow client to avoid API calls
    from unittest.mock import Mock

    greeting_model._mlflow_client = Mock()
    print(f"   ✅ Created model: {greeting_model.name} v{greeting_model.version}")
    print(f"   📝 Template variables: {greeting_model.get_template_variables()}")

    # 2. Validate the model
    print("\n2. Validating model...")
    try:
        greeting_model.validate()
        print("   ✅ Model validation passed")
    except ModelValidationError as e:
        print(f"   ❌ Validation failed: {e}")
        return

    # 3. Register the model (commented out to avoid actual MLflow calls)
    print("\n3. Registering model to MLflow...")
    print("   ⚠️  Skipping actual registration in demo (requires MLflow server)")
    # greeting_model.register()

    # 4. Render template with variables
    print("\n4. Rendering template...")
    rendered = greeting_model.render(
        name="Alice", platform="ThreadsAgent", role="admin"
    )
    print(f"   📄 Rendered: {rendered}")

    # 5. Create an improved version
    print("\n5. Creating improved version...")
    greeting_v2 = PromptModel(
        name="greeting-prompt",
        template="Hello {name}! 👋 Welcome to {platform}. As a {role}, you have access to {features}.",
        version="2.0.0",
        metadata={
            "author": "ai-team",
            "purpose": "enhanced user onboarding",
            "complexity": "medium",
            "improvements": "Added emoji and features variable",
        },
    )
    # Mock MLflow client for v2 as well
    from unittest.mock import Mock

    greeting_v2._mlflow_client = Mock()
    print(f"   ✅ Created improved model: {greeting_v2.name} v{greeting_v2.version}")

    # 6. Compare model versions
    print("\n6. Comparing model versions...")
    comparison = greeting_model.compare_with(greeting_v2)
    print(
        f"   📊 Version change: {comparison['version_diff']['old']} → {comparison['version_diff']['new']}"
    )
    print(f"   ➕ Variables added: {comparison['template_diff']['variables_added']}")
    print(
        f"   📈 Complexity upgrade: {comparison['metadata_diff']['complexity']['old']} → {comparison['metadata_diff']['complexity']['new']}"
    )

    # 7. Demonstrate stage promotion workflow (mock mode)
    print("\n7. Demonstrating stage promotion workflow...")
    print(f"   📍 Initial stage: {greeting_model.stage}")

    # For demo purposes, mock the MLflow client to avoid API calls
    from unittest.mock import Mock

    greeting_model._mlflow_client = Mock()
    greeting_model._model_version = "1"

    print("   🔄 Promoting to staging...")
    greeting_model.promote_to_staging()
    print(f"   ✅ Current stage: {greeting_model.stage}")

    print("   🔄 Promoting to production...")
    greeting_model.promote_to_production()
    print(f"   ✅ Final stage: {greeting_model.stage}")

    # 8. Show model dictionary representation
    print("\n8. Model information...")
    model_info = greeting_model.to_dict()
    print("   📋 Model details:")
    for key, value in model_info.items():
        print(f"      {key}: {value}")

    # 9. Demonstrate validation failures
    print("\n9. Demonstrating validation...")
    try:
        PromptModel(
            name="invalid-model",
            template="Hello {name! Missing bracket",
            version="1.0.0",
        )
    except ValueError as e:
        print(f"   ✅ Validation caught invalid template: {e}")

    try:
        PromptModel(
            name="invalid-version", template="Hello {name}!", version="not.a.version"
        )
    except ValueError as e:
        print(f"   ✅ Validation caught invalid version: {e}")

    print("\n" + "=" * 60)
    print("🎉 PromptModel Registry Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("  ✅ Model creation and validation")
    print("  ✅ Template variable extraction")
    print("  ✅ Template rendering with type-aware validation")
    print("  ✅ Version comparison and diff analysis")
    print("  ✅ Stage promotion workflow (dev → staging → prod)")
    print("  ✅ Comprehensive error handling")
    print("  ✅ Metadata tracking and lineage")


if __name__ == "__main__":
    main()
