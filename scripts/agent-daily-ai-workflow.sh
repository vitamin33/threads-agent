#!/bin/bash

# Enhanced AI-Powered Daily Workflow for 4-Agent Development
# Integrates ALL existing intelligent systems
# PRIMARY GOAL: Land high-paid remote AI role (US/EU) per AI_JOB_STRATEGY.md

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load agent configuration
source .agent.env 2>/dev/null || true

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════
# Morning Routine with Full AI Integration
# ═══════════════════════════════════════════════════════

morning_ai_routine() {
    clear
    echo "═══════════════════════════════════════════════════════"
    echo "🌅 AI-Powered Morning Routine for Agent $AGENT_ID"
    echo "📅 $(date '+%A, %B %d, %Y')"
    echo "🎯 PRIMARY GOAL: Land \$160-220k Remote AI Role"
    echo "═══════════════════════════════════════════════════════"
    
    # 1. Update and prepare branch
    echo -e "\n${BLUE}[1/10]${NC} Updating from main..."
    git fetch origin --quiet
    git checkout main --quiet
    git pull origin main --quiet
    
    local branch="feat/$AGENT_ID/$(date +%Y%m%d)-ai"
    git checkout -b "$branch" 2>/dev/null || git checkout "$branch"
    echo "✅ Branch: $branch"
    
    # 2. Run workflow automation system
    if [[ -f "$SCRIPT_DIR/workflow-automation.sh" ]]; then
        echo -e "\n${BLUE}[2/10]${NC} Activating workflow automation..."
        "$SCRIPT_DIR/workflow-automation.sh" orchestrate --agent "$AGENT_ID"
    fi
    
    # 3. AI Epic Planning with Job Strategy Focus + AGENT_FOCUS.md
    if [[ -f "$SCRIPT_DIR/ai-focus-manager.sh" ]]; then
        echo -e "\n${BLUE}[3/10]${NC} AI Task Planning (aligned with AI_JOB_STRATEGY.md)..."
        
        # Update AGENT_FOCUS.md with real progress
        "$SCRIPT_DIR/ai-focus-manager.sh" update
        
        # Generate new tasks based on job strategy
        "$SCRIPT_DIR/ai-focus-manager.sh" plan
        
        # Show current status
        "$SCRIPT_DIR/ai-focus-manager.sh" status
        
        # Weekly job strategy sync
        if [[ $(date +%u) -eq 1 ]]; then  # Monday
            echo -e "${YELLOW}📋 Weekly Job Strategy Sync:${NC}"
            "$SCRIPT_DIR/ai-focus-manager.sh" sync
            check_job_progress
        fi
    elif [[ -f "$SCRIPT_DIR/ai-epic-planner.sh" ]]; then
        # Fallback to old system
        echo -e "\n${BLUE}[3/10]${NC} Getting AI task recommendations..."
        JOB_CONTEXT="Focus on MLOps artifacts per AI_JOB_STRATEGY.md"
        
        if [[ -f "$PROJECT_ROOT/.requirements/pending.txt" ]]; then
            while IFS= read -r req; do
                "$SCRIPT_DIR/ai-epic-planner.sh" plan "$req" \
                    --agent "$AGENT_ID" \
                    --services "$AGENT_SERVICES" \
                    --context "$JOB_CONTEXT"
            done < "$PROJECT_ROOT/.requirements/pending.txt"
        fi
    fi
    
    # 4. Learning System Analysis
    if [[ -f "$SCRIPT_DIR/learning-system.sh" ]]; then
        echo -e "\n${BLUE}[4/10]${NC} Learning from patterns..."
        "$SCRIPT_DIR/learning-system.sh" analyze
        "$SCRIPT_DIR/learning-system.sh" suggest
    fi
    
    # 5. Business Intelligence
    if [[ -f "$SCRIPT_DIR/business-intelligence.sh" ]]; then
        echo -e "\n${BLUE}[5/10]${NC} Business intelligence analysis..."
        "$SCRIPT_DIR/business-intelligence.sh" daily-report \
            --agent "$AGENT_ID" \
            --focus "$FOCUS_AREAS"
    fi
    
    # 6. Customer Intelligence (if agent A4)
    if [[ "$AGENT_ID" == "a4" ]] && [[ -f "$SCRIPT_DIR/customer-intelligence.sh" ]]; then
        echo -e "\n${BLUE}[6/10]${NC} Customer intelligence insights..."
        "$SCRIPT_DIR/customer-intelligence.sh" analyze-feedback
    fi
    
    # 7. Quality Gates Check
    if [[ -f "$SCRIPT_DIR/quality-gates.sh" ]]; then
        echo -e "\n${BLUE}[7/10]${NC} Checking quality gates..."
        "$SCRIPT_DIR/quality-gates.sh" check \
            --services "$AGENT_SERVICES" \
            --agent "$AGENT_ID"
    fi
    
    # 8. Trend Detection (for GenAI agent)
    if [[ "$AGENT_ID" == "a2" ]] && [[ -f "$SCRIPT_DIR/trend-detection-workflow.sh" ]]; then
        echo -e "\n${BLUE}[8/10]${NC} Detecting AI/ML trends..."
        "$SCRIPT_DIR/trend-detection-workflow.sh" analyze \
            --domain "genai,llm,rag" \
            --output "$PROJECT_ROOT/.trends/agent_a2.json"
    fi
    
    # 9. Performance Metrics
    if [[ -f "$SCRIPT_DIR/show_performance_metrics.py" ]]; then
        echo -e "\n${BLUE}[9/10]${NC} Performance metrics..."
        python3 "$SCRIPT_DIR/show_performance_metrics.py" \
            --agent "$AGENT_ID" \
            --services "$AGENT_SERVICES"
    fi
    
    # 10. Linear Integration for Tasks
    if [[ -f "$SCRIPT_DIR/linear_epic_status.py" ]]; then
        echo -e "\n${BLUE}[10/10]${NC} Fetching Linear tasks..."
        python3 "$SCRIPT_DIR/linear_epic_status.py" \
            --labels "$FOCUS_AREAS" \
            --agent "$AGENT_ID"
    fi
    
    # Final Summary
    show_ai_dashboard
    
    # Job Search Reminder
    echo -e "\n${PURPLE}💼 Job Search Actions Today:${NC}"
    show_job_actions
}

# ═══════════════════════════════════════════════════════
# AI-Powered Dashboard
# ═══════════════════════════════════════════════════════

show_ai_dashboard() {
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "📊 AI Dashboard for Agent $AGENT_ID"
    echo "═══════════════════════════════════════════════════════"
    
    # Today's priorities (from AI analysis)
    echo -e "\n${PURPLE}🎯 Today's AI-Recommended Priorities:${NC}"
    if [[ -f "$PROJECT_ROOT/.workflows/recommendations/agent_${AGENT_ID}.json" ]]; then
        jq -r '.priorities[]' "$PROJECT_ROOT/.workflows/recommendations/agent_${AGENT_ID}.json" 2>/dev/null | \
            head -5 | nl -s '. '
    else
        echo "  1. Run 'just ai-plan' to generate recommendations"
    fi
    
    # Key metrics
    echo -e "\n${CYAN}📈 Key Metrics:${NC}"
    echo "  Velocity: $(git log --since='1 week ago' --oneline | grep "\[$AGENT_ID\]" | wc -l) commits/week"
    echo "  Coverage: $(find services/$AGENT_SERVICES -name "*.py" 2>/dev/null | wc -l) Python files"
    echo "  Tasks: $(ls $PROJECT_ROOT/.workflows/tasks/*${AGENT_ID}*.yaml 2>/dev/null | wc -l) assigned"
    
    # Intelligent suggestions
    echo -e "\n${YELLOW}💡 AI Suggestions:${NC}"
    suggest_next_actions
    
    # Quick commands
    echo -e "\n${GREEN}⚡ Quick Commands:${NC}"
    echo "  just ai-plan <requirement>  - Generate AI task plan"
    echo "  just ai-commit              - Commit with AI message"
    echo "  just ai-pr                  - Create PR with AI description"
    echo "  just ai-review              - Get AI code review"
    echo "  just learn                  - Learn from patterns"
    echo "  just mlops-artifact         - Generate MLOps proof artifact"
    echo "  just job-apply <company> <role> - Track job application"
    echo "  just proof-pack             - Generate proof pack items"
    
    echo "═══════════════════════════════════════════════════════"
}

# ═══════════════════════════════════════════════════════
# Intelligent Action Suggestions
# ═══════════════════════════════════════════════════════

suggest_next_actions() {
    # Check various conditions and suggest actions
    
    # Check for uncommitted changes
    if [[ -n $(git status --porcelain) ]]; then
        echo "  • You have uncommitted changes - run 'just ai-commit'"
    fi
    
    # Check for unpushed commits
    if [[ -n $(git log origin/$(git branch --show-current)..HEAD 2>/dev/null) ]]; then
        echo "  • You have unpushed commits - run 'git push'"
    fi
    
    # Check test status
    if [[ $(find . -name "*.py" -newer .pytest_cache 2>/dev/null | wc -l) -gt 0 ]]; then
        echo "  • Code changed since last test - run 'just test-agent'"
    fi
    
    # Check for PR opportunities
    local commits_ahead=$(git log origin/main..HEAD --oneline 2>/dev/null | wc -l)
    if [[ $commits_ahead -gt 3 ]]; then
        echo "  • $commits_ahead commits ahead - consider creating PR with 'just ai-pr'"
    fi
    
    # Service-specific suggestions
    case "$AGENT_ID" in
        a1)
            echo "  • Check performance metrics with 'just real-metrics'"
            ;;
        a2)
            echo "  • Analyze token usage with 'just ai-token-optimize'"
            ;;
        a3)
            echo "  • Generate documentation with 'just ai-docs'"
            ;;
        a4)
            echo "  • Check A/B test results with 'just ab-results'"
            ;;
    esac
}

# ═══════════════════════════════════════════════════════
# Continuous AI Assistance Mode
# ═══════════════════════════════════════════════════════

ai_assist_mode() {
    echo "🤖 AI Assist Mode Active for Agent $AGENT_ID"
    echo "Commands: plan, commit, review, learn, metrics, quit"
    echo ""
    
    while true; do
        read -p "ai-$AGENT_ID> " cmd args
        
        case "$cmd" in
            plan)
                "$SCRIPT_DIR/ai-epic-planner.sh" plan "$args" \
                    --agent "$AGENT_ID" --services "$AGENT_SERVICES"
                ;;
            commit)
                "$SCRIPT_DIR/agent-intelligence-system.sh" commit
                ;;
            review)
                echo "Getting AI code review..."
                git diff | head -500 | \
                    "$SCRIPT_DIR/ai-dev-enhancements.sh" review
                ;;
            learn)
                "$SCRIPT_DIR/learning-system.sh" analyze
                ;;
            metrics)
                "$SCRIPT_DIR/business-intelligence.sh" show-metrics
                ;;
            quit|exit)
                break
                ;;
            *)
                echo "Unknown command: $cmd"
                ;;
        esac
    done
}

# ═══════════════════════════════════════════════════════
# Job Strategy Functions (AI_JOB_STRATEGY.md integration)
# ═══════════════════════════════════════════════════════

check_job_progress() {
    echo "📊 Weekly Progress on Job Strategy Goals:"
    
    # Check MLflow integration
    if [[ -f "$PROJECT_ROOT/mlflow.db" ]]; then
        echo "  ✅ MLflow tracking active"
    else
        echo "  ⚠️  MLflow not configured - PRIORITY!"
    fi
    
    # Check for SLO gates
    if grep -q "slo_gate" "$PROJECT_ROOT/.github/workflows/"*.yml 2>/dev/null; then
        echo "  ✅ SLO-gated CI configured"
    else
        echo "  ⚠️  No SLO gates - needed for portfolio!"
    fi
    
    # Check vLLM integration
    if grep -r "vllm" "$PROJECT_ROOT/services/" 2>/dev/null | grep -q "import"; then
        echo "  ✅ vLLM integration present"
    else
        echo "  ⚠️  vLLM not integrated - cost optimization needed"
    fi
    
    # Check portfolio artifacts
    local artifacts=$(ls "$PROJECT_ROOT/.portfolio/" 2>/dev/null | wc -l)
    echo "  📦 Portfolio artifacts: $artifacts (target: 10+)"
    
    # Check job applications this week
    local apps_week=$(find "$PROJECT_ROOT/.job-tracker/" -name "*.json" -mtime -7 2>/dev/null | wc -l)
    echo "  📮 Applications this week: $apps_week (target: 10)"
}

show_job_actions() {
    # Daily actions based on AI_JOB_STRATEGY.md timeline
    local day_of_week=$(date +%u)
    
    case $day_of_week in
        1) # Monday
            echo "  • Send 10 tailored applications with Proof Pack"
            echo "  • Update portfolio README with latest metrics"
            ;;
        2) # Tuesday
            echo "  • Record Loom demo if new feature complete"
            echo "  • Post on LinkedIn about technical achievement"
            ;;
        3) # Wednesday
            echo "  • Warm outreach to 5 hiring managers"
            echo "  • Update cost/latency comparison table"
            ;;
        4) # Thursday
            echo "  • Push MLflow registry updates"
            echo "  • Generate new Grafana screenshots"
            ;;
        5) # Friday
            echo "  • Weekly portfolio review"
            echo "  • Schedule coffee chats for next week"
            ;;
        *)
            echo "  • Continue building proof artifacts"
            ;;
    esac
    
    # Always show next priority artifact
    echo -e "\n  ${YELLOW}Next Priority Artifact:${NC}"
    suggest_next_artifact
}

suggest_next_artifact() {
    # Based on AI_JOB_STRATEGY.md gap plan
    if [[ ! -f "$PROJECT_ROOT/.portfolio/mlflow_lifecycle.mp4" ]]; then
        echo "    🎥 MLflow lifecycle Loom (train→eval→promote→rollback)"
    elif [[ ! -f "$PROJECT_ROOT/.portfolio/slo_gate_demo.mp4" ]]; then
        echo "    🎥 SLO gate catching regression Loom"
    elif [[ ! -f "$PROJECT_ROOT/.portfolio/cost_latency_table.md" ]]; then
        echo "    📊 vLLM vs API cost/latency comparison table"
    elif [[ ! -f "$PROJECT_ROOT/.portfolio/drift_detection.png" ]]; then
        echo "    📸 Drift detection screenshot with alert"
    elif [[ ! -f "$PROJECT_ROOT/.portfolio/ab_testing_dashboard.png" ]]; then
        echo "    📸 A/B testing dashboard with results"
    else
        echo "    ✅ Core artifacts complete - focus on applications!"
    fi
}

# ═══════════════════════════════════════════════════════
# Main execution
# ═══════════════════════════════════════════════════════

case "${1:-morning}" in
    morning)
        morning_ai_routine
        ;;
    assist)
        ai_assist_mode
        ;;
    dashboard)
        show_ai_dashboard
        ;;
    *)
        echo "Usage: $0 [morning|assist|dashboard]"
        echo "  morning   - Full AI-powered morning routine"
        echo "  assist    - Interactive AI assistance mode"
        echo "  dashboard - Show AI dashboard"
        ;;
esac