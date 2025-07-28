#!/bin/bash
# Voice notification when Claude is waiting for response

# macOS voice notification
if [[ "$OSTYPE" == "darwin"* ]]; then
    say "Claude Code is waiting motherfucker" &
    # Also show system notification
    osascript -e 'display notification "Claude Code needs your input" with title "Claude Code" sound name "Glass"'
fi

# Linux notification (requires espeak)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    espeak "Claude Code is waiting for your response" 2>/dev/null &
    notify-send "Claude Code" "Claude Code needs your input" -u critical
fi
