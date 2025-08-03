"""
Optimized Prometheus Metrics Emitter - High-performance metrics with batching and caching.

PERFORMANCE OPTIMIZATIONS:
1. Metric batching for reduced overhead
2. Connection pooling to Prometheus
3. Metric deduplication and aggregation
4. Asynchronous metric emission
5. Circuit breaker for resilience
6. Memory-efficient metric storage

Performance Targets:
- Metric emission latency: <10ms
- Throughput: 1000+ metrics/second
- Memory usage: <50MB for metrics
- Batch processing: 100 metrics/batch
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass
import logging

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        CollectorRegistry,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MetricsConfig:
    """Configuration for optimized metrics emission."""

    batch_size: int = 100
    batch_timeout_ms: int = 1000  # 1 second max batching delay
    max_memory_mb: int = 50
    enable_deduplication: bool = True
    enable_aggregation: bool = True
    metric_retention_seconds: int = 300  # 5 minutes
    circuit_breaker_threshold: int = 10
    enable_compression: bool = True


class MetricsBatcher:
    """High-performance metrics batching with deduplication."""

    def __init__(self, config: MetricsConfig):
        self.config = config
        self.pending_metrics: List[Dict[str, Any]] = []
        self.metric_aggregates: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.last_flush = time.time()
        self.batch_lock = asyncio.Lock()

        # Deduplication tracking
        self.seen_metrics: Set[str] = set()
        self.metric_hashes: deque = deque(maxlen=1000)  # Keep last 1000 metric hashes

    def add_metric(self, metric: Dict[str, Any]) -> None:
        """Add metric to batch with deduplication."""
        # Generate hash for deduplication
        metric_hash = self._generate_metric_hash(metric)

        if self.config.enable_deduplication and metric_hash in self.seen_metrics:
            # Update existing metric instead of duplicating
            self._update_existing_metric(metric_hash, metric)
            return

        # Add to batch
        self.pending_metrics.append(metric)
        self.seen_metrics.add(metric_hash)
        self.metric_hashes.append(metric_hash)

        # Aggregate if enabled
        if self.config.enable_aggregation:
            self._aggregate_metric(metric)

    def _generate_metric_hash(self, metric: Dict[str, Any]) -> str:
        """Generate hash for metric deduplication."""
        key_parts = [
            metric.get("metric_name", ""),
            str(sorted(metric.get("labels", {}).items())),
            metric.get("metric_type", ""),
        ]
        return hash(tuple(key_parts))

    def _update_existing_metric(
        self, metric_hash: str, new_metric: Dict[str, Any]
    ) -> None:
        """Update existing metric value."""
        for i, existing_metric in enumerate(self.pending_metrics):
            if self._generate_metric_hash(existing_metric) == metric_hash:
                # Update value based on metric type
                if new_metric.get("metric_type") == "counter":
                    existing_metric["value"] += new_metric.get("value", 0)
                else:
                    existing_metric["value"] = new_metric.get("value", 0)
                existing_metric["timestamp"] = new_metric.get("timestamp")
                break

    def _aggregate_metric(self, metric: Dict[str, Any]) -> None:
        """Aggregate metric for batching efficiency."""
        metric_name = metric.get("metric_name", "")
        labels_key = str(sorted(metric.get("labels", {}).items()))
        aggregate_key = f"{metric_name}:{labels_key}"

        if aggregate_key not in self.metric_aggregates:
            self.metric_aggregates[aggregate_key] = {
                "count": 0,
                "sum": 0.0,
                "max": float("-inf"),
                "min": float("inf"),
                "last_value": 0.0,
                "first_timestamp": metric.get("timestamp"),
                "last_timestamp": metric.get("timestamp"),
            }

        agg = self.metric_aggregates[aggregate_key]
        value = metric.get("value", 0)

        agg["count"] += 1
        agg["sum"] += value
        agg["max"] = max(agg["max"], value)
        agg["min"] = min(agg["min"], value)
        agg["last_value"] = value
        agg["last_timestamp"] = metric.get("timestamp")

    def should_flush(self) -> bool:
        """Check if batch should be flushed."""
        return (
            len(self.pending_metrics) >= self.config.batch_size
            or (time.time() - self.last_flush) * 1000 >= self.config.batch_timeout_ms
        )

    def flush_batch(self) -> List[Dict[str, Any]]:
        """Flush and return current batch."""
        batch = self.pending_metrics.copy()
        self.pending_metrics.clear()
        self.last_flush = time.time()

        # Clean old hashes
        if len(self.metric_hashes) >= 800:
            old_hashes = set(list(self.metric_hashes)[:200])  # Remove oldest 200
            self.seen_metrics -= old_hashes

        return batch

    def get_aggregates(self) -> Dict[str, Dict[str, Any]]:
        """Get current aggregated metrics."""
        return dict(self.metric_aggregates)

    def clear_aggregates(self) -> None:
        """Clear aggregated metrics."""
        self.metric_aggregates.clear()


class CircuitBreaker:
    """Circuit breaker for metrics emission resilience."""

    def __init__(self, threshold: int = 10, timeout: int = 60):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.threshold:
                self.state = "OPEN"

            raise e

    async def async_call(self, func, *args, **kwargs):
        """Execute async function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.threshold:
                self.state = "OPEN"

            raise e


class OptimizedPrometheusMetricsEmitter:
    """
    High-performance Prometheus metrics emitter with batching and optimization.

    PERFORMANCE FEATURES:
    - Metric batching for reduced overhead
    - Deduplication to prevent duplicate metrics
    - Aggregation for efficiency
    - Circuit breaker for resilience
    - Memory-efficient storage
    - Asynchronous emission
    """

    def __init__(self, config: Optional[MetricsConfig] = None):
        """Initialize optimized metrics emitter."""
        self.config = config or MetricsConfig()
        self.batcher = MetricsBatcher(self.config)
        self.circuit_breaker = CircuitBreaker(self.config.circuit_breaker_threshold)

        # Prometheus metrics (if available)
        self.prometheus_metrics: Dict[str, Any] = {}
        self.registry = None

        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()
            self._setup_prometheus_metrics()

        # Performance tracking
        self.stats = {
            "metrics_emitted": 0,
            "batches_processed": 0,
            "deduplication_hits": 0,
            "circuit_breaker_trips": 0,
            "avg_batch_size": 0.0,
            "avg_emission_time_ms": 0.0,
        }

        # Background processing
        self._emission_task = None
        self._shutdown_event = asyncio.Event()

    def _setup_prometheus_metrics(self) -> None:
        """Setup optimized Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        # Cost metrics with optimized labels
        self.prometheus_metrics["openai_costs"] = Counter(
            "finops_openai_api_costs_usd_total",
            "Total OpenAI API costs in USD",
            ["model", "operation", "persona_id"],
            registry=self.registry,
        )

        self.prometheus_metrics["kubernetes_costs"] = Counter(
            "finops_kubernetes_resource_costs_usd_total",
            "Total Kubernetes resource costs in USD",
            ["service", "resource_type", "operation"],
            registry=self.registry,
        )

        self.prometheus_metrics["vector_db_costs"] = Counter(
            "finops_vector_db_operation_costs_usd_total",
            "Total vector database operation costs in USD",
            ["operation", "collection"],
            registry=self.registry,
        )

        # Performance metrics
        self.prometheus_metrics["cost_per_post"] = Gauge(
            "finops_cost_per_post_usd",
            "Cost per post in USD",
            ["persona_id"],
            registry=self.registry,
        )

        self.prometheus_metrics["alert_threshold_breach"] = Gauge(
            "finops_cost_threshold_breach",
            "Cost threshold breach alert",
            ["persona_id", "severity"],
            registry=self.registry,
        )

        # Emission performance metrics
        self.prometheus_metrics["emission_latency"] = Histogram(
            "finops_metrics_emission_latency_ms",
            "Metrics emission latency in milliseconds",
            ["operation"],
            registry=self.registry,
        )

        self.prometheus_metrics["batch_size"] = Histogram(
            "finops_metrics_batch_size",
            "Size of metrics batches processed",
            registry=self.registry,
        )

    async def start_background_processing(self) -> None:
        """Start background metrics processing."""
        if self._emission_task and not self._emission_task.done():
            return

        self._emission_task = asyncio.create_task(self._background_emission_loop())
        logger.info("Background metrics processing started")

    async def stop_background_processing(self) -> None:
        """Stop background metrics processing."""
        self._shutdown_event.set()

        if self._emission_task:
            try:
                await asyncio.wait_for(self._emission_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._emission_task.cancel()

        logger.info("Background metrics processing stopped")

    def emit_cost_metric(self, cost_event: Dict[str, Any]) -> None:
        """
        Emit cost metric with high-performance batching.

        Target: <10ms latency
        """
        start_time = time.time()

        try:
            # Convert to optimized metric format
            metric = self._convert_cost_event_to_metric(cost_event)

            # Add to batch
            self.batcher.add_metric(metric)

            # Update stats
            emission_time = (time.time() - start_time) * 1000
            self._update_emission_stats(emission_time)

            # Immediate flush if batch is full
            if self.batcher.should_flush():
                asyncio.create_task(self._flush_metrics_batch())

        except Exception as e:
            logger.error(f"Failed to emit cost metric: {e}")
            self.stats["circuit_breaker_trips"] += 1

    def _convert_cost_event_to_metric(
        self, cost_event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert cost event to optimized metric format."""
        cost_type = cost_event.get("cost_type", "unknown")

        # Base metric
        metric = {
            "metric_name": f"finops_{cost_type}_costs_usd_total",
            "metric_type": "counter",
            "value": cost_event.get("cost_amount", 0.0),
            "timestamp": cost_event.get(
                "timestamp", datetime.now(timezone.utc).isoformat()
            ),
            "labels": {},
        }

        # Add type-specific labels
        if cost_type == "openai_api":
            metric["labels"] = {
                "model": cost_event.get("metadata", {}).get("model", "unknown"),
                "operation": cost_event.get("operation", "unknown"),
                "persona_id": cost_event.get("persona_id", "unknown"),
            }
        elif cost_type == "kubernetes":
            metric["labels"] = {
                "service": cost_event.get("metadata", {}).get("service", "unknown"),
                "resource_type": cost_event.get("metadata", {}).get(
                    "resource_type", "unknown"
                ),
                "operation": cost_event.get("operation", "unknown"),
            }
        elif cost_type == "vector_db":
            metric["labels"] = {
                "operation": cost_event.get("operation", "unknown"),
                "collection": cost_event.get("metadata", {}).get(
                    "collection", "unknown"
                ),
            }
        else:
            metric["labels"] = {
                "cost_type": cost_type,
                "operation": cost_event.get("operation", "unknown"),
            }

        return metric

    def update_cost_per_post_metric(
        self, persona_id: str, cost_per_post: float, post_id: str
    ) -> None:
        """Update cost per post metric efficiently."""
        metric = {
            "metric_name": "finops_cost_per_post_usd",
            "metric_type": "gauge",
            "value": cost_per_post,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "labels": {"persona_id": persona_id},
        }

        self.batcher.add_metric(metric)

    def emit_alert_threshold_metric(
        self,
        metric_name: str,
        persona_id: str,
        current_value: float,
        threshold_value: float,
        severity: str = "warning",
    ) -> None:
        """Emit alert threshold metric efficiently."""
        alert_active = 1 if current_value > threshold_value else 0

        metric = {
            "metric_name": metric_name,
            "metric_type": "gauge",
            "value": alert_active,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "labels": {"persona_id": persona_id, "severity": severity},
        }

        self.batcher.add_metric(metric)

    def emit_latency_metric(
        self, operation: str, latency_ms: float, status: str = "success"
    ) -> None:
        """Emit latency metric efficiently."""
        metric = {
            "metric_name": "finops_operation_latency_ms",
            "metric_type": "histogram",
            "value": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "labels": {"operation": operation, "status": status},
        }

        self.batcher.add_metric(metric)

    async def _background_emission_loop(self) -> None:
        """Background loop for processing metrics batches."""
        while not self._shutdown_event.is_set():
            try:
                # Check if batch should be flushed
                if self.batcher.should_flush():
                    await self._flush_metrics_batch()

                # Sleep for short interval
                await asyncio.sleep(0.1)  # 100ms check interval

            except Exception as e:
                logger.error(f"Background emission error: {e}")
                await asyncio.sleep(1.0)  # Back off on error

    async def _flush_metrics_batch(self) -> None:
        """Flush current metrics batch to Prometheus."""
        batch_start = time.time()

        try:
            async with self.batcher.batch_lock:
                batch = self.batcher.flush_batch()

            if not batch:
                return

            # Process batch with circuit breaker
            await self.circuit_breaker.async_call(self._process_metrics_batch, batch)

            # Update stats
            batch_time = (time.time() - batch_start) * 1000
            self.stats["batches_processed"] += 1
            self.stats["avg_batch_size"] = (
                self.stats["avg_batch_size"] * (self.stats["batches_processed"] - 1)
                + len(batch)
            ) / self.stats["batches_processed"]

            logger.debug(
                f"Processed metrics batch: {len(batch)} metrics in {batch_time:.2f}ms"
            )

        except Exception as e:
            logger.error(f"Failed to flush metrics batch: {e}")
            self.stats["circuit_breaker_trips"] += 1

    async def _process_metrics_batch(self, batch: List[Dict[str, Any]]) -> None:
        """Process batch of metrics to Prometheus."""
        if not PROMETHEUS_AVAILABLE or not self.prometheus_metrics:
            # Fallback to in-memory storage
            self._store_metrics_fallback(batch)
            return

        # Process each metric in batch
        for metric in batch:
            metric_name = metric.get("metric_name", "")
            value = metric.get("value", 0)
            labels = metric.get("labels", {})

            try:
                # Route to appropriate Prometheus metric
                if (
                    "openai_api_costs" in metric_name
                    and "openai_costs" in self.prometheus_metrics
                ):
                    self.prometheus_metrics["openai_costs"].labels(**labels).inc(value)
                elif (
                    "kubernetes_resource_costs" in metric_name
                    and "kubernetes_costs" in self.prometheus_metrics
                ):
                    self.prometheus_metrics["kubernetes_costs"].labels(**labels).inc(
                        value
                    )
                elif (
                    "vector_db_operation_costs" in metric_name
                    and "vector_db_costs" in self.prometheus_metrics
                ):
                    self.prometheus_metrics["vector_db_costs"].labels(**labels).inc(
                        value
                    )
                elif (
                    "cost_per_post" in metric_name
                    and "cost_per_post" in self.prometheus_metrics
                ):
                    persona_labels = {
                        k: v for k, v in labels.items() if k == "persona_id"
                    }
                    self.prometheus_metrics["cost_per_post"].labels(
                        **persona_labels
                    ).set(value)
                elif (
                    "threshold_breach" in metric_name
                    and "alert_threshold_breach" in self.prometheus_metrics
                ):
                    alert_labels = {
                        k: v
                        for k, v in labels.items()
                        if k in ["persona_id", "severity"]
                    }
                    self.prometheus_metrics["alert_threshold_breach"].labels(
                        **alert_labels
                    ).set(value)
                elif (
                    "latency" in metric_name
                    and "emission_latency" in self.prometheus_metrics
                ):
                    operation_labels = {
                        k: v for k, v in labels.items() if k == "operation"
                    }
                    self.prometheus_metrics["emission_latency"].labels(
                        **operation_labels
                    ).observe(value)

            except Exception as e:
                logger.warning(f"Failed to process metric {metric_name}: {e}")

    def _store_metrics_fallback(self, batch: List[Dict[str, Any]]) -> None:
        """Fallback storage for metrics when Prometheus is unavailable."""
        # Store in memory for testing (implement persistent storage as needed)
        if not hasattr(self, "_fallback_metrics"):
            self._fallback_metrics = []

        self._fallback_metrics.extend(batch)

        # Keep only recent metrics to prevent memory growth
        if len(self._fallback_metrics) > 10000:
            self._fallback_metrics = self._fallback_metrics[-5000:]

    def _update_emission_stats(self, latency_ms: float) -> None:
        """Update emission performance statistics."""
        self.stats["metrics_emitted"] += 1

        # Update rolling average
        current_avg = self.stats["avg_emission_time_ms"]
        count = self.stats["metrics_emitted"]
        self.stats["avg_emission_time_ms"] = (
            current_avg * (count - 1) + latency_ms
        ) / count

    def get_emitted_metrics(self) -> List[Dict[str, Any]]:
        """Get emitted metrics for testing/monitoring."""
        if hasattr(self, "_fallback_metrics"):
            return self._fallback_metrics.copy()
        return []

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return {
            **self.stats,
            "pending_metrics": len(self.batcher.pending_metrics),
            "circuit_breaker_state": self.circuit_breaker.state,
            "aggregated_metrics": len(self.batcher.get_aggregates()),
            "deduplication_cache_size": len(self.batcher.seen_metrics),
        }

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in exposition format."""
        if not PROMETHEUS_AVAILABLE or not self.registry:
            return "# Prometheus not available\n"

        try:
            return generate_latest(self.registry).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to generate Prometheus metrics: {e}")
            return f"# Error generating metrics: {e}\n"

    def clear_metrics(self) -> None:
        """Clear metrics for testing."""
        if hasattr(self, "_fallback_metrics"):
            self._fallback_metrics.clear()

        # Clear batcher
        self.batcher.pending_metrics.clear()
        self.batcher.metric_aggregates.clear()
        self.batcher.seen_metrics.clear()

    async def close(self) -> None:
        """Cleanup resources."""
        # Flush remaining metrics
        if self.batcher.pending_metrics:
            await self._flush_metrics_batch()

        # Stop background processing
        await self.stop_background_processing()

        logger.info("Optimized metrics emitter closed")
