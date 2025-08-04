#!/usr/bin/env python3
"""
Demo script for Alert Channel Manager (CRA-241)

This script demonstrates how to use the AlertChannelManager to send alerts
to multiple channels in parallel with proper formatting and error handling.

Usage:
    python demo_alert_channels.py

Prerequisites:
    Set environment variables for the channels you want to test:
    - SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
    - DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK
    - TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    - TELEGRAM_CHAT_ID=your_chat_id
    - CUSTOM_WEBHOOK_URL=https://your.webhook.endpoint.com/alert
"""

import asyncio
import os
from alert_channels import AlertChannelManager


async def demo_cost_alert():
    """Demonstrate sending a cost alert to all configured channels."""
    manager = AlertChannelManager()

    # Example cost alert data
    alert_data = {
        "title": "High Cost Alert",
        "message": "Monthly spending has exceeded the threshold",
        "severity": "critical",
        "current_cost": 1250.75,
        "threshold": 1000.00,
        "overage": 250.75,
        "service": "OpenAI API",
        "timestamp": "2025-01-25T10:30:00Z",
    }

    print("🚨 Sending cost alert to all configured channels...")

    # Send to all channel types
    channels = ["slack", "discord", "telegram", "webhook"]
    result = await manager.send_alert(alert_data, channels)

    # Display results
    print("\nAlert Results:")
    print("=" * 50)
    for channel, status in result.items():
        emoji = (
            "✅"
            if status["status"] == "success"
            else "❌"
            if status["status"] == "failed"
            else "⏭️"
        )
        print(f"{emoji} {channel.upper()}: {status['status']}")
        if status["status"] != "success":
            print(f"   Reason: {status.get('reason', 'Unknown')}")

    return result


async def demo_performance_alert():
    """Demonstrate sending a performance warning alert."""
    manager = AlertChannelManager()

    # Example performance alert data
    alert_data = {
        "title": "Performance Degradation",
        "message": "System performance metrics are showing degradation",
        "severity": "warning",
        "cpu_usage": 85.2,
        "memory_usage": 78.5,
        "response_time": 1.2,
        "error_rate": 2.1,
        "timestamp": "2025-01-25T10:35:00Z",
    }

    print("\n⚠️ Sending performance alert to Slack and Discord...")

    # Send to specific channels only
    channels = ["slack", "discord"]
    result = await manager.send_alert(alert_data, channels)

    # Display results
    print("\nAlert Results:")
    print("=" * 50)
    for channel, status in result.items():
        emoji = (
            "✅"
            if status["status"] == "success"
            else "❌"
            if status["status"] == "failed"
            else "⏭️"
        )
        print(f"{emoji} {channel.upper()}: {status['status']}")
        if status["status"] != "success":
            print(f"   Reason: {status.get('reason', 'Unknown')}")

    return result


async def demo_info_alert():
    """Demonstrate sending an informational alert."""
    manager = AlertChannelManager()

    # Example info alert data
    alert_data = {
        "title": "System Status Update",
        "message": "Daily backup completed successfully",
        "severity": "info",
        "backup_size": "2.1 GB",
        "duration": "4 minutes",
        "files_backed_up": 15420,
        "timestamp": "2025-01-25T10:40:00Z",
    }

    print("\n💡 Sending info alert to Telegram...")

    # Send to Telegram only
    channels = ["telegram"]
    result = await manager.send_alert(alert_data, channels)

    # Display results
    print("\nAlert Results:")
    print("=" * 50)
    for channel, status in result.items():
        emoji = (
            "✅"
            if status["status"] == "success"
            else "❌"
            if status["status"] == "failed"
            else "⏭️"
        )
        print(f"{emoji} {channel.upper()}: {status['status']}")
        if status["status"] != "success":
            print(f"   Reason: {status.get('reason', 'Unknown')}")

    return result


async def main():
    """Run all demo scenarios."""
    print("Alert Channel Manager Demo")
    print("=" * 50)
    print("Testing multi-channel alert system with parallel delivery...")

    # Check which channels are configured
    configured_channels = []
    if os.environ.get("SLACK_WEBHOOK_URL"):
        configured_channels.append("Slack")
    if os.environ.get("DISCORD_WEBHOOK_URL"):
        configured_channels.append("Discord")
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        configured_channels.append("Telegram")
    if os.environ.get("CUSTOM_WEBHOOK_URL"):
        configured_channels.append("Custom Webhook")

    if configured_channels:
        print(f"Configured channels: {', '.join(configured_channels)}")
    else:
        print(
            "⚠️  No channels configured. Set environment variables to test actual delivery."
        )
        print("   The demo will still run but alerts will be skipped.")

    print()

    try:
        # Run demo scenarios
        await demo_cost_alert()
        await demo_performance_alert()
        await demo_info_alert()

        print("\n🎉 Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Parallel processing for fast delivery (<60s SLA)")
        print(
            "✅ Severity-based color coding (critical=red, warning=orange, info=green)"
        )
        print(
            "✅ Rich formatting per channel (Slack attachments, Discord embeds, etc.)"
        )
        print("✅ Graceful handling of missing configurations")
        print("✅ Retry logic with exponential backoff")
        print("✅ 30-second timeout per channel")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
