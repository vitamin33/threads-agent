#!/bin/bash
# ci-preflight-check.sh - Quick validation before pushing to CI
set -e

echo "🚀 CI PREFLIGHT CHECK"
echo "===================="

# Check 1: Verify essential services have Dockerfiles
echo "1. Checking essential service Dockerfiles..."
ESSENTIAL_SERVICES="orchestrator celery_worker persona_runtime fake_threads"
for svc in $ESSENTIAL_SERVICES; do
    if [ -f "services/${svc}/Dockerfile" ]; then
        echo "  ✅ $svc - Dockerfile exists"
    else
        echo "  ❌ $svc - Missing Dockerfile!"
        exit 1
    fi
done

# Check 2: Validate Helm values
echo -e "\n2. Validating Helm values..."
helm template ./chart -f chart/values-ci-fast.yaml --dry-run > /dev/null 2>&1 && \
    echo "  ✅ Helm template renders successfully" || \
    echo "  ❌ Helm template failed!"

# Check 3: Check for disabled services in CI
echo -e "\n3. Checking CI service configuration..."
grep -E "enabled: false" chart/values-ci-fast.yaml | grep -E "(viral|mlflow|achievement|conversation|revenue)" && \
    echo "  ✅ Non-essential services disabled for CI" || \
    echo "  ⚠️  Consider disabling non-essential services"

# Check 4: Estimate CI runtime
echo -e "\n4. CI Runtime Estimate:"
if git diff --name-only HEAD~1 2>/dev/null | grep -qE "(chart/|Dockerfile|scripts/)"; then
    echo "  ⏱️  Infrastructure changes detected: ~10-12 minutes"
else
    echo "  ⚡ Code-only changes: ~2-3 minutes (quick-ci only)"
fi

echo -e "\n✅ Preflight check complete!"
echo "Ready to push? Run: git push"