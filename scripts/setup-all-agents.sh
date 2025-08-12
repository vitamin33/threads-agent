#!/bin/bash

# One-time setup script to prepare all 4 agent worktrees
set -e

echo "═══════════════════════════════════════════════════════"
echo "🚀 Setting up 4-Agent Parallel Development Environment"
echo "═══════════════════════════════════════════════════════"

# Base directory for worktrees (one level up from main repo)
BASE_DIR=$(dirname $(pwd))

# Create worktrees if they don't exist
setup_worktree() {
    local AGENT_ID=$1
    local AGENT_NAME=$2
    local WORKTREE_DIR="$BASE_DIR/wt-$AGENT_ID-$AGENT_NAME"
    
    echo ""
    echo "Setting up Agent $AGENT_ID ($AGENT_NAME)..."
    
    if [ ! -d "$WORKTREE_DIR" ]; then
        echo "  Creating worktree at $WORKTREE_DIR"
        git worktree add "$WORKTREE_DIR" main
    else
        echo "  Worktree already exists at $WORKTREE_DIR"
    fi
    
    # Copy scripts to worktree
    echo "  Copying scripts..."
    cp -r scripts "$WORKTREE_DIR/" 2>/dev/null || true
    
    # Make scripts executable
    chmod +x "$WORKTREE_DIR/scripts/"*.sh 2>/dev/null || true
    
    echo "✅ Agent $AGENT_ID setup complete"
}

# Setup each agent
setup_worktree "a1" "mlops"
setup_worktree "a2" "genai"
setup_worktree "a3" "analytics"
setup_worktree "a4" "platform"

# Create agent configuration files
echo ""
echo "📝 Creating agent configuration files..."

# Agent A1 Configuration
cat > "$BASE_DIR/wt-a1-mlops/.agent.env" << 'EOF'
AGENT_ID=a1
AGENT_NAME="MLOps Specialist"
FOCUS_AREAS="orchestrator,celery_worker,common,monitoring"
AGENT_SERVICES="orchestrator celery_worker"
PRIMARY_GOALS="Performance optimization, SLO monitoring, MLflow integration"
SKIP_SERVICES="rag_pipeline,vllm_service,achievement_collector,revenue"
PORT_OFFSET=0
EOF

# Agent A2 Configuration
cat > "$BASE_DIR/wt-a2-genai/.agent.env" << 'EOF'
AGENT_ID=a2
AGENT_NAME="GenAI Specialist"
FOCUS_AREAS="rag_pipeline,vllm_service,persona_runtime,viral_engine"
AGENT_SERVICES="rag_pipeline vllm_service persona_runtime"
PRIMARY_GOALS="LLM optimization, RAG accuracy, Cost reduction"
SKIP_SERVICES="orchestrator,achievement_collector,revenue,finops_engine"
PORT_OFFSET=100
EOF

# Agent A3 Configuration
cat > "$BASE_DIR/wt-a3-analytics/.agent.env" << 'EOF'
AGENT_ID=a3
AGENT_NAME="Analytics Specialist"
FOCUS_AREAS="achievement_collector,tech_doc_generator,dashboard_api"
AGENT_SERVICES="achievement_collector tech_doc_generator dashboard_api"
PRIMARY_GOALS="Portfolio building, Metrics tracking, Documentation"
SKIP_SERVICES="orchestrator,rag_pipeline,revenue,viral_engine"
PORT_OFFSET=200
EOF

# Agent A4 Configuration
cat > "$BASE_DIR/wt-a4-platform/.agent.env" << 'EOF'
AGENT_ID=a4
AGENT_NAME="Platform Specialist"
FOCUS_AREAS="revenue,finops_engine,event_bus,threads_adaptor"
AGENT_SERVICES="revenue finops_engine event_bus"
PRIMARY_GOALS="Monetization, Cost optimization, Platform scaling"
SKIP_SERVICES="orchestrator,rag_pipeline,achievement_collector"
PORT_OFFSET=300
EOF

# Create launch scripts for each terminal
echo ""
echo "📱 Creating Warp launch commands..."

cat > "$BASE_DIR/launch-agents.md" << 'EOF'
# Launch Commands for Warp Windows

## Window 1 - Agent A1 (MLOps)
```bash
cd ~/development/wt-a1-mlops && source .agent.env && ./scripts/daily-agent-setup.sh
```

## Window 2 - Agent A2 (GenAI)
```bash
cd ~/development/wt-a2-genai && source .agent.env && ./scripts/daily-agent-setup.sh
```

## Window 3 - Agent A3 (Analytics)
```bash
cd ~/development/wt-a3-analytics && source .agent.env && ./scripts/daily-agent-setup.sh
```

## Window 4 - Agent A4 (Platform)
```bash
cd ~/development/wt-a4-platform && source .agent.env && ./scripts/daily-agent-setup.sh
```

## Quick All-Agent Status Check
```bash
for agent in a1 a2 a3 a4; do
    echo "Agent $agent: $(cd ~/development/wt-$agent-* && git branch --show-current)"
done
```
EOF

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ 4-Agent Setup Complete!"
echo ""
echo "📂 Worktree Locations:"
echo "  A1 (MLOps):     $BASE_DIR/wt-a1-mlops"
echo "  A2 (GenAI):     $BASE_DIR/wt-a2-genai"
echo "  A3 (Analytics): $BASE_DIR/wt-a3-analytics"
echo "  A4 (Platform):  $BASE_DIR/wt-a4-platform"
echo ""
echo "🚀 Next Steps:"
echo "  1. Open 4 Warp windows"
echo "  2. Copy the launch command for each agent from:"
echo "     $BASE_DIR/launch-agents.md"
echo "  3. Paste into each window to start working"
echo ""
echo "💡 Daily Workflow:"
echo "  - Each morning, run: ./scripts/daily-agent-setup.sh"
echo "  - This will update, create branches, and check tasks"
echo "═══════════════════════════════════════════════════════"