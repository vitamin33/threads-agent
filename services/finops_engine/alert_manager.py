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
from datetime import datetime


class AlertManager:
    """Multi-channel alert manager for cost anomalies."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize alert manager with channel configurations."""
        self.config = config or {
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

    async def send_alert(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert through appropriate channels based on severity."""
        severity = anomaly_data.get("severity", "medium")
        channels_to_notify = self.config["severity_routing"].get(severity, ["slack"])

        results = {}

        # Send to each required channel
        for channel in channels_to_notify:
            if channel == "slack":
                results[channel] = await self.send_slack_alert(anomaly_data)
            elif channel == "pagerduty":
                results[channel] = await self.send_pagerduty_alert(anomaly_data)
            elif channel == "email":
                results[channel] = await self.send_email_alert(anomaly_data)

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
            "timestamp": datetime.utcnow().isoformat(),
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
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def send_email_alert(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email alert."""
        # Simulate sending email alert
        await asyncio.sleep(0.01)  # Simulate network call

        return {
            "success": True,
            "channel": "email",
            "recipients": self.config["channels"]["email"]["recipients"],
            "timestamp": datetime.utcnow().isoformat(),
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

        return message
