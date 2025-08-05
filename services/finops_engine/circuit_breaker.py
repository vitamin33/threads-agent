"""
Circuit Breaker for Cost Anomaly Detection System (CRA-240)

Implements automated cost control responses:
- Request throttling
- Model switching (expensive -> cheaper)
- Persona pausing (as last resort)
- Human operator alerts

Target: Automatic cost control when anomalies are detected.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class CircuitBreaker:
    """Automated cost control circuit breaker."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize circuit breaker with thresholds and actions."""
        self.config = config or {
            "cost_spike_threshold": 3.0,  # 3x baseline triggers circuit breaker
            "budget_threshold": 0.90,  # 90% budget triggers circuit breaker
            "roi_threshold": -0.60,  # -60% ROI triggers circuit breaker
            "actions": {
                "throttle_requests": True,  # Reduce API request rate
                "disable_expensive_models": True,  # Switch to cheaper models
                "pause_persona": False,  # Don't fully pause (too aggressive)
                "alert_human_operator": True,  # Always alert humans
            },
        }

    def should_trigger(self, anomaly_data: Dict[str, Any]) -> bool:
        """Determine if circuit breaker should trigger based on anomaly data."""
        anomaly_type = anomaly_data.get("anomaly_type", "")
        severity = anomaly_data.get("severity", "medium")

        # Always trigger for critical anomalies
        if severity == "critical":
            return True

        # Check specific thresholds based on anomaly type
        if anomaly_type == "cost_spike":
            multiplier = anomaly_data.get("multiplier", 0)
            return multiplier >= self.config["cost_spike_threshold"]

        elif anomaly_type == "budget_overrun":
            budget_usage_percent = anomaly_data.get("budget_usage_percent", 0)
            return budget_usage_percent >= (self.config["budget_threshold"] * 100)

        elif anomaly_type == "negative_roi":
            roi_percent = anomaly_data.get("roi_percent", 0)
            return roi_percent <= (self.config["roi_threshold"] * 100)

        # Don't trigger for minor anomalies like efficiency drops
        return False

    async def execute_actions(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute circuit breaker actions based on configuration."""
        results = {}

        # Execute enabled actions
        if self.config["actions"]["throttle_requests"]:
            results["throttle_requests"] = await self.throttle_requests(anomaly_data)

        if self.config["actions"]["disable_expensive_models"]:
            results["switch_to_cheaper_models"] = await self.switch_to_cheaper_models(
                anomaly_data
            )

        if self.config["actions"]["pause_persona"]:
            results["pause_persona"] = await self.pause_persona(anomaly_data)

        if self.config["actions"]["alert_human_operator"]:
            results["alert_human_operator"] = await self.alert_human_operator(
                anomaly_data
            )

        return results

    async def throttle_requests(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Throttle API request rate to reduce costs."""
        # Simulate throttling implementation
        await asyncio.sleep(0.01)  # Simulate action execution

        # Calculate new rate limit based on severity
        severity = anomaly_data.get("severity", "medium")
        if severity == "critical":
            new_rate_limit = 10  # Very aggressive throttling
        elif severity == "high":
            new_rate_limit = 20  # Moderate throttling
        else:
            new_rate_limit = 50  # Light throttling

        return {
            "executed": True,
            "action": "throttle_requests",
            "new_rate_limit": new_rate_limit,
            "previous_rate_limit": 100,  # Assume previous was 100 req/min
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def switch_to_cheaper_models(
        self, anomaly_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Switch from expensive models to cheaper alternatives."""
        await asyncio.sleep(0.01)  # Simulate action execution

        # Define model switching logic
        model_mappings = {
            "gpt-4o": "gpt-3.5-turbo-0125",
            "gpt-4": "gpt-3.5-turbo-0125",
            "gpt-3.5-turbo-0125": "gpt-3.5-turbo-0125",  # Already cheapest
        }

        return {
            "executed": True,
            "action": "switch_to_cheaper_models",
            "model_mappings": model_mappings,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def pause_persona(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pause persona activity (last resort)."""
        await asyncio.sleep(0.01)  # Simulate action execution

        persona_id = anomaly_data.get("persona_id", "unknown")

        return {
            "executed": True,
            "action": "pause_persona",
            "persona_id": persona_id,
            "pause_duration_minutes": 60,  # Pause for 1 hour
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def alert_human_operator(
        self, anomaly_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Alert human operator about circuit breaker activation."""
        await asyncio.sleep(0.01)  # Simulate action execution

        return {
            "executed": True,
            "action": "alert_human_operator",
            "alert_sent": True,
            "channels": ["slack", "email"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
