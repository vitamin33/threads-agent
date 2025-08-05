"""
Prometheus Metrics Emitter - Real-time cost metrics emission for monitoring and alerting.

Minimal implementation to make our TDD tests pass.
Integrates with existing Prometheus metrics infrastructure.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List


class PrometheusMetricsEmitter:
    """
    Emits cost-related metrics to Prometheus for real-time monitoring and alerting.

    Minimal implementation following TDD principles.
    Integrates with existing metrics.py infrastructure.
    """

    def __init__(self):
        """Initialize the Prometheus metrics emitter."""
        # For testing, we'll track emitted metrics in memory
        # In production, this would use the real Prometheus client
        self._metrics_emitted: List[Dict[str, Any]] = []

        # In production, these would be references to actual Prometheus metrics
        # from services.common.metrics import OPENAI_API_COSTS_TOTAL, etc.

    def emit_cost_metric(self, cost_event: Dict[str, Any]) -> None:
        """
        Emit a cost metric to Prometheus based on the cost event type.

        Routes to appropriate metric based on cost_type.
        """
        cost_type = cost_event.get("cost_type", "unknown")

        if cost_type == "openai_api":
            self._emit_openai_cost_metric(cost_event)
        elif cost_type == "kubernetes":
            self._emit_kubernetes_cost_metric(cost_event)
        elif cost_type == "database":
            self._emit_database_cost_metric(cost_event)
        elif cost_type == "vector_db":
            self._emit_vector_db_cost_metric(cost_event)
        else:
            # Generic cost metric for unknown types
            self._emit_generic_cost_metric(cost_event)

    def _emit_openai_cost_metric(self, cost_event: Dict[str, Any]) -> None:
        """Emit OpenAI API cost metric."""
        metric = {
            "metric_name": "openai_api_costs_usd_total",
            "metric_type": "counter",
            "value": cost_event["cost_amount"],
            "labels": {
                "model": cost_event.get("model", "unknown"),
                "operation": cost_event.get("operation", "unknown"),
                "persona_id": cost_event.get("persona_id", "unknown"),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._metrics_emitted.append(metric)

        # In production: OPENAI_API_COSTS_TOTAL.labels(**metric['labels']).inc(metric['value'])

    def _emit_kubernetes_cost_metric(self, cost_event: Dict[str, Any]) -> None:
        """Emit Kubernetes resource cost metric."""
        metric = {
            "metric_name": "kubernetes_resource_costs_usd_total",
            "metric_type": "counter",
            "value": cost_event["cost_amount"],
            "labels": {
                "service": cost_event.get("service", "unknown"),
                "resource_type": cost_event.get("resource_type", "unknown"),
                "operation": cost_event.get("operation", "unknown"),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._metrics_emitted.append(metric)

        # In production: KUBERNETES_RESOURCE_COSTS_TOTAL.labels(**metric['labels']).inc(metric['value'])

    def _emit_database_cost_metric(self, cost_event: Dict[str, Any]) -> None:
        """Emit database operation cost metric."""
        metric = {
            "metric_name": "database_operation_costs_usd_total",
            "metric_type": "counter",
            "value": cost_event["cost_amount"],
            "labels": {
                "db_type": cost_event.get("db_type", "unknown"),
                "operation": cost_event.get("operation", "unknown"),
                "persona_id": cost_event.get("persona_id", "unknown"),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._metrics_emitted.append(metric)

    def _emit_vector_db_cost_metric(self, cost_event: Dict[str, Any]) -> None:
        """Emit vector database operation cost metric."""
        metric = {
            "metric_name": "vector_db_operation_costs_usd_total",
            "metric_type": "counter",
            "value": cost_event["cost_amount"],
            "labels": {
                "operation": cost_event.get("operation", "unknown"),
                "collection": cost_event.get("collection", "unknown"),
                "persona_id": cost_event.get("persona_id", "unknown"),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._metrics_emitted.append(metric)

    def _emit_generic_cost_metric(self, cost_event: Dict[str, Any]) -> None:
        """Emit generic cost metric for unknown cost types."""
        metric = {
            "metric_name": "finops_generic_costs_usd_total",
            "metric_type": "counter",
            "value": cost_event["cost_amount"],
            "labels": {
                "cost_type": cost_event.get("cost_type", "unknown"),
                "operation": cost_event.get("operation", "unknown"),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._metrics_emitted.append(metric)

    def update_cost_per_post_metric(
        self, persona_id: str, cost_per_post: float, post_id: str
    ) -> None:
        """
        Update the cost per post metric for tracking $0.02 target.

        This is a key business metric for cost optimization.
        """
        metric = {
            "metric_name": "cost_per_post_usd",
            "metric_type": "gauge",
            "value": cost_per_post,
            "labels": {
                "persona_id": persona_id,
                "post_id": post_id,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._metrics_emitted.append(metric)

        # In production: COST_PER_POST.labels(persona_id=persona_id).set(cost_per_post)

    def emit_alert_threshold_metric(
        self,
        metric_name: str,
        persona_id: str,
        current_value: float,
        threshold_value: float,
        severity: str = "warning",
    ) -> None:
        """
        Emit alert threshold breach metric for cost monitoring.

        Used for alerting when costs exceed thresholds (e.g., 2x $0.02 = $0.04).
        """
        # Alert metric (1 = alert active, 0 = alert cleared)
        alert_active = 1 if current_value > threshold_value else 0

        metric = {
            "metric_name": metric_name,
            "metric_type": "gauge",
            "value": alert_active,
            "labels": {
                "persona_id": persona_id,
                "severity": severity,
                "current_value": str(current_value),
                "threshold_value": str(threshold_value),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._metrics_emitted.append(metric)

        # In production: would emit to alerting-specific metrics

    def emit_latency_metric(
        self, operation: str, latency_ms: float, status: str = "success"
    ) -> None:
        """
        Emit operation latency metric for performance monitoring.

        Tracks sub-second latency requirements for cost event storage.
        """
        metric = {
            "metric_name": "finops_operation_latency_ms",
            "metric_type": "histogram",
            "value": latency_ms,
            "labels": {
                "operation": operation,
                "status": status,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._metrics_emitted.append(metric)

        # In production: would use histogram metric for latency distribution

    def get_emitted_metrics(self) -> List[Dict[str, Any]]:
        """Get all emitted metrics (for testing purposes)."""
        return self._metrics_emitted.copy()

    def clear_metrics(self) -> None:
        """Clear emitted metrics (for testing purposes)."""
        self._metrics_emitted.clear()
