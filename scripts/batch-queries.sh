# scripts/batch-queries.sh
#!/bin/bash

# Combine multiple queries to save tokens

case "$1" in
    "sprint-prep")
        # Batch multiple planning queries
        claude "Sprint preparation batch:
        1. Current Linear project status (1 sentence)
        2. Next 3 specific tasks to implement
        3. Critical blockers or dependencies
        4. Database migrations needed (if any)
        Return concise bullet points only."
        ;;
    "deploy-prep")
        # Batch deployment queries
        claude "Deployment readiness batch:
        1. Code review summary (issues only)
        2. Database migration validation
        3. Configuration changes needed
        4. Testing gaps
        Return action items only."
        ;;
    "debug-batch")
        if [ -z "$2" ]; then
            echo "Usage: $0 debug-batch 'issue description'"
            exit 1
        fi
        # Batch debugging queries
        claude "Debug batch for: $2
        1. Check relevant logs for errors
        2. Validate database state
        3. Review recent code changes
        4. Provide specific fix
        Return diagnosis + solution only."
        ;;
    *)
        echo "Batch query options:"
        echo "  sprint-prep     - Sprint planning batch"
        echo "  deploy-prep     - Deployment readiness batch"
        echo "  debug-batch     - Comprehensive debugging"
        ;;
esac
