"""
Background processor for continuous viral metrics collection.
Implements efficient batch processing with <60s SLA.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from services.common.celery_app import get_celery_app
from services.common.db import get_db_connection
from .metrics_collector import ViralMetricsCollector

logger = logging.getLogger(__name__)


class ViralMetricsProcessor:
    """
    Background processor for continuous metrics collection.

    Features:
    - Batch processing for efficiency
    - Parallel metric collection
    - Anomaly detection and alerting
    - Performance monitoring
    """

    def __init__(self):
        """Initialize processor with dependencies."""
        self.metrics_collector = ViralMetricsCollector()
        self.celery_app = get_celery_app()
        self._db = None

        # Performance configuration
        self.batch_size = 50
        self.max_parallel_tasks = 10
        self.metrics_ttl_hours = 24  # Process posts from last 24 hours
    
    @property
    def db(self):
        """Lazy-load database connection."""
        if self._db is None:
            self._db = get_db_connection()
        return self._db

    async def process_active_posts(self, batch_size: int = None) -> Dict[str, Any]:
        """
        Process metrics for all active posts in batches.

        Args:
            batch_size: Override default batch size

        Returns:
            Processing summary with success/failure counts
        """
        batch_size = batch_size or self.batch_size
        start_time = asyncio.get_event_loop().time()

        try:
            # Get posts that need metrics updates
            active_posts = await self._get_active_posts(batch_size)

            if not active_posts:
                logger.info("No active posts to process")
                return {"processed": 0, "success": 0, "failed": 0}

            logger.info(f"Processing metrics for {len(active_posts)} active posts")

            # Process posts in parallel batches
            results = await self._process_posts_batch(active_posts)

            # Calculate summary
            success_count = sum(1 for r in results if r.get("status") == "success")
            failed_count = len(results) - success_count

            elapsed_time = asyncio.get_event_loop().time() - start_time

            summary = {
                "processed": len(active_posts),
                "success": success_count,
                "failed": failed_count,
                "elapsed_time_seconds": elapsed_time,
                "posts_per_second": len(active_posts) / elapsed_time
                if elapsed_time > 0
                else 0,
            }

            logger.info(f"Metrics processing complete: {summary}")

            return summary

        except Exception as e:
            logger.error(f"Error in batch metrics processing: {e}")
            return {"error": str(e), "processed": 0}

    async def _get_active_posts(self, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch posts that need metrics collection.

        Active posts are those created in the last 24 hours.
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.metrics_ttl_hours)

            posts = await self.db.fetch_all(
                """
                SELECT id, persona_id, created_at 
                FROM posts 
                WHERE created_at >= $1
                ORDER BY created_at DESC
                LIMIT $2
            """,
                cutoff_time,
                limit,
            )

            return [dict(post) for post in posts]

        except Exception as e:
            logger.error(f"Error fetching active posts: {e}")
            return []

    async def _process_posts_batch(
        self, posts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of posts in parallel with rate limiting.

        Returns:
            List of results for each post
        """
        results = []

        # Process in chunks to avoid overwhelming the system
        for i in range(0, len(posts), self.max_parallel_tasks):
            chunk = posts[i : i + self.max_parallel_tasks]

            # Create tasks for parallel processing
            tasks = []
            for post in chunk:
                task = self.collect_post_metrics_async(post["id"])
                tasks.append(task)

            # Wait for chunk to complete
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for post, result in zip(chunk, chunk_results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Failed to collect metrics for post {post['id']}: {result}"
                    )
                    results.append(
                        {"post_id": post["id"], "status": "error", "error": str(result)}
                    )
                else:
                    results.append(result)

        return results

    async def collect_post_metrics_async(self, post_id: str) -> Dict[str, Any]:
        """
        Collect metrics for a single post asynchronously.

        This method can be called directly or via Celery task.
        """
        try:
            # Collect metrics
            metrics = await self.metrics_collector.collect_viral_metrics(post_id)

            # Check for anomalies
            anomalies = await self.check_metrics_anomalies(post_id, metrics)

            return {
                "status": "success",
                "post_id": post_id,
                "metrics": metrics,
                "anomalies": anomalies,
            }

        except Exception as e:
            logger.error(f"Failed to collect metrics for post {post_id}: {e}")
            return {"status": "error", "post_id": post_id, "error": str(e)}

    async def check_metrics_anomalies(
        self, post_id: str, current_metrics: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Check for performance anomalies and trigger alerts if needed.

        Detects:
        - 30%+ drop in viral coefficient
        - Significant trajectory changes
        - Pattern fatigue warnings
        """
        anomalies = []

        try:
            # Get historical baseline
            baseline_metrics = await self.metrics_collector.get_baseline_metrics(
                post_id
            )

            # Check viral coefficient drop
            if baseline_metrics.get("viral_coefficient", 0) > 0:
                current_vc = current_metrics.get("viral_coefficient", 0)
                baseline_vc = baseline_metrics["viral_coefficient"]

                vc_drop = self.calculate_percentage_drop(baseline_vc, current_vc)

                if vc_drop > 0.3:  # 30% drop
                    anomalies.append(
                        {
                            "type": "viral_coefficient_drop",
                            "severity": "high" if vc_drop > 0.5 else "medium",
                            "drop_percentage": vc_drop,
                            "current_value": current_vc,
                            "baseline_value": baseline_vc,
                            "message": f"Viral coefficient dropped {vc_drop:.1%} from baseline",
                        }
                    )

            # Check for negative trajectory
            trajectory = current_metrics.get("engagement_trajectory", 0)
            if trajectory < -50:  # Significant deceleration
                anomalies.append(
                    {
                        "type": "negative_trajectory",
                        "severity": "medium",
                        "trajectory_value": trajectory,
                        "message": f"Engagement is rapidly decelerating (trajectory: {trajectory})",
                    }
                )

            # Check pattern fatigue
            fatigue_score = current_metrics.get("pattern_fatigue", 0)
            if fatigue_score > 0.8:  # High fatigue
                anomalies.append(
                    {
                        "type": "pattern_fatigue",
                        "severity": "low",
                        "fatigue_score": fatigue_score,
                        "message": f"Content pattern showing high fatigue (score: {fatigue_score:.2f})",
                    }
                )

            # Send alerts if high-severity anomalies found
            high_severity_anomalies = [a for a in anomalies if a["severity"] == "high"]
            if high_severity_anomalies:
                await self.send_metrics_alerts(post_id, high_severity_anomalies)

        except Exception as e:
            logger.error(f"Error checking anomalies for post {post_id}: {e}")

        return anomalies

    def calculate_percentage_drop(self, baseline: float, current: float) -> float:
        """Calculate percentage drop from baseline."""
        if baseline == 0:
            return 0.0
        return max(0, (baseline - current) / baseline)

    async def send_metrics_alerts(
        self, post_id: str, anomalies: List[Dict[str, Any]]
    ) -> None:
        """
        Send alerts for detected anomalies.

        In production, this would integrate with alerting systems like
        Slack, Discord, or PagerDuty.
        """
        for anomaly in anomalies:
            logger.warning(
                f"Metrics anomaly detected for post {post_id}: "
                f"{anomaly['type']} - {anomaly['message']}"
            )

            # TODO: Integrate with actual alerting system
            # await alert_manager.send_alert({
            #     "post_id": post_id,
            #     "anomaly": anomaly,
            #     "timestamp": datetime.now()
            # })


# Celery task wrapper
celery_app = get_celery_app()


@celery_app.task(name="viral_metrics.collect_post_metrics")
def collect_post_metrics(post_id: str) -> Dict[str, Any]:
    """
    Celery task to collect metrics for a single post.

    This allows distributed processing across multiple workers.
    """
    processor = ViralMetricsProcessor()

    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(processor.collect_post_metrics_async(post_id))
        return result
    finally:
        loop.close()


@celery_app.task(name="viral_metrics.process_active_posts_batch")
def process_active_posts_batch(batch_size: int = 50) -> Dict[str, Any]:
    """
    Celery task to process a batch of active posts.

    Scheduled to run periodically (e.g., every 5 minutes).
    """
    processor = ViralMetricsProcessor()

    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(processor.process_active_posts(batch_size))
        return result
    finally:
        loop.close()
