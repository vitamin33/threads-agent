# /scripts/smart-queries.sh
#!/bin/bash

# Smart queries that leverage existing MCP context

case "$1" in
    "schema-code")
        if [ -z "$2" ]; then
            echo "Usage: $0 schema-code 'endpoint description'"
            exit 1
        fi
        # Use database context efficiently
        claude "Based on my PostgreSQL schema, generate FastAPI endpoint: $2. Return implementation only."
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
        echo "Smart context queries:"
        echo "  schema-code 'desc'     - Generate code using DB schema"
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
