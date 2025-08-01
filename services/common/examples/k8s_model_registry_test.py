#!/usr/bin/env python3
"""
Kubernetes deployment verification script for MLflow Model Registry.

This script tests the Model Registry functionality when deployed in k8s.
Run this after deploying to verify everything works correctly.
"""

import os
import sys
import time
from datetime import datetime

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from services.common.prompt_model_registry import PromptModel
from services.common.mlflow_model_registry_config import (
    verify_model_registry_setup,
    test_model_registry_connection,
)


def test_k8s_deployment():
    """Test Model Registry in k8s deployment."""
    print("🚀 MLflow Model Registry K8s Deployment Test")
    print("=" * 60)

    # 1. Verify configuration
    print("\n1. Verifying Model Registry configuration...")
    setup_info = verify_model_registry_setup()

    print(f"   Tracking URI: {setup_info['tracking_uri']}")
    print(f"   Registry URI: {setup_info['registry_uri']}")
    print(f"   Backend Store: {setup_info['backend_store']}")
    print(f"   Registry Accessible: {setup_info['registry_accessible']}")

    if not setup_info["registry_accessible"]:
        print("   ❌ Model Registry is not accessible!")
        print(
            "   Please ensure MLflow is running and MLFLOW_TRACKING_URI is set correctly."
        )
        return False

    print("   ✅ Model Registry is accessible")

    # 2. Test connection
    print("\n2. Testing Model Registry connection...")
    if test_model_registry_connection():
        print("   ✅ Connection successful")
    else:
        print("   ❌ Connection failed")
        return False

    # 3. Create and register a test model
    print("\n3. Creating and registering test model...")
    test_model = PromptModel(
        name=f"k8s-test-model-{int(time.time())}",
        template="Hello {user}! This is a test from {environment} at {timestamp}.",
        version="1.0.0",
        metadata={
            "deployment": "k8s",
            "test_time": datetime.now().isoformat(),
            "pod_name": os.getenv("HOSTNAME", "unknown"),
            "namespace": os.getenv("K8S_NAMESPACE", "default"),
        },
    )

    try:
        test_model.register()
        print(f"   ✅ Model registered: {test_model.name}")
    except Exception as e:
        print(f"   ❌ Registration failed: {e}")
        return False

    # 4. Test model operations
    print("\n4. Testing model operations...")

    # Render template
    rendered = test_model.render(
        user="K8s Tester",
        environment="Kubernetes",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    print(f"   ✅ Template rendered: {rendered}")

    # Get model info
    model_info = test_model.to_dict()
    print(
        f"   ✅ Model info retrieved: v{model_info['version']}, stage: {model_info['stage']}"
    )

    # 5. Test stage transitions
    print("\n5. Testing stage transitions...")
    try:
        test_model.promote_to_staging()
        print("   ✅ Promoted to staging")

        test_model.promote_to_production()
        print("   ✅ Promoted to production")
    except Exception as e:
        print(f"   ⚠️  Stage transition warning: {e}")
        print("   (This may be expected if using MLflow 2.9+ with deprecated stages)")

    # 6. Create version 2
    print("\n6. Creating new version...")
    test_model_v2 = PromptModel(
        name=test_model.name,
        template="Greetings {user}! 👋 This is v2 from {environment} at {timestamp}. Status: {status}",
        version="2.0.0",
        metadata={
            "deployment": "k8s",
            "test_time": datetime.now().isoformat(),
            "parent_version": "1.0.0",
            "improvements": "Added emoji and status field",
        },
    )

    try:
        test_model_v2.register()
        print("   ✅ Version 2 registered")
    except Exception as e:
        print(f"   ❌ Version 2 registration failed: {e}")
        return False

    # 7. Compare versions
    print("\n7. Comparing model versions...")
    comparison = test_model.compare_with(test_model_v2)
    print(f"   ✅ Version diff: {comparison['version_diff']}")
    print(f"   ✅ Variables added: {comparison['template_diff']['variables_added']}")

    # 8. Performance test
    print("\n8. Running performance test...")
    start_time = time.time()

    # Create 10 models rapidly
    for i in range(10):
        perf_model = PromptModel(
            name=f"k8s-perf-test-{int(time.time())}-{i}",
            template="Performance test {index} at {time}",
            version="1.0.0",
            metadata={"test": "performance", "index": i},
        )
        perf_model.register()

    elapsed = time.time() - start_time
    print(f"   ✅ Created 10 models in {elapsed:.2f}s ({elapsed / 10:.2f}s per model)")

    # 9. Summary
    print("\n" + "=" * 60)
    print("🎉 K8s Deployment Test Complete!")
    print("\nDeployment Info:")
    print(f"  Pod: {os.getenv('HOSTNAME', 'unknown')}")
    print(f"  Namespace: {os.getenv('K8S_NAMESPACE', 'default')}")
    print(f"  MLflow URI: {setup_info['tracking_uri']}")
    print(f"  Backend: {setup_info['backend_store']}")

    return True


if __name__ == "__main__":
    # Check if running in k8s
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        print("✅ Running in Kubernetes environment")
    else:
        print("⚠️  Not running in Kubernetes - using local MLflow")

    # Set MLflow URI if not set
    if not os.getenv("MLFLOW_TRACKING_URI"):
        print("⚠️  MLFLOW_TRACKING_URI not set, using default")
        os.environ["MLFLOW_TRACKING_URI"] = "http://mlflow:5000"

    # Run tests
    success = test_k8s_deployment()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
