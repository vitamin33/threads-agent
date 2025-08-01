"""Verify MLflow Model Registry setup and demonstrate usage."""

import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from services.common.mlflow_model_registry_config import verify_model_registry_setup
from services.common.prompt_model_registry import PromptModel
import json


def main():
    """Verify Model Registry setup and demonstrate functionality."""

    print("🔍 Verifying MLflow Model Registry Setup...")
    print("=" * 60)

    # Verify setup
    setup_info = verify_model_registry_setup()
    print(json.dumps(setup_info, indent=2))

    if not setup_info.get("registry_accessible"):
        print("\n❌ Model Registry is not accessible!")
        print("Please ensure MLflow server is running with a proper backend store.")
        print("\nTo start MLflow with Model Registry support:")
        print(
            "  1. With PostgreSQL: mlflow server --backend-store-uri postgresql://user:pass@localhost/mlflow"
        )
        print("  2. With SQLite: mlflow server --backend-store-uri sqlite:///mlflow.db")
        return

    print("\n✅ Model Registry is accessible!")

    # Demonstrate PromptModel usage
    print("\n" + "=" * 60)
    print("📝 Demonstrating PromptModel Usage...")
    print("=" * 60)

    # Create a sample prompt model
    model = PromptModel(
        name="customer-support-greeting",
        template="Hello {customer_name}! Thank you for contacting {company_name} support. How can I help you with {issue_type} today?",
        version="1.0.0",
        metadata={
            "author": "support-team",
            "category": "greeting",
            "language": "en",
            "tone": "friendly",
        },
    )

    print("\n1️⃣ Created PromptModel:")
    print(json.dumps(model.to_dict(), indent=2, default=str))

    print("\n2️⃣ Template Variables:")
    print(f"   Variables: {model.get_template_variables()}")

    print("\n3️⃣ Rendering Template:")
    rendered = model.render(
        customer_name="Alice", company_name="ThreadsAgent", issue_type="billing"
    )
    print(f"   Rendered: {rendered}")

    # Register the model
    print("\n4️⃣ Registering Model...")
    try:
        model.register()
        print("   ✅ Model registered successfully!")
    except Exception as e:
        print(f"   ❌ Registration failed: {e}")
        return

    # Create and compare a new version
    print("\n5️⃣ Creating New Version...")
    model_v2 = PromptModel(
        name="customer-support-greeting",
        template="Hi {customer_name}! Welcome to {company_name}. I see you need help with {issue_type}. Let me assist you right away!",
        version="2.0.0",
        metadata={
            "author": "support-team",
            "category": "greeting",
            "language": "en",
            "tone": "professional",
            "updated": "true",
        },
    )

    print("\n6️⃣ Comparing Versions:")
    comparison = model.compare_with(model_v2)
    print(json.dumps(comparison, indent=2))

    # Demonstrate stage promotion
    print("\n7️⃣ Stage Promotion Workflow:")
    print("   Current stage: DEV")

    try:
        print("   Promoting to STAGING...")
        model.promote_to_staging()
        print("   ✅ Promoted to STAGING")

        print("   Promoting to PRODUCTION...")
        model.promote_to_production()
        print("   ✅ Promoted to PRODUCTION")
    except Exception as e:
        print(f"   ❌ Promotion failed: {e}")

    print("\n" + "=" * 60)
    print("✨ Model Registry setup is working correctly!")
    print("=" * 60)


if __name__ == "__main__":
    main()
