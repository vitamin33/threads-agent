"""
Alert Channel Manager for CRA-241

Multi-channel alert system supporting:
- Slack, Discord, Telegram, and custom webhooks
- Parallel processing for <60s SLA
- Rich formatting per channel type
- Graceful handling of missing configurations
- Retry logic for failed alerts
- Severity-based color coding

Target: Sub-60s alert delivery with 99.9% reliability.
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Any


class AlertChannelManager:
    """Multi-channel alert system for FinOps notifications."""

    def __init__(self):
        """Initialize AlertChannelManager with default configuration."""
        self.channels = []

    async def send_alert(
        self, alert_data: Dict[str, Any], channels: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Send alert to specified channels.

        Args:
            alert_data: Alert information including title, message, severity
            channels: List of channel names to send to (e.g., ['slack', 'discord'])

        Returns:
            Dict mapping channel names to their send results
        """
        # Create tasks for parallel execution
        tasks = []
        channel_names = []
        results = {}

        for channel in channels:
            if channel == "slack":
                # Support both Bot Token and Webhook URL methods
                if os.environ.get("SLACK_BOT_TOKEN") or os.environ.get(
                    "SLACK_WEBHOOK_URL"
                ):
                    tasks.append(self._send_slack_alert(alert_data))
                    channel_names.append("slack")
                else:
                    results["slack"] = {
                        "status": "skipped",
                        "reason": "Slack bot token or webhook URL not configured",
                    }
            elif channel == "discord":
                if os.environ.get("DISCORD_WEBHOOK_URL"):
                    tasks.append(self._send_discord_alert(alert_data))
                    channel_names.append("discord")
                else:
                    results["discord"] = {
                        "status": "skipped",
                        "reason": "Discord webhook URL not configured",
                    }
            elif channel == "telegram":
                if os.environ.get("TELEGRAM_BOT_TOKEN"):
                    tasks.append(self._send_telegram_alert(alert_data))
                    channel_names.append("telegram")
                else:
                    results["telegram"] = {
                        "status": "skipped",
                        "reason": "Telegram bot token not configured",
                    }
            elif channel == "webhook":
                if os.environ.get("CUSTOM_WEBHOOK_URL"):
                    tasks.append(self._send_webhook_alert(alert_data))
                    channel_names.append("webhook")
                else:
                    results["webhook"] = {
                        "status": "skipped",
                        "reason": "Custom webhook URL not configured",
                    }

        # Execute all tasks in parallel and merge with skipped results
        if tasks:
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            executed_results = dict(zip(channel_names, results_list))
            results.update(executed_results)

        return results

    async def _send_slack_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to Slack channel using Bot Token or Webhook URL."""
        bot_token = os.environ.get("SLACK_BOT_TOKEN")
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        channel = os.environ.get("ALERT_SLACK_CHANNEL", "#alerts")

        # Severity color mapping
        color_map = {
            "critical": "#FF0000",  # Red
            "warning": "#FFA500",  # Orange
            "info": "#00FF00",  # Green
        }

        severity = alert_data.get("severity", "info")
        color = color_map.get(severity, "#00FF00")

        # Format severity emoji
        emoji_map = {"critical": "🚨", "warning": "⚠️", "info": "💡"}
        emoji = emoji_map.get(severity, "💡")

        if bot_token:
            # Use Slack Bot API
            url = "https://slack.com/api/chat.postMessage"

            # Build message blocks
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *{alert_data.get('title', 'Alert')}*\n{alert_data.get('message', '')}",
                    },
                }
            ]

            # Add fields as context
            context_elements = []
            for key, value in alert_data.items():
                if key not in ["title", "message", "severity", "timestamp"]:
                    context_elements.append(
                        {
                            "type": "mrkdwn",
                            "text": f"*{key.replace('_', ' ').title()}:* {value}",
                        }
                    )

            if context_elements:
                blocks.append(
                    {
                        "type": "context",
                        "elements": context_elements[:10],  # Slack limit
                    }
                )

            payload = {
                "channel": channel,
                "blocks": blocks,
                "username": "FinOps Alert Bot",
                "icon_emoji": ":warning:",
            }

            headers = {
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json",
            }

            return await self._send_http_request_with_headers(url, payload, headers)

        elif webhook_url:
            # Use Webhook URL (legacy method)
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": alert_data.get("title", "Alert"),
                        "text": alert_data.get("message", ""),
                        "fields": [],
                    }
                ]
            }

            # Add additional fields if present
            for key, value in alert_data.items():
                if key not in ["title", "message", "severity"]:
                    payload["attachments"][0]["fields"].append(
                        {
                            "title": key.replace("_", " ").title(),
                            "value": str(value),
                            "short": True,
                        }
                    )

            return await self._send_http_request(webhook_url, payload)

        else:
            return {
                "status": "failed",
                "reason": "Neither Slack bot token nor webhook URL configured",
            }

    async def _send_discord_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to Discord channel with rich embed formatting."""
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

        # Severity color mapping for Discord embeds
        color_map = {
            "critical": 0xFF0000,  # Red
            "warning": 0xFFA500,  # Orange
            "info": 0x00FF00,  # Green
        }

        severity = alert_data.get("severity", "info")
        color = color_map.get(severity, 0x00FF00)

        # Discord uses embeds for rich formatting
        embed = {
            "title": alert_data.get("title", "Alert"),
            "description": alert_data.get("message", ""),
            "color": color,
            "fields": [],
            "timestamp": alert_data.get("timestamp", None),
        }

        # Add additional fields
        for key, value in alert_data.items():
            if key not in ["title", "message", "severity", "timestamp"]:
                embed["fields"].append(
                    {
                        "name": key.replace("_", " ").title(),
                        "value": str(value),
                        "inline": True,
                    }
                )

        payload = {"embeds": [embed]}

        return await self._send_http_request(webhook_url, payload)

    async def _send_telegram_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to Telegram channel with markdown formatting."""
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            return {
                "status": "failed",
                "reason": "Telegram bot token or chat ID not configured",
            }

        # Telegram severity emoji mapping
        emoji_map = {"critical": "🚨", "warning": "⚠️", "info": "💡"}

        severity = alert_data.get("severity", "info")
        emoji = emoji_map.get(severity, "💡")

        # Format message with markdown
        message_parts = [
            f"{emoji} *{alert_data.get('title', 'Alert')}*",
            f"{alert_data.get('message', '')}",
        ]

        # Add additional fields
        for key, value in alert_data.items():
            if key not in ["title", "message", "severity"]:
                field_name = key.replace("_", " ").title()
                message_parts.append(f"{field_name}: `{value}`")

        message_text = "\n".join(message_parts)

        telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message_text, "parse_mode": "Markdown"}

        return await self._send_http_request(telegram_url, payload)

    async def _send_webhook_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to custom webhook with standardized payload."""
        webhook_url = os.environ.get("CUSTOM_WEBHOOK_URL")

        # Standardized webhook payload format
        payload = {
            "alert": {
                "title": alert_data.get("title", "Alert"),
                "message": alert_data.get("message", ""),
                "severity": alert_data.get("severity", "info"),
                "timestamp": alert_data.get("timestamp", None),
                "metadata": {},
            }
        }

        # Add all other fields as metadata
        for key, value in alert_data.items():
            if key not in ["title", "message", "severity", "timestamp"]:
                payload["alert"]["metadata"][key] = value

        return await self._send_http_request(webhook_url, payload)

    async def _send_http_request(
        self, url: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Common HTTP request method with retry logic and timeout."""
        max_retries = 3
        timeout = 30  # 30 second timeout per channel

        for attempt in range(max_retries):
            try:
                timeout_session = aiohttp.ClientTimeout(total=timeout)
                async with aiohttp.ClientSession(timeout=timeout_session) as session:
                    async with session.post(url, json=payload) as response:
                        if response.status == 200:
                            return {"status": "success"}
                        elif attempt < max_retries - 1:
                            # Wait before retry (exponential backoff)
                            await asyncio.sleep(2**attempt)
                            continue
                        else:
                            return {
                                "status": "failed",
                                "reason": f"HTTP {response.status} after {max_retries} attempts",
                            }
            except asyncio.TimeoutError:
                return {
                    "status": "failed",
                    "reason": f"Request timeout after {timeout}s",
                }
            except Exception as e:
                if "timeout" in str(e).lower():
                    return {
                        "status": "failed",
                        "reason": f"Request timeout after {timeout}s",
                    }
                elif attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                else:
                    return {
                        "status": "failed",
                        "reason": f"Exception after {max_retries} attempts: {str(e)}",
                    }

        return {"status": "failed", "reason": "Unexpected error"}

    async def _send_http_request_with_headers(
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """HTTP request method with custom headers, retry logic and timeout."""
        max_retries = 3
        timeout = 30  # 30 second timeout per channel

        for attempt in range(max_retries):
            try:
                timeout_session = aiohttp.ClientTimeout(total=timeout)
                async with aiohttp.ClientSession(timeout=timeout_session) as session:
                    async with session.post(
                        url, json=payload, headers=headers
                    ) as response:
                        if response.status in [200, 201]:
                            return {"status": "success"}
                        elif attempt < max_retries - 1:
                            # Wait before retry (exponential backoff)
                            await asyncio.sleep(2**attempt)
                            continue
                        else:
                            return {
                                "status": "failed",
                                "reason": f"HTTP {response.status} after {max_retries} attempts",
                            }
            except asyncio.TimeoutError:
                return {
                    "status": "failed",
                    "reason": f"Request timeout after {timeout}s",
                }
            except Exception as e:
                if "timeout" in str(e).lower():
                    return {
                        "status": "failed",
                        "reason": f"Request timeout after {timeout}s",
                    }
                elif attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                else:
                    return {
                        "status": "failed",
                        "reason": f"Exception after {max_retries} attempts: {str(e)}",
                    }

        return {"status": "failed", "reason": "Unexpected error"}
