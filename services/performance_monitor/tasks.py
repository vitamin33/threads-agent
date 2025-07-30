"""Celery tasks for performance monitoring."""
import logging
from datetime import datetime
from typing import Dict, Any

from celery import shared_task
from sqlalchemy.orm import Session

from services.common.database import get_db_session
from services.performance_monitor.early_kill import (
    EarlyKillMonitor, 
    VariantPerformance
)
from services.performance_monitor.models import VariantMonitoring
from services.threads_adaptor.client import ThreadsClient

logger = logging.getLogger(__name__)


@shared_task(name="performance_monitor.start_monitoring")
def start_monitoring_task(
    variant_id: str,
    persona_id: str,
    post_id: str,
    expected_engagement_rate: float
) -> Dict[str, Any]:
    """Start monitoring a variant for early kill decisions."""
    logger.info(f"Starting monitoring for variant {variant_id}")
    
    with get_db_session() as db:
        # Create monitoring record
        monitoring = VariantMonitoring(
            variant_id=variant_id,
            persona_id=persona_id,
            post_id=post_id,
            expected_engagement_rate=expected_engagement_rate,
            started_at=datetime.utcnow()
        )
        db.add(monitoring)
        db.commit()
        
        # Schedule periodic checks
        check_performance_task.apply_async(
            args=[variant_id],
            countdown=30  # First check after 30 seconds
        )
        
        return {
            "variant_id": variant_id,
            "monitoring_id": monitoring.id,
            "status": "monitoring_started"
        }


@shared_task(name="performance_monitor.check_performance")
def check_performance_task(variant_id: str) -> Dict[str, Any]:
    """Check variant performance and make kill decision."""
    logger.info(f"Checking performance for variant {variant_id}")
    
    with get_db_session() as db:
        # Get monitoring record
        monitoring = db.query(VariantMonitoring).filter_by(
            variant_id=variant_id,
            is_active=True
        ).first()
        
        if not monitoring:
            logger.warning(f"No active monitoring found for variant {variant_id}")
            return {"status": "no_monitoring"}
        
        # Check if timed out
        elapsed_minutes = (datetime.utcnow() - monitoring.started_at).total_seconds() / 60
        if elapsed_minutes >= monitoring.timeout_minutes:
            monitoring.is_active = False
            monitoring.ended_at = datetime.utcnow()
            db.commit()
            logger.info(f"Monitoring timed out for variant {variant_id}")
            return {"status": "timeout"}
        
        # Get current performance from Threads
        try:
            threads_client = ThreadsClient()
            performance = threads_client.get_post_performance(monitoring.post_id)
            
            # Create performance data
            perf_data = VariantPerformance(
                variant_id=variant_id,
                total_views=performance["views"],
                total_interactions=performance["interactions"],
                engagement_rate=performance["engagement_rate"],
                last_updated=datetime.utcnow()
            )
            
            # Evaluate performance
            monitor = EarlyKillMonitor()
            monitor.start_monitoring(
                variant_id=variant_id,
                persona_id=monitoring.persona_id,
                expected_engagement_rate=monitoring.expected_engagement_rate,
                post_timestamp=monitoring.started_at
            )
            
            decision = monitor.evaluate_performance(variant_id, perf_data)
            
            if decision and decision.should_kill:
                # Kill the variant
                logger.info(f"Killing variant {variant_id}: {decision.reason}")
                
                # Update monitoring record
                monitoring.is_active = False
                monitoring.was_killed = True
                monitoring.kill_reason = decision.reason
                monitoring.ended_at = datetime.utcnow()
                monitoring.final_engagement_rate = perf_data.engagement_rate
                monitoring.final_interaction_count = perf_data.total_interactions
                monitoring.final_view_count = perf_data.total_views
                db.commit()
                
                # Trigger cleanup
                cleanup_killed_variant_task.delay(variant_id, monitoring.post_id)
                
                return {
                    "status": "killed",
                    "reason": decision.reason,
                    "final_engagement_rate": perf_data.engagement_rate
                }
            else:
                # Schedule next check
                check_performance_task.apply_async(
                    args=[variant_id],
                    countdown=30  # Check again in 30 seconds
                )
                
                return {
                    "status": "monitoring",
                    "current_engagement_rate": perf_data.engagement_rate,
                    "interactions": perf_data.total_interactions
                }
                
        except Exception as e:
            logger.error(f"Error checking performance for variant {variant_id}: {e}")
            # Schedule retry
            check_performance_task.apply_async(
                args=[variant_id],
                countdown=60  # Retry in 60 seconds
            )
            return {"status": "error", "error": str(e)}


@shared_task(name="performance_monitor.cleanup_killed_variant")
def cleanup_killed_variant_task(variant_id: str, post_id: str) -> Dict[str, Any]:
    """Clean up a killed variant."""
    logger.info(f"Cleaning up killed variant {variant_id}")
    
    try:
        # Remove from variant pool
        # This would integrate with your variant pool management
        
        # Cancel scheduled posts if any
        # This would integrate with your scheduling system
        
        # Delete from Threads (if configured)
        threads_client = ThreadsClient()
        if threads_client.delete_post(post_id):
            logger.info(f"Deleted post {post_id} from Threads")
        
        return {
            "status": "cleaned_up",
            "variant_id": variant_id,
            "post_id": post_id
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up variant {variant_id}: {e}")
        return {"status": "error", "error": str(e)}