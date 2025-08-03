"""
Optimized ViralFinOpsEngine - Memory-efficient with connection pooling and caching.

PERFORMANCE OPTIMIZATIONS:
1. Redis caching for frequently accessed data
2. Connection pooling with circuit breakers
3. Asynchronous batching for high throughput
4. Memory-efficient data structures
5. Prometheus metrics optimization
6. Cost aggregation with sliding windows

Performance Targets:
- Cost tracking latency: <100ms
- Throughput: 200+ posts/minute
- Memory usage: <500MB under load
- Cache hit ratio: >85%
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import deque, defaultdict
import logging

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .optimized_cost_event_storage import OptimizedCostEventStorage, DatabaseConfig
from .prometheus_metrics_emitter import PrometheusMetricsEmitter

logger = logging.getLogger(__name__)


@dataclass
class FinOpsConfig:
    """Optimized configuration for FinOps engine."""

    # Cost thresholds
    cost_threshold_per_post: float = 0.02
    alert_threshold_multiplier: float = 2.0

    # Performance settings
    storage_latency_target_ms: float = 100.0
    batch_size: int = 100
    max_memory_mb: int = 500

    # Caching configuration
    enable_redis_cache: bool = True
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    # Anomaly detection
    anomaly_detection_enabled: bool = True
    anomaly_check_interval_seconds: int = 30
    anomaly_history_window_hours: int = 24

    # Connection pooling
    database_config: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Memory management
    max_post_costs_in_memory: int = 1000
    cost_history_cleanup_interval: int = 3600  # 1 hour


class MemoryEfficientCostTracker:
    """Memory-efficient cost tracking with sliding windows."""

    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self._post_costs: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=50)
        )  # Max 50 events per post
        self._cost_totals: Dict[str, float] = {}
        self._last_cleanup = time.time()
        self._access_times: Dict[str, float] = {}

    def add_cost_event(self, post_id: str, cost_event: Dict[str, Any]) -> None:
        """Add cost event with memory bounds."""
        self._post_costs[post_id].append(cost_event)
        self._cost_totals[post_id] = sum(
            e["cost_amount"] for e in self._post_costs[post_id]
        )
        self._access_times[post_id] = time.time()

        # Periodic cleanup to prevent memory growth
        if len(self._post_costs) > self.max_entries:
            self._cleanup_old_entries()

    def get_post_costs(self, post_id: str) -> List[Dict[str, Any]]:
        """Get costs for a post."""
        self._access_times[post_id] = time.time()
        return list(self._post_costs.get(post_id, []))

    def get_total_cost(self, post_id: str) -> float:
        """Get total cost for a post."""
        self._access_times[post_id] = time.time()
        return self._cost_totals.get(post_id, 0.0)

    def _cleanup_old_entries(self) -> None:
        """Remove least recently used entries."""
        if len(self._post_costs) <= self.max_entries * 0.8:
            return

        # Sort by access time and remove oldest 20%
        sorted_posts = sorted(self._access_times.items(), key=lambda x: x[1])
        posts_to_remove = sorted_posts[: len(sorted_posts) // 5]

        for post_id, _ in posts_to_remove:
            self._post_costs.pop(post_id, None)
            self._cost_totals.pop(post_id, None)
            self._access_times.pop(post_id, None)

        logger.info(f"Cleaned up {len(posts_to_remove)} old cost entries")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        total_events = sum(len(costs) for costs in self._post_costs.values())
        return {
            "tracked_posts": len(self._post_costs),
            "total_events": total_events,
            "memory_usage_estimate_mb": (total_events * 0.001),  # Rough estimate
            "max_entries": self.max_entries,
        }


class OptimizedViralFinOpsEngine:
    """
    Optimized ViralFinOpsEngine with advanced performance features.

    PERFORMANCE FEATURES:
    - AsyncPG connection pooling
    - Redis caching for hot data
    - Memory-efficient cost tracking
    - Batch processing for high throughput
    - Circuit breakers for resilience
    - Prometheus metrics optimization
    """

    def __init__(self, config: Optional[FinOpsConfig] = None):
        """Initialize optimized FinOps engine."""
        self.config = config or FinOpsConfig()

        # Initialize optimized storage
        self.cost_storage = OptimizedCostEventStorage(self.config.database_config)

        # Memory-efficient cost tracking
        self.memory_tracker = MemoryEfficientCostTracker(
            max_entries=self.config.max_post_costs_in_memory
        )

        # Prometheus metrics
        self.prometheus_client = PrometheusMetricsEmitter()

        # Redis cache (if available)
        self.redis_client: Optional[redis.Redis] = None
        self.cache_enabled = False

        # Batch processing
        self.pending_events: List[Dict[str, Any]] = []
        self.batch_lock = asyncio.Lock()
        self.last_batch_process = time.time()

        # Performance monitoring
        self.performance_stats = {
            "operations_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_latency_ms": 0.0,
            "batch_operations": 0,
            "memory_usage_mb": 0.0,
        }

        # Anomaly detection (lightweight)
        if self.config.anomaly_detection_enabled:
            self._anomaly_baselines: Dict[str, List[float]] = defaultdict(list)
            self._last_anomaly_check = {}

    async def initialize(self) -> None:
        """Initialize all components."""
        # Initialize database storage
        await self.cost_storage.initialize()

        # Initialize Redis cache if available
        if REDIS_AVAILABLE and self.config.enable_redis_cache:
            try:
                self.redis_client = redis.from_url(
                    self.config.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                await self.redis_client.ping()
                self.cache_enabled = True
                logger.info("Redis cache enabled")
            except Exception as e:
                logger.warning(f"Redis cache unavailable: {e}")
                self.cache_enabled = False

        # Start background tasks
        asyncio.create_task(self._batch_processor())
        asyncio.create_task(self._performance_monitor())

        logger.info("Optimized FinOps engine initialized")

    async def track_openai_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str,
        persona_id: str,
        post_id: str,
    ) -> Dict[str, Any]:
        """Track OpenAI cost with optimizations."""
        start_time = time.time()

        # Calculate cost (simplified pricing)
        cost_per_1k_input = 0.01 if "gpt-4" in model else 0.0015
        cost_per_1k_output = 0.03 if "gpt-4" in model else 0.002

        total_cost = (input_tokens / 1000) * cost_per_1k_input + (
            output_tokens / 1000
        ) * cost_per_1k_output

        # Create cost event
        cost_event = {
            "cost_amount": total_cost,
            "cost_type": "openai_api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "persona_id": persona_id,
            "post_id": post_id,
            "operation": operation,
            "metadata": {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_per_1k_input": cost_per_1k_input,
                "cost_per_1k_output": cost_per_1k_output,
            },
        }

        # Process with optimizations
        await self._process_cost_event_optimized(cost_event)

        # Update performance stats
        latency_ms = (time.time() - start_time) * 1000
        self._update_performance_stats(latency_ms)

        return cost_event

    async def track_infrastructure_cost(
        self,
        resource_type: str,
        service: str,
        cpu_cores: float,
        memory_gb: float,
        duration_minutes: int,
        operation: str,
        persona_id: str,
        post_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Track infrastructure cost with optimizations."""
        start_time = time.time()

        # Calculate infrastructure cost (simplified)
        cpu_cost_per_hour = 0.048  # $0.048 per vCPU hour
        memory_cost_per_hour = 0.0067  # $0.0067 per GB hour

        duration_hours = duration_minutes / 60.0
        total_cost = (
            cpu_cores * cpu_cost_per_hour * duration_hours
            + memory_gb * memory_cost_per_hour * duration_hours
        )

        # Create cost event
        cost_event = {
            "cost_amount": total_cost,
            "cost_type": "kubernetes",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "persona_id": persona_id,
            "post_id": post_id,
            "operation": operation,
            "metadata": {
                "service": service,
                "resource_type": resource_type,
                "cpu_cores": cpu_cores,
                "memory_gb": memory_gb,
                "duration_minutes": duration_minutes,
                "cpu_cost_per_hour": cpu_cost_per_hour,
                "memory_cost_per_hour": memory_cost_per_hour,
                **kwargs,
            },
        }

        # Process with optimizations
        await self._process_cost_event_optimized(cost_event)

        # Update performance stats
        latency_ms = (time.time() - start_time) * 1000
        self._update_performance_stats(latency_ms)

        return cost_event

    async def track_vector_db_cost(
        self,
        operation: str,
        query_count: int,
        collection: str,
        persona_id: str,
        post_id: str,
    ) -> Dict[str, Any]:
        """Track vector database cost with optimizations."""
        start_time = time.time()

        # Calculate vector DB cost (simplified)
        cost_per_1k_queries = 0.0002
        total_cost = (query_count / 1000) * cost_per_1k_queries

        # Create cost event
        cost_event = {
            "cost_amount": total_cost,
            "cost_type": "vector_db",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "persona_id": persona_id,
            "post_id": post_id,
            "operation": operation,
            "metadata": {
                "query_count": query_count,
                "collection": collection,
                "cost_per_1k_queries": cost_per_1k_queries,
            },
        }

        # Process with optimizations
        await self._process_cost_event_optimized(cost_event)

        # Update performance stats
        latency_ms = (time.time() - start_time) * 1000
        self._update_performance_stats(latency_ms)

        return cost_event

    async def _process_cost_event_optimized(self, cost_event: Dict[str, Any]) -> None:
        """Process cost event with all optimizations."""
        # 1. Add to memory tracker for fast access
        self.memory_tracker.add_cost_event(cost_event["post_id"], cost_event)

        # 2. Add to batch for efficient database storage
        async with self.batch_lock:
            self.pending_events.append(cost_event)

            # Trigger immediate batch if threshold reached
            if len(self.pending_events) >= self.config.batch_size:
                await self._process_batch()

        # 3. Update cache if enabled
        if self.cache_enabled:
            await self._update_cache(cost_event)

        # 4. Emit metrics
        self.prometheus_client.emit_cost_metric(cost_event)

    async def _process_batch(self) -> None:
        """Process pending events in batch."""
        if not self.pending_events:
            return

        batch_start = time.time()
        batch_events = self.pending_events.copy()
        self.pending_events.clear()

        try:
            # Store batch in database
            await self.cost_storage.store_cost_events_batch(batch_events)

            batch_duration = (time.time() - batch_start) * 1000
            self.performance_stats["batch_operations"] += 1

            logger.info(
                f"Processed batch: {len(batch_events)} events in {batch_duration:.2f}ms"
            )

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Re-add events to pending for retry
            self.pending_events.extend(batch_events)

    async def _update_cache(self, cost_event: Dict[str, Any]) -> None:
        """Update Redis cache with cost event."""
        if not self.redis_client:
            return

        try:
            post_id = cost_event["post_id"]
            cache_key = f"post_costs:{post_id}"

            # Get current cached costs
            cached_costs = await self.redis_client.get(cache_key)
            if cached_costs:
                costs = json.loads(cached_costs)
            else:
                costs = []

            # Add new event and keep last 50 events
            costs.append(cost_event)
            costs = costs[-50:]  # Keep only recent events

            # Update cache
            await self.redis_client.setex(
                cache_key, self.config.cache_ttl_seconds, json.dumps(costs)
            )

        except Exception as e:
            logger.warning(f"Cache update failed: {e}")

    async def calculate_total_post_cost(self, post_id: str) -> float:
        """Calculate total cost with caching optimizations."""
        # Check memory tracker first (fastest)
        memory_cost = self.memory_tracker.get_total_cost(post_id)
        if memory_cost > 0:
            self.performance_stats["cache_hits"] += 1
            return memory_cost

        # Check Redis cache
        if self.cache_enabled:
            try:
                cache_key = f"post_costs:{post_id}"
                cached_costs = await self.redis_client.get(cache_key)
                if cached_costs:
                    costs = json.loads(cached_costs)
                    total = sum(event["cost_amount"] for event in costs)
                    self.performance_stats["cache_hits"] += 1
                    return total
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")

        # Fallback to database
        self.performance_stats["cache_misses"] += 1
        events = await self.cost_storage.get_cost_events(post_id=post_id)
        total_cost = sum(event["cost_amount"] for event in events)

        # Update memory tracker
        for event in events:
            self.memory_tracker.add_cost_event(post_id, event)

        return total_cost

    async def get_post_cost_breakdown(self, post_id: str) -> Dict[str, Any]:
        """Get detailed cost breakdown with optimizations."""
        # Try memory tracker first
        memory_costs = self.memory_tracker.get_post_costs(post_id)
        if memory_costs:
            events = memory_costs
            self.performance_stats["cache_hits"] += 1
        else:
            # Check cache or database
            if self.cache_enabled:
                try:
                    cache_key = f"post_costs:{post_id}"
                    cached_costs = await self.redis_client.get(cache_key)
                    if cached_costs:
                        events = json.loads(cached_costs)
                        self.performance_stats["cache_hits"] += 1
                    else:
                        events = await self.cost_storage.get_cost_events(
                            post_id=post_id
                        )
                        self.performance_stats["cache_misses"] += 1
                except Exception as e:
                    logger.warning(f"Cache read failed: {e}")
                    events = await self.cost_storage.get_cost_events(post_id=post_id)
                    self.performance_stats["cache_misses"] += 1
            else:
                events = await self.cost_storage.get_cost_events(post_id=post_id)
                self.performance_stats["cache_misses"] += 1

        # Calculate breakdown
        total_cost = sum(event["cost_amount"] for event in events)
        cost_breakdown = defaultdict(float)

        for event in events:
            cost_breakdown[event["cost_type"]] += event["cost_amount"]

        return {
            "post_id": post_id,
            "total_cost": total_cost,
            "cost_breakdown": dict(cost_breakdown),
            "event_count": len(events),
            "audit_trail": events[-10:],  # Last 10 events for audit
        }

    async def check_for_anomalies(self, persona_id: str) -> Dict[str, Any]:
        """Lightweight anomaly detection with caching."""
        if not self.config.anomaly_detection_enabled:
            return {"anomalies_detected": [], "alerts_sent": [], "actions_taken": []}

        current_time = time.time()
        last_check = self._last_anomaly_check.get(persona_id, 0)

        # Rate limiting: check every 30 seconds per persona
        if current_time - last_check < self.config.anomaly_check_interval_seconds:
            return {"anomalies_detected": [], "alerts_sent": [], "actions_taken": []}

        self._last_anomaly_check[persona_id] = current_time

        # Get recent costs from memory tracker
        recent_costs = []
        for post_id, costs in self.memory_tracker._post_costs.items():
            for cost_event in costs:
                if cost_event.get("persona_id") == persona_id:
                    recent_costs.append(cost_event["cost_amount"])

        if not recent_costs:
            return {"anomalies_detected": [], "alerts_sent": [], "actions_taken": []}

        # Simple statistical anomaly detection
        current_avg = sum(recent_costs[-10:]) / min(
            10, len(recent_costs)
        )  # Last 10 costs
        baseline = self._anomaly_baselines[persona_id]

        if not baseline:
            # Initialize baseline
            self._anomaly_baselines[persona_id] = recent_costs[
                -5:
            ]  # Last 5 as baseline
            return {"anomalies_detected": [], "alerts_sent": [], "actions_taken": []}

        baseline_avg = sum(baseline) / len(baseline)

        # Detect anomaly (3x threshold)
        is_anomaly = current_avg > baseline_avg * 3.0

        if is_anomaly:
            anomaly = {
                "persona_id": persona_id,
                "current_cost": current_avg,
                "baseline_cost": baseline_avg,
                "multiplier": current_avg / baseline_avg if baseline_avg > 0 else 0,
                "severity": "high" if current_avg > baseline_avg * 5.0 else "medium",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Update baseline with recent data (sliding window)
            self._anomaly_baselines[persona_id] = recent_costs[-20:]  # Keep last 20

            return {
                "anomalies_detected": [anomaly],
                "alerts_sent": [],  # Simplified for performance
                "actions_taken": [],
            }

        # Update baseline
        self._anomaly_baselines[persona_id] = recent_costs[-20:]  # Keep last 20

        return {"anomalies_detected": [], "alerts_sent": [], "actions_taken": []}

    async def _batch_processor(self) -> None:
        """Background batch processor."""
        while True:
            try:
                await asyncio.sleep(5)  # Process every 5 seconds

                async with self.batch_lock:
                    if self.pending_events:
                        await self._process_batch()

            except Exception as e:
                logger.error(f"Batch processor error: {e}")

    async def _performance_monitor(self) -> None:
        """Background performance monitoring."""
        while True:
            try:
                await asyncio.sleep(60)  # Monitor every minute

                # Update memory stats
                memory_stats = self.memory_tracker.get_memory_stats()
                self.performance_stats["memory_usage_mb"] = memory_stats[
                    "memory_usage_estimate_mb"
                ]

                # Log performance metrics
                stats = self.get_performance_stats()
                logger.info(f"Performance stats: {stats}")

                # Cleanup if needed
                if (
                    self.performance_stats["memory_usage_mb"]
                    > self.config.max_memory_mb * 0.8
                ):
                    self.memory_tracker._cleanup_old_entries()

                # Clean database cache
                await self.cost_storage.cleanup_cache()

            except Exception as e:
                logger.error(f"Performance monitor error: {e}")

    def _update_performance_stats(self, latency_ms: float) -> None:
        """Update performance statistics."""
        self.performance_stats["operations_processed"] += 1

        # Update rolling average latency
        current_avg = self.performance_stats["avg_latency_ms"]
        op_count = self.performance_stats["operations_processed"]
        self.performance_stats["avg_latency_ms"] = (
            current_avg * (op_count - 1) + latency_ms
        ) / op_count

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        storage_stats = self.cost_storage.get_performance_stats()
        memory_stats = self.memory_tracker.get_memory_stats()

        cache_hit_rate = 0.0
        if (
            self.performance_stats["cache_hits"]
            + self.performance_stats["cache_misses"]
            > 0
        ):
            cache_hit_rate = self.performance_stats["cache_hits"] / (
                self.performance_stats["cache_hits"]
                + self.performance_stats["cache_misses"]
            )

        return {
            **self.performance_stats,
            "cache_hit_rate": cache_hit_rate,
            "storage_stats": storage_stats,
            "memory_stats": memory_stats,
            "cache_enabled": self.cache_enabled,
            "pending_batch_events": len(self.pending_events),
        }

    async def close(self) -> None:
        """Cleanup resources."""
        # Process remaining batch
        if self.pending_events:
            await self._process_batch()

        # Close storage
        await self.cost_storage.close()

        # Close Redis
        if self.redis_client:
            await self.redis_client.close()

        logger.info("Optimized FinOps engine closed")
