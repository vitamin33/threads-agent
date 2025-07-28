#!/bin/bash
# Alert when Claude encounters errors or gets stuck

ERROR_TYPE="${1:-Error}"
ERROR_MSG="${2:-An error occurred}"

# Log error
echo "[$(date '+%Y-%m-%d %H:%M:%S')] $ERROR_TYPE: $ERROR_MSG" >> "$CLAUDE_PROJECT_DIR/.claude/logs/errors.log"

# macOS alert
if [[ "$OSTYPE" == "darwin"* ]]; then
    say "Alert! Claude Code encountered an error" &
    osascript -e "display alert \"Claude Code Error\" message \"$ERROR_MSG\" as critical"
fi

# Linux alert
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    espeak "Alert! Claude Code encountered an error" 2>/dev/null &
    notify-send "Claude Code Error" "$ERROR_MSG" -u critical -t 0
fi