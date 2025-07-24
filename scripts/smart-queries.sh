# /scripts/smart-queries.sh
#!/bin/bash

# Smart queries that leverage existing MCP context

# Context management system
CONTEXT_DIR="$HOME/.threads-agent/context"
CURRENT_SESSION="$CONTEXT_DIR/current.ctx"

# Ensure context directory exists
mkdir -p "$CONTEXT_DIR"

# Context management functions
save_context() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Usage: save_context <name>"
        return 1
    fi

    local ctx_file="$CONTEXT_DIR/${name}.ctx"

    # Save current working state
    {
        echo "# Threads-Agent Context: $name"
        echo "# Saved: $(date)"
        echo "TIMESTAMP=$(date +%s)"
        echo "PWD=$(pwd)"
        echo "BRANCH=$(git branch --show-current 2>/dev/null || echo 'unknown')"
        echo ""
        echo "# Git status"
        git status --porcelain 2>/dev/null | head -20 || echo "No git repo"
        echo ""
        echo "# Recent commits"
        git log --oneline -5 2>/dev/null || echo "No commits"
        echo ""
        echo "# Current Kubernetes context"
        kubectl config current-context 2>/dev/null || echo "No k8s context"
        echo ""
        echo "# Active pods"
        kubectl get pods --no-headers 2>/dev/null | head -10 || echo "No pods"
    } > "$ctx_file"

    # Set as current session
    cp "$ctx_file" "$CURRENT_SESSION"
    echo "Context saved: $name"
}

load_context() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Usage: load_context <name>"
        echo "Available contexts:"
        ls -1 "$CONTEXT_DIR"/*.ctx 2>/dev/null | xargs -n1 basename | sed 's/\.ctx$//' || echo "No saved contexts"
        return 1
    fi

    local ctx_file="$CONTEXT_DIR/${name}.ctx"
    if [ ! -f "$ctx_file" ]; then
        echo "Context not found: $name"
        return 1
    fi

    # Load and display context
    echo "Loading context: $name"
    echo "===================="
    cat "$ctx_file"
    echo "===================="

    # Set as current session
    cp "$ctx_file" "$CURRENT_SESSION"
    echo "Context loaded. Use 'show_context' to reference in queries."
}

show_context() {
    if [ ! -f "$CURRENT_SESSION" ]; then
        echo "No active context. Use 'save_context <name>' to create one."
        return 1
    fi

    echo "Current session context:"
    echo "========================"
    cat "$CURRENT_SESSION"
    echo "========================"
}

clean_context() {
    local days="${1:-7}"
    echo "Cleaning contexts older than $days days..."
    find "$CONTEXT_DIR" -name "*.ctx" -type f -mtime +$days -delete
    echo "Cleanup complete."
}

list_contexts() {
    echo "Saved contexts:"
    if [ -d "$CONTEXT_DIR" ]; then
        for ctx in "$CONTEXT_DIR"/*.ctx; do
            if [ -f "$ctx" ]; then
                local name=$(basename "$ctx" .ctx)
                local date=$(grep "# Saved:" "$ctx" | cut -d: -f2- | xargs)
                echo "  $name ($date)"
            fi
        done
    else
        echo "  No contexts found"
    fi
}

# Context management commands
case "$1" in
    "save-ctx")
        if [ -z "$2" ]; then
            echo "Usage: $0 save-ctx <name>"
            exit 1
        fi
        save_context "$2"
        exit 0
        ;;
    "load-ctx")
        if [ -z "$2" ]; then
            load_context
            exit 1
        fi
        load_context "$2"
        exit 0
        ;;
    "show-ctx")
        show_context
        exit 0
        ;;
    "list-ctx")
        list_contexts
        exit 0
        ;;
    "clean-ctx")
        clean_context "$2"
        exit 0
        ;;
esac

# Enhanced queries with context integration
case "$1" in
    "schema-code")
        if [ -z "$2" ]; then
            echo "Usage: $0 schema-code 'endpoint description'"
            exit 1
        fi
        # Use database context efficiently with session context
        local context_info=""
        if [ -f "$CURRENT_SESSION" ]; then
            context_info="Session context: $(head -10 "$CURRENT_SESSION" | tr '\n' ' ')"
        fi
        claude "Based on my PostgreSQL schema, generate FastAPI endpoint: $2. $context_info Return implementation only."
        ;;
    "api-from-model")
        if [ -z "$2" ]; then
            echo "Usage: $0 api-from-model 'model name'"
            exit 1
        fi
        # Leverage existing code patterns
        claude "Find $2 model in my codebase. Generate CRUD endpoints following existing patterns. Code only."
        ;;
    "test-current")
        # Test for current work
        claude "Generate tests for my most recent code changes. Follow existing test patterns. Return test code only."
        ;;
    "deploy-check")
        # Quick deployment validation
        claude "Check if current changes are deployment-ready: migrations, configs, dependencies. Yes/No + critical issues only."
        ;;
    "pm-epic")
        if [ -z "$2" ]; then
            echo "Usage: $0 pm-epic 'epic name'"
            exit 1
        fi
        claude "Generate PM agent JSON for epic: $2

        Analyze my Threads-Agent Stack codebase and create a complete PM agent JSON structure:

        Requirements:
        - Use actual file paths from my project structure
        - Reference real dependencies from requirements.txt
        - Consider existing database schema and services
        - Include proper Helm/Kubernetes integration
        - Add appropriate test files and strategies
        - Use realistic story point estimates

        Epic focus: $2

        Return ONLY valid JSON in the exact format:
        {
          \"title\": \"Epic title with context\",
          \"context\": \"Detailed description with KPIs\",
          \"size_pref\": \"L\",
          \"priority\": 1,
          \"tasks\": [
            {
              \"title\": \"Task title\",
              \"body\": \"Implementation details\",
              \"estimate\": \"S|M|L\",
              \"labels\": [\"labels\"],
              \"files\": [\"actual/file/paths.py\"],
              \"libs\": [\"dependency>=version\"],
              \"acceptance\": \"Test criteria\"
            }
          ]
        }

        Generate 6-10 tasks covering full implementation."
        ;;
    "pm-analyze")
        claude "Analyze my current codebase structure for PM agent integration:

        1. List all service directories and main files
        2. Extract current dependencies from requirements.txt
        3. Identify database models and schemas
        4. Map Helm chart structure
        5. Note test patterns and frameworks

        Format output for use in PM agent JSON generation."
        ;;
    "infra-status")
        claude "Analyze my infrastructure status:
        1. k3d cluster: $(k3d cluster list)
        2. Pods: $(kubectl get pods)
        3. Services: $(kubectl get svc)
        4. Recent events: $(kubectl get events --sort-by='.lastTimestamp' | tail -10)

        Provide analysis and recommendations."
        ;;
    "helm-analyze")
        claude "Analyze my Helm configuration:
        1. Chart structure in chart/ directory
        2. Values files and their relationships
        3. Template validation
        4. Deployment readiness

        Suggest improvements and identify issues."
        ;;
    "infra-troubleshoot")
        if [ -z "$2" ]; then
            echo "Usage: $0 infra-troubleshoot 'issue description'"
            exit 1
        fi
        claude "Debug infrastructure issue: $2

        Current status:
        - Cluster: $(k3d cluster list)
        - Pods: $(kubectl get pods --no-headers)
        - Events: $(kubectl get events --sort-by='.lastTimestamp' | tail -5)

        Provide specific troubleshooting steps."
        ;;
    *)
        echo "Context Management:"
        echo "  save-ctx <name>        - Save current session context"
        echo "  load-ctx <name>        - Load saved context"
        echo "  show-ctx               - Show current session context"
        echo "  list-ctx               - List all saved contexts"
        echo "  clean-ctx [days]       - Clean contexts older than N days (default: 7)"
        echo ""
        echo "Smart Context Queries:"
        echo "  schema-code 'desc'     - Generate code using DB schema + context"
        echo "  api-from-model 'name'  - Create API from existing model"
        echo "  test-current           - Test recent changes"
        echo "  deploy-check           - Quick deployment check"
        echo "  pm-epic 'name'         - Generate PM agent JSON for epic"
        echo "  pm-analyze             - Analyze codebase for PM integration"
        echo "  infra-status           - Analyze infrastructure status"
        echo "  helm-analyze           - Analyze Helm configuration"
        echo "  infra-troubleshoot 'issue' - Debug infrastructure issues"
        ;;
esac
