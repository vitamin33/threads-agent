# CLAUDE.md - Threads-Agent Stack Development Guide

> **🚀 AI-Powered Development**: From idea to shipped code in minutes with GPT-4 planning + auto-git workflow.
> **Quick Start**: `export OPENAI_API_KEY=your-key && ./scripts/workflow-automation.sh ai-plan "your idea"`

## 🎯 Daily Development Workflow

### Essential Commands (4 Core Commands)
| Command | Purpose | Example |
|---------|---------|---------|
| `ai-plan` | AI creates project plan | `./scripts/workflow-automation.sh ai-plan "user auth"` |
| `tasks start` | Begin working (auto-branch) | `./scripts/workflow-automation.sh tasks start task_001` |
| `tasks commit` | Enhanced commit + push | `./scripts/workflow-automation.sh tasks commit task_001 "add middleware"` |
| `tasks ship` | Create PR automatically | `./scripts/workflow-automation.sh tasks ship task_001` |

### Complete Workflow Example
```bash
# 1. Plan feature
./scripts/workflow-automation.sh ai-plan "Build payment processing"

# 2. Start task
./scripts/workflow-automation.sh tasks start task_001

# 3. Code + commit
./scripts/workflow-automation.sh tasks commit task_001 "implement stripe"

# 4. Ship & complete
./scripts/workflow-automation.sh tasks ship task_001
./scripts/workflow-automation.sh tasks complete task_001
```

## Project Overview

**Threads-Agent Stack**: Production-grade AI agent system for content generation
- **Architecture**: Microservices on Kubernetes with LangGraph + OpenAI
- **Goal**: 6%+ engagement, $0.01/follow, $20k MRR
- **Tech**: Python 3.12+, FastAPI, Celery, k3d, PostgreSQL, Qdrant

### KPIs
- Engagement Rate: 6%+ (`posts_engagement_rate`)
- Cost/Follow: $0.01 (`cost_per_follow_dollars`)
- Monthly Revenue: $20k MRR (`revenue_projection_monthly`)

## Architecture

### Services
```
services/
├── orchestrator/    # FastAPI coordinator + Search APIs
├── celery_worker/   # Background processor + SSE
├── persona_runtime/ # LangGraph with LLM + Search
├── fake_threads/    # Mock API for testing
└── common/         # Shared utilities
```

### Core Stack
- **Infrastructure**: k3d, Kubernetes, Helm
- **Data**: PostgreSQL, Qdrant, RabbitMQ
- **Monitoring**: Prometheus, Grafana, Jaeger, AlertManager
- **AI**: OpenAI API, SearXNG search
- **MCP Servers**: Redis, K8s, PostgreSQL, Slack, GitHub

## Quick Start

```bash
git clone git@github.com:threads-agent-stack/threads-agent.git
cd threads-agent

# For parallel development with 4 Claude Code instances:
./setup-4-agents.sh  # Creates 4 isolated worktrees

# For regular development:
just dev-start  # Starts everything!
```

### 🎯 MEGA Commands (80/20 Rule)
```bash
just work-day       # Morning: Start env + dashboards
just create-viral   # Work: AI creates viral content
just ship-it        # Deploy: Test + Deploy + PR
just end-day        # Evening: Analyze + optimize
just make-money     # Autopilot mode
```

### Key Development Commands
- `just dev-start` - Bootstrap + Deploy + MCP + Dashboard
- `just logs` - View service logs
- `just unit` - Run unit tests
- `just e2e` - Run integration tests
- `just ship "message"` - Commit + push + PR
- `just reset-hard` - Nuclear reset

### Search & Trends
- `just trend-check "topic"` - Find trends
- `just competitive-analysis "topic"` - Analyze viral patterns
- `just search-enhanced-post "persona" "topic"` - Generate with trends

### MCP Usage
```bash
just cache-set "key" "value"    # Redis cache
just cache-get "key"            # Retrieve data
just mcp-setup                  # Setup all servers
```

## Testing Strategy

### Organization
```
tests/
├── e2e/        # Integration tests
├── unit/       # Cross-service tests
└── test_sanity.py

services/*/tests/  # Service-specific tests
```

### Markers
- `@pytest.mark.e2e` - Tests requiring k3d cluster
- Default - Fast unit tests

## Database & Models

### PostgreSQL (Centralized Migrations)
- **Location**: `services/orchestrator/db/alembic/`
- **Pattern**: ALL migrations in orchestrator service
- **Convention**: `add_{service}_tables.py`

### Models
```python
class Post:
    id, persona_id, hook, body, tokens_used, ts

class Task:
    id, payload, status
```

### Qdrant
- Collections: `posts_{persona_id}`
- Purpose: Semantic deduplication

## Service Details

### Orchestrator
- `POST /task` - Queue generation
- `POST /search/trends` - Find trends
- `GET /metrics` - Prometheus

### Celery Worker
- Task: `queue_post`
- Features: SSE progress updates

### Persona Runtime
- Workflow: ingest → trend_research → hook → body → guardrail → format
- Models: `HOOK_MODEL` (gpt-4o), `BODY_MODEL` (gpt-3.5-turbo)

### Environment Variables
```bash
# Core
OPENAI_API_KEY      # Use "test" for offline
RABBITMQ_URL        # Celery broker
DATABASE_URL        # PostgreSQL
QDRANT_URL          # Vector store
SEARXNG_URL         # Search engine

# Models
HOOK_MODEL          # Default: gpt-4o
BODY_MODEL          # Default: gpt-3.5-turbo-0125
```

## Monitoring

### Prometheus Metrics
- `request_latency_seconds` - Pipeline timing
- `posts_engagement_rate` - Engagement tracking
- `cost_per_follow_dollars` - Cost efficiency
- `search_requests_total` - Search usage

### Dashboards
- `just grafana` - Business & technical metrics
- `just jaeger-ui` - Distributed tracing

### Alerts (AlertManager)
- **Critical**: PagerDuty (service down, high errors)
- **Warning**: Slack (latency, costs)
- **Business**: Email (engagement, revenue)

## Development Best Practices

### Git Workflow & Branch Strategy (Solo Dev + 4 AI Agents)

**Branch Naming for Parallel Development**:
```
<type>/<area>/<feature>__<agent>
Examples:
- feat/mlops/mlflow-slo-gates__a1
- feat/genai/vllm-optimize__a2
- fix/achieve/portfolio-bug__a3
- perf/revenue/ab-testing__a4
```

**Worktree Setup (4 Parallel Claude Sessions)**:
```bash
# Each agent works in separate worktree
wt-a1-mlflow-slo    → Agent 1 (MLOps/SLO)
wt-a2-vllm-cost     → Agent 2 (GenAI/RAG)
wt-a3-portfolio     → Agent 3 (Achievement)
wt-a4-ab-testing    → Agent 4 (Revenue/AB)
```

**Solo Dev Optimizations**:
- No PR reviews required (auto-merge on green CI)
- Direct push to branches
- Shared Docker services (use DB_SCHEMA for isolation)
- Light coordination via .common-lock files
- **Pre-Push**: Run `just check` before push

### Configuration Management (CRITICAL)
**Centralized config for all services - prevents deployment failures:**
- **Database**: Use `services/common/database_config.py` or Helm helpers
- **ML/AI**: Use `services/common/ml_config.py` for model configs
- **Helm**: Use `{{ include "threads.postgres.dsn" . }}` for DB strings
- **Env vars**: `DATABASE_URL` (standard) or `POSTGRES_DSN` (SQLAlchemy)
- **Defaults**: `postgres:pass@postgres:5432/threads_agent`
- **CI Fix**: Wrap DB imports in try/except for resilience
- **Docs**: See `docs/DATABASE_CONFIGURATION.md` for full guide

### Auto-Commit System (Working State Protection)
Keep your code in a known-good state with automatic checkpoints:

**Quick Commands:**
```bash
just checkpoint          # Create checkpoint commit (runs tests first)
just checkpoint-push     # Checkpoint + push to remote
just safe-dev           # Auto-commit every 30 minutes
```

**Features:**
- **Test-Driven Commits**: Only commits when tests pass
- **Pre-Push Hook**: Blocks pushing broken code
- **Safe Development Mode**: Auto-checkpoints every 30 minutes
- **Emergency Override**: `SKIP_TESTS=1 git push` (use sparingly!)

**Usage Examples:**
```bash
# Before risky changes
just checkpoint "before major refactor"

# Regular development
just safe-dev  # Runs in background, commits every 30 min

# End of coding session
just checkpoint-push "completed feature X"
```

**Commit Format:**
```
[auto-commit] ✅ Working state - all tests passing

Branch: feature/new-feature
Timestamp: 2024-01-15 14:30:00
Test Status: PASSED
```

### AI-Powered Planning
```bash
# Create epic with AI
./scripts/workflow-automation.sh ai-plan "feature idea"

# Auto-git integration
./scripts/workflow-automation.sh tasks start task_001
./scripts/workflow-automation.sh tasks commit task_001 "changes"
./scripts/workflow-automation.sh tasks ship task_001
```

### Code Quality
- Type checking: mypy strict
- Formatting: ruff + black + isort
- Pre-commit: via `just ship`
- **Testing Requirements**:
  - Every new feature MUST be tested on local k3d cluster
  - Helm charts MUST be updated for new services/features
  - Run `just check` before creating PR
  - Verify health endpoints are accessible

## Troubleshooting

### Common Issues
```bash
# k3d issues
just k3d-nuke-all && just bootstrap

# Test failures
just e2e-prepare

# Port forwarding
kubectl port-forward svc/orchestrator 8080:8080
```

## Productivity Features

### Time Saved (Per Week)
1. **MCP Servers**: 10-12 hours
2. **Search Integration**: 5-6 hours
3. **AI Tools**: 8-10 hours
4. **Monitoring**: 2-3 hours

### Essential Commands
```bash
# Development
just dev-start
just persona-hot-reload
just ai-test-gen

# Deployment
just smart-deploy canary
just grafana
```

## AI Token Efficiency

### Optimization
```bash
just token-optimize  # Enable all optimizations
just cached-analyze  # 0 tokens (cached)
just token-batch     # Batch processing (80% savings)
```

### Strategies
1. Smart Caching (60-70% savings)
2. Batch Processing (30-40% savings)
3. Template Generation (40-50% savings)

## 🚀 Parallel AI Agent Development (4 Claude Code Instances)

### Quick Setup
```bash
# One command to set up 4 parallel development environments
./setup-4-agents.sh
```

This creates 4 isolated worktrees with no conflicts:
- **No port conflicts** - Each agent has 100-port range
- **No database conflicts** - Separate schemas per agent
- **No file conflicts** - Local config files never committed
- **No merge conflicts** - Agent-specific files in .gitignore

### Your 4 Parallel Agents - Specialized Development Vectors

#### **Agent A1 - MLOps/Orchestrator** (`../wt-a1-mlops`)
```yaml
Services: orchestrator, celery_worker, persona_runtime
Focus Areas: MLflow, SLO-gates, monitoring, performance
Job Targets: MLOps Engineer, Platform Engineer, SRE
Portfolio Priority:
  - MLflow registry with 2+ model versions
  - SLO-gated CI demo (p95 < 500ms)
  - Grafana dashboards with drift detection
Keywords: MLflow, Prometheus, Grafana, latency, reliability, rollback
```

#### **Agent A2 - GenAI/RAG** (`../wt-a2-genai`)
```yaml
Services: rag_pipeline, vllm_service, viral_engine
Focus Areas: vLLM, RAG, embeddings, token-optimization
Job Targets: GenAI Engineer, LLM Specialist, AI/ML Engineer
Portfolio Priority:
  - vLLM cost reduction (60% savings)
  - RAG accuracy metrics
  - Token optimization dashboard
Keywords: vLLM, Qdrant, embeddings, Llama, semantic, cost
```

#### **Agent A3 - Analytics/Documentation** (`../wt-a3-analytics`)
```yaml
Services: achievement_collector, tech_doc_generator, dashboard_api
Focus Areas: portfolio, documentation, achievements, visualization
Job Targets: Technical Writer, Data Analyst, Developer Advocate
Portfolio Priority:
  - Achievement report from PRs
  - Technical documentation
  - Portfolio website
Keywords: portfolio, impact, metrics, visualization, documentation
```

#### **Agent A4 - Platform/Revenue** (`../wt-a4-platform`)
```yaml
Services: revenue, finops_engine, event_bus, threads_adaptor
Focus Areas: A/B-testing, revenue, cost-optimization, platform
Job Targets: Platform Engineer, Growth Engineer, FinOps Engineer
Portfolio Priority:
  - A/B test results with significance
  - Revenue dashboard ($20k MRR)
  - FinOps cost savings (30%)
Keywords: A/B testing, MRR, CAC, FinOps, event-driven, platform
```

### Working in Your Worktree

1. **Navigate to your worktree**:
```bash
cd ../wt-a1-mlops  # or a2-genai, a3-analytics, a4-platform
```

2. **Activate environment**:
```bash
source .venv/bin/activate
source .agent.env  # Sets AGENT_ID, ports, schema
```

3. **Check your identity**:
```bash
echo $AGENT_ID      # Shows a1, a2, a3, or a4
cat AGENT_FOCUS.md  # Your responsibilities (local file)
```

### Coordination Rules

#### Modifying Common Files
```bash
# Check if locked
ls .locks/

# Lock for your agent
touch .locks/.common-lock-$AGENT_ID

# Make changes to /services/common/*

# Unlock when done
rm .locks/.common-lock-$AGENT_ID
```

#### Database Changes
- Only A1 modifies schema (owns Alembic)
- Others submit migration requests

#### Creating PRs
```bash
# Your branch naming: feat/<agent_id>/<feature>
git checkout -b feat/a1/mlflow-integration

# Commit and push
git add .
git commit -m "feat: mlflow integration"
git push origin feat/a1/mlflow-integration

# Create PR with agent tag
gh pr create --title "[A1] MLflow integration" --label "auto-merge"
```

### Instructions for Claude Code Sessions

When starting a new Claude Code session in a worktree, tell Claude:

```markdown
I am working in Agent A1 worktree focused on MLOps.
My services: orchestrator, celery_worker, persona_runtime
My focus: MLflow, SLO-gates, monitoring, performance
Ignore: rag_pipeline, achievement_collector, revenue services
Job priority: Build MLflow demos and SLO gate artifacts for MLOps Engineer roles
```

This ensures Claude understands:
1. Which services to work on
2. Which to ignore completely
3. What portfolio artifacts to prioritize
4. Which job roles to optimize for

### Important: Local Files Never Commit

These files are LOCAL ONLY (in .gitignore):
- `AGENT_FOCUS.md` - Your complete planning document (identity, tasks, progress)
- `.agent.env` - Your runtime configuration
- `.ai-context.json` - AI planning context
- `*.local` - Any local notes
- `.locks/` - Coordination locks

This prevents merge conflicts between agents!

## AI Guidelines

### Feature Development with Sub-Agents (MANDATORY)
- **ALL feature development MUST use specialized sub-agents**
- **NEVER implement features directly - always delegate to appropriate agents**
- **Required workflow for ANY feature/task development:**
  1. Analyze the task requirements
  2. Identify which specialized agents are needed
  3. Launch agents in parallel when possible for maximum efficiency
  4. Coordinate results and ensure integration

### Sub-Agent Usage Patterns

#### Feature Development Workflow (MANDATORY ORDER):
1. **`epic-planning-specialist`** - Break down requirements into actionable tasks
2. **`tdd-master`** - Create failing tests BEFORE any implementation
3. **Implementation** - Write code to make tests pass
4. **`k8s-performance-optimizer`** - Optimize code for production
5. **`test-generation-specialist`** - Add edge cases and integration tests
6. **`devops-automation-expert`** - Create/update deployment configurations
7. **`tech-documentation-generator`** - Generate comprehensive documentation

#### Specialized Workflows:
- **Bug Fixes**: `tdd-master` (reproduce bug) → Fix → `test-generation-specialist`
- **Performance Issues**: `k8s-performance-optimizer` → `tdd-master` → Implementation
- **Infrastructure**: `devops-automation-expert` → `k8s-performance-optimizer`
- **Documentation Only**: `tech-documentation-generator`

#### Parallel Agent Execution:
When tasks are independent, launch agents in parallel:
```bash
# Example: After implementation
- k8s-performance-optimizer (optimize code)
- test-generation-specialist (create tests)  
- devops-automation-expert (update configs)
# All three can run simultaneously
```

### Benefits of Sub-Agent Development
1. **Parallel execution** - Multiple agents work simultaneously
2. **Specialized expertise** - Each agent excels in their domain
3. **Higher quality** - Deep expertise in specific areas
4. **Comprehensive coverage** - Nothing gets missed
5. **Faster delivery** - Parallel work completes faster than sequential

### Example Multi-Agent Workflow
```bash
# For a new microservice feature:
1. epic-planning-specialist: Break down requirements
2. tdd-master: Create test-first implementation
3. k8s-performance-optimizer: Optimize the code
4. test-generation-specialist: Ensure full test coverage
5. devops-automation-expert: Create deployment configs
6. tech-documentation-generator: Document everything
```

### Collaboration Practices
- **CRITICAL: NEVER add Claude as co-author in git commits**
- **NEVER include "🤖 Generated with [Claude Code]" in commits**
- **NEVER include "Co-Authored-By: Claude <noreply@anthropic.com>" in commits**
- Git commits should ONLY have the actual developer as author
- This is a strict requirement - no exceptions

### Development Environment
- **ALWAYS use virtual environments** for Python services (venv contains all dependencies)
- Without venv: ModuleNotFoundError, command not found (pytest, mypy, etc.)

## Resources

- **[DAILY_PLAYBOOK.md](./docs/DAILY_PLAYBOOK.md)** - Daily cheat sheet
- **[PRODUCTIVITY_GUIDE.md](./docs/PRODUCTIVITY_GUIDE.md)** - Full productivity guide
- **[docs/](./docs/)** - Additional documentation

---

**Repository**: https://github.com/threads-agent-stack/threads-agent
**Last Updated**: 2025-01-25
- dont forget to write testable clean code but not overcomplicate, use approach which best fit for               │
│   solopreneuers, this is important