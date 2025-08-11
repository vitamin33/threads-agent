# ⚠️ IMPORTANT: Where to Work

## The Golden Rule

**🚫 DON'T develop in the main `threads-agent` folder**
**✅ DO develop in your assigned worktree folder**

## Why?

The main `threads-agent` folder is for:
- Running setup scripts
- Checking overall status
- Managing the repository
- Pulling latest changes from GitHub

The worktree folders (`wt-a1-mlops`, etc.) are for:
- **ALL your development work**
- Writing code
- Running tests
- Creating commits
- Pushing branches

## Your Workflow

### ❌ WRONG Way
```bash
cd /Users/vitaliiserbyn/development/threads-agent
# Edit files here
# Create branches here
# This causes conflicts!
```

### ✅ RIGHT Way
```bash
# Agent A1 works here:
cd /Users/vitaliiserbyn/development/wt-a1-mlops
# All development happens here
# This is YOUR workspace

# Agent A2 works here:
cd /Users/vitaliiserbyn/development/wt-a2-genai
# Completely separate from A1

# etc...
```

## Think of it Like This

```
threads-agent/          = The "control center" (don't code here)
├── scripts/           = Setup and management tools
├── docs/              = Documentation
└── .git/              = Main git repository

wt-a1-mlops/           = Agent A1's "office" (code here!)
├── services/          = Edit these files
├── AGENT_FOCUS.md     = Your responsibilities (local)
├── .agent.env         = Your config (local)
└── .venv/             = Your Python environment

wt-a2-genai/           = Agent A2's "office" (separate)
wt-a3-analytics/       = Agent A3's "office" (separate)
wt-a4-platform/        = Agent A4's "office" (separate)
```

## Daily Workflow Example

### Morning Setup
```bash
# 1. Check status from main repo
cd /Users/vitaliiserbyn/development/threads-agent
./scripts/agent-status.sh

# 2. Go to YOUR worktree
cd /Users/vitaliiserbyn/development/wt-a1-mlops

# 3. Start Claude Code HERE
source .venv/bin/activate
source .agent.env
claude
```

### During Development
```bash
# You're in wt-a1-mlops
git status           # Shows YOUR changes
git add .            # Adds YOUR files
git commit           # Creates YOUR commit
git push             # Pushes YOUR branch
```

### Coordination Tasks
```bash
# Only go back to main for management tasks
cd ../threads-agent
./scripts/agent-lock.sh a1 lock    # Lock common files
./scripts/agent-status.sh          # Check all agents
```

## Key Points

1. **Each worktree is a complete copy** of the repository
2. **Changes in one worktree don't affect others** until merged
3. **You can edit the SAME files** without conflicts (git handles it)
4. **Local files (AGENT_FOCUS.md, .agent.env) stay separate**

## Quick Reference

| Task | Where to Do It |
|------|---------------|
| Write code | Worktree (wt-a1-mlops) |
| Run tests | Worktree (wt-a1-mlops) |
| Create commits | Worktree (wt-a1-mlops) |
| Push branches | Worktree (wt-a1-mlops) |
| Check agent status | Main repo (threads-agent) |
| Run setup scripts | Main repo (threads-agent) |
| Update from GitHub | Main repo first, then rebase worktrees |

## The Big Picture

```
GitHub
  ↓ (pull)
threads-agent (main)
  ↓ (worktrees)
┌─────────────┬─────────────┬─────────────┬─────────────┐
wt-a1-mlops  wt-a2-genai  wt-a3-analytics wt-a4-platform
(develop)    (develop)    (develop)       (develop)
  ↓ (push)     ↓ (push)     ↓ (push)       ↓ (push)
GitHub PRs → Merge to main
```

## Summary

- **Main repo** = Management only
- **Worktrees** = Development only
- **Never mix the two!**

This separation is what enables 4 agents to work in parallel without conflicts!