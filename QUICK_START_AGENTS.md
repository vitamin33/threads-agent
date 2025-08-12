# 🚀 Quick Start: 4-Agent Parallel Development

## Initial Setup (Run Once)
```bash
cd ~/development/threads-agent
./scripts/setup-all-agents.sh
```

This creates 4 worktrees with configurations:
- `~/development/wt-a1-mlops` - MLOps Agent
- `~/development/wt-a2-genai` - GenAI Agent  
- `~/development/wt-a3-analytics` - Analytics Agent
- `~/development/wt-a4-platform` - Platform Agent

## Daily Workflow for Each Warp Window

### Window 1: Agent A1 (MLOps)
```bash
cd ~/development/wt-a1-mlops
source .agent.env
./scripts/daily-agent-setup.sh

# Your focus: Orchestrator, Celery, Performance
# Primary agents: k8s-performance-optimizer, devops-automation-expert
```

### Window 2: Agent A2 (GenAI)
```bash
cd ~/development/wt-a2-genai
source .agent.env
./scripts/daily-agent-setup.sh

# Your focus: RAG Pipeline, LLM, Viral Engine
# Primary agents: epic-planning-specialist, k8s-performance-optimizer
```

### Window 3: Agent A3 (Analytics)
```bash
cd ~/development/wt-a3-analytics
source .agent.env
./scripts/daily-agent-setup.sh

# Your focus: Achievements, Documentation, Dashboard
# Primary agents: test-generation-specialist, tech-documentation-generator
```

### Window 4: Agent A4 (Platform)
```bash
cd ~/development/wt-a4-platform
source .agent.env
./scripts/daily-agent-setup.sh

# Your focus: Revenue, FinOps, Platform
# Primary agents: tdd-master, devops-automation-expert
```

## Essential Commands (Run in Each Window)

```bash
# Morning
just morning          # Update from main, create work branch

# During work
just test-agent       # Test your services only
just agent-commit "message"  # Commit with agent prefix
just check-conflicts  # Check if others locked files
just lock-file path   # Lock a file you're editing

# Evening
just agent-pr         # Create PR with agent labels
just evening          # Commit EOD work and push
```

## Agent-Specific Claude Code Usage

### For Each Window, Tell Claude:
```
I am Agent A1 working on MLOps and orchestrator services.
My focus is: orchestrator, celery_worker, monitoring.
I should use these sub-agents: k8s-performance-optimizer, devops-automation-expert.
I should NOT touch: rag_pipeline, achievement_collector, revenue services.
```

### Sub-Agent Workflow Pattern:
1. `epic-planning-specialist` - Plan the feature
2. `tdd-master` - Write tests first
3. Your implementation
4. `k8s-performance-optimizer` - Optimize code
5. `test-generation-specialist` - Add more tests
6. `tech-documentation-generator` - Document

## Coordination Between Agents

### Check what others are doing:
```bash
just team-status      # See all agents' branches
just show-locks       # See locked files
```

### Working on shared files:
```bash
just lock-file services/common/config.py   # Lock before editing
# ... make your changes ...
just unlock-file services/common/config.py # Unlock when done
```

### Request review from other agents:
```bash
just agent-pr                    # Create your PR first
just request-review "a2 a3"      # Request from agents 2 and 3
```

## Quick Reference

| Agent | Services | Focus | Port Range |
|-------|----------|-------|------------|
| A1 | orchestrator, celery_worker | MLOps, Performance | 8080-8099 |
| A2 | rag_pipeline, vllm_service | GenAI, LLM | 8180-8199 |
| A3 | achievement_collector, dashboard | Analytics, Docs | 8280-8299 |
| A4 | revenue, finops_engine | Platform, Revenue | 8380-8399 |

## Tips for Success

1. **Always run morning setup**: Updates main and checks for conflicts
2. **Use agent prefixes**: All commits should start with [a1], [a2], etc.
3. **Check locks before editing common files**: Prevents merge conflicts
4. **Small, focused PRs**: Each agent should create small PRs
5. **Use sub-agents appropriately**: Each agent has specialized sub-agents
6. **Coordinate at sync points**: 10 AM, 2 PM, 5 PM check-ins

## Troubleshooting

```bash
# If you get conflicts
git fetch origin
git rebase origin/main

# If another agent has a lock you need
just show-locks  # See who has it
# Contact them or wait

# If tests fail in CI but not locally
just test-agent  # Run your tests
# Check if you modified services outside your scope

# If you're unsure what to work on
just agent-tasks  # Check Linear assignments
```

## Ready to Start!
1. Run setup script: `./scripts/setup-all-agents.sh`
2. Open 4 Warp windows
3. Navigate to each worktree
4. Run daily setup in each
5. Start coding with your assigned agent role!