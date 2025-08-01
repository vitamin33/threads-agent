"""Test suite for MLflow configuration."""

import os
from unittest.mock import patch

from services.common.mlflow_config import get_mlflow_tracking_uri, configure_mlflow


class TestMLflowConfiguration:
    """Test cases for MLflow configuration."""

    def test_get_mlflow_tracking_uri_from_environment(self):
        """Test that MLflow tracking URI is read from environment."""
        # Arrange
        with patch.dict(
            os.environ, {"MLFLOW_TRACKING_URI": "http://mlflow.local:5000"}
        ):
            # Act
            uri = get_mlflow_tracking_uri()

            # Assert
            assert uri == "http://mlflow.local:5000"

    def test_get_mlflow_tracking_uri_returns_default_when_not_set(self):
        """Test that default URI is returned when environment variable is not set."""
        # Arrange
        with patch.dict(os.environ, {}, clear=True):
            # Act
            uri = get_mlflow_tracking_uri()

            # Assert
            assert uri == "http://localhost:5000"

    def test_configure_mlflow_sets_tracking_uri(self):
        """Test that configure_mlflow sets the tracking URI."""
        # Arrange
        with patch("mlflow.set_tracking_uri") as mock_set_tracking_uri:
            with patch.dict(
                os.environ, {"MLFLOW_TRACKING_URI": "http://mlflow.local:5000"}
            ):
                # Act
                configure_mlflow()

                # Assert
                mock_set_tracking_uri.assert_called_once_with(
                    "http://mlflow.local:5000"
                )
