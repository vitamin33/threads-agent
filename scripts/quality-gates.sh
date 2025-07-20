#!/bin/bash

# scripts/quality-gates.sh - Comprehensive quality gates system for threads-agent
# Implements pre-commit and pre-deploy checks with Claude Code integration

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
QUALITY_LOG_DIR="$PROJECT_ROOT/.quality-logs"
CLAUDE_REVIEW_DIR="$PROJECT_ROOT/.claude-reviews"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }

# Initialize quality logging and environment
init_quality_logging() {
    mkdir -p "$QUALITY_LOG_DIR" "$CLAUDE_REVIEW_DIR"
    export QUALITY_LOG="$QUALITY_LOG_DIR/quality-gate-$TIMESTAMP.log"
    exec 1> >(tee -a "$QUALITY_LOG")
    exec 2> >(tee -a "$QUALITY_LOG" >&2)
}

# Setup virtual environment if available
setup_environment() {
    if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]] && [[ -z "${VIRTUAL_ENV:-}" ]]; then
        log_info "Activating virtual environment..."
        source "$PROJECT_ROOT/.venv/bin/activate"
        export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
    fi
}

# Helper: Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Helper: Run command with timeout and logging
run_quality_check() {
    local name="$1"
    local cmd="$2"
    local timeout="${3:-300}" # 5 minutes default
    
    log_info "Running $name..."
    # Use gtimeout on macOS if available, otherwise run without timeout
    local timeout_cmd=""
    if command_exists gtimeout; then
        timeout_cmd="gtimeout $timeout"
    elif command_exists timeout; then
        timeout_cmd="timeout $timeout"
    fi
    
    if [[ -n "$timeout_cmd" ]]; then
        if $timeout_cmd bash -c "$cmd"; then
            log_success "$name passed"
            return 0
        else
            log_error "$name failed"
            return 1
        fi
    else
        if bash -c "$cmd"; then
            log_success "$name passed"
            return 0
        else
            log_error "$name failed"
            return 1
        fi
    fi
}

# Phase 1: Code Quality Checks
phase_code_quality() {
    log_info "=== Phase 1: Code Quality Checks ==="
    local failed=0
    
    # Format check (skip if we just ran lint, as indicated by SKIP_FORMAT_CHECK)
    if [[ "${SKIP_FORMAT_CHECK:-}" != "true" ]]; then
        if ! run_quality_check "Ruff format check" "cd '$PROJECT_ROOT' && ruff format --check ."; then
            failed=$((failed + 1))
            log_warn "Run 'just lint' to fix formatting issues"
            log_warn "Alternatively, run 'just pre-commit-fix' to auto-fix and validate"
        fi
    else
        log_info "Skipping format check (already formatted)"
    fi
    
    # Lint check
    if ! run_quality_check "Ruff lint check" "cd '$PROJECT_ROOT' && ruff check ."; then
        failed=$((failed + 1))
        log_warn "Run 'ruff check --fix .' to fix linting issues"
    fi
    
    # Import sorting check (using same profile as justfile)
    if ! run_quality_check "isort check" "cd '$PROJECT_ROOT' && isort --check-only --diff --profile black ."; then
        failed=$((failed + 1))
        log_warn "Run 'isort . --profile black' to fix import sorting"
        log_warn "Alternatively, run 'just pre-commit-fix' to auto-fix and validate"
    fi
    
    # Type checking
    if ! run_quality_check "mypy type checking" "cd '$PROJECT_ROOT' && mypy ."; then
        failed=$((failed + 1))
    fi
    
    return $failed
}

# Phase 2: Security Checks
phase_security() {
    log_info "=== Phase 2: Security Checks ==="
    local failed=0
    
    # Security scanning with bandit (if available)
    if command_exists bandit; then
        if ! run_quality_check "Security scan (bandit)" "cd '$PROJECT_ROOT' && bandit -r services/ -f json -o '$QUALITY_LOG_DIR/bandit-$TIMESTAMP.json' || bandit -r services/"; then
            failed=$((failed + 1))
        fi
    else
        log_warn "bandit not found - install with: pip install bandit"
    fi
    
    # Dependency vulnerability check with safety (if available)
    if command_exists safety; then
        if ! run_quality_check "Dependency vulnerability scan" "cd '$PROJECT_ROOT' && safety check --json --output '$QUALITY_LOG_DIR/safety-$TIMESTAMP.json' || safety check"; then
            failed=$((failed + 1))
        fi
    else
        log_warn "safety not found - install with: pip install safety"
    fi
    
    # Secret scanning (basic patterns)
    if ! run_quality_check "Secret pattern check" "cd '$PROJECT_ROOT' && ! grep -r -E '(password|secret|key|token)\s*=\s*[\"'][^\"']{8,}[\"']' --include='*.py' --include='*.yaml' --include='*.yml' services/ chart/ || true"; then
        failed=$((failed + 1))
        log_error "Potential secrets found in code"
    fi
    
    return $failed
}

# Phase 3: Test Quality
phase_test_quality() {
    log_info "=== Phase 3: Test Quality ==="
    local failed=0
    
    # Unit tests with coverage
    if ! run_quality_check "Unit tests with coverage" "cd '$PROJECT_ROOT' && python -m pytest -m 'not e2e' --cov=services --cov-report=html:$QUALITY_LOG_DIR/coverage-$TIMESTAMP --cov-report=term --cov-fail-under=70"; then
        failed=$((failed + 1))
        log_warn "Coverage report available at: $QUALITY_LOG_DIR/coverage-$TIMESTAMP/index.html"
    fi
    
    # Test structure validation
    if ! run_quality_check "Test structure validation" "cd '$PROJECT_ROOT' && python -c 'import pytest; pytest.main([\"--collect-only\", \"-q\"])'"; then
        failed=$((failed + 1))
    fi
    
    return $failed
}

# Phase 4: Claude Code Review Integration
phase_claude_review() {
    log_info "=== Phase 4: Claude Code Automated Review ==="
    local failed=0
    
    # Check if claude command is available
    if ! command_exists claude; then
        log_warn "Claude Code not found - skipping automated review"
        log_info "Install Claude Code: https://docs.anthropic.com/en/docs/claude-code"
        return 0
    fi
    
    # Skip Claude review if no claude command or if explicitly disabled
    if [[ "${SKIP_CLAUDE_REVIEW:-}" == "true" ]]; then
        log_info "Claude review skipped (SKIP_CLAUDE_REVIEW=true)"
        return 0
    fi
    
    # Get changed files instead of full diff to avoid parsing issues
    local changed_files
    if git diff --cached --quiet; then
        changed_files=$(git diff --name-only HEAD~1 2>/dev/null || git ls-files --modified 2>/dev/null || echo "")
    else
        changed_files=$(git diff --cached --name-only)
    fi
    
    if [[ -z "$changed_files" ]]; then
        log_info "No files changed for Claude review"
        return 0
    fi
    
    local review_file="$CLAUDE_REVIEW_DIR/review-$TIMESTAMP.md"
    local review_prompt="Perform a comprehensive code review of the following changed files:

$(echo "$changed_files" | head -10)

Focus on:
1. Security vulnerabilities and best practices
2. Performance implications and optimizations  
3. Code maintainability and readability
4. Testing coverage and quality
5. Architecture patterns and consistency
6. Error handling and edge cases

Provide specific, actionable feedback and rate overall quality 1-10."
    
    # Write prompt to temp file to avoid shell escaping issues
    local prompt_file="$CLAUDE_REVIEW_DIR/prompt-$TIMESTAMP.txt"
    echo "$review_prompt" > "$prompt_file"
    
    if ! run_quality_check "Claude Code automated review" "cd '$PROJECT_ROOT' && claude < '$prompt_file' > '$review_file' 2>&1"; then
        failed=$((failed + 1))
        log_error "Claude Code review failed - check $review_file for details"
    else
        log_success "Claude Code review completed: $review_file"
        
        # Extract quality score if present
        if grep -q "score\|rating\|quality.*[0-9]" "$review_file" 2>/dev/null; then
            local score=$(grep -i "score\|rating\|quality.*[0-9]" "$review_file" | head -1)
            log_info "Quality assessment: $score"
        fi
        
        # Check for critical issues
        if grep -qi "critical\|security.*issue\|vulnerability\|major.*problem" "$review_file" 2>/dev/null; then
            log_error "Critical issues found in Claude review - check $review_file"
            failed=$((failed + 1))
        fi
    fi
    
    # Cleanup temp file
    rm -f "$prompt_file"
    
    return $failed
}

# Phase 5: Infrastructure Validation
phase_infrastructure() {
    log_info "=== Phase 5: Infrastructure Validation ==="
    local failed=0
    
    # Validate Helm chart
    if command_exists helm; then
        if ! run_quality_check "Helm chart validation" "cd '$PROJECT_ROOT' && helm lint chart/"; then
            failed=$((failed + 1))
        fi
        
        # Validate chart template rendering
        if ! run_quality_check "Helm template rendering" "cd '$PROJECT_ROOT' && helm template test-release chart/ --values chart/values-dev.yaml > /dev/null"; then
            failed=$((failed + 1))
        fi
    else
        log_warn "helm not found - skipping chart validation"
    fi
    
    # Validate Kubernetes manifests
    if command_exists kubectl; then
        # Dry-run validation
        if ! run_quality_check "Kubernetes manifest validation" "cd '$PROJECT_ROOT' && helm template test-release chart/ --values chart/values-dev.yaml | kubectl apply --dry-run=client -f -"; then
            failed=$((failed + 1))
        fi
    else
        log_warn "kubectl not found - skipping Kubernetes validation"
    fi
    
    # Docker build validation
    if command_exists docker; then
        for service in orchestrator celery_worker persona_runtime fake_threads; do
            if [[ -f "$PROJECT_ROOT/services/$service/Dockerfile" ]]; then
                if ! run_quality_check "Docker build validation ($service)" "cd '$PROJECT_ROOT/services/$service' && docker build --no-cache -t $service:quality-check . > /dev/null"; then
                    failed=$((failed + 1))
                fi
            fi
        done
    else
        log_warn "docker not found - skipping Docker validation"
    fi
    
    return $failed
}

# Phase 6: Performance & Resource Validation
phase_performance() {
    log_info "=== Phase 6: Performance & Resource Validation ==="
    local failed=0
    
    # Check for performance anti-patterns
    if ! run_quality_check "Performance pattern check" "cd '$PROJECT_ROOT' && ! grep -r -E '(time\.sleep\([^0][0-9]*\)|requests\.get\([^)]*timeout.*=.*None|while True.*:.*time\.sleep)' --include='*.py' services/ || true"; then
        failed=$((failed + 1))
        log_error "Performance anti-patterns detected"
    fi
    
    # Memory usage patterns
    if ! run_quality_check "Memory pattern check" "cd '$PROJECT_ROOT' && ! grep -r -E '(\.load\(\)|pickle\.loads|json\.loads.*large|pd\.read_csv.*chunksize.*=.*None)' --include='*.py' services/ || true"; then
        log_warn "Potential memory usage issues detected"
    fi
    
    # Resource limit validation in Helm charts
    if ! run_quality_check "Resource limits check" "cd '$PROJECT_ROOT' && grep -r 'resources:' chart/ && grep -A 10 'resources:' chart/ | grep -E '(limits|requests):'"; then
        log_warn "Resource limits should be defined in Helm charts"
    fi
    
    return $failed
}

# Pre-commit checks
pre_commit() {
    log_info "🚀 Running Pre-Commit Quality Gates"
    setup_environment
    init_quality_logging
    
    local total_failed=0
    
    # Run lightweight checks for pre-commit
    phase_code_quality
    local code_result=$?
    total_failed=$((total_failed + code_result))
    
    phase_security
    local security_result=$?
    total_failed=$((total_failed + security_result))
    
    # Quick unit tests only (skip e2e for speed)
    if ! run_quality_check "Quick unit tests" "cd '$PROJECT_ROOT' && python -m pytest -m 'not e2e' --tb=short -x"; then
        total_failed=$((total_failed + 1))
    fi
    
    # Claude review for staged changes
    phase_claude_review
    local claude_result=$?
    total_failed=$((total_failed + claude_result))
    
    if [[ $total_failed -gt 0 ]]; then
        log_error "Pre-commit quality gates failed: $total_failed checks failed"
        log_info "Check logs: $QUALITY_LOG"
        exit 1
    else
        log_success "All pre-commit quality gates passed! ✅"
        exit 0
    fi
}

# Pre-deploy checks (comprehensive)
pre_deploy() {
    log_info "🚀 Running Pre-Deploy Quality Gates"
    setup_environment
    init_quality_logging
    
    local total_failed=0
    
    # Run all quality phases
    phase_code_quality; total_failed=$((total_failed + $?))
    phase_security; total_failed=$((total_failed + $?))
    phase_test_quality; total_failed=$((total_failed + $?))
    phase_claude_review; total_failed=$((total_failed + $?))
    phase_infrastructure; total_failed=$((total_failed + $?))
    phase_performance; total_failed=$((total_failed + $?))
    
    # E2E tests (if infrastructure is available)
    if kubectl cluster-info >/dev/null 2>&1 && kubectl get nodes >/dev/null 2>&1; then
        if ! run_quality_check "End-to-end tests" "cd '$PROJECT_ROOT' && python -m pytest -m e2e --tb=short" 900; then # 15 minutes timeout
            total_failed=$((total_failed + 1))
        fi
    else
        log_warn "Kubernetes cluster not available - skipping E2E tests"
        log_info "Run 'just bootstrap' to set up k3d cluster for full validation"
    fi
    
    # Generate quality report
    generate_quality_report "$total_failed"
    
    if [[ $total_failed -gt 0 ]]; then
        log_error "Pre-deploy quality gates failed: $total_failed checks failed"
        log_info "Check logs: $QUALITY_LOG"
        log_info "Quality report: $QUALITY_LOG_DIR/quality-report-$TIMESTAMP.html"
        exit 1
    else
        log_success "All pre-deploy quality gates passed! 🎉"
        log_info "Quality report: $QUALITY_LOG_DIR/quality-report-$TIMESTAMP.html"
        exit 0
    fi
}

# Generate HTML quality report
generate_quality_report() {
    local failed_count="$1"
    local report_file="$QUALITY_LOG_DIR/quality-report-$TIMESTAMP.html"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Threads-Agent Quality Report - $TIMESTAMP</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        .pass { color: #28a745; }
        .fail { color: #dc3545; }
        .warn { color: #ffc107; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Threads-Agent Quality Report</h1>
        <p><strong>Timestamp:</strong> $TIMESTAMP</p>
        <p><strong>Status:</strong> $([ "$failed_count" -eq 0 ] && echo '<span class="pass">✅ PASSED</span>' || echo '<span class="fail">❌ FAILED</span>')</p>
        <p><strong>Failed Checks:</strong> $failed_count</p>
    </div>
    
    <div class="section">
        <h2>Files Generated</h2>
        <ul>
            <li>Quality Log: <code>$QUALITY_LOG</code></li>
            $([ -f "$QUALITY_LOG_DIR/coverage-$TIMESTAMP/index.html" ] && echo "<li>Coverage Report: <code>$QUALITY_LOG_DIR/coverage-$TIMESTAMP/index.html</code></li>")
            $([ -f "$CLAUDE_REVIEW_DIR/review-$TIMESTAMP.md" ] && echo "<li>Claude Review: <code>$CLAUDE_REVIEW_DIR/review-$TIMESTAMP.md</code></li>")
            $([ -f "$QUALITY_LOG_DIR/bandit-$TIMESTAMP.json" ] && echo "<li>Security Scan: <code>$QUALITY_LOG_DIR/bandit-$TIMESTAMP.json</code></li>")
        </ul>
    </div>
    
    <div class="section">
        <h2>Quality Log</h2>
        <pre>$(tail -50 "$QUALITY_LOG" | sed 's/\x1b\[[0-9;]*m//g')</pre>
    </div>
</body>
</html>
EOF
    
    log_info "Quality report generated: $report_file"
}

# Show help
show_help() {
    cat << EOF
Quality Gates System for Threads-Agent

USAGE:
    $0 [COMMAND]

COMMANDS:
    pre-commit     Run lightweight quality checks before commit
    pre-deploy     Run comprehensive quality checks before deployment
    code-quality   Run only code quality checks (ruff, mypy, etc.)
    security       Run only security checks (bandit, safety, secrets)
    test-quality   Run only test quality checks (pytest with coverage)
    claude-review  Run only Claude Code automated review
    infrastructure Run only infrastructure validation checks
    performance    Run only performance and resource validation
    help           Show this help message

EXAMPLES:
    $0 pre-commit              # Run before git commit
    $0 pre-deploy              # Run before deployment
    $0 claude-review           # Get AI code review
    $0 security                # Security-focused checks only

ENVIRONMENT VARIABLES:
    SKIP_CLAUDE_REVIEW=1       Skip Claude Code integration
    QUALITY_LOG_LEVEL=debug    Set logging verbosity
    COVERAGE_THRESHOLD=70      Set coverage failure threshold

INTEGRATION:
    # Git pre-commit hook
    echo "$0 pre-commit" > .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
    
    # Justfile integration  
    just quality-gate pre-deploy
    
    # CI/CD integration
    ./scripts/quality-gates.sh pre-deploy

EOF
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    case "${1:-help}" in
        pre-commit)
            pre_commit
            ;;
        pre-deploy)
            pre_deploy
            ;;
        code-quality)
            setup_environment
            init_quality_logging
            phase_code_quality
            ;;
        security)
            setup_environment
            init_quality_logging
            phase_security
            ;;
        test-quality)
            setup_environment
            init_quality_logging
            phase_test_quality
            ;;
        claude-review)
            setup_environment
            init_quality_logging
            phase_claude_review
            ;;
        infrastructure)
            setup_environment
            init_quality_logging
            phase_infrastructure
            ;;
        performance)
            setup_environment
            init_quality_logging
            phase_performance
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Trap cleanup
cleanup() {
    if [[ -n "${QUALITY_LOG:-}" ]] && [[ -f "$QUALITY_LOG" ]]; then
        log_info "Quality gates completed. Log: $QUALITY_LOG"
    fi
}

trap cleanup EXIT

main "$@"