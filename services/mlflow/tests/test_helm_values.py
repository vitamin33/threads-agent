"""Test suite for MLflow Helm chart configuration."""

import yaml
from pathlib import Path


class TestMLflowHelmValues:
    """Test cases for MLflow Helm chart values."""

    def test_helm_values_file_exists(self):
        """Test that the Helm values file exists."""
        values_path = Path(__file__).parent.parent / "helm" / "values.yaml"
        assert values_path.exists(), f"Helm values file not found at {values_path}"

    def test_helm_values_contains_required_fields(self):
        """Test that Helm values contain all required fields."""
        values_path = Path(__file__).parent.parent / "helm" / "values.yaml"

        with open(values_path, "r") as f:
            values = yaml.safe_load(f)

        # Check required top-level fields
        assert "image" in values
        assert "service" in values
        assert "ingress" in values
        assert "persistence" in values
        assert "postgresql" in values
        assert "minio" in values

    def test_mlflow_image_configuration(self):
        """Test MLflow image configuration."""
        values_path = Path(__file__).parent.parent / "helm" / "values.yaml"

        with open(values_path, "r") as f:
            values = yaml.safe_load(f)

        image = values.get("image", {})
        assert image.get("repository") == "burakince/mlflow"
        assert "tag" in image
        assert image.get("pullPolicy") == "IfNotPresent"

    def test_mlflow_service_configuration(self):
        """Test MLflow service configuration."""
        values_path = Path(__file__).parent.parent / "helm" / "values.yaml"

        with open(values_path, "r") as f:
            values = yaml.safe_load(f)

        service = values.get("service", {})
        assert service.get("type") == "LoadBalancer"
        assert service.get("port") == 5000

    def test_postgresql_backend_configuration(self):
        """Test PostgreSQL backend configuration."""
        values_path = Path(__file__).parent.parent / "helm" / "values.yaml"

        with open(values_path, "r") as f:
            values = yaml.safe_load(f)

        postgresql = values.get("postgresql", {})
        assert postgresql.get("enabled") is True
        assert "auth" in postgresql
        assert postgresql["auth"].get("database") == "mlflow"

    def test_minio_artifact_storage_configuration(self):
        """Test MinIO artifact storage configuration."""
        values_path = Path(__file__).parent.parent / "helm" / "values.yaml"

        with open(values_path, "r") as f:
            values = yaml.safe_load(f)

        minio = values.get("minio", {})
        assert minio.get("enabled") is True
        assert "defaultBuckets" in minio
        assert minio.get("defaultBuckets") == "mlflow-artifacts"
