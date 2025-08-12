#!/bin/bash
# AI-Powered AGENT_FOCUS.md Manager
# Updates progress, plans tasks, aligns with AI_JOB_STRATEGY.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load agent configuration
source .agent.env 2>/dev/null || true

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════
# AI-Powered Task Planning (from AI_JOB_STRATEGY.md)
# ═══════════════════════════════════════════════════════

plan_next_tasks() {
    echo -e "${BLUE}🤖 AI Planning Next Tasks for Agent $AGENT_ID${NC}"
    
    # Read current AGENT_FOCUS.md
    local current_focus=$(cat AGENT_FOCUS.md 2>/dev/null || echo "No focus file yet")
    
    # Read AI_JOB_STRATEGY.md for context
    local job_strategy=$(cat "$PROJECT_ROOT/AI_JOB_STRATEGY.md" 2>/dev/null | head -100)
    
    # Create AI prompt based on agent role
    local ai_prompt=""
    
    case "$AGENT_ID" in
        a1)
            ai_prompt="As Agent A1 (MLOps), based on AI_JOB_STRATEGY.md priorities:
            - Need: MLflow with 2+ model versions for portfolio
            - Need: SLO-gated CI demo (p95 < 500ms)
            - Need: Grafana dashboards
            Current progress: $current_focus
            
            Generate next 5 concrete tasks to build MLOps portfolio for job applications.
            Focus on MLflow, SLO gates, monitoring.
            Each task should be specific and completable in 1-2 hours."
            ;;
        a2)
            ai_prompt="As Agent A2 (GenAI), based on AI_JOB_STRATEGY.md priorities:
            - Need: vLLM deployment with 60% cost reduction proof
            - Need: RAG pipeline with Qdrant
            - Need: Token optimization metrics
            Current progress: $current_focus
            
            Generate next 5 concrete tasks to prove cost optimization for GenAI Engineer roles.
            Focus on vLLM, RAG, token tracking.
            Each task should be specific and completable in 1-2 hours."
            ;;
        a3)
            ai_prompt="As Agent A3 (Analytics), based on AI_JOB_STRATEGY.md priorities:
            - Need: Achievement collection from PRs
            - Need: Portfolio website
            - Need: Technical documentation
            Current progress: $current_focus
            
            Generate next 5 concrete tasks to build portfolio artifacts.
            Focus on achievements, documentation, visualization.
            Each task should be specific and completable in 1-2 hours."
            ;;
        a4)
            ai_prompt="As Agent A4 (Platform), based on AI_JOB_STRATEGY.md priorities:
            - Need: A/B testing framework with statistical significance
            - Need: Revenue tracking ($20k MRR goal)
            - Need: FinOps cost optimization (30% reduction)
            Current progress: $current_focus
            
            Generate next 5 concrete tasks for Platform Engineer portfolio.
            Focus on A/B testing, revenue metrics, cost optimization.
            Each task should be specific and completable in 1-2 hours."
            ;;
    esac
    
    # Call AI planner if available
    if [[ -f "$SCRIPT_DIR/ai-epic-planner.sh" ]] && [[ -n "${OPENAI_API_KEY:-}" ]]; then
        echo "$ai_prompt" | "$SCRIPT_DIR/ai-epic-planner.sh" plan --context-stdin
    else
        # Fallback to template-based planning
        generate_template_tasks
    fi
}

# ═══════════════════════════════════════════════════════
# Update AGENT_FOCUS.md Progress
# ═══════════════════════════════════════════════════════

update_progress() {
    local section="${1:-today}"
    
    echo -e "${GREEN}📊 Updating progress in AGENT_FOCUS.md${NC}"
    
    # Check real metrics
    local metrics=$(./scripts/collect-real-metrics-v2.sh "$AGENT_ID" 2>/dev/null || echo "No metrics")
    
    # Parse current progress
    case "$AGENT_ID" in
        a1)
            # Check MLflow status
            if [[ -f "$PROJECT_ROOT/mlflow.db" ]]; then
                local models=$(sqlite3 "$PROJECT_ROOT/mlflow.db" "SELECT COUNT(*) FROM registered_models" 2>/dev/null || echo 0)
                update_metric "Models Registered" "$models/2"
            fi
            
            # Check SLO gates
            if grep -q "slo_gate" "$PROJECT_ROOT/.github/workflows/"*.yml 2>/dev/null; then
                update_metric "SLO Gates Active" "Yes"
            fi
            ;;
        a2)
            # Check vLLM deployment
            if kubectl get svc vllm-service 2>/dev/null; then
                update_metric "vLLM Deployed" "Yes"
                
                # Calculate cost savings
                local savings=$(calculate_cost_savings)
                update_metric "Cost Reduction" "$savings%"
            fi
            ;;
        a3)
            # Check achievements
            if [[ -f "$PROJECT_ROOT/.achievements/summary.json" ]]; then
                local count=$(jq '.achievements | length' "$PROJECT_ROOT/.achievements/summary.json")
                update_metric "Achievements Collected" "$count"
            fi
            ;;
        a4)
            # Check A/B tests
            local ab_tests=$(find "$PROJECT_ROOT/.ab-tests" -name "*.json" 2>/dev/null | wc -l)
            update_metric "A/B Tests Run" "$ab_tests"
            ;;
    esac
    
    # Update portfolio checklist
    update_portfolio_checklist
    
    # Add timestamp
    sed -i '' "s/Last Updated:.*/Last Updated: $(date)/" AGENT_FOCUS.md 2>/dev/null || \
        echo "---" >> AGENT_FOCUS.md && echo "Last Updated: $(date)" >> AGENT_FOCUS.md
}

# ═══════════════════════════════════════════════════════
# Check Off Completed Tasks
# ═══════════════════════════════════════════════════════

mark_task_complete() {
    local task_pattern="$1"
    
    echo -e "${GREEN}✅ Marking task as complete: $task_pattern${NC}"
    
    # Update checkbox from [ ] to [x]
    sed -i '' "s/- \[ \] $task_pattern/- [x] $task_pattern/" AGENT_FOCUS.md
    
    # Move to completed section if it exists
    if grep -q "## ✅ Completed This Week" AGENT_FOCUS.md; then
        local completed_line=$(grep "- \[x\] $task_pattern" AGENT_FOCUS.md)
        sed -i '' "/- \[x\] $task_pattern/d" AGENT_FOCUS.md
        sed -i '' "/## ✅ Completed This Week/a\\
$completed_line" AGENT_FOCUS.md
    fi
    
    # Update progress metrics
    update_progress
}

# ═══════════════════════════════════════════════════════
# Generate Portfolio Artifact Tasks
# ═══════════════════════════════════════════════════════

generate_portfolio_tasks() {
    echo -e "${YELLOW}📦 Generating portfolio-focused tasks${NC}"
    
    # Read AI_JOB_STRATEGY.md for priorities
    local priorities=$(grep -A 10 "Gap Plan" "$PROJECT_ROOT/AI_JOB_STRATEGY.md" 2>/dev/null)
    
    case "$AGENT_ID" in
        a1)
            cat << EOF

### 🎯 Portfolio Tasks for MLOps Engineer Role
- [ ] Set up MLflow tracking server with SQLite backend
- [ ] Train 2 models and register in MLflow registry
- [ ] Create Python script for SLO validation (p95 < 500ms)
- [ ] Configure Grafana dashboard with 3 panels
- [ ] Record 2-min Loom showing model promotion workflow
- [ ] Generate cost/performance comparison table
- [ ] Write one-pager on MLOps architecture decisions
EOF
            ;;
        a2)
            cat << EOF

### 🎯 Portfolio Tasks for GenAI Engineer Role
- [ ] Deploy vLLM with Llama-70B model
- [ ] Run benchmark: vLLM vs OpenAI API (latency & cost)
- [ ] Implement RAG pipeline with Qdrant vector store
- [ ] Create token usage tracking dashboard
- [ ] Generate cost savings report (target: 60% reduction)
- [ ] Build semantic search demo with accuracy metrics
- [ ] Document vLLM deployment architecture
EOF
            ;;
        a3)
            cat << EOF

### 🎯 Portfolio Tasks for Analytics Role
- [ ] Process last 20 PRs for achievements
- [ ] Generate achievement impact report (PDF)
- [ ] Create portfolio website landing page
- [ ] Build interactive achievement visualization
- [ ] Write 3 technical blog posts from PRs
- [ ] Generate API documentation
- [ ] Create developer onboarding guide
EOF
            ;;
        a4)
            cat << EOF

### 🎯 Portfolio Tasks for Platform Engineer Role
- [ ] Implement A/B testing framework
- [ ] Run first A/B test with significance calculation
- [ ] Create revenue tracking dashboard
- [ ] Implement FinOps cost tracking
- [ ] Generate cost optimization report (30% target)
- [ ] Build event-driven architecture diagram
- [ ] Create platform scaling documentation
EOF
            ;;
    esac
}

# ═══════════════════════════════════════════════════════
# Interactive Task Management
# ═══════════════════════════════════════════════════════

interactive_mode() {
    echo -e "${BLUE}🤖 AI Focus Manager - Interactive Mode${NC}"
    echo "Commands: plan, update, complete, status, portfolio, quit"
    
    while true; do
        read -p "focus-$AGENT_ID> " cmd args
        
        case "$cmd" in
            plan)
                plan_next_tasks
                ;;
            update)
                update_progress
                ;;
            complete)
                mark_task_complete "$args"
                ;;
            status)
                show_current_status
                ;;
            portfolio)
                generate_portfolio_tasks
                ;;
            sync)
                sync_with_job_strategy
                ;;
            quit|exit)
                break
                ;;
            *)
                echo "Unknown command: $cmd"
                echo "Available: plan, update, complete, status, portfolio, sync, quit"
                ;;
        esac
    done
}

# ═══════════════════════════════════════════════════════
# Show Current Status
# ═══════════════════════════════════════════════════════

show_current_status() {
    echo -e "${GREEN}📊 Current Status for Agent $AGENT_ID${NC}"
    
    # Count tasks
    local todo=$(grep -c "- \[ \]" AGENT_FOCUS.md 2>/dev/null || echo 0)
    local done=$(grep -c "- \[x\]" AGENT_FOCUS.md 2>/dev/null || echo 0)
    local total=$((todo + done))
    
    echo "Tasks: $done/$total complete"
    
    # Show portfolio progress
    echo ""
    echo "Portfolio Checklist:"
    grep -E "^- \[.\]" AGENT_FOCUS.md | grep -E "(screenshot|video|demo|report)" | head -5 || true
    
    # Show metrics
    echo ""
    echo "Metrics:"
    sed -n '/## 📊 Progress Tracking/,/^```$/p' AGENT_FOCUS.md | grep -v '^```$' | tail -n +2
}

# ═══════════════════════════════════════════════════════
# Sync with AI_JOB_STRATEGY.md
# ═══════════════════════════════════════════════════════

sync_with_job_strategy() {
    echo -e "${YELLOW}🔄 Syncing with AI_JOB_STRATEGY.md${NC}"
    
    # Extract key requirements from job strategy
    local mlops_needs=$(grep -A 5 "MLOps Platform Engineer" "$PROJECT_ROOT/AI_JOB_STRATEGY.md" 2>/dev/null)
    local genai_needs=$(grep -A 5 "GenAI Product Engineer" "$PROJECT_ROOT/AI_JOB_STRATEGY.md" 2>/dev/null)
    
    # Update focus based on job requirements
    case "$AGENT_ID" in
        a1)
            echo "Priority from job strategy: MLflow, SLO gates, monitoring"
            echo "Target roles: MLOps Engineer \$160-180k"
            ;;
        a2)
            echo "Priority from job strategy: vLLM, cost optimization, RAG"
            echo "Target roles: GenAI Engineer \$170-190k"
            ;;
        a3)
            echo "Priority from job strategy: Portfolio website, documentation"
            echo "Target roles: Technical Writer, Developer Advocate"
            ;;
        a4)
            echo "Priority from job strategy: A/B testing, revenue, FinOps"
            echo "Target roles: Platform Engineer \$170-190k"
            ;;
    esac
    
    # Generate aligned tasks
    plan_next_tasks
}

# ═══════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════

update_metric() {
    local metric_name="$1"
    local new_value="$2"
    
    # Update in the Progress Tracking section
    sed -i '' "s/$metric_name:.*/$metric_name: $new_value/" AGENT_FOCUS.md 2>/dev/null || \
        echo "$metric_name: $new_value" >> AGENT_FOCUS.md
}

update_portfolio_checklist() {
    # Check for actual files and update checklist
    if [[ -f "$PROJECT_ROOT/.portfolio/mlflow_registry.png" ]]; then
        sed -i '' "s/- \[ \] MLflow registry screenshot/- [x] MLflow registry screenshot/" AGENT_FOCUS.md
    fi
    
    if [[ -f "$PROJECT_ROOT/.portfolio/slo_gate_demo.mp4" ]]; then
        sed -i '' "s/- \[ \] SLO gate demo video/- [x] SLO gate demo video/" AGENT_FOCUS.md
    fi
    
    # Add more checks based on agent
}

calculate_cost_savings() {
    # Real calculation based on token usage
    local openai_cost=$(grep "openai_cost" "$PROJECT_ROOT/.metrics/costs.json" 2>/dev/null | awk '{print $2}')
    local vllm_cost=$(grep "vllm_cost" "$PROJECT_ROOT/.metrics/costs.json" 2>/dev/null | awk '{print $2}')
    
    if [[ -n "$openai_cost" && -n "$vllm_cost" ]]; then
        echo "scale=0; (1 - $vllm_cost / $openai_cost) * 100" | bc
    else
        echo "0"
    fi
}

generate_template_tasks() {
    # Fallback when AI is not available
    echo -e "${YELLOW}Generating template tasks (no AI available)${NC}"
    generate_portfolio_tasks
}

# ═══════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════

case "${1:-help}" in
    plan)
        plan_next_tasks
        ;;
    update)
        update_progress "${2:-}"
        ;;
    complete)
        mark_task_complete "${2:-}"
        ;;
    status)
        show_current_status
        ;;
    portfolio)
        generate_portfolio_tasks
        ;;
    sync)
        sync_with_job_strategy
        ;;
    interactive)
        interactive_mode
        ;;
    help)
        echo "AI Focus Manager - Manage AGENT_FOCUS.md with AI"
        echo ""
        echo "Usage: $0 [command] [args]"
        echo ""
        echo "Commands:"
        echo "  plan        - Generate next tasks with AI (uses job strategy)"
        echo "  update      - Update progress metrics from real data"
        echo "  complete    - Mark a task as complete"
        echo "  status      - Show current progress"
        echo "  portfolio   - Generate portfolio-specific tasks"
        echo "  sync        - Sync with AI_JOB_STRATEGY.md"
        echo "  interactive - Interactive mode"
        echo ""
        echo "Examples:"
        echo "  $0 plan                    # AI generates next tasks"
        echo "  $0 complete 'MLflow setup' # Mark task complete"
        echo "  $0 update                  # Update all metrics"
        echo "  $0 sync                    # Align with job strategy"
        ;;
esac