# 🚀 Warp Terminal + Claude Code Setup Guide

## Your Worktrees Are Ready!

The worktrees already exist in your development folder:
```
/Users/vitaliiserbyn/development/
├── threads-agent/          (main repo - you are here)
├── wt-a1-mlops/           (Agent 1 worktree)
├── wt-a2-genai/           (Agent 2 worktree)
├── wt-a3-analytics/       (Agent 3 worktree)
└── wt-a4-platform/        (Agent 4 worktree)
```

## How to Open 4 Claude Code Instances in Warp

### Method 1: Using Warp Splits (Recommended)

1. **Open Warp Terminal**

2. **Create 4 splits**:
   - Press `Cmd+D` to split vertically (or `Cmd+Shift+D` for horizontal)
   - Repeat until you have 4 panes
   - Or use Warp's "Launch Configuration" for a saved layout

3. **In each pane, navigate to a different worktree**:

**Pane 1 (Agent A1 - MLOps):**
```bash
cd /Users/vitaliiserbyn/development/wt-a1-mlops
source .venv/bin/activate
source .agent.env
claude  # or 'claude-code' depending on your CLI name
```

**Pane 2 (Agent A2 - GenAI):**
```bash
cd /Users/vitaliiserbyn/development/wt-a2-genai
source .venv/bin/activate
source .agent.env
claude
```

**Pane 3 (Agent A3 - Analytics):**
```bash
cd /Users/vitaliiserbyn/development/wt-a3-analytics
source .venv/bin/activate
source .agent.env
claude
```

**Pane 4 (Agent A4 - Platform):**
```bash
cd /Users/vitaliiserbyn/development/wt-a4-platform
source .venv/bin/activate
source .agent.env
claude
```

### Method 2: Using Warp Tabs

1. **Open 4 new tabs** in Warp (`Cmd+T`)

2. **In each tab**, run the commands above for each agent

3. **Name your tabs** (right-click on tab):
   - Tab 1: "A1-MLOps"
   - Tab 2: "A2-GenAI"
   - Tab 3: "A3-Analytics"
   - Tab 4: "A4-Platform"

### Method 3: Warp Launch Configuration (Best for Daily Use)

Create a Warp Launch Configuration to automate this:

1. **Create configuration file**:
```bash
cat > ~/.warp/launch_configs/4-agents.yaml <<'EOF'
name: "4 Claude Agents"
windows:
  - tabs:
    - name: "A1-MLOps"
      panes:
        - commands:
          - "cd /Users/vitaliiserbyn/development/wt-a1-mlops"
          - "source .venv/bin/activate"
          - "source .agent.env"
          - "echo 'Agent A1 Ready - MLOps/Orchestrator'"
          - "claude"
    - name: "A2-GenAI"
      panes:
        - commands:
          - "cd /Users/vitaliiserbyn/development/wt-a2-genai"
          - "source .venv/bin/activate"
          - "source .agent.env"
          - "echo 'Agent A2 Ready - GenAI/RAG'"
          - "claude"
    - name: "A3-Analytics"
      panes:
        - commands:
          - "cd /Users/vitaliiserbyn/development/wt-a3-analytics"
          - "source .venv/bin/activate"
          - "source .agent.env"
          - "echo 'Agent A3 Ready - Analytics/Achievements'"
          - "claude"
    - name: "A4-Platform"
      panes:
        - commands:
          - "cd /Users/vitaliiserbyn/development/wt-a4-platform"
          - "source .venv/bin/activate"
          - "source .agent.env"
          - "echo 'Agent A4 Ready - Platform/Revenue'"
          - "claude"
EOF
```

2. **Launch with**: Open Warp → File → Open Launch Configuration → Select "4 Claude Agents"

## Quick Verification

After opening Claude Code in each worktree, verify the agent knows its identity:

**In each Claude session, ask:**
```
What is my AGENT_ID and what services am I responsible for?
```

**Expected responses:**
- A1: "AGENT_ID=a1, responsible for orchestrator, celery_worker, persona_runtime"
- A2: "AGENT_ID=a2, responsible for viral_engine, rag_pipeline, vllm_service"
- A3: "AGENT_ID=a3, responsible for achievement_collector, dashboard_api, finops_engine"
- A4: "AGENT_ID=a4, responsible for revenue, event_bus, threads_adaptor"

## One-Line Setup Commands

For quick copy-paste into each Warp pane:

```bash
# Agent A1
cd /Users/vitaliiserbyn/development/wt-a1-mlops && source .venv/bin/activate && source .agent.env && claude

# Agent A2
cd /Users/vitaliiserbyn/development/wt-a2-genai && source .venv/bin/activate && source .agent.env && claude

# Agent A3
cd /Users/vitaliiserbyn/development/wt-a3-analytics && source .venv/bin/activate && source .agent.env && claude

# Agent A4
cd /Users/vitaliiserbyn/development/wt-a4-platform && source .venv/bin/activate && source .agent.env && claude
```

## Important Notes

1. **Each Claude instance is isolated** - They work in different directories
2. **Environment variables are set** - Each knows its AGENT_ID
3. **No conflicts** - Different ports, schemas, and branches
4. **Local files don't sync** - AGENT_FOCUS.md stays local

## Troubleshooting

### "Directory not found"
The worktrees are at the SAME level as threads-agent, not inside it:
```
/Users/vitaliiserbyn/development/wt-a1-mlops  ✅ Correct
/Users/vitaliiserbyn/development/threads-agent/wt-a1-mlops  ❌ Wrong
```

### "Claude command not found"
Check your Claude CLI installation:
```bash
which claude
# or
which claude-code
```

### "Permission denied"
Make sure Python venv is activated:
```bash
source .venv/bin/activate
```

## Daily Workflow

1. **Morning**: Open Warp, use launch configuration
2. **Check status**: Run `./scripts/agent-status.sh` from main repo
3. **Develop**: Each agent works independently
4. **Sync**: Periodically run `git rebase origin/main` in each worktree
5. **End of day**: Commit and push changes from each agent

## Success!

You now have 4 parallel Claude Code instances ready to work without conflicts!