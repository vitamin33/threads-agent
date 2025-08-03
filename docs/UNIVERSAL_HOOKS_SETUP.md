# Universal Claude Code Hooks for Multi-Teammate Setup

## Overview
This setup allows multiple virtual teammates (different git repositories) to share the same Claude Code hooks configuration for voice notifications and workflow tracking.

## Setup Instructions

### 1. Create Universal Hooks Directory
```bash
mkdir -p ~/.claude/hooks
```

### 2. Copy Universal Hooks
```bash
# Copy the notification scripts to user home
cp .claude/hooks/notify-waiting.sh ~/.claude/hooks/
cp .claude/hooks/notify-complete.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh
```

### 3. Configure Claude Code Settings
Create or update `~/.claude/settings.json` with:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/notify-waiting.sh"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/notify-complete.sh 'subagent task'"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/notify-complete.sh 'agent task'"
          }
        ]
      }
    ]
  }
}
```

## How It Works

### Shared Configuration
- All teammates use `~/.claude/settings.json` (user-level config)
- Hooks are stored in `~/.claude/hooks/` (accessible from any project)
- Uses `$HOME` variable instead of absolute paths

### Notifications
1. **Waiting Alert**: "Claude Code is waiting motherfucker"
   - Triggers when Claude finishes responding
   - Both voice and visual notification

2. **Completion Alerts**: "Claude Code has completed the [task type]"
   - Triggers when subagents or tasks complete
   - Different messages for different task types

## Benefits for Multi-Teammate Setup

1. **One Configuration**: Set up once, works for all repositories
2. **Consistent Experience**: All teammates get same notifications
3. **Easy Updates**: Change hooks in one place, affects all instances
4. **No Git Conflicts**: User-level config not checked into repos

## Testing

```bash
# Test waiting notification
~/.claude/hooks/notify-waiting.sh

# Test completion notification
~/.claude/hooks/notify-complete.sh "test task"
```

## Customization

### Using Custom Audio (ElevenLabs, etc.)

For ultra-realistic voices, use custom audio files:

1. **Generate Audio**:
   - Go to [ElevenLabs](https://elevenlabs.io)
   - Generate: "Claude Code is waiting, motherfucker"
   - Download as MP3

2. **Install Audio**:
   ```bash
   mkdir -p ~/.claude/sounds
   # Save your file as: ~/.claude/sounds/claude-waiting.mp3
   ```

3. **Automatic Usage**:
   - Hooks automatically detect and use custom audio
   - Falls back to system voice if file missing

### System Voice Options

```bash
# Most natural macOS voices:
say -v "Samantha" "text"  # US female (very natural)
say -v "Daniel" "text"    # UK male (professional)
say -v "Karen" "text"     # Australian female
say -v "Tessa" "text"     # South African female

# With speech rate adjustment:
say -v "Samantha" -r 180 "text"  # Slightly faster (more natural)
```

### Advanced Customization

```bash
# Example: Different voices for different times
HOUR=$(date +%H)
if [ $HOUR -ge 9 ] && [ $HOUR -le 17 ]; then
    say -v "Samantha" "Claude needs attention"
else
    say -v "Alex" "Claude is waiting"
fi
```

## Troubleshooting

### No Sound?
1. Check system volume
2. Ensure Terminal has accessibility permissions
3. Test with: `say "test"`

### Hooks Not Triggering?
1. Restart Claude Code after configuration
2. Check settings location: `ls -la ~/.claude/settings.json`
3. Verify scripts are executable: `ls -la ~/.claude/hooks/`

## Additional Notes

- Works with all 3 virtual teammates simultaneously
- Independent of repository location
- Survives repository clones/moves
- Can be version controlled separately if needed