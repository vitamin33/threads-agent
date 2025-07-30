"""Integration hooks for performance monitoring with other services."""
import logging
from typing import Dict, Any

from services.performance_monitor.tasks import start_monitoring_task

logger = logging.getLogger(__name__)


def on_variant_posted(variant_data: Dict[str, Any]) -> None:
    """Hook to be called when a variant is posted to Threads.
    
    This should be integrated into the orchestrator or threads_adaptor
    to automatically start monitoring.
    """
    try:
        variant_id = variant_data.get("variant_id")
        persona_id = variant_data.get("persona_id")
        post_id = variant_data.get("post_id")
        expected_engagement_rate = variant_data.get("expected_engagement_rate", 0.06)

        if not all([variant_id, persona_id, post_id]):
            logger.error(f"Missing required fields in variant data: {variant_data}")
            return

        # Start monitoring asynchronously
        start_monitoring_task.delay(
            variant_id=variant_id,
            persona_id=persona_id,
            post_id=post_id,
            expected_engagement_rate=expected_engagement_rate
        )

        logger.info(f"Started monitoring for variant {variant_id}")

    except Exception as e:
        logger.error(f"Failed to start monitoring for variant: {e}")


def register_monitoring_hooks():
    """Register monitoring hooks with the event system.
    
    This should be called during service initialization.
    """
    # This would integrate with your event/hook system
    # For example:
    # event_bus.subscribe("variant.posted", on_variant_posted)
    pass
