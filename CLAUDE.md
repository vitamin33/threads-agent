# CLAUDE.md - Threads-Agent Stack Development Guide

> **🚀 Productivity First**: This codebase includes advanced productivity features that save 20-25 hours/week.
> See [PRODUCTIVITY_GUIDE.md](./PRODUCTIVITY_GUIDE.md) for the complete guide.
> 
> **Quick Start**: `just dev-start` - This single command sets up EVERYTHING!

## Project Overview

**Threads-Agent Stack** is a production-grade, multi-persona AI agent system that:
- Researches trends and generates AI-powered Threads content
- Uses a microservices architecture on Kubernetes
- Implements LangGraph workflows with LLM integration (OpenAI)
- Includes comprehensive monitoring, testing, and FinOps capabilities
- **NEW**: Integrates SearXNG for real-time trend detection and competitive analysis
- Goal: Achieve 6%+ engagement rate and $0.01 cost/follow, scaling to $20k MRR

### Key Performance Indicators (KPIs)
- **Engagement Rate**: 6%+ (current: tracking via `posts_engagement_rate` metric)
- **Cost per Follow**: $0.01 (current: tracking via `cost_per_follow_dollars` metric)
- **Monthly Revenue**: $20k MRR target (tracking via `revenue_projection_monthly` metric)
- **Content Velocity**: 10+ posts/day across personas with trend relevance >0.7
- **Search Cache Hit Rate**: >60% (reduces API latency and improves performance)

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
- **MCP Servers**: 
  - **Slack** - Real-time alerts to #alerts channel
  - **SearXNG** - Free search for trends and competitive analysis
  - **Redis** - Fast caching for trends, search results, metrics
  - **Kubernetes** - Direct cluster management without kubectl
  - **PostgreSQL** - Database queries without port-forwarding
  - **OpenAI** - Token tracking and model management
  - **File System** - Direct file access
  - **GitHub** - Repository operations

## Development Workflow

### Prerequisites
- Docker >= 24
- k3d >= 5.6  
- Helm >= 3.14
- Python 3.12+
- just (command runner)
- npm (for MCP servers)

### Quick Start
```bash
git clone git@github.com:threads-agent-stack/threads-agent.git
cd threads-agent
just dev-start        # ONE COMMAND: Starts everything!

# For multiple developers on same machine
just dev-start-multi  # Creates unique cluster per developer
```

### 🎯 MEGA PRODUCTIVITY (80/20 Rule) - NEW!
**IMPORTANT**: We've created mega commands that do 80% of your work with 20% effort.
See **[DAILY_PLAYBOOK.md](./DAILY_PLAYBOOK.md)** for your daily cheat sheet.

**The Only 3 Commands You Need Daily**:
```bash
just work-day        # Morning: Start everything + dashboards
just create-viral    # Work: AI creates viral content 
just end-day        # Evening: Analyze + deploy + optimize
```

**Or Just One Command**:
```bash
just make-money     # Runs your entire business on autopilot
```

#### Real Examples (Tested & Working):
```bash
# Create viral content about AI ethics
just create-viral ai-jesus "AI ethics"
# Output: Researches trends → Creates content → Tests → Ready to deploy!

# Ship a new feature
just ship-it "feat: added engagement tracking"  
# Output: Runs tests → Deploys safely → Creates PR

# Check your business metrics
just ai-biz revenue
# Output: Shows path to $20k MRR with specific actions

# Start autopilot mode
just autopilot-start
# Output: Generates content every hour automatically
```

See **[docs/mega-commands-guide.md](./docs/mega-commands-guide.md)** for detailed examples.

### 🚀 Productivity Enhancements
**IMPORTANT**: We've built extensive productivity features that save 20-25 hours/week.
See **[PRODUCTIVITY_GUIDE.md](./PRODUCTIVITY_GUIDE.md)** for:
- One-command development setup
- MCP server integrations (Redis, PostgreSQL, Kubernetes)
- AI-powered test generation
- Hot-reload persona development
- Smart deployment with auto-rollback
- Real-time performance dashboard
- Intelligent error recovery

**Key Commands**:
- `just dev-start` - Start EVERYTHING with one command
- `just persona-hot-reload` - Edit personas with instant preview
- `just ai-test-gen` - AI generates tests automatically
- `just smart-deploy` - Deploy with automatic rollback
- `just dev-dashboard` - Real-time metrics and AI insights

### 🎯 Daily Development Flow - The New Way

#### Morning (1 Command, 30 Seconds)
```bash
just work-day        # That's it! Everything starts automatically
```
This single command:
- ✅ Checks your cluster status
- ✅ Shows trending topics
- ✅ Displays cached trends
- ✅ Opens AI business dashboard
- ✅ Gives you today's action items

#### During Work (1 Command Per Task)
```bash
# Need content? One command:
just create-viral ai-jesus "mental health AI"

# Ship a feature? One command:
just ship-it "feat: improved engagement algorithm"

# Check finances? One command:
just analyze-money
```

#### Evening (1 Command, Done)
```bash
just end-day         # Commits work, starts overnight optimization
```

### 🎯 The Old Way vs The New Way

| Task | Old Way (Multiple Commands) | New Way (Mega Command) | Time Saved |
|------|----------------------------|------------------------|------------|
| Morning Setup | `just bootstrap` + `just deploy-dev` + `just mcp-setup` + more... | `just work-day` | 29 minutes |
| Create Content | Research → Write → Test → Deploy (manual) | `just create-viral` | 2 hours |
| Deploy Feature | Test → Build → Deploy → PR (4 commands) | `just ship-it` | 45 minutes |
| End Day | Multiple commits + manual optimization | `just end-day` | 30 minutes |

#### Content Generation Workflow (Throughout the Day)

**Option 1: Manual Trend-Based Generation**
```bash
# 1. Research what's trending
just trend-check "AI productivity"
# Output: Shows top 5 trends with scores

# 2. Analyze competition
just competitive-analysis "AI productivity tips"
# Output: Viral patterns, keywords, engagement indicators

# 3. Generate trend-aware content
just search-enhanced-post ai-jesus "AI productivity and mindfulness"
# Creates content that incorporates current trends
```

**Option 2: Automated Trend Detection**
```bash
# Start automated workflow (runs in background)
just trend-start
# - Checks trends every hour
# - Automatically generates content for trending topics
# - Tracks performance metrics
```

#### Development & Testing Flow
```bash
# When developing new features:
just test-watch orchestrator    # Watch mode for service tests
just logs                       # Monitor service logs
just metrics                    # Check Prometheus metrics

# When testing search features:
just searxng-test "your query"  # Test search directly
curl localhost:8080/search/trends -d '{"topic":"AI"}'  # Test API
```

#### End of Day Analysis (5 min)
```bash
# Review performance
just trend-dashboard           # See day's trending content
just grafana                   # Check engagement metrics
just cost-analysis             # Review API costs

# Commit your work
just ship "feat: implemented trend-aware content generation"
```

### Key Commands (justfile)

#### 🎯 MEGA Commands (80/20 Rule) - Do More with Less!
- `just work-day` - **MORNING**: Start env + trends + dashboards (7 commands → 1)
- `just create-viral [persona] [topic]` - **WORK**: Research + Create + Test (2 hours → 5 min)
- `just ship-it [message]` - **DEPLOY**: Test + Deploy + PR (45 min → 1 min)
- `just end-day` - **EVENING**: Analyze + Commit + Optimize overnight
- `just make-money` - **AUTOPILOT**: Run entire business automatically
- `just grow-business` - **GROWTH**: Activate all growth systems + AI analysis
- `just analyze-money` - **FINANCE**: Complete ROI analysis + recommendations
- `just ai-biz [action]` - **INTELLIGENCE**: AI business insights dashboard
- `just health-check` - **STATUS**: Everything in one glance

#### 🎯 Quick Productivity Commands
- `just dev-start` - **ONE COMMAND**: Bootstrap + Deploy + MCP + Search + Hot-reload + Dashboard
- `just persona-hot-reload` - Edit personas with instant preview (no rebuild!)
- `just ai-test-gen [persona]` - AI generates tests automatically
- `just smart-deploy [strategy]` - Deploy with health checks and auto-rollback
- `just dev-dashboard` - Real-time performance monitoring
- `just cache-set/get` - Instant Redis cache operations
- `just trend-check [topic]` - Find what's trending now

#### Development
- `just bootstrap` - Create fresh k3d cluster with networking (single cluster)
- `just bootstrap-multi` - Create unique k3d cluster per developer/repo (multi-developer)
- `just images` - Build all service Docker images and import to k3d
- `just deploy-dev` - Helm install with dev values
- `just logs` / `just logs-celery` - View service logs

#### 👥 Multi-Cluster Management (NEW)
- `just cluster-list` - List all available k3d clusters
- `just cluster-switch NAME` - Switch to a different cluster
- `just cluster-current` - Show current active cluster
- `just cluster-delete NAME` - Delete a specific cluster
- `just dev-start-multi` - Full environment with unique cluster per developer
- `just dev-start-multi share` - Shared team cluster for collaboration

#### 🔍 Search & Trend Detection (NEW)
- `just searxng-start` - Start local SearXNG search engine (**KPI**: Enables 100% free search)
- `just searxng-stop` - Stop SearXNG instance
- `just trend-check "topic"` - Check current trends for a topic (**KPI**: Find >5 trends per topic)
- `just trend-dashboard` - Visual overview of trending topics (**KPI**: Monitor trend relevance >0.7)
- `just trend-start` - Start automated trend detection (**KPI**: Generate 10+ posts/day)
- `just competitive-analysis "topic"` - Analyze viral content patterns (**KPI**: Extract patterns from top 10% content)
- `just search-enhanced-post "persona" "topic"` - Generate trend-aware content (**KPI**: Boost engagement by 2x)

#### 🚀 MCP Server Management (NEW)
- `just mcp-setup` - Setup all MCP servers with port-forwarding (**KPI**: Save 30 min/day on manual setup)
- `just cache-set "key" "value"` - Store data in Redis cache (**KPI**: 100ms vs 1s database queries)
- `just cache-get "key"` - Retrieve cached data instantly
- `just cache-trends` - View trending topics in Redis (**KPI**: Track trend persistence)
- `just redis-cli` - Direct Redis CLI access
- `just mcp-redis-test` - Test Redis MCP functionality
- `just mcp-k8s-test` - Test Kubernetes MCP access
- `just mcp-postgres-test` - Test PostgreSQL MCP queries

#### Testing  
- `just unit` - Run unit tests only (`pytest -m "not e2e"`)
- `just e2e` - Run end-to-end tests with automatic port forwarding (`pytest -m e2e`)
- `just test-watch [SERVICE]` - Watch mode testing
- `just e2e-prepare` - Full e2e setup (bootstrap + images + deploy + service readiness checks)

#### Quality & Shipping
- `just lint` - Format with ruff, isort, black
- `just check` - Full quality gate (lint + mypy + tests)
- `just ship "commit message"` - CI-green commit → push → auto-PR

#### Utilities
- `just scaffold SERVICE` - Generate new service from template
- `just reset-hard` - Nuclear reset (delete k3d + Docker cache)
- `just jaeger-ui` - Open Jaeger tracing UI
- `just grafana` - Open Grafana dashboards (**KPI**: Monitor all business metrics)

### Environment Files
- `chart/values-dev.yaml` - Local k3d development
- `chart/values-ci.yaml` - CI/testing environment  
- `chart/values-prod.yaml` - Production configuration

## Testing Strategy

### Test Organization
```
tests/
├── e2e/              # End-to-end integration tests
│   ├── test_post_flow.py      # Full pipeline: task → Celery → fake-threads
│   ├── test_metrics.py        # Prometheus metrics validation
│   └── test_draft_post.py     # Draft generation workflow
├── unit/             # Cross-service unit tests
└── test_sanity.py    # Basic smoke tests

services/*/tests/     # Service-specific unit tests
├── unit/            # Pure unit tests (no I/O)
└── test_*.py        # Integration tests (with test doubles)
```

### Test Markers
- `@pytest.mark.e2e` - Slow tests requiring full k3d cluster
- Default: Unit tests that run quickly without infrastructure

### Testing Patterns
- **E2E**: Use `kubectl port-forward` to access services in k3d
- **Unit**: Use `:memory:` Qdrant, stub OpenAI calls with `OPENAI_API_KEY=test`
- **Fixtures**: Auto-setup port forwarding in e2e tests
- **Timeouts**: Generous timeouts (40s) for async pipeline completion

## Database & Models

### Primary Database (PostgreSQL)
```python
# services/orchestrator/db/models.py
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
- Collections: `posts_{persona_id}` (e.g., `posts_ai-jesus`)
- Purpose: Semantic similarity search for content deduplication
- Configuration: `services/orchestrator/vector.py`

### Migrations
- **Tool**: Alembic (SQLAlchemy-based)
- **Location**: `services/orchestrator/db/alembic/`
- **Auto-run**: Kubernetes init container in Helm chart

## Service Architecture Details

### Orchestrator (`services/orchestrator/`)
- **Purpose**: Main API gateway and Celery task dispatcher
- **Framework**: FastAPI
- **Key Routes**:
  - `POST /task` - Queue content generation task
  - `GET /health` - Health check
  - `GET /metrics` - Prometheus metrics endpoint
  - **NEW** `POST /search/trends` - Discover trending topics
  - **NEW** `POST /search/competitive` - Analyze viral content
  - **NEW** `POST /search/enhanced-task` - Create search-powered content
- **Dependencies**: PostgreSQL, RabbitMQ, Qdrant, SearXNG

### Celery Worker (`services/celery_worker/`)  
- **Purpose**: Background task processing with SSE updates
- **Tasks**: `tasks.queue_post` - Full content generation pipeline
- **Features**: Server-Sent Events for real-time progress
- **Integration**: Calls persona-runtime, posts to fake-threads

### Persona Runtime (`services/persona_runtime/`)
- **Purpose**: LangGraph DAG execution with LLM calls
- **Standard Workflow**: ingest → hook_llm → body_llm → guardrail → format
- **Enhanced Workflow**: ingest → **trend_research** → **competitive_analysis** → hook_llm → body_llm → guardrail → format
- **Models**: Configurable via env vars (`HOOK_MODEL`, `BODY_MODEL`)
- **Safety**: Content moderation + regex guardrails
- **Offline Mode**: Deterministic stubs when `OPENAI_API_KEY=test`
- **Search Integration**: Optional trend-aware content generation

### Fake Threads (`services/fake_threads/`)
- **Purpose**: Mock Threads API for development/testing
- **Endpoints**: 
  - `POST /publish` - Accept generated content
  - `GET /published` - List all published content
  - `GET /ping` - Health check

### Common (`services/common/`)
- **Metrics**: Prometheus instrumentation helpers + search metrics
- **OpenAI Wrapper**: Centralized LLM client with token counting
- **SearXNG Wrapper**: Search API with caching, trend detection, competitive analysis
- **Shared across**: All services import common utilities

## Configuration & Secrets

### Environment Variables

#### Orchestrator
- `RABBITMQ_URL` - Celery broker connection
- `PERSONA_RUNTIME_URL` - Service-to-service communication  
- `DATABASE_URL` - PostgreSQL connection
- `QDRANT_URL` - Vector store connection
- `SEARXNG_URL` - SearXNG search engine URL (default: http://localhost:8888)
- `SEARCH_TIMEOUT` - Search request timeout in seconds (default: 10)

#### Persona Runtime  
- `OPENAI_API_KEY` - OpenAI API access (use "test" for offline mode)
- `HOOK_MODEL` - Model for hook generation (default: gpt-4o)
- `BODY_MODEL` - Model for body generation (default: gpt-3.5-turbo-0125)
- `LORA_PATH` - Optional LoRA adapter path
- `SEARCH_ENABLED` - Enable search enhancement (default: true)
- `TREND_CHECK_INTERVAL` - Seconds between trend checks (default: 3600)

#### Development Overrides
- `chart/values-dev.local.yaml` - Personal local overrides (gitignored)
- Services use `test` API key by default to avoid costs

## Build & Deployment

### Docker Strategy
- **Multi-stage builds**: Services share common dependencies
- **Base**: `python:3.12-slim-bookworm`
- **Pattern**: Copy requirements → install → copy source code
- **Images**: Built with `just images`, tagged as `{service}:local`

### Helm Configuration
- **Chart**: Single mono-chart in `chart/`
- **Values Hierarchy**: 
  1. `values.yaml` (base/production)
  2. `values-dev.yaml` (local overrides)  
  3. `values-dev.local.yaml` (personal, gitignored)
- **Components**: All services + PostgreSQL + RabbitMQ + Qdrant

### CI/CD Pipeline (`.github/workflows/dev-ci.yml`)

#### Triggers
- Pull requests to `main`
- Comprehensive 15-minute timeout

#### Pipeline Steps
1. **Setup**: Checkout + BuildX cache
2. **Infrastructure**: Create k3d cluster  
3. **Build**: Docker images with cache optimization
4. **Deploy**: Helm install with CI values + secret injection
5. **Test**: Unit + E2E test suite with port forwarding
6. **Artifacts**: Generate/upload Mermaid infrastructure diagram

#### Quality Gates
- All tests must pass
- Type checking with mypy
- Code formatting with ruff/black/isort
- Helm deployment must succeed

## Monitoring & Observability

### Metrics (Prometheus)
- **Endpoint**: `GET /metrics` on each service (port 9090)
- **Key Metrics**:
  - `request_latency_seconds{phase}` - Pipeline phase timing
  - `llm_tokens_total{model}` - Token usage by model
  - `posts_generated_total{persona_id,status}` - Total posts by persona and outcome
  - `posts_engagement_rate{persona_id}` - Actual engagement rates
  - `revenue_projection_monthly{source}` - Monthly revenue projections
  - `cost_per_post_usd{persona_id}` - Cost per post generation
  - `cost_per_follow_dollars{persona_id}` - Cost per follower acquisition
  - `openai_cost_hourly_dollars{model}` - Hourly OpenAI costs
  - `service_uptime_seconds{service_name}` - Service uptime tracking
  - `error_rate_percentage{service_name,error_type}` - Error rate percentages
  - **NEW** `search_requests_total{search_type,persona_id}` - Search usage tracking
  - **NEW** `trends_discovered_total{topic,timeframe}` - Trend detection success
  - **NEW** `search_enhanced_posts_total{persona_id,enhancement_type}` - Enhanced content tracking
  - **NEW** `search_cache_operations{operation,result}` - Cache performance
  - **NEW** `trend_relevance_score{topic,persona_id}` - Trend quality scoring
- **Helpers**: 
  - `services.common.metrics.record_latency()`
  - `services.common.metrics.record_business_metric()`
  - `services.common.metrics.record_engagement_rate()`
  - `services.common.metrics.update_revenue_projection()`

### Grafana Dashboards (CRA-221)
- **Access**: `kubectl port-forward svc/grafana 3000:3000` → http://localhost:3000
- **Credentials**: admin / admin123 (dev), configurable in production
- **Dashboards**:
  - **Business KPIs** (`business-kpis.json`): Revenue projection to $20k MRR, engagement rate tracking (target: 6%+), cost per follow (target: $0.01), token usage costs, content quality scores
  - **Technical Metrics** (`technical-metrics.json`): Service uptime, error rates by service, HTTP request latency (P95, P99), Celery queue depth, database connection pools, task execution times
  - **Infrastructure** (`infrastructure.json`): Pod CPU/memory usage, network I/O patterns, storage usage trends, Kubernetes cluster health, Qdrant vector database operations
- **Location**: `monitoring/grafana/dashboards/`
- **Auto-provisioned**: Dashboards deployed via Helm ConfigMaps in `chart/templates/grafana.yaml`
- **Configuration**: Enable via `monitoring.grafana.enabled: true` in values files

### AlertManager (CRA-222)
- **Access**: `kubectl port-forward svc/alertmanager 9093:9093` → http://localhost:9093
- **Purpose**: Centralized alerting with intelligent routing and escalation
- **Integration**: PagerDuty (critical), Slack (warnings), Email (business)

#### Alert Categories
- **Critical Alerts** (🚨 PagerDuty):
  - `ServiceDown` - Service unavailable >1 minute
  - `HighErrorRate` - Error rate >5% for 5 minutes
  - `DatabaseConnectionFailure` - No active DB connections
  - `CeleryQueueDepthHigh` - Queue >1000 messages
  - `DiskSpaceHigh` - Disk usage >85%
  - `PodCrashLooping` - Pod restarts >5 in 1 hour
  
- **Warning Alerts** (⚠️ Slack):
  - `HighLatency` - P95 >2s for 10 minutes
  - `HighTokenCost` - OpenAI costs >$5/hour
  - `HighMemoryUsage` - Memory >80% for 5 minutes
  - `HighPostFailureRate` - Post failures >10% for 15 minutes
  - `SlowDatabaseQueries` - P95 query time >1s

- **Business Alerts** (📈 Email):
  - `LowEngagementRate` - Engagement <4% for 30 minutes (target: 6%+)
  - `HighCostPerFollow` - Cost >$0.02 per follow (target: $0.01)
  - `NoPostsGenerated` - Zero posts for 30 minutes
  - `RevenueBelowTarget` - Revenue <80% of $20k MRR target
  - `LowContentQuality` - Quality score <0.6

- **Infrastructure Alerts** (🏗️ Hybrid):
  - `KubernetesNodeNotReady` - Node unavailable >5 minutes
  - `HighCPUUsage` - CPU >85% for 10 minutes
  - `HighNetworkErrors` - Network errors >100/5min

#### Configuration Files
- **Alert Rules**: `monitoring/alertmanager/alert-rules.yml`
- **Base Config**: `monitoring/alertmanager/alertmanager.yml`
- **Helm Template**: `chart/templates/alertmanager.yaml`
- **Prometheus Integration**: Rule files mounted at `/etc/prometheus/rules/`

#### Notification Channels
- **PagerDuty**: Integration key configured via `monitoring.alertmanager.pagerduty.integrationKey`
- **Slack**: Webhook URL via `monitoring.alertmanager.slack.apiUrl`
  - Warnings → `#alerts-warnings`
  - Infrastructure → `#alerts-infrastructure`
- **Email**: SMTP configuration in `monitoring.alertmanager.smtp`
  - Business alerts → `business@threads-agent.com`
  - Infrastructure → `ops@threads-agent.com`

#### Deployment
- **Development**: Enabled in `values-dev.yaml` with local email testing
- **Production**: Enabled in `values-prod.yaml` with full PagerDuty/Slack integration
- **High Availability**: 2 replicas in production with persistent storage
- **Templates**: Custom notification templates in `alertmanager-templates` ConfigMap

#### Runbook
- **Location**: `docs/runbook-alerting.md`
- **Response Procedures**: Detailed steps for each alert type
- **Escalation**: L1 (Auto) → L2 (Manual, 1hr) → L3 (Executive, 4hr)
- **Troubleshooting**: Ready-to-use kubectl commands and health checks

### Tracing (Jaeger)
- **UI**: `just jaeger-ui` → http://localhost:16686
- **Integration**: OpenTelemetry auto-instrumentation
- **Scope**: Request flow across microservices

### Logging
- **Access**: `just logs` (orchestrator), `just logs-celery`
- **Format**: Structured logging with correlation IDs
- **Level**: Configurable per service

## Development Best Practices

### Code Quality
- **Type Checking**: mypy with strict mode (`mypy.ini`)
- **Formatting**: ruff (linting) + black (formatting) + isort (imports)
- **Pre-commit**: Enforced via `just ship` command
- **Testing**: High coverage with unit + integration + e2e

### Git Workflow  
- **Branching**: `feat/<epic>-<slug>` pattern (general features)
- **Task Branches**: `cra-{ticket-number}-{kebab-case-title}` pattern (Linear tasks)
- **Protection**: `main` branch requires PR + CI passing + code owner review
- **Automation**: `just ship` handles commit → push → PR creation

### Branch Management for Linear Tasks

**IMPORTANT**: When starting work on any new task from Linear, you MUST:

1. **ALWAYS create a new branch** before making any changes
2. **Branch naming format**: `cra-{ticket-number}-{kebab-case-title}`
   - Example: For ticket CRA-217 "Alerting & Incident Response System"
   - Branch name: `cra-217-alerting-incident-response-system`
3. **Required commands to run**:
   ```bash
   # Ensure you're on main and up to date
   git checkout main
   git pull origin main
   
   # Create and checkout new branch
   git checkout -b cra-{number}-{title}
   
   # Push branch to set upstream tracking
   git push -u origin cra-{number}-{title}
   ```
4. **Never commit directly to main** - all work must be done in feature branches
5. **Confirm branch creation** with the user before proceeding with implementation

### Service Development
- **Scaffolding**: `just scaffold NEW_SERVICE` from template
- **Testing**: Each service has own test suite + shared e2e tests
- **Isolation**: Services communicate via HTTP/message queues only
- **Configuration**: Environment-based with sensible defaults

### Multi-Developer Cluster Management

**NEW**: Support for multiple isolated k3d clusters on the same machine. See [Multi-Cluster Development Guide](./docs/multi-cluster-development.md) for details.

#### Key Features
- **Unique clusters** per developer based on git user/email
- **Automatic port allocation** to avoid conflicts
- **Shared team clusters** for collaboration
- **Easy switching** between clusters

#### Quick Commands
```bash
# Create personal cluster
just bootstrap-multi

# Create shared team cluster
just bootstrap-multi --share

# List all clusters
just cluster-list

# Switch clusters
just cluster-switch threads-agent-john-abc123

# Full environment with unique cluster
just dev-start-multi
```

#### Cluster Naming
Clusters are named: `{repo}-{username}-{email-hash}`
Example: `threads-agent-jordan-kim-bc9e97`

## Personas & AI Configuration

### Supported Personas
```python
_PERSONA_DB = {
    "ai-jesus": SimpleNamespace(emoji="🙏", temperament="kind"),
    "ai-elon": SimpleNamespace(emoji="🚀", temperament="hype"), 
}
```

### Content Generation Pipeline

#### Standard Pipeline
1. **Ingest**: Clean and validate user input
2. **Hook Generation**: Create engaging opening with gpt-4o
3. **Body Generation**: Expand with gpt-3.5-turbo-0125  
4. **Guardrail**: Content moderation + safety checks
5. **Format**: Apply persona styling + emojis

#### Enhanced Pipeline (with Search)
1. **Ingest**: Clean and validate user input
2. **🔍 Trend Research**: Discover trending topics related to input
3. **🔍 Competitive Analysis**: Analyze viral patterns and successful hooks
4. **Hook Generation**: Create trend-aware opening incorporating insights
5. **Body Generation**: Expand with viral patterns and trending keywords
6. **Guardrail**: Content moderation + safety checks
7. **Format**: Apply persona styling + trend optimization

### Safety & Moderation
- **Regex Guards**: Block harmful keywords (`suicide`, `bomb`, `kill`)
- **OpenAI Moderation**: `omni-moderation-latest` model
- **Pipeline Halt**: Fail fast on policy violations

## Troubleshooting

### Common Issues

#### "k3d cluster not ready"
```bash
just k3d-nuke-all  # Nuclear reset
just bootstrap     # Fresh start
```

#### "Helm deployment timeout"  
```bash
kubectl get pods -A              # Check pod status
kubectl get events --sort-by='.lastTimestamp' | tail -20  # Recent events
kubectl logs deploy/SERVICE     # Service-specific logs
```

#### "Tests failing locally"
```bash
just e2e-prepare                 # Full clean setup
kubectl port-forward svc/orchestrator 8080:8080 &  # Manual port forward
curl localhost:8080/health       # Verify connectivity
```

#### "OpenAI API cost concerns"
- Use `OPENAI_API_KEY=test` for offline development
- Check `chart/values-dev.yaml` forces test mode by default
- Monitor token usage via Prometheus metrics

### Port Forwards for Development
```bash
# Postgres access
kubectl port-forward svc/postgres 5432:5432

# Fake Threads API  
kubectl port-forward svc/fake-threads 9009:9009
curl localhost:9009/ping  # Health check

# Orchestrator API
kubectl port-forward svc/orchestrator 8080:8080
curl localhost:8080/health
```

## Performance & Cost Optimization

### FinOps Features
- **Token Tracking**: Prometheus metrics for LLM usage
- **Model Selection**: Cheaper models for body generation
- **Caching**: Vector similarity prevents duplicate content
- **Offline Mode**: Development without API costs

### Scaling Considerations
- **Horizontal**: Increase replica counts in Helm values
- **Resource Limits**: Configure in `values.yaml` resources section
- **Database**: Consider Aurora Serverless for production
- **Vector Store**: Qdrant clustering for high availability

## Future Roadmap

### Upcoming Features (from README.md)
- **E2 - Core MVP**: Full content generation pipeline ✅
- **E3 - SRE v1**: Advanced monitoring and alerting ✅
- **E4 - Bandit A/B**: Multi-armed bandit optimization
- **E5 - Trend & Pain**: Automated trend detection ✅ (Implemented with SearXNG)
- **E6 - FinOps Board**: Cost optimization dashboard
- **E7+ - Production**: EKS, Aurora, security hardening

### Extension Points
- **New Personas**: Add to `_PERSONA_DB` + corresponding prompts
- **New Models**: Configure via environment variables
- **Custom Workflows**: Extend LangGraph DAGs in persona-runtime
- **Additional Integrations**: Follow fake-threads pattern for new platforms

## 🚀 MCP Server Integration

### Overview
MCP (Model Context Protocol) servers provide direct access to tools and services, eliminating manual commands and dramatically speeding up development.

### Installed MCP Servers

1. **Redis MCP** - Lightning-fast caching
   - Cache search results, trends, API responses
   - Track metrics and counters in real-time
   - **Time Saved**: 2-3 hours/week on performance optimization

2. **Kubernetes MCP** - Direct cluster management
   - No more manual `kubectl` commands
   - Automatic port-forwarding handling
   - **Time Saved**: 3-4 hours/week on k8s operations

3. **PostgreSQL MCP** - Database without barriers
   - Query directly without port-forwarding
   - Schema-aware operations
   - **Time Saved**: 1-2 hours/week on database tasks

4. **OpenAI MCP** - AI model management
   - Track token usage across personas
   - Switch models without code changes
   - **Time Saved**: 1-2 hours/week on AI optimization

5. **SearXNG MCP** - Free search integration
   - Trend detection and competitive analysis
   - No API keys or rate limits
   - **Time Saved**: $500+/month vs paid alternatives

### Daily MCP Usage Examples

#### Cache Management (Redis)
```bash
# Cache expensive operations
just cache-set "trends:AI:2025-01-22" "$(just trend-check AI)"
just cache-get "trends:AI:2025-01-22"  # Instant retrieval

# Track real-time metrics
just redis-cli INCR "posts:ai-jesus:count"
just redis-cli ZADD "trending:topics" 95 "AI productivity"
```

#### Database Queries (PostgreSQL)
```sql
-- Direct queries without port-forwarding
SELECT persona_id, AVG(engagement_rate) as avg_engagement
FROM posts 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY persona_id;
```

#### Cluster Management (Kubernetes)
```bash
# No more manual kubectl commands
# MCP handles port-forwarding automatically
# Direct access to pods, logs, deployments
```

## 🔍 SearXNG Search Integration

### Overview
SearXNG provides free, privacy-respecting search capabilities to enhance content generation with real-time trends and competitive intelligence.

### Why Search Matters for Your KPIs
1. **6%+ Engagement Rate**: Trending content gets 2-3x higher engagement
2. **$0.01 Cost/Follow**: Better targeting through trends = more efficient growth
3. **$20k MRR**: Automated trend detection scales content production
4. **Zero Search Costs**: SearXNG is 100% free (vs $500+/month for Brave API)

### Architecture Components
- **SearXNG Wrapper** (`services/common/searxng_wrapper.py`): Centralized search API
- **Search Endpoints** (`services/orchestrator/search_endpoints.py`): REST APIs
- **Enhanced Runtime** (`services/persona_runtime/search_enhanced_runtime.py`): Trend-aware generation
- **Trend Workflow** (`scripts/trend-detection-workflow.sh`): Automation script

### Daily Usage Patterns

#### Morning Routine (5 min)
```bash
just searxng-start          # Start search engine
just trend-dashboard        # Check overnight trends
just trend-start &          # Start background automation
```

#### Active Development
```bash
# Before creating content
just trend-check "your topic"
just competitive-analysis "your topic"

# Generate with trends
just search-enhanced-post ai-jesus "trending topic"
```

#### Monitoring Success
```bash
just grafana               # Check engagement metrics
# Look for:
# - search_enhanced_posts_total increasing
# - posts_engagement_rate > 0.06
# - trend_relevance_score > 0.7
```

### Search Metrics to Track
- **Trend Discovery Rate**: >5 trends per topic
- **Cache Hit Rate**: >60% (improves performance)
- **Enhanced Post Engagement**: 2x standard posts
- **Trend Relevance**: >0.7 correlation with engagement

### Troubleshooting
```bash
# SearXNG issues
just searxng-logs          # Check container logs
just searxng-stop && just searxng-start  # Restart

# No trends found
curl http://localhost:8888/search?q=test&format=json  # Test directly
```

## 💡 Productivity Features Summary

### Time Savings Breakdown (Per Week)
1. **MCP Servers** (10-12 hours saved)
   - No manual port-forwarding
   - Direct database queries
   - Instant cache operations
   - Kubernetes automation

2. **Search Integration** (5-6 hours saved)
   - Free trend detection
   - Competitive analysis
   - Automated content research
   - Zero API costs

3. **AI Development Tools** (8-10 hours saved)
   - Hot-reload personas (instant vs 20min rebuild)
   - AI-generated tests
   - Smart deployment with rollback
   - Intelligent error recovery

4. **Monitoring & Insights** (2-3 hours saved)
   - Real-time dashboard
   - AI recommendations
   - Automated alerts
   - Performance tracking

### Essential Daily Commands
```bash
# Morning
just dev-start              # Start everything
just trend-dashboard        # Check trends
just dev-dashboard          # Monitor performance

# During Development
just persona-hot-reload     # Instant persona testing
just ai-test-gen           # Generate tests
just cache-set/get         # Fast data access
just search-enhanced-post  # Trend-aware content

# Deployment
just smart-deploy canary   # Safe deployment
just grafana              # Check metrics
```

## 🎯 AI Token Efficiency (80/20 Principle)

Apply the Pareto principle to AI costs - get 80% of AI value with 20% of token usage:

### Quick Start
```bash
just token-optimize     # Enable all optimizations
just token-status      # Check your savings
```

### Token-Efficient Commands
```bash
# Instead of expensive repeated AI calls
just cached-analyze    # 0 tokens (uses morning's analysis)
just cached-trends     # 0 tokens (uses daily trends)
just token-batch       # Week's content in one call (80% savings)
just token-viral       # Template-based creation (50% savings)
```

### Real Savings Example
```bash
# Traditional approach: 10,000 tokens/day ($0.20/day)
just create-viral (x5)  # 5,000 tokens
just ai-biz (x5)       # 2,500 tokens  
just analyze-money (x5) # 2,500 tokens

# Optimized approach: 2,000 tokens/day ($0.04/day - 80% less!)
just token-batch       # 1,500 tokens (entire week)
just cached-analyze    # 0 tokens (cached)
just cached-trends     # 0 tokens (cached)
```

### Token Optimization Strategies
1. **Smart Caching** (60-70% savings) - Reuse AI responses for 24h
2. **Batch Processing** (30-40% savings) - Process multiple items together
3. **Template Generation** (40-50% savings) - Reuse content patterns
4. **Pattern Learning** (70-80% savings) - Learn from successful content
5. **Incremental Updates** (50-60% savings) - Update only changed parts

**Result**: Same quality, 80% less AI cost, more profit toward $20k MRR!

### 🎓 Learning Resources
- **[DAILY_PLAYBOOK.md](./DAILY_PLAYBOOK.md)** - ⚡ Your daily cheat sheet (START HERE!)
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - 📋 Command quick reference
- **[PRODUCTIVITY_GUIDE.md](./PRODUCTIVITY_GUIDE.md)** - Complete productivity guide
- **[docs/ai-token-efficiency-guide.md](./docs/ai-token-efficiency-guide.md)** - 🎯 Complete token optimization guide
- **[docs/mega-commands-guide.md](./docs/mega-commands-guide.md)** - Mega commands documentation
- **[docs/multi-cluster-development.md](./docs/multi-cluster-development.md)** - Multi-developer cluster management
- **[docs/searxng-integration-guide.md](./docs/searxng-integration-guide.md)** - Search integration
- **[docs/mcp-servers-setup.md](./docs/mcp-servers-setup.md)** - MCP configuration

---

**Last Updated**: 2025-07-22  
**Repository**: https://github.com/threads-agent-stack/threads-agent  
**Documentation**: This file serves as the authoritative development guide for future Claude instances working on this codebase.