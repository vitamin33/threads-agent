# Script Migration Mapping

This file tracks the migration of legacy scripts to the new `.dev-system/` structure.

## Core Development System Scripts

### High Priority (Move First)
| Legacy Script | New Location | Status | Notes |
|---------------|--------------|--------|-------|
| `scripts/workflow-automation.sh` | `.dev-system/cli/dev-system` | 🔄 Planned | Main workflow entry point |
| `scripts/setup-4-agents.sh` | `.dev-system/cli/wt-bootstrap` | 🔄 Planned | Worktree setup |
| `scripts/ai-epic-planner.sh` | `.dev-system/planner/brief.py` | 🔄 Planned | AI planning integration |
| `scripts/quality-gates.sh` | `.dev-system/evals/gate.py` | 🔄 Planned | Quality gate enforcement |
| `scripts/auto-commit.sh` | `.dev-system/ops/auto-commit.py` | 🔄 Planned | Safety net automation |

### Medium Priority (Move Second)  
| Legacy Script | New Location | Status | Notes |
|---------------|--------------|--------|-------|
| `scripts/agent-*.sh` | `.dev-system/agents/` | 🔄 Planned | Agent coordination |
| `scripts/ai-*.sh` | `.dev-system/planner/` | 🔄 Planned | AI workflow helpers |
| `scripts/smart-deploy.sh` | `.dev-system/ops/release.py` | 🔄 Planned | Release automation |
| `scripts/collect-real-metrics*.sh` | `.dev-system/ops/telemetry.py` | 🔄 Planned | Metrics collection |

### Low Priority (Move Last)
| Legacy Script | New Location | Status | Notes |
|---------------|--------------|--------|-------|
| `scripts/business-*.sh` | Keep in `scripts/` | ✅ Keep | Business-specific logic |
| `scripts/trend-*.sh` | Keep in `scripts/` | ✅ Keep | Domain-specific functionality |
| `scripts/validate-*.sh` | `.dev-system/evals/` | 🔄 Planned | Validation helpers |

## Migration Strategy

### Phase 1: Core Infrastructure
1. **Workflow automation** → CLI entry point
2. **Agent coordination** → Multi-agent system  
3. **Quality gates** → Evaluation system

### Phase 2: Operational Systems
1. **Telemetry collection** → Metrics system
2. **Release automation** → Deployment system
3. **Planning integration** → AI planning

### Phase 3: Cleanup
1. **Update path references** in justfile, docs, CI
2. **Remove legacy scripts** after verification
3. **Update documentation** with new paths

## Backward Compatibility

During migration, maintain backward compatibility:
- Legacy scripts proxy to new locations
- Gradual deprecation warnings  
- Documentation updates

## Status Legend
- ✅ Complete
- 🔄 Planned  
- ❌ Skip
- 🚧 In Progress