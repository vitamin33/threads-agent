"""Enhanced MLflow configuration with Model Registry support."""

import os
import mlflow
from mlflow.tracking import MlflowClient
from typing import Optional, Any


def configure_mlflow_with_registry() -> None:
    """Configure MLflow with Model Registry support using environment variables."""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    registry_uri = os.getenv("MLFLOW_REGISTRY_URI", tracking_uri)

    # Set tracking URI
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    # Also set the registry URI to the same location
    if registry_uri:
        mlflow.set_registry_uri(registry_uri)

    # Enable autologging for better tracking
    if os.getenv("MLFLOW_AUTOLOG_ENABLED", "true").lower() == "true":
        mlflow.autolog(log_models=True, log_input_examples=True, silent=True)


def get_mlflow_client() -> MlflowClient:
    """
    Get configured MLflow client.

    Returns:
        MlflowClient instance
    """
    # Ensure MLflow is configured
    if not mlflow.get_tracking_uri():
        configure_mlflow_with_registry()

    tracking_uri = mlflow.get_tracking_uri()
    registry_uri = mlflow.get_registry_uri()

    return MlflowClient(tracking_uri=tracking_uri, registry_uri=registry_uri)


def test_model_registry_connection() -> bool:
    """
    Test if Model Registry is accessible.

    Returns:
        True if registry is accessible, False otherwise
    """
    try:
        client = get_mlflow_client()
        # Try to list registered models
        client.search_registered_models(max_results=1)
        return True
    except Exception as e:
        print(f"Model Registry connection test failed: {e}")
        return False


def get_model_registry_info() -> dict[str, Any]:
    """
    Get information about the Model Registry setup.

    Returns:
        Dictionary with registry information
    """
    tracking_uri = mlflow.get_tracking_uri() or os.getenv(
        "MLFLOW_TRACKING_URI", "http://localhost:5000"
    )
    registry_uri = mlflow.get_registry_uri() or os.getenv(
        "MLFLOW_REGISTRY_URI", tracking_uri
    )

    info: dict[str, Any] = {
        "tracking_uri": tracking_uri,
        "registry_uri": registry_uri,
        "registry_accessible": test_model_registry_connection(),
        "backend_store": "unknown",
        "artifact_store": "local",
    }

    # Determine backend store type
    backend_store_uri = tracking_uri
    if backend_store_uri is not None and "postgresql" in backend_store_uri:
        info["backend_store"] = "postgresql"
    elif backend_store_uri is not None and "mysql" in backend_store_uri:
        info["backend_store"] = "mysql"
    elif backend_store_uri is not None and "sqlite" in backend_store_uri:
        info["backend_store"] = "sqlite"
    elif backend_store_uri is not None and "file:" in backend_store_uri:
        info["backend_store"] = "file"

    # Determine artifact store type
    artifact_uri = os.getenv("MLFLOW_ARTIFACT_URI", "")
    if "s3://" in artifact_uri:
        info["artifact_store"] = "s3"
    elif "gs://" in artifact_uri:
        info["artifact_store"] = "gcs"
    elif "wasbs://" in artifact_uri:
        info["artifact_store"] = "azure"

    return info


def create_or_get_registered_model(name: str, description: Optional[str] = None) -> str:
    """
    Create a registered model or get it if it already exists.

    Args:
        name: Model name
        description: Optional model description

    Returns:
        Model name
    """
    client = get_mlflow_client()

    try:
        # Try to create the model
        client.create_registered_model(
            name=name,
            description=description,
        )
        print(f"Created registered model: {name}")
    except Exception:
        # Model already exists
        print(f"Using existing registered model: {name}")

    return name


def verify_model_registry_setup() -> dict[str, Any]:
    """
    Verify Model Registry is properly set up.

    Returns:
        Dictionary with setup verification results
    """
    info = get_model_registry_info()

    # Additional checks
    checks = {
        "tracking_uri_set": bool(mlflow.get_tracking_uri()),
        "registry_uri_set": bool(mlflow.get_registry_uri()),
        "client_accessible": False,
        "can_create_model": False,
    }

    try:
        client = get_mlflow_client()
        checks["client_accessible"] = True

        # Try to create a test model (will fail if exists, but that's ok)
        try:
            client.create_registered_model("_test_model_registry_")
            client.delete_registered_model("_test_model_registry_")
            checks["can_create_model"] = True
        except Exception:
            # Model might already exist or no permissions
            pass
    except Exception:
        pass

    return {**info, "checks": checks}
