#!/bin/bash
# Compatibility shim for scripts/workflow-automation.sh
# Redirects calls to the new .dev-system CLI

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_SYSTEM_CLI="$SCRIPT_DIR/../cli/dev-system"

# Map legacy commands to new dev-system commands
case "${1:-}" in
    "ai-plan")
        echo "🔄 Redirecting to new planning system..."
        $DEV_SYSTEM_CLI brief
        ;;
    "tasks")
        case "${2:-}" in
            "start")
                echo "🔄 Redirecting to worktree system..."
                $DEV_SYSTEM_CLI worktree --name "${3:-task}" --focus "${4:-general}"
                ;;
            "commit")
                echo "🔄 Using legacy git workflow for now..."
                git add . && git commit -m "${4:-Auto commit}"
                ;;
            "ship")
                echo "🔄 Redirecting to release system..."
                $DEV_SYSTEM_CLI release --strategy canary
                ;;
            *)
                echo "❌ Unknown tasks command: ${2:-}"
                exit 1
                ;;
        esac
        ;;
    *)
        echo "🔄 Legacy workflow automation command: ${1:-}"
        echo "📖 Available commands in new system:"
        echo "  just dev-system brief       # Get morning priorities"
        echo "  just wt-setup <name>        # Setup worktree"
        echo "  just release canary         # Deploy with canary"
        echo "  just eval-run core          # Run evaluations"
        echo "  just metrics-today          # Check yesterday's metrics"
        ;;
esac