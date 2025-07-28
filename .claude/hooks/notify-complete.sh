#!/bin/bash
# Voice notification when Claude completes a task

TASK_TYPE="${1:-task}"

# macOS voice notification
if [[ "$OSTYPE" == "darwin"* ]]; then
    say "Claude Code has completed the $TASK_TYPE" &
    osascript -e "display notification \"$TASK_TYPE completed successfully\" with title \"Claude Code\" sound name \"Blow\""
fi

# Linux notification
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    espeak "Claude Code has completed the $TASK_TYPE" 2>/dev/null &
    notify-send "Claude Code" "$TASK_TYPE completed successfully" -u normal
fi