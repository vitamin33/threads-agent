#!/bin/bash
# Test Slack MCP Integration

echo "Testing Slack MCP Server Connection..."

# Export credentials
export SLACK_BOT_TOKEN="xoxb-8970898560864-8950765486740-LPDfpEPZ5cEFWNcN7RLplgoR"
export SLACK_SIGNING_SECRET="d14a59f32d23120a6cbd391e24f0e4c1"
export SLACK_CHANNEL="#alerts"

# Test sending a message using curl
echo "Sending test message to Slack #alerts channel..."

curl -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "alerts",
    "text": "🚀 Threads-Agent MCP Integration Test",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Threads-Agent MCP Server Test*\n✅ Slack MCP server configured successfully!"
        }
      },
      {
        "type": "divider"
      },
      {
        "type": "section",
        "fields": [
          {
            "type": "mrkdwn",
            "text": "*Status:*\nActive"
          },
          {
            "type": "mrkdwn",
            "text": "*Integration:*\nMCP Server"
          }
        ]
      }
    ]
  }' | jq .

echo "Test complete. Check #alerts channel for the message."