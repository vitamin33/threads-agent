#!/bin/bash
# Test script to verify 4-agent parallel setup is working

echo "🧪 Testing 4-Agent Parallel Setup"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

errors=0

# Test 1: Worktrees exist
echo "Test 1: Checking worktrees..."
for agent in a1-mlops a2-genai a3-analytics a4-platform; do
  if [ -d "../wt-$agent" ]; then
    echo -e "  ${GREEN}✓${NC} wt-$agent exists"
  else
    echo -e "  ${RED}✗${NC} wt-$agent missing"
    ((errors++))
  fi
done

# Test 2: Git branches
echo -e "\nTest 2: Checking git branches..."
for agent in a1 a2 a3 a4; do
  branch=$(git -C "../wt-${agent}-"* branch --show-current 2>/dev/null)
  if [[ "$branch" == "feat/${agent}/main" ]]; then
    echo -e "  ${GREEN}✓${NC} Agent $agent on branch $branch"
  else
    echo -e "  ${RED}✗${NC} Agent $agent branch issue"
    ((errors++))
  fi
done

# Test 3: Local files
echo -e "\nTest 3: Checking local files..."
for wt in ../wt-a*; do
  [ ! -d "$wt" ] && continue
  agent=$(basename "$wt")
  
  if [ -f "$wt/AGENT_FOCUS.md" ] && [ -f "$wt/.agent.env" ]; then
    echo -e "  ${GREEN}✓${NC} $agent has local config files"
  else
    echo -e "  ${RED}✗${NC} $agent missing config files"
    ((errors++))
  fi
done

# Test 4: Python environments
echo -e "\nTest 4: Checking Python venvs..."
for wt in ../wt-a*; do
  [ ! -d "$wt" ] && continue
  agent=$(basename "$wt")
  
  if [ -d "$wt/.venv" ]; then
    echo -e "  ${GREEN}✓${NC} $agent has Python venv"
  else
    echo -e "  ${RED}✗${NC} $agent missing venv"
    ((errors++))
  fi
done

# Test 5: Gitignore working
echo -e "\nTest 5: Checking gitignore..."
for wt in ../wt-a*; do
  [ ! -d "$wt" ] && continue
  agent=$(basename "$wt")
  
  # Check if AGENT_FOCUS.md is ignored
  if git -C "$wt" check-ignore AGENT_FOCUS.md 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} $agent ignores local files"
  else
    # Check if it's in gitignore at least
    if grep -q "AGENT_FOCUS.md" "$wt/.gitignore"; then
      echo -e "  ${GREEN}✓${NC} $agent has gitignore patterns"
    else
      echo -e "  ${RED}✗${NC} $agent gitignore issue"
      ((errors++))
    fi
  fi
done

# Test 6: Database schemas
echo -e "\nTest 6: Checking database schemas..."
if kubectl exec postgres-0 -- psql -U postgres -d threads_agent -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'agent_%';" 2>/dev/null | grep -q "agent_a"; then
  echo -e "  ${GREEN}✓${NC} Database schemas created"
else
  echo -e "  ${RED}✗${NC} Database schemas not found (may be normal if k3d not running)"
fi

# Test 7: Lock directory
echo -e "\nTest 7: Checking coordination..."
if [ -d ".locks" ]; then
  echo -e "  ${GREEN}✓${NC} Lock directory exists"
else
  echo -e "  ${RED}✗${NC} Lock directory missing"
  ((errors++))
fi

# Summary
echo ""
echo "=================================="
if [ $errors -eq 0 ]; then
  echo -e "${GREEN}✅ All tests passed!${NC}"
  echo ""
  echo "Your 4-agent parallel setup is ready!"
  echo ""
  echo "Next steps:"
  echo "1. Open 4 editor windows (one per worktree)"
  echo "2. In each: source .venv/bin/activate && source .agent.env"
  echo "3. Start developing with no conflicts!"
else
  echo -e "${RED}❌ $errors tests failed${NC}"
  echo ""
  echo "Run ./setup-4-agents.sh to fix the setup"
fi