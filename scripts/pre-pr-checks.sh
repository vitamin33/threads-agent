#!/bin/bash
# Pre-PR validation script - Run all checks before creating a PR
# Usage: ./scripts/pre-pr-checks.sh

set -e

echo "🚀 Running Pre-PR Checks"
echo "========================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# 1. Check for uncommitted changes
echo -e "\n${YELLOW}1. Checking for uncommitted changes...${NC}"
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}❌ You have uncommitted changes${NC}"
    git status --short
    echo "   Please commit or stash your changes first"
    FAILED=1
else
    echo -e "${GREEN}✅ Working directory clean${NC}"
fi

# 2. Run linting
echo -e "\n${YELLOW}2. Running linters...${NC}"
if command -v ruff &> /dev/null; then
    if ruff check . --select=E,W,F --quiet; then
        echo -e "${GREEN}✅ Linting passed${NC}"
    else
        echo -e "${RED}❌ Linting failed${NC}"
        echo "   Run 'ruff check .' to see details"
        FAILED=1
    fi
else
    echo -e "${YELLOW}⚠️  Ruff not installed, skipping lint${NC}"
fi

# 3. Check for debug prints
echo -e "\n${YELLOW}3. Checking for debug prints...${NC}"
if grep -r "print(" services/ --include="*.py" | grep -v "# noqa" | grep -v "__pycache__" > /dev/null; then
    echo -e "${RED}❌ Found debug print statements${NC}"
    echo "   Run: grep -r 'print(' services/ --include='*.py'"
    FAILED=1
else
    echo -e "${GREEN}✅ No debug prints found${NC}"
fi

# 4. Run unit tests (fast)
echo -e "\n${YELLOW}4. Running unit tests...${NC}"
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if pytest is available
if command -v pytest &> /dev/null; then
    # Run only unit tests (not e2e) for speed
    if PYTHONPATH=$PWD:$PYTHONPATH pytest -m "not e2e" -q --tb=short --maxfail=3; then
        echo -e "${GREEN}✅ Unit tests passed${NC}"
    else
        echo -e "${RED}❌ Unit tests failed${NC}"
        FAILED=1
    fi
else
    echo -e "${YELLOW}⚠️  Pytest not installed, skipping tests${NC}"
fi

# 5. Check CI will pass
echo -e "\n${YELLOW}5. Checking CI configuration...${NC}"

# Check if required test dependencies are installed
MISSING_DEPS=()
for dep in psutil httpx pytest-xdist pytest-timeout; do
    if ! pip show $dep &> /dev/null; then
        MISSING_DEPS+=($dep)
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing test dependencies: ${MISSING_DEPS[*]}${NC}"
    echo "   Run: pip install -r tests/requirements.txt"
    FAILED=1
else
    echo -e "${GREEN}✅ Test dependencies installed${NC}"
fi

# 6. Run quick CI simulation
echo -e "\n${YELLOW}6. Running quick CI simulation...${NC}"
if [ "$FAILED" -eq 0 ]; then
    # Simulate what quick-ci workflow does
    echo "   • Checking Python files changed..."
    CHANGED_PY=$(git diff --name-only origin/main...HEAD | grep -E "\.py$" | wc -l)
    echo "   • Python files changed: $CHANGED_PY"
    
    if [ "$CHANGED_PY" -gt 0 ]; then
        echo "   • Would trigger full CI suite"
    else
        echo "   • Would skip heavy CI (no Python changes)"
    fi
    echo -e "${GREEN}✅ CI simulation passed${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping CI simulation due to previous failures${NC}"
fi

# 7. Optional: Run e2e tests locally
echo -e "\n${YELLOW}7. E2E Tests (Optional)${NC}"
echo "To run e2e tests locally before PR:"
echo "   1. Ensure k3d cluster is running: just dev-start"
echo "   2. Run: PYTHONPATH=\$PWD pytest tests/e2e -v"

# Summary
echo -e "\n${"="*60}"
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED! Ready to create PR${NC}"
    echo -e "\nNext steps:"
    echo "1. Push your branch: git push origin <branch-name>"
    echo "2. Create PR: gh pr create"
else
    echo -e "${RED}❌ SOME CHECKS FAILED! Fix issues before creating PR${NC}"
    echo -e "\nFailed checks need attention before PR will pass CI"
    exit 1
fi