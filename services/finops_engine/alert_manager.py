"""
Alert Manager for Cost Anomaly Detection System (CRA-240)

Handles multi-channel notifications:
- Slack webhooks
- PagerDuty integration
- Email alerts
- Severity-based routing

Target: Support all notification channels with proper routing.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class AlertManager:
    """Multi-channel alert manager for cost anomalies."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize alert manager with channel configurations."""
        default_config = {
            "channels": {
                "slack": {
                    "webhook_url": "https://hooks.slack.com/test",
                    "channel": "#finops-alerts",
                    "enabled": True,
                },
                "pagerduty": {"integration_key": "test-key-123", "enabled": True},
                "email": {
                    "smtp_server": "smtp.gmail.com",
                    "recipients": ["team@company.com"],
                    "enabled": True,
                },
            },
            "severity_routing": {
                "critical": ["slack", "pagerduty", "email"],
                "high": ["slack", "pagerduty"],
                "medium": ["slack"],
                "low": ["email"],
            },
        }

        if config:
            # Deep merge config to preserve defaults for missing keys
            self.config = self._merge_configs(default_config, config)
        else:
            self.config = default_config

        # Rate limiting state
        self.alert_history = []
        self.rate_limit_config = self.config.get("rate_limiting", {})
        self.deduplication_cache = {}

    def _merge_configs(
        self, default: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge configuration dictionaries."""
        result = default.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _is_rate_limited(self, anomaly_data: Dict[str, Any]) -> bool:
        """Check if alert should be rate limited."""
        if not self.rate_limit_config:
            return False

        max_alerts_per_minute = self.rate_limit_config.get("max_alerts_per_minute", 10)
        current_time = datetime.now(timezone.utc)

        # Clean old entries (older than 1 minute)
        cutoff_time = current_time.timestamp() - 60
        self.alert_history = [t for t in self.alert_history if t > cutoff_time]

        # Check if we're over the limit
        if len(self.alert_history) >= max_alerts_per_minute:
            return True

        # Add current alert to history
        self.alert_history.append(current_time.timestamp())
        return False

    def _is_duplicate(self, anomaly_data: Dict[str, Any]) -> bool:
        """Check if this is a duplicate alert."""
        if not self.rate_limit_config:
            return False

        # Create a key for deduplication
        dedup_key = f"{anomaly_data.get('persona_id', '')}-{anomaly_data.get('anomaly_type', '')}"
        current_time = datetime.now(timezone.utc)

        # Check if we've seen this recently (last 5 minutes)
        if dedup_key in self.deduplication_cache:
            last_time = self.deduplication_cache[dedup_key]
            if (current_time - last_time).total_seconds() < 300:  # 5 minutes
                return True

        # Update cache
        self.deduplication_cache[dedup_key] = current_time
        return False

    async def send_alert(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert through appropriate channels based on severity."""
        # Check rate limiting
        if self._is_rate_limited(anomaly_data):
            return {
                "rate_limited": True,
                "message": "Alert blocked due to rate limiting",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Check for duplicates
        if self._is_duplicate(anomaly_data):
            return {
                "duplicate": True,
                "message": "Duplicate alert suppressed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        severity = anomaly_data.get("severity", "medium")
        channels_to_notify = self.config.get("severity_routing", {}).get(
            severity, ["slack"]
        )

        results = {}

        # Send to each required channel
        for channel in channels_to_notify:
            try:
                if channel == "slack":
                    results[channel] = await self.send_slack_alert(anomaly_data)
                elif channel == "pagerduty":
                    results[channel] = await self.send_pagerduty_alert(anomaly_data)
                elif channel == "email":
                    results[channel] = await self.send_email_alert(anomaly_data)
            except Exception as e:
                results[channel] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        return results

    async def send_slack_alert(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to Slack channel."""
        # Simulate sending Slack alert
        message = self.format_slack_message(anomaly_data)

        # In real implementation, this would call Slack webhook
        await asyncio.sleep(0.01)  # Simulate network call

        return {
            "success": True,
            "channel": "slack",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def send_pagerduty_alert(
        self, anomaly_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send alert to PagerDuty."""
        # Simulate sending PagerDuty alert
        await asyncio.sleep(0.01)  # Simulate network call

        return {
            "success": True,
            "channel": "pagerduty",
            "incident_key": f"cost-anomaly-{anomaly_data.get('persona_id', 'unknown')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def send_email_alert(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email alert."""
        # Simulate sending email alert
        await asyncio.sleep(0.01)  # Simulate network call

        return {
            "success": True,
            "channel": "email",
            "recipients": self.config["channels"]["email"]["recipients"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def format_slack_message(self, anomaly_data: Dict[str, Any]) -> str:
        """Format anomaly data for Slack message."""
        anomaly_type = anomaly_data.get("anomaly_type", "unknown")
        severity = anomaly_data.get("severity", "medium")
        persona_id = anomaly_data.get("persona_id", "unknown")

        message = "🚨 COST ANOMALY DETECTED\n"
        message += f"Type: {anomaly_type}\n"
        message += f"Severity: {severity.upper()}\n"
        message += f"Persona: {persona_id}\n"

        # Add specific details based on anomaly type
        if anomaly_type == "cost_spike":
            current_cost = anomaly_data.get("current_cost", 0)
            multiplier = anomaly_data.get("multiplier", 0)
            message += f"Current cost: ${current_cost:.3f}\n"
            message += f"Multiplier: {multiplier:.2f}x baseline"
        elif anomaly_type == "efficiency_drop":
            efficiency_drop_percent = anomaly_data.get("efficiency_drop_percent", 0)
            message += f"Performance efficiency drop: {efficiency_drop_percent}%"
        elif anomaly_type == "negative_roi":
            roi_percent = anomaly_data.get("roi_percent", 0)
            message += f"ROI: {roi_percent}%"
        elif anomaly_type == "budget_overrun":
            current_spend = anomaly_data.get("current_spend", 0)
            budget_limit = anomaly_data.get("budget_limit", 0)
            budget_usage_percent = anomaly_data.get("budget_usage_percent", 0)
            message += f"Budget overrun: {budget_usage_percent:.0f}%\n"
            message += (
                f"Current spend: ${current_spend:.0f}, Limit: ${budget_limit:.0f}"
            )

        return message
