# scripts/efficient-dev.sh
#!/bin/bash

# Token-efficient development assistant

case "$1" in
    "next")
        # Minimal query for next action
        claude "Next specific task: check Linear progress, recommend immediate action (1-2 sentences)."
        ;;
    "code")
        if [ -z "$2" ]; then
            echo "Usage: $0 code 'specific requirement'"
            exit 1
        fi
        # Focused code generation
        claude "Generate code for: $2. Use existing patterns from my codebase. Return only the code with minimal explanation."
        ;;
    "fix")
        if [ -z "$2" ]; then
            echo "Usage: $0 fix 'error description'"
            exit 1
        fi
        # Targeted debugging
        claude "Debug this specific issue: $2. Check relevant logs/database. Provide solution only."
        ;;
    "task")
        # Efficient task planning
        claude "Current Linear project: create 3-5 specific tasks for next sprint. Format: Title | Description | Acceptance Criteria. No extra explanation."
        ;;
    "review")
        # Focused code review
        claude "Review my recent commits. Identify specific issues and actionable improvements only."
        ;;
    *)
        echo "Efficient commands:"
        echo "  next            - Get immediate next action"
        echo "  code 'req'      - Generate specific code"
        echo "  fix 'error'     - Debug specific issue"
        echo "  task            - Create sprint tasks"
        echo "  review          - Review recent changes"
        ;;
esac
