#!/bin/bash

# Smart TDD Integration for AI Development
# Based on top AI companies' practices for solo developers

set -e

AGENT_ID=${AGENT_ID:-"main-dev"}
ACTION=${1:-"help"}

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${BLUE}[TDD]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

# AI-assisted test-first development
test_first() {
    local feature="$1"
    log "🧪 Starting TDD for: $feature"
    
    # Generate AI prompt for test-first development
    cat > .tdd-prompt.txt << EOF
Context: Agent $AGENT_ID working on threads-agent
Feature: $feature
Current files: $(find . -name "*.py" | grep -v .venv | head -5 | tr '\n' ' ')
Recent work: $(git log --oneline -2)

Generate TDD implementation:
1. Write failing test that describes the expected behavior
2. Minimal implementation to make test pass
3. Refactor for clean code

Focus on:
- Business logic and AI components (skip simple CRUD)
- Integration points and API contracts
- Performance-critical paths
- Error handling and edge cases

Follow existing test patterns in codebase.
EOF
    
    success "📝 TDD prompt generated: .tdd-prompt.txt"
    log "💡 Use this with Claude Code for AI-assisted TDD"
}

# Continuous testing with smart filtering
test_watch() {
    log "👀 Starting smart test watcher..."
    
    # Create test watcher script
    cat > .test-watch.sh << 'EOF'
#!/bin/bash
while true; do
    if command -v fswatch >/dev/null 2>&1; then
        # macOS - watch Python files only
        fswatch -1 -r --include=".*\.py$" . 2>/dev/null
    else
        # Fallback: polling every 2 seconds
        sleep 2
    fi
    
    echo "🔄 Python change detected, running smart tests..."
    
    # Get changed files from git
    CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null | grep "\.py$" || echo "")
    
    if [[ -n "$CHANGED_FILES" ]]; then
        # Run tests for changed modules only
        for file in $CHANGED_FILES; do
            # Convert file path to test path
            TEST_FILE="tests/$(dirname "$file")/test_$(basename "$file")"
            if [[ -f "$TEST_FILE" ]]; then
                echo "🎯 Testing: $TEST_FILE"
                python -m pytest "$TEST_FILE" -v --tb=short || echo "❌ Test failed"
            fi
        done
    else
        # Run quick smoke tests
        python -m pytest tests/ -x --tb=no -q | head -10
    fi
    
    echo "✅ Smart test cycle complete at $(date +%H:%M:%S)"
    sleep 1
done
EOF
    chmod +x .test-watch.sh
    
    log "🔍 Starting test watcher (Ctrl+C to stop)..."
    ./.test-watch.sh &
    echo $! > .test-watch-pid
    success "👀 Test watcher active - will run tests on Python file changes"
}

# AI-powered test generation
test_generate() {
    local target="$1"
    log "🤖 Generating comprehensive tests for: $target"
    
    # Analyze target file/class
    if [[ -f "$target" ]]; then
        local functions=$(grep -n "def " "$target" | head -10)
        local classes=$(grep -n "class " "$target" | head -5)
    fi
    
    cat > .test-gen-prompt.txt << EOF
Context: Agent $AGENT_ID, threads-agent project
Target: $target
Functions found: $functions
Classes found: $classes

Generate comprehensive pytest test suite:
1. Unit tests for all public methods
2. Integration tests for API endpoints
3. Edge cases and error conditions
4. Performance tests for critical paths
5. Mock external dependencies (OpenAI, databases)

Test categories to include:
- Happy path scenarios
- Error handling and exceptions
- Boundary conditions and edge cases
- Performance and timeout scenarios
- Security and input validation

Follow pytest conventions and existing test patterns.
EOF
    
    success "📝 Test generation prompt: .test-gen-prompt.txt"
    log "💡 Use with Claude Code to generate comprehensive test suite"
}

# Stop test watcher
stop_watch() {
    if [[ -f ".test-watch-pid" ]]; then
        kill $(cat .test-watch-pid) 2>/dev/null || true
        rm .test-watch-pid
        success "🛑 Test watcher stopped"
    else
        log "No test watcher running"
    fi
}

# Quick TDD cycle
quick_cycle() {
    local feature="$1"
    log "⚡ Quick TDD cycle for: $feature"
    
    # 1. Generate test prompt
    test_first "$feature"
    
    # 2. Wait for implementation  
    log "📋 Steps:"
    log "  1. Use .tdd-prompt.txt with Claude Code"
    log "  2. Implement the failing test"
    log "  3. Run: python -m pytest <test_file> -v"
    log "  4. Implement minimal code to pass"
    log "  5. Refactor and commit with: just save"
    
    success "🧪 TDD cycle ready - implement with AI assistance"
}

# Main command handler
case "$ACTION" in
    "first")
        test_first "$2"
        ;;
    "watch")
        test_watch
        ;;
    "generate")
        test_generate "$2"
        ;;
    "stop")
        stop_watch
        ;;
    "cycle")
        quick_cycle "$2"
        ;;
    "help")
        cat << EOF
🧪 Smart TDD System (AI Company Practices)

Usage: $0 <command>

Commands:
  first <feature>    Generate AI prompt for test-first development
  watch             Start smart test watcher (runs tests on changes)
  generate <target>  Generate comprehensive test suite with AI
  stop              Stop test watcher
  cycle <feature>   Complete TDD cycle with AI assistance

Examples:
  $0 first "user authentication"     # Start TDD for auth feature
  $0 watch                          # Continuous testing
  $0 generate "services/auth.py"    # Generate test suite
  $0 cycle "payment processing"     # Full TDD workflow

Integration:
  - Use with Claude Code for AI-assisted test writing
  - Integrates with learning system for pattern tracking
  - Follows 80/20 rule: TDD for critical logic only
  - Optimized for solo developer efficiency

EOF
        ;;
    *)
        log "Unknown command: $ACTION. Use 'help' for usage."
        exit 1
        ;;
esac