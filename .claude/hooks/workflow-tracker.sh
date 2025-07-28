#!/bin/bash
# Track workflow progress and time spent

WORKFLOW_LOG="$CLAUDE_PROJECT_DIR/.claude/logs/workflow.log"
TOOL_NAME="${1:-unknown}"
ACTION="${2:-executed}"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$WORKFLOW_LOG")"

# Log workflow event
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Tool: $TOOL_NAME - Action: $ACTION" >> "$WORKFLOW_LOG"

# Track specific patterns
case "$TOOL_NAME" in
    "Bash")
        # Alert on dangerous commands
        if [[ "$ACTION" == *"rm -rf"* ]] || [[ "$ACTION" == *"sudo"* ]]; then
            "$CLAUDE_PROJECT_DIR/.claude/hooks/error-alert.sh" "Dangerous Command" "Attempted: $ACTION"
        fi
        ;;
    "Write"|"Edit"|"MultiEdit")
        # Track file modifications
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] File modified via $TOOL_NAME" >> "$WORKFLOW_LOG"
        ;;
    "Task")
        # Notify on subagent launch
        if [[ "$OSTYPE" == "darwin"* ]]; then
            say "Launching subagent for complex task" &
        fi
        ;;
esac