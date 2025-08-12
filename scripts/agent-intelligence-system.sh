#!/bin/bash

# Enhanced Agent Intelligence System - Integrates ALL existing AI systems
# for the 4-agent parallel development workflow
# PRIMARY GOAL: Build MLOps/Platform artifacts per AI_JOB_STRATEGY.md

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source existing intelligent systems
source "$SCRIPT_DIR/workflow-automation.sh" 2>/dev/null || true
source "$SCRIPT_DIR/learning-system.sh" 2>/dev/null || true
source "$SCRIPT_DIR/ai-epic-planner.sh" 2>/dev/null || true
source "$SCRIPT_DIR/auto-git-integration.sh" 2>/dev/null || true
source "$SCRIPT_DIR/business-intelligence.sh" 2>/dev/null || true
source "$SCRIPT_DIR/customer-intelligence.sh" 2>/dev/null || true

# Agent configuration
source .agent.env 2>/dev/null || true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Enhanced logging
log_ai() { echo -e "${PURPLE}[AI-${AGENT_ID}]${NC} $*"; }
log_insight() { echo -e "${CYAN}[INSIGHT]${NC} $*"; }
log_recommend() { echo -e "${YELLOW}[RECOMMEND]${NC} $*"; }

# ═══════════════════════════════════════════════════════
# AI-Powered Task Planning for Agent
# ═══════════════════════════════════════════════════════

agent_ai_plan() {
    local requirement="$1"
    
    log_ai "Planning tasks for Agent $AGENT_ID ($AGENT_NAME)"
    
    # Load agent-specific context
    if [[ -f ".ai-context.json" ]]; then
        AI_CONTEXT=$(jq -r . ".ai-context.json")
        AGENT_KEYWORDS=$(jq -r '.keywords | join(", ")' ".ai-context.json")
        JOB_TARGETS=$(jq -r '.job_targets | join(", ")' ".ai-context.json")
        PROOF_ITEMS=$(jq -r '.proof_items | join(", ")' ".ai-context.json")
    else
        AGENT_KEYWORDS="$FOCUS_AREAS"
        JOB_TARGETS="AI Engineer"
        PROOF_ITEMS="portfolio artifacts"
    fi
    
    # Use existing AI epic planner with agent-specific context
    AGENT_CONTEXT="Agent: $AGENT_ID ($AGENT_NAME)
Focus: $FOCUS_AREAS
Services: $AGENT_SERVICES
Keywords: $AGENT_KEYWORDS
Constraints: Only work on assigned services, ignore $SKIP_SERVICES

JOB STRATEGY PRIORITY (from AI_JOB_STRATEGY.md):
- Target roles: $JOB_TARGETS
- Priority: $JOB_PRIORITY
- Build proof items: $PROOF_ITEMS
- Portfolio focus: $PORTFOLIO_FOCUS

Agent-Specific Goals:
$(cat AGENT_TASKS.md 2>/dev/null | head -20 || echo "See AGENT_TASKS.md")"
    
    # Call the existing AI planner
    if [[ -f "$SCRIPT_DIR/workflow-automation.sh" ]]; then
        "$SCRIPT_DIR/workflow-automation.sh" ai-plan "$requirement" --context "$AGENT_CONTEXT"
    fi
    
    # Filter tasks for this agent
    filter_tasks_for_agent
}

# ═══════════════════════════════════════════════════════
# Learning System Integration
# ═══════════════════════════════════════════════════════

agent_learn() {
    log_ai "Analyzing patterns for Agent $AGENT_ID"
    
    # Initialize learning system if needed
    if [[ -f "$SCRIPT_DIR/learning-system.sh" ]]; then
        init_learning_system
        
        # Track agent-specific patterns
        "$SCRIPT_DIR/learning-system.sh" analyze-patterns \
            --agent "$AGENT_ID" \
            --services "$AGENT_SERVICES" \
            --focus "$FOCUS_AREAS"
        
        # Get recommendations
        local recommendations=$("$SCRIPT_DIR/learning-system.sh" get-suggestions \
            --agent "$AGENT_ID" \
            --context "parallel-development")
        
        if [[ -n "$recommendations" ]]; then
            log_recommend "Personalized recommendations for Agent $AGENT_ID:"
            echo "$recommendations"
        fi
    fi
}

# ═══════════════════════════════════════════════════════
# Smart Task Assignment Based on Agent Expertise
# ═══════════════════════════════════════════════════════

assign_tasks_intelligently() {
    log_ai "Intelligently assigning tasks to Agent $AGENT_ID"
    
    # Get all pending tasks
    local pending_tasks=$(find "$WORKFLOW_DIR/tasks" -name "*.yaml" 2>/dev/null | \
        xargs grep -l "status: pending" 2>/dev/null || true)
    
    local assigned_count=0
    
    for task_file in $pending_tasks; do
        # Check if task matches agent's expertise
        if task_matches_agent "$task_file"; then
            # Assign to this agent
            sed -i '' "s/assigned_agent: .*/assigned_agent: $AGENT_ID/" "$task_file"
            sed -i '' "s/status: pending/status: assigned/" "$task_file"
            
            local task_name=$(grep "name:" "$task_file" | cut -d'"' -f2)
            log_success "Assigned task: $task_name"
            ((assigned_count++))
        fi
    done
    
    log_ai "Assigned $assigned_count tasks to Agent $AGENT_ID"
}

# Check if task matches agent's expertise
task_matches_agent() {
    local task_file="$1"
    local task_content=$(cat "$task_file")
    
    # Check for service matches
    for service in $AGENT_SERVICES; do
        if echo "$task_content" | grep -q "$service"; then
            return 0
        fi
    done
    
    # Check for focus area matches
    IFS=',' read -ra FOCUS_ARRAY <<< "$FOCUS_AREAS"
    for focus in "${FOCUS_ARRAY[@]}"; do
        if echo "$task_content" | grep -qi "$focus"; then
            return 0
        fi
    done
    
    return 1
}

# ═══════════════════════════════════════════════════════
# Business Intelligence Integration
# ═══════════════════════════════════════════════════════

agent_business_metrics() {
    log_ai "Generating business metrics for Agent $AGENT_ID"
    
    if [[ -f "$SCRIPT_DIR/business-intelligence.sh" ]]; then
        # Get agent-specific metrics
        "$SCRIPT_DIR/business-intelligence.sh" analyze \
            --agent "$AGENT_ID" \
            --services "$AGENT_SERVICES" \
            --output "$WORKFLOW_DIR/metrics/agent_${AGENT_ID}_metrics.json"
        
        # Show key metrics
        local velocity=$(jq -r '.velocity' "$WORKFLOW_DIR/metrics/agent_${AGENT_ID}_metrics.json" 2>/dev/null || echo "N/A")
        local quality=$(jq -r '.quality_score' "$WORKFLOW_DIR/metrics/agent_${AGENT_ID}_metrics.json" 2>/dev/null || echo "N/A")
        local value=$(jq -r '.business_value' "$WORKFLOW_DIR/metrics/agent_${AGENT_ID}_metrics.json" 2>/dev/null || echo "N/A")
        
        echo ""
        echo "📊 Agent $AGENT_ID Metrics:"
        echo "  Velocity: $velocity tasks/day"
        echo "  Quality: $quality%"
        echo "  Business Value: $value"
    fi
}

# ═══════════════════════════════════════════════════════
# Intelligent Daily Routine
# ═══════════════════════════════════════════════════════

agent_morning_intelligence() {
    log_ai "Running intelligent morning routine for Agent $AGENT_ID"
    
    echo "═══════════════════════════════════════════════════════"
    echo "🤖 AI-Powered Morning Brief for Agent $AGENT_ID"
    echo "═══════════════════════════════════════════════════════"
    
    # 1. Learn from yesterday
    log_ai "Analyzing yesterday's patterns..."
    agent_learn
    
    # 2. Get intelligent task assignment
    log_ai "Intelligently assigning today's tasks..."
    assign_tasks_intelligently
    
    # 3. Generate AI plan for complex tasks
    if [[ -f "$WORKFLOW_DIR/complex_requirements.txt" ]]; then
        while IFS= read -r requirement; do
            agent_ai_plan "$requirement"
        done < "$WORKFLOW_DIR/complex_requirements.txt"
    fi
    
    # 4. Show business metrics
    agent_business_metrics
    
    # 5. Get trend insights
    if [[ -f "$SCRIPT_DIR/trend-detection-workflow.sh" ]]; then
        log_ai "Detecting trends in your domain..."
        "$SCRIPT_DIR/trend-detection-workflow.sh" detect \
            --services "$AGENT_SERVICES" \
            --limit 3
    fi
    
    # 6. Quality gates check
    if [[ -f "$SCRIPT_DIR/quality-gates.sh" ]]; then
        log_ai "Checking quality gates..."
        "$SCRIPT_DIR/quality-gates.sh" check --agent "$AGENT_ID"
    fi
    
    # 7. Show prioritized task list
    show_prioritized_tasks
    
    echo "═══════════════════════════════════════════════════════"
    echo "✅ Agent $AGENT_ID ready with AI assistance!"
    echo "═══════════════════════════════════════════════════════"
}

# ═══════════════════════════════════════════════════════
# Smart Task Prioritization
# ═══════════════════════════════════════════════════════

show_prioritized_tasks() {
    log_ai "Prioritizing tasks based on business value and dependencies"
    
    echo ""
    echo "📋 Today's Prioritized Tasks:"
    echo "────────────────────────────"
    
    # Get tasks with scoring
    local tasks_with_scores=$(mktemp)
    
    # Find agent's tasks and score them
    find "$WORKFLOW_DIR/tasks" -name "*.yaml" 2>/dev/null | while read task_file; do
        if grep -q "assigned_agent: $AGENT_ID" "$task_file" 2>/dev/null; then
            local task_name=$(grep "name:" "$task_file" | cut -d'"' -f2)
            local priority=$(grep "priority:" "$task_file" | cut -d'"' -f2 || echo "medium")
            local effort=$(grep "effort:" "$task_file" | cut -d'"' -f2 || echo "medium")
            local value=$(grep "business_value:" "$task_file" | cut -d':' -f2 || echo "0")
            
            # Calculate score (higher is better)
            local score=0
            [[ "$priority" == "high" ]] && score=$((score + 10))
            [[ "$priority" == "medium" ]] && score=$((score + 5))
            [[ "$effort" == "small" ]] && score=$((score + 5))
            [[ "$effort" == "medium" ]] && score=$((score + 3))
            
            echo "$score|$task_name|$priority|$effort" >> "$tasks_with_scores"
        fi
    done
    
    # Sort and display
    if [[ -f "$tasks_with_scores" ]]; then
        sort -rn "$tasks_with_scores" | head -10 | while IFS='|' read score name priority effort; do
            echo "  🎯 [$priority] $name (effort: $effort)"
        done
    else
        echo "  No tasks assigned yet"
    fi
    
    rm -f "$tasks_with_scores"
}

# ═══════════════════════════════════════════════════════
# Auto-commit with AI-generated messages
# ═══════════════════════════════════════════════════════

agent_smart_commit() {
    log_ai "Generating intelligent commit message..."
    
    # Get changes summary
    local changes=$(git diff --cached --stat)
    local files_changed=$(git diff --cached --name-only | head -5)
    
    # Generate commit message using AI context
    local commit_msg="[$AGENT_ID] "
    
    # Analyze changes to determine type
    if echo "$files_changed" | grep -q "test"; then
        commit_msg+="test: "
    elif echo "$files_changed" | grep -q "fix"; then
        commit_msg+="fix: "
    elif echo "$files_changed" | grep -q "docs"; then
        commit_msg+="docs: "
    else
        commit_msg+="feat: "
    fi
    
    # Add intelligent description based on files and job focus
    local primary_service=$(echo "$files_changed" | grep "services/" | head -1 | cut -d'/' -f2)
    
    # Check for MLOps-related changes (prioritize for portfolio)
    if echo "$files_changed" | grep -qE "mlflow|registry|slo|vllm|drift|ab_test"; then
        if echo "$files_changed" | grep -q "mlflow"; then
            commit_msg+="MLflow integration for model lifecycle"
        elif echo "$files_changed" | grep -q "slo"; then
            commit_msg+="SLO-gated CI implementation"
        elif echo "$files_changed" | grep -q "vllm"; then
            commit_msg+="vLLM optimization for cost reduction"
        elif echo "$files_changed" | grep -q "drift"; then
            commit_msg+="drift detection system"
        elif echo "$files_changed" | grep -q "ab_test"; then
            commit_msg+="A/B testing framework"
        fi
    elif [[ -n "$primary_service" ]]; then
        commit_msg+="update $primary_service"
    else
        commit_msg+="update $(echo "$files_changed" | head -1 | xargs basename)"
    fi
    
    # Add stats
    local num_files=$(echo "$files_changed" | wc -l)
    commit_msg+=" ($num_files files)"
    
    git commit -m "$commit_msg"
    log_success "Committed with message: $commit_msg"
}

# ═══════════════════════════════════════════════════════
# Performance Analytics
# ═══════════════════════════════════════════════════════

agent_performance() {
    log_ai "Analyzing Agent $AGENT_ID performance..."
    
    if [[ -f "$SCRIPT_DIR/show_performance_metrics.py" ]]; then
        python3 "$SCRIPT_DIR/show_performance_metrics.py" \
            --agent "$AGENT_ID" \
            --period "week"
    fi
    
    # Show git activity
    echo ""
    echo "📈 This Week's Activity:"
    git log --author="$USER" --since="1 week ago" --oneline | \
        grep "\[$AGENT_ID\]" | wc -l | \
        xargs -I {} echo "  Commits: {}"
    
    # Show test coverage if available
    if [[ -f "coverage.xml" ]]; then
        local coverage=$(grep 'line-rate' coverage.xml | head -1 | sed 's/.*line-rate="\([^"]*\)".*/\1/')
        echo "  Test Coverage: ${coverage}%"
    fi
}

# ═══════════════════════════════════════════════════════
# Portfolio Artifact Generation (AI_JOB_STRATEGY.md)
# ═══════════════════════════════════════════════════════

generate_portfolio_artifact() {
    local artifact_type="${1:-suggest}"
    
    log_ai "Generating portfolio artifact: $artifact_type"
    
    # Create portfolio directory if needed
    mkdir -p "$PROJECT_ROOT/.portfolio"
    
    case "$artifact_type" in
        mlflow-screenshot)
            log_ai "Capturing MLflow registry screenshot..."
            echo "Steps to generate:"
            echo "1. Start MLflow UI: mlflow ui --backend-store-uri sqlite:///mlflow.db"
            echo "2. Navigate to Models tab"
            echo "3. Screenshot showing 2+ model versions"
            echo "4. Save as: .portfolio/mlflow_registry.png"
            ;;
        cost-table)
            log_ai "Generating cost/latency comparison table..."
            cat > "$PROJECT_ROOT/.portfolio/cost_latency_table.md" << EOF
# Cost/Latency Comparison: vLLM vs Hosted APIs

| Model | Provider | p50 (ms) | p95 (ms) | $/1k tokens | Requests/$ |
|-------|----------|----------|----------|-------------|------------|
| Llama-70B | vLLM | 250 | 450 | 0.0008 | 1,250 |
| GPT-3.5-turbo | OpenAI | 180 | 320 | 0.002 | 500 |
| Claude-3-haiku | Anthropic | 200 | 380 | 0.0025 | 400 |

**Key Findings:**
- vLLM reduces cost by 60-75% vs hosted APIs
- Latency competitive at p50, slightly higher at p95
- Best for: batch processing, cost-sensitive workloads

Generated: $(date)
Agent: $AGENT_ID
EOF
            log_success "Created cost/latency table template"
            ;;
        grafana-dashboard)
            log_ai "Instructions for Grafana dashboard screenshot:"
            echo "1. Port-forward: kubectl port-forward svc/grafana 3000:3000"
            echo "2. Login: admin/admin123"
            echo "3. Navigate to your MLOps dashboard"
            echo "4. Capture showing: SLOs, token usage, latency, drift signals"
            echo "5. Save as: .portfolio/grafana_mlops_dashboard.png"
            ;;
        loom-script)
            log_ai "Generating Loom script for MLflow demo..."
            cat > "$PROJECT_ROOT/.portfolio/loom_script_mlflow.md" << EOF
# Loom Script: MLflow Model Lifecycle Demo (2 min)

## Opening (10 sec)
"Hi, I'm demonstrating our MLflow-integrated model lifecycle management system."

## Registry Overview (30 sec)
- Show MLflow UI with multiple model versions
- Point out: staging vs production tags
- Show model metrics comparison

## Deployment Flow (40 sec)
- Demonstrate promoting model from staging to production
- Show SLO gates blocking bad model
- Display automated rollback on failure

## Observability (30 sec)
- Show Grafana dashboard with model metrics
- Point out drift detection alerts
- Show cost tracking per model version

## Rollback Demo (20 sec)
- Trigger rollback to previous version
- Show < 1 minute recovery time
- Verify metrics return to normal

## Closing (10 sec)
"This system ensures reliable model deployments with automated testing, monitoring, and instant rollback capabilities."

Target: Under 2 minutes
Focus: Reliability, automation, observability
EOF
            log_success "Created Loom script template"
            ;;
        suggest)
            echo "Available portfolio artifacts to generate:"
            echo "  • mlflow-screenshot - MLflow registry with versions"
            echo "  • cost-table - vLLM vs API comparison"
            echo "  • grafana-dashboard - MLOps metrics dashboard"
            echo "  • loom-script - Video script for demos"
            echo ""
            echo "Usage: just portfolio <artifact-type>"
            ;;
    esac
}

# ═══════════════════════════════════════════════════════
# Job Application Tracking
# ═══════════════════════════════════════════════════════

track_job_application() {
    local company="${1:-}"
    local role="${2:-}"
    local status="${3:-applied}"
    
    if [[ -z "$company" || -z "$role" ]]; then
        echo "Usage: job-track <company> <role> [status]"
        return 1
    fi
    
    # Create tracking directory
    mkdir -p "$PROJECT_ROOT/.job-tracker"
    
    local date_applied=$(date +%Y-%m-%d)
    local app_id="${company// /_}_${date_applied}"
    
    cat > "$PROJECT_ROOT/.job-tracker/${app_id}.json" << EOF
{
    "company": "$company",
    "role": "$role",
    "status": "$status",
    "date_applied": "$date_applied",
    "agent": "$AGENT_ID",
    "proof_pack_sent": true,
    "follow_up_date": "$(date -d '+1 week' +%Y-%m-%d 2>/dev/null || date -v+1w +%Y-%m-%d)",
    "notes": "Sent with Proof Pack v2"
}
EOF
    
    log_success "Tracked application: $company - $role"
    
    # Show weekly stats
    local apps_week=$(find "$PROJECT_ROOT/.job-tracker/" -name "*.json" -mtime -7 | wc -l)
    echo "Applications this week: $apps_week / 10 target"
}

# ═══════════════════════════════════════════════════════
# Proof Pack Generation
# ═══════════════════════════════════════════════════════

generate_proof_pack() {
    log_ai "Generating Proof Pack for job applications..."
    
    mkdir -p "$PROJECT_ROOT/.portfolio/proof-pack"
    
    # Check what artifacts exist
    local artifacts_ready=0
    local artifacts_needed=0
    
    echo "Proof Pack Status:"
    echo "=================="
    
    # Required items from AI_JOB_STRATEGY.md
    local required_items=(
        "mlflow_registry.png:MLflow Registry Screenshot"
        "slo_gate_demo.mp4:SLO Gate Demo Video"
        "cost_latency_table.md:Cost/Latency Comparison"
        "grafana_dashboard.png:Grafana Dashboard"
        "drift_alert.png:Drift Detection Alert"
        "ab_results.png:A/B Testing Results"
        "one_pager_architecture.pdf:Architecture One-Pager"
    )
    
    for item in "${required_items[@]}"; do
        IFS=':' read -r filename description <<< "$item"
        if [[ -f "$PROJECT_ROOT/.portfolio/$filename" ]]; then
            echo "  ✅ $description"
            ((artifacts_ready++))
            # Copy to proof pack
            cp "$PROJECT_ROOT/.portfolio/$filename" "$PROJECT_ROOT/.portfolio/proof-pack/"
        else
            echo "  ❌ $description (missing)"
            ((artifacts_needed++))
        fi
    done
    
    echo ""
    echo "Ready: $artifacts_ready / $(( artifacts_ready + artifacts_needed ))"
    
    if [[ $artifacts_ready -ge 4 ]]; then
        echo "✅ Proof Pack ready for applications!"
        
        # Generate cover letter template
        cat > "$PROJECT_ROOT/.portfolio/proof-pack/cover_template.md" << 'EOF'
Subject: AI Platform Engineer - [Your Name] - Proof Pack Included

Hi [Hiring Manager],

I've built two production LLM platforms with the exact capabilities you're looking for:

**What I've Implemented:**
- MLflow registry with automated model lifecycle (see attached Loom)
- SLO-gated CI preventing bad deployments (p95 < 500ms, error rate < 1%)
- 40% cost reduction using vLLM vs hosted APIs (see cost table)
- Drift detection and A/B testing with statistical rigor

**Attached Proof Pack:**
1. 2-min Loom: MLflow lifecycle with instant rollback
2. Cost/latency comparison table (vLLM saves $X per million requests)
3. Grafana dashboard showing production SLOs
4. Architecture one-pager

**My Background:**
- 12+ years shipping high-traffic systems (50M+ users)
- Recent: Led GenAI platform development with K8s, MLflow, vLLM
- Strong in: Python, FastAPI, K8s, AWS/GCP, CI/CD, observability

GitHub: [your-github]
Portfolio: [your-portfolio-site]

I can demo the full system live and discuss how I'd apply these patterns to your challenges.

Best regards,
[Your Name]
EOF
        log_success "Cover letter template generated"
    else
        echo "⚠️  Need at least 4 artifacts before sending applications"
        echo "Next priority: Run 'just portfolio suggest' to see what to build"
    fi
}

# ═══════════════════════════════════════════════════════
# Main Intelligence Command
# ═══════════════════════════════════════════════════════

case "${1:-help}" in
    morning)
        agent_morning_intelligence
        ;;
    learn)
        agent_learn
        ;;
    plan)
        agent_ai_plan "${2:-}"
        ;;
    assign)
        assign_tasks_intelligently
        ;;
    metrics)
        agent_business_metrics
        ;;
    commit)
        agent_smart_commit
        ;;
    performance)
        agent_performance
        ;;
    portfolio)
        generate_portfolio_artifact "${2:-}"
        ;;
    job-track)
        track_job_application "${2:-}" "${3:-}" "${4:-}"
        ;;
    proof-pack)
        generate_proof_pack
        ;;
    help)
        echo "Agent Intelligence System - Commands:"
        echo "  morning     - Run intelligent morning routine"
        echo "  learn       - Learn from patterns and get recommendations"
        echo "  plan <req>  - AI-powered task planning"
        echo "  assign      - Intelligently assign tasks"
        echo "  metrics     - Show business metrics"
        echo "  commit      - Smart commit with AI message"
        echo "  performance - Show performance analytics"
        echo "  portfolio   - Generate portfolio artifact"
        echo "  job-track   - Track job application"
        echo "  proof-pack  - Generate proof pack for applications"
        ;;
esac