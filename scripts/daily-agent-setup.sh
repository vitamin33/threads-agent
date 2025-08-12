#!/bin/bash

# Daily setup script for agent worktrees
set -e

# Load agent configuration
if [ -f .agent.env ]; then
    source .agent.env
else
    echo "❌ No .agent.env file found. Please run initial setup first."
    exit 1
fi

echo "═══════════════════════════════════════════════════════"
echo "🤖 Setting up Agent $AGENT_ID ($AGENT_NAME)"
echo "📅 Date: $(date +%Y-%m-%d)"
echo "═══════════════════════════════════════════════════════"

# 1. Update from main
echo ""
echo "📥 Updating from main branch..."
git fetch origin
git checkout main --quiet
git pull origin main --quiet
echo "✅ Main branch updated"

# 2. Create today's work branch
BRANCH="feat/$AGENT_ID/$(date +%Y%m%d)-$(git rev-parse --short HEAD)"
echo ""
echo "🌿 Creating work branch: $BRANCH"
git checkout -b $BRANCH 2>/dev/null || git checkout $BRANCH
echo "✅ Work branch ready"

# 3. Set up environment variables
echo ""
echo "🔧 Setting up environment..."
export DATABASE_URL="postgresql://postgres:pass@localhost:$((5432 + PORT_OFFSET))/agent_$AGENT_ID"
export REDIS_URL="redis://localhost:$((6379 + PORT_OFFSET))"
export RABBITMQ_URL="amqp://user:pass@localhost:$((5672 + PORT_OFFSET))/%2f"
export PROMETHEUS_PORT=$((9090 + PORT_OFFSET))
export GRAFANA_PORT=$((3000 + PORT_OFFSET))

# 4. Check for conflicts
echo ""
echo "🔍 Checking for file locks from other agents..."
if ls ../.common-lock-* 2>/dev/null | grep -v "$AGENT_ID"; then
    echo "⚠️  Warning: Other agents have locked files:"
    ls ../.common-lock-* 2>/dev/null | grep -v "$AGENT_ID" | sed 's/.*lock-/  - /'
else
    echo "✅ No conflicting locks found"
fi

# 5. Check Linear tasks (if API key is set)
if [ -n "$LINEAR_API_KEY" ]; then
    echo ""
    echo "📋 Fetching assigned tasks..."
    ./scripts/check-agent-tasks.sh 2>/dev/null || echo "⚠️  Linear API not configured"
fi

# 6. Display agent focus
echo ""
echo "🎯 Your Focus Areas:"
echo "  - Services: $AGENT_SERVICES"
echo "  - Goals: $PRIMARY_GOALS"
echo ""
echo "📝 Quick Commands:"
echo "  just test-agent      - Run tests for your services"
echo "  just agent-commit    - Commit with agent prefix"
echo "  just agent-pr        - Create PR with agent labels"
echo "  just check-conflicts - Check for file locks"
echo ""
echo "✅ Agent $AGENT_ID is ready for work!"
echo "═══════════════════════════════════════════════════════"