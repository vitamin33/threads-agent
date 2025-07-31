"""Test suite for MLflow Model Registry following TDD principles."""

import pytest
from unittest.mock import patch, AsyncMock

from mlops.mlflow_registry import MLflowModelRegistry


class TestMLflowModelRegistry:
    """Test cases for MLflow Model Registry implementation."""

    @pytest.mark.asyncio
    async def test_mlflow_server_connection_returns_health_status(self):
        """Test that MLflow server connection can be verified."""
        # Arrange
        registry = MLflowModelRegistry(
            mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
        )

        with patch("mlops.mlflow_registry.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            is_healthy = await registry.check_health()

            # Assert
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_check_health_makes_http_request_to_mlflow_server(self):
        """Test that health check actually contacts MLflow server."""
        # Arrange
        registry = MLflowModelRegistry(
            mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
        )

        with patch("mlops.mlflow_registry.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            is_healthy = await registry.check_health()

            # Assert
            assert is_healthy is True
            mock_client.get.assert_called_once_with("/health")

    @pytest.mark.asyncio
    async def test_register_model_returns_model_version(self):
        """Test that registering a model returns a version string."""
        # Arrange
        registry = MLflowModelRegistry(
            mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
        )

        model_name = "business_value_predictor"
        model_path = "/tmp/model.pkl"
        metrics = {"accuracy": 0.95, "precision": 0.93, "recall": 0.94}

        with patch("mlops.mlflow_registry.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            version = await registry.register_model(
                name=model_name,
                model_path=model_path,
                metrics=metrics,
                tags={"team": "ai", "framework": "sklearn"},
            )

            # Assert
            assert version is not None
            assert isinstance(version, str)
            assert version.startswith("1")

    @pytest.mark.asyncio
    async def test_register_model_calls_mlflow_api(self):
        """Test that model registration actually calls MLflow API."""
        # Arrange
        registry = MLflowModelRegistry(
            mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
        )

        with patch("mlops.mlflow_registry.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "registered_model": {
                    "name": "business_value_predictor",
                    "latest_versions": [{"version": "1", "run_id": "abc123"}],
                }
            }
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            version = await registry.register_model(
                name="business_value_predictor",
                model_path="/tmp/model.pkl",
                metrics={"accuracy": 0.95},
                tags={"team": "ai"},
            )

            # Assert
            assert version == "1.0.0"  # Now using semantic versioning
            # Verify MLflow API was called
            mock_client.post.assert_called()

    @pytest.mark.asyncio
    async def test_semantic_versioning_increments_correctly(self):
        """Test that model versions follow semantic versioning rules."""
        # Arrange
        registry = MLflowModelRegistry(
            mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
        )

        with patch("mlops.mlflow_registry.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Register first model
            version1 = await registry.register_model(
                name="sentiment_analyzer",
                model_path="/tmp/model_v1.pkl",
                metrics={"accuracy": 0.92},
            )

            # Register minor update (performance improvement)
            version2 = await registry.register_model(
                name="sentiment_analyzer",
                model_path="/tmp/model_v2.pkl",
                metrics={"accuracy": 0.94},
                version_type="minor",
            )

            # Register major update (architecture change)
            version3 = await registry.register_model(
                name="sentiment_analyzer",
                model_path="/tmp/model_v3.pkl",
                metrics={"accuracy": 0.96},
                version_type="major",
            )

            # Assert semantic versioning
            assert version1 == "1.0.0"
            assert version2 == "1.1.0"
            assert version3 == "2.0.0"

    @pytest.mark.asyncio
    async def test_model_validation_rejects_low_accuracy_models(self):
        """Test that models with accuracy below 95% are rejected."""
        # Arrange
        registry = MLflowModelRegistry(
            mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
        )

        # Act & Assert - Low accuracy model should be rejected
        with pytest.raises(
            ValueError, match="Model accuracy 0.90 is below minimum threshold 0.95"
        ):
            await registry.register_model(
                name="low_accuracy_model",
                model_path="/tmp/bad_model.pkl",
                metrics={"accuracy": 0.90, "precision": 0.88, "recall": 0.92},
                validate=True,
            )

    @pytest.mark.asyncio
    async def test_model_validation_accepts_high_accuracy_models(self):
        """Test that models with accuracy >= 95% are accepted."""
        # Arrange
        registry = MLflowModelRegistry(
            mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
        )

        with patch("mlops.mlflow_registry.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act - High accuracy model should be accepted
            version = await registry.register_model(
                name="high_accuracy_model",
                model_path="/tmp/good_model.pkl",
                metrics={"accuracy": 0.96, "precision": 0.95, "recall": 0.97},
                validate=True,
            )

            # Assert
            assert version == "1.0.0"

    @pytest.mark.asyncio
    async def test_prometheus_metrics_are_exposed(self):
        """Test that registry exposes Prometheus metrics."""
        # Arrange
        registry = MLflowModelRegistry(
            mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
        )

        # Act
        metrics = registry.get_metrics()

        # Assert
        assert "model_registration_total" in metrics
        assert "model_validation_failures" in metrics
        assert "model_inference_latency_seconds" in metrics
        assert "model_accuracy_gauge" in metrics

    @pytest.mark.asyncio
    async def test_comprehensive_mlflow_integration(self):
        """Test comprehensive MLflow integration with multiple models."""
        # Arrange
        registry = MLflowModelRegistry(
            mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
        )

        with patch("mlops.mlflow_registry.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act - Register multiple models
            models_registered = []

            # Register business value model
            version1 = await registry.register_model(
                name="business_value_predictor",
                model_path="/tmp/bv_model.pkl",
                metrics={"accuracy": 0.96, "precision": 0.95},
                tags={"framework": "xgboost"},
                validate=True,
            )
            models_registered.append(version1)

            # Register sentiment analysis model
            version2 = await registry.register_model(
                name="sentiment_analyzer",
                model_path="/tmp/sentiment_model.pt",
                metrics={"accuracy": 0.98, "f1_score": 0.97},
                tags={"framework": "pytorch"},
                validate=True,
            )
            models_registered.append(version2)

            # Assert
            assert len(models_registered) == 2
            assert all(v == "1.0.0" for v in models_registered)

            # Verify health check still works
            is_healthy = await registry.check_health()
            assert is_healthy is True

            # Verify metrics are available
            metrics = registry.get_metrics()
            assert isinstance(metrics, dict)
            assert len(metrics) >= 4
