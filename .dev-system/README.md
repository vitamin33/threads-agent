# AI Agent Development System

> **🚀 From Solo Dev to Top 1% Agent Factory**
> 
> This directory contains the complete development system for building, measuring, and optimizing AI agent workflows. Designed for easy extraction to a separate repository.

## Structure

```
.dev-system/
├── README.md              # This file
├── config/               # Configuration management
│   ├── dev-system.yaml   # Main config
│   ├── agents.yaml       # Agent definitions
│   └── environments.yaml # Environment configs
├── ops/                  # Operations & Infrastructure  
│   ├── telemetry.py      # M1: Metrics collection
│   ├── secrets.py        # Secret management
│   ├── release.py        # M4: Canary/rollback
│   └── health.py         # System health checks
├── evals/                # Quality Gates & Testing
│   ├── suites/          # Golden test suites
│   ├── run.py           # M2: Eval runner
│   ├── gate.py          # CI gates
│   └── reports/         # Evaluation reports
├── prompts/              # Prompt Management
│   ├── registry/        # M3: Versioned prompts
│   ├── contracts/       # Tool contracts
│   └── testing/         # Prompt tests
├── planner/              # Smart Planning System
│   ├── brief.py         # M5: Morning briefs
│   ├── debrief.py       # Evening analysis
│   ├── ice.py           # ICE scoring
│   └── context/         # Planning context
├── knowledge/            # Knowledge Management
│   ├── corpus/          # M6: RAG documents
│   ├── ingest.py        # Data ingestion
│   ├── index.py         # Search indexing
│   └── sync.py          # Content sync
├── agents/               # Agent Coordination
│   ├── coordination.py  # Multi-agent sync
│   ├── worktree.py      # Worktree management
│   └── distribution.py  # Task distribution
├── dashboard/            # Observability
│   ├── metrics.py       # M9: Health dashboard
│   ├── templates/       # Dashboard templates
│   └── alerts.py        # Alert management
├── cli/                  # Command Line Tools
│   ├── dev-system       # Main CLI entry
│   ├── metrics-today    # Daily metrics
│   ├── eval-report      # Evaluation reports
│   └── wt-bootstrap     # Worktree setup
├── workflows/            # Workflow Management  
│   ├── epics/           # Epic definitions
│   ├── features/        # Feature specs
│   ├── planning.py      # AI planning integration
│   └── automation.py    # Workflow automation
└── scripts/              # Legacy Scripts (to be migrated)
    └── migration-map.md  # Migration tracking
```

## Quick Start

```bash
# Initialize development system
./.dev-system/cli/dev-system init

# Daily workflow
./.dev-system/cli/metrics-today          # Check yesterday's metrics
./.dev-system/cli/dev-system brief       # Get morning priorities
./.dev-system/cli/dev-system worktree    # Setup parallel development

# Quality gates
./.dev-system/evals/run.py --suite core  # Run evaluations
./.dev-system/ops/release.py canary 10   # Deploy with canary
```

## Milestones Implementation Order

1. **M1** (telemetry) → `ops/telemetry.py`
2. **M2** (CI gates) → `evals/suites/core.yaml`
3. **M5** (planner) → `planner/brief.py`
4. **M4** (release) → `ops/release.py`
5. **M3** (prompts) → `prompts/registry/`
6. **M6** (knowledge) → `knowledge/corpus/`
7. **M7-M9** (scale) → Complete system

## Integration Points

- **Justfile**: Commands reference `.dev-system/cli/*`
- **CI/CD**: Uses `.dev-system/evals/*` for gates
- **Services**: Import from `.dev-system/ops/*`
- **Scripts**: Gradually migrate to `.dev-system/`

## Extraction Readiness

This structure is designed for easy extraction:
- Self-contained dependencies
- Clear external interfaces  
- Minimal threads-agent coupling
- Complete documentation