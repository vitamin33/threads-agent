#!/bin/bash
# quick-ci-check.sh - Quick local validation before pushing
set -e

echo "⚡ QUICK CI VALIDATION"
echo "====================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_step() { echo -e "\n${BLUE}🔹 $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# 1. Check if changes would trigger full CI
log_step "Detecting changes that would trigger CI"
CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null || echo "all")
E2E_REQUIRED=false

if echo "$CHANGED_FILES" | grep -qE "(chart/|Dockerfile|scripts/)" || [ "$CHANGED_FILES" = "all" ]; then
    E2E_REQUIRED=true
    log_warning "Infrastructure changes detected - CI will run full e2e tests (~12 minutes)"
    echo "Changed files that trigger e2e:"
    echo "$CHANGED_FILES" | grep -E "(chart/|Dockerfile|scripts/)" || echo "Multiple files"
else
    log_success "Only code changes detected - CI will skip expensive operations (~2 minutes)"
fi

# 2. Validate Helm chart syntax
log_step "Validating Helm chart syntax"
helm lint ./chart >/dev/null 2>&1 || {
    log_warning "Helm chart has lint issues - CI may fail during template rendering"
    helm lint ./chart
}

# 3. Test Helm template rendering
log_step "Testing Helm template rendering"
helm template ./chart -f chart/values-ci-fast.yaml --dry-run >/tmp/helm-test.yaml 2>&1 || {
    log_warning "Helm template rendering failed - CI will fail at deployment step"
    echo "Error:"
    cat /tmp/helm-test.yaml
    exit 1
}
log_success "Helm template renders successfully"

# 4. Check for Docker images availability
log_step "Checking Docker images"
SERVICES="orchestrator celery_worker persona_runtime fake_threads"
MISSING_IMAGES=0

for svc in $SERVICES; do
    LOCAL_NAME="${svc//_/-}:local"
    if docker image inspect $LOCAL_NAME >/dev/null 2>&1; then
        echo "  ✅ $LOCAL_NAME - available locally"
    else
        echo "  ❌ $LOCAL_NAME - missing (will build in CI)"
        MISSING_IMAGES=$((MISSING_IMAGES + 1))
    fi
done

if [ $MISSING_IMAGES -gt 0 ]; then
    log_warning "$MISSING_IMAGES images missing - CI will build them (adds ~5 minutes)"
else
    log_success "All images available locally"
fi

# 5. Quick Python syntax check
log_step "Quick Python syntax validation"
find services -name "*.py" -exec python3 -m py_compile {} \; 2>/dev/null || {
    log_warning "Python syntax errors found - CI will fail at test collection"
    find services -name "*.py" -exec python3 -m py_compile {} \;
    exit 1
}
log_success "Python syntax validation passed"

# 6. Check for common CI failure patterns
log_step "Checking for common CI failure patterns"

# Check for print statements that might block git
if grep -r "print(" services/ --include="*.py" | grep -v "#" | head -5; then
    log_warning "Found print statements - ensure they don't block git operations"
fi

# Check for missing requirements
if find services -name "requirements.txt" -exec grep -l "langsmith" {} \; 2>/dev/null | head -1; then
    log_warning "Found langsmith in requirements - CI removes it to avoid conflicts"
fi

# Summary
echo ""
echo "📊 PREDICTION SUMMARY"
echo "===================="
if [ "$E2E_REQUIRED" = "true" ]; then
    echo "🕐 Estimated CI runtime: 10-12 minutes (full e2e pipeline)"
    echo "🔧 CI will: create k3d cluster → build/pull images → deploy → test"
else
    echo "🕐 Estimated CI runtime: 1-2 minutes (quick validation only)"
    echo "🔧 CI will: skip k3d cluster → skip Docker builds → run unit tests only"
fi

echo ""
if [ $MISSING_IMAGES -eq 0 ] && [ "$E2E_REQUIRED" = "false" ]; then
    log_success "🚀 Ready to push - CI should complete quickly!"
elif [ "$E2E_REQUIRED" = "true" ]; then
    log_warning "⚠️  Infrastructure changes detected - consider running full local test:"
    echo "   ./scripts/test-ci-locally.sh"
else
    log_success "🚀 Ready to push - CI should succeed!"
fi