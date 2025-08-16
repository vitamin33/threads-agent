# 🚀 4-Agent Parallel Development Guide

## Quick Start

Run this single command to set up everything:
```bash
./setup-4-agents.sh
```

This creates 4 isolated worktrees, each with its own:
- Git branch
- Python virtual environment
- Port range (no conflicts)
- Database schema
- Local configuration files

## Your 4 Parallel Agents

### Agent A1 - MLOps (Ports 8080-8099)
- **Worktree**: `../wt-a1-mlops`
- **Services**: orchestrator, celery_worker, persona_runtime
- **Focus**: Core pipeline, MLflow integration, SLO gates
- **Database**: `agent_a1` schema

### Agent A2 - GenAI (Ports 8180-8199)
- **Worktree**: `../wt-a2-genai`
- **Services**: viral_engine, rag_pipeline, vllm_service
- **Focus**: AI/ML optimization, vLLM, cost reduction
- **Database**: `agent_a2` schema

### Agent A3 - Analytics (Ports 8280-8299)
- **Worktree**: `../wt-a3-analytics`
- **Services**: achievement_collector, dashboard_api, finops_engine
- **Focus**: Portfolio generation, business metrics, dashboards
- **Database**: `agent_a3` schema

### Agent A4 - Platform (Ports 8380-8399)
- **Worktree**: `../wt-a4-platform`
- **Services**: revenue, event_bus, threads_adaptor
- **Focus**: A/B testing, monetization, event architecture
- **Database**: `agent_a4` schema

## Working with Claude Code

### For Each Claude Session

1. **Navigate to your worktree**:
```bash
cd ../wt-a1-mlops  # or a2, a3, a4
```

2. **Activate environment**:
```bash
source .venv/bin/activate
source .agent.env  # Sets AGENT_ID, ports, etc.
```

3. **Your agent identity is set**:
- `AGENT_ID` environment variable tells you who you are
- `AGENT_FOCUS.md` describes your responsibilities
- `.agent.env` contains your configuration

### Coordination Rules

#### Working on Common Files

When modifying `/services/common/*`:

1. **Check for locks**:
```bash
ls .locks/
```

2. **Create lock** (if available):
```bash
touch .locks/.common-lock-a1  # Replace a1 with your agent ID
```

3. **Make changes**

4. **Remove lock**:
```bash
rm .locks/.common-lock-a1
```

#### Database Changes

Only Agent A1 can modify database schema (owns Alembic migrations).
Other agents submit requests via:
```python
# services/orchestrator/db/migration_queue.py
submit_migration(agent_id="a2", sql="ALTER TABLE...", priority=1)
```

## Git Workflow

### Branch Naming
```
feat/<agent_id>/<feature>
Example: feat/a1/mlflow-integration
```

### Creating PRs
```bash
# Commit your changes
git add .
git commit -m "feat: your feature description"

# Push to your branch
git push origin feat/a1/main

# Create PR with agent tag
gh pr create \
  --title "[A1] Your feature" \
  --body "Description" \
  --label "auto-merge"
```

### Syncing with Main
```bash
# Fetch latest
git fetch origin main

# Rebase your branch
git rebase origin/main

# Force push if needed
git push --force-with-lease
```

## Important Files

### Local Files (Never Committed)
These files are in `.gitignore` and stay local:
- `AGENT_FOCUS.md` - Your responsibilities
- `.agent.env` - Your configuration
- `*.local` - Any local notes
- `.locks/` - Coordination locks

### Shared Files (Careful!)
These affect all agents:
- `/services/common/*.py` - Use locks
- `/requirements.txt` - Coordinate changes
- `/helm/` - Deployment configs

## Resource Allocation

### Memory Usage
- **A1**: 4GB (standard services)
- **A2**: 12GB (BERT models, transformers)
- **A3**: 3GB (lightweight analytics)
- **A4**: 3GB (platform services)

### API Rate Limits
Configure separate OpenAI keys:
```bash
export OPENAI_API_KEY_A1=sk-proj-xxx  # 10K TPM
export OPENAI_API_KEY_A2=sk-proj-yyy  # 20K TPM (AI heavy)
export OPENAI_API_KEY_A3=sk-proj-zzz  # 5K TPM
export OPENAI_API_KEY_A4=sk-proj-www  # 5K TPM
```

## Testing

### Run Your Service Tests
```bash
# In your worktree
pytest services/your_service/tests/
```

### Integration Testing
```bash
# Start your services
just dev-start

# Run integration tests
just e2e
```

## Monitoring

### Check All Agents Status
```bash
# From main repo
./agent-status.sh
```

### Check Your Services
```bash
kubectl get pods | grep <your-service>
kubectl logs <your-service-pod>
```

## Troubleshooting

### Port Conflicts
Each agent has 100-port range:
- A1: 8080-8099
- A2: 8180-8199
- A3: 8280-8299
- A4: 8380-8399

### Database Issues
Check your schema:
```sql
SET search_path TO agent_a1, public;  -- Use your agent's schema
```

### Git Conflicts
Always rebase, don't merge:
```bash
git fetch origin main
git rebase origin/main
```

### Lock Conflicts
If common files are locked:
```bash
ls .locks/  # See who has the lock
# Wait or coordinate with that agent
```

## Best Practices

1. **Small, Focused PRs**: Keep changes under 300 lines
2. **Frequent Rebasing**: Every 2-3 hours minimum
3. **Clear Commit Messages**: Include your agent ID
4. **Test Locally First**: Before pushing
5. **Respect Boundaries**: Stay in your assigned services
6. **Communicate via PRs**: Document your changes well

## Success Metrics

- **Velocity**: 1-2 PRs per agent per day
- **Conflicts**: <2 per week
- **Build Time**: <5 minutes
- **Test Coverage**: >80%
- **Integration Success**: >95%

## Quick Reference

```bash
# Your identity
echo $AGENT_ID

# Your services
echo $AGENT_SERVICES

# Your ports
echo $PORT_OFFSET

# Lock common files
touch .locks/.common-lock-$AGENT_ID

# Unlock
rm .locks/.common-lock-$AGENT_ID

# Create PR
gh pr create --title "[$AGENT_ID] Feature"

# Sync with main
git rebase origin/main
```

## Need Help?

1. Check `AGENT_FOCUS.md` in your worktree
2. Run `./agent-status.sh` for overall status
3. Review this guide
4. Check PR comments for coordination

---

**Remember**: You're one of 4 parallel agents. Stay in your lane, use locks for common files, and create focused PRs. This setup enables 4x development velocity!