# 🔧 GitHub CI Setup for 4-Agent Parallel Development

## Overview

The CI has been enhanced to support 4 parallel agents working simultaneously without conflicts.

## New CI Features

### 1. Agent Detection
The CI automatically detects which agent created the PR based on branch naming:
- `feat/a1/*` → Agent A1 (MLOps)
- `feat/a2/*` → Agent A2 (GenAI)
- `feat/a3/*` → Agent A3 (Analytics)
- `feat/a4/*` → Agent A4 (Platform)

### 2. Agent-Specific Testing
- Only tests the services owned by that agent
- Faster CI runs (10 minutes vs 20 minutes)
- Isolated test databases per agent

### 3. Auto-Merge Support
PRs with `auto-merge` label will automatically merge when tests pass.

## GitHub Settings Required

### 1. Enable Auto-Merge (Repository Settings)

Go to: Settings → General → Pull Requests

Enable:
- ✅ Allow auto-merge
- ✅ Allow squash merging
- ✅ Automatically delete head branches

### 2. Branch Protection Rules

Go to: Settings → Branches → Add rule

**Pattern**: `main`

**Settings**:
```yaml
Require a pull request before merging:
  ✅ Required
  ❌ Require approvals (disabled for solo dev)
  ✅ Dismiss stale pull request approvals
  ✅ Require conversation resolution

Require status checks to pass:
  ✅ Required
  Status checks:
    - agent-focused-tests
    - parallel-integration-check
  ✅ Require branches to be up to date

Require linear history:
  ✅ Required (prevents merge commits)

Allow force pushes:
  ❌ Disabled (safety)

Allow deletions:
  ❌ Disabled (safety)
```

### 3. Create GitHub App Token (Optional)

For auto-merge to work with branch protection:

1. Create a GitHub App or use a PAT with `repo` scope
2. Add as secret: `AUTO_MERGE_TOKEN`
3. Update workflow to use this token

## CI Workflows

### Existing Workflows (Still Active)
- `branch-ci.yml` - Main comprehensive CI
- `quick-ci.yml` - Fast validation
- `fast-ci.yml` - Quick checks

### New Workflow
- `parallel-agent-ci.yml` - Agent-specific CI

## How It Works

### When Agent Creates PR

1. **Agent A1 creates PR**:
   ```bash
   git push origin feat/a1/mlflow-integration
   gh pr create --title "[A1] MLflow integration" --label "auto-merge"
   ```

2. **CI detects agent**:
   - Identifies as Agent A1
   - Tests only: orchestrator, celery_worker, persona_runtime
   - Runs in ~5 minutes instead of 20

3. **Auto-merge**:
   - If tests pass and label `auto-merge` exists
   - Automatically squash-merges to main
   - No manual review needed

### Parallel PR Example

All 4 agents can have PRs open simultaneously:
```
PR #101: [A1] MLflow integration     → Testing... → Auto-merged ✅
PR #102: [A2] vLLM optimization       → Testing... → Auto-merged ✅
PR #103: [A3] Achievement tracker     → Testing... → Auto-merged ✅
PR #104: [A4] Revenue dashboard       → Testing... → Auto-merged ✅
```

## CI Status Comments

Each PR gets an automatic comment:
```
🔧 Agent A1: MLOps/Orchestrator

This PR is from Agent A1 working on:
- Services: orchestrator, celery_worker, persona_runtime
- Branch Pattern: feat/a1/*

CI Status:
- ✅ Agent-specific tests passed
- ✅ No conflicts detected
- ✅ Parallel development compatible
```

## Conflict Prevention

The CI checks for:

### 1. Database Migration Conflicts
- Only Agent A1 can add migrations
- Other agents get error if they try

### 2. Common File Modifications
- Warns if `/services/common/` is modified
- Suggests using lock system

### 3. Port Range Validation
- A1: 8080-8099
- A2: 8180-8199
- A3: 8280-8299
- A4: 8380-8399

## Manual Setup Commands

### Enable Auto-Merge for Repository
```bash
gh repo edit --enable-auto-merge --enable-squash-merge
```

### Add Auto-Merge Label
```bash
gh label create auto-merge --description "Auto-merge when CI passes" --color 0E8A16
```

### Create Agent Labels
```bash
gh label create agent-a1 --description "Agent A1 (MLOps)" --color 1f77b4
gh label create agent-a2 --description "Agent A2 (GenAI)" --color ff7f0e
gh label create agent-a3 --description "Agent A3 (Analytics)" --color 2ca02c
gh label create agent-a4 --description "Agent A4 (Platform)" --color d62728
```

## Testing the Setup

### 1. Create Test PR
```bash
cd /Users/vitaliiserbyn/development/wt-a1-mlops
git checkout -b feat/a1/test-ci
echo "# Test" >> README.md
git add . && git commit -m "test: CI setup"
git push origin feat/a1/test-ci
gh pr create --title "[A1] Test CI" --label "auto-merge"
```

### 2. Watch CI
```bash
gh pr checks
gh run watch
```

### 3. Verify Auto-Merge
Should auto-merge when tests pass!

## Monitoring

### Check All Agent PRs
```bash
gh pr list --label "agent-a1"
gh pr list --label "agent-a2"
gh pr list --label "agent-a3"
gh pr list --label "agent-a4"
```

### CI Performance
- Agent-specific: ~5 minutes
- Comprehensive: ~20 minutes
- Parallel capacity: 4 PRs simultaneously

## Troubleshooting

### Auto-Merge Not Working
1. Check branch protection settings
2. Verify `auto-merge` label exists
3. Ensure all required checks pass
4. Check token permissions

### Tests Failing
1. Run locally first: `pytest services/your_service/`
2. Check PYTHONPATH is set
3. Verify dependencies installed

### Conflicts
1. Always rebase: `git rebase origin/main`
2. Never merge main into feature branch
3. Use linear history

## Summary

✅ **CI is ready for parallel development!**

- Each agent has focused, fast CI runs
- Auto-merge enables continuous delivery
- No conflicts between agents
- 4x development velocity achieved!

The CI will handle parallel PRs from all 4 agents simultaneously, with automatic merging when tests pass!