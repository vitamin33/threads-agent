"""
MLflow Performance Monitor for Kubernetes environments.

Tracks and reports performance metrics for MLflow Model Registry operations:
- Database query patterns and N+1 detection
- Connection pool utilization
- Memory usage patterns
- API call latency and throughput
- Cache hit rates
"""

import time
import threading
import logging
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from dataclasses import dataclass
from collections import defaultdict, deque
import psutil
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    operation_count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0
    error_count: int = 0
    memory_usage_mb: float = 0.0
    database_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    concurrent_operations: int = 0

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        return self.total_latency_ms / max(1, self.operation_count)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "operation_count": self.operation_count,
            "avg_latency_ms": self.avg_latency_ms,
            "min_latency_ms": self.min_latency_ms
            if self.min_latency_ms != float("inf")
            else 0,
            "max_latency_ms": self.max_latency_ms,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(1, self.operation_count),
            "memory_usage_mb": self.memory_usage_mb,
            "database_queries": self.database_queries,
            "cache_hit_rate": self.cache_hits
            / max(1, self.cache_hits + self.cache_misses),
            "concurrent_operations": self.concurrent_operations,
        }


class MLflowPerformanceMonitor:
    """Performance monitor for MLflow operations."""

    def __init__(self, enable_prometheus: bool = True):
        self._metrics: Dict[str, PerformanceMetrics] = defaultdict(PerformanceMetrics)
        self._lock = threading.RLock()
        self._operation_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self._active_operations: Dict[str, int] = defaultdict(int)
        self._enable_prometheus = enable_prometheus

        # Prometheus metrics
        if enable_prometheus:
            self._registry = CollectorRegistry()
            self._setup_prometheus_metrics()

    def _setup_prometheus_metrics(self) -> None:
        """Set up Prometheus metrics."""
        self.operation_counter = Counter(
            "mlflow_operations_total",
            "Total number of MLflow operations",
            ["operation_type", "status"],
            registry=self._registry,
        )

        self.latency_histogram = Histogram(
            "mlflow_operation_duration_seconds",
            "Duration of MLflow operations",
            ["operation_type"],
            registry=self._registry,
        )

        self.memory_gauge = Gauge(
            "mlflow_memory_usage_bytes",
            "Memory usage during MLflow operations",
            ["operation_type"],
            registry=self._registry,
        )

        self.database_queries_counter = Counter(
            "mlflow_database_queries_total",
            "Total database queries made",
            ["operation_type"],
            registry=self._registry,
        )

        self.cache_hits_counter = Counter(
            "mlflow_cache_hits_total",
            "Cache hits for MLflow operations",
            ["operation_type"],
            registry=self._registry,
        )

        self.concurrent_operations_gauge = Gauge(
            "mlflow_concurrent_operations",
            "Number of concurrent MLflow operations",
            ["operation_type"],
            registry=self._registry,
        )

    def track_operation(self, operation_type: str):
        """Decorator to track operation performance."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_with_tracking(
                    operation_type, func, *args, **kwargs
                )

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._execute_async_with_tracking(
                    operation_type, func, *args, **kwargs
                )

            # Return appropriate wrapper based on function type
            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return wrapper

        return decorator

    def _execute_with_tracking(
        self, operation_type: str, func: Callable, *args, **kwargs
    ):
        """Execute function with performance tracking."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        with self._lock:
            self._active_operations[operation_type] += 1
            if self._enable_prometheus:
                self.concurrent_operations_gauge.labels(
                    operation_type=operation_type
                ).inc()

        try:
            # Track database queries if MLflow client is involved
            initial_query_count = self._get_database_query_count()

            result = func(*args, **kwargs)

            # Calculate metrics
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - start_memory
            query_count = self._get_database_query_count() - initial_query_count

            self._record_success(operation_type, latency_ms, memory_delta, query_count)

            return result

        except Exception as e:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            self._record_error(operation_type, latency_ms, str(e))
            raise

        finally:
            with self._lock:
                self._active_operations[operation_type] -= 1
                if self._enable_prometheus:
                    self.concurrent_operations_gauge.labels(
                        operation_type=operation_type
                    ).dec()

    async def _execute_async_with_tracking(
        self, operation_type: str, func: Callable, *args, **kwargs
    ):
        """Execute async function with performance tracking."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        with self._lock:
            self._active_operations[operation_type] += 1
            if self._enable_prometheus:
                self.concurrent_operations_gauge.labels(
                    operation_type=operation_type
                ).inc()

        try:
            initial_query_count = self._get_database_query_count()

            result = await func(*args, **kwargs)

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - start_memory
            query_count = self._get_database_query_count() - initial_query_count

            self._record_success(operation_type, latency_ms, memory_delta, query_count)

            return result

        except Exception as e:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            self._record_error(operation_type, latency_ms, str(e))
            raise

        finally:
            with self._lock:
                self._active_operations[operation_type] -= 1
                if self._enable_prometheus:
                    self.concurrent_operations_gauge.labels(
                        operation_type=operation_type
                    ).dec()

    def _record_success(
        self,
        operation_type: str,
        latency_ms: float,
        memory_delta: float,
        query_count: int,
    ) -> None:
        """Record successful operation metrics."""
        with self._lock:
            metrics = self._metrics[operation_type]
            metrics.operation_count += 1
            metrics.total_latency_ms += latency_ms
            metrics.min_latency_ms = min(metrics.min_latency_ms, latency_ms)
            metrics.max_latency_ms = max(metrics.max_latency_ms, latency_ms)
            metrics.memory_usage_mb += memory_delta
            metrics.database_queries += query_count

            # Store operation history
            self._operation_history[operation_type].append(
                {
                    "timestamp": time.time(),
                    "latency_ms": latency_ms,
                    "memory_delta_mb": memory_delta,
                    "query_count": query_count,
                    "status": "success",
                }
            )

            # Update Prometheus metrics
            if self._enable_prometheus:
                self.operation_counter.labels(
                    operation_type=operation_type, status="success"
                ).inc()
                self.latency_histogram.labels(operation_type=operation_type).observe(
                    latency_ms / 1000
                )
                self.memory_gauge.labels(operation_type=operation_type).set(
                    memory_delta * 1024 * 1024
                )
                self.database_queries_counter.labels(operation_type=operation_type).inc(
                    query_count
                )

    def _record_error(
        self, operation_type: str, latency_ms: float, error_message: str
    ) -> None:
        """Record error metrics."""
        with self._lock:
            metrics = self._metrics[operation_type]
            metrics.operation_count += 1
            metrics.error_count += 1
            metrics.total_latency_ms += latency_ms

            # Store error in history
            self._operation_history[operation_type].append(
                {
                    "timestamp": time.time(),
                    "latency_ms": latency_ms,
                    "status": "error",
                    "error": error_message,
                }
            )

            # Update Prometheus metrics
            if self._enable_prometheus:
                self.operation_counter.labels(
                    operation_type=operation_type, status="error"
                ).inc()

    def record_cache_hit(self, operation_type: str) -> None:
        """Record cache hit."""
        with self._lock:
            self._metrics[operation_type].cache_hits += 1
            if self._enable_prometheus:
                self.cache_hits_counter.labels(operation_type=operation_type).inc()

    def record_cache_miss(self, operation_type: str) -> None:
        """Record cache miss."""
        with self._lock:
            self._metrics[operation_type].cache_misses += 1

    def get_metrics(self, operation_type: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics."""
        with self._lock:
            if operation_type:
                return {operation_type: self._metrics[operation_type].to_dict()}
            else:
                return {op: metrics.to_dict() for op, metrics in self._metrics.items()}

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            total_operations = sum(m.operation_count for m in self._metrics.values())
            total_errors = sum(m.error_count for m in self._metrics.values())

            # Find bottlenecks
            slowest_operations = sorted(
                [(op, m.avg_latency_ms) for op, m in self._metrics.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:5]

            # Find N+1 query patterns
            high_query_operations = [
                (op, m.database_queries / max(1, m.operation_count))
                for op, m in self._metrics.items()
                if m.database_queries / max(1, m.operation_count)
                > 10  # More than 10 queries per operation
            ]

            return {
                "total_operations": total_operations,
                "total_errors": total_errors,
                "overall_error_rate": total_errors / max(1, total_operations),
                "slowest_operations": slowest_operations,
                "potential_n_plus_1_queries": high_query_operations,
                "memory_usage_by_operation": {
                    op: m.memory_usage_mb / max(1, m.operation_count)
                    for op, m in self._metrics.items()
                },
                "concurrent_operations": dict(self._active_operations),
            }

    def get_recent_operations(
        self, operation_type: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent operations for debugging."""
        with self._lock:
            history = list(self._operation_history[operation_type])
            return history[-limit:]

    def detect_performance_issues(self) -> List[Dict[str, Any]]:
        """Detect performance issues automatically."""
        issues = []

        with self._lock:
            for operation_type, metrics in self._metrics.items():
                # High error rate
                if metrics.error_count / max(1, metrics.operation_count) > 0.1:
                    issues.append(
                        {
                            "type": "high_error_rate",
                            "operation": operation_type,
                            "error_rate": metrics.error_count / metrics.operation_count,
                            "severity": "critical",
                        }
                    )

                # High latency
                if metrics.avg_latency_ms > 5000:  # 5 seconds
                    issues.append(
                        {
                            "type": "high_latency",
                            "operation": operation_type,
                            "avg_latency_ms": metrics.avg_latency_ms,
                            "severity": "warning",
                        }
                    )

                # Potential N+1 queries
                avg_queries = metrics.database_queries / max(1, metrics.operation_count)
                if avg_queries > 10:
                    issues.append(
                        {
                            "type": "potential_n_plus_1",
                            "operation": operation_type,
                            "avg_queries_per_operation": avg_queries,
                            "severity": "critical",
                        }
                    )

                # High memory usage
                avg_memory = metrics.memory_usage_mb / max(1, metrics.operation_count)
                if avg_memory > 100:  # 100MB per operation
                    issues.append(
                        {
                            "type": "high_memory_usage",
                            "operation": operation_type,
                            "avg_memory_mb": avg_memory,
                            "severity": "warning",
                        }
                    )

        return issues

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._operation_history.clear()
            self._active_operations.clear()

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def _get_database_query_count(self) -> int:
        """Get database query count (placeholder - would integrate with actual DB monitoring)."""
        # This would integrate with your PostgreSQL monitoring
        # For now, return 0 as placeholder
        return 0

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        if not self._enable_prometheus:
            return ""

        from prometheus_client import generate_latest

        return generate_latest(self._registry).decode("utf-8")


# Global performance monitor instance
_global_monitor = MLflowPerformanceMonitor()


def get_performance_monitor() -> MLflowPerformanceMonitor:
    """Get the global performance monitor instance."""
    return _global_monitor


def track_mlflow_operation(operation_type: str):
    """Decorator for tracking MLflow operations."""
    return _global_monitor.track_operation(operation_type)
