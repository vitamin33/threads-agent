# Claude Code Hooks Integration Guide

## 🎯 Overview
This guide shows how to integrate Claude Code hooks into your workflow for notifications, automation, and monitoring.

## 🔊 Voice Notifications Setup

### What's Included
1. **Waiting Notification** - Alerts when Claude needs your input
2. **Completion Alerts** - Notifies when tasks/subagents finish
3. **Error Alerts** - Critical notifications for errors
4. **Workflow Tracking** - Logs all tool usage

### Installation
```bash
# Make scripts executable
chmod +x .claude/hooks/*.sh

# Test voice notification (macOS)
.claude/hooks/notify-waiting.sh

# Create logs directory
mkdir -p .claude/logs
```

## 📋 Available Hooks

### 1. **Stop Hook** - When Claude Waits
- Triggers voice: "Claude Code is waiting for your response"
- Shows system notification
- Perfect for multitasking

### 2. **SubagentStop Hook** - Task Completion
- Announces: "Claude Code has completed the subagent task"
- Tracks complex task completion

### 3. **PreToolUse Hook** - Workflow Tracking
- Logs all tool usage to `.claude/logs/workflow.log`
- Warns on dangerous commands (rm -rf, sudo)
- Shows command preview for Bash

### 4. **PostToolUse Hook** - Success Notifications
- Notifies on Task agent completion
- Confirms TodoWrite updates

### 5. **UserPromptSubmit Hook** - Request Tracking
- Shows what Claude is processing
- Useful for long-running tasks

### 6. **PreCompact Hook** - Memory Management
- Warns when context is getting full
- Signals long conversation

## 🚀 Advanced Use Cases

### 1. Pomodoro Integration
```bash
#!/bin/bash
# .claude/hooks/pomodoro.sh
# Start 25-min timer when task begins
osascript -e 'display notification "Starting 25-min work session" with title "Pomodoro"'
sleep 1500
say "Time for a 5 minute break"
```

### 2. Git Auto-Commit Safety
```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{
      "type": "command",
      "command": "grep -q 'git.*push\\|git.*commit' <<< '{{parameters.command}}' && echo '⚠️  GIT OPERATION DETECTED - Review carefully!'"
    }]
  }]
}
```

### 3. Time Tracking
```bash
#!/bin/bash
# Track time spent per session
echo "Session start: $(date)" >> .claude/logs/time-tracking.log
```

### 4. Slack Integration
```bash
#!/bin/bash
# Send critical alerts to Slack
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Claude Code needs attention!"}' \
  YOUR_SLACK_WEBHOOK_URL
```

### 5. Focus Mode
```bash
#!/bin/bash
# Activate Do Not Disturb when Claude is working
osascript -e 'do shell script "defaults write com.apple.ncprefs.plist dnd_enabled -boolean true"'
```

## 🛠️ Customization Tips

### 1. Custom Voice Alerts
```bash
# Different voices for different events
say -v "Samantha" "Task completed successfully"
say -v "Alex" "Error detected"
```

### 2. Sound Effects
```bash
# Play custom sounds
afplay /System/Library/Sounds/Glass.aiff
```

### 3. Visual Indicators
```bash
# Change terminal color on events
echo -e "\033[0;31mERROR STATE\033[0m"
```

### 4. Smart Notifications
```bash
# Only notify during work hours
HOUR=$(date +%H)
if [ $HOUR -ge 9 ] && [ $HOUR -le 17 ]; then
    say "Claude needs your attention"
fi
```

## 🔧 Troubleshooting

### macOS Permissions
```bash
# Grant terminal permission for notifications
# System Preferences > Security & Privacy > Privacy > Notifications
```

### Linux Setup
```bash
# Install dependencies
sudo apt-get install espeak libnotify-bin
```

### Testing Hooks
```bash
# Test individual hooks
CLAUDE_PROJECT_DIR=$(pwd) .claude/hooks/notify-waiting.sh
```

## 📊 Monitoring

### View Logs
```bash
# Workflow history
tail -f .claude/logs/workflow.log

# Error tracking
tail -f .claude/logs/errors.log
```

### Statistics
```bash
# Most used tools
grep "Tool:" .claude/logs/workflow.log | sort | uniq -c | sort -nr
```

## 🎯 Best Practices

1. **Don't Overdo It** - Too many notifications become noise
2. **Critical Only** - Reserve voice for important events
3. **Context Aware** - Different alerts for different tools
4. **Performance** - Keep hooks lightweight and fast
5. **Security** - Validate inputs in hook scripts

## 🔒 Security Notes

- Hooks execute shell commands with your permissions
- Always validate and sanitize inputs
- Use read-only operations where possible
- Log suspicious activities
- Never store credentials in hooks

---

**Pro Tip**: Start with just the waiting notification - it's the most useful for staying productive while Claude works!