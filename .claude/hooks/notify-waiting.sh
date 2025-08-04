#!/bin/bash
# Voice notification when Claude is waiting for response

# macOS voice notification
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Option 1: Use custom audio file (e.g., from ElevenLabs)
    AUDIO_FILE="$HOME/.claude/sounds/claude-waiting.mp3"
    if [ -f "$AUDIO_FILE" ]; then
        afplay "$AUDIO_FILE" &
    else
        # Option 2: Fallback to system voice
        say -v "Samantha" -r 180 --volume=50 "Claude Code is waiting, motherfucker" &
    fi
    
    # Also show system notification
    osascript -e 'display notification "Claude Code needs your input" with title "Claude Code" sound name "Glass"'
fi

# Linux notification (requires espeak)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    espeak "Claude Code is waiting for your response" 2>/dev/null &
    notify-send "Claude Code" "Claude Code needs your input" -u critical
fi
