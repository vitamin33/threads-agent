# CLAUDE.md - Threads-Agent Stack Development Guide

## Project Overview

**Threads-Agent Stack** is a production-grade, multi-persona AI agent system that:
- Researches trends and generates AI-powered Threads content
- Uses a microservices architecture on Kubernetes
- Implements LangGraph workflows with LLM integration (OpenAI)
- Includes comprehensive monitoring, testing, and FinOps capabilities
- Goal: Achieve 6%+ engagement rate and $0.01 cost/follow, scaling to $20k MRR

## Architecture

### Microservices Structure
```
services/
├── orchestrator/        # FastAPI coordinator + Celery task dispatcher
├── celery_worker/      # Background task processor + SSE
├── persona_runtime/    # LangGraph DAG factory with LLM calls
├── fake_threads/       # Mock Threads API for testing
└── common/            # Shared utilities (metrics, OpenAI wrapper)
```

### Core Technologies
- **Language**: Python 3.12+
- **Frameworks**: FastAPI, Celery, LangGraph, SQLAlchemy
- **Infrastructure**: k3d (local), Kubernetes, Helm
- **Databases**: PostgreSQL, Qdrant (vector store)
- **Messaging**: RabbitMQ
- **Monitoring**: Prometheus, OpenTelemetry, Jaeger
- **AI/ML**: OpenAI API, optional LoRA support via PEFT

## Development Workflow

### Prerequisites
- Docker >= 24
- k3d >= 5.6  
- Helm >= 3.14
- Python 3.12+
- just (command runner)

### Quick Start
```bash
git clone git@github.com:threads-agent-stack/threads-agent.git
cd threads-agent
just bootstrap        # Spin up k3d cluster
just images           # Build and import all service images
just deploy-dev       # Deploy with Helm
just test             # Run full test suite
```

### Key Commands (justfile)

#### Development
- `just bootstrap` - Create fresh k3d cluster with networking
- `just images` - Build all service Docker images and import to k3d
- `just deploy-dev` - Helm install with dev values
- `just logs` / `just logs-celery` - View service logs

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
- **Dependencies**: PostgreSQL, RabbitMQ, Qdrant

### Celery Worker (`services/celery_worker/`)  
- **Purpose**: Background task processing with SSE updates
- **Tasks**: `tasks.queue_post` - Full content generation pipeline
- **Features**: Server-Sent Events for real-time progress
- **Integration**: Calls persona-runtime, posts to fake-threads

### Persona Runtime (`services/persona_runtime/`)
- **Purpose**: LangGraph DAG execution with LLM calls
- **Workflow**: ingest → hook_llm → body_llm → guardrail → format
- **Models**: Configurable via env vars (`HOOK_MODEL`, `BODY_MODEL`)
- **Safety**: Content moderation + regex guardrails
- **Offline Mode**: Deterministic stubs when `OPENAI_API_KEY=test`

### Fake Threads (`services/fake_threads/`)
- **Purpose**: Mock Threads API for development/testing
- **Endpoints**: 
  - `POST /publish` - Accept generated content
  - `GET /published` - List all published content
  - `GET /ping` - Health check

### Common (`services/common/`)
- **Metrics**: Prometheus instrumentation helpers
- **OpenAI Wrapper**: Centralized LLM client with token counting
- **Shared across**: All services import common utilities

## Configuration & Secrets

### Environment Variables

#### Orchestrator
- `RABBITMQ_URL` - Celery broker connection
- `PERSONA_RUNTIME_URL` - Service-to-service communication  
- `DATABASE_URL` - PostgreSQL connection
- `QDRANT_URL` - Vector store connection

#### Persona Runtime  
- `OPENAI_API_KEY` - OpenAI API access (use "test" for offline mode)
- `HOOK_MODEL` - Model for hook generation (default: gpt-4o)
- `BODY_MODEL` - Model for body generation (default: gpt-3.5-turbo-0125)
- `LORA_PATH` - Optional LoRA adapter path

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

## Personas & AI Configuration

### Supported Personas
```python
_PERSONA_DB = {
    "ai-jesus": SimpleNamespace(emoji="🙏", temperament="kind"),
    "ai-elon": SimpleNamespace(emoji="🚀", temperament="hype"), 
}
```

### Content Generation Pipeline
1. **Ingest**: Clean and validate user input
2. **Hook Generation**: Create engaging opening with gpt-4o
3. **Body Generation**: Expand with gpt-3.5-turbo-0125  
4. **Guardrail**: Content moderation + safety checks
5. **Format**: Apply persona styling + emojis

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
- **E2 - Core MVP**: Full content generation pipeline
- **E3 - SRE v1**: Advanced monitoring and alerting  
- **E4 - Bandit A/B**: Multi-armed bandit optimization
- **E5 - Trend & Pain**: Automated trend detection
- **E6 - FinOps Board**: Cost optimization dashboard
- **E7+ - Production**: EKS, Aurora, security hardening

### Extension Points
- **New Personas**: Add to `_PERSONA_DB` + corresponding prompts
- **New Models**: Configure via environment variables
- **Custom Workflows**: Extend LangGraph DAGs in persona-runtime
- **Additional Integrations**: Follow fake-threads pattern for new platforms

---

**Last Updated**: 2025-07-22  
**Repository**: https://github.com/threads-agent-stack/threads-agent  
**Documentation**: This file serves as the authoritative development guide for future Claude instances working on this codebase.