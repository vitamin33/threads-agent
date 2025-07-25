# CLAUDE.md - Threads-Agent Stack Development Guide

> **🚀 AI-Powered Development**: From idea to shipped code in minutes with GPT-4 planning + auto-git workflow.
>
> **Quick Start**: `export OPENAI_API_KEY=your-key && ./scripts/workflow-automation.sh ai-plan "your idea"`

## 🎯 Quick Reference

### Essential Commands (Only 4 you need)
| Command | Purpose | Example |
|---------|---------|---------|
| `ai-plan` | AI creates project plan | `./scripts/workflow-automation.sh ai-plan "user auth"` |
| `tasks start` | Begin working (auto-branch) | `./scripts/workflow-automation.sh tasks start task_001` |
| `tasks commit` | Enhanced commit + push | `./scripts/workflow-automation.sh tasks commit task_001 "add middleware"` |
| `tasks ship` | Create PR automatically | `./scripts/workflow-automation.sh tasks ship task_001` |

### Development Quick Start
```bash
# One-time setup
just dev-start        # Starts everything locally
just dev-start-multi  # Multiple developers on same machine

# Daily workflow
just work-day         # Morning: Start everything + dashboards
just create-viral     # Work: AI creates viral content
just ship-it          # Deploy: Test + Deploy + PR
just end-day          # Evening: Analyze + optimize
```

## Project Overview

**Threads-Agent Stack** is a production-grade, multi-persona AI agent system that:
- Generates AI-powered Threads content with trend research
- Uses microservices on Kubernetes (k3d locally)
- Implements LangGraph workflows with OpenAI integration
- Goal: 6%+ engagement rate, $0.01 cost/follow, $20k MRR

### Architecture
```
services/
├── orchestrator/        # FastAPI + Celery dispatcher + Search APIs
├── celery_worker/      # Background tasks + SSE
├── persona_runtime/    # LangGraph DAG + LLM calls + Search
├── fake_threads/       # Mock Threads API
└── common/            # Shared utilities
```

### Core Technologies
- **Language**: Python 3.12+
- **Frameworks**: FastAPI, Celery, LangGraph, SQLAlchemy
- **Infrastructure**: k3d, Kubernetes, Helm
- **Databases**: PostgreSQL, Qdrant
- **Monitoring**: Prometheus, Grafana, Jaeger, AlertManager
- **Search**: SearXNG (free metasearch)
- **MCP Servers**: Redis, PostgreSQL, Kubernetes, OpenAI, SearXNG

## Development Workflow

### Prerequisites
- Docker >= 24, k3d >= 5.6, Helm >= 3.14
- Python 3.12+, just, npm

### Key Commands (justfile)

#### Development
- `just bootstrap[-multi]` - Create k3d cluster
- `just images` - Build Docker images
- `just deploy-dev` - Helm install
- `just logs` - View service logs
- `just unit` / `just e2e` - Run tests
- `just check` - Full quality gate
- `just ship "message"` - Commit → push → PR

#### Productivity Mega Commands
- `just dev-start` - One command full setup
- `just persona-hot-reload` - Instant persona testing
- `just ai-test-gen` - Generate tests automatically
- `just smart-deploy` - Deploy with auto-rollback
- `just trend-check` - Find trending topics
- `just search-enhanced-post` - Generate trend-aware content

#### MCP & Search
- `just mcp-setup` - Setup all MCP servers
- `just cache-set/get` - Redis operations
- `just searxng-start` - Start search engine
- `just competitive-analysis` - Analyze viral patterns

## Testing Strategy

```
tests/
├── e2e/              # Integration tests (k3d required)
├── unit/             # Cross-service unit tests
└── test_sanity.py    # Smoke tests

services/*/tests/     # Service-specific tests
```

- **Markers**: `@pytest.mark.e2e` for slow tests
- **Patterns**: E2E uses port-forwarding, unit uses test doubles

## Database & Models

### PostgreSQL
```python
class Post(Base):
    id, persona_id, hook, body, tokens_used, ts
    
class Task(Base):
    id, payload, status
```

### Qdrant
- Collections: `posts_{persona_id}`
- Purpose: Semantic deduplication

## Service Details

### Orchestrator Routes
- `POST /task` - Queue generation
- `GET /health`, `/metrics`
- `POST /search/trends` - Trending topics
- `POST /search/competitive` - Viral analysis
- `POST /search/enhanced-task` - Search-powered content

### Content Pipeline
1. **Standard**: ingest → hook → body → guardrail → format
2. **Enhanced**: ingest → trend_research → competitive_analysis → hook → body → guardrail → format

### Environment Variables
```bash
# Orchestrator
RABBITMQ_URL, DATABASE_URL, QDRANT_URL, SEARXNG_URL

# Persona Runtime
OPENAI_API_KEY="test"  # Offline mode
HOOK_MODEL="gpt-4o"
BODY_MODEL="gpt-3.5-turbo-0125"
```

## CI/CD Pipeline

- **Triggers**: PRs to main
- **Steps**: Setup → k3d → Build → Deploy → Test → Artifacts
- **Quality Gates**: Tests, mypy, formatting, Helm success

## Monitoring

### Prometheus Metrics
- `request_latency_seconds` - Pipeline timing
- `posts_engagement_rate` - KPI tracking
- `revenue_projection_monthly` - Business metrics
- `search_requests_total` - Search usage
- `trend_relevance_score` - Content quality

### Grafana Dashboards
- Business KPIs (revenue, engagement)
- Technical Metrics (latency, errors)
- Infrastructure (CPU, memory, network)

### AlertManager
- **Critical** → PagerDuty (service down, high errors)
- **Warning** → Slack (latency, costs)
- **Business** → Email (engagement, revenue)

## AI Workflow System

```bash
# AI Planning
./scripts/workflow-automation.sh ai-plan "Build feature X"

# Git Integration (all automated)
./scripts/workflow-automation.sh tasks start task_12345
./scripts/workflow-automation.sh tasks commit task_12345 "implement feature"
./scripts/workflow-automation.sh tasks ship task_12345
./scripts/workflow-automation.sh tasks complete task_12345
```

**Directory**: `.workflows/` contains epics, features, tasks in YAML

## Troubleshooting

```bash
# Common fixes
just k3d-nuke-all && just bootstrap    # Reset cluster
kubectl get pods -A                    # Check pod status
just e2e-prepare                       # Full test setup

# Port forwards
kubectl port-forward svc/postgres 5432:5432
kubectl port-forward svc/orchestrator 8080:8080
```

## Key Features

### 🚀 MCP Servers
- Redis: Instant caching (saves 2-3 hrs/week)
- Kubernetes: Direct cluster access (saves 3-4 hrs/week)
- PostgreSQL: No port-forwarding (saves 1-2 hrs/week)
- SearXNG: Free search ($500+/month savings)

### 🔍 Search Integration
- Trend detection for 2-3x engagement
- Competitive analysis for viral patterns
- Zero API costs with SearXNG
- Automated trend monitoring

### 💡 Productivity Summary
- **Total Time Saved**: 25-31 hours/week
- **Key Tools**: Hot-reload, AI tests, smart deploy
- **Business Impact**: Path to $20k MRR with automation

## Resources
- [DAILY_PLAYBOOK.md](./DAILY_PLAYBOOK.md) - Daily cheat sheet
- [PRODUCTIVITY_GUIDE.md](./PRODUCTIVITY_GUIDE.md) - Complete guide
- [docs/](./docs/) - Detailed documentation

---

**Repository**: https://github.com/threads-agent-stack/threads-agent
**Last Updated**: 2025-07-25