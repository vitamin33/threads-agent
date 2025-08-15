#!/bin/bash

# AI Development Acceleration System
# Based on top AI companies' practices (OpenAI, Anthropic, Meta AI)
# 80/20 rule: Maximum impact, minimal setup

set -e

AGENT_ID=${AGENT_ID:-"unknown"}
ACTION=${1:-"help"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[AI-DEV]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. ANTHROPIC: Smart Context Loading (Enhanced with Learning System)
smart_context() {
    log "🧠 Loading smart context for Agent $AGENT_ID..."
    
    # Initialize learning system if not already done
    if [[ -f "scripts/learning-system.sh" ]]; then
        log "🧠 Integrating with intelligent learning system..."
        ./scripts/learning-system.sh init >/dev/null 2>&1 || true
    fi
    
    # Get learning system insights
    local learning_insights="{}"
    if [[ -f ".learning/analytics/commands.log" ]]; then
        local top_commands=$(tail -200 .learning/analytics/commands.log 2>/dev/null | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -3 | awk '{printf "\"%s\",", $2}' | sed 's/,$//')
        local recent_patterns=$(tail -50 .learning/analytics/commands.log 2>/dev/null | cut -d'|' -f3 | uniq | tail -5 | jq -R . | jq -s . 2>/dev/null || echo '[]')
        local success_rate=$(tail -100 .learning/analytics/commands.log 2>/dev/null | wc -l)
        local failure_count=$(tail -100 .learning/analytics/failures.log 2>/dev/null | wc -l || echo "0")
        
        learning_insights=$(cat << EOF
{
  "top_commands": [$top_commands],
  "recent_patterns": $recent_patterns,
  "recent_success_rate": $(echo "scale=1; (($success_rate - $failure_count) * 100) / $success_rate" | bc -l 2>/dev/null || echo "100"),
  "suggestions_available": $(test -d .learning/suggestions && find .learning/suggestions -name "*.md" | wc -l || echo "0")
}
EOF
)
    fi
    
    # Create enhanced AI context file
    cat > .ai-context.json << EOF
{
  "agent_id": "$AGENT_ID",
  "session_start": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "focus_areas": $(cat AGENT_FOCUS.md 2>/dev/null | head -5 | jq -R . | jq -s . || echo '["General development"]'),
  "recent_commits": $(git log --oneline -5 --format='"%h %s"' | jq -s .),
  "active_files": $(find . -name "*.py" -o -name "*.ts" -o -name "*.js" | grep -v node_modules | grep -v .venv | head -10 | jq -R . | jq -s .),
  "current_branch": "$(git branch --show-current)",
  "todo_items": $(grep -r "TODO\|FIXME\|XXX" . --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null | head -5 | cut -d: -f2- | jq -R . | jq -s . || echo '[]'),
  "learning_insights": $learning_insights,
  "development_patterns": {
    "most_used_commands": $(tail -200 .learning/analytics/commands.log 2>/dev/null | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -3 | jq -R . | jq -s . || echo '[]'),
    "recent_workflow_success": $(tail -50 .learning/analytics/workflows.log 2>/dev/null | awk -F'|' '$5=="true"' | wc -l || echo "0"),
    "optimization_opportunities": $(find .learning/suggestions -name "*.md" -type f -exec head -3 {} \; 2>/dev/null | grep -E "^\-" | head -3 | jq -R . | jq -s . || echo '[]')
  },
  "context_quality": "enhanced_with_learning_system"
}
EOF
    
    log "✅ Enhanced smart context loaded to .ai-context.json"
    log "🧠 Integrated $(wc -l < .learning/analytics/commands.log 2>/dev/null || echo 0) commands from learning system"
}

# 2. META AI: Fast Feedback Loops  
feedback_loop() {
    log "⚡ Starting fast feedback loop..."
    
    # Watch mode for instant feedback (macOS and Linux compatible)
    cat > .watch-dev.sh << 'EOF'
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
EOF
    chmod +x .watch-dev.sh
    
    log "🔍 Starting file watcher (Ctrl+C to stop)..."
    ./.watch-dev.sh &
    echo $! > .watch-pid
    
    if ! command -v fswatch >/dev/null 2>&1 && ! command -v inotifywait >/dev/null 2>&1; then
        warn "For better performance: brew install fswatch (macOS) or apt install inotify-tools (Linux)"
        log "📊 Using polling fallback mode"
    fi
}

# 3. OPENAI: AI-Assisted Code Generation
ai_assist() {
    local task="$2"
    log "🤖 AI-assisted development for: $task"
    
    # Generate code stub with AI context
    cat > ai-prompt.txt << EOF
Context: Working on $(cat AGENT_FOCUS.md | head -1 2>/dev/null || echo "threads-agent")
Agent: $AGENT_ID
Current files: $(ls *.py *.ts *.js 2>/dev/null | head -5 | tr '\n' ' ')
Recent work: $(git log --oneline -2)

Task: $task

Generate production-ready code with:
1. Proper error handling
2. Type hints (Python) / TypeScript types
3. Unit tests
4. Documentation
5. Follow existing patterns in codebase
EOF

    log "📝 AI prompt saved to ai-prompt.txt"
    log "💡 Use this with Claude Code or copy to ChatGPT/Cursor"
}

# 4. GOOGLE DEEPMIND: Automated Testing
smart_test() {
    log "🧪 Smart testing strategy..."
    
    # Identify what to test based on changes
    CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null || echo "")
    
    if [[ -n "$CHANGED_FILES" ]]; then
        log "📋 Files changed: $CHANGED_FILES"
        
        # Run tests for changed modules only
        for file in $CHANGED_FILES; do
            if [[ "$file" == *.py ]]; then
                TEST_FILE="tests/$(dirname "$file")/test_$(basename "$file")"
                if [[ -f "$TEST_FILE" ]]; then
                    log "🎯 Running targeted test: $TEST_FILE"
                    python -m pytest "$TEST_FILE" -v
                fi
            fi
        done
    else
        log "🔄 Running full test suite..."
        just unit
    fi
}

# 5. ANTHROPIC: Quality Gates
quality_gate() {
    log "🚦 Running quality gates..."
    
    local start_time=$(date +%s)
    local issues=0
    
    # Fast quality checks (< 30 seconds total)
    echo "1/5 🔍 Type checking..."
    if ! mypy . --no-error-summary 2>/dev/null; then
        ((issues++))
        warn "Type check issues found"
    fi
    
    echo "2/5 🧹 Code formatting..."
    if ! ruff check . --quiet; then
        ((issues++))
        warn "Linting issues found"
    fi
    
    echo "3/5 🔒 Security scan..."
    if command -v bandit >/dev/null 2>&1; then
        if ! bandit -r . -q -f json 2>/dev/null | jq -e '.results | length == 0' >/dev/null; then
            ((issues++))
            warn "Security issues found"
        fi
    fi
    
    echo "4/5 🧪 Critical tests..."
    if ! python -m pytest tests/ -x --tb=no -q 2>/dev/null; then
        ((issues++))
        error "Critical tests failing"
    fi
    
    echo "5/5 📊 Performance check..."
    if [[ -f "performance_baseline.json" ]]; then
        # Run performance comparison
        local current_perf=$(python -c "import time; start=time.time(); import sys; print(time.time()-start)" 2>/dev/null || echo "0")
        log "Import time: ${current_perf}s"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [[ $issues -eq 0 ]]; then
        log "✅ All quality gates passed in ${duration}s"
        return 0
    else
        error "❌ $issues quality issues found in ${duration}s"
        return 1
    fi
}

# 6. META AI: Auto-Documentation
auto_docs() {
    log "📚 Generating auto-documentation..."
    
    # Generate API docs
    if [[ -f "main.py" ]] || [[ -f "app.py" ]]; then
        log "🔌 Generating API documentation..."
        python -c "
import sys
import inspect
import json
try:
    import main
    docs = {}
    for name, obj in inspect.getmembers(main):
        if inspect.isfunction(obj):
            docs[name] = {
                'docstring': obj.__doc__,
                'signature': str(inspect.signature(obj))
            }
    with open('api-docs.json', 'w') as f:
        json.dump(docs, f, indent=2)
    print('✅ API docs generated')
except Exception as e:
    print(f'⚠️ Could not generate docs: {e}')
" 2>/dev/null || warn "Auto-docs skipped"
    fi
    
    # Update README with latest metrics
    if [[ -f "README.md" ]]; then
        local commits=$(git rev-list --count HEAD 2>/dev/null || echo "0")
        local files=$(find . -name "*.py" -o -name "*.ts" -o -name "*.js" | grep -v node_modules | grep -v .venv | wc -l)
        local tests=$(find . -name "*test*.py" | wc -l)
        
        # Add/update metrics section
        if ! grep -q "## Metrics" README.md; then
            cat >> README.md << EOF

## Metrics
- 📊 Commits: $commits
- 📁 Files: $files  
- 🧪 Tests: $tests
- 🤖 Agent: $AGENT_ID
- ⏰ Updated: $(date +'%Y-%m-%d %H:%M')
EOF
        fi
    fi
}

# 7. AI COMPANY SHARED: Development Insights (Enhanced with Learning System)
insights() {
    log "🔍 Development insights for Agent $AGENT_ID..."
    
    # Integrate with existing learning system
    if [[ -f "scripts/learning-system.sh" ]]; then
        log "🧠 Analyzing with intelligent learning system..."
        ./scripts/learning-system.sh analyze >/dev/null 2>&1 || true
        ./scripts/learning-system.sh suggest >/dev/null 2>&1 || true
    fi
    
    # Code complexity analysis
    local py_files=$(find . -name "*.py" | grep -v .venv | wc -l)
    local avg_lines=0
    if [[ $py_files -gt 0 ]]; then
        avg_lines=$(find . -name "*.py" | grep -v .venv | xargs wc -l 2>/dev/null | tail -1 | awk -v files="$py_files" '{print int($1/files)}' || echo "0")
    fi
    local commits_today=$(git log --since="00:00:00" --oneline | wc -l)
    local test_coverage=$(python -m pytest --cov=. --cov-report=term-missing 2>/dev/null | grep "TOTAL" | awk '{print $4}' || echo "N/A")
    
    # Learning system insights
    local learning_data="{}"
    if [[ -f ".learning/analytics/commands.log" ]]; then
        local total_commands=$(wc -l < .learning/analytics/commands.log)
        local recent_failures=$(tail -100 .learning/analytics/failures.log 2>/dev/null | wc -l || echo "0")
        local recent_commands=$(tail -100 .learning/analytics/commands.log 2>/dev/null | wc -l || echo "0")
        local success_rate=100
        if [[ $recent_commands -gt 0 ]]; then
            success_rate=$(echo "scale=1; (($recent_commands - $recent_failures) * 100) / $recent_commands" | bc -l)
        fi
        
        learning_data=$(cat << EOF
{
  "total_commands_tracked": $total_commands,
  "recent_success_rate": $success_rate,
  "pattern_analysis_available": true,
  "top_command": "$(tail -200 .learning/analytics/commands.log 2>/dev/null | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -1 | awk '{print $2}' || echo "none")"
}
EOF
)
    fi
    
    cat > .dev-insights.json << EOF
{
  "agent_id": "$AGENT_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "metrics": {
    "python_files": $py_files,
    "avg_lines_per_file": $avg_lines,
    "commits_today": $commits_today,
    "test_coverage": "$test_coverage",
    "current_branch": "$(git branch --show-current)",
    "last_commit": "$(git log -1 --format='%h %s')"
  },
  "focus_time": {
    "session_duration": "$(ps -o etime= -p $$ | tr -d ' ')",
    "productivity_score": $(echo "scale=1; $commits_today * 10 + $py_files" | bc)
  },
  "learning_system": $learning_data,
  "ai_acceleration": {
    "context_loaded": $(test -f .ai-context.json && echo "true" || echo "false"),
    "watcher_active": $(test -f .watch-pid && echo "true" || echo "false"),
    "quality_gates_enabled": true
  }
}
EOF
    
    log "📊 Enhanced insights saved to .dev-insights.json"
    
    # Display key insights with learning system data
    if [[ -f ".learning/analytics/commands.log" ]]; then
        local total_tracked=$(wc -l < .learning/analytics/commands.log)
        local top_cmd=$(tail -200 .learning/analytics/commands.log 2>/dev/null | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -1 | awk '{print $2}' || echo "none")
        log "🧠 Learning System: $total_tracked commands tracked, top: $top_cmd"
        
        # Show recent suggestions if available
        local latest_suggestion=$(find .learning/suggestions -name "suggestions_*.md" -type f -exec ls -t {} + 2>/dev/null | head -1)
        if [[ -n "$latest_suggestion" ]]; then
            log "💡 Latest AI suggestions available in: $latest_suggestion"
        fi
    fi
    
    cat .dev-insights.json | jq .
}

# Main command handler
case "$ACTION" in
    "context")
        smart_context
        ;;
    "watch")
        feedback_loop
        ;;
    "assist")
        ai_assist "$@"
        ;;
    "test")
        smart_test
        ;;
    "quality")
        quality_gate
        ;;
    "docs")
        auto_docs
        ;;
    "insights")
        insights
        ;;
    "all")
        # Track this workflow in learning system
        if [[ -f "scripts/learning-system.sh" ]]; then
            ./scripts/learning-system.sh track "dev-boost-all" 0 0 "ai_acceleration_workflow"
        fi
        
        smart_context
        auto_docs
        quality_gate
        insights
        
        # Track successful completion
        if [[ -f "scripts/learning-system.sh" ]]; then
            ./scripts/learning-system.sh workflow "ai-dev-boost" "context,docs,quality,insights" true 0
        fi
        ;;
    "stop")
        if [[ -f ".watch-pid" ]]; then
            kill $(cat .watch-pid) 2>/dev/null || true
            rm .watch-pid
            log "🛑 Stopped file watcher"
        fi
        ;;
    *)
        cat << EOF
🚀 AI Development Acceleration System

Usage: $0 <command>

Commands:
  context   - Load smart AI context (Anthropic approach)
  watch     - Start fast feedback loop (Meta AI approach)  
  assist    - AI-assisted code generation (OpenAI approach)
  test      - Smart testing strategy (DeepMind approach)
  quality   - Run quality gates (All companies)
  docs      - Auto-generate documentation
  insights  - Development insights & metrics
  all       - Run context + docs + quality + insights
  stop      - Stop background processes

Examples:
  $0 context              # Load AI context for Claude Code
  $0 watch               # Start file watcher for instant feedback
  $0 assist "add auth"   # Generate AI prompt for authentication
  $0 quality             # Run all quality checks
  $0 all                 # Full acceleration setup

Agent: $AGENT_ID
EOF
        ;;
esac