"""MLflow configuration for the threads-agent project."""

import os
import mlflow


def get_mlflow_tracking_uri() -> str:
    """Get MLflow tracking URI from environment or return default."""
    return os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")


def configure_mlflow() -> None:
    """Configure MLflow with the tracking URI."""
    tracking_uri = get_mlflow_tracking_uri()
    mlflow.set_tracking_uri(tracking_uri)
