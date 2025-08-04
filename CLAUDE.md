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

### Git Workflow
- Branch: `task-{epic-id}-{title}`
- Protection: PR + CI required
- Automation: `just ship` handles all
- **Pre-Push Checklist**:
  - Before every push 'just check' command should be fully successful
- When working on a Linear task, create a git branch starting with the task number (e.g., for task CRA-331, branch name should be 'cra-331-title-of-task')

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

## AI Guidelines

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