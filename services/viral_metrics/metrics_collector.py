"""
Main viral metrics collection engine with real-time calculation capabilities.
Implements MLOps best practices for production-grade metric tracking.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import httpx

from services.common.metrics import PrometheusClient
from services.common.db import get_db_connection
from services.common.cache import get_redis_connection

from .calculators.viral_coefficient_calculator import ViralCoefficientCalculator
from .calculators.scroll_stop_rate_calculator import ScrollStopRateCalculator
from .calculators.share_velocity_calculator import ShareVelocityCalculator
from .calculators.reply_depth_calculator import ReplyDepthCalculator
from .calculators.engagement_trajectory_calculator import EngagementTrajectoryCalculator
from .calculators.pattern_fatigue_calculator import PatternFatigueCalculator

logger = logging.getLogger(__name__)


class ViralMetricsCollector:
    """
    Real-time viral metrics collection system with <60s SLA.

    Collects and calculates advanced viral KPIs beyond traditional engagement metrics:
    - Viral Coefficient: Secondary engagement generation rate
    - Scroll-Stop Rate: Content stopping power
    - Share Velocity: Speed of content spread
    - Reply Depth: Conversation generation capability
    - Engagement Trajectory: Acceleration/deceleration trends
    - Pattern Fatigue: Content freshness score
    """

    def __init__(self):
        """Initialize metrics collector with all dependencies."""
        self.prometheus_client = PrometheusClient()
        self.redis_client = get_redis_connection()
        self.db = get_db_connection()

        # Initialize metric calculators
        self.calculators = {
            "viral_coefficient": ViralCoefficientCalculator(),
            "scroll_stop_rate": ScrollStopRateCalculator(),
            "share_velocity": ShareVelocityCalculator(),
            "reply_depth": ReplyDepthCalculator(),
            "engagement_trajectory": EngagementTrajectoryCalculator(),
            "pattern_fatigue": PatternFatigueCalculator(),
        }

        # Performance tracking
        self.collection_latency_metric = self.prometheus_client.histogram(
            "viral_metrics_collection_latency_seconds",
            "Time taken to collect all viral metrics",
        )

    async def collect_viral_metrics(
        self, post_id: str, timeframe: str = "1h"
    ) -> Dict[str, float]:
        """
        Collect comprehensive viral metrics for a post with <60s SLA.

        Args:
            post_id: Unique identifier for the post
            timeframe: Time window for metrics (e.g., "1h", "3h", "24h")

        Returns:
            Dictionary of calculated viral metrics
        """
        start_time = asyncio.get_event_loop().time()
        metrics = {}

        try:
            # Get base engagement data
            engagement_data = await self.get_engagement_data(post_id, timeframe)

            if not engagement_data:
                logger.warning(f"No engagement data found for post {post_id}")
                return self._get_default_metrics()

            # Calculate each viral metric in parallel for performance
            calculation_tasks = []
            for metric_name, calculator in self.calculators.items():
                task = self._calculate_metric_safe(
                    metric_name, calculator, post_id, engagement_data, timeframe
                )
                calculation_tasks.append(task)

            # Wait for all calculations to complete
            calculated_metrics = await asyncio.gather(*calculation_tasks)

            # Combine results
            for metric_name, value in zip(self.calculators.keys(), calculated_metrics):
                metrics[metric_name] = value

                # Emit to Prometheus with labels
                self.prometheus_client.gauge(f"viral_{metric_name}").set(
                    value,
                    labels={
                        "post_id": post_id,
                        "persona_id": engagement_data.get("persona_id", "unknown"),
                    },
                )

            # Cache metrics for fast retrieval
            await self.cache_metrics(post_id, metrics, ttl=300)  # 5 min cache

            # Store metrics history for MLOps tracking
            await self.store_metrics_history(post_id, metrics)

            # Track collection latency
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.collection_latency_metric.observe(
                elapsed_time, labels={"post_id": post_id}
            )

            logger.info(
                f"Collected viral metrics for post {post_id} in {elapsed_time:.2f}s"
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect viral metrics for post {post_id}: {e}")
            return self._get_default_metrics()

    async def _calculate_metric_safe(
        self,
        metric_name: str,
        calculator: Any,
        post_id: str,
        engagement_data: Dict,
        timeframe: str,
    ) -> float:
        """
        Safely calculate a single metric with error handling.

        Returns 0.0 if calculation fails to ensure system stability.
        """
        try:
            value = await calculator.calculate(post_id, engagement_data, timeframe)
            return value
        except Exception as e:
            logger.warning(f"Failed to calculate {metric_name} for post {post_id}: {e}")
            return 0.0

    async def get_engagement_data(self, post_id: str, timeframe: str) -> Dict[str, Any]:
        """
        Fetch comprehensive engagement data from fake-threads API.

        Returns:
            Dictionary containing all engagement metrics needed for calculations
        """
        try:
            # In production, this would call the actual fake-threads API
            # For now, we'll simulate the call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"http://fake-threads:9009/analytics/{post_id}",
                    params={"timeframe": timeframe},
                )

                if response.status_code != 200:
                    logger.warning(
                        f"Failed to get engagement data for post {post_id}: {response.status_code}"
                    )
                    return {}

                raw_data = response.json()

                # Ensure all required fields are present
                return {
                    "post_id": post_id,
                    "persona_id": raw_data.get("persona_id", "unknown"),
                    "views": raw_data.get("views", 0),
                    "impressions": raw_data.get("impressions", 0),
                    "engaged_views": raw_data.get("engaged_views", 0),
                    "likes": raw_data.get("likes", 0),
                    "comments": raw_data.get("comments", 0),
                    "shares": raw_data.get("shares", 0),
                    "saves": raw_data.get("saves", 0),
                    "click_throughs": raw_data.get("click_throughs", 0),
                    "view_duration_avg": raw_data.get("view_duration_avg", 0),
                    "hourly_breakdown": raw_data.get("hourly_breakdown", []),
                    "demographic_data": raw_data.get("demographic_data", {}),
                }

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching engagement data for post {post_id}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching engagement data for post {post_id}: {e}")
            return {}

    async def cache_metrics(
        self, post_id: str, metrics: Dict[str, float], ttl: int = 300
    ) -> None:
        """
        Cache metrics in Redis for fast retrieval.

        Args:
            post_id: Post identifier
            metrics: Calculated metrics to cache
            ttl: Time to live in seconds (default: 5 minutes)
        """
        try:
            cache_key = f"viral_metrics:{post_id}"
            cache_value = json.dumps(metrics)
            await self.redis_client.setex(cache_key, ttl, cache_value)
        except Exception as e:
            logger.warning(f"Failed to cache metrics for post {post_id}: {e}")

    async def get_cached_metrics(self, post_id: str) -> Optional[Dict[str, float]]:
        """
        Retrieve cached metrics if available.

        Returns:
            Cached metrics or None if not found/expired
        """
        try:
            cache_key = f"viral_metrics:{post_id}"
            cached_value = await self.redis_client.get(cache_key)

            if cached_value:
                return json.loads(cached_value)
            return None

        except Exception as e:
            logger.warning(f"Failed to retrieve cached metrics for post {post_id}: {e}")
            return None

    async def store_metrics_history(
        self, post_id: str, metrics: Dict[str, float]
    ) -> None:
        """
        Store metrics in database for historical tracking and MLOps analysis.

        This data is used for:
        - Pattern analysis and optimization
        - Model training for engagement prediction
        - Performance monitoring and alerting
        """
        try:
            # Extract persona_id from the post (would come from engagement data in production)
            persona_id = "unknown"  # This would be fetched from post metadata

            # Store comprehensive metrics record
            await self.db.execute(
                """
                INSERT INTO viral_metrics (
                    post_id, persona_id, viral_coefficient, scroll_stop_rate,
                    share_velocity, reply_depth, engagement_trajectory,
                    pattern_fatigue_score, collected_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                post_id,
                persona_id,
                metrics.get("viral_coefficient", 0.0),
                metrics.get("scroll_stop_rate", 0.0),
                metrics.get("share_velocity", 0.0),
                metrics.get("reply_depth", 0.0),
                metrics.get("engagement_trajectory", 0.0),
                metrics.get("pattern_fatigue", 0.0),
                datetime.now(),
            )

            # Also store individual metric history for time series analysis
            for metric_name, metric_value in metrics.items():
                await self.db.execute(
                    """
                    INSERT INTO viral_metrics_history (
                        post_id, metric_name, metric_value, recorded_at
                    ) VALUES ($1, $2, $3, $4)
                """,
                    post_id,
                    metric_name,
                    metric_value,
                    datetime.now(),
                )

        except Exception as e:
            logger.error(f"Failed to store metrics history for post {post_id}: {e}")

    def _get_default_metrics(self) -> Dict[str, float]:
        """Return default metrics when calculation fails."""
        return {
            "viral_coefficient": 0.0,
            "scroll_stop_rate": 0.0,
            "share_velocity": 0.0,
            "reply_depth": 0.0,
            "engagement_trajectory": 0.0,
            "pattern_fatigue": 0.0,
        }

    async def get_baseline_metrics(self, post_id: str) -> Dict[str, float]:
        """
        Get historical baseline metrics for anomaly detection.

        Used to detect significant drops in viral performance.
        """
        try:
            # Get average metrics from similar posts in the last 7 days
            result = await self.db.fetch_one(
                """
                SELECT 
                    AVG(viral_coefficient) as avg_viral_coefficient,
                    AVG(scroll_stop_rate) as avg_scroll_stop_rate,
                    AVG(share_velocity) as avg_share_velocity
                FROM viral_metrics
                WHERE persona_id = (
                    SELECT persona_id FROM viral_metrics WHERE post_id = $1 LIMIT 1
                )
                AND collected_at >= NOW() - INTERVAL '7 days'
                AND post_id != $1
            """,
                post_id,
            )

            if result:
                return {
                    "viral_coefficient": result["avg_viral_coefficient"] or 0.0,
                    "scroll_stop_rate": result["avg_scroll_stop_rate"] or 0.0,
                    "share_velocity": result["avg_share_velocity"] or 0.0,
                }

            return self._get_default_metrics()

        except Exception as e:
            logger.error(f"Failed to get baseline metrics for post {post_id}: {e}")
            return self._get_default_metrics()
