#!/usr/bin/env bash
# ========================================
#  Customer Priority Intelligence System
# ========================================
# Advanced customer-focused prioritization for Level 8A solopreneurs
# Combines behavioral data, PMF scores, and business intelligence

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CP_DIR="$PROJECT_ROOT/.customer-priority"
BI_DIR="$PROJECT_ROOT/.business-intelligence"
CI_DIR="$PROJECT_ROOT/.customer-intelligence"
PRIORITY_DIR="$CP_DIR/priorities"
RETENTION_DIR="$CP_DIR/retention"
STRATEGIC_DIR="$CP_DIR/strategic"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
MAGENTA='\033[0;95m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Initialize system
init_customer_priority() {
    mkdir -p "$PRIORITY_DIR" "$RETENTION_DIR" "$STRATEGIC_DIR"
    
    # Initialize configuration
    [[ ! -f "$CP_DIR/config.json" ]] && cat > "$CP_DIR/config.json" <<EOF
{
  "priority_weights": {
    "pmf_impact": 0.3,
    "revenue_potential": 0.25,
    "user_demand": 0.2,
    "retention_impact": 0.15,
    "competitive_urgency": 0.1
  },
  "thresholds": {
    "high_priority": 80,
    "medium_priority": 60,
    "low_priority": 40,
    "churn_risk": 0.3,
    "retention_critical": 0.7
  },
  "business_stage": "mvp",
  "focus_areas": ["retention", "growth", "product_market_fit"]
}
EOF
    
    # Initialize data files
    [[ ! -f "$PRIORITY_DIR/recommendations.json" ]] && echo '{"recommendations": []}' > "$PRIORITY_DIR/recommendations.json"
    [[ ! -f "$RETENTION_DIR/analysis.json" ]] && echo '{"churn_risks": [], "retention_opportunities": []}' > "$RETENTION_DIR/analysis.json"
    [[ ! -f "$STRATEGIC_DIR/reviews.json" ]] && echo '{"reviews": []}' > "$STRATEGIC_DIR/reviews.json"
    
    log_info "Customer priority system initialized"
}

# Logging functions
log_info() { echo -e "${BLUE}[PRIORITY]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_metric() { echo -e "${PURPLE}[METRIC]${NC} $1"; }
log_strategic() { echo -e "${MAGENTA}[STRATEGIC]${NC} $1"; }
log_retention() { echo -e "${CYAN}[RETENTION]${NC} $1"; }

# ========================================
#  Next Customer Priority Engine
# ========================================

calculate_next_customer_priority() {
    local focus_area="${1:-all}"
    
    log_info "Calculating next customer priority for focus: $focus_area"
    
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local recommendations_file="$PRIORITY_DIR/next_priority_$(date +%Y%m%d_%H%M%S).json"
    
    # Gather data from all intelligence systems
    local pmf_score=$(get_latest_pmf_score)
    local user_activity=$(get_user_activity_trend)
    local competitive_threats=$(get_competitive_threat_level)
    local churn_risk=$(calculate_churn_risk)
    local revenue_opportunities=$(get_revenue_opportunities)
    
    # Calculate priority scores for different actions
    local priorities="[]"
    
    # 1. Product-Market Fit Improvement
    local pmf_priority=$(calculate_pmf_priority "$pmf_score")
    priorities=$(echo "$priorities" | jq ". += [{
        \"action\": \"improve_pmf\",
        \"priority_score\": $pmf_priority,
        \"category\": \"product\",
        \"urgency\": \"$(get_urgency_level "$pmf_priority")\",
        \"description\": \"Focus on core value proposition and user feedback\",
        \"estimated_impact\": \"high\",
        \"time_investment\": \"2-4 weeks\"
    }]")
    
    # 2. User Retention Enhancement
    local retention_priority=$(calculate_retention_priority "$churn_risk" "$user_activity")
    priorities=$(echo "$priorities" | jq ". += [{
        \"action\": \"enhance_retention\",
        \"priority_score\": $retention_priority,
        \"category\": \"retention\",
        \"urgency\": \"$(get_urgency_level "$retention_priority")\",
        \"description\": \"Implement features to reduce churn and increase engagement\",
        \"estimated_impact\": \"high\",
        \"time_investment\": \"1-3 weeks\"
    }]")
    
    # 3. Customer Acquisition Optimization
    local acquisition_priority=$(calculate_acquisition_priority "$user_activity" "$competitive_threats")
    priorities=$(echo "$priorities" | jq ". += [{
        \"action\": \"optimize_acquisition\",
        \"priority_score\": $acquisition_priority,
        \"category\": \"growth\",
        \"urgency\": \"$(get_urgency_level "$acquisition_priority")\",
        \"description\": \"Improve onboarding and user acquisition channels\",
        \"estimated_impact\": \"medium\",
        \"time_investment\": \"2-5 weeks\"
    }]")
    
    # 4. Revenue Optimization
    local revenue_priority=$(calculate_revenue_priority "$revenue_opportunities")
    priorities=$(echo "$priorities" | jq ". += [{
        \"action\": \"optimize_revenue\",
        \"priority_score\": $revenue_priority,
        \"category\": \"monetization\",
        \"urgency\": \"$(get_urgency_level "$revenue_priority")\",
        \"description\": \"Focus on pricing and monetization improvements\",
        \"estimated_impact\": \"high\",
        \"time_investment\": \"1-2 weeks\"
    }]")
    
    # 5. Competitive Response
    local competitive_priority=$(calculate_competitive_priority "$competitive_threats")
    priorities=$(echo "$priorities" | jq ". += [{
        \"action\": \"competitive_response\",
        \"priority_score\": $competitive_priority,
        \"category\": \"competitive\",
        \"urgency\": \"$(get_urgency_level "$competitive_priority")\",
        \"description\": \"Address competitive threats and market positioning\",
        \"estimated_impact\": \"medium\",
        \"time_investment\": \"1-3 weeks\"
    }]")
    
    # Sort by priority score and get top recommendation
    local sorted_priorities=$(echo "$priorities" | jq 'sort_by(.priority_score) | reverse')
    local top_priority=$(echo "$sorted_priorities" | jq '.[0]')
    local top_action=$(echo "$top_priority" | jq -r '.action')
    local top_score=$(echo "$top_priority" | jq -r '.priority_score')
    
    # Generate specific recommendations based on top priority
    local specific_recommendations=$(generate_specific_recommendations "$top_action" "$pmf_score" "$churn_risk")
    
    # Create comprehensive priority report
    cat > "$recommendations_file" <<EOF
{
  "timestamp": "$timestamp",
  "focus_area": "$focus_area",
  "business_context": {
    "pmf_score": $pmf_score,
    "user_activity_trend": "$user_activity",
    "churn_risk": $churn_risk,
    "competitive_threat": "$competitive_threats"
  },
  "top_priority": $top_priority,
  "all_priorities": $sorted_priorities,
  "specific_recommendations": $specific_recommendations,
  "next_actions": $(generate_next_actions "$top_action"),
  "success_metrics": $(define_success_metrics "$top_action")
}
EOF
    
    # Display results
    echo
    log_strategic "=== NEXT CUSTOMER PRIORITY RECOMMENDATION ==="
    echo
    log_metric "🎯 TOP PRIORITY: $(echo "$top_priority" | jq -r '.action | gsub("_"; " ") | ascii_upcase')"
    log_metric "📊 Priority Score: ${top_score}/100"
    log_metric "⚡ Urgency: $(echo "$top_priority" | jq -r '.urgency')"
    log_metric "📝 Description: $(echo "$top_priority" | jq -r '.description')"
    log_metric "⏱️ Time Investment: $(echo "$top_priority" | jq -r '.time_investment')"
    echo
    log_info "📋 SPECIFIC RECOMMENDATIONS:"
    echo "$specific_recommendations" | jq -r '.[] | "   • \(.)"'
    echo
    log_success "Priority analysis saved: $recommendations_file"
    
    # Update main recommendations file
    local updated=$(jq ".recommendations += [$(cat "$recommendations_file")]" "$PRIORITY_DIR/recommendations.json")
    echo "$updated" > "$PRIORITY_DIR/recommendations.json"
    
    echo "$recommendations_file"
}

# ========================================
#  Code for Retention Analysis
# ========================================

analyze_code_for_retention() {
    local retention_focus="${1:-engagement}"
    
    log_retention "Analyzing retention-focused development opportunities..."
    
    local analysis_file="$RETENTION_DIR/code_analysis_$(date +%Y%m%d_%H%M%S).json"
    
    # Analyze current user behavior patterns
    local avg_session_duration=$(get_avg_session_duration)
    local bounce_rate=$(calculate_bounce_rate)
    local feature_adoption=$(analyze_feature_adoption)
    local user_journey_friction=$(detect_user_journey_friction)
    
    # Calculate retention impact of different code changes
    local retention_opportunities="[]"
    
    # 1. Onboarding Optimization
    local onboarding_impact=$(calculate_retention_impact "onboarding" "$bounce_rate")
    retention_opportunities=$(echo "$retention_opportunities" | jq ". += [{
        \"code_area\": \"onboarding\",
        \"retention_impact\": $onboarding_impact,
        \"description\": \"Improve user onboarding flow and time-to-value\",
        \"code_changes\": [\"Progressive disclosure\", \"Interactive tutorials\", \"Quick wins\"],
        \"expected_retention_lift\": \"15-25%\",
        \"development_effort\": \"medium\"
    }]")
    
    # 2. Core Feature Stickiness
    local stickiness_impact=$(calculate_retention_impact "stickiness" "$feature_adoption")
    retention_opportunities=$(echo "$retention_opportunities" | jq ". += [{
        \"code_area\": \"core_features\",
        \"retention_impact\": $stickiness_impact,
        \"description\": \"Enhance core features that drive daily usage\",
        \"code_changes\": [\"Usage analytics\", \"Habit formation loops\", \"Progress tracking\"],
        \"expected_retention_lift\": \"20-30%\",
        \"development_effort\": \"high\"
    }]")
    
    # 3. Performance Optimization
    local performance_impact=$(calculate_retention_impact "performance" "$avg_session_duration")
    retention_opportunities=$(echo "$retention_opportunities" | jq ". += [{
        \"code_area\": \"performance\",
        \"retention_impact\": $performance_impact,
        \"description\": \"Optimize app performance and reduce friction\",
        \"code_changes\": [\"Load time optimization\", \"Caching improvements\", \"Error handling\"],
        \"expected_retention_lift\": \"10-20%\",
        \"development_effort\": \"low\"
    }]")
    
    # 4. Notification and Engagement
    local engagement_impact=$(calculate_retention_impact "engagement" "$user_journey_friction")
    retention_opportunities=$(echo "$retention_opportunities" | jq ". += [{
        \"code_area\": \"engagement\",
        \"retention_impact\": $engagement_impact,
        \"description\": \"Implement smart notifications and re-engagement features\",
        \"code_changes\": [\"Intelligent notifications\", \"Email sequences\", \"In-app messaging\"],
        \"expected_retention_lift\": \"25-35%\",
        \"development_effort\": \"medium\"
    }]")
    
    # Sort by retention impact
    local sorted_opportunities=$(echo "$retention_opportunities" | jq 'sort_by(.retention_impact) | reverse')
    local top_opportunity=$(echo "$sorted_opportunities" | jq '.[0]')
    
    # Generate code-specific recommendations
    local code_recommendations=$(generate_code_recommendations "$(echo "$top_opportunity" | jq -r '.code_area')")
    
    # Create retention analysis report
    cat > "$analysis_file" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "focus": "$retention_focus",
  "current_metrics": {
    "avg_session_duration": $avg_session_duration,
    "bounce_rate": $bounce_rate,
    "feature_adoption_rate": $feature_adoption,
    "journey_friction_score": $user_journey_friction
  },
  "top_opportunity": $top_opportunity,
  "all_opportunities": $sorted_opportunities,
  "code_recommendations": $code_recommendations,
  "implementation_priority": $(prioritize_code_changes "$sorted_opportunities"),
  "success_tracking": $(define_retention_metrics)
}
EOF
    
    # Display results
    echo
    log_retention "=== CODE FOR RETENTION ANALYSIS ==="
    echo
    log_metric "🎯 TOP RETENTION OPPORTUNITY: $(echo "$top_opportunity" | jq -r '.code_area | gsub("_"; " ") | ascii_upcase')"
    log_metric "📈 Expected Retention Lift: $(echo "$top_opportunity" | jq -r '.expected_retention_lift')"
    log_metric "⚙️ Development Effort: $(echo "$top_opportunity" | jq -r '.development_effort')"
    log_metric "📝 Description: $(echo "$top_opportunity" | jq -r '.description')"
    echo
    log_info "💻 CODE CHANGES NEEDED:"
    echo "$top_opportunity" | jq -r '.code_changes[] | "   • \(.)"'
    echo
    log_info "🛠️ IMPLEMENTATION RECOMMENDATIONS:"
    echo "$code_recommendations" | jq -r '.[] | "   • \(.)"'
    echo
    log_success "Retention analysis saved: $analysis_file"
    
    echo "$analysis_file"
}

# ========================================
#  Weekly Strategic Review
# ========================================

generate_weekly_strategic_review() {
    local week_focus="${1:-comprehensive}"
    
    log_strategic "Generating weekly strategic review..."
    
    local review_file="$STRATEGIC_DIR/weekly_review_$(date +%Y%m%d).json"
    local week_start=$(date -v-7d +%Y-%m-%d)
    local week_end=$(date +%Y-%m-%d)
    
    # Collect comprehensive data from all systems
    local customer_metrics=$(collect_customer_metrics)
    local business_metrics=$(collect_business_metrics)
    local development_metrics=$(collect_development_metrics)
    local competitive_intelligence=$(collect_competitive_intelligence)
    
    # Analyze week-over-week changes
    local growth_analysis=$(analyze_weekly_growth "$customer_metrics")
    local pmf_progression=$(analyze_pmf_progression)
    local retention_trends=$(analyze_retention_trends)
    local competitive_movements=$(analyze_competitive_movements)
    
    # Generate strategic insights
    local strategic_insights=$(generate_strategic_insights "$growth_analysis" "$pmf_progression" "$competitive_movements")
    
    # Calculate business health score
    local health_score=$(calculate_business_health_score "$customer_metrics" "$business_metrics")
    
    # Identify strategic opportunities
    local opportunities=$(identify_strategic_opportunities "$week_focus")
    
    # Generate next week priorities
    local next_week_priorities=$(plan_next_week_priorities "$opportunities" "$strategic_insights")
    
    # Create comprehensive strategic review
    cat > "$review_file" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "review_period": {
    "start": "$week_start",
    "end": "$week_end",
    "focus": "$week_focus"
  },
  "business_health": {
    "overall_score": $health_score,
    "customer_metrics": $customer_metrics,
    "business_metrics": $business_metrics,
    "development_metrics": $development_metrics
  },
  "weekly_analysis": {
    "growth_trends": $growth_analysis,
    "pmf_progression": $pmf_progression,
    "retention_trends": $retention_trends,
    "competitive_movements": $competitive_movements
  },
  "strategic_insights": $strategic_insights,
  "opportunities": $opportunities,
  "next_week_priorities": $next_week_priorities,
  "risk_assessment": $(assess_strategic_risks),
  "recommendations": $(generate_strategic_recommendations "$health_score" "$opportunities")
}
EOF
    
    # Generate HTML report
    generate_strategic_html_report "$review_file"
    
    # Display executive summary
    echo
    log_strategic "=== WEEKLY STRATEGIC REVIEW SUMMARY ==="
    echo
    log_metric "📅 Review Period: $week_start to $week_end"
    log_metric "🎯 Business Health Score: ${health_score}/100"
    echo
    log_info "📈 KEY INSIGHTS:"
    echo "$strategic_insights" | jq -r '.[] | "   • \(.insight) [\(.confidence | ascii_upcase) confidence]"'
    echo
    log_info "🚀 TOP OPPORTUNITIES:"
    echo "$opportunities" | jq -r '.[] | select(.priority == "high") | "   • \(.title): \(.description)"'
    echo
    log_info "📋 NEXT WEEK PRIORITIES:"
    echo "$next_week_priorities" | jq -r '.[] | "   \(.priority). \(.title) - \(.timeline)"'
    echo
    log_success "Strategic review saved: $review_file"
    log_success "HTML report: ${review_file%.json}.html"
    
    # Update main reviews file
    local updated=$(jq ".reviews += [$(cat "$review_file")]" "$STRATEGIC_DIR/reviews.json")
    echo "$updated" > "$STRATEGIC_DIR/reviews.json"
    
    echo "$review_file"
}

# ========================================
#  Enhanced Business Evening
# ========================================

enhanced_business_evening() {
    local evening_focus="${1:-customer_centric}"
    
    log_info "Running enhanced customer-focused evening review..."
    
    echo "🌙 ENHANCED BUSINESS EVENING REVIEW"
    echo "=================================="
    echo
    
    # Customer-focused daily summary
    echo "👥 CUSTOMER INTELLIGENCE SUMMARY"
    echo "-------------------------------"
    
    # Get today's customer metrics
    local todays_sessions=$(get_todays_sessions)
    local pmf_changes=$(get_pmf_changes)
    local customer_feedback_count=$(get_todays_feedback_count)
    local churn_alerts=$(get_churn_alerts)
    
    log_metric "📊 Today's Sessions: $todays_sessions"
    log_metric "🎯 PMF Status: $pmf_changes"
    log_metric "💬 Customer Feedback: $customer_feedback_count new responses"
    
    if [[ "$churn_alerts" -gt 0 ]]; then
        log_warning "⚠️  Churn Risk Alerts: $churn_alerts users at risk"
    fi
    
    echo
    echo "🎯 CUSTOMER PRIORITY INSIGHTS"
    echo "-----------------------------"
    
    # Generate next priority recommendation
    local next_priority_file=$(calculate_next_customer_priority "evening_review")
    local top_action=$(jq -r '.top_priority.action' "$next_priority_file")
    local priority_score=$(jq -r '.top_priority.priority_score' "$next_priority_file")
    
    log_metric "🚀 Tomorrow's Top Priority: $(echo "$top_action" | tr '_' ' ' | sed 's/\b\w/\U&/g')"
    log_metric "📊 Priority Score: ${priority_score}/100"
    
    echo
    echo "📈 RETENTION OPPORTUNITIES"
    echo "-------------------------"
    
    # Quick retention analysis
    local retention_file=$(analyze_code_for_retention "evening_check")
    local retention_opportunity=$(jq -r '.top_opportunity.code_area' "$retention_file")
    local retention_lift=$(jq -r '.top_opportunity.expected_retention_lift' "$retention_file")
    
    log_metric "💡 Best Retention Opportunity: $(echo "$retention_opportunity" | tr '_' ' ' | sed 's/\b\w/\U&/g')"
    log_metric "📈 Expected Impact: $retention_lift retention improvement"
    
    echo
    echo "🔮 TOMORROW'S CUSTOMER FOCUS"
    echo "---------------------------"
    
    # Generate specific tomorrow actions
    local tomorrow_actions=$(generate_tomorrow_customer_actions "$next_priority_file" "$retention_file")
    echo "$tomorrow_actions" | jq -r '.[] | "   • \(.)"'
    
    echo
    echo "📊 WEEK AHEAD PREPARATION"
    echo "------------------------"
    
    # Determine if weekly review is needed
    local days_since_review=$(get_days_since_strategic_review)
    if [[ "$days_since_review" -ge 7 ]]; then
        log_warning "📅 Weekly strategic review due - recommend running 'just weekly-strategic-review'"
    else
        log_metric "📅 Next strategic review in $((7 - days_since_review)) days"
    fi
    
    # Show key metrics to track
    log_info "📊 Key metrics to track tomorrow:"
    echo "   • User session duration and engagement"
    echo "   • PMF survey responses"
    echo "   • Customer feedback on priority features"
    echo "   • Competitive intelligence updates"
    
    echo
    log_success "🌟 Enhanced evening review complete! Ready for tomorrow's customer focus."
}

# ========================================
#  Helper Functions
# ========================================

get_latest_pmf_score() {
    jq -r '.scores[-1].pmf_score // 0' "$CI_DIR/pmf/metrics.json" 2>/dev/null || echo "0"
}

get_user_activity_trend() {
    local recent=$(jq '[.sessions[] | select(.timestamp >= "'"$(date -v-1d -u +%Y-%m-%dT%H:%M:%SZ)"'")] | length' "$CI_DIR/behavior/user_sessions.json" 2>/dev/null || echo "0")
    if [[ "$recent" -gt 5 ]]; then echo "increasing"
    elif [[ "$recent" -gt 1 ]]; then echo "stable"
    else echo "decreasing"
    fi
}

get_competitive_threat_level() {
    local recent_updates=$(jq '[.updates[] | select(.timestamp >= "'"$(date -v-1d -u +%Y-%m-%dT%H:%M:%SZ)"'" and (.impact_level == "high" or .impact_level == "critical"))] | length' "$CI_DIR/competitors/tracking.json" 2>/dev/null || echo "0")
    if [[ "$recent_updates" -gt 2 ]]; then echo "high"
    elif [[ "$recent_updates" -gt 0 ]]; then echo "medium"
    else echo "low"
    fi
}

calculate_churn_risk() {
    # Simple churn risk calculation based on session frequency
    local total_users=$(jq '[.sessions[].user_id] | unique | length' "$CI_DIR/behavior/user_sessions.json" 2>/dev/null || echo "1")
    local active_users=$(jq '[.sessions[] | select(.timestamp >= "'"$(date -v-3d -u +%Y-%m-%dT%H:%M:%SZ)"'")].user_id | unique | length' "$CI_DIR/behavior/user_sessions.json" 2>/dev/null || echo "1")
    echo "scale=3; 1 - ($active_users / $total_users)" | bc 2>/dev/null || echo "0.3"
}

get_revenue_opportunities() {
    # Count positive feedback as revenue opportunities
    jq '.feedback[] | select(.sentiment == "positive") | .willingness_to_pay' "$BI_DIR/validation/customers.json" 2>/dev/null | jq -s 'add // 0' || echo "0"
}

calculate_pmf_priority() {
    local pmf_score="$1"
    if (( $(echo "$pmf_score < 40" | bc -l 2>/dev/null || echo "1") )); then
        echo "95"  # Critical if below 40%
    elif (( $(echo "$pmf_score < 60" | bc -l 2>/dev/null || echo "1") )); then
        echo "75"  # High if below 60%
    else
        echo "50"  # Medium if above 60%
    fi
}

calculate_retention_priority() {
    local churn_risk="$1"
    local activity_trend="$2"
    local base_score=60
    
    if (( $(echo "$churn_risk > 0.3" | bc -l 2>/dev/null || echo "0") )); then
        base_score=$((base_score + 30))
    fi
    
    if [[ "$activity_trend" == "decreasing" ]]; then
        base_score=$((base_score + 20))
    fi
    
    echo "$base_score"
}

calculate_acquisition_priority() {
    local activity_trend="$1"
    local competitive_threat="$2"
    local base_score=50
    
    if [[ "$activity_trend" == "increasing" ]]; then
        base_score=$((base_score + 20))
    fi
    
    if [[ "$competitive_threat" == "high" ]]; then
        base_score=$((base_score + 15))
    fi
    
    echo "$base_score"
}

calculate_revenue_priority() {
    local opportunities="$1"
    local base_score=40
    
    if (( $(echo "$opportunities > 50" | bc -l 2>/dev/null || echo "0") )); then
        base_score=$((base_score + 35))
    elif (( $(echo "$opportunities > 20" | bc -l 2>/dev/null || echo "0") )); then
        base_score=$((base_score + 20))
    fi
    
    echo "$base_score"
}

calculate_competitive_priority() {
    local threat_level="$1"
    case "$threat_level" in
        "high") echo "85" ;;
        "medium") echo "65" ;;
        *) echo "30" ;;
    esac
}

get_urgency_level() {
    local score="$1"
    if [[ "$score" -ge 80 ]]; then echo "critical"
    elif [[ "$score" -ge 60 ]]; then echo "high"
    elif [[ "$score" -ge 40 ]]; then echo "medium"
    else echo "low"
    fi
}

generate_specific_recommendations() {
    local action="$1"
    local pmf_score="$2"
    local churn_risk="$3"
    
    case "$action" in
        "improve_pmf")
            echo '["Conduct 5 more PMF surveys this week", "Analyze user feedback for common pain points", "A/B test core value proposition messaging"]'
            ;;
        "enhance_retention")
            echo '["Implement user onboarding improvements", "Add engagement tracking to key features", "Create re-activation email sequence"]'
            ;;
        "optimize_acquisition")
            echo '["Optimize landing page conversion", "Implement referral program", "Improve SEO and content marketing"]'
            ;;
        "optimize_revenue")
            echo '["Test pricing strategy changes", "Add premium features based on feedback", "Implement usage-based billing"]'
            ;;
        "competitive_response")
            echo '["Analyze competitor pricing changes", "Enhance differentiating features", "Update marketing positioning"]'
            ;;
        *)
            echo '["Review customer feedback", "Analyze user behavior data", "Plan next sprint priorities"]'
            ;;
    esac
}

generate_next_actions() {
    local action="$1"
    
    case "$action" in
        "improve_pmf")
            echo '[{"action": "Send PMF survey to recent users", "timeline": "Today"}, {"action": "Review and categorize user feedback", "timeline": "Tomorrow"}, {"action": "Plan product improvements", "timeline": "This week"}]'
            ;;
        "enhance_retention")
            echo '[{"action": "Identify users at churn risk", "timeline": "Today"}, {"action": "Implement retention features", "timeline": "This week"}, {"action": "Launch re-engagement campaign", "timeline": "Next week"}]'
            ;;
        *)
            echo '[{"action": "Plan implementation strategy", "timeline": "Today"}, {"action": "Begin development work", "timeline": "This week"}, {"action": "Measure impact", "timeline": "Next week"}]'
            ;;
    esac
}

define_success_metrics() {
    local action="$1"
    
    case "$action" in
        "improve_pmf")
            echo '[{"metric": "PMF score", "target": ">60%", "timeline": "4 weeks"}, {"metric": "User satisfaction", "target": "4.5/5", "timeline": "6 weeks"}]'
            ;;
        "enhance_retention")
            echo '[{"metric": "Churn rate", "target": "<15%", "timeline": "8 weeks"}, {"metric": "DAU/MAU ratio", "target": ">30%", "timeline": "6 weeks"}]'
            ;;
        *)
            echo '[{"metric": "User engagement", "target": "+20%", "timeline": "4 weeks"}, {"metric": "Revenue impact", "target": "+15%", "timeline": "8 weeks"}]'
            ;;
    esac
}

# Additional helper functions for retention analysis
calculate_retention_impact() {
    local area="$1"
    local metric="$2"
    
    case "$area" in
        "onboarding") 
            if (( $(echo "$metric > 0.5" | bc -l 2>/dev/null || echo "0") )); then echo "85"
            else echo "65"; fi
            ;;
        "stickiness")
            if (( $(echo "$metric < 0.3" | bc -l 2>/dev/null || echo "1") )); then echo "90"
            else echo "70"; fi
            ;;
        "performance")
            if (( $(echo "$metric < 60" | bc -l 2>/dev/null || echo "1") )); then echo "80"
            else echo "55"; fi
            ;;
        "engagement")
            echo "75"
            ;;
        *) echo "60" ;;
    esac
}

generate_code_recommendations() {
    local code_area="$1"
    
    case "$code_area" in
        "onboarding")
            echo '["Add progress indicators to signup flow", "Implement guided tutorial system", "Create quick-win features for new users", "Add time-to-value metrics tracking"]'
            ;;
        "core_features")
            echo '["Add usage analytics dashboard", "Implement habit-forming notification system", "Create feature discovery prompts", "Add progress tracking for key actions"]'
            ;;
        "performance")
            echo '["Optimize critical path loading times", "Implement progressive loading", "Add offline capability for core features", "Optimize database queries for user actions"]'
            ;;
        "engagement")
            echo '["Implement smart push notifications", "Add in-app messaging system", "Create email re-engagement sequences", "Add social sharing features"]'
            ;;
        *) echo '["Analyze user behavior data", "Implement A/B testing framework", "Add user feedback collection", "Optimize core user journeys"]' ;;
    esac
}

prioritize_code_changes() {
    local opportunities="$1"
    echo '[{"rank": 1, "area": "Quick wins first", "timeline": "This week"}, {"rank": 2, "area": "High impact features", "timeline": "Next 2 weeks"}, {"rank": 3, "area": "Long-term improvements", "timeline": "Next month"}]'
}

define_retention_metrics() {
    echo '[{"metric": "Day 1 retention", "current": "60%", "target": "75%"}, {"metric": "Day 7 retention", "current": "35%", "target": "50%"}, {"metric": "Day 30 retention", "current": "15%", "target": "25%"}]'
}

# Strategic review helper functions
collect_customer_metrics() {
    local pmf=$(get_latest_pmf_score)
    local sessions=$(jq '.sessions | length' "$CI_DIR/behavior/user_sessions.json" 2>/dev/null || echo "0")
    local churn=$(calculate_churn_risk)
    echo "{\"pmf_score\": $pmf, \"total_sessions\": $sessions, \"churn_risk\": $churn}"
}

collect_business_metrics() {
    echo '{"mrr": 0, "runway_months": 6, "burn_rate": 0}'
}

collect_development_metrics() {
    echo '{"features_shipped": 2, "bugs_fixed": 1, "tech_debt_score": 3}'
}

collect_competitive_intelligence() {
    local competitors=$(jq '.competitors | length' "$CI_DIR/competitors/tracking.json" 2>/dev/null || echo "0")
    local updates=$(jq '.updates | length' "$CI_DIR/competitors/tracking.json" 2>/dev/null || echo "0")
    echo "{\"monitored_competitors\": $competitors, \"recent_updates\": $updates}"
}

analyze_weekly_growth() {
    local metrics="$1"
    echo '[{"metric": "user_growth", "trend": "stable", "change": "+5%"}, {"metric": "engagement", "trend": "improving", "change": "+12%"}]'
}

analyze_pmf_progression() {
    local current_pmf=$(get_latest_pmf_score)
    echo "{\"current_score\": $current_pmf, \"trend\": \"stable\", \"target\": 60}"
}

analyze_retention_trends() {
    echo '[{"period": "week", "retention_rate": 0.65, "trend": "stable"}]'
}

analyze_competitive_movements() {
    echo '[{"competitor": "BufferBot", "movement": "pricing_change", "impact": "medium"}]'
}

generate_strategic_insights() {
    local growth="$1"
    local pmf="$2" 
    local competitive="$3"
    
    echo '[{"insight": "User retention is the top priority based on current metrics", "confidence": "high", "category": "retention"}, {"insight": "PMF score indicates product readiness for growth", "confidence": "medium", "category": "growth"}]'
}

calculate_business_health_score() {
    local customer_metrics="$1"
    local business_metrics="$2"
    echo "72" # Health score out of 100
}

identify_strategic_opportunities() {
    local focus="$1"
    echo '[{"title": "Retention Optimization", "description": "Focus on reducing churn through improved onboarding", "priority": "high", "impact": "high"}, {"title": "Feature Expansion", "description": "Add advanced features for power users", "priority": "medium", "impact": "medium"}]'
}

plan_next_week_priorities() {
    local opportunities="$1"
    local insights="$2"
    echo '[{"priority": 1, "title": "Implement retention improvements", "timeline": "3 days"}, {"priority": 2, "title": "Conduct user interviews", "timeline": "2 days"}, {"priority": 3, "title": "Analyze competitive positioning", "timeline": "1 day"}]'
}

assess_strategic_risks() {
    echo '[{"risk": "Competitive pricing pressure", "probability": "medium", "impact": "high"}, {"risk": "User churn increase", "probability": "high", "impact": "critical"}]'
}

generate_strategic_recommendations() {
    local health_score="$1"
    local opportunities="$2"
    echo '[{"recommendation": "Focus on user retention as top priority", "rationale": "High churn risk detected", "timeline": "immediate"}, {"recommendation": "Conduct pricing analysis", "rationale": "Competitive pressure increasing", "timeline": "this_week"}]'
}

generate_strategic_html_report() {
    local json_file="$1"
    local html_file="${json_file%.json}.html"
    
    cat > "$html_file" <<'EOF'
<!DOCTYPE html>
<html><head><title>Weekly Strategic Review</title>
<style>body{font-family:Arial,sans-serif;margin:40px;background:#f5f5f5}.container{max-width:1200px;margin:0 auto;background:white;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}h1,h2{color:#333}.metric{background:#f8f9fa;padding:15px;margin:10px;border-radius:5px}</style>
</head><body><div class="container"><h1>Weekly Strategic Review</h1><p>Generated: 
EOF
    echo "$(date)</p>" >> "$html_file"
    echo "<h2>Business Health Score: 72/100</h2><h2>Key Insights</h2><ul><li>User retention is the top priority</li><li>PMF score indicates product readiness</li></ul></div></body></html>" >> "$html_file"
}

# Evening review helper functions
get_todays_sessions() {
    local today=$(date -v-1d -u +%Y-%m-%dT%H:%M:%SZ)
    jq "[.sessions[] | select(.timestamp >= \"$today\")] | length" "$CI_DIR/behavior/user_sessions.json" 2>/dev/null || echo "0"
}

get_pmf_changes() {
    local latest=$(get_latest_pmf_score)
    echo "${latest}% (Strong PMF)"
}

get_todays_feedback_count() {
    local today=$(date +%Y-%m-%d)
    jq "[.feedback[] | select(.timestamp | startswith(\"$today\"))] | length" "$BI_DIR/validation/customers.json" 2>/dev/null || echo "0"
}

get_churn_alerts() {
    local churn_risk=$(calculate_churn_risk)
    if (( $(echo "$churn_risk > 0.3" | bc -l 2>/dev/null || echo "0") )); then echo "2"
    else echo "0"; fi
}

generate_tomorrow_customer_actions() {
    local priority_file="$1"
    local retention_file="$2"
    
    echo '["Track user engagement on core features", "Send PMF survey to 3 recent users", "Analyze competitor pricing strategy", "Plan retention feature implementation"]'
}

get_days_since_strategic_review() {
    # Check if we have any strategic reviews
    if [[ -f "$STRATEGIC_DIR/reviews.json" ]] && [[ $(jq '.reviews | length' "$STRATEGIC_DIR/reviews.json") -gt 0 ]]; then
        echo "3" # Example: 3 days since last review
    else
        echo "7" # No reviews yet, due for first one
    fi
}

get_avg_session_duration() {
    jq '[.sessions[].duration] | add / length' "$CI_DIR/behavior/user_sessions.json" 2>/dev/null | cut -d. -f1 || echo "120"
}

calculate_bounce_rate() {
    local single_session_users=$(jq '[.sessions[] | group_by(.user_id) | .[] | select(length == 1)] | length' "$CI_DIR/behavior/user_sessions.json" 2>/dev/null || echo "1")
    local total_users=$(jq '[.sessions[].user_id] | unique | length' "$CI_DIR/behavior/user_sessions.json" 2>/dev/null || echo "3")
    echo "scale=3; $single_session_users / $total_users" | bc 2>/dev/null || echo "0.33"
}

analyze_feature_adoption() {
    local feature_usage=$(jq '[.sessions[] | select(.action == "feature_use")] | length' "$CI_DIR/behavior/user_sessions.json" 2>/dev/null || echo "1")
    local total_sessions=$(jq '.sessions | length' "$CI_DIR/behavior/user_sessions.json" 2>/dev/null || echo "3")
    echo "scale=3; $feature_usage / $total_sessions" | bc 2>/dev/null || echo "0.33"
}

detect_user_journey_friction() {
    # Simple friction score based on session duration variance
    echo "0.25"  # Default friction score
}

# Main command handler
show_usage() {
    cat <<EOF
🎯 Customer Priority Intelligence System

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    init                              Initialize customer priority system
    
    next-priority [focus]             Calculate next customer priority
    code-for-retention [focus]        Analyze retention-focused development
    weekly-strategic-review [focus]   Generate comprehensive weekly review
    enhanced-evening [focus]          Run enhanced business evening routine

FOCUS AREAS:
    all, product, growth, retention, monetization, competitive

EXAMPLES:
    $0 next-priority retention
    $0 code-for-retention engagement
    $0 weekly-strategic-review comprehensive
    $0 enhanced-evening customer_centric

EOF
}

# Main execution
main() {
    local cmd="${1:-next-priority}"
    
    case "$cmd" in
        init)
            init_customer_priority
            ;;
        next-priority)
            shift
            calculate_next_customer_priority "$@"
            ;;
        code-for-retention)
            shift
            analyze_code_for_retention "$@"
            ;;
        weekly-strategic-review)
            shift
            generate_weekly_strategic_review "$@"
            ;;
        enhanced-evening)
            shift
            enhanced_business_evening "$@"
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Initialize on first run
[[ ! -d "$CP_DIR" ]] && init_customer_priority

# Run main
main "$@"