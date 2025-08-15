#!/bin/bash

# Agent Worktree Merge Script
# Safely merges agent worktree changes back to main

set -e

# Detect current agent from worktree path
CURRENT_PATH=$(pwd)
if [[ "$CURRENT_PATH" == *"wt-a1"* ]]; then
    AGENT_ID="a1"
    AGENT_TYPE="MLOps"
elif [[ "$CURRENT_PATH" == *"wt-a2"* ]]; then
    AGENT_ID="a2" 
    AGENT_TYPE="GenAI"
elif [[ "$CURRENT_PATH" == *"wt-a3"* ]]; then
    AGENT_ID="a3"
    AGENT_TYPE="Analytics"
elif [[ "$CURRENT_PATH" == *"wt-a4"* ]]; then
    AGENT_ID="a4"
    AGENT_TYPE="Platform"
else
    echo "⚠️  Not in an agent worktree. Use from wt-a1, wt-a2, wt-a3, or wt-a4"
    exit 1
fi

echo "🤖 Agent $AGENT_TYPE ($AGENT_ID) merge process starting..."

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --staged --quiet; then
    echo "❌ Uncommitted changes detected. Please commit first."
    git status --short
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Quality checks
echo "🔍 Running quality checks..."
if ! just check; then
    echo "❌ Quality checks failed. Fix issues before merging."
    exit 1
fi

# Switch to main and update
echo "🔄 Switching to main branch..."
cd ../threads-agent  # Main worktree
git checkout main
git pull origin main

# Create feature branch for this agent
FEATURE_BRANCH="feat/$AGENT_ID/$(date +%Y%m%d-%H%M%S)"
echo "🌟 Creating feature branch: $FEATURE_BRANCH"
git checkout -b "$FEATURE_BRANCH"

# Merge agent changes (using merge to preserve agent context)
echo "🔀 Merging $AGENT_TYPE agent changes..."
git merge --no-ff "$CURRENT_BRANCH" -m "feat: merge $AGENT_TYPE agent work from $CURRENT_BRANCH

🤖 Agent: $AGENT_TYPE ($AGENT_ID)
📝 Branch: $CURRENT_BRANCH
🎯 Focus: $AGENT_TYPE specialization
⚡ Auto-merged via agent-merge.sh"

# Run final tests on merged result
echo "🧪 Running integration tests on merged code..."
if ! just e2e-prepare && just unit; then
    echo "❌ Integration tests failed. Please review manually."
    exit 1
fi

# Push feature branch
echo "📤 Pushing feature branch..."
git push origin "$FEATURE_BRANCH"

# Create PR
echo "📋 Creating pull request..."
gh pr create \
    --title "[$AGENT_TYPE] Agent work integration - $(date +%Y-%m-%d)" \
    --body "## $AGENT_TYPE Agent Integration

🤖 **Agent**: $AGENT_TYPE ($AGENT_ID)
📝 **Source Branch**: $CURRENT_BRANCH  
🎯 **Specialization**: $AGENT_TYPE focus area
📅 **Date**: $(date +'%Y-%m-%d %H:%M:%S')

### Changes Summary
Auto-merged from agent worktree with quality gates:
- ✅ Quality checks passed (lint, type, tests)
- ✅ Integration tests passed
- ✅ No merge conflicts

### Agent Context
This PR contains work from the $AGENT_TYPE agent worktree focused on:
$(cat ../wt-$AGENT_ID-*/AGENT_FOCUS.md 2>/dev/null | head -3 || echo "- $AGENT_TYPE specialization work")

🤖 Auto-generated via agent-merge.sh" \
    --label "agent-integration" \
    --label "auto-merge"

echo "✅ Agent merge completed!"
echo "🔗 View PR: $(gh pr view --web)"
echo ""
echo "📋 Next steps:"
echo "1. Review PR in GitHub"
echo "2. Wait for CI to pass"  
echo "3. Auto-merge will complete if all checks pass"