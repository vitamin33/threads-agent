# 🚀 4-Agent Parallel Development Workflow

## Initial Setup (One-Time per Warp Window)

### Window 1: Agent A1 (MLOps/Orchestrator)
```bash
# 1. Navigate to worktree
cd ~/development/wt-a1-mlops

# 2. Update and prepare
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/a1/work-$(date +%Y%m%d)

# 3. Set agent environment
export AGENT_ID=a1
export AGENT_FOCUS="MLOps, Orchestrator, Common Infrastructure"
export AGENT_SERVICES="orchestrator celery_worker common"
export PORT_OFFSET=0

# 4. Create local agent config
cat > .agent.env << 'EOF'
AGENT_ID=a1
AGENT_NAME="MLOps Specialist"
FOCUS_AREAS="orchestrator,celery_worker,common,monitoring"
PRIMARY_GOALS="Performance optimization, SLO monitoring, MLflow integration"
SKIP_SERVICES="rag_pipeline,vllm_service,achievement_collector,revenue"
EOF
```

### Window 2: Agent A2 (GenAI/RAG)
```bash
# 1. Navigate to worktree
cd ~/development/wt-a2-genai

# 2. Update and prepare
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/a2/work-$(date +%Y%m%d)

# 3. Set agent environment
export AGENT_ID=a2
export AGENT_FOCUS="GenAI, RAG Pipeline, Vector Search"
export AGENT_SERVICES="rag_pipeline vllm_service persona_runtime"
export PORT_OFFSET=100

# 4. Create local agent config
cat > .agent.env << 'EOF'
AGENT_ID=a2
AGENT_NAME="GenAI Specialist"
FOCUS_AREAS="rag_pipeline,vllm_service,persona_runtime,viral_engine"
PRIMARY_GOALS="LLM optimization, RAG accuracy, Cost reduction"
SKIP_SERVICES="orchestrator,achievement_collector,revenue,finops_engine"
EOF
```

### Window 3: Agent A3 (Achievement/Analytics)
```bash
# 1. Navigate to worktree
cd ~/development/wt-a3-analytics

# 2. Update and prepare
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/a3/work-$(date +%Y%m%d)

# 3. Set agent environment
export AGENT_ID=a3
export AGENT_FOCUS="Achievement System, Analytics, Documentation"
export AGENT_SERVICES="achievement_collector tech_doc_generator dashboard_api"
export PORT_OFFSET=200

# 4. Create local agent config
cat > .agent.env << 'EOF'
AGENT_ID=a3
AGENT_NAME="Analytics Specialist"
FOCUS_AREAS="achievement_collector,tech_doc_generator,dashboard_api"
PRIMARY_GOALS="Portfolio building, Metrics tracking, Documentation"
SKIP_SERVICES="orchestrator,rag_pipeline,revenue,viral_engine"
EOF
```

### Window 4: Agent A4 (Revenue/Platform)
```bash
# 1. Navigate to worktree
cd ~/development/wt-a4-platform

# 2. Update and prepare
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/a4/work-$(date +%Y%m%d)

# 3. Set agent environment
export AGENT_ID=a4
export AGENT_FOCUS="Revenue, FinOps, Platform Infrastructure"
export AGENT_SERVICES="revenue finops_engine event_bus"
export PORT_OFFSET=300

# 4. Create local agent config
cat > .agent.env << 'EOF'
AGENT_ID=a4
AGENT_NAME="Platform Specialist"
FOCUS_AREAS="revenue,finops_engine,event_bus,threads_adaptor"
PRIMARY_GOALS="Monetization, Cost optimization, Platform scaling"
SKIP_SERVICES="orchestrator,rag_pipeline,achievement_collector"
EOF
```

## Daily Workflow Process

### 🌅 Morning Routine (All Agents)

```bash
# Run this in each worktree every morning
./scripts/daily-agent-setup.sh

# This script will:
# 1. Pull latest main
# 2. Create today's work branch
# 3. Check for assigned tasks
# 4. Set up environment
# 5. Start local services
```

### 📋 Task Distribution System

#### Linear Integration
Each agent monitors specific Linear labels:
- **A1**: `mlops`, `orchestrator`, `performance`, `monitoring`
- **A2**: `genai`, `rag`, `llm`, `viral-engine`
- **A3**: `achievement`, `analytics`, `documentation`, `portfolio`
- **A4**: `revenue`, `finops`, `platform`, `infrastructure`

#### Automated Task Assignment
```bash
# Check assigned tasks for your agent
just agent-tasks

# This will show:
# - Linear issues assigned to your agent's areas
# - PR reviews needed in your services
# - Test failures in your domains
```

### 🤖 Claude Code Agent Configuration

#### Agent-Specific Sub-Agents Usage

**For Agent A1 (MLOps):**
```bash
# Primary sub-agents to use:
- k8s-performance-optimizer (for all performance work)
- devops-automation-expert (for CI/CD and monitoring)
- tdd-master (for test-driven development)

# Workflow:
1. Start with epic-planning-specialist for new features
2. Use tdd-master for implementation
3. Run k8s-performance-optimizer for optimization
4. Finish with tech-documentation-generator
```

**For Agent A2 (GenAI):**
```bash
# Primary sub-agents to use:
- epic-planning-specialist (for RAG features)
- tdd-master (for implementation)
- k8s-performance-optimizer (for LLM optimization)

# Focus areas:
- Token optimization
- RAG accuracy improvements
- Cost reduction strategies
```

**For Agent A3 (Achievement):**
```bash
# Primary sub-agents to use:
- epic-planning-specialist (for portfolio features)
- test-generation-specialist (for comprehensive testing)
- tech-documentation-generator (for all documentation)

# Focus areas:
- Achievement tracking
- Portfolio generation
- Dashboard improvements
```

**For Agent A4 (Revenue):**
```bash
# Primary sub-agents to use:
- epic-planning-specialist (for revenue features)
- tdd-master (for payment systems)
- devops-automation-expert (for platform scaling)

# Focus areas:
- Payment integration
- Cost optimization
- Platform reliability
```

### 💻 Development Commands

#### Agent-Specific Commands
```bash
# Test only your services
just test-agent

# Build only your Docker images
just build-agent

# Deploy only your services
just deploy-agent

# Check your code quality
just lint-agent
```

#### Coordination Commands
```bash
# Check if other agents are working on common files
just check-conflicts

# Lock a common file for editing
just lock-file services/common/config.py

# Release lock when done
just unlock-file services/common/config.py

# See all active locks
just show-locks
```

### 📊 Progress Monitoring

```bash
# Check your daily progress
just agent-progress

# See team overview (all agents)
just team-dashboard

# Generate achievement report
just agent-achievements
```

### 🔄 Sync Points

#### Daily Sync (Automated)
- **10 AM**: Morning sync - task distribution
- **2 PM**: Progress check - blocker identification
- **5 PM**: EOD sync - commit and push

#### Weekly Sync
- **Monday**: Sprint planning - assign epics to agents
- **Friday**: Demo day - show achievements

### 🚀 Commit and PR Process

```bash
# 1. Quick commit (agent-specific)
just agent-commit "feat: implement new feature"

# 2. Create PR with agent label
just agent-pr

# 3. Request review from other agents (if needed)
just request-review a2 a3  # Request from agents 2 and 3
```

## Automation Scripts

### Create Daily Setup Script
Save as `scripts/daily-agent-setup.sh`:

```bash
#!/bin/bash
source .agent.env

echo "🤖 Setting up Agent $AGENT_ID for $(date +%Y-%m-%d)"

# 1. Update main
git fetch origin
git checkout main
git pull origin main

# 2. Create work branch
BRANCH="feat/$AGENT_ID/$(date +%Y%m%d)-$(git rev-parse --short HEAD)"
git checkout -b $BRANCH

# 3. Check Linear tasks
echo "📋 Checking assigned tasks..."
just agent-tasks

# 4. Set up environment
export DATABASE_URL="postgresql://postgres:pass@localhost:$((5432 + PORT_OFFSET))/agent_$AGENT_ID"
export REDIS_URL="redis://localhost:$((6379 + PORT_OFFSET))"

# 5. Start services
echo "🚀 Starting local services..."
just dev-start-agent

echo "✅ Agent $AGENT_ID ready for work!"
```

### Create Task Checker
Save as `scripts/check-agent-tasks.sh`:

```bash
#!/bin/bash
source .agent.env

# Check Linear for assigned tasks
echo "📋 Tasks for Agent $AGENT_ID:"
echo "================================"

# Use Linear API to fetch tasks
curl -s -H "Authorization: $LINEAR_API_KEY" \
  "https://api.linear.app/graphql" \
  -d '{"query":"{ issues(filter: { labels: { name: { in: ['$FOCUS_AREAS'] } } }) { nodes { identifier title state { name } } } }"}' \
  | jq -r '.data.issues.nodes[] | "\(.identifier): \(.title) [\(.state.name)]"'
```

## Justfile Additions

Add to your Justfile:

```makefile
# Agent-specific commands
agent-tasks:
    @./scripts/check-agent-tasks.sh

agent-commit message:
    @git add -A && git commit -m "[{{AGENT_ID}}] {{message}}"

agent-pr:
    @gh pr create --label "agent-{{AGENT_ID}}" --label "auto-merge"

test-agent:
    @pytest services/{{AGENT_SERVICES}}/tests -v

build-agent:
    @for service in {{AGENT_SERVICES}}; do \
        docker build -t $$service:agent-{{AGENT_ID}} services/$$service; \
    done

agent-progress:
    @echo "📊 Progress for Agent {{AGENT_ID}}:"
    @git log --oneline --since="6am" --author="{{USER}}"

check-conflicts:
    @ls ../.common-lock-* 2>/dev/null || echo "✅ No locks found"

lock-file file:
    @touch ../.common-lock-{{AGENT_ID}}-{{file}}
    @echo "🔒 Locked {{file}} for Agent {{AGENT_ID}}"

unlock-file file:
    @rm -f ../.common-lock-{{AGENT_ID}}-{{file}}
    @echo "🔓 Unlocked {{file}}"
```

## VS Code / Cursor Settings

For each worktree, create `.vscode/settings.json`:

```json
{
  "window.title": "Agent ${AGENT_ID} - ${AGENT_FOCUS}",
  "workbench.colorTheme": "Agent Theme A${AGENT_ID}",
  "terminal.integrated.env.osx": {
    "AGENT_ID": "${AGENT_ID}",
    "PORT_OFFSET": "${PORT_OFFSET}"
  },
  "files.exclude": {
    "**/services/": true,
    "!**/services/${AGENT_SERVICES}/": true,
    "!**/services/common/": true
  }
}
```

## Claude Code Integration

### CLAUDE.md Updates for Each Agent

Create `CLAUDE_AGENT.md` in each worktree:

```markdown
# Agent A1 - MLOps Specialist

You are Agent A1, focused on MLOps and orchestration.

## Your Responsibilities
- services/orchestrator
- services/celery_worker
- services/common (shared with others - check locks!)
- Monitoring and observability
- Performance optimization

## Your Sub-Agents
Always use these in order:
1. epic-planning-specialist - for planning
2. tdd-master - for implementation
3. k8s-performance-optimizer - for optimization
4. tech-documentation-generator - for docs

## Ignore These Services
Never modify: rag_pipeline, vllm_service, achievement_collector, revenue

## Daily Tasks
Check Linear labels: mlops, orchestrator, performance, monitoring
```

## Recommended Daily Schedule

### For Each Agent (Staggered):
- **9:00 AM**: A1 starts, pulls tasks, begins work
- **9:15 AM**: A2 starts, pulls tasks, begins work  
- **9:30 AM**: A3 starts, pulls tasks, begins work
- **9:45 AM**: A4 starts, pulls tasks, begins work
- **2:00 PM**: All agents sync progress
- **5:00 PM**: All agents commit and push

This staggered approach prevents conflicts and allows smooth parallel development.

## Summary

This setup provides:
1. **Clear separation** - Each agent has specific services
2. **Automated workflows** - Scripts handle daily setup
3. **Conflict prevention** - Lock system for shared files
4. **Progress tracking** - Built-in monitoring
5. **Efficient commits** - Agent-specific PR process

Start tomorrow by:
1. Opening 4 Warp windows
2. Running the setup commands for each agent
3. Using the daily workflow process
4. Leveraging the specialized sub-agents for each domain

This system will make your 4-agent development highly efficient and conflict-free!