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
    *)
        echo "Smart context queries:"
        echo "  schema-code 'desc'     - Generate code using DB schema"
        echo "  api-from-model 'name'  - Create API from existing model"
        echo "  test-current           - Test recent changes"
        echo "  deploy-check           - Quick deployment check"
        ;;
esac
