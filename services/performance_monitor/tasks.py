"""Celery tasks for performance monitoring."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from contextlib import contextmanager

from celery import Celery, shared_task
from sqlalchemy import and_

from services.performance_monitor.early_kill import EarlyKillMonitor, VariantPerformance
from services.performance_monitor.models import VariantMonitoring
from services.performance_monitor.cache import PerformanceCache

# Create Celery app instance
celery = Celery("performance_monitor")
celery.config_from_object("services.common.celery_config")


# Mock implementation since ThreadsClientSync doesn't exist
class ThreadsClientSync:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def bulk_get_performance(self, post_ids):
        """Mock performance data for testing"""
        import random

        return [
            {
                "views": random.randint(100, 1000),
                "interactions": random.randint(5, 50),
                "engagement_rate": random.uniform(0.01, 0.10),
            }
            for _ in post_ids
        ]


logger = logging.getLogger(__name__)

# Try to import threads_adaptor, fall back to mock if not available
try:
    from services.threads_adaptor.client_sync import ThreadsClientSync
except ImportError:
    logger.warning("threads_adaptor not found, using mock client")
    from services.performance_monitor.client_mock import ThreadsClientSync


@contextmanager
def get_db_session():
    """Get database session for tasks."""
    from services.performance_monitor.main import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@shared_task(name="performance_monitor.start_monitoring")
def start_monitoring_task(
    variant_id: str, persona_id: str, post_id: str, expected_engagement_rate: float
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
            started_at=datetime.utcnow(),
        )
        db.add(monitoring)
        db.commit()

        # Schedule batch check if not already scheduled
        schedule_batch_check()

        return {
            "variant_id": variant_id,
            "monitoring_id": monitoring.id,
            "status": "monitoring_started",
        }


@shared_task(name="performance_monitor.check_performance")
def check_performance_task(variant_id: str) -> Dict[str, Any]:
    """Check variant performance and make kill decision."""
    logger.info(f"Checking performance for variant {variant_id}")

    with get_db_session() as db:
        # Get monitoring record
        monitoring = (
            db.query(VariantMonitoring)
            .filter_by(variant_id=variant_id, is_active=True)
            .first()
        )

        if not monitoring:
            logger.warning(f"No active monitoring found for variant {variant_id}")
            return {"status": "no_monitoring"}

        # Check if timed out
        elapsed_minutes = (
            datetime.utcnow() - monitoring.started_at
        ).total_seconds() / 60
        if elapsed_minutes >= monitoring.timeout_minutes:
            monitoring.is_active = False
            monitoring.ended_at = datetime.utcnow()
            db.commit()
            logger.info(f"Monitoring timed out for variant {variant_id}")
            return {"status": "timeout"}

        # Get current performance from Threads
        try:
            # TODO: Replace with actual Threads API integration
            # For now, use mock data
            import random

            performance = {
                "views": random.randint(100, 1000),
                "interactions": random.randint(5, 50),
                "engagement_rate": random.uniform(0.01, 0.10),
            }

            # Create performance data
            perf_data = VariantPerformance(
                variant_id=variant_id,
                total_views=performance["views"],
                total_interactions=performance["interactions"],
                engagement_rate=performance["engagement_rate"],
                last_updated=datetime.utcnow(),
            )

            # Evaluate performance
            monitor = EarlyKillMonitor()
            monitor.start_monitoring(
                variant_id=variant_id,
                persona_id=monitoring.persona_id,
                expected_engagement_rate=monitoring.expected_engagement_rate,
                post_timestamp=monitoring.started_at,
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
                    "final_engagement_rate": perf_data.engagement_rate,
                }
            else:
                # Schedule next check
                check_performance_task.apply_async(
                    args=[variant_id],
                    countdown=30,  # Check again in 30 seconds
                )

                return {
                    "status": "monitoring",
                    "current_engagement_rate": perf_data.engagement_rate,
                    "interactions": perf_data.total_interactions,
                }

        except Exception as e:
            logger.error(f"Error checking performance for variant {variant_id}: {e}")
            # Schedule retry
            check_performance_task.apply_async(
                args=[variant_id],
                countdown=60,  # Retry in 60 seconds
            )
            return {"status": "error", "error": str(e)}


@shared_task(name="performance_monitor.batch_check_performance")
def batch_check_performance_task() -> Dict[str, Any]:
    """Check all active variants in batches for better performance."""
    logger.info("Starting batch performance check")

    cache = PerformanceCache()
    processed_count = 0
    killed_count = 0

    with get_db_session() as db:
        # Get all active monitoring sessions
        active_sessions = (
            db.query(VariantMonitoring)
            .filter(
                and_(
                    VariantMonitoring.is_active.is_(True),
                    VariantMonitoring.started_at
                    >= datetime.utcnow() - timedelta(minutes=10),
                )
            )
            .all()
        )

        if not active_sessions:
            logger.info("No active monitoring sessions")
            return {"status": "no_active_sessions"}

        # Process in batches
        batch_size = 50
        monitor = EarlyKillMonitor()

        with ThreadsClientSync() as threads_client:
            for i in range(0, len(active_sessions), batch_size):
                batch = active_sessions[i : i + batch_size]
                post_ids = [s.post_id for s in batch]

                # Check cache first
                cached_performances = cache.bulk_get_performance(post_ids)

                # Fetch missing data
                to_fetch = [
                    post_id
                    for post_id, perf in cached_performances.items()
                    if perf is None
                ]

                if to_fetch:
                    fresh_performances = threads_client.bulk_get_performance(to_fetch)

                    # Cache fresh data
                    to_cache = {}
                    for post_id, perf in zip(to_fetch, fresh_performances):
                        if not perf.get("error"):
                            to_cache[post_id] = perf
                            cached_performances[post_id] = perf

                    if to_cache:
                        cache.bulk_set_performance(to_cache)

                # Process each monitoring session
                for session in batch:
                    processed_count += 1

                    # Check timeout first
                    elapsed_minutes = (
                        datetime.utcnow() - session.started_at
                    ).total_seconds() / 60
                    if elapsed_minutes >= session.timeout_minutes:
                        session.is_active = False
                        session.ended_at = datetime.utcnow()
                        logger.info(
                            f"Monitoring timed out for variant {session.variant_id}"
                        )
                        continue

                    # Get performance data
                    perf = cached_performances.get(session.post_id)
                    if not perf or perf.get("error"):
                        logger.warning(
                            f"No performance data for variant {session.variant_id}"
                        )
                        continue

                    # Create performance data object
                    perf_data = VariantPerformance(
                        variant_id=session.variant_id,
                        total_views=perf["views"],
                        total_interactions=perf["interactions"],
                        engagement_rate=perf["engagement_rate"],
                        last_updated=datetime.utcnow(),
                    )

                    # Evaluate performance
                    monitor.start_monitoring(
                        variant_id=session.variant_id,
                        persona_id=session.persona_id,
                        expected_engagement_rate=session.expected_engagement_rate,
                        post_timestamp=session.started_at,
                    )

                    decision = monitor.evaluate_performance(
                        session.variant_id, perf_data
                    )

                    if decision and decision.should_kill:
                        killed_count += 1
                        logger.info(
                            f"Killing variant {session.variant_id}: {decision.reason}"
                        )

                        # Update monitoring record
                        session.is_active = False
                        session.was_killed = True
                        session.kill_reason = decision.reason
                        session.ended_at = datetime.utcnow()
                        session.final_engagement_rate = perf_data.engagement_rate
                        session.final_interaction_count = perf_data.total_interactions
                        session.final_view_count = perf_data.total_views

                        # Trigger cleanup
                        cleanup_killed_variant_task.delay(
                            session.variant_id, session.post_id
                        )

                        # Invalidate cache
                        cache.invalidate(session.post_id)

            # Commit all changes
            db.commit()

    # Schedule next batch check
    schedule_batch_check()

    logger.info(
        f"Batch check complete: {processed_count} processed, {killed_count} killed"
    )

    return {"status": "complete", "processed": processed_count, "killed": killed_count}


def schedule_batch_check():
    """Schedule next batch check if not already scheduled."""
    # Check if task is already scheduled
    from celery import current_app

    inspect = current_app.control.inspect()
    scheduled = inspect.scheduled()

    # Simple check - in production you'd want more sophisticated deduplication
    task_scheduled = False
    if scheduled:
        for worker, tasks in scheduled.items():
            for task in tasks:
                if task["name"] == "performance_monitor.batch_check_performance":
                    task_scheduled = True
                    break

    if not task_scheduled:
        batch_check_performance_task.apply_async(countdown=30)


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
        # TODO: Implement actual Threads deletion
        logger.info(f"Would delete post {post_id} from Threads (not implemented)")

        return {"status": "cleaned_up", "variant_id": variant_id, "post_id": post_id}

    except Exception as e:
        logger.error(f"Error cleaning up variant {variant_id}: {e}")
        return {"status": "error", "error": str(e)}
