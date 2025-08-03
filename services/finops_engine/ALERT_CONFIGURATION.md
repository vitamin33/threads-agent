# FinOps Alert System Configuration

## Overview

The FinOps alert system supports multiple notification channels with enhanced Slack Bot Token integration and BM API support.

## Environment Variables

### Slack Configuration (Bot Token - Recommended)
```bash
SLACK_BOT_TOKEN=xoxb-8970898560864-8950765486740-LPDfpEPZ5cEFWNcN7RLplgoR
SLACK_SIGNING_SECRET=d14a59f32d23120a6cbd391e24f0e4c1
ALERT_SLACK_CHANNEL=#alerts
```

### Slack Configuration (Webhook - Legacy)
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Other Channels
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK
TELEGRAM_BOT_TOKEN=bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-123456789
CUSTOM_WEBHOOK_URL=https://your-custom-endpoint.com/webhook
```

## Helm Chart Configuration

Update your `values.yaml`:

```yaml
finopsEngine:
  enabled: true
  alertSlackChannel: "#alerts"
  alertWebhooks:
    # Slack Bot Token (preferred)
    slackBotToken: "xoxb-8970898560864-8950765486740-LPDfpEPZ5cEFWNcN7RLplgoR"
    slackSigningSecret: "d14a59f32d23120a6cbd391e24f0e4c1"
    # Legacy webhook support
    slack: ""                      # Slack webhook URL
    discord: ""                    # Discord webhook URL
    telegramBotToken: ""          # Telegram bot token
    telegramChatId: ""            # Telegram chat ID
    customWebhook: ""             # Custom webhook URL
```

## Supported Alert Channels

### 1. Slack (Bot Token) ✅ **Recommended**
- Uses official Slack Bot API
- Rich block formatting with emojis
- Configurable channel via `ALERT_SLACK_CHANNEL`
- Better reliability and features

### 2. Slack (Webhook) - Legacy
- Simple webhook integration
- Basic attachment formatting
- Fallback option

### 3. Discord
- Rich embed formatting with colors
- Webhook-based integration

### 4. Telegram
- Markdown formatting with emojis
- Bot token + chat ID required

### 5. Custom Webhook
- Generic webhook support
- Standardized payload format

## Alert Payload Examples

### Slack Bot Token Format
```json
{
  "channel": "#alerts",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "🚨 *Critical Cost Anomaly Detected*\\nCost per post has increased to $0.04"
      }
    }
  ],
  "username": "FinOps Alert Bot",
  "icon_emoji": ":warning:"
}
```

## Testing

Use the provided test script:

```bash
./test-finops-alerts.sh
```

Or test manually:

```bash
# Test anomaly detection
curl -X POST http://localhost:8095/anomaly/detect \\
  -H "Content-Type: application/json" \\
  -d '{
    "cost_per_post": 0.04,
    "viral_coefficient": 1.2,
    "pattern_usage_count": 5,
    "pattern_name": "hook_controversy",
    "engagement_rate": 0.05
  }'

# Test alert delivery
curl -X POST http://localhost:8095/anomaly/alert \\
  -H "Content-Type: application/json" \\
  -d '{
    "alert_data": {
      "title": "Test Alert",
      "message": "This is a test alert",
      "severity": "warning"
    },
    "channels": ["slack"]
  }'
```

## Features

✅ **Slack Bot Token Integration** - Enhanced Slack experience  
✅ **Multi-Channel Delivery** - Parallel alert processing  
✅ **Graceful Degradation** - Missing configs don't break other channels  
✅ **Retry Logic** - Exponential backoff for failed requests  
✅ **Rich Formatting** - Channel-specific message formatting  
✅ **<60s SLA** - Fast alert delivery guarantee  

## Migration from Webhook to Bot Token

1. **Create Slack App** with Bot Token
2. **Update environment variables** with Bot Token
3. **Deploy updated configuration**
4. **Remove webhook URL** (optional, both can coexist)

The system automatically prefers Bot Token over webhook if both are configured.