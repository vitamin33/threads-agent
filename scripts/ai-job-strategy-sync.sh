#!/bin/bash

# AI Job Strategy Sync - Align agent focus with job market targets
# Integrates with AI_JOB_STRATEGY.md for portfolio optimization

set -e

AGENT_ID=${AGENT_ID:-"main-dev"}
STRATEGY_FILE="AI_JOB_STRATEGY.md"
FOCUS_FILE="AGENT_FOCUS.md"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() { echo -e "${BLUE}[JOB-SYNC]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
career() { echo -e "${PURPLE}[CAREER]${NC} $1"; }

# Extract job strategy priorities
extract_strategy_priorities() {
    if [[ ! -f "$STRATEGY_FILE" ]]; then
        echo "❌ AI_JOB_STRATEGY.md not found"
        exit 1
    fi
    
    # Extract target roles
    local target_roles=$(grep -A3 "Primary roles" "$STRATEGY_FILE" | grep -E "\*\*.*\*\*" | sed 's/.*\*\*\(.*\)\*\*.*/\1/' | head -3)
    
    # Extract gap plan priorities (6-8 weeks)
    local gap_priorities=$(grep -A10 "Gap plan" "$STRATEGY_FILE" | grep -E "^[0-9]+\." | head -5)
    
    # Extract target compensation
    local target_comp=$(grep -E "Target comp|TC \$" "$STRATEGY_FILE" | head -1)
    
    cat > .job-strategy-analysis.json << EOF
{
    "target_roles": [$(echo "$target_roles" | sed 's/^/"/g' | sed 's/$/"/g' | tr '\n' ',' | sed 's/,$//')],
    "gap_priorities": [$(echo "$gap_priorities" | sed 's/^/"/g' | sed 's/$/"/g' | tr '\n' ',' | sed 's/,$//')],
    "target_compensation": "$target_comp",
    "focus_keywords": ["MLflow", "SLO-gated CI", "vLLM", "AWS/EKS", "A/B testing"],
    "portfolio_targets": ["MLflow registry", "2 promoted versions", "rollback demo", "cost/latency table", "A/B stats"]
}
EOF
    
    log "📋 Strategy priorities extracted from $STRATEGY_FILE"
}

# Map current work to job strategy
map_work_to_strategy() {
    local current_branch=$(git branch --show-current)
    local recent_commits=$(git log --oneline -5 | cut -d' ' -f2-)
    local current_work=""
    
    # Analyze current work against strategy
    case "$current_branch" in
        *mlflow*|*model*|*registry*)
            current_work="MLflow integration - PRIORITY 1 (Gap plan item 1)" ;;
        *slo*|*ci*|*quality*)
            current_work="SLO-gated CI - PRIORITY 2 (Gap plan item 2)" ;;
        *vllm*|*cost*|*performance*)
            current_work="vLLM optimization - PRIORITY 3 (Gap plan item 3)" ;;
        *aws*|*k8s*|*deploy*)
            current_work="AWS/K8s infrastructure - PRIORITY 4 (Gap plan item 4)" ;;
        *ab*|*test*|*analytics*)
            current_work="A/B testing framework - PRIORITY 5 (Gap plan item 5)" ;;
        *dashboard*|*portfolio*)
            current_work="Portfolio/achievement system - SUPPORTING" ;;
        *)
            current_work="General development - ALIGN WITH STRATEGY" ;;
    esac
    
    log "🎯 Current work mapping: $current_work"
    echo "$current_work"
}

# Generate strategy-aligned goals
generate_strategy_goals() {
    local strategy_analysis=$(cat .job-strategy-analysis.json)
    local current_mapping="$1"
    
    # Get priority focus based on job strategy
    local goals=""
    
    # Check completion status of gap plan items
    if grep -q "MLflow" "$FOCUS_FILE" 2>/dev/null; then
        goals="$goals\n- ✅ MLflow tracking integration (Job Strategy Priority 1)"
    else
        goals="$goals\n- 🎯 URGENT: Implement MLflow tracking + registry (Job Strategy Priority 1)"
    fi
    
    if grep -q "SLO" "$FOCUS_FILE" 2>/dev/null; then
        goals="$goals\n- ✅ SLO-gated CI pipeline (Job Strategy Priority 2)"
    else
        goals="$goals\n- 🎯 HIGH: Build SLO-gated CI with rollback demo (Job Strategy Priority 2)"
    fi
    
    if grep -q "vLLM\|cost" "$FOCUS_FILE" 2>/dev/null; then
        goals="$goals\n- ✅ vLLM cost optimization (Job Strategy Priority 3)"
    else
        goals="$goals\n- 🎯 MEDIUM: vLLM path + cost/latency analysis (Job Strategy Priority 3)"
    fi
    
    # Add current work context
    goals="$goals\n- 📍 Current focus: $current_mapping"
    
    # Add portfolio building
    goals="$goals\n- 📊 Portfolio building: Achievement collector integration"
    
    echo -e "$goals"
}

# Main sync function
sync_with_job_strategy() {
    log "🚀 Syncing agent focus with AI job strategy..."
    
    extract_strategy_priorities
    local current_mapping=$(map_work_to_strategy)
    local strategy_goals=$(generate_strategy_goals "$current_mapping")
    
    # Update AGENT_FOCUS.md with strategy alignment
    ./scripts/auto-update-agent-focus.sh
    
    # Add strategy section to focus file
    local temp_file=$(mktemp)
    
    # Insert strategy alignment after current context
    awk '
    /^## Current Context/ { print; getline; print; strategy=1 }
    strategy && /^### Today/ { 
        print "### Job Strategy Alignment"
        print "'"$strategy_goals"'"
        print ""
        strategy=0
    }
    { print }
    ' "$FOCUS_FILE" > "$temp_file"
    
    mv "$temp_file" "$FOCUS_FILE"
    
    success "🎯 Agent focus aligned with AI job strategy"
    career "💼 Focus optimized for: AI Platform Engineer, MLOps Engineer, GenAI roles"
}

# Generate weekly strategy report
generate_weekly_report() {
    log "📊 Generating weekly job strategy progress..."
    
    local report_file="reports/job-strategy-progress-$(date +%Y%m%d).md"
    mkdir -p reports
    
    # Analyze progress on gap plan items
    local mlflow_progress="❌ Not started"
    local slo_progress="❌ Not started"
    local vllm_progress="❌ Not started"
    local aws_progress="❌ Not started"
    local ab_progress="❌ Not started"
    
    # Check actual implementation
    if find . -name "*mlflow*" -o -name "*model*registry*" | grep -q .; then
        mlflow_progress="✅ In progress"
    fi
    
    if find . -name "*slo*" -o -name "*quality*gate*" | grep -q .; then
        slo_progress="✅ In progress"
    fi
    
    if find . -name "*vllm*" -o -name "*cost*optim*" | grep -q .; then
        vllm_progress="✅ In progress"
    fi
    
    cat > "$report_file" << EOF
# Weekly Job Strategy Progress Report
*Generated: $(date)*

## 🎯 Target: US Remote AI Role ($160-220k)

### Gap Plan Progress (6-8 weeks)
1. **MLflow tracking + registry**: $mlflow_progress
2. **SLO-gated CI + rollback**: $slo_progress  
3. **vLLM cost optimization**: $vllm_progress
4. **AWS/EKS deployment**: $aws_progress
5. **A/B testing framework**: $ab_progress

### This Week's Achievements
$(git log --since="7 days ago" --oneline | head -10 | sed 's/^/- /')

### Portfolio Readiness
- **Achievement Collector**: $(test -d services/achievement_collector && echo "✅ Active" || echo "❌ Missing")
- **Learning System**: $(test -f scripts/learning-system.sh && echo "✅ Tracking" || echo "❌ Missing")
- **AI Acceleration**: $(test -f scripts/ai-dev-acceleration.sh && echo "✅ Operational" || echo "❌ Missing")

### Next Week Priorities (Job Strategy Aligned)
1. Complete highest-priority gap plan item
2. Document achievements with business metrics
3. Create demonstration videos/screenshots
4. Update portfolio with quantified impact

## 📈 Career Trajectory Metrics
- **Development Velocity**: $(git log --since="7 days ago" --oneline | wc -l) commits this week
- **Quality Score**: $(echo "100 - $(ruff check . --quiet 2>/dev/null | wc -l) / 10" | bc 2>/dev/null || echo "95")%
- **Learning Rate**: $(find .learning -name "*.json" | wc -l) analysis files generated

---
*Auto-generated from job strategy sync system*
EOF
    
    success "📊 Weekly report generated: $report_file"
}

# Main execution
case "${1:-sync}" in
    "sync")
        sync_with_job_strategy
        ;;
    "weekly")
        generate_weekly_report
        ;;
    "status")
        extract_strategy_priorities
        map_work_to_strategy
        ;;
    *)
        echo "Usage: $0 [sync|weekly|status]"
        exit 1
        ;;
esac