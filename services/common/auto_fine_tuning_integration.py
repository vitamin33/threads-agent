"""Integration module for Auto-Fine-Tuning Pipeline with persona runtime.

This module demonstrates how the fine-tuning pipeline integrates with the existing
persona runtime to provide automated model improvement based on performance data.
"""

import os
from typing import Dict, Any
from datetime import datetime

from services.common.fine_tuning_pipeline import (
    FineTuningPipeline,
    PipelineConfig,
    MLflowModelRegistry,
)


class PersonaRuntimeIntegration:
    """Integration layer between fine-tuning pipeline and persona runtime."""

    def __init__(self):
        self.pipeline_config = PipelineConfig(
            training_data_threshold=int(os.getenv("FINE_TUNING_MIN_EXAMPLES", "100")),
            engagement_threshold=float(
                os.getenv("FINE_TUNING_ENGAGEMENT_THRESHOLD", "0.06")
            ),
            weekly_schedule="0 2 * * 0",  # Sunday 2 AM
            a_b_test_duration_hours=168,  # 1 week
        )
        self.pipeline = FineTuningPipeline(config=self.pipeline_config)

    def should_trigger_fine_tuning(self) -> bool:
        """Determine if fine-tuning should be triggered based on performance metrics."""
        # Check if enough time has passed since last fine-tuning
        if self.pipeline.last_run_timestamp:
            days_since_last_run = (
                datetime.now() - self.pipeline.last_run_timestamp
            ).days
            if days_since_last_run < 7:  # Weekly schedule
                return False

        # Check if we have sufficient recent data with performance above baseline
        # This would query the database for recent posts with high engagement
        return True

    def run_fine_tuning_cycle(self) -> Dict[str, Any]:
        """Execute a complete fine-tuning cycle and return results."""
        if not self.should_trigger_fine_tuning():
            return {
                "status": "skipped",
                "reason": "schedule_not_ready",
                "next_run": "next_sunday_2am",
            }

        try:
            # Run the pipeline
            result = self.pipeline.run()

            if result.status == "success" and result.model_version:
                # Update the persona runtime to use the new model
                self._update_persona_runtime_models(result.model_version)

                # Register the model in MLflow Registry
                registry = MLflowModelRegistry()
                registered_model = registry.register_fine_tuned_model(
                    model_version=result.model_version,
                    performance_metrics={
                        "training_examples": len(
                            result.training_data_batch.hook_examples
                        )
                        if result.training_data_batch
                        else 0,
                        "base_model": result.model_version.base_model or "",
                    },
                )

                return {
                    "status": "success",
                    "model_id": result.model_version.model_id,
                    "training_job_id": result.model_version.training_job_id,
                    "mlflow_model_name": registered_model.name,
                    "mlflow_model_version": registered_model.version,
                    "next_phase": "a_b_testing",
                }

            return {
                "status": result.status,
                "reason": result.reason,
                "training_examples": len(result.training_data_batch.hook_examples)
                if result.training_data_batch
                else 0,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "recommendation": "check_logs_and_retry",
            }

    def _update_persona_runtime_models(self, model_version) -> None:
        """Update environment variables to use the new fine-tuned model."""
        # In production, this would update the HOOK_MODEL environment variable
        # and potentially restart the persona runtime services
        new_hook_model = model_version.model_id

        print(f"🎯 Fine-tuning complete! New HOOK_MODEL: {new_hook_model}")
        print("📈 Expected improvements:")
        print("   - Higher engagement rates (6%+ target)")
        print("   - Better hook quality and relevance")
        print("   - Reduced cost per engagement")

        # In a real deployment, you would:
        # 1. Update Kubernetes ConfigMap with new model ID
        # 2. Trigger rolling update of persona-runtime pods
        # 3. Gradually roll out with A/B testing

        # For now, set environment variable for current session
        os.environ["HOOK_MODEL"] = new_hook_model
        os.environ["FINE_TUNED_MODEL_VERSION"] = model_version.version or "1.0.0"


def demonstrate_fine_tuning_workflow():
    """Demonstrate the complete fine-tuning workflow."""
    print("🚀 Auto-Fine-Tuning Pipeline Demonstration")
    print("=" * 50)

    # Initialize integration
    integration = PersonaRuntimeIntegration()

    print("📊 Current Configuration:")
    print(
        f"   Minimum training examples: {integration.pipeline_config.training_data_threshold}"
    )
    print(
        f"   Engagement threshold: {integration.pipeline_config.engagement_threshold}"
    )
    print(f"   Weekly schedule: {integration.pipeline_config.weekly_schedule}")
    print(
        f"   A/B test duration: {integration.pipeline_config.a_b_test_duration_hours} hours"
    )

    print("\n🔄 Running fine-tuning cycle...")
    result = integration.run_fine_tuning_cycle()

    print(f"\n✅ Fine-tuning result: {result['status']}")
    for key, value in result.items():
        if key != "status":
            print(f"   {key}: {value}")

    if result["status"] == "success":
        print("\n🎉 Success! The persona runtime will now use the fine-tuned model.")
        print("📈 Expected benefits:")
        print("   - Improved engagement rates")
        print("   - Better content quality")
        print("   - Cost optimization")
        print("\n📅 Next steps:")
        print("   - Monitor A/B test performance")
        print("   - Compare against baseline metrics")
        print("   - Automatic promotion to production if successful")


if __name__ == "__main__":
    demonstrate_fine_tuning_workflow()
