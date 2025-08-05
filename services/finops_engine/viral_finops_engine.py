"""
ViralFinOpsEngine - Main orchestrator for real-time cost data collection.

Integrates all cost tracking components for comprehensive FinOps monitoring.
"""

from typing import Dict, Any, Optional, List

try:
    from .openai_cost_tracker import OpenAICostTracker
    from .infrastructure_cost_tracker import InfrastructureCostTracker
    from .cost_event_storage import CostEventStorage
    from .prometheus_metrics_emitter import PrometheusMetricsEmitter
    from .post_cost_attributor import PostCostAttributor
    from .cost_anomaly_detector import CostAnomalyDetector
    from .alert_manager import AlertManager
    from .circuit_breaker import CircuitBreaker
except ImportError:
    # Fallback for standalone execution
    from openai_cost_tracker import OpenAICostTracker
    from infrastructure_cost_tracker import InfrastructureCostTracker
    from cost_event_storage import CostEventStorage
    from prometheus_metrics_emitter import PrometheusMetricsEmitter
    from post_cost_attributor import PostCostAttributor
    from cost_anomaly_detector import CostAnomalyDetector
    from alert_manager import AlertManager
    from circuit_breaker import CircuitBreaker


class ViralFinOpsEngine:
    """
    Main orchestrator for real-time cost data collection engine.

    Integrates all tracking components for comprehensive cost monitoring.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ViralFinOpsEngine with all required components."""
        default_config = {
            "cost_threshold_per_post": 0.02,
            "alert_threshold_multiplier": 2.0,
            "storage_latency_target_ms": 500,
            "anomaly_detection_enabled": False,
            "anomaly_check_interval_seconds": 30,
        }
        if config:
            default_config.update(config)
        self.config = default_config

        # Initialize all tracking components
        self.openai_tracker = OpenAICostTracker()
        self.infrastructure_tracker = InfrastructureCostTracker()
        self.vector_db_tracker = (
            self.infrastructure_tracker
        )  # Uses same tracker for vector DB
        self.monitoring_tracker = (
            self.infrastructure_tracker
        )  # Uses same tracker for monitoring
        self.cost_storage = CostEventStorage()
        self.prometheus_client = PrometheusMetricsEmitter()

        # Initialize post cost attributor for integration
        self.post_cost_attributor = PostCostAttributor()

        # Initialize anomaly detection components if enabled
        if self.config.get("anomaly_detection_enabled", False):
            self.anomaly_detector = CostAnomalyDetector()
            self.alert_manager = AlertManager()
            self.circuit_breaker = CircuitBreaker()

        # Track cost events per post for aggregation
        self._post_costs: Dict[str, List[Dict[str, Any]]] = {}

        # Historical data for anomaly detection
        self._historical_costs: Dict[str, List[float]] = {}

    async def track_openai_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str,
        persona_id: str,
        post_id: str,
    ) -> Dict[str, Any]:
        """Track OpenAI API cost and emit metrics."""
        # Generate cost event
        cost_event = self.openai_tracker.track_api_call(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            operation=operation,
            persona_id=persona_id,
            post_id=post_id,
        )

        # Store cost event
        await self.cost_storage.store_cost_event(cost_event)

        # Emit Prometheus metrics (with error handling)
        try:
            self.prometheus_client.emit_cost_metric(cost_event)
        except Exception:
            # Continue operation even if metrics emission fails
            pass

        # Track for post-level aggregation
        await self._add_post_cost(post_id, cost_event)

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
        """Track infrastructure cost (K8s, etc.) and emit metrics."""
        # Generate cost event
        cost_event = self.infrastructure_tracker.track_k8s_resource_usage(
            resource_type=resource_type,
            resource_name=f"{service}-{post_id}",
            service=service,
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            duration_minutes=duration_minutes,
            operation=operation,
        )

        # Add persona and post context
        cost_event["persona_id"] = persona_id
        cost_event["post_id"] = post_id

        # Store cost event
        await self.cost_storage.store_cost_event(cost_event)

        # Emit Prometheus metrics (with error handling)
        try:
            self.prometheus_client.emit_cost_metric(cost_event)
        except Exception:
            # Continue operation even if metrics emission fails
            pass

        # Track for post-level aggregation
        await self._add_post_cost(post_id, cost_event)

        return cost_event

    async def track_vector_db_cost(
        self,
        operation: str,
        query_count: int,
        collection: str,
        persona_id: str,
        post_id: str,
    ) -> Dict[str, Any]:
        """Track vector database cost and emit metrics."""
        # Generate cost event
        cost_event = self.infrastructure_tracker.track_vector_db_operation(
            operation=operation,
            query_count=query_count,
            collection=collection,
            persona_id=persona_id,
        )

        # Add post context
        cost_event["post_id"] = post_id

        # Store cost event
        await self.cost_storage.store_cost_event(cost_event)

        # Emit Prometheus metrics (with error handling)
        try:
            self.prometheus_client.emit_cost_metric(cost_event)
        except Exception:
            # Continue operation even if metrics emission fails
            pass

        # Track for post-level aggregation
        await self._add_post_cost(post_id, cost_event)

        return cost_event

    async def calculate_total_post_cost(self, post_id: str) -> float:
        """Calculate total cost for a specific post across all services."""
        if post_id not in self._post_costs:
            return 0.0

        total_cost = sum(event["cost_amount"] for event in self._post_costs[post_id])

        # Update cost per post metric
        if self._post_costs[post_id]:
            # Get persona_id from any event for this post
            persona_id = self._post_costs[post_id][0].get("persona_id", "unknown")
            self.prometheus_client.update_cost_per_post_metric(
                persona_id=persona_id, cost_per_post=total_cost, post_id=post_id
            )

        # Check alert thresholds
        await self._check_cost_thresholds(post_id, total_cost)

        return total_cost

    async def _check_cost_thresholds(self, post_id: str, total_cost: float) -> None:
        """Check if cost exceeds thresholds and emit alerts."""
        cost_threshold = self.config["cost_threshold_per_post"]
        alert_threshold = cost_threshold * self.config["alert_threshold_multiplier"]

        if total_cost > alert_threshold:
            # Get persona_id for alert context
            persona_id = "unknown"
            if post_id in self._post_costs and self._post_costs[post_id]:
                persona_id = self._post_costs[post_id][0].get("persona_id", "unknown")

            # Emit alert metric
            self.prometheus_client.emit_alert_threshold_metric(
                metric_name="cost_per_post_threshold_breach",
                persona_id=persona_id,
                current_value=total_cost,
                threshold_value=alert_threshold,
                severity="warning",
            )

    async def _add_post_cost(self, post_id: str, cost_event: Dict[str, Any]) -> None:
        """Add cost event to post-level tracking."""
        if post_id not in self._post_costs:
            self._post_costs[post_id] = []
        self._post_costs[post_id].append(cost_event)

        # Also track in PostCostAttributor for integration
        # Extract metadata from cost_event (everything except core fields)
        metadata = {
            k: v
            for k, v in cost_event.items()
            if k not in ["post_id", "cost_type", "cost_amount", "timestamp"]
        }

        await self.post_cost_attributor.track_cost_for_post(
            post_id=post_id,
            cost_type=cost_event.get("cost_type", "unknown"),
            cost_amount=cost_event.get("cost_amount", 0.0),
            metadata=metadata,
        )

    def track_cost_event(self, event: Dict[str, Any]) -> None:
        """Track a generic cost event - legacy interface."""
        # Route to appropriate tracker based on cost_type
        cost_type = event.get("cost_type", "unknown")

        if cost_type == "openai_api":
            # Handle via openai tracker
            pass
        elif cost_type in ["kubernetes", "database", "vector_db"]:
            # Handle via infrastructure tracker
            pass

        # Emit metrics
        self.prometheus_client.emit_cost_metric(event)

    async def check_for_anomalies(self, persona_id: str) -> Dict[str, Any]:
        """Check for cost anomalies for a specific persona."""
        if not self.config.get("anomaly_detection_enabled", False):
            return {"anomalies_detected": [], "alerts_sent": [], "actions_taken": []}

        # Get current costs for persona
        current_costs = []
        for post_costs in self._post_costs.values():
            for cost_event in post_costs:
                if cost_event.get("persona_id") == persona_id:
                    current_costs.append(cost_event.get("cost_amount", 0.0))

        # Use the maximum cost (most expensive operation) rather than average
        # This better detects expensive outliers
        current_max_cost = max(current_costs) if current_costs else 0.0

        # Get historical baseline for persona
        baseline_costs = self._historical_costs.get(
            persona_id, [0.018, 0.020, 0.017]
        )  # Default baseline

        # Detect anomalies
        anomalies_detected = []
        alerts_sent = []
        actions_taken = []

        # Statistical anomaly detection
        if hasattr(self, "anomaly_detector"):
            anomaly_result = self.anomaly_detector.detect_statistical_anomaly(
                current_cost=current_max_cost,
                baseline_costs=baseline_costs,
                persona_id=persona_id,
            )

            if anomaly_result["is_anomaly"]:
                anomalies_detected.append(anomaly_result)

                # Send alerts
                if hasattr(self, "alert_manager"):
                    alert_results = await self.alert_manager.send_alert(anomaly_result)
                    alerts_sent.append(alert_results)

                # Execute circuit breaker actions if needed
                if hasattr(
                    self, "circuit_breaker"
                ) and self.circuit_breaker.should_trigger(anomaly_result):
                    action_results = await self.circuit_breaker.execute_actions(
                        anomaly_result
                    )
                    actions_taken.append(action_results)

        return {
            "anomalies_detected": anomalies_detected,
            "alerts_sent": alerts_sent,
            "actions_taken": actions_taken,
        }
