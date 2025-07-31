#!/bin/bash
# Custom notification for sub-agent task completion

AGENT_TYPE="${1:-subagent}"
TASK_DESC="${2:-task}"

# macOS notification with custom sound
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Use custom TD_Default sound
    osascript -e "display notification \"$AGENT_TYPE completed: $TASK_DESC\" with title \"Claude Code Sub-Agent\" sound name \"TD_Default\""
    
    # Optional: Also play the sound file directly for reliability
    # afplay ~/Library/Sounds/TD_Default.wav &
fi

# Linux notification
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    notify-send "Claude Code Sub-Agent" "$AGENT_TYPE completed: $TASK_DESC" -u normal
fi