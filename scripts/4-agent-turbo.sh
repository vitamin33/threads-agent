#!/bin/bash

# 4-Agent Development Turbo System
# Quick-wins for maximum parallel development speed

set -e

ACTION=${1:-"help"}
AGENT_ID=${AGENT_ID:-"main"}

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() { echo -e "${BLUE}[TURBO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
career() { echo -e "${PURPLE}[CAREER]${NC} $1"; }

# QUICK-WIN 1: Ultra-fast agent switching
agent_switch() {
    local target_agent="$1"
    local current_dir=$(pwd)
    
    case "$target_agent" in
        "a1"|"mlops")
            cd ../wt-a1-mlops 2>/dev/null || { warn "A1 worktree not found"; return 1; }
            export AGENT_ID="a1"
            log "🤖 Switched to A1 (MLOps) - MLflow, SLO gates, monitoring" ;;
        "a2"|"genai")
            cd ../wt-a2-genai 2>/dev/null || { warn "A2 worktree not found"; return 1; }
            export AGENT_ID="a2"  
            log "🤖 Switched to A2 (GenAI) - vLLM, cost optimization, inference" ;;
        "a3"|"analytics")
            cd ../wt-a3-analytics 2>/dev/null || { warn "A3 worktree not found"; return 1; }
            export AGENT_ID="a3"
            log "🤖 Switched to A3 (Analytics) - portfolio, docs, achievements" ;;
        "a4"|"platform")
            cd ../wt-a4-platform 2>/dev/null || { warn "A4 worktree not found"; return 1; }
            export AGENT_ID="a4"
            log "🤖 Switched to A4 (Platform) - A/B testing, revenue, AWS" ;;
        *)
            error "Unknown agent: $target_agent. Use: a1, a2, a3, a4"
            return 1 ;;
    esac
    
    # Auto-load context for new agent
    just dev-context >/dev/null 2>&1 || true
    success "🎯 Agent $target_agent ready with loaded context"
}

# QUICK-WIN 2: Parallel agent status dashboard
agent_status() {
    log "📊 4-Agent Status Dashboard"
    echo
    
    local agents=("a1:MLOps:../wt-a1-mlops" "a2:GenAI:../wt-a2-genai" "a3:Analytics:../wt-a3-analytics" "a4:Platform:../wt-a4-platform")
    
    printf "%-8s %-12s %-15s %-20s %-15s\n" "AGENT" "TYPE" "STATUS" "BRANCH" "LAST COMMIT"
    printf "%-8s %-12s %-15s %-20s %-15s\n" "-----" "----" "------" "------" "-----------"
    
    for agent_info in "${agents[@]}"; do
        IFS=':' read -r agent_id agent_type agent_path <<< "$agent_info"
        
        if [[ -d "$agent_path" ]]; then
            local status="🟢 ACTIVE"
            local branch=$(cd "$agent_path" && git branch --show-current 2>/dev/null || echo "unknown")
            local last_commit=$(cd "$agent_path" && git log -1 --format="%h %s" 2>/dev/null | cut -c1-20 || echo "none")
            local uncommitted=$(cd "$agent_path" && git status --porcelain 2>/dev/null | wc -l || echo "0")
            
            if [[ $uncommitted -gt 0 ]]; then
                status="🟡 CHANGES"
            fi
        else
            status="🔴 MISSING"
            branch="N/A"
            last_commit="N/A"
        fi
        
        printf "%-8s %-12s %-15s %-20s %-15s\n" "$agent_id" "$agent_type" "$status" "$branch" "$last_commit"
    done
    
    echo
    log "💡 Use: ./scripts/4-agent-turbo.sh switch <agent> to switch agents"
}

# QUICK-WIN 3: Batch operations across all agents
batch_operation() {
    local operation="$1"
    log "🔄 Running '$operation' across all 4 agents..."
    
    local agents=("../wt-a1-mlops" "../wt-a2-genai" "../wt-a3-analytics" "../wt-a4-platform")
    local results=()
    
    for agent_path in "${agents[@]}"; do
        local agent_name=$(basename "$agent_path")
        
        if [[ -d "$agent_path" ]]; then
            log "  Processing $agent_name..."
            
            case "$operation" in
                "status")
                    local status=$(cd "$agent_path" && git status --porcelain | wc -l)
                    results+=("$agent_name: $status changes")
                    ;;
                "pull")
                    (cd "$agent_path" && git pull origin main >/dev/null 2>&1) && \
                    results+=("$agent_name: ✅ pulled") || \
                    results+=("$agent_name: ❌ pull failed")
                    ;;
                "quality")
                    local quality=$(cd "$agent_path" && ruff check . --quiet 2>/dev/null | wc -l || echo "unknown")
                    results+=("$agent_name: $quality lint issues")
                    ;;
                "sync")
                    (cd "$agent_path" && just auto-focus >/dev/null 2>&1) && \
                    results+=("$agent_name: ✅ focus synced") || \
                    results+=("$agent_name: ❌ sync failed")
                    ;;
                *)
                    warn "Unknown operation: $operation"
                    return 1
                    ;;
            esac
        else
            results+=("$agent_name: 🔴 missing")
        fi
    done
    
    # Display results
    echo
    for result in "${results[@]}"; do
        success "  $result"
    done
}

# QUICK-WIN 4: Smart agent assignment based on service groups
smart_assign() {
    local work_type="$1"
    
    case "$work_type" in
        # A1 - Infrastructure & Platform Services
        "infra"|"orchestrator"|"celery"|"common"|"monitoring"|"mlflow"|"platform")
            log "🎯 Infrastructure work → A1 (Infrastructure & Platform)"
            log "   Services: orchestrator, celery_worker, common, performance_monitor"
            agent_switch "a1"
            ;;
        # A2 - AI/ML & Content Services  
        "ai"|"ml"|"persona"|"rag"|"vllm"|"viral"|"content"|"inference")
            log "🎯 AI/ML work → A2 (AI/ML & Content)"
            log "   Services: persona_runtime, rag_pipeline, vllm_service, viral_engine"
            agent_switch "a2"
            ;;
        # A3 - Data & Analytics Pipeline
        "data"|"analytics"|"dashboard"|"metrics"|"achievements"|"docs")
            log "🎯 Data/Analytics work → A3 (Data & Analytics)"
            log "   Services: dashboard, viral_metrics, achievement_collector, tech_doc_generator"
            agent_switch "a3"
            ;;
        # A4 - Revenue & Business Systems
        "revenue"|"business"|"finops"|"ab"|"testing"|"cost")
            log "🎯 Business/Revenue work → A4 (Revenue & Business)"
            log "   Services: revenue, finops_engine, ab_testing_framework"
            agent_switch "a4"
            ;;
        *)
            log "🤔 Work type '$work_type' not recognized. Available service groups:"
            echo ""
            echo "🏗️  A1 - Infrastructure & Platform (8 services):"
            echo "     orchestrator, celery_worker, common, event_bus, mlflow, performance_monitor"
            echo ""
            echo "🤖 A2 - AI/ML & Content (9 services):"
            echo "     persona_runtime, rag_pipeline, vllm_service, viral_engine, conversation_engine"
            echo ""
            echo "📊 A3 - Data & Analytics (8 services):"
            echo "     dashboard, viral_metrics, achievement_collector, tech_doc_generator"
            echo ""
            echo "💰 A4 - Revenue & Business (8 services):"
            echo "     revenue, finops_engine, ab_testing_framework, threads_adaptor"
            ;;
    esac
}

# QUICK-WIN 5: Learning system activation for all agents
activate_learning() {
    log "🧠 Activating learning system for 4-agent development..."
    
    # Enable learning for current session
    if [[ -f "scripts/learning-system.sh" ]]; then
        ./scripts/learning-system.sh init
        
        # Hook learning into common commands
        cat > .learning-hooks.sh << 'EOF'
#!/bin/bash
# Auto-track commands in learning system

original_command="$1"
shift
args="$@"

start_time=$(date +%s.%N)
$original_command $args
exit_code=$?
end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc -l)

# Track in learning system
if [[ -f "scripts/learning-system.sh" ]]; then
    ./scripts/learning-system.sh track "$original_command $args" "$exit_code" "$duration" "agent:${AGENT_ID:-unknown}" >/dev/null 2>&1 &
fi

exit $exit_code
EOF
        chmod +x .learning-hooks.sh
        
        success "🧠 Learning system activated - will track all commands"
    else
        warn "Learning system script not found"
    fi
}

# QUICK-WIN 6: Agent coordination system
coordinate_agents() {
    log "🤝 Coordinating all 4 agents..."
    
    # Check for conflicts in shared files
    local shared_conflicts=0
    local shared_files=("services/common/" "helm/" "k8s/" "docs/")
    
    for shared_path in "${shared_files[@]}"; do
        if [[ -d "$shared_path" ]]; then
            # Check if multiple agents modified same files
            local modifiers=$(find ../wt-a*/ -name "$(basename "$shared_path")" -exec git -C {} log --since="24 hours ago" --name-only --pretty=format: \; 2>/dev/null | sort -u | grep "$shared_path" | wc -l || echo "0")
            if [[ $modifiers -gt 1 ]]; then
                ((shared_conflicts++))
                warn "Potential conflict in $shared_path (modified by $modifiers agents)"
            fi
        fi
    done
    
    if [[ $shared_conflicts -eq 0 ]]; then
        success "✅ No coordination conflicts detected"
    else
        warn "⚠️ $shared_conflicts potential conflicts need attention"
    fi
    
    # Generate coordination report
    cat > .agent-coordination.json << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "shared_conflicts": $shared_conflicts,
    "agent_status": $(agent_status 2>/dev/null | tail -4 | jq -R . | jq -s . || echo '[]'),
    "coordination_needed": $(test $shared_conflicts -gt 0 && echo "true" || echo "false")
}
EOF
    
    log "📋 Coordination analysis saved to .agent-coordination.json"
}

# Main command handler
case "$ACTION" in
    "switch")
        agent_switch "$2"
        ;;
    "status")
        agent_status
        ;;
    "batch")
        batch_operation "$2"
        ;;
    "assign")
        smart_assign "$2"
        ;;
    "learn")
        activate_learning
        ;;
    "coordinate")
        coordinate_agents
        ;;
    "help")
        cat << EOF
🚀 4-Agent Development Turbo System

ULTRA-FAST COMMANDS:
  switch <agent>     Switch to specific agent (a1/a2/a3/a4)
  status            Show all 4 agents status dashboard
  batch <op>        Run operation across all agents
  assign <work>     Smart work assignment to best agent
  learn             Activate learning system tracking
  coordinate        Check agent coordination status

AGENT SHORTCUTS:
  a1, infra         → Infrastructure & Platform (8 services: orchestrator, celery, common, monitoring)  
  a2, ai            → AI/ML & Content (9 services: persona, rag, vllm, viral_engine)
  a3, data          → Data & Analytics (8 services: dashboard, metrics, achievements, docs)
  a4, revenue       → Revenue & Business (8 services: revenue, finops, a/b testing)

BATCH OPERATIONS:
  batch status      → Check changes across all agents
  batch pull        → Pull latest for all agents
  batch quality     → Quality check all agents
  batch sync        → Sync focus for all agents

SMART ASSIGNMENT:
  assign mlflow     → Auto-switch to A1 (MLOps)
  assign vllm       → Auto-switch to A2 (GenAI)  
  assign docs       → Auto-switch to A3 (Analytics)
  assign ab         → Auto-switch to A4 (Platform)

EXAMPLES:
  $0 switch a1              # Switch to MLOps agent
  $0 assign vllm           # Smart assignment for vLLM work
  $0 batch quality         # Quality check all agents
  $0 coordinate           # Check coordination status

EOF
        ;;
    *)
        error "Unknown action: $ACTION"
        exit 1
        ;;
esac