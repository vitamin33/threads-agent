#!/usr/bin/env bash
# ================================================================
#  UNIFIED COMMAND CENTER - Level 9 Solopreneur Decision System
# ================================================================

set -euo pipefail

# Color codes
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_PURPLE='\033[0;35m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_BOLD='\033[1m'
readonly COLOR_RESET='\033[0m'

log_info() { echo -e "${COLOR_BLUE}[CENTER]${COLOR_RESET} $*"; }
log_success() { echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $*"; }
log_priority() { echo -e "${COLOR_BOLD}${COLOR_GREEN}[PRIORITY]${COLOR_RESET} $*"; }
log_metric() { echo -e "${COLOR_PURPLE}[METRIC]${COLOR_RESET} $*"; }

# Data directories
readonly DATA_DIR=".command-center"
readonly ACTIONS_DIR="$DATA_DIR/actions"
readonly FEEDBACK_DIR="$DATA_DIR/feedback"

mkdir -p "$ACTIONS_DIR" "$FEEDBACK_DIR"

generate_action_plan() {
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local date_str=$(date +%Y%m%d_%H%M%S)
    
    log_info "Generating unified action plan..."
    
    # Get latest customer priority
    local customer_priority_score=90
    local customer_priority_action="enhance_retention"
    
    if [[ -f ".customer-priority/priorities/latest.json" ]]; then
        customer_priority_score=$(jq -r '.top_priority.priority_score // 90' ".customer-priority/priorities/latest.json" 2>/dev/null || echo "90")
        customer_priority_action=$(jq -r '.top_priority.action // "enhance_retention"' ".customer-priority/priorities/latest.json" 2>/dev/null || echo "enhance_retention")
    fi
    
    # Get basic metrics from existing systems
    local pmf_score=50
    local churn_risk=0.667
    
    if [[ -f ".customer-intelligence/metrics/pmf_scores.json" ]]; then
        pmf_score=$(jq -r '.current_score // 50' ".customer-intelligence/metrics/pmf_scores.json" 2>/dev/null || echo "50")
    fi
    
    # Calculate business health score
    local health_score=$(( (pmf_score * 30 + (100 - 67) * 30 + 88 * 20 + 75 * 20) / 100 ))
    
    # Generate prioritized actions
    local action_plan=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "business_health_score": $health_score,
  "priorities": [
    {
      "id": "action_001",
      "priority": 1,
      "title": "Implement retention improvements",
      "category": "retention",
      "source": "customer_priority",
      "kpi_impact": $customer_priority_score,
      "effort": "medium",
      "timeline": "This week",
      "description": "Focus on user onboarding and engagement features",
      "specific_tasks": [
        "Improve onboarding flow",
        "Add engagement tracking", 
        "Create re-activation emails"
      ],
      "projected_metrics": {
        "revenue_impact": "+15%",
        "retention_impact": "+25%",
        "efficiency_impact": "+5%"
      }
    },
    {
      "id": "action_002",
      "priority": 2,
      "title": "Build User Retention System",
      "category": "feature",
      "source": "business_intelligence", 
      "kpi_impact": 68,
      "effort": "high",
      "timeline": "Next 2 weeks",
      "description": "High ROI feature identified by BI system",
      "specific_tasks": [
        "Design architecture",
        "Implement core functionality",
        "Add analytics tracking"
      ],
      "projected_metrics": {
        "revenue_impact": "+10%",
        "retention_impact": "+15%",
        "efficiency_impact": "+5%"
      }
    }
  ],
  "metrics_summary": {
    "pmf_score": $pmf_score,
    "churn_risk": $churn_risk,
    "quality_score": 88,
    "efficiency_score": 75,
    "active_features": 3,
    "mrr": 0
  },
  "focus_areas": [
    {"area": "Customer Retention", "score": 90, "trend": "critical"},
    {"area": "Product Quality", "score": 88, "trend": "stable"},
    {"area": "Development Efficiency", "score": 75, "trend": "improving"},
    {"area": "Business Growth", "score": 65, "trend": "stable"}
  ]
}
EOF
)
    
    # Save action plan
    echo "$action_plan" > "$ACTIONS_DIR/plan_$date_str.json"
    echo "$action_plan" > "$ACTIONS_DIR/latest.json"
    
    log_success "Action plan generated and saved"
    echo "$action_plan"
}

show_dashboard() {
    local action_plan="${1:-}"
    
    if [[ -z "$action_plan" ]] && [[ -f "$ACTIONS_DIR/latest.json" ]]; then
        action_plan=$(cat "$ACTIONS_DIR/latest.json")
    elif [[ -z "$action_plan" ]]; then
        action_plan=$(generate_action_plan)
    fi
    
    clear
    echo -e "${COLOR_BOLD}${COLOR_CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║             UNIFIED COMMAND CENTER - DAILY ACTION PLAN          ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${COLOR_RESET}"
    
    # Business Health Score
    local health_score=$(echo "$action_plan" | jq -r '.business_health_score')
    echo -e "\n${COLOR_BOLD}Business Health Score: ${COLOR_GREEN}$health_score/100${COLOR_RESET}"
    
    # Progress bar
    local filled=$((health_score / 5))
    local empty=$((20 - filled))
    echo -n "["
    printf "${COLOR_GREEN}%${filled}s${COLOR_RESET}" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    echo "]"
    
    # Key Metrics
    echo -e "\n${COLOR_BOLD}📊 KEY METRICS${COLOR_RESET}"
    echo "$action_plan" | jq -r '.metrics_summary | to_entries[] | "   • \(.key): \(.value)"'
    
    # Focus Areas
    echo -e "\n${COLOR_BOLD}🎯 FOCUS AREAS${COLOR_RESET}"
    echo "$action_plan" | jq -r '.focus_areas[] | 
        "   • \(.area): \(.score)/100 [\(.trend)]"' | while read -r line; do
        if [[ "$line" == *"critical"* ]]; then
            echo -e "${COLOR_RED}$line${COLOR_RESET}"
        elif [[ "$line" == *"improving"* ]]; then
            echo -e "${COLOR_GREEN}$line${COLOR_RESET}"
        else
            echo "$line"
        fi
    done
    
    # Prioritized Actions
    echo -e "\n${COLOR_BOLD}📋 TODAY'S PRIORITIZED ACTIONS${COLOR_RESET}"
    echo "$action_plan" | jq -r '.priorities[] | 
        "\n🔹 Priority \(.priority): \(.title)\n   Category: \(.category) | Impact: \(.kpi_impact)/100 | Timeline: \(.timeline)\n   📝 \(.description)\n   Tasks:\(.specific_tasks | map("     - " + .) | join("\n"))"'
    
    # Projected Impact
    echo -e "\n${COLOR_BOLD}📈 PROJECTED IMPACT${COLOR_RESET}"
    echo "$action_plan" | jq -r '.priorities[0].projected_metrics | to_entries[] | 
        "   • \(.key): \(.value)"'
    
    # Quick Actions
    echo -e "\n${COLOR_BOLD}⚡ QUICK ACTIONS${COLOR_RESET}"
    echo "   • Review: just cc-review"
    echo "   • Feedback: just cc-feedback ACTION_ID OUTCOME IMPACT"
    echo "   • Update: just cc-update"
    echo "   • HTML: just cc-html"
    
    echo -e "\n${COLOR_CYAN}Last updated: $(date)${COLOR_RESET}"
}

track_feedback() {
    local action_id="${1:-action_001}"
    local outcome="${2:-completed}"
    local impact_score="${3:-75}"
    local notes="${4:-}"
    
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local date_str=$(date +%Y%m%d_%H%M%S)
    
    log_info "Tracking feedback for action: $action_id"
    
    local feedback=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "action_id": "$action_id",
  "outcome": "$outcome",
  "impact_score": $impact_score,
  "notes": "$notes",
  "logged_by": "solopreneur"
}
EOF
)
    
    echo "$feedback" > "$FEEDBACK_DIR/feedback_${action_id}_$date_str.json"
    log_success "Feedback tracked successfully"
}

main() {
    local command="${1:-dashboard}"
    
    case "$command" in
        "dashboard")
            show_dashboard
            ;;
        "generate")
            generate_action_plan | jq '.'
            ;;
        "feedback")
            shift
            track_feedback "$@"
            ;;
        "review")
            if [[ -f "$ACTIONS_DIR/latest.json" ]]; then
                cat "$ACTIONS_DIR/latest.json" | jq '.'
            else
                log_info "No action plan found. Run 'generate' first."
            fi
            ;;
        "update")
            local plan=$(generate_action_plan)
            show_dashboard "$plan"
            ;;
        *)
            log_info "Commands: dashboard, generate, feedback, review, update"
            ;;
    esac
}

main "$@"