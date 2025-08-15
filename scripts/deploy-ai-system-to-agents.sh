#!/bin/bash

# Deploy AI Development System to All 4 Agent Worktrees
# After successful testing on A1

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[DEPLOY]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Files to sync to all agents
CORE_FILES=(
    "Justfile"
    "AI_JOB_STRATEGY.md"
    ".pre-commit-config.yaml"
    ".vscode/settings.json"
)

SCRIPT_FILES=(
    "scripts/ai-dev-acceleration.sh"
    "scripts/auto-update-agent-focus.sh"  
    "scripts/4-agent-turbo.sh"
    "scripts/ai-job-strategy-sync.sh"
    "scripts/cleanup.sh"
)

DOC_FILES=(
    "docs/AI_DEVELOPMENT_ACCELERATION_GUIDE.md"
    "docs/AI_POWERED_DAILY_WORKFLOW.md" 
    "docs/AGENT_MERGE_STRATEGY.md"
)

AGENT_WORKTREES=(
    "../wt-a1-mlops:a1:MLOps"
    "../wt-a2-genai:a2:GenAI"
    "../wt-a3-analytics:a3:Analytics"
    "../wt-a4-platform:a4:Platform"
)

# Deploy to specific agent
deploy_to_agent() {
    local agent_path="$1"
    local agent_id="$2"
    local agent_type="$3"
    
    if [[ ! -d "$agent_path" ]]; then
        error "Agent worktree not found: $agent_path"
        return 1
    fi
    
    log "🚀 Deploying AI system to $agent_type ($agent_id)..."
    
    # Create directories
    mkdir -p "$agent_path/scripts"
    mkdir -p "$agent_path/docs"
    mkdir -p "$agent_path/.vscode"
    mkdir -p "$agent_path/reports"
    
    # Copy core files
    for file in "${CORE_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            cp "$file" "$agent_path/"
            log "  ✅ Copied $file"
        else
            warn "  ⚠️ File not found: $file"
        fi
    done
    
    # Copy scripts
    for script in "${SCRIPT_FILES[@]}"; do
        if [[ -f "$script" ]]; then
            cp "$script" "$agent_path/$script"
            chmod +x "$agent_path/$script"
            log "  ✅ Copied $script (executable)"
        else
            warn "  ⚠️ Script not found: $script"
        fi
    done
    
    # Copy documentation
    for doc in "${DOC_FILES[@]}"; do
        if [[ -f "$doc" ]]; then
            cp "$doc" "$agent_path/$doc"
            log "  ✅ Copied $doc"
        else
            warn "  ⚠️ Doc not found: $doc"
        fi
    done
    
    # Create agent-specific AGENT_FOCUS.md
    cat > "$agent_path/AGENT_FOCUS.md" << EOF
# Agent $agent_type ($agent_id) Focus Areas

## Current Sprint Goals (Job Strategy Aligned)
- Implement AI development acceleration system
- Focus on $agent_type specialization for US remote AI roles
- Integrate learning system with development workflows
- Build portfolio evidence for \$160-220k positions

## Agent Specialization
**$agent_type Agent ($agent_id)**
$(case "$agent_id" in
    "a1") echo "- MLOps: MLflow registry, SLO-gated CI, monitoring
- Target Role: Senior MLOps Engineer (\$180-220k)
- Priority: Gap plan items 1-2 (MLflow + SLO gates)" ;;
    "a2") echo "- GenAI: vLLM optimization, cost reduction, inference scaling  
- Target Role: LLM Infrastructure Engineer (\$160-200k)
- Priority: Gap plan item 3 (vLLM cost/latency)" ;;
    "a3") echo "- Analytics: Portfolio automation, achievement documentation
- Target Role: Technical Lead with Analytics (\$160-180k)  
- Priority: Portfolio building and documentation" ;;
    "a4") echo "- Platform: A/B testing, revenue metrics, AWS/K8s deployment
- Target Role: Platform Engineer with AI focus (\$170-210k)
- Priority: Gap plan items 4-5 (A/B testing + AWS)" ;;
esac)

## Current Priorities
1. **Job Strategy Focus**: Work on highest-priority gap plan items
2. **AI Acceleration**: Use enhanced development tools daily
3. **Quality Gates**: Maintain high code quality standards
4. **Learning Integration**: Track patterns for continuous improvement

## Success Criteria
- Deliver job-strategy-aligned features
- Maintain >95% development success rate
- Document achievements with business metrics
- Demonstrate expertise for target role

## Current Context (Auto-Updated Daily)
### Today's Goals
- Focus on $agent_type specialization work
- Use AI acceleration tools for productivity
- Maintain quality standards

### Current Issues/Blockers
- Code quality improvements needed
- Learning system integration

### Next Session Priorities
1. Focus on gap plan priorities for $agent_type
2. Use enhanced development workflow
3. Track achievements for portfolio

## Technologies in Use
- Python 3.13, FastAPI, Celery
- Kubernetes, k3d, Helm
- AI tools: OpenAI API, Claude Code
- Learning system: custom analytics
- Agent: $agent_type ($agent_id) specialization

---
*Auto-updated by smart focus system for $agent_type agent*
EOF
    
    # Initialize learning system in agent
    if [[ -f "$agent_path/scripts/learning-system.sh" ]]; then
        (cd "$agent_path" && ./scripts/learning-system.sh init >/dev/null 2>&1) || true
    fi
    
    success "✅ $agent_type ($agent_id) deployment complete"
}

# Deploy to all agents
deploy_all() {
    log "🚀 Deploying AI development system to all 4 agent worktrees..."
    
    local deployed=0
    local failed=0
    
    for agent_info in "${AGENT_WORKTREES[@]}"; do
        IFS=':' read -r agent_path agent_id agent_type <<< "$agent_info"
        
        if deploy_to_agent "$agent_path" "$agent_id" "$agent_type"; then
            ((deployed++))
        else
            ((failed++))
        fi
        echo
    done
    
    success "✅ Deployment complete: $deployed successful, $failed failed"
    
    if [[ $deployed -gt 0 ]]; then
        log "🎯 All agents now have enhanced AI development system!"
        log ""
        log "Next steps:"
        log "1. Test: just agents (view status)"
        log "2. Use: just a1, just a2, just a3, just a4 (switch agents)"
        log "3. Work: just mlflow, just vllm, just docs, just ab (smart assignment)"
        log "4. Save: just save (AI-powered commits)"
        log "5. Track: All commands now tracked in learning system"
    fi
}

# Test deployment  
test_deployment() {
    log "🧪 Testing deployment across all agents..."
    
    for agent_info in "${AGENT_WORKTREES[@]}"; do
        IFS=':' read -r agent_path agent_id agent_type <<< "$agent_info"
        
        if [[ -d "$agent_path" ]]; then
            log "Testing $agent_type ($agent_id)..."
            
            # Test context loading
            local context_test=$(cd "$agent_path" && export AGENT_ID="$agent_id" && ./scripts/ai-dev-acceleration.sh context 2>&1 | grep "Enhanced smart context" || echo "FAILED")
            
            if [[ "$context_test" != "FAILED" ]]; then
                success "  ✅ Context loading works"
            else
                error "  ❌ Context loading failed"
            fi
            
            # Test agent focus exists
            if [[ -f "$agent_path/AGENT_FOCUS.md" ]]; then
                success "  ✅ Agent focus configured"
            else
                error "  ❌ Agent focus missing"
            fi
            
        else
            error "  ❌ Worktree missing: $agent_path"
        fi
    done
}

# Main execution
case "${1:-deploy}" in
    "deploy")
        deploy_all
        ;;
    "test")
        test_deployment
        ;;
    "agent")
        deploy_to_agent "${2}" "${3}" "${4}"
        ;;
    *)
        cat << EOF
🚀 AI System Deployment Tool

Usage: $0 [command]

Commands:
  deploy    Deploy AI system to all 4 agent worktrees
  test      Test deployment across all agents  
  agent     Deploy to specific agent worktree

Examples:
  $0 deploy                           # Deploy to all agents
  $0 test                            # Test all deployments
  $0 agent ../wt-a1-mlops a1 MLOps   # Deploy to specific agent

EOF
        ;;
esac