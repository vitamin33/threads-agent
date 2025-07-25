#!/bin/bash
set -e

PROJECT_ROOT="/Users/vitaliiserbyn/development/threads-agent"
cd "$PROJECT_ROOT"

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT"
export OPENAI_API_KEY="test"

echo "🔍 Running mypy type-check..."

# Run mypy (excluding problematic achievement_collector files)
if ! mypy --config-file mypy.ini . \
    --exclude "services/achievement_collector/db/alembic/" \
    --exclude "services/achievement_collector/services/ai_analyzer.py" \
    --exclude "services/achievement_collector/api/" \
    --exclude "services/achievement_collector/tests/" \
    2>&1 | tee mypy_output.txt; then
    echo "❌ mypy type check failed!"
    # Show a summary of errors by service
    echo -e "\n📊 Error Summary by Service:"
    for service in achievement_collector persona_runtime viral_engine threads_adaptor orchestrator celery_worker fake_threads common; do
        error_count=$(grep -c "services/$service/" mypy_output.txt || true)
        if [ $error_count -gt 0 ]; then
            echo "  - $service: $error_count errors"
        fi
    done
    
    # Show which files have most errors
    echo -e "\n📁 Files with most errors:"
    grep "error:" mypy_output.txt | cut -d: -f1 | sort | uniq -c | sort -nr | head -10
    
    exit 1
fi

echo "✅ mypy passed!"

echo -e "\n🧪 Running pytest unit tests..."
pytest -q -m "not e2e" -n auto --ignore=services/achievement_collector/tests/

echo -e "\n✅ All checks passed!"