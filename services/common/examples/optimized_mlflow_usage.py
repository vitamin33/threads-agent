"""
Example of optimized MLflow Model Registry usage in Kubernetes environment.

This example demonstrates:
- Connection pooling and caching
- Batch operations
- Performance monitoring
- Memory optimization
- Async operations
"""

import asyncio
import time
import logging
from typing import List
from services.common.prompt_model_registry_optimized import (
    OptimizedPromptModel,
    get_model_registry_optimizer,
)
from services.common.mlflow_performance_monitor import (
    get_performance_monitor,
    track_mlflow_operation,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@track_mlflow_operation("create_viral_content_models")
async def create_viral_content_models() -> List[OptimizedPromptModel]:
    """Create multiple viral content models with optimizations."""
    logger.info("Creating viral content models with optimizations...")

    # Define model templates
    model_templates = [
        {
            "name": "hook_generator_v2",
            "template": "Create a viral hook for {topic} targeting {audience} with {emotion} emotion",
            "version": "2.0.0",
            "metadata": {"type": "hook", "viral_score": 0.85},
        },
        {
            "name": "story_narrator_v3",
            "template": "Tell a compelling story about {subject} with {twist} twist for {platform}",
            "version": "3.0.0",
            "metadata": {"type": "story", "engagement_rate": 0.92},
        },
        {
            "name": "engagement_booster_v1",
            "template": "Boost engagement for {content} using {strategy} strategy on {platform}",
            "version": "1.0.0",
            "metadata": {"type": "engagement", "conversion_rate": 0.78},
        },
    ]

    # Create models efficiently
    models = []
    for template_data in model_templates:
        model = OptimizedPromptModel(
            name=template_data["name"],
            template=template_data["template"],
            version=template_data["version"],
            metadata=template_data["metadata"],
        )
        models.append(model)

    return models


@track_mlflow_operation("batch_register_models")
async def batch_register_models(models: List[OptimizedPromptModel]) -> None:
    """Register multiple models using batch operations."""
    logger.info(f"Batch registering {len(models)} models...")

    optimizer = get_model_registry_optimizer()
    result = await optimizer.batch_register_models_async(models)

    logger.info(
        f"Registration results: {len(result['success'])} successful, {len(result['failed'])} failed"
    )

    # Log any failures
    for failure in result["failed"]:
        logger.error(f"Failed to register {failure['name']}: {failure['error']}")


@track_mlflow_operation("promote_models_workflow")
async def promote_models_workflow(models: List[OptimizedPromptModel]) -> None:
    """Demonstrate optimized model promotion workflow."""
    logger.info("Starting model promotion workflow...")

    # Promote models through stages efficiently
    for model in models:
        try:
            # Promote to staging
            await model.promote_to_staging_async()
            logger.info(f"Promoted {model.name} to staging")

            # Simulate testing/validation
            await asyncio.sleep(0.1)  # Simulate validation time

            # Promote to production
            await model.promote_to_production_async()
            logger.info(f"Promoted {model.name} to production")

        except Exception as e:
            logger.error(f"Failed to promote {model.name}: {e}")


@track_mlflow_operation("compare_model_versions")
def compare_model_versions() -> None:
    """Demonstrate optimized model comparison."""
    logger.info("Comparing model versions...")

    # Create two versions of the same model
    model_v1 = OptimizedPromptModel(
        name="content_generator",
        template="Generate {content_type} for {audience}",
        version="1.0.0",
        metadata={"features": ["basic"], "performance": "good"},
    )

    model_v2 = OptimizedPromptModel(
        name="content_generator",
        template="Generate {content_type} for {audience} with {tone} tone and {length} length",
        version="2.0.0",
        metadata={"features": ["advanced", "tone_control"], "performance": "excellent"},
    )

    # Compare versions efficiently
    comparison = model_v2.compare_with_optimized(model_v1)

    logger.info(f"Version diff: {comparison['version_diff']}")
    logger.info(f"Variables added: {comparison['template_diff']['variables_added']}")
    logger.info(f"Metadata changes: {comparison['metadata_diff']}")


@track_mlflow_operation("render_templates_batch")
def render_templates_batch(models: List[OptimizedPromptModel]) -> List[str]:
    """Demonstrate efficient template rendering."""
    logger.info("Rendering templates in batch...")

    rendered_templates = []

    for model in models:
        try:
            # Use optimized rendering
            if "hook_generator" in model.name:
                rendered = model.render_optimized(
                    topic="AI productivity",
                    audience="tech entrepreneurs",
                    emotion="excitement",
                )
            elif "story_narrator" in model.name:
                rendered = model.render_optimized(
                    subject="startup success",
                    twist="unexpected failure turned into learning",
                    platform="LinkedIn",
                )
            elif "engagement_booster" in model.name:
                rendered = model.render_optimized(
                    content="product launch post",
                    strategy="storytelling",
                    platform="Twitter",
                )
            else:
                continue

            rendered_templates.append(rendered)
            logger.info(f"Rendered template for {model.name}")

        except Exception as e:
            logger.error(f"Failed to render {model.name}: {e}")

    return rendered_templates


@track_mlflow_operation("analyze_model_lineage")
async def analyze_model_lineage(models: List[OptimizedPromptModel]) -> None:
    """Demonstrate optimized lineage analysis."""
    logger.info("Analyzing model lineage...")

    for model in models:
        try:
            # Get lineage with caching
            lineage = await model.get_lineage_optimized()
            logger.info(f"Lineage for {model.name}: {len(lineage)} versions")

            # Log lineage summary
            if lineage:
                latest = lineage[-1]
                logger.info(
                    f"Latest version: {latest['version']} (stage: {latest['stage']})"
                )

        except Exception as e:
            logger.error(f"Failed to get lineage for {model.name}: {e}")


def demonstrate_performance_monitoring() -> None:
    """Demonstrate performance monitoring capabilities."""
    logger.info("Demonstrating performance monitoring...")

    monitor = get_performance_monitor()

    # Get performance metrics
    metrics = monitor.get_metrics()
    logger.info(f"Current metrics: {metrics}")

    # Get performance summary
    summary = monitor.get_performance_summary()
    logger.info(f"Performance summary: {summary}")

    # Detect performance issues
    issues = monitor.detect_performance_issues()
    if issues:
        logger.warning(f"Performance issues detected: {issues}")
    else:
        logger.info("No performance issues detected")

    # Export Prometheus metrics
    prometheus_metrics = monitor.export_prometheus_metrics()
    logger.info(f"Prometheus metrics exported: {len(prometheus_metrics)} characters")


def demonstrate_cache_warming() -> None:
    """Demonstrate cache warming for frequently accessed models."""
    logger.info("Warming up caches...")

    optimizer = get_model_registry_optimizer()

    # Pre-warm cache with frequently accessed models
    frequently_used_models = [
        "hook_generator_v2",
        "story_narrator_v3",
        "engagement_booster_v1",
    ]

    optimizer.warm_cache(frequently_used_models)
    logger.info("Cache warmed for frequently used models")


async def main():
    """Main demonstration function."""
    logger.info("Starting MLflow Performance Optimization Demo")

    try:
        # 1. Create models with optimizations
        models = await create_viral_content_models()
        logger.info(f"Created {len(models)} optimized models")

        # 2. Batch register models
        await batch_register_models(models)

        # 3. Promote models through workflow
        await promote_models_workflow(models)

        # 4. Compare model versions
        compare_model_versions()

        # 5. Render templates efficiently
        rendered = render_templates_batch(models)
        logger.info(f"Rendered {len(rendered)} templates")

        # 6. Analyze model lineage
        await analyze_model_lineage(models)

        # 7. Demonstrate performance monitoring
        demonstrate_performance_monitoring()

        # 8. Cache warming
        demonstrate_cache_warming()

        logger.info("Demo completed successfully!")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


def run_performance_comparison():
    """Compare performance between original and optimized implementations."""
    logger.info("Running performance comparison...")

    # Test original vs optimized model creation
    start_time = time.time()

    # Create 100 models with original implementation
    original_models = []
    for i in range(100):
        try:
            from services.common.prompt_model_registry import PromptModel

            model = PromptModel(
                name=f"test_model_{i}",
                template=f"Test template {{var1}} and {{var2}} for model {i}",
                version="1.0.0",
            )
            original_models.append(model)
        except ImportError:
            logger.warning("Original PromptModel not available for comparison")
            break

    original_time = time.time() - start_time

    # Create 100 models with optimized implementation
    start_time = time.time()

    optimized_models = []
    for i in range(100):
        model = OptimizedPromptModel(
            name=f"optimized_model_{i}",
            template=f"Optimized template {{var1}} and {{var2}} for model {i}",
            version="1.0.0",
        )
        optimized_models.append(model)

    optimized_time = time.time() - start_time

    # Report results
    logger.info(f"Original implementation: {original_time:.3f}s for 100 models")
    logger.info(f"Optimized implementation: {optimized_time:.3f}s for 100 models")

    if original_time > 0:
        improvement = ((original_time - optimized_time) / original_time) * 100
        logger.info(f"Performance improvement: {improvement:.1f}%")


if __name__ == "__main__":
    # Run performance comparison
    run_performance_comparison()

    # Run main demo
    asyncio.run(main())
