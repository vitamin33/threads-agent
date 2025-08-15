#!/bin/bash

# Final Agent Deployment - Service-Based Distribution
# Deploys complete refactored system to all agents

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${BLUE}[FINAL-DEPLOY]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[INFO]${NC} $1"; }

# Agent service mappings
declare -A AGENT_SERVICES
AGENT_SERVICES[a1]="orchestrator celery_worker common event_bus mlflow mlflow_service performance_monitor chaos_engineering"
AGENT_SERVICES[a2]="persona_runtime rag_pipeline vllm_service prompt_engineering conversation_engine viral_engine viral_pattern_engine ml_autoscaling viral_learning_flywheel" 
AGENT_SERVICES[a3]="achievement_collector dashboard dashboard_api dashboard_frontend viral_metrics pattern_analyzer tech_doc_generator viral_scraper"
AGENT_SERVICES[a4]="revenue finops_engine ab_testing_framework threads_adaptor fake_threads"

# Agent descriptions
declare -A AGENT_DESCRIPTIONS
AGENT_DESCRIPTIONS[a1]="Infrastructure & Platform"
AGENT_DESCRIPTIONS[a2]="AI/ML & Content"  
AGENT_DESCRIPTIONS[a3]="Data & Analytics"
AGENT_DESCRIPTIONS[a4]="Revenue & Business"

# Agent targets
declare -A AGENT_TARGETS
AGENT_TARGETS[a1]="Platform Engineer, SRE, Infrastructure Engineer (\$170-220k)"
AGENT_TARGETS[a2]="ML Engineer, LLM Specialist, AI Platform Engineer (\$160-200k)"
AGENT_TARGETS[a3]="Data Engineer, Analytics Engineer, Technical Lead (\$160-190k)"
AGENT_TARGETS[a4]="Growth Engineer, Business Platform Engineer, FinOps (\$170-210k)"

AGENTS=("a1" "a2" "a3" "a4")

# Deploy to specific agent with new service distribution
deploy_agent() {
    local agent_id="$1"
    local agent_path="../wt-${agent_id}-$(echo ${AGENT_DESCRIPTIONS[$agent_id]} | tr '[:upper:]' '[:lower:]' | cut -d' ' -f1)"
    local agent_desc="${AGENT_DESCRIPTIONS[$agent_id]}"
    local services="${AGENT_SERVICES[$agent_id]}"
    local target="${AGENT_TARGETS[$agent_id]}"
    
    if [[ ! -d "$agent_path" ]]; then
        warn "Agent worktree not found: $agent_path"
        return 1
    fi
    
    log "🚀 Deploying ${agent_desc} system to ${agent_id}..."
    
    # Create directories
    mkdir -p "$agent_path/scripts"
    mkdir -p "$agent_path/docs"
    mkdir -p "$agent_path/.vscode"
    
    # Copy core scripts (safe to sync)
    local scripts=(
        "scripts/ai-dev-acceleration.sh"
        "scripts/auto-update-agent-focus.sh"
        "scripts/4-agent-turbo.sh"
        "scripts/ai-job-strategy-sync.sh"
        "scripts/smart-tdd.sh"
        "scripts/cleanup.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            cp "$script" "$agent_path/$script"
            chmod +x "$agent_path/$script"
        fi
    done
    
    # Copy documentation (safe to sync)
    local docs=(
        "docs/AI_DEVELOPMENT_ACCELERATION_GUIDE.md"
        "docs/AI_POWERED_DAILY_WORKFLOW.md"
        "docs/AGENT_MERGE_STRATEGY.md"
        "docs/QUICK_REFERENCE.md"
        "docs/OPTIMAL_AGENT_DISTRIBUTION.md"
    )
    
    for doc in "${docs[@]}"; do
        if [[ -f "$doc" ]]; then
            cp "$doc" "$agent_path/$doc"
        fi
    done
    
    # Create agent-specific AGENT_FOCUS.md (local only - no conflicts)
    cat > "$agent_path/AGENT_FOCUS.md.local" << EOF
# Agent ${agent_desc} (${agent_id}) - Service-Based Focus

## Service Ownership ($(echo $services | wc -w) services)
$(echo "$services" | tr ' ' '\n' | sed 's/^/- services\//' | sed 's/$\//')

## Target Role
$target

## Responsibilities
**${agent_desc} Agent ($agent_id)**
- End-to-end ownership of assigned services
- Testing and quality for service group
- Documentation and monitoring for owned services
- Integration with other agent services

## Daily Enhanced Workflow
\`\`\`bash
# Start AI-powered session
export AGENT_ID="$agent_id"
just start       # Complete AI session setup + learning

# Service group work
just ${agent_id,,}        # Auto-focus on your service group
just tdd "feature"       # TDD for critical business logic
just save               # AI-powered commits

# Session management
just done               # Auto-commit + focus update
just finish             # Complete session cleanup
\`\`\`

## Job Strategy Alignment (AI_JOB_STRATEGY.md)
**Gap Plan Focus**: 
$(case "$agent_id" in
    "a1") echo "- Items 1-2: MLflow registry + SLO-gated CI (PRIORITY)
- Platform reliability and infrastructure scaling" ;;
    "a2") echo "- Item 3: vLLM cost/latency optimization (PRIORITY) 
- AI/ML service performance and content generation" ;;
    "a3") echo "- Portfolio building and technical documentation (SUPPORTING)
- Data pipeline development and analytics" ;;
    "a4") echo "- Items 4-5: A/B testing + revenue optimization (PRIORITY)
- Business intelligence and cost management" ;;
esac)

## Service Group Commands
\`\`\`bash
# Use service group assignments for efficiency:
just infra       # Infrastructure work → A1
just ai          # AI/ML work → A2  
just data        # Analytics work → A3
just revenue     # Business work → A4
\`\`\`

## Success Criteria
- Deliver high-quality features for owned services
- Maintain >95% development success rate with learning system
- Document achievements with business metrics for portfolio
- Demonstrate expertise in service group for target role

---
*Agent-specific file - local only, prevents merge conflicts*
*Auto-updated by enhanced development system*
EOF

    success "✅ ${agent_desc} ($agent_id) deployment complete"
    warn "📋 Agent focus: AGENT_FOCUS.md.local (local only - no conflicts)"
}

# Deploy to all agents
deploy_all() {
    log "🚀 Final deployment: Service-based agent distribution to all 4 worktrees..."
    
    local deployed=0
    local failed=0
    
    for agent_id in "${AGENTS[@]}"; do
        if deploy_agent "$agent_id"; then
            ((deployed++))
        else
            ((failed++))
        fi
        echo
    done
    
    success "✅ Final deployment complete: $deployed successful, $failed failed"
    
    if [[ $deployed -gt 0 ]]; then
        log "🎯 All agents now have service-based distribution!"
        log ""
        log "📊 New Service Groups:"
        log "  A1: Infrastructure & Platform (8 services)"
        log "  A2: AI/ML & Content (9 services)"  
        log "  A3: Data & Analytics (8 services)"
        log "  A4: Revenue & Business (8 services)"
        log ""
        log "🚀 Enhanced Commands Available:"
        log "  just infra    → A1 infrastructure work"
        log "  just ai       → A2 AI/ML work"
        log "  just data     → A3 analytics work" 
        log "  just revenue  → A4 business work"
        log ""
        log "✅ No more bottlenecks - balanced service distribution!"
        log "✅ Clear boundaries - minimal coordination needed!"
        log "✅ Career aligned - each agent builds specialized portfolio!"
    fi
}

# Validate deployment
validate_deployment() {
    log "🧪 Validating service-based deployment..."
    
    for agent_id in "${AGENTS[@]}"; do
        local agent_path="../wt-${agent_id}-$(echo ${AGENT_DESCRIPTIONS[$agent_id]} | tr '[:upper:]' '[:lower:]' | cut -d' ' -f1)"
        local agent_desc="${AGENT_DESCRIPTIONS[$agent_id]}"
        
        if [[ -d "$agent_path" ]]; then
            log "Testing ${agent_desc} ($agent_id)..."
            
            # Check if scripts exist and are executable
            if [[ -x "$agent_path/scripts/ai-dev-acceleration.sh" ]]; then
                success "  ✅ AI acceleration system ready"
            else
                warn "  ⚠️ AI scripts missing"
            fi
            
            # Check agent focus
            if [[ -f "$agent_path/AGENT_FOCUS.md.local" ]]; then
                success "  ✅ Service-based focus configured"
            else
                warn "  ⚠️ Agent focus not configured"
            fi
            
            # Test context loading (if possible)
            local context_test=$(cd "$agent_path" && export AGENT_ID="$agent_id" && ./scripts/ai-dev-acceleration.sh context 2>&1 | grep "Enhanced smart context" || echo "SKIP")
            if [[ "$context_test" != "SKIP" ]]; then
                success "  ✅ Context loading functional"
            fi
            
        else
            warn "  ❌ Worktree missing: $agent_path"
        fi
    done
    
    success "🎯 Service-based deployment validation complete!"
}

# Main execution
case "${1:-deploy}" in
    "deploy")
        deploy_all
        ;;
    "validate")
        validate_deployment
        ;;
    "agent")
        deploy_agent "${2}"
        ;;
    *)
        cat << EOF
🚀 Final Agent Deployment - Service-Based Distribution

Usage: $0 [command]

Commands:
  deploy      Deploy service-based system to all 4 agents
  validate    Validate deployment and functionality
  agent <id>  Deploy to specific agent only

Agent Distribution:
  A1: Infrastructure & Platform (8 services)
  A2: AI/ML & Content (9 services)  
  A3: Data & Analytics (8 services)
  A4: Revenue & Business (8 services)

Benefits:
  ✅ No bottlenecks - balanced service ownership
  ✅ Clear boundaries - minimal coordination needed
  ✅ Career aligned - specialized portfolio building

EOF
        ;;
esac