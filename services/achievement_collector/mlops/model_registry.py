"""Production model registry for MLOps job showcase.

Demonstrates:
- Model versioning and lifecycle management
- Performance tracking and comparison
- Automated deployment pipelines
- Model governance and compliance
"""

import asyncio
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model lifecycle status."""

    TRAINING = "training"
    VALIDATION = "validation"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class ModelMetrics:
    """Model performance metrics."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    business_impact_score: float
    inference_latency_ms: float
    cost_per_prediction: float

    def is_better_than(
        self, other: "ModelMetrics", weights: Dict[str, float] = None
    ) -> bool:
        """Compare models using weighted metrics."""
        if weights is None:
            weights = {
                "accuracy": 0.3,
                "business_impact_score": 0.4,
                "inference_latency_ms": 0.2,  # Lower is better
                "cost_per_prediction": 0.1,  # Lower is better
            }

        self_score = (
            self.accuracy * weights["accuracy"]
            + self.business_impact_score * weights["business_impact_score"]
            + (1 - min(self.inference_latency_ms / 1000, 1))
            * weights["inference_latency_ms"]
            + (1 - min(self.cost_per_prediction, 1)) * weights["cost_per_prediction"]
        )

        other_score = (
            other.accuracy * weights["accuracy"]
            + other.business_impact_score * weights["business_impact_score"]
            + (1 - min(other.inference_latency_ms / 1000, 1))
            * weights["inference_latency_ms"]
            + (1 - min(other.cost_per_prediction, 1)) * weights["cost_per_prediction"]
        )

        return self_score > other_score


@dataclass
class RegisteredModel:
    """Model registry entry."""

    model_id: str
    name: str
    version: str
    status: ModelStatus
    metrics: ModelMetrics
    model_path: str
    training_data_hash: str
    hyperparameters: Dict[str, Any]
    created_at: datetime
    created_by: str
    tags: List[str]
    description: str

    # Model lineage
    parent_model_id: Optional[str] = None
    training_job_id: Optional[str] = None
    experiment_id: Optional[str] = None

    # Deployment info
    deployed_at: Optional[datetime] = None
    deployment_config: Optional[Dict[str, Any]] = None
    traffic_percentage: float = 0.0


class ProductionModelRegistry:
    """Production-ready model registry for job interviews."""

    def __init__(self):
        self.models: Dict[str, RegisteredModel] = {}
        self.model_aliases: Dict[str, str] = {}  # alias -> model_id
        self.performance_history: Dict[str, List[Dict]] = {}

    async def register_model(
        self,
        name: str,
        model_path: str,
        metrics: ModelMetrics,
        hyperparameters: Dict[str, Any],
        training_data_hash: str,
        description: str = "",
        tags: List[str] = None,
        parent_model_id: Optional[str] = None,
    ) -> str:
        """Register a new model version."""

        # Generate model ID and version
        model_id = self._generate_model_id(name, training_data_hash)
        version = await self._get_next_version(name)

        # Create model entry
        model = RegisteredModel(
            model_id=model_id,
            name=name,
            version=version,
            status=ModelStatus.VALIDATION,
            metrics=metrics,
            model_path=model_path,
            training_data_hash=training_data_hash,
            hyperparameters=hyperparameters,
            created_at=datetime.utcnow(),
            created_by="system",  # In production, get from auth context
            tags=tags or [],
            description=description,
            parent_model_id=parent_model_id,
        )

        # Store model
        self.models[model_id] = model

        # Update aliases
        self.model_aliases[f"{name}:latest"] = model_id
        self.model_aliases[f"{name}:{version}"] = model_id

        logger.info(f"Registered model {name}:{version} with ID {model_id}")
        return model_id

    async def promote_model(
        self,
        model_id: str,
        target_status: ModelStatus,
        validation_results: Optional[Dict] = None,
    ) -> bool:
        """Promote model through deployment pipeline."""

        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")

        model = self.models[model_id]

        # Validate promotion path
        valid_transitions = {
            ModelStatus.TRAINING: [ModelStatus.VALIDATION, ModelStatus.FAILED],
            ModelStatus.VALIDATION: [ModelStatus.TESTING, ModelStatus.FAILED],
            ModelStatus.TESTING: [ModelStatus.STAGING, ModelStatus.FAILED],
            ModelStatus.STAGING: [ModelStatus.PRODUCTION, ModelStatus.DEPRECATED],
            ModelStatus.PRODUCTION: [ModelStatus.DEPRECATED],
        }

        if target_status not in valid_transitions.get(model.status, []):
            raise ValueError(
                f"Invalid transition from {model.status} to {target_status}"
            )

        # Special handling for production promotion
        if target_status == ModelStatus.PRODUCTION:
            success = await self._promote_to_production(model, validation_results)
            if not success:
                return False

        # Update status
        old_status = model.status
        model.status = target_status

        # Log promotion
        await self._log_model_event(
            model_id, "promotion", {"from": old_status.value, "to": target_status.value}
        )

        logger.info(f"Promoted model {model_id} from {old_status} to {target_status}")
        return True

    async def _promote_to_production(
        self, model: RegisteredModel, validation_results: Optional[Dict]
    ) -> bool:
        """Handle production deployment with safety checks."""

        # Check if model meets production quality gates
        quality_gates = {
            "min_accuracy": 0.85,
            "min_business_impact": 0.7,
            "max_latency_ms": 500,
            "max_cost_per_prediction": 0.10,
        }

        if (
            model.metrics.accuracy < quality_gates["min_accuracy"]
            or model.metrics.business_impact_score
            < quality_gates["min_business_impact"]
            or model.metrics.inference_latency_ms > quality_gates["max_latency_ms"]
            or model.metrics.cost_per_prediction
            > quality_gates["max_cost_per_prediction"]
        ):
            logger.warning(f"Model {model.model_id} failed quality gates")
            return False

        # Check if it's better than current production model
        current_prod = await self.get_production_model(model.name)
        if current_prod and not model.metrics.is_better_than(current_prod.metrics):
            logger.warning(f"Model {model.model_id} not better than current production")
            return False

        # Deprecate current production model
        if current_prod:
            await self.promote_model(current_prod.model_id, ModelStatus.DEPRECATED)

        # Update deployment info
        model.deployed_at = datetime.utcnow()
        model.traffic_percentage = 100.0

        # Update production alias
        self.model_aliases[f"{model.name}:production"] = model.model_id

        return True

    async def get_model(self, model_identifier: str) -> Optional[RegisteredModel]:
        """Get model by ID or alias."""

        # Try direct ID lookup
        if model_identifier in self.models:
            return self.models[model_identifier]

        # Try alias lookup
        if model_identifier in self.model_aliases:
            model_id = self.model_aliases[model_identifier]
            return self.models[model_id]

        return None

    async def get_production_model(self, model_name: str) -> Optional[RegisteredModel]:
        """Get current production model for a given name."""
        return await self.get_model(f"{model_name}:production")

    async def list_models(
        self,
        name_filter: Optional[str] = None,
        status_filter: Optional[ModelStatus] = None,
        tags_filter: Optional[List[str]] = None,
    ) -> List[RegisteredModel]:
        """List models with optional filters."""

        models = list(self.models.values())

        if name_filter:
            models = [m for m in models if name_filter in m.name]

        if status_filter:
            models = [m for m in models if m.status == status_filter]

        if tags_filter:
            models = [m for m in models if any(tag in m.tags for tag in tags_filter)]

        # Sort by creation date (newest first)
        models.sort(key=lambda m: m.created_at, reverse=True)

        return models

    async def compare_models(self, model_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple models for performance analysis."""

        models = []
        for model_id in model_ids:
            model = await self.get_model(model_id)
            if model:
                models.append(model)

        if len(models) < 2:
            raise ValueError("Need at least 2 models to compare")

        # Prepare comparison data
        comparison = {
            "models": [
                {
                    "id": m.model_id,
                    "name": f"{m.name}:{m.version}",
                    "status": m.status.value,
                    "metrics": asdict(m.metrics),
                    "created_at": m.created_at.isoformat(),
                }
                for m in models
            ],
            "best_performer": {},
            "metric_comparison": {},
        }

        # Find best performer for each metric
        metrics_to_compare = [
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "auc_roc",
            "business_impact_score",
        ]

        for metric in metrics_to_compare:
            values = [(getattr(m.metrics, metric), m.model_id) for m in models]
            best_value, best_model_id = max(values, key=lambda x: x[0])

            comparison["best_performer"][metric] = {
                "model_id": best_model_id,
                "value": best_value,
            }

        # For latency and cost, lower is better
        for metric in ["inference_latency_ms", "cost_per_prediction"]:
            values = [(getattr(m.metrics, metric), m.model_id) for m in models]
            best_value, best_model_id = min(values, key=lambda x: x[0])

            comparison["best_performer"][metric] = {
                "model_id": best_model_id,
                "value": best_value,
            }

        return comparison

    async def get_model_lineage(self, model_id: str) -> Dict[str, Any]:
        """Get model lineage and dependency graph."""

        model = await self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        # Build lineage tree
        lineage = {"root": model_id, "ancestors": [], "descendants": []}

        # Find ancestors
        current = model
        while current.parent_model_id:
            parent = await self.get_model(current.parent_model_id)
            if parent:
                lineage["ancestors"].append(
                    {
                        "id": parent.model_id,
                        "name": f"{parent.name}:{parent.version}",
                        "created_at": parent.created_at.isoformat(),
                    }
                )
                current = parent
            else:
                break

        # Find descendants
        for other_model in self.models.values():
            if other_model.parent_model_id == model_id:
                lineage["descendants"].append(
                    {
                        "id": other_model.model_id,
                        "name": f"{other_model.name}:{other_model.version}",
                        "created_at": other_model.created_at.isoformat(),
                    }
                )

        return lineage

    def _generate_model_id(self, name: str, training_data_hash: str) -> str:
        """Generate unique model ID."""
        content = f"{name}_{training_data_hash}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    async def _get_next_version(self, name: str) -> str:
        """Get next version number for model name."""
        existing_versions = []

        for model in self.models.values():
            if model.name == name:
                try:
                    version_num = int(model.version.replace("v", ""))
                    existing_versions.append(version_num)
                except ValueError:
                    continue

        if not existing_versions:
            return "v1"

        return f"v{max(existing_versions) + 1}"

    async def _log_model_event(self, model_id: str, event_type: str, event_data: Dict):
        """Log model events for audit trail."""

        if model_id not in self.performance_history:
            self.performance_history[model_id] = []

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": event_data,
        }

        self.performance_history[model_id].append(event)

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics for monitoring dashboard."""

        status_counts = {}
        for status in ModelStatus:
            status_counts[status.value] = len(
                [m for m in self.models.values() if m.status == status]
            )

        # Calculate average metrics for production models
        prod_models = [
            m for m in self.models.values() if m.status == ModelStatus.PRODUCTION
        ]

        avg_metrics = {}
        if prod_models:
            avg_metrics = {
                "accuracy": sum(m.metrics.accuracy for m in prod_models)
                / len(prod_models),
                "business_impact": sum(
                    m.metrics.business_impact_score for m in prod_models
                )
                / len(prod_models),
                "latency_ms": sum(m.metrics.inference_latency_ms for m in prod_models)
                / len(prod_models),
                "cost_per_prediction": sum(
                    m.metrics.cost_per_prediction for m in prod_models
                )
                / len(prod_models),
            }

        return {
            "total_models": len(self.models),
            "status_breakdown": status_counts,
            "production_models": len(prod_models),
            "average_production_metrics": avg_metrics,
            "model_families": len(set(m.name for m in self.models.values())),
            "deployment_success_rate": self._calculate_deployment_success_rate(),
        }

    def _calculate_deployment_success_rate(self) -> float:
        """Calculate deployment success rate."""
        total_promotions = 0
        successful_promotions = 0

        for events in self.performance_history.values():
            for event in events:
                if event["event_type"] == "promotion":
                    total_promotions += 1
                    if event["data"]["to"] != "failed":
                        successful_promotions += 1

        return successful_promotions / total_promotions if total_promotions > 0 else 1.0


# Demo function for job interviews
async def demonstrate_model_registry():
    """Demonstrate model registry capabilities for job interviews."""

    registry = ProductionModelRegistry()

    # Register initial model
    model1_metrics = ModelMetrics(
        accuracy=0.87,
        precision=0.85,
        recall=0.89,
        f1_score=0.87,
        auc_roc=0.92,
        business_impact_score=0.78,
        inference_latency_ms=245,
        cost_per_prediction=0.05,
    )

    model1_id = await registry.register_model(
        name="pr_impact_predictor",
        model_path="/models/pr_impact_v1.pkl",
        metrics=model1_metrics,
        hyperparameters={"n_estimators": 100, "max_depth": 8},
        training_data_hash="abc123",
        description="Initial PR impact prediction model",
        tags=["xgboost", "baseline"],
    )

    print(f"✅ Registered model: {model1_id}")

    # Promote through pipeline
    await registry.promote_model(model1_id, ModelStatus.TESTING)
    await registry.promote_model(model1_id, ModelStatus.STAGING)
    await registry.promote_model(model1_id, ModelStatus.PRODUCTION)

    print("✅ Promoted to production")

    # Register improved model
    model2_metrics = ModelMetrics(
        accuracy=0.91,
        precision=0.89,
        recall=0.93,
        f1_score=0.91,
        auc_roc=0.95,
        business_impact_score=0.85,
        inference_latency_ms=198,
        cost_per_prediction=0.04,
    )

    model2_id = await registry.register_model(
        name="pr_impact_predictor",
        model_path="/models/pr_impact_v2.pkl",
        metrics=model2_metrics,
        hyperparameters={"n_estimators": 150, "max_depth": 10, "learning_rate": 0.1},
        training_data_hash="def456",
        description="Improved model with feature engineering",
        tags=["xgboost", "optimized"],
        parent_model_id=model1_id,
    )

    print(f"✅ Registered improved model: {model2_id}")

    # Compare models
    comparison = await registry.compare_models([model1_id, model2_id])
    print("\n📊 Model Comparison:")
    for metric, data in comparison["best_performer"].items():
        print(f"  {metric}: {data['value']:.3f} (Model: {data['model_id'][:8]})")

    # Show registry stats
    stats = await registry.get_registry_stats()
    print("\n📈 Registry Stats:")
    print(f"  Total models: {stats['total_models']}")
    print(f"  Production models: {stats['production_models']}")
    print(f"  Deployment success rate: {stats['deployment_success_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(demonstrate_model_registry())
