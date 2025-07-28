#!/bin/bash
# Setup universal Claude Code hooks for multi-teammate configuration

set -e

echo "🔧 Setting up universal Claude Code hooks..."

# Create hooks directory
echo "📁 Creating ~/.claude/hooks directory..."
mkdir -p ~/.claude/hooks

# Copy hook scripts
echo "📋 Copying hook scripts..."
cp .claude/hooks/notify-waiting.sh ~/.claude/hooks/
cp .claude/hooks/notify-complete.sh ~/.claude/hooks/

# Make executable
echo "✅ Making scripts executable..."
chmod +x ~/.claude/hooks/*.sh

# Create or update settings
echo "⚙️  Configuring Claude Code settings..."
cat > ~/.claude/settings.json << 'EOF'
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
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Tool: {{tool_name}}'"
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
      },
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "echo '✅ Todo list updated'"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '🚀 Processing request: {{prompt}}' | head -c 100"
          }
        ]
      }
    ]
  }
}
EOF

echo "🎯 Testing hooks..."
~/.claude/hooks/notify-waiting.sh

echo ""
echo "✅ Universal hooks setup complete!"
echo ""
echo "📍 Hooks location: ~/.claude/hooks/"
echo "⚙️  Settings location: ~/.claude/settings.json"
echo "🔊 Sounds directory: ~/.claude/sounds/"
echo ""
echo "🎤 For realistic voices:"
echo "   1. Generate audio at elevenlabs.io"
echo "   2. Save as: ~/.claude/sounds/claude-waiting.mp3"
echo "   3. Hooks will automatically use custom audio!"
echo ""
echo "This configuration works for all 3 virtual teammates!"