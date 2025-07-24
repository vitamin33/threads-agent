#!/usr/bin/env bash
# ========================================
#  Customer Intelligence System for Solopreneurs
# ========================================
# Automated user behavior analysis, PMF tracking, and competitor monitoring
# Designed for minimal manual overhead and maximum insight

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CI_DIR="$PROJECT_ROOT/.customer-intelligence"
BEHAVIOR_DIR="$CI_DIR/behavior"
PMF_DIR="$CI_DIR/pmf"
COMPETITOR_DIR="$CI_DIR/competitors"
INSIGHTS_DIR="$CI_DIR/insights"
AUTOMATION_DIR="$CI_DIR/automation"
ALERTS_DIR="$CI_DIR/alerts"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
MAGENTA='\033[0;95m'
NC='\033[0m' # No Color

# Initialize system
init_customer_intelligence() {
    mkdir -p "$BEHAVIOR_DIR" "$PMF_DIR" "$COMPETITOR_DIR" "$INSIGHTS_DIR" "$AUTOMATION_DIR" "$ALERTS_DIR"

    # Initialize configuration
    [[ ! -f "$CI_DIR/config.json" ]] && cat > "$CI_DIR/config.json" <<EOF
{
  "tracking": {
    "user_behavior": true,
    "pmf_metrics": true,
    "competitor_monitoring": true,
    "automated_insights": true
  },
  "thresholds": {
    "pmf_score_alert": 40,
    "churn_rate_alert": 0.15,
    "engagement_drop_alert": 0.20,
    "competitor_activity_alert": 5
  },
  "automation": {
    "daily_analysis": true,
    "weekly_reports": true,
    "alert_notifications": true,
    "auto_insights": true
  },
  "integrations": {
    "google_analytics": false,
    "mixpanel": false,
    "custom_events": true
  }
}
EOF

    # Initialize data files
    [[ ! -f "$BEHAVIOR_DIR/user_sessions.json" ]] && echo '{"sessions": []}' > "$BEHAVIOR_DIR/user_sessions.json"
    [[ ! -f "$PMF_DIR/metrics.json" ]] && echo '{"scores": [], "surveys": []}' > "$PMF_DIR/metrics.json"
    [[ ! -f "$COMPETITOR_DIR/tracking.json" ]] && echo '{"competitors": [], "updates": []}' > "$COMPETITOR_DIR/tracking.json"
    [[ ! -f "$INSIGHTS_DIR/analysis.json" ]] && echo '{"insights": [], "trends": []}' > "$INSIGHTS_DIR/analysis.json"
    [[ ! -f "$ALERTS_DIR/notifications.json" ]] && echo '{"alerts": []}' > "$ALERTS_DIR/notifications.json"

    log_info "Customer intelligence system initialized"
}

# Logging functions
log_info() { echo -e "${BLUE}[CI]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_metric() { echo -e "${PURPLE}[METRIC]${NC} $1"; }
log_insight() { echo -e "${MAGENTA}[INSIGHT]${NC} $1"; }
log_behavior() { echo -e "${CYAN}[BEHAVIOR]${NC} $1"; }

# ========================================
#  User Behavior Analysis Engine
# ========================================

track_user_behavior() {
    local user_id="${1:-anonymous}"
    local action="${2:-page_view}"
    local page="${3:-home}"
    local session_duration="${4:-0}"
    local metadata='{"source":"manual"}'

    log_behavior "Tracking behavior: $user_id -> $action"

    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local session_id=$(echo "$user_id$timestamp" | md5 | cut -c1-8)

    # Create behavior event
    local week=$(date +%Y-W%U)
    local month=$(date +%Y-%m)
    local event=$(cat <<EOF
{
  "session_id": "$session_id",
  "user_id": "$user_id",
  "timestamp": "$timestamp",
  "action": "$action",
  "page": "$page",
  "duration": $session_duration,
  "metadata": $metadata,
  "week": "$week",
  "month": "$month"
}
EOF
)

    # Add to sessions
    echo "$event" | jq . > /tmp/event.json  # Validate JSON first
    local updated=$(jq ".sessions += [$(cat /tmp/event.json)]" "$BEHAVIOR_DIR/user_sessions.json")
    echo "$updated" > "$BEHAVIOR_DIR/user_sessions.json"
    rm -f /tmp/event.json

    # Auto-analyze if we have enough data
    local session_count=$(jq '.sessions | length' "$BEHAVIOR_DIR/user_sessions.json")
    if [[ "$session_count" -gt 50 ]] && [[ $((session_count % 25)) -eq 0 ]]; then
        analyze_user_behavior_patterns > /dev/null 2>&1 &
    fi

    log_success "Behavior tracked for $user_id"
}

analyze_user_behavior_patterns() {
    log_behavior "Analyzing user behavior patterns..."

    local sessions_file="$BEHAVIOR_DIR/user_sessions.json"
    local analysis_file="$BEHAVIOR_DIR/analysis_$(date +%Y%m%d_%H%M%S).json"

    # Calculate key metrics
    local total_sessions=$(jq '.sessions | length' "$sessions_file")
    local unique_users=$(jq '[.sessions[].user_id] | unique | length' "$sessions_file")
    local avg_session_duration=$(jq '[.sessions[].duration] | add / length' "$sessions_file" 2>/dev/null || echo "0")

    # Most popular actions
    local top_actions=$(jq -r '[.sessions[].action] | group_by(.) | map({action: .[0], count: length}) | sort_by(.count) | reverse | .[0:5]' "$sessions_file")

    # Most popular pages
    local top_pages=$(jq -r '[.sessions[].page] | group_by(.) | map({page: .[0], count: length}) | sort_by(.count) | reverse | .[0:5]' "$sessions_file")

    # Weekly trends
    local weekly_sessions=$(jq -r '[.sessions[].week] | group_by(.) | map({week: .[0], count: length}) | sort_by(.week)' "$sessions_file")

    # User engagement patterns
    local returning_users=$(jq '[.sessions[] | group_by(.user_id) | .[] | select(length > 1)] | length' "$sessions_file")
    local retention_rate=$(echo "scale=4; $returning_users / $unique_users" | bc 2>/dev/null || echo "0")

    # Generate insights
    local insights="[]"

    # High engagement insight
    if (( $(echo "$avg_session_duration > 300" | bc -l 2>/dev/null || echo "0") )); then
        insights=$(echo "$insights" | jq '. += [{"type": "positive", "message": "High user engagement detected (avg 5+ min sessions)", "confidence": 0.8}]')
    fi

    # Retention insight
    if (( $(echo "$retention_rate > 0.3" | bc -l 2>/dev/null || echo "0") )); then
        insights=$(echo "$insights" | jq '. += [{"type": "positive", "message": "Good user retention (30%+ returning users)", "confidence": 0.7}]')
    elif (( $(echo "$retention_rate < 0.1" | bc -l 2>/dev/null || echo "1") )); then
        insights=$(echo "$insights" | jq '. += [{"type": "warning", "message": "Low user retention detected - investigate user journey", "confidence": 0.9}]')
    fi

    # Growth trend insight
    local recent_week=$(echo "$weekly_sessions" | jq -r '.[-1].count // 0')
    local previous_week=$(echo "$weekly_sessions" | jq -r '.[-2].count // 0')

    if [[ "$recent_week" -gt "$previous_week" ]] && [[ "$previous_week" -gt 0 ]]; then
        local growth=$(echo "scale=2; ($recent_week - $previous_week) / $previous_week * 100" | bc)
        insights=$(echo "$insights" | jq ". += [{\"type\": \"positive\", \"message\": \"Weekly growth: +$growth%\", \"confidence\": 0.8}]")
    fi

    # Create analysis report
    cat > "$analysis_file" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "period": "$(date -d '30 days ago' +%Y-%m-%d) to $(date +%Y-%m-%d)",
  "metrics": {
    "total_sessions": $total_sessions,
    "unique_users": $unique_users,
    "avg_session_duration": $avg_session_duration,
    "retention_rate": $retention_rate,
    "returning_users": $returning_users
  },
  "top_actions": $top_actions,
  "top_pages": $top_pages,
  "weekly_trends": $weekly_sessions,
  "insights": $insights,
  "score": $(calculate_engagement_score "$total_sessions" "$avg_session_duration" "$retention_rate")
}
EOF

    log_success "Behavior analysis complete: $analysis_file"

    # Auto-generate alerts if needed
    check_behavior_alerts "$analysis_file"
}

calculate_engagement_score() {
    local sessions="$1"
    local duration="$2"
    local retention="$3"

    # Simple scoring algorithm (0-100)
    local session_score=$(echo "scale=2; ($sessions / 10) * 20" | bc | cut -d. -f1)
    [[ "$session_score" -gt 40 ]] && session_score=40

    local duration_score=$(echo "scale=2; ($duration / 60) * 30" | bc | cut -d. -f1)
    [[ "$duration_score" -gt 30 ]] && duration_score=30

    local retention_score=$(echo "scale=2; $retention * 30" | bc | cut -d. -f1)

    local total=$((session_score + duration_score + retention_score))
    [[ "$total" -gt 100 ]] && total=100

    echo "$total"
}

# ========================================
#  Product-Market Fit (PMF) Tracking
# ========================================

track_pmf_survey() {
    local user_id="$1"
    local disappointed_score="$2" # 1-5 scale (how disappointed if product disappeared)
    local recommendation_score="$3" # 0-10 NPS scale
    local primary_benefit="$4"
    local improvement_suggestion="$5"

    log_info "Recording PMF survey response from $user_id"

    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local survey_response=$(cat <<EOF
{
  "user_id": "$user_id",
  "timestamp": "$timestamp",
  "disappointed_score": $disappointed_score,
  "recommendation_score": $recommendation_score,
  "primary_benefit": "$primary_benefit",
  "improvement_suggestion": "$improvement_suggestion",
  "month": "$(date +%Y-%m)"
}
EOF
)

    # Add to surveys
    local updated=$(jq ".surveys += [$survey_response]" "$PMF_DIR/metrics.json")
    echo "$updated" > "$PMF_DIR/metrics.json"

    # Recalculate PMF score
    calculate_pmf_score

    log_success "PMF survey recorded and score updated"
}

calculate_pmf_score() {
    log_info "Calculating Product-Market Fit score..."

    local metrics_file="$PMF_DIR/metrics.json"
    local pmf_report="$PMF_DIR/pmf_score_$(date +%Y%m%d_%H%M%S).json"

    # Sean Ellis PMF Survey methodology
    local very_disappointed=$(jq '[.surveys[] | select(.disappointed_score >= 4)] | length' "$metrics_file")
    local total_responses=$(jq '.surveys | length' "$metrics_file")

    if [[ "$total_responses" -eq 0 ]]; then
        log_warning "No PMF survey data available"
        return 0
    fi

    local pmf_score=$(echo "scale=2; $very_disappointed / $total_responses * 100" | bc)

    # NPS calculation
    local promoters=$(jq '[.surveys[] | select(.recommendation_score >= 9)] | length' "$metrics_file")
    local detractors=$(jq '[.surveys[] | select(.recommendation_score <= 6)] | length' "$metrics_file")
    local nps=$(echo "scale=2; ($promoters - $detractors) / $total_responses * 100" | bc)

    # Top benefits analysis
    local benefits=$(jq -r '[.surveys[].primary_benefit] | group_by(.) | map({benefit: .[0], count: length}) | sort_by(.count) | reverse' "$metrics_file")

    # Monthly trend
    local monthly_scores=$(jq -r 'group_by(.month) | map({month: .[0].month, disappointed: ([.[] | select(.disappointed_score >= 4)] | length), total: length}) | map(. + {score: ((.disappointed / .total) * 100)})' "$metrics_file" <<< "$(jq '.surveys' "$metrics_file")")

    # PMF interpretation
    local pmf_status="Pre-PMF"
    local confidence="low"

    if (( $(echo "$pmf_score >= 40" | bc -l) )); then
        pmf_status="Strong PMF"
        confidence="high"
    elif (( $(echo "$pmf_score >= 20" | bc -l) )); then
        pmf_status="Weak PMF"
        confidence="medium"
    fi

    # Generate recommendations
    local recommendations="[]"

    if (( $(echo "$pmf_score < 20" | bc -l) )); then
        recommendations=$(echo "$recommendations" | jq '. += ["Focus on core value proposition", "Conduct more user interviews", "Consider pivot or feature changes"]')
    elif (( $(echo "$pmf_score < 40" | bc -l) )); then
        recommendations=$(echo "$recommendations" | jq '. += ["Optimize current features", "Expand successful use cases", "Improve onboarding"]')
    else
        recommendations=$(echo "$recommendations" | jq '. += ["Scale marketing efforts", "Expand to adjacent markets", "Build advanced features"]')
    fi

    # Create PMF report
    cat > "$pmf_report" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "pmf_score": $pmf_score,
  "nps_score": $nps,
  "status": "$pmf_status",
  "confidence": "$confidence",
  "metrics": {
    "total_responses": $total_responses,
    "very_disappointed": $very_disappointed,
    "promoters": $promoters,
    "detractors": $detractors
  },
  "top_benefits": $benefits,
  "monthly_trend": $monthly_scores,
  "recommendations": $recommendations
}
EOF

    # Update main metrics file
    local updated=$(jq ".scores += [{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"pmf_score\": $pmf_score, \"nps_score\": $nps, \"status\": \"$pmf_status\"}]" "$PMF_DIR/metrics.json")
    echo "$updated" > "$PMF_DIR/metrics.json"

    log_success "PMF score calculated: ${pmf_score}% ($pmf_status)"
    log_metric "NPS Score: $nps"
    log_metric "Total Responses: $total_responses"

    # Check for alerts
    check_pmf_alerts "$pmf_score"

    echo "$pmf_report"
}

# ========================================
#  Competitor Monitoring System
# ========================================

add_competitor() {
    local competitor_name="$1"
    local website="${2:-}"
    local social_handle="${3:-}"
    local monitoring_focus="${4:-general}" # pricing, features, marketing, general

    log_info "Adding competitor: $competitor_name"

    local competitor_entry=$(cat <<EOF
{
  "name": "$competitor_name",
  "website": "$website",
  "social_handle": "$social_handle",
  "monitoring_focus": "$monitoring_focus",
  "added": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "active"
}
EOF
)

    # Add to competitors
    local updated=$(jq ".competitors += [$competitor_entry]" "$COMPETITOR_DIR/tracking.json")
    echo "$updated" > "$COMPETITOR_DIR/tracking.json"

    log_success "Competitor $competitor_name added to monitoring"
}

track_competitor_update() {
    local competitor_name="$1"
    local update_type="$2" # pricing, feature, marketing, funding, team
    local description="$3"
    local impact_level="${4:-medium}" # low, medium, high, critical
    local source="${5:-manual}"

    log_info "Recording competitor update: $competitor_name"

    local update_entry=$(cat <<EOF
{
  "competitor": "$competitor_name",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "type": "$update_type",
  "description": "$description",
  "impact_level": "$impact_level",
  "source": "$source",
  "month": "$(date +%Y-%m)",
  "week": "$(date +%Y-W%U)"
}
EOF
)

    # Add to updates
    local updated=$(jq ".updates += [$update_entry]" "$COMPETITOR_DIR/tracking.json")
    echo "$updated" > "$COMPETITOR_DIR/tracking.json"

    log_success "Competitor update recorded"

    # Generate alert for high impact updates
    if [[ "$impact_level" == "high" ]] || [[ "$impact_level" == "critical" ]]; then
        create_alert "competitor_update" "$competitor_name: $description" "$impact_level"
    fi
}

analyze_competitor_landscape() {
    log_info "Analyzing competitive landscape..."

    local tracking_file="$COMPETITOR_DIR/tracking.json"
    local analysis_file="$COMPETITOR_DIR/landscape_analysis_$(date +%Y%m%d_%H%M%S).json"

    # Basic metrics
    local total_competitors=$(jq '.competitors | length' "$tracking_file")
    local total_updates=$(jq '.updates | length' "$tracking_file")
    local seven_days_ago=$(date -v-7d -u +%Y-%m-%dT%H:%M:%SZ)
    local recent_updates=$(jq "[.updates[] | select(.timestamp >= \"$seven_days_ago\")] | length" "$tracking_file")

    # Update types analysis
    local update_types=$(jq -r '[.updates[].type] | group_by(.) | map({type: .[0], count: length}) | sort_by(.count) | reverse' "$tracking_file")

    # Most active competitors
    local active_competitors=$(jq -r '[.updates[].competitor] | group_by(.) | map({competitor: .[0], updates: length}) | sort_by(.updates) | reverse' "$tracking_file")

    # Impact level distribution
    local high_impact_updates=$(jq '[.updates[] | select(.impact_level == "high" or .impact_level == "critical")] | length' "$tracking_file")

    # Weekly activity trend
    local weekly_activity=$(jq -r '[.updates[].week] | group_by(.) | map({week: .[0], count: length}) | sort_by(.week)' "$tracking_file")

    # Generate competitive insights
    local insights="[]"

    # High activity insight
    if [[ "$recent_updates" -gt 5 ]]; then
        insights=$(echo "$insights" | jq ". += [{\"type\": \"warning\", \"message\": \"High competitive activity detected ($recent_updates updates this week)\", \"actionable\": true}]")
    fi

    # Feature gap insight
    local feature_updates=$(jq '[.updates[] | select(.type == "feature")] | length' "$tracking_file")
    if [[ "$feature_updates" -gt 3 ]]; then
        insights=$(echo "$insights" | jq '. += [{"type": "opportunity", "message": "Multiple competitors releasing new features - analyze for gaps", "actionable": true}]')
    fi

    # Pricing pressure insight
    local pricing_updates=$(jq '[.updates[] | select(.type == "pricing")] | length' "$tracking_file")
    if [[ "$pricing_updates" -gt 1 ]]; then
        insights=$(echo "$insights" | jq '. += [{"type": "alert", "message": "Pricing changes in market - review your pricing strategy", "actionable": true}]')
    fi

    # Create analysis report
    cat > "$analysis_file" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "period": "Last 30 days",
  "metrics": {
    "total_competitors": $total_competitors,
    "total_updates": $total_updates,
    "recent_updates": $recent_updates,
    "high_impact_updates": $high_impact_updates
  },
  "analysis": {
    "update_types": $update_types,
    "most_active": $active_competitors,
    "weekly_activity": $weekly_activity
  },
  "insights": $insights,
  "threat_level": "$(calculate_competitive_threat "$recent_updates" "$high_impact_updates")"
}
EOF

    log_success "Competitive analysis complete: $analysis_file"

    # Check for competitive alerts
    check_competitor_alerts "$analysis_file"

    echo "$analysis_file"
}

calculate_competitive_threat() {
    local recent_updates="$1"
    local high_impact="$2"

    local threat_score=$(($recent_updates + $high_impact * 2))

    if [[ "$threat_score" -ge 10 ]]; then
        echo "HIGH"
    elif [[ "$threat_score" -ge 5 ]]; then
        echo "MEDIUM"
    else
        echo "LOW"
    fi
}

# ========================================
#  Automated Insights Generation
# ========================================

generate_daily_insights() {
    log_info "Generating daily automated insights..."

    local insights_file="$INSIGHTS_DIR/daily_$(date +%Y%m%d).json"
    local combined_insights="[]"

    # Collect recent behavior data
    local yesterday=$(date -v-1d -u +%Y-%m-%dT%H:%M:%SZ)
    local recent_sessions=$(jq '[.sessions[] | select(.timestamp >= "'"$yesterday"'")] | length' "$BEHAVIOR_DIR/user_sessions.json")

    # Collect latest PMF data
    local latest_pmf_score=$(jq -r '.scores[-1].pmf_score // 0' "$PMF_DIR/metrics.json")

    # Collect competitor activity
    local recent_competitor_updates=$(jq '[.updates[] | select(.timestamp >= "'"$yesterday"'")] | length' "$COMPETITOR_DIR/tracking.json")

    # Generate insights based on data
    if [[ "$recent_sessions" -gt 10 ]]; then
        combined_insights=$(echo "$combined_insights" | jq '. += [{"category": "growth", "insight": "High user activity today ('"$recent_sessions"' sessions)", "priority": "positive", "auto_generated": true}]')
    elif [[ "$recent_sessions" -eq 0 ]]; then
        combined_insights=$(echo "$combined_insights" | jq '. += [{"category": "warning", "insight": "No user activity detected today", "priority": "high", "auto_generated": true}]')
    fi

    if (( $(echo "$latest_pmf_score > 0" | bc -l 2>/dev/null || echo "0") )); then
        if (( $(echo "$latest_pmf_score >= 40" | bc -l) )); then
            combined_insights=$(echo "$combined_insights" | jq '. += [{"category": "pmf", "insight": "Strong PMF maintained ('"$latest_pmf_score"'%)", "priority": "positive", "auto_generated": true}]')
        elif (( $(echo "$latest_pmf_score < 20" | bc -l) )); then
            combined_insights=$(echo "$combined_insights" | jq '. += [{"category": "pmf", "insight": "PMF below threshold - consider product changes", "priority": "high", "auto_generated": true}]')
        fi
    fi

    if [[ "$recent_competitor_updates" -gt 0 ]]; then
        combined_insights=$(echo "$combined_insights" | jq '. += [{"category": "competitive", "insight": "Competitor activity detected ('"$recent_competitor_updates"' updates)", "priority": "medium", "auto_generated": true}]')
    fi

    # Create daily insights report
    cat > "$insights_file" <<EOF
{
  "date": "$(date +%Y-%m-%d)",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "metrics_summary": {
    "sessions_24h": $(echo "${recent_sessions:-0}"),
    "latest_pmf_score": $(echo "${latest_pmf_score:-0}"),
    "competitor_updates_24h": $(echo "${recent_competitor_updates:-0}")
  },
  "insights": $combined_insights,
  "auto_generated": true
}
EOF

    # Add to main insights
    local updated=$(jq ".insights += [$(cat "$insights_file")]" "$INSIGHTS_DIR/analysis.json")
    echo "$updated" > "$INSIGHTS_DIR/analysis.json"

    log_success "Daily insights generated: $insights_file"

    # Create alerts for high priority insights
    echo "$combined_insights" | jq -r '.[] | select(.priority == "high") | .insight' | while read -r insight; do
        create_alert "daily_insight" "$insight" "medium"
    done
}

# ========================================
#  Alert System
# ========================================

create_alert() {
    local alert_type="$1"
    local message="$2"
    local severity="${3:-medium}"
    local source="${4:-system}"

    local alert_entry=$(cat <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "type": "$alert_type",
  "message": "$message",
  "severity": "$severity",
  "source": "$source",
  "status": "active"
}
EOF
)

    # Add to alerts
    local updated=$(jq ".alerts += [$alert_entry]" "$ALERTS_DIR/notifications.json")
    echo "$updated" > "$ALERTS_DIR/notifications.json"

    log_warning "ALERT: $message"
}

check_behavior_alerts() {
    local analysis_file="$1"

    local engagement_score=$(jq -r '.score' "$analysis_file")
    local retention_rate=$(jq -r '.metrics.retention_rate' "$analysis_file")

    # Check thresholds from config
    local engagement_threshold=$(jq -r '.thresholds.engagement_drop_alert // 0.20' "$CI_DIR/config.json")
    local churn_threshold=$(jq -r '.thresholds.churn_rate_alert // 0.15' "$CI_DIR/config.json")

    if [[ "$engagement_score" -lt 30 ]]; then
        create_alert "low_engagement" "User engagement score dropped to $engagement_score" "high"
    fi

    if (( $(echo "$retention_rate < $churn_threshold" | bc -l) )); then
        create_alert "high_churn" "User retention rate below threshold: $retention_rate" "high"
    fi
}

check_pmf_alerts() {
    local pmf_score="$1"
    local alert_threshold=$(jq -r '.thresholds.pmf_score_alert // 40' "$CI_DIR/config.json")

    if (( $(echo "$pmf_score < $alert_threshold" | bc -l) )); then
        create_alert "low_pmf" "PMF score below target: ${pmf_score}%" "high"
    fi
}

check_competitor_alerts() {
    local analysis_file="$1"
    local recent_updates=$(jq -r '.metrics.recent_updates' "$analysis_file")
    local threat_level=$(jq -r '.threat_level' "$analysis_file")

    if [[ "$threat_level" == "HIGH" ]]; then
        create_alert "high_competitive_threat" "High competitive activity detected" "high"
    fi

    if [[ "$recent_updates" -gt 5 ]]; then
        create_alert "competitor_surge" "Unusual competitor activity: $recent_updates updates this week" "medium"
    fi
}

# ========================================
#  Dashboard & Reporting
# ========================================

show_customer_intelligence_dashboard() {
    clear
    cat <<EOF
╔══════════════════════════════════════════════════════════════╗
║                CUSTOMER INTELLIGENCE DASHBOARD               ║
╚══════════════════════════════════════════════════════════════╝

📊 OVERVIEW (Last 7 Days)
EOF

    # User behavior metrics
    local seven_days_ago=$(date -v-7d -u +%Y-%m-%dT%H:%M:%SZ)
    local recent_sessions=$(jq '[.sessions[] | select(.timestamp >= "'"$seven_days_ago"'")] | length' "$BEHAVIOR_DIR/user_sessions.json" 2>/dev/null || echo "0")
    local unique_users=$(jq '[.sessions[] | select(.timestamp >= "'"$seven_days_ago"'")].user_id | unique | length' "$BEHAVIOR_DIR/user_sessions.json" 2>/dev/null || echo "0")
    local avg_duration=$(jq '[.sessions[] | select(.timestamp >= "'"$seven_days_ago"'")].duration | add / length' "$BEHAVIOR_DIR/user_sessions.json" 2>/dev/null | cut -d. -f1 || echo "0")

    printf "   Sessions: %s  |  Unique Users: %s  |  Avg Duration: %ss\n" "$recent_sessions" "$unique_users" "$avg_duration"

    # PMF metrics
    echo
    echo "🎯 PRODUCT-MARKET FIT"
    local latest_pmf=$(jq -r '.scores[-1].pmf_score // "N/A"' "$PMF_DIR/metrics.json" 2>/dev/null)
    local pmf_status=$(jq -r '.scores[-1].status // "Unknown"' "$PMF_DIR/metrics.json" 2>/dev/null)
    local total_surveys=$(jq '.surveys | length' "$PMF_DIR/metrics.json" 2>/dev/null || echo "0")

    printf "   PMF Score: %s%%  |  Status: %s  |  Surveys: %s\n" "$latest_pmf" "$pmf_status" "$total_surveys"

    # Competitor metrics
    echo
    echo "🏁 COMPETITIVE LANDSCAPE"
    local monitored_competitors=$(jq '.competitors | length' "$COMPETITOR_DIR/tracking.json" 2>/dev/null || echo "0")
    local recent_updates=$(jq '[.updates[] | select(.timestamp >= "'"$seven_days_ago"'")] | length' "$COMPETITOR_DIR/tracking.json" 2>/dev/null || echo "0")
    local high_impact=$(jq '[.updates[] | select(.timestamp >= "'"$seven_days_ago"'" and (.impact_level == "high" or .impact_level == "critical"))] | length' "$COMPETITOR_DIR/tracking.json" 2>/dev/null || echo "0")

    printf "   Monitored: %s  |  Recent Updates: %s  |  High Impact: %s\n" "$monitored_competitors" "$recent_updates" "$high_impact"

    # Recent alerts
    echo
    echo "🚨 ACTIVE ALERTS"
    local active_alerts=$(jq '[.alerts[] | select(.status == "active")] | length' "$ALERTS_DIR/notifications.json" 2>/dev/null || echo "0")
    if [[ "$active_alerts" -gt 0 ]]; then
        jq -r '.alerts[] | select(.status == "active") | "   - [\(.severity | ascii_upcase)] \(.message)"' "$ALERTS_DIR/notifications.json" 2>/dev/null | head -5
    else
        echo "   No active alerts"
    fi

    # Quick insights
    echo
    echo "💡 RECENT INSIGHTS"
    jq -r '.insights[-3:] | reverse | .[] | select(.auto_generated == true) | "   - \(.category | ascii_upcase): \(.insight)"' "$INSIGHTS_DIR/analysis.json" 2>/dev/null | head -3 || echo "   No recent insights"

    echo
    echo "⚡ QUICK ACTIONS"
    echo "   1. Track user behavior (track-behavior)"
    echo "   2. Record PMF survey (pmf-survey)"
    echo "   3. Add competitor update (competitor-update)"
    echo "   4. Generate insights (daily-insights)"
    echo "   5. View detailed analytics (ci-report)"
    echo
}

generate_intelligence_report() {
    local report_type="${1:-weekly}"

    log_info "Generating $report_type intelligence report..."

    local report_file="$INSIGHTS_DIR/${report_type}_report_$(date +%Y%m%d).html"

    cat > "$report_file" <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Customer Intelligence Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
        .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 10px; text-align: center; }
        .metric-value { font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }
        .metric-label { opacity: 0.9; font-size: 0.9em; }
        .insight { background: #e8f5e8; border-left: 4px solid #27ae60; padding: 15px; margin: 15px 0; border-radius: 4px; }
        .warning { background: #fef5e7; border-left: 4px solid #f39c12; }
        .alert { background: #fdeaea; border-left: 4px solid #e74c3c; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }
        th { background: #f8f9fa; font-weight: 600; }
        .status-good { color: #27ae60; font-weight: bold; }
        .status-warning { color: #f39c12; font-weight: bold; }
        .status-critical { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Customer Intelligence Report</h1>
EOF

    # Add current date and period
    echo "<p><strong>Generated:</strong> $(date '+%Y-%m-%d %H:%M')</p>" >> "$report_file"
    echo "<p><strong>Period:</strong> $(date -d '7 days ago' '+%Y-%m-%d') to $(date '+%Y-%m-%d')</p>" >> "$report_file"

    # Add metrics cards
    echo "<div class='metric-grid'>" >> "$report_file"

    # User behavior metrics
    local total_sessions=$(jq '.sessions | length' "$BEHAVIOR_DIR/user_sessions.json" 2>/dev/null || echo "0")
    local unique_users=$(jq '[.sessions[].user_id] | unique | length' "$BEHAVIOR_DIR/user_sessions.json" 2>/dev/null || echo "0")
    local latest_pmf=$(jq -r '.scores[-1].pmf_score // 0' "$PMF_DIR/metrics.json" 2>/dev/null)
    local monitored_competitors=$(jq '.competitors | length' "$COMPETITOR_DIR/tracking.json" 2>/dev/null || echo "0")

    cat >> "$report_file" <<EOF
<div class="metric-card">
    <div class="metric-value">$total_sessions</div>
    <div class="metric-label">Total Sessions</div>
</div>
<div class="metric-card">
    <div class="metric-value">$unique_users</div>
    <div class="metric-label">Unique Users</div>
</div>
<div class="metric-card">
    <div class="metric-value">${latest_pmf}%</div>
    <div class="metric-label">PMF Score</div>
</div>
<div class="metric-card">
    <div class="metric-value">$monitored_competitors</div>
    <div class="metric-label">Competitors</div>
</div>
EOF

    echo "</div>" >> "$report_file"

    # Add insights section
    echo "<h2>Key Insights</h2>" >> "$report_file"

    # Recent insights from analysis
    jq -r '.insights[-5:] | reverse | .[] | "<div class=\"insight\"><strong>" + (.category | ascii_upcase) + ":</strong> " + .insight + "</div>"' "$INSIGHTS_DIR/analysis.json" 2>/dev/null >> "$report_file" || echo "<p>No recent insights available.</p>" >> "$report_file"

    # Add alerts section
    echo "<h2>Active Alerts</h2>" >> "$report_file"

    local active_alerts=$(jq '[.alerts[] | select(.status == "active")] | length' "$ALERTS_DIR/notifications.json" 2>/dev/null || echo "0")

    if [[ "$active_alerts" -gt 0 ]]; then
        echo "<table><tr><th>Severity</th><th>Message</th><th>Time</th></tr>" >> "$report_file"
        jq -r '.alerts[] | select(.status == "active") | "<tr><td class=\"status-" + (if .severity == "high" then "critical" elif .severity == "medium" then "warning" else "good" end) + "\">" + (.severity | ascii_upcase) + "</td><td>" + .message + "</td><td>" + (.timestamp | split("T")[0]) + "</td></tr>"' "$ALERTS_DIR/notifications.json" 2>/dev/null >> "$report_file"
        echo "</table>" >> "$report_file"
    else
        echo "<p>No active alerts - all systems healthy!</p>" >> "$report_file"
    fi

    # Close HTML
    echo "</div></body></html>" >> "$report_file"

    log_success "Intelligence report generated: $report_file"

    # Open in browser if available
    if command -v open &> /dev/null; then
        open "$report_file"
    fi
}

# ========================================
#  Automation & Scheduling
# ========================================

setup_automation() {
    log_info "Setting up automated customer intelligence tasks..."

    local automation_config="$AUTOMATION_DIR/schedule.json"

    cat > "$automation_config" <<EOF
{
  "daily_tasks": [
    {
      "name": "generate_insights",
      "command": "$0 daily-insights",
      "time": "09:00",
      "enabled": true
    },
    {
      "name": "behavior_analysis",
      "command": "$0 analyze-behavior",
      "time": "18:00",
      "enabled": true
    }
  ],
  "weekly_tasks": [
    {
      "name": "pmf_calculation",
      "command": "$0 calculate-pmf",
      "day": "monday",
      "time": "10:00",
      "enabled": true
    },
    {
      "name": "competitor_analysis",
      "command": "$0 analyze-competitors",
      "day": "wednesday",
      "time": "14:00",
      "enabled": true
    },
    {
      "name": "weekly_report",
      "command": "$0 report weekly",
      "day": "friday",
      "time": "16:00",
      "enabled": true
    }
  ]
}
EOF

    log_success "Automation schedule configured: $automation_config"
    log_info "To enable automation, add these to your crontab:"
    echo
    echo "# Customer Intelligence Automation"
    echo "0 9 * * * $0 daily-insights >/dev/null 2>&1"
    echo "0 18 * * * $0 analyze-behavior >/dev/null 2>&1"
    echo "0 10 * * 1 $0 calculate-pmf >/dev/null 2>&1"
    echo "0 14 * * 3 $0 analyze-competitors >/dev/null 2>&1"
    echo "0 16 * * 5 $0 report weekly >/dev/null 2>&1"
    echo
}

# ========================================
#  Main Command Handler
# ========================================

show_usage() {
    cat <<EOF
🧠 Customer Intelligence System for Solopreneurs

USAGE:
    $0 [COMMAND] [OPTIONS]

CORE COMMANDS:
    init                              Initialize customer intelligence system
    dashboard                         Show CI dashboard
    report [weekly|monthly]           Generate intelligence report

USER BEHAVIOR:
    track-behavior <user> <action> [page] [duration] [metadata]
                                     Track user behavior event
    analyze-behavior                  Analyze behavior patterns
    behavior-score                    Calculate engagement score

PMF TRACKING:
    pmf-survey <user> <disappointed> <nps> <benefit> <improvement>
                                     Record PMF survey response
    calculate-pmf                     Calculate PMF score
    pmf-status                        Show current PMF status

COMPETITOR MONITORING:
    add-competitor <name> [website] [social] [focus]
                                     Add competitor to monitoring
    competitor-update <name> <type> <description> [impact] [source]
                                     Track competitor update
    analyze-competitors              Analyze competitive landscape

AUTOMATION:
    daily-insights                   Generate daily automated insights
    setup-automation                 Configure automated tasks
    alerts                          Show active alerts

EXAMPLES:
    # Track user behavior
    $0 track-behavior user123 signup pricing_page 180

    # Record PMF survey
    $0 pmf-survey user456 4 8 "easy to use" "add mobile app"

    # Add competitor
    $0 add-competitor "CompetitorX" "https://competitor.com" "@competitor" features

    # Track competitor update
    $0 competitor-update "CompetitorX" pricing "Reduced prices by 20%" high

EOF
}

# Main execution
main() {
    local cmd="${1:-dashboard}"

    case "$cmd" in
        init)
            init_customer_intelligence
            ;;
        dashboard)
            show_customer_intelligence_dashboard
            ;;
        track-behavior)
            shift
            track_user_behavior "$@"
            ;;
        analyze-behavior)
            analyze_user_behavior_patterns
            ;;
        behavior-score)
            local analysis_file=$(find "$BEHAVIOR_DIR" -name "analysis_*.json" -type f -exec ls -t {} + | head -1)
            if [[ -n "$analysis_file" ]]; then
                jq -r '.score' "$analysis_file"
            else
                echo "No behavior analysis available. Run 'analyze-behavior' first."
            fi
            ;;
        pmf-survey)
            shift
            track_pmf_survey "$@"
            ;;
        calculate-pmf)
            calculate_pmf_score
            ;;
        pmf-status)
            local latest=$(jq -r '.scores[-1] | "PMF Score: \(.pmf_score)% | Status: \(.status) | NPS: \(.nps_score)"' "$PMF_DIR/metrics.json" 2>/dev/null || echo "No PMF data available")
            echo "$latest"
            ;;
        add-competitor)
            shift
            add_competitor "$@"
            ;;
        competitor-update)
            shift
            track_competitor_update "$@"
            ;;
        analyze-competitors)
            analyze_competitor_landscape
            ;;
        daily-insights)
            generate_daily_insights
            ;;
        setup-automation)
            setup_automation
            ;;
        alerts)
            jq -r '.alerts[] | select(.status == "active") | "[\(.severity | ascii_upcase)] \(.message) (\(.timestamp | split("T")[0]))"' "$ALERTS_DIR/notifications.json" 2>/dev/null || echo "No active alerts"
            ;;
        report)
            shift
            generate_intelligence_report "$@"
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Initialize on first run
[[ ! -d "$CI_DIR" ]] && init_customer_intelligence

# Run main
main "$@"
