# CLAUDE.md - Threads-Agent Stack Development Guide

> **🚀 AI-Powered Development**: From idea to shipped code in minutes with GPT-4 planning + auto-git workflow.
> 
> **Quick Start**: `export OPENAI_API_KEY=your-key && ./scripts/workflow-automation.sh ai-plan "your idea"`

## 🎯 Daily Development Workflow

### Morning: Plan Your Work (2 minutes)
```bash
# Setup (one-time)
export OPENAI_API_KEY="your-openai-key"
gh auth login

# Plan today's work
./scripts/workflow-automation.sh ai-plan "Build user authentication system"
# → AI creates epic with features and tasks in 30 seconds

# See tasks
./scripts/workflow-automation.sh tasks list epic_generated_id
```

### Development: Zero-Friction Coding
```bash
# Start task (creates branch, sets up everything)
./scripts/workflow-automation.sh tasks start task_auth_001

# Commit with rich context (enhanced messages, auto-push)
./scripts/workflow-automation.sh tasks commit task_auth_001 "implement JWT middleware"

# Ship when ready (auto-PR with task description)
./scripts/workflow-automation.sh tasks ship task_auth_001

# Complete and move to next
./scripts/workflow-automation.sh tasks complete task_auth_001
```

### End of Day: Track Progress
```bash
./scripts/workflow-automation.sh tasks list epic_current_001
./scripts/workflow-automation.sh epics  # All epic progress
```

### Team Collaboration
```bash
./scripts/workflow-automation.sh tasks assign task_001 alice
./scripts/workflow-automation.sh tasks list epic_team_001
```

## 🚀 Quick Reference

### Essential Commands (Only 4 you need)

| Command | Purpose | Example |
|---------|---------|---------|
| `ai-plan` | AI creates project plan | `./scripts/workflow-automation.sh ai-plan "user auth"` |
| `tasks start` | Begin working (auto-branch) | `./scripts/workflow-automation.sh tasks start task_001` |
| `tasks commit` | Enhanced commit + push | `./scripts/workflow-automation.sh tasks commit task_001 "add middleware"` |
| `tasks ship` | Create PR automatically | `./scripts/workflow-automation.sh tasks ship task_001` |

### Complete Workflow (Copy-Paste Ready)
```bash
# 1. Plan feature
./scripts/workflow-automation.sh ai-plan "Build payment processing system"

# 2. Start first task
./scripts/workflow-automation.sh tasks start $(./scripts/workflow-automation.sh tasks list <epic_id> | head -1 | awk '{print $1}')

# 3. Code + commit
./scripts/workflow-automation.sh tasks commit <task_id> "implement stripe integration"

# 4. Ship for review
./scripts/workflow-automation.sh tasks ship <task_id>

# 5. Complete and get next
./scripts/workflow-automation.sh tasks complete <task_id>
```

### Power Tips
- **Demo Mode**: `./scripts/ai-epic-planner.sh demo` without OpenAI API key
- **See All Tasks**: `./scripts/workflow-automation.sh tasks list epic_12345`
- **Team Assignment**: `./scripts/workflow-automation.sh tasks assign task_001 alice`
- **Epic Overview**: `./scripts/workflow-automation.sh epics`

### Emergency Recovery
```bash
git checkout main && git pull origin main
git checkout -b emergency-fix-branch
git add . && git commit -m "emergency fix"
git push -u origin emergency-fix-branch
```

## Project Overview

**Threads-Agent Stack** is a production-grade, multi-persona AI agent system that:
- Researches trends and generates AI-powered Threads content
- Uses microservices architecture on Kubernetes
- Implements LangGraph workflows with LLM integration (OpenAI)
- Includes comprehensive monitoring, testing, and FinOps capabilities
- **🤖 AI-Powered Development**: Complete planning system using GPT-4
- **🔄 Auto-Git Integration**: Seamless task → code → ship workflow
- **📋 Local Epic Management**: YAML-based project tracking
- **🔍 SearXNG Integration**: Real-time trend detection and competitive analysis
- Goal: Achieve 6%+ engagement rate and $0.01 cost/follow, scaling to $20k MRR

### Key Performance Indicators (KPIs)
- **Engagement Rate**: 6%+ (tracking via `posts_engagement_rate`)
- **Cost per Follow**: $0.01 (tracking via `cost_per_follow_dollars`)
- **Monthly Revenue**: $20k MRR target (tracking via `revenue_projection_monthly`)
- **Content Velocity**: 10+ posts/day across personas with trend relevance >0.7
- **Search Cache Hit Rate**: >60% (reduces API latency)

## Architecture

### Microservices Structure
```
services/
├── orchestrator/        # FastAPI coordinator + Celery task dispatcher + Search APIs
├── celery_worker/      # Background task processor + SSE
├── persona_runtime/    # LangGraph DAG factory with LLM calls + Search enhancement
├── fake_threads/       # Mock Threads API for testing
└── common/            # Shared utilities (metrics, OpenAI wrapper, SearXNG wrapper)
```

### Core Technologies
- **Language**: Python 3.12+
- **Frameworks**: FastAPI, Celery, LangGraph, SQLAlchemy
- **Infrastructure**: k3d (local), Kubernetes, Helm
- **Databases**: PostgreSQL, Qdrant (vector store)
- **Messaging**: RabbitMQ
- **Monitoring**: Prometheus, OpenTelemetry, Jaeger, Grafana, AlertManager
- **AI/ML**: OpenAI API, optional LoRA support via PEFT
- **Search**: SearXNG (self-hosted metasearch engine)
- **MCP Servers**: Slack, SearXNG, Redis, Kubernetes, PostgreSQL, OpenAI, File System, GitHub, Linear

## Development Workflow

### Prerequisites
- Docker >= 24, k3d >= 5.6, Helm >= 3.14, Python 3.12+, just, npm

### Quick Start
```bash
git clone git@github.com:threads-agent-stack/threads-agent.git
cd threads-agent
just dev-start        # ONE COMMAND: Starts everything!
just dev-start-multi  # For multiple developers (unique cluster)
```

### 🎯 MEGA PRODUCTIVITY (80/20 Rule)
See **[DAILY_PLAYBOOK.md](./DAILY_PLAYBOOK.md)** for your daily cheat sheet.

**The Only 3 Commands You Need Daily**:
```bash
just work-day        # Morning: Start everything + dashboards
just create-viral    # Work: AI creates viral content 
just end-day        # Evening: Analyze + deploy + optimize
```

**Or Just One Command**: `just make-money` - Runs entire business on autopilot

#### Real Examples:
```bash
just create-viral ai-jesus "AI ethics"  # Research → Create → Test → Deploy!
just ship-it "feat: added engagement tracking"  # Test → Deploy → PR
just ai-biz revenue  # Shows path to $20k MRR
just autopilot-start  # Generates content every hour
```

### 🚀 Productivity Enhancements
See **[PRODUCTIVITY_GUIDE.md](./PRODUCTIVITY_GUIDE.md)** for complete guide.

**Key Commands**:
- `just dev-start` - Start EVERYTHING with one command
- `just persona-hot-reload` - Edit personas with instant preview
- `just ai-test-gen` - AI generates tests automatically
- `just smart-deploy` - Deploy with automatic rollback
- `just dev-dashboard` - Real-time metrics and AI insights

### 🎯 Daily Development Flow

#### Morning (1 Command, 30 Seconds)
```bash
just work-day        # Starts everything automatically
```

#### During Work (1 Command Per Task)
```bash
just create-viral ai-jesus "mental health AI"
just ship-it "feat: improved engagement algorithm"
just analyze-money
```

#### Evening (1 Command)
```bash
just end-day         # Commits work, starts overnight optimization
```

### 🎯 Old Way vs New Way

| Task | Old Way | New Way | Time Saved |
|------|---------|---------|------------|
| Morning Setup | Multiple commands | `just work-day` | 29 minutes |
| Create Content | Manual process | `just create-viral` | 2 hours |
| Deploy Feature | 4 commands | `just ship-it` | 45 minutes |
| End Day | Manual commits | `just end-day` | 30 minutes |

#### Content Generation Workflow

**Option 1: Manual Trend-Based**
```bash
just trend-check "AI productivity"
just competitive-analysis "AI productivity tips"
just search-enhanced-post ai-jesus "AI productivity and mindfulness"
```

**Option 2: Automated**
```bash
just trend-start  # Runs in background, generates content hourly
```

#### Development & Testing Flow
```bash
just test-watch orchestrator    # Watch mode for tests
just logs                       # Monitor service logs
just metrics                    # Check Prometheus metrics
just searxng-test "your query"  # Test search directly
```

### Key Commands (justfile)

#### 🎯 MEGA Commands (80/20 Rule)
- `just work-day` - Morning: Start env + trends + dashboards
- `just create-viral [persona] [topic]` - Work: Research + Create + Test
- `just ship-it [message]` - Deploy: Test + Deploy + PR
- `just end-day` - Evening: Analyze + Commit + Optimize
- `just make-money` - Autopilot: Run entire business
- `just grow-business` - Growth: Activate all systems + AI analysis
- `just analyze-money` - Finance: Complete ROI analysis
- `just ai-biz [action]` - Intelligence: AI business insights
- `just health-check` - Status: Everything in one glance

#### 🎯 Quick Productivity Commands
- `just dev-start` - Bootstrap + Deploy + MCP + Search + Hot-reload + Dashboard
- `just persona-hot-reload` - Edit personas with instant preview
- `just ai-test-gen [persona]` - AI generates tests
- `just smart-deploy [strategy]` - Deploy with health checks
- `just dev-dashboard` - Real-time performance monitoring
- `just cache-set/get` - Instant Redis cache operations
- `just trend-check [topic]` - Find what's trending now

#### Development
- `just bootstrap` - Create fresh k3d cluster
- `just bootstrap-multi` - Create unique cluster per developer
- `just images` - Build all Docker images
- `just deploy-dev` - Helm install with dev values
- `just logs` / `just logs-celery` - View service logs

#### Multi-Cluster Management
- `just cluster-list` - List all k3d clusters
- `just cluster-switch NAME` - Switch clusters
- `just cluster-current` - Show current cluster
- `just cluster-delete NAME` - Delete cluster
- `just dev-start-multi` - Full env with unique cluster
- `just dev-start-multi share` - Shared team cluster

#### 🔍 Search & Trend Detection
- `just searxng-start` - Start local SearXNG
- `just trend-check "topic"` - Check current trends
- `just trend-dashboard` - Visual overview of trends
- `just trend-start` - Start automated trend detection
- `just competitive-analysis "topic"` - Analyze viral patterns
- `just search-enhanced-post "persona" "topic"` - Generate trend-aware content

#### 🚀 MCP Server Management
- `just mcp-setup` - Setup all MCP servers
- `just cache-set/get` - Redis cache operations
- `just cache-trends` - View trending topics in Redis
- `just redis-cli` - Direct Redis CLI access
- `just mcp-redis-test` - Test Redis MCP
- `just mcp-k8s-test` - Test Kubernetes MCP
- `just mcp-postgres-test` - Test PostgreSQL MCP
- `just linear-mcp-setup` - Setup Linear MCP

#### Testing  
- `just unit` - Run unit tests only
- `just e2e` - Run end-to-end tests
- `just test-watch [SERVICE]` - Watch mode testing
- `just e2e-prepare` - Full e2e setup

#### Quality & Shipping
- `just lint` - Format with ruff, isort, black
- `just check` - Full quality gate
- `just ship "commit message"` - CI-green commit → push → auto-PR

#### Utilities
- `just scaffold SERVICE` - Generate new service
- `just reset-hard` - Nuclear reset
- `just jaeger-ui` - Open Jaeger tracing UI
- `just grafana` - Open Grafana dashboards

### Environment Files
- `chart/values-dev.yaml` - Local k3d development
- `chart/values-ci.yaml` - CI/testing environment  
- `chart/values-prod.yaml` - Production configuration

## Testing Strategy

### Test Organization
```
tests/
├── e2e/              # End-to-end integration tests
├── unit/             # Cross-service unit tests
└── test_sanity.py    # Basic smoke tests

services/*/tests/     # Service-specific unit tests
```

### Test Markers
- `@pytest.mark.e2e` - Slow tests requiring full k3d cluster
- Default: Unit tests that run quickly without infrastructure

### Testing Patterns
- **E2E**: Use `kubectl port-forward` to access services
- **Unit**: Use `:memory:` Qdrant, stub OpenAI calls
- **Fixtures**: Auto-setup port forwarding
- **Timeouts**: Generous timeouts (40s) for async completion

## Database & Models

### Primary Database (PostgreSQL)
```python
class Post(Base):
    id: int (BigInteger, PK)
    persona_id: str
    hook: str  
    body: str
    tokens_used: int
    ts: datetime (default=NOW())

class Task(Base):
    id: int (BigInteger, PK) 
    payload: dict[str, Any]
    status: str (default="queued")
```

### Vector Store (Qdrant)
- Collections: `posts_{persona_id}`
- Purpose: Semantic similarity for deduplication
- Configuration: `services/orchestrator/vector.py`

### Migrations
- Tool: Alembic
- Location: `services/orchestrator/db/alembic/`
- Auto-run: Kubernetes init container

## Service Architecture Details

### Orchestrator
- **Purpose**: Main API gateway and Celery dispatcher
- **Framework**: FastAPI
- **Key Routes**: `/task`, `/health`, `/metrics`, `/search/*`
- **Dependencies**: PostgreSQL, RabbitMQ, Qdrant, SearXNG

### Celery Worker  
- **Purpose**: Background task processing with SSE
- **Tasks**: `tasks.queue_post` - Full content pipeline
- **Features**: Server-Sent Events for real-time progress

### Persona Runtime
- **Purpose**: LangGraph DAG execution with LLM calls
- **Standard**: ingest → hook_llm → body_llm → guardrail → format
- **Enhanced**: ingest → trend_research → competitive_analysis → hook_llm → body_llm → guardrail → format
- **Models**: Configurable via env vars
- **Safety**: Content moderation + regex guardrails
- **Offline Mode**: Deterministic stubs when `OPENAI_API_KEY=test`

### Fake Threads
- **Purpose**: Mock Threads API for dev/testing
- **Endpoints**: `/publish`, `/published`, `/ping`

### Common
- **Metrics**: Prometheus instrumentation helpers
- **OpenAI Wrapper**: Centralized LLM client
- **SearXNG Wrapper**: Search API with caching
- **Shared across**: All services import common utilities

## Configuration & Secrets

### Environment Variables

#### Orchestrator
- `RABBITMQ_URL`, `PERSONA_RUNTIME_URL`, `DATABASE_URL`, `QDRANT_URL`
- `SEARXNG_URL` (default: http://localhost:8888)
- `SEARCH_TIMEOUT` (default: 10)

#### Persona Runtime  
- `OPENAI_API_KEY` (use "test" for offline)
- `HOOK_MODEL` (default: gpt-4o)
- `BODY_MODEL` (default: gpt-3.5-turbo-0125)
- `LORA_PATH`, `SEARCH_ENABLED`, `TREND_CHECK_INTERVAL`

#### Development Overrides
- `chart/values-dev.local.yaml` - Personal local overrides (gitignored)

## Build & Deployment

### Docker Strategy
- Multi-stage builds, Base: `python:3.12-slim-bookworm`
- Images: Built with `just images`, tagged as `{service}:local`

### Helm Configuration
- Chart: Single mono-chart in `chart/`
- Values Hierarchy: `values.yaml` → `values-dev.yaml` → `values-dev.local.yaml`
- Components: All services + PostgreSQL + RabbitMQ + Qdrant

### CI/CD Pipeline
- Triggers: Pull requests to `main`
- Steps: Setup → Infrastructure → Build → Deploy → Test → Artifacts
- Quality Gates: All tests pass, mypy, formatting, Helm deployment

## Monitoring & Observability

### Metrics (Prometheus)
- **Endpoint**: `GET /metrics` on each service (port 9090)
- **Key Metrics**: Request latency, token usage, posts generated, engagement rates, revenue projections, costs, uptime, error rates, search metrics
- **Helpers**: `record_latency()`, `record_business_metric()`, `record_engagement_rate()`, `update_revenue_projection()`

### Grafana Dashboards
- **Access**: `kubectl port-forward svc/grafana 3000:3000`
- **Dashboards**: Business KPIs, Technical Metrics, Infrastructure
- **Location**: `monitoring/grafana/dashboards/`

### AlertManager
- **Access**: `kubectl port-forward svc/alertmanager 9093:9093`
- **Integration**: PagerDuty (critical), Slack (warnings), Email (business)
- **Alert Categories**: Critical (🚨), Warning (⚠️), Business (📈), Infrastructure (🏗️)
- **Configuration**: `monitoring/alertmanager/`

### Tracing & Logging
- **Jaeger**: `just jaeger-ui` → http://localhost:16686
- **Logs**: `just logs` (orchestrator), `just logs-celery`

## Development Best Practices

### Code Quality
- Type Checking: mypy strict mode
- Formatting: ruff + black + isort
- Pre-commit: Enforced via `just ship`
- Testing: High coverage unit + integration + e2e

### Git Workflow  
- Branching: `feat/<epic>-<slug>` or `task-{epic-id}-{title}`
- Protection: `main` requires PR + CI + review
- Automation: `just ship` handles commit → push → PR

### 🤖 AI-Powered Epic & Task Management

**Overview**: Local YAML-based project management with AI-powered planning using GPT-4.

**Directory Structure**:
```
.workflows/
├── epics/              # AI-generated epic definitions
├── features/           # AI-broken-down features
├── tasks/              # Smart task tracking with git integration
├── templates/          # AI-optimized templates
├── active_epics.json   # Active epic registry
└── feature_registry.json # Feature tracking
```

**Core AI Workflow Commands**:
```bash
# AI PLANNING: From idea to implementation plan
./scripts/workflow-automation.sh ai-plan "Build user authentication system"

# GIT INTEGRATION: Smart branch + commit + PR workflow
./scripts/workflow-automation.sh tasks start task_12345    # Auto-branch
./scripts/workflow-automation.sh tasks commit task_12345 "add JWT validation"
./scripts/workflow-automation.sh tasks ship task_12345     # Auto-PR
./scripts/workflow-automation.sh tasks complete task_12345 # Cleanup

# MANAGEMENT: Traditional commands enhanced with AI
./scripts/workflow-automation.sh epics                     # List epics
./scripts/workflow-automation.sh tasks list epic_001      # Show tasks
./scripts/workflow-automation.sh tasks assign task_001 alice  # Team assign
```

### Auto-Git Integration

**One Command Does Everything**:
```bash
./scripts/workflow-automation.sh tasks start task_12345
```

**What happens automatically:**
- Ensures main branch is up-to-date
- Creates semantic branch: `task-epic123-implement-auth-middleware`
- Sets up commit template with task context
- Updates task status to "in_progress"
- Shows task description and next steps

### Multi-Developer Cluster Management

See [Multi-Cluster Development Guide](./docs/multi-cluster-development.md).

**Key Features**: Unique clusters per developer, automatic port allocation, shared team clusters, easy switching

**Quick Commands**:
```bash
just bootstrap-multi  # Personal cluster
just bootstrap-multi --share  # Team cluster
just cluster-list  # List all
just cluster-switch threads-agent-john-abc123
```

## Personas & AI Configuration

### Supported Personas
```python
_PERSONA_DB = {
    "ai-jesus": SimpleNamespace(emoji="🙏", temperament="kind"),
    "ai-elon": SimpleNamespace(emoji="🚀", temperament="hype"), 
}
```

### Content Generation Pipeline

**Standard**: Ingest → Hook → Body → Guardrail → Format
**Enhanced**: Ingest → Trend Research → Competitive Analysis → Hook → Body → Guardrail → Format

### Safety & Moderation
- Regex Guards: Block harmful keywords
- OpenAI Moderation: `omni-moderation-latest`
- Pipeline Halt: Fail fast on violations

## Troubleshooting

### Common Issues

**k3d cluster not ready**: `just k3d-nuke-all && just bootstrap`

**Helm deployment timeout**: Check `kubectl get pods -A` and `kubectl get events`

**Tests failing locally**: `just e2e-prepare` for full clean setup

**OpenAI API cost concerns**: Use `OPENAI_API_KEY=test` for offline dev

### Port Forwards for Development
```bash
kubectl port-forward svc/postgres 5432:5432
kubectl port-forward svc/fake-threads 9009:9009
kubectl port-forward svc/orchestrator 8080:8080
```

## Performance & Cost Optimization

### FinOps Features
- Token Tracking: Prometheus metrics for LLM usage
- Model Selection: Cheaper models for body generation
- Caching: Vector similarity prevents duplicates
- Offline Mode: Development without API costs

### Scaling Considerations
- Horizontal: Increase replica counts in Helm
- Resource Limits: Configure in `values.yaml`
- Database: Consider Aurora Serverless for production
- Vector Store: Qdrant clustering for HA

## Future Roadmap

- **E2 - Core MVP**: Full content generation pipeline ✅
- **E3 - SRE v1**: Advanced monitoring and alerting ✅
- **E4 - Bandit A/B**: Multi-armed bandit optimization
- **E5 - Trend & Pain**: Automated trend detection ✅ (SearXNG)
- **E6 - FinOps Board**: Cost optimization dashboard
- **E7+ - Production**: EKS, Aurora, security hardening

## 🚀 MCP Server Integration

MCP servers provide direct access to tools and services, eliminating manual commands.

### Installed MCP Servers

1. **Redis MCP** - Lightning-fast caching (2-3 hours/week saved)
2. **Kubernetes MCP** - Direct cluster management (3-4 hours/week saved)
3. **PostgreSQL MCP** - Database without barriers (1-2 hours/week saved)
4. **OpenAI MCP** - AI model management (1-2 hours/week saved)
5. **SearXNG MCP** - Free search integration ($500+/month saved)
6. **Linear MCP** - Issue tracking integration (2-3 hours/week saved)

### Daily MCP Usage Examples

**Cache Management (Redis)**:
```bash
just cache-set "trends:AI:2025-01-22" "$(just trend-check AI)"
just cache-get "trends:AI:2025-01-22"
```

**Database Queries (PostgreSQL)**:
```sql
SELECT persona_id, AVG(engagement_rate) as avg_engagement
FROM posts WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY persona_id;
```

## 🔍 SearXNG Search Integration

Free, privacy-respecting search capabilities for trend detection and competitive intelligence.

### Why Search Matters for KPIs
1. **6%+ Engagement Rate**: Trending content gets 2-3x higher engagement
2. **$0.01 Cost/Follow**: Better targeting through trends
3. **$20k MRR**: Automated trend detection scales content
4. **Zero Search Costs**: SearXNG is 100% free

### Daily Usage Patterns
```bash
# Morning
just searxng-start
just trend-dashboard
just trend-start &

# Active Development
just trend-check "your topic"
just competitive-analysis "your topic"
just search-enhanced-post ai-jesus "trending topic"

# Monitoring
just grafana  # Check engagement metrics
```

## 💡 Productivity Features Summary

### Time Savings Breakdown (Per Week)
1. **MCP Servers** (10-12 hours saved)
2. **Search Integration** (5-6 hours saved)
3. **AI Development Tools** (8-10 hours saved)
4. **Monitoring & Insights** (2-3 hours saved)

### Essential Daily Commands
```bash
# Morning
just dev-start
just trend-dashboard
just dev-dashboard

# During Development
just persona-hot-reload
just ai-test-gen
just cache-set/get
just search-enhanced-post

# Deployment
just smart-deploy canary
just grafana
```

## 🎯 AI Token Efficiency (80/20 Principle)

Get 80% of AI value with 20% of token usage:

### Quick Start
```bash
just token-optimize     # Enable all optimizations
just token-status      # Check your savings
```

### Token-Efficient Commands
```bash
just cached-analyze    # 0 tokens (uses morning's analysis)
just cached-trends     # 0 tokens (uses daily trends)
just token-batch       # Week's content in one call (80% savings)
just token-viral       # Template-based creation (50% savings)
```

### Real Savings Example
Traditional: 10,000 tokens/day ($0.20/day)
Optimized: 2,000 tokens/day ($0.04/day - 80% less!)

### 🎓 Learning Resources
- **[DAILY_PLAYBOOK.md](./DAILY_PLAYBOOK.md)** - ⚡ Daily cheat sheet (START HERE!)
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - 📋 Command quick reference
- **[PRODUCTIVITY_GUIDE.md](./PRODUCTIVITY_GUIDE.md)** - Complete productivity guide
- **[docs/ai-token-efficiency-guide.md](./docs/ai-token-efficiency-guide.md)** - Token optimization
- **[docs/mega-commands-guide.md](./docs/mega-commands-guide.md)** - Mega commands
- **[docs/multi-cluster-development.md](./docs/multi-cluster-development.md)** - Multi-developer
- **[docs/searxng-integration-guide.md](./docs/searxng-integration-guide.md)** - Search integration
- **[docs/mcp-servers-setup.md](./docs/mcp-servers-setup.md)** - MCP configuration

---

**Last Updated**: 2025-07-22  
**Repository**: https://github.com/threads-agent-stack/threads-agent  
**Documentation**: This file serves as the authoritative development guide for future Claude instances working on this codebase.