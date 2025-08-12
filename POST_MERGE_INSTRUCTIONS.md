# 📋 Post-Merge Instructions for 4-Agent System

## After PR #108 is Merged

### Step 1: Update Main Repository
```bash
git checkout main
git pull origin main
```

### Step 2: Update Each Worktree

#### Window 1 - Agent A1 (MLOps)
```bash
cd /Users/vitaliiserbyn/development/wt-a1-mlops
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/a1/mlops-portfolio
source .agent.env
just ai-morning
```

#### Window 2 - Agent A2 (GenAI)
```bash
cd /Users/vitaliiserbyn/development/wt-a2-genai
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/a2/vllm-optimization
source .agent.env
just ai-morning
```

#### Window 3 - Agent A3 (Analytics)
```bash
cd /Users/vitaliiserbyn/development/wt-a3-analytics
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/a3/portfolio-site
source .agent.env
just ai-morning
```

#### Window 4 - Agent A4 (Platform)
```bash
cd /Users/vitaliiserbyn/development/wt-a4-platform
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/a4/ab-testing
source .agent.env
just ai-morning
```

## Daily Commands Reference

### Morning Routine
```bash
just ai-morning        # Full AI routine with task planning
just focus-status      # Check current tasks
just real-metrics      # Verify real data
```

### During Work
```bash
just focus-complete "task name"  # Mark task done
just focus-update              # Update progress
just dashboard                 # Check all agents
```

### Job Applications
```bash
just job-status                # Daily check
just job-track "Company" "Role" # Track application
just proof-pack                # Check portfolio
```

### Evening Routine
```bash
just ai-evening        # Wrap up day
just pr-portfolio "title" # Create PR with context
```

## Priority First Tasks

### A1 - MLOps (Quickest Portfolio Wins)
1. `mlflow server --backend-store-uri sqlite:///mlflow.db`
2. `just mlflow-train`
3. Take screenshot → `.portfolio/mlflow_registry.png`

### A2 - GenAI (Cost Proof)
1. Deploy vLLM service
2. Run benchmark
3. Generate cost table

### A3 - Analytics (Portfolio Site)
1. `just collect-achievements`
2. Generate documentation
3. Build portfolio landing

### A4 - Platform (A/B Testing)
1. Setup A/B framework
2. Run first test
3. Generate results

## Remember
- AGENT_FOCUS.md is your task list (never commit it)
- Real metrics only - no fake data
- Every PR should add portfolio value
- Target: $160-220k remote AI roles

Ready to start after merge!