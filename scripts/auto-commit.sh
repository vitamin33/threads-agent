#!/bin/bash
# Auto-commit script for working states after successful tests

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AUTO_COMMIT_PREFIX="[auto-commit]"
BRANCH=$(git branch --show-current)

echo "🚀 Auto-Commit System Starting..."

# Function to check if there are uncommitted changes
has_changes() {
    ! git diff --quiet || ! git diff --cached --quiet
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    
    # Try different test commands based on what's available
    if [[ -f "justfile" ]] && command -v just &> /dev/null; then
        echo "Using justfile..."
        if just check; then
            return 0
        else
            return 1
        fi
    elif [[ -f "Makefile" ]] && grep -q "test:" Makefile; then
        echo "Using Makefile..."
        make test
    elif [[ -f "requirements.txt" ]]; then
        echo "Running Python tests..."
        python -m pytest -q -m "not e2e" || return 1
    else
        echo -e "${YELLOW}⚠️  No test runner found, skipping tests${NC}"
        return 0
    fi
}

# Function to create auto-commit
create_auto_commit() {
    local test_status=$1
    local commit_msg=""
    
    if [[ $test_status -eq 0 ]]; then
        commit_msg="$AUTO_COMMIT_PREFIX ✅ Working state - all tests passing"
    else
        commit_msg="$AUTO_COMMIT_PREFIX ⚠️  Work in progress - tests failing"
    fi
    
    # Add a timestamp and branch info
    commit_msg="$commit_msg

Branch: $BRANCH
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Test Status: $([ $test_status -eq 0 ] && echo "PASSED" || echo "FAILED")"
    
    # Stage all changes
    git add -A
    
    # Create commit
    git commit -m "$commit_msg" || {
        echo -e "${RED}❌ Failed to create commit${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ Auto-commit created successfully${NC}"
    return 0
}

# Main logic
main() {
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}❌ Not in a git repository${NC}"
        exit 1
    fi
    
    # Check if there are changes to commit
    if ! has_changes; then
        echo -e "${YELLOW}ℹ️  No changes to commit${NC}"
        exit 0
    fi
    
    # Show what will be committed
    echo "📝 Changes to be committed:"
    git status --short
    echo ""
    
    # Run tests and capture result
    test_status=0
    run_tests || test_status=$?
    
    # Create auto-commit based on test results
    create_auto_commit $test_status
    
    # Optional: push to remote if tests passed and on feature branch
    if [[ $test_status -eq 0 ]] && [[ "$BRANCH" != "main" ]] && [[ "$1" == "--push" ]]; then
        echo "📤 Pushing to remote..."
        git push origin "$BRANCH" || echo -e "${YELLOW}⚠️  Push failed, commit saved locally${NC}"
    fi
}

# Run main function
main "$@"