#!/bin/bash
while true; do
    if command -v fswatch >/dev/null 2>&1; then
        # macOS
        fswatch -1 -r --include=".*\.(py|ts|js)$" . 2>/dev/null
    elif command -v inotifywait >/dev/null 2>&1; then
        # Linux
        inotifywait -e modify,create,delete -r . --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null
    else
        # Fallback: polling every 3 seconds
        sleep 3
    fi
    
    echo "🔄 Change detected, running quick checks..."
    
    # Super fast checks (< 10 seconds)
    if [[ -f .venv/bin/activate ]]; then
        source .venv/bin/activate
        python -c "import py_compile; [py_compile.compile(f, doraise=True) for f in __import__('glob').glob('*.py')]" 2>/dev/null || echo "❌ Python syntax error"
    fi
    
    if command -v ruff >/dev/null 2>&1; then
        ruff check . --quiet --fix 2>/dev/null || echo "⚠️ Lint issues"
    fi
    
    echo "✅ Feedback loop complete at $(date +%H:%M:%S)"
    sleep 2
done
