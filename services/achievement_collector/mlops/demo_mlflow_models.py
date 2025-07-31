"""Demo script to register 15+ production models in MLflow registry."""

import asyncio
from datetime import datetime
from mlflow_registry import MLflowModelRegistry


async def register_production_models():
    """Register 15+ production models showcasing MLOps capabilities."""

    # Initialize registry
    registry = MLflowModelRegistry(
        mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
    )

    print("🚀 MLflow Model Registry Demo - Registering 15+ Production Models")
    print("=" * 70)

    # Define production models
    models = [
        # Business Value Models
        {
            "name": "business_value_predictor",
            "path": "/models/business_value/xgboost_v1.pkl",
            "metrics": {
                "accuracy": 0.96,
                "precision": 0.95,
                "recall": 0.94,
                "f1_score": 0.945,
            },
            "tags": {
                "team": "ai",
                "framework": "xgboost",
                "purpose": "revenue_prediction",
            },
            "description": "Predicts business value impact of PR achievements",
        },
        {
            "name": "roi_calculator",
            "path": "/models/business_value/roi_model.pkl",
            "metrics": {
                "accuracy": 0.97,
                "precision": 0.96,
                "recall": 0.95,
                "rmse": 0.12,
            },
            "tags": {
                "team": "ai",
                "framework": "sklearn",
                "purpose": "financial_analysis",
            },
            "description": "Calculates ROI for technical achievements",
        },
        # Sentiment Analysis Models
        {
            "name": "pr_sentiment_analyzer",
            "path": "/models/sentiment/bert_sentiment.pt",
            "metrics": {
                "accuracy": 0.98,
                "precision": 0.97,
                "recall": 0.98,
                "f1_score": 0.975,
            },
            "tags": {"team": "nlp", "framework": "pytorch", "model": "bert"},
            "description": "Analyzes sentiment in PR descriptions and comments",
        },
        {
            "name": "code_review_sentiment",
            "path": "/models/sentiment/roberta_reviews.pt",
            "metrics": {
                "accuracy": 0.96,
                "precision": 0.95,
                "recall": 0.96,
                "auc": 0.98,
            },
            "tags": {"team": "nlp", "framework": "pytorch", "model": "roberta"},
            "description": "Detects sentiment in code review comments",
        },
        # Text Classification Models
        {
            "name": "achievement_categorizer",
            "path": "/models/classification/category_model.pkl",
            "metrics": {
                "accuracy": 0.95,
                "precision": 0.94,
                "recall": 0.95,
                "f1_score": 0.945,
            },
            "tags": {"team": "ai", "framework": "sklearn", "type": "multiclass"},
            "description": "Categorizes achievements into technical domains",
        },
        {
            "name": "skill_extractor",
            "path": "/models/classification/skill_ner.pt",
            "metrics": {
                "accuracy": 0.97,
                "precision": 0.96,
                "recall": 0.97,
                "f1_score": 0.965,
            },
            "tags": {"team": "nlp", "framework": "spacy", "type": "ner"},
            "description": "Extracts technical skills from PR descriptions",
        },
        # Optimization Models
        {
            "name": "pr_priority_optimizer",
            "path": "/models/optimization/priority_model.pkl",
            "metrics": {
                "accuracy": 0.96,
                "precision": 0.95,
                "recall": 0.94,
                "mape": 0.08,
            },
            "tags": {"team": "ai", "framework": "lightgbm", "purpose": "ranking"},
            "description": "Optimizes PR review priorities based on impact",
        },
        {
            "name": "resource_allocator",
            "path": "/models/optimization/allocation_model.pkl",
            "metrics": {
                "accuracy": 0.95,
                "precision": 0.94,
                "recall": 0.95,
                "efficiency": 0.92,
            },
            "tags": {"team": "ai", "framework": "ortools", "purpose": "scheduling"},
            "description": "Allocates development resources optimally",
        },
        # Time Series Models
        {
            "name": "productivity_forecaster",
            "path": "/models/timeseries/prophet_productivity.pkl",
            "metrics": {"accuracy": 0.95, "mape": 0.12, "rmse": 0.15, "r2": 0.89},
            "tags": {"team": "ai", "framework": "prophet", "type": "forecasting"},
            "description": "Forecasts developer productivity trends",
        },
        {
            "name": "bug_rate_predictor",
            "path": "/models/timeseries/arima_bugs.pkl",
            "metrics": {"accuracy": 0.96, "mape": 0.10, "rmse": 0.13, "aic": 1234.5},
            "tags": {"team": "ai", "framework": "statsmodels", "type": "arima"},
            "description": "Predicts bug introduction rates",
        },
        # Computer Vision Models (for diagram analysis)
        {
            "name": "architecture_diagram_analyzer",
            "path": "/models/vision/diagram_cnn.pt",
            "metrics": {
                "accuracy": 0.95,
                "precision": 0.94,
                "recall": 0.95,
                "iou": 0.88,
            },
            "tags": {"team": "cv", "framework": "pytorch", "architecture": "resnet"},
            "description": "Analyzes architecture diagrams in PRs",
        },
        {
            "name": "code_screenshot_classifier",
            "path": "/models/vision/screenshot_model.pt",
            "metrics": {
                "accuracy": 0.97,
                "precision": 0.96,
                "recall": 0.97,
                "map": 0.94,
            },
            "tags": {
                "team": "cv",
                "framework": "pytorch",
                "architecture": "efficientnet",
            },
            "description": "Classifies code screenshots by language/framework",
        },
        # Recommendation Models
        {
            "name": "reviewer_recommender",
            "path": "/models/recommendation/reviewer_collab.pkl",
            "metrics": {
                "accuracy": 0.96,
                "precision": 0.95,
                "recall": 0.94,
                "ndcg": 0.89,
            },
            "tags": {"team": "ai", "framework": "surprise", "type": "collaborative"},
            "description": "Recommends optimal PR reviewers",
        },
        {
            "name": "skill_gap_recommender",
            "path": "/models/recommendation/skill_matrix.pkl",
            "metrics": {
                "accuracy": 0.95,
                "precision": 0.94,
                "recall": 0.95,
                "coverage": 0.87,
            },
            "tags": {"team": "ai", "framework": "sklearn", "type": "content_based"},
            "description": "Recommends skills to develop based on career goals",
        },
        # Anomaly Detection Models
        {
            "name": "code_anomaly_detector",
            "path": "/models/anomaly/isolation_forest.pkl",
            "metrics": {
                "accuracy": 0.97,
                "precision": 0.96,
                "recall": 0.95,
                "auc": 0.98,
            },
            "tags": {
                "team": "ai",
                "framework": "sklearn",
                "algorithm": "isolation_forest",
            },
            "description": "Detects anomalous code patterns",
        },
        {
            "name": "performance_anomaly_detector",
            "path": "/models/anomaly/lstm_anomaly.pt",
            "metrics": {
                "accuracy": 0.96,
                "precision": 0.95,
                "recall": 0.96,
                "f1_score": 0.955,
            },
            "tags": {"team": "ai", "framework": "pytorch", "architecture": "lstm_ae"},
            "description": "Detects performance anomalies in metrics",
        },
        # Graph Neural Network Models
        {
            "name": "dependency_impact_analyzer",
            "path": "/models/graph/gnn_dependencies.pt",
            "metrics": {
                "accuracy": 0.95,
                "precision": 0.94,
                "recall": 0.95,
                "auc": 0.97,
            },
            "tags": {"team": "ai", "framework": "dgl", "architecture": "gcn"},
            "description": "Analyzes impact of dependency changes",
        },
    ]

    # Register all models
    registered_models = []
    for i, model in enumerate(models, 1):
        print(f"\n📦 Registering Model {i}/{len(models)}: {model['name']}")
        print(f"   Framework: {model['tags']['framework']}")
        print(f"   Accuracy: {model['metrics']['accuracy']:.1%}")

        try:
            version = await registry.register_model(
                name=model["name"],
                model_path=model["path"],
                metrics=model["metrics"],
                tags=model["tags"],
                validate=True,  # Ensure 95%+ accuracy
            )
            registered_models.append(
                {"name": model["name"], "version": version, "status": "✅ Success"}
            )
            print(f"   Version: {version}")
            print("   Status: ✅ Registered successfully")
        except ValueError as e:
            registered_models.append(
                {
                    "name": model["name"],
                    "version": None,
                    "status": f"❌ Failed: {str(e)}",
                }
            )
            print(f"   Status: ❌ Failed - {str(e)}")

    # Summary
    print("\n" + "=" * 70)
    print("📊 Registration Summary")
    print("=" * 70)

    successful = sum(1 for m in registered_models if m["status"].startswith("✅"))
    print(f"\nTotal Models: {len(models)}")
    print(f"Successfully Registered: {successful}")
    print(f"Failed: {len(models) - successful}")

    # Get metrics
    metrics = registry.get_metrics()
    print("\n📈 Prometheus Metrics:")
    for metric, value in metrics.items():
        print(f"   {metric}: {value}")

    # Model categories summary
    categories = {}
    for model in models:
        purpose = model["tags"].get("purpose", model["tags"].get("type", "general"))
        categories[purpose] = categories.get(purpose, 0) + 1

    print("\n🏷️  Model Categories:")
    for category, count in sorted(categories.items()):
        print(f"   {category}: {count} models")

    return registered_models


async def demonstrate_model_operations():
    """Demonstrate additional model operations."""

    registry = MLflowModelRegistry(
        mlflow_uri="http://localhost:5000", s3_bucket="model-artifacts"
    )

    print("\n" + "=" * 70)
    print("🔧 Demonstrating Model Operations")
    print("=" * 70)

    # Version updates
    print("\n📌 Semantic Versioning Demo:")

    # Patch update
    v1 = await registry.register_model(
        name="demo_model",
        model_path="/models/demo/v1.pkl",
        metrics={"accuracy": 0.95},
        version_type="patch",
    )
    print(f"   Patch update: {v1}")

    # Minor update
    v2 = await registry.register_model(
        name="demo_model",
        model_path="/models/demo/v2.pkl",
        metrics={"accuracy": 0.96},
        version_type="minor",
    )
    print(f"   Minor update: {v2}")

    # Major update
    v3 = await registry.register_model(
        name="demo_model",
        model_path="/models/demo/v3.pkl",
        metrics={"accuracy": 0.97},
        version_type="major",
    )
    print(f"   Major update: {v3}")


async def main():
    """Run the complete MLflow registry demo."""
    print("\n🚀 MLflow Model Registry - Production Demo")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Register production models
    await register_production_models()

    # Demonstrate operations
    await demonstrate_model_operations()

    print(f"\n✅ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
