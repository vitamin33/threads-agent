#!/usr/bin/env bash
# ========================================
#  Solopreneur Business Intelligence System
# ========================================
# ROI calculator, market timing analyzer, and revenue predictor
# optimized for solo developer decision-making

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BI_DIR="$PROJECT_ROOT/.business-intelligence"
MARKET_DATA_DIR="$BI_DIR/market"
REVENUE_DATA_DIR="$BI_DIR/revenue"
VALIDATION_DIR="$BI_DIR/validation"
DECISIONS_DIR="$BI_DIR/decisions"
REPORTS_DIR="$BI_DIR/reports"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Initialize system
init_business_intelligence() {
    mkdir -p "$MARKET_DATA_DIR" "$REVENUE_DATA_DIR" "$VALIDATION_DIR" "$DECISIONS_DIR" "$REPORTS_DIR"

    # Initialize data files if they don't exist
    [[ ! -f "$BI_DIR/config.json" ]] && cat > "$BI_DIR/config.json" <<EOF
{
  "business": {
    "name": "Threads Agent Stack",
    "type": "saas",
    "stage": "mvp",
    "launched": false
  },
  "financials": {
    "mrr_target": 20000,
    "cost_per_follow_target": 0.01,
    "engagement_rate_target": 0.06,
    "runway_months": 6,
    "burn_rate": 0
  },
  "market": {
    "target_audience": "content_creators",
    "market_size": 1000000,
    "competition_level": "medium"
  }
}
EOF

    [[ ! -f "$REVENUE_DATA_DIR/projections.json" ]] && echo '{"scenarios": []}' > "$REVENUE_DATA_DIR/projections.json"
    [[ ! -f "$VALIDATION_DIR/customers.json" ]] && echo '{"interviews": [], "feedback": []}' > "$VALIDATION_DIR/customers.json"
    [[ ! -f "$DECISIONS_DIR/history.json" ]] && echo '{"decisions": []}' > "$DECISIONS_DIR/history.json"

    log_info "Business intelligence system initialized"
}

# Logging functions
log_info() { echo -e "${BLUE}[BI]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_metric() { echo -e "${PURPLE}[METRIC]${NC} $1"; }
log_money() { echo -e "${CYAN}[\$]${NC} $1"; }

# ========================================
#  ROI Calculator
# ========================================

calculate_roi() {
    local feature_name="$1"
    local dev_hours="${2:-40}"
    local hourly_rate="${3:-150}"
    local expected_revenue="${4:-0}"
    local customer_impact="${5:-medium}"

    log_info "Calculating ROI for: $feature_name"

    # Calculate costs
    local dev_cost=$((dev_hours * hourly_rate))
    local opportunity_cost=$((dev_hours * hourly_rate / 2)) # 50% opportunity cost
    local total_cost=$((dev_cost + opportunity_cost))

    # Calculate expected returns based on impact
    local revenue_multiplier=1
    case "$customer_impact" in
        "critical") revenue_multiplier=3 ;;
        "high") revenue_multiplier=2 ;;
        "medium") revenue_multiplier=1.5 ;;
        "low") revenue_multiplier=1.2 ;;
        *) revenue_multiplier=1 ;;
    esac

    # If no expected revenue provided, estimate based on MRR target
    if [[ "$expected_revenue" -eq 0 ]]; then
        local mrr_target=$(jq -r '.financials.mrr_target // 20000' "$BI_DIR/config.json")
        expected_revenue=$((mrr_target / 10)) # Assume feature contributes 10% to MRR
    fi

    local adjusted_revenue=$(echo "$expected_revenue * $revenue_multiplier" | bc)
    local monthly_roi=$(echo "scale=2; ($adjusted_revenue - $total_cost / 3) / $total_cost * 100" | bc)
    local annual_roi=$(echo "scale=2; ($adjusted_revenue * 12 - $total_cost) / $total_cost * 100" | bc)

    # Risk assessment
    local risk_factor="medium"
    if [[ "$dev_hours" -gt 80 ]]; then
        risk_factor="high"
    elif [[ "$dev_hours" -lt 20 ]]; then
        risk_factor="low"
    fi

    # Generate ROI report
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local safe_name=$(echo "$feature_name" | tr ' /' '__')
    local roi_report="$REPORTS_DIR/roi_${safe_name}_${timestamp}.json"

    cat > "$roi_report" <<EOF
{
  "feature": "$feature_name",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "investment": {
    "dev_hours": $dev_hours,
    "hourly_rate": $hourly_rate,
    "dev_cost": $dev_cost,
    "opportunity_cost": $opportunity_cost,
    "total_cost": $total_cost
  },
  "returns": {
    "expected_monthly": $expected_revenue,
    "adjusted_monthly": $adjusted_revenue,
    "customer_impact": "$customer_impact",
    "revenue_multiplier": $revenue_multiplier
  },
  "roi": {
    "monthly_percentage": $monthly_roi,
    "annual_percentage": $annual_roi,
    "payback_months": $(echo "scale=1; $total_cost / $adjusted_revenue" | bc),
    "risk_level": "$risk_factor"
  },
  "recommendation": "$(get_roi_recommendation "$monthly_roi" "$risk_factor")"
}
EOF

    # Display results
    echo
    log_money "=== ROI Analysis: $feature_name ==="
    log_metric "Development Cost: \$$dev_cost"
    log_metric "Opportunity Cost: \$$opportunity_cost"
    log_metric "Total Investment: \$$total_cost"
    echo
    log_metric "Expected Monthly Revenue: \$$adjusted_revenue"
    log_metric "Monthly ROI: ${monthly_roi}%"
    log_metric "Annual ROI: ${annual_roi}%"
    log_metric "Payback Period: $(echo "scale=1; $total_cost / $adjusted_revenue" | bc) months"
    log_metric "Risk Level: $risk_factor"
    echo
    log_success "ROI report saved: $roi_report"

    # Update decision history
    update_decision_history "roi_analysis" "$feature_name" "$roi_report"
}

get_roi_recommendation() {
    local roi="$1"
    local risk="$2"

    if (( $(echo "$roi > 50" | bc -l) )); then
        echo "STRONGLY RECOMMENDED - High ROI with acceptable risk"
    elif (( $(echo "$roi > 20" | bc -l) )); then
        if [[ "$risk" == "low" ]]; then
            echo "RECOMMENDED - Good ROI with low risk"
        else
            echo "PROCEED WITH CAUTION - Good ROI but higher risk"
        fi
    elif (( $(echo "$roi > 0" | bc -l) )); then
        echo "MARGINAL - Consider alternatives or scope reduction"
    else
        echo "NOT RECOMMENDED - Negative ROI expected"
    fi
}

# ========================================
#  Market Timing Analyzer
# ========================================

analyze_market_timing() {
    local feature_name="$1"
    local market_trend="${2:-stable}"
    local competition_moves="${3:-none}"
    local seasonal_factor="${4:-neutral}"

    log_info "Analyzing market timing for: $feature_name"

    # Calculate timing score (0-100)
    local timing_score=50

    # Market trend impact
    case "$market_trend" in
        "growing") timing_score=$((timing_score + 20)) ;;
        "stable") timing_score=$((timing_score + 0)) ;;
        "declining") timing_score=$((timing_score - 20)) ;;
    esac

    # Competition analysis
    case "$competition_moves" in
        "none") timing_score=$((timing_score + 10)) ;;
        "similar") timing_score=$((timing_score - 10)) ;;
        "aggressive") timing_score=$((timing_score - 20)) ;;
    esac

    # Seasonal factors
    case "$seasonal_factor" in
        "peak") timing_score=$((timing_score + 15)) ;;
        "neutral") timing_score=$((timing_score + 0)) ;;
        "low") timing_score=$((timing_score - 15)) ;;
    esac

    # Current date analysis
    local month=$(date +%m)
    local quarter=$((($month - 1) / 3 + 1))

    # Tech launch patterns (avoid August and December)
    if [[ "$month" == "08" ]] || [[ "$month" == "12" ]]; then
        timing_score=$((timing_score - 10))
        local timing_note="Off-peak launch month detected"
    elif [[ "$month" == "09" ]] || [[ "$month" == "01" ]] || [[ "$month" == "03" ]]; then
        timing_score=$((timing_score + 10))
        local timing_note="Peak launch month detected"
    else
        local timing_note="Standard launch month"
    fi

    # Generate market timing report
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local safe_name=$(echo "$feature_name" | tr ' /' '__')
    local market_report="$MARKET_DATA_DIR/timing_${safe_name}_${timestamp}.json"

    cat > "$market_report" <<EOF
{
  "feature": "$feature_name",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "market_conditions": {
    "trend": "$market_trend",
    "competition": "$competition_moves",
    "seasonal": "$seasonal_factor",
    "current_quarter": "Q$quarter",
    "launch_month_quality": "$timing_note"
  },
  "timing_score": $timing_score,
  "recommendation": "$(get_timing_recommendation "$timing_score")",
  "optimal_launch_window": "$(calculate_launch_window "$timing_score")"
}
EOF

    # Display results
    echo
    log_metric "=== Market Timing Analysis: $feature_name ==="
    log_metric "Market Trend: $market_trend"
    log_metric "Competition Activity: $competition_moves"
    log_metric "Seasonal Factor: $seasonal_factor"
    log_metric "Timing Score: $timing_score/100"
    log_metric "Launch Window: $(calculate_launch_window "$timing_score")"
    echo
    log_success "Market analysis saved: $market_report"

    # Update decision history
    update_decision_history "market_timing" "$feature_name" "$market_report"
}

get_timing_recommendation() {
    local score="$1"

    if [[ "$score" -ge 70 ]]; then
        echo "EXCELLENT TIMING - Launch as soon as ready"
    elif [[ "$score" -ge 50 ]]; then
        echo "GOOD TIMING - Proceed with launch planning"
    elif [[ "$score" -ge 30 ]]; then
        echo "SUBOPTIMAL - Consider waiting or accelerating development"
    else
        echo "POOR TIMING - Strongly consider delaying"
    fi
}

calculate_launch_window() {
    local score="$1"

    if [[ "$score" -ge 70 ]]; then
        echo "Next 2-4 weeks"
    elif [[ "$score" -ge 50 ]]; then
        echo "Next 4-8 weeks"
    else
        echo "8+ weeks (reassess market conditions)"
    fi
}

# ========================================
#  Revenue Impact Predictor
# ========================================

predict_revenue_impact() {
    local feature_name="$1"
    local user_acquisition_boost="${2:-10}" # % increase in user acquisition
    local retention_boost="${3:-5}" # % increase in retention
    local price_elasticity="${4:-medium}" # low/medium/high
    local implementation_time="${5:-4}" # weeks

    log_info "Predicting revenue impact for: $feature_name"

    # Load current business metrics
    local mrr_target=$(jq -r '.financials.mrr_target // 20000' "$BI_DIR/config.json")
    local cost_per_follow=$(jq -r '.financials.cost_per_follow_target // 0.01' "$BI_DIR/config.json")
    local engagement_rate=$(jq -r '.financials.engagement_rate_target // 0.06' "$BI_DIR/config.json")

    # Base calculations
    local current_mrr=0 # Starting from 0 for MVP
    local avg_revenue_per_user=10 # $10/month subscription
    local current_users=$((current_mrr / avg_revenue_per_user))

    # Calculate growth impact
    local new_users_monthly=$((1000 * user_acquisition_boost / 100))
    local churn_reduction=$(echo "scale=4; $retention_boost / 100" | bc)

    # Price elasticity impact
    local price_multiplier=1
    case "$price_elasticity" in
        "low") price_multiplier="1.1" ;;
        "medium") price_multiplier="1.0" ;;
        "high") price_multiplier="0.9" ;;
    esac

    # Project MRR growth over 12 months
    local projections="["
    local month_mrr="$current_mrr"
    local total_users="$current_users"

    for month in {1..12}; do
        # Add new users
        total_users=$((total_users + new_users_monthly))

        # Apply retention improvement
        local retained_users=$(echo "scale=0; $total_users * (1 - 0.05 + $churn_reduction)" | bc)
        total_users=$(echo "$retained_users" | cut -d. -f1)  # Convert to integer

        # Calculate MRR
        month_mrr=$(echo "scale=2; $total_users * $avg_revenue_per_user * $price_multiplier" | bc)

        # Add to projections
        [[ "$month" -gt 1 ]] && projections+=","
        projections+="{\"month\":$month,\"users\":$total_users,\"mrr\":$month_mrr}"
    done
    projections+="]"

    # Calculate key metrics
    local year_end_mrr=$(echo "$projections" | jq -r '.[-1].mrr')
    local total_revenue=$(echo "$projections" | jq '[.[].mrr] | add')
    local growth_rate=$(echo "scale=2; ($year_end_mrr - $current_mrr) / 1 * 100" | bc)

    # Customer validation score
    local validation_score=$(calculate_validation_score "$feature_name")

    # Generate revenue prediction report
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local safe_name=$(echo "$feature_name" | tr ' /' '__')
    local revenue_report="$REVENUE_DATA_DIR/prediction_${safe_name}_${timestamp}.json"

    cat > "$revenue_report" <<EOF
{
  "feature": "$feature_name",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "assumptions": {
    "user_acquisition_boost": $user_acquisition_boost,
    "retention_boost": $retention_boost,
    "price_elasticity": "$price_elasticity",
    "implementation_weeks": $implementation_time,
    "avg_revenue_per_user": $avg_revenue_per_user
  },
  "projections": $projections,
  "summary": {
    "year_end_mrr": $year_end_mrr,
    "total_revenue_year1": $total_revenue,
    "growth_rate": "$growth_rate%",
    "months_to_mrr_target": $(calculate_months_to_target "$projections" "$mrr_target"),
    "customer_validation_score": $validation_score
  },
  "confidence_level": "$(calculate_confidence_level "$validation_score" "$implementation_time")"
}
EOF

    # Display results
    echo
    log_money "=== Revenue Impact Prediction: $feature_name ==="
    log_metric "User Acquisition Boost: +${user_acquisition_boost}%"
    log_metric "Retention Improvement: +${retention_boost}%"
    log_metric "Implementation Time: $implementation_time weeks"
    echo
    log_money "Year-End MRR: \$$year_end_mrr"
    log_money "Total Year 1 Revenue: \$$total_revenue"
    log_metric "Growth Rate: ${growth_rate}%"
    log_metric "Months to \$${mrr_target} MRR: $(calculate_months_to_target "$projections" "$mrr_target")"
    log_metric "Customer Validation: ${validation_score}/100"
    echo
    log_success "Revenue prediction saved: $revenue_report"

    # Update projections file
    local all_projections=$(jq ".scenarios += [{\"name\": \"$feature_name\", \"file\": \"$revenue_report\"}]" "$REVENUE_DATA_DIR/projections.json")
    echo "$all_projections" > "$REVENUE_DATA_DIR/projections.json"
}

calculate_months_to_target() {
    local projections="$1"
    local target="$2"

    local months=$(echo "$projections" | jq "[.[] | select(.mrr >= $target)] | first | .month // 999")

    if [[ "$months" == "999" ]]; then
        echo ">12"
    else
        echo "$months"
    fi
}

calculate_validation_score() {
    local feature_name="$1"

    # Check if we have customer validation data
    local interviews=$(jq '.interviews | length' "$VALIDATION_DIR/customers.json" 2>/dev/null || echo "0")
    local positive_feedback=$(jq '[.feedback[] | select(.sentiment == "positive")] | length' "$VALIDATION_DIR/customers.json" 2>/dev/null || echo "0")
    local total_feedback=$(jq '.feedback | length' "$VALIDATION_DIR/customers.json" 2>/dev/null || echo "0")

    local score=50 # Base score

    # Interview bonus
    score=$((score + interviews * 5))

    # Feedback ratio bonus
    if [[ "$total_feedback" -gt 0 ]]; then
        local positive_ratio=$(echo "scale=2; $positive_feedback / $total_feedback * 30" | bc)
        score=$(echo "scale=0; $score + $positive_ratio" | bc)
    fi

    # Cap at 100
    [[ "$score" -gt 100 ]] && score=100

    echo "$score"
}

calculate_confidence_level() {
    local validation_score="$1"
    local implementation_time="$2"

    if [[ "$validation_score" -ge 70 ]] && [[ "$implementation_time" -le 4 ]]; then
        echo "HIGH - Strong validation and quick implementation"
    elif [[ "$validation_score" -ge 50 ]] || [[ "$implementation_time" -le 2 ]]; then
        echo "MEDIUM - Reasonable validation or very quick to implement"
    else
        echo "LOW - Limited validation and longer implementation"
    fi
}

# ========================================
#  Customer Validation
# ========================================

add_customer_feedback() {
    local feature_name="$1"
    local customer_segment="$2"
    local sentiment="$3" # positive/neutral/negative
    local feedback_text="$4"
    local willingness_to_pay="${5:-0}"

    log_info "Adding customer feedback for: $feature_name"

    # Create feedback entry
    local feedback_entry=$(cat <<EOF
{
  "feature": "$feature_name",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "customer_segment": "$customer_segment",
  "sentiment": "$sentiment",
  "feedback": "$feedback_text",
  "willingness_to_pay": $willingness_to_pay
}
EOF
)

    # Add to customers file
    local updated=$(jq ".feedback += [$feedback_entry]" "$VALIDATION_DIR/customers.json")
    echo "$updated" > "$VALIDATION_DIR/customers.json"

    log_success "Customer feedback recorded"

    # Recalculate validation score
    local new_score=$(calculate_validation_score "$feature_name")
    log_metric "Updated validation score: ${new_score}/100"
}

# ========================================
#  Decision Support
# ========================================

compare_features() {
    local feature1="$1"
    local feature2="$2"

    log_info "Comparing features: $feature1 vs $feature2"

    # Find latest reports for each feature
    local safe_name1=$(echo "$feature1" | tr ' /' '__')
    local safe_name2=$(echo "$feature2" | tr ' /' '__')
    local roi1=$(find "$REPORTS_DIR" -name "roi_${safe_name1}_*.json" -type f -exec ls -t {} + | head -1)
    local roi2=$(find "$REPORTS_DIR" -name "roi_${safe_name2}_*.json" -type f -exec ls -t {} + | head -1)
    local revenue1=$(find "$REVENUE_DATA_DIR" -name "prediction_${safe_name1}_*.json" -type f -exec ls -t {} + | head -1)
    local revenue2=$(find "$REVENUE_DATA_DIR" -name "prediction_${safe_name2}_*.json" -type f -exec ls -t {} + | head -1)

    if [[ -z "$roi1" ]] || [[ -z "$roi2" ]]; then
        log_error "Missing ROI analysis for comparison. Run 'roi' command first."
        return 1
    fi

    # Extract comparison metrics
    local roi1_monthly=$(jq -r '.roi.monthly_percentage' "$roi1")
    local roi2_monthly=$(jq -r '.roi.monthly_percentage' "$roi2")
    local cost1=$(jq -r '.investment.total_cost' "$roi1")
    local cost2=$(jq -r '.investment.total_cost' "$roi2")
    local risk1=$(jq -r '.roi.risk_level' "$roi1")
    local risk2=$(jq -r '.roi.risk_level' "$roi2")

    # Revenue comparison if available
    local mrr1="N/A"
    local mrr2="N/A"
    if [[ -n "$revenue1" ]]; then
        mrr1=$(jq -r '.summary.year_end_mrr' "$revenue1")
    fi
    if [[ -n "$revenue2" ]]; then
        mrr2=$(jq -r '.summary.year_end_mrr' "$revenue2")
    fi

    # Generate comparison report
    local comparison_report="$REPORTS_DIR/comparison_${safe_name1}_vs_${safe_name2}_$(date +%Y%m%d_%H%M%S).json"

    cat > "$comparison_report" <<EOF
{
  "comparison": {
    "feature1": "$feature1",
    "feature2": "$feature2",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  },
  "metrics": {
    "$feature1": {
      "roi_monthly": $roi1_monthly,
      "investment": $cost1,
      "risk": "$risk1",
      "year_end_mrr": "$mrr1"
    },
    "$feature2": {
      "roi_monthly": $roi2_monthly,
      "investment": $cost2,
      "risk": "$risk2",
      "year_end_mrr": "$mrr2"
    }
  },
  "recommendation": "$(get_comparison_recommendation "$roi1_monthly" "$roi2_monthly" "$risk1" "$risk2")",
  "analysis": {
    "roi_winner": "$(get_winner "$roi1_monthly" "$roi2_monthly" "$feature1" "$feature2")",
    "cost_winner": "$(get_winner "$cost2" "$cost1" "$feature1" "$feature2")",
    "risk_winner": "$(get_risk_winner "$risk1" "$risk2" "$feature1" "$feature2")"
  }
}
EOF

    # Display comparison
    echo
    log_metric "=== Feature Comparison ==="
    echo
    printf "%-30s %-20s %-20s\n" "Metric" "$feature1" "$feature2"
    printf "%-30s %-20s %-20s\n" "-----" "-----" "-----"
    printf "%-30s %-20s %-20s\n" "Monthly ROI" "${roi1_monthly}%" "${roi2_monthly}%"
    printf "%-30s %-20s %-20s\n" "Investment" "\$$cost1" "\$$cost2"
    printf "%-30s %-20s %-20s\n" "Risk Level" "$risk1" "$risk2"
    printf "%-30s %-20s %-20s\n" "Year-End MRR" "\$$mrr1" "\$$mrr2"
    echo
    log_success "Comparison saved: $comparison_report"

    # Update decision history
    update_decision_history "feature_comparison" "$feature1 vs $feature2" "$comparison_report"
}

get_winner() {
    local val1="$1"
    local val2="$2"
    local name1="$3"
    local name2="$4"

    if (( $(echo "$val1 > $val2" | bc -l) )); then
        echo "$name1"
    elif (( $(echo "$val2 > $val1" | bc -l) )); then
        echo "$name2"
    else
        echo "TIE"
    fi
}

get_risk_winner() {
    local risk1="$1"
    local risk2="$2"
    local name1="$3"
    local name2="$4"

    # Lower risk is better
    local score1=0
    local score2=0

    case "$risk1" in
        "low") score1=3 ;;
        "medium") score1=2 ;;
        "high") score1=1 ;;
    esac

    case "$risk2" in
        "low") score2=3 ;;
        "medium") score2=2 ;;
        "high") score2=1 ;;
    esac

    if [[ "$score1" -gt "$score2" ]]; then
        echo "$name1"
    elif [[ "$score2" -gt "$score1" ]]; then
        echo "$name2"
    else
        echo "TIE"
    fi
}

get_comparison_recommendation() {
    local roi1="$1"
    local roi2="$2"
    local risk1="$3"
    local risk2="$4"

    local roi_diff=$(echo "scale=2; $roi1 - $roi2" | bc)

    if (( $(echo "$roi_diff > 20" | bc -l) )); then
        echo "STRONGLY FAVOR Feature 1 - Significantly higher ROI"
    elif (( $(echo "$roi_diff > 0" | bc -l) )); then
        if [[ "$risk1" == "$risk2" ]]; then
            echo "FAVOR Feature 1 - Higher ROI with similar risk"
        else
            echo "CONSIDER BOTH - Feature 1 has higher ROI but check risk levels"
        fi
    elif (( $(echo "$roi_diff < -20" | bc -l) )); then
        echo "STRONGLY FAVOR Feature 2 - Significantly higher ROI"
    elif (( $(echo "$roi_diff < 0" | bc -l) )); then
        if [[ "$risk1" == "$risk2" ]]; then
            echo "FAVOR Feature 2 - Higher ROI with similar risk"
        else
            echo "CONSIDER BOTH - Feature 2 has higher ROI but check risk levels"
        fi
    else
        echo "TIE - Consider other factors like market timing and validation"
    fi
}

# ========================================
#  Dashboard & Reporting
# ========================================

show_dashboard() {
    clear
    cat <<EOF
╔══════════════════════════════════════════════════════════════╗
║              SOLOPRENEUR BUSINESS INTELLIGENCE               ║
╚══════════════════════════════════════════════════════════════╝

💼 BUSINESS STATUS
   Stage:           $(jq -r '.business.stage' "$BI_DIR/config.json")
   MRR Target:      \$$(jq -r '.financials.mrr_target' "$BI_DIR/config.json")
   Runway:          $(jq -r '.financials.runway_months' "$BI_DIR/config.json") months

📊 RECENT ANALYSES
EOF

    # Show recent ROI analyses
    echo "   ROI Analyses:"
    find "$REPORTS_DIR" -name "roi_*.json" -type f -exec ls -t {} + | head -3 | while read -r file; do
        local feature=$(jq -r '.feature' "$file")
        local roi=$(jq -r '.roi.monthly_percentage' "$file")
        printf "   - %-30s ROI: %s%%\n" "$feature" "$roi"
    done

    # Show recent revenue predictions
    echo
    echo "   Revenue Predictions:"
    find "$REVENUE_DATA_DIR" -name "prediction_*.json" -type f -exec ls -t {} + | head -3 | while read -r file; do
        local feature=$(jq -r '.feature' "$file")
        local mrr=$(jq -r '.summary.year_end_mrr' "$file")
        printf "   - %-30s Year-End MRR: \$%s\n" "$feature" "$mrr"
    done

    # Show validation metrics
    echo
    echo "🎯 CUSTOMER VALIDATION"
    local total_feedback=$(jq '.feedback | length' "$VALIDATION_DIR/customers.json" 2>/dev/null || echo "0")
    local positive=$(jq '[.feedback[] | select(.sentiment == "positive")] | length' "$VALIDATION_DIR/customers.json" 2>/dev/null || echo "0")
    echo "   Total Feedback:  $total_feedback"
    echo "   Positive:        $positive"

    # Show recent decisions
    echo
    echo "📝 RECENT DECISIONS"
    jq -r '.decisions[-3:] | reverse | .[] | "   - \(.timestamp | split("T")[0]): \(.type) - \(.description)"' "$DECISIONS_DIR/history.json" 2>/dev/null || echo "   No decisions recorded yet"

    echo
    echo "⚡ QUICK ACTIONS"
    echo "   1. Calculate ROI (roi)"
    echo "   2. Analyze market timing (market)"
    echo "   3. Predict revenue impact (revenue)"
    echo "   4. Compare features (compare)"
    echo "   5. Add customer feedback (feedback)"
    echo
}

generate_executive_report() {
    local report_type="${1:-weekly}"

    log_info "Generating $report_type executive report..."

    local report_file="$REPORTS_DIR/executive_${report_type}_$(date +%Y%m%d).html"

    cat > "$report_file" <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Business Intelligence Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #333; }
        .metric { display: inline-block; margin: 20px; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .metric-label { color: #666; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: bold; }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .chart { margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Business Intelligence Report</h1>
EOF

    # Add current date
    echo "<p>Generated: $(date '+%Y-%m-%d %H:%M')</p>" >> "$report_file"

    # Add key metrics
    echo "<h2>Key Metrics</h2>" >> "$report_file"
    echo "<div class='metrics'>" >> "$report_file"

    # Calculate average ROI from recent analyses
    local avg_roi=$(find "$REPORTS_DIR" -name "roi_*.json" -type f -exec ls -t {} + | head -5 | \
        xargs -I {} jq -r '.roi.monthly_percentage' {} | \
        awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}')

    echo "<div class='metric'><div class='metric-value'>$avg_roi%</div><div class='metric-label'>Avg Monthly ROI</div></div>" >> "$report_file"

    # Add feature comparison table
    echo "<h2>Recent Feature Analyses</h2>" >> "$report_file"
    echo "<table>" >> "$report_file"
    echo "<tr><th>Feature</th><th>ROI</th><th>Investment</th><th>Risk</th><th>Recommendation</th></tr>" >> "$report_file"

    find "$REPORTS_DIR" -name "roi_*.json" -type f -exec ls -t {} + | head -5 | while read -r file; do
        local feature=$(jq -r '.feature' "$file")
        local roi=$(jq -r '.roi.monthly_percentage' "$file")
        local cost=$(jq -r '.investment.total_cost' "$file")
        local risk=$(jq -r '.roi.risk_level' "$file")
        local rec=$(jq -r '.recommendation' "$file" | cut -d'-' -f1)

        echo "<tr><td>$feature</td><td class='positive'>$roi%</td><td>\$$cost</td><td>$risk</td><td>$rec</td></tr>" >> "$report_file"
    done

    echo "</table>" >> "$report_file"

    # Close HTML
    echo "</div></body></html>" >> "$report_file"

    log_success "Executive report generated: $report_file"

    # Open in browser if available
    if command -v open &> /dev/null; then
        open "$report_file"
    fi
}

# ========================================
#  Utility Functions
# ========================================

update_decision_history() {
    local decision_type="$1"
    local description="$2"
    local report_file="$3"

    local decision_entry=$(cat <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "type": "$decision_type",
  "description": "$description",
  "report": "$report_file"
}
EOF
)

    local updated=$(jq ".decisions += [$decision_entry]" "$DECISIONS_DIR/history.json")
    echo "$updated" > "$DECISIONS_DIR/history.json"
}

cleanup_old_data() {
    local days="${1:-30}"

    log_info "Cleaning data older than $days days..."

    find "$BI_DIR" -name "*.json" -type f -mtime +$days -delete
    find "$REPORTS_DIR" -name "*.html" -type f -mtime +$days -delete

    log_success "Cleanup complete"
}

# ========================================
#  Main Command Handler
# ========================================

show_usage() {
    cat <<EOF
💼 Solopreneur Business Intelligence System

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    init                Initialize business intelligence system
    roi <feature> [hours] [rate] [revenue] [impact]
                       Calculate ROI for a feature
    market <feature> [trend] [competition] [seasonal]
                       Analyze market timing
    revenue <feature> [acquisition%] [retention%] [elasticity] [weeks]
                       Predict revenue impact
    compare <feature1> <feature2>
                       Compare two features
    feedback <feature> <segment> <sentiment> <text> [pay]
                       Add customer feedback
    dashboard          Show BI dashboard
    report [type]      Generate executive report
    cleanup [days]     Clean old data

EXAMPLES:
    # Calculate ROI for a new feature
    $0 roi "API Rate Limiting" 40 150 2000 high

    # Analyze market timing
    $0 market "API Rate Limiting" growing none peak

    # Predict revenue impact
    $0 revenue "API Rate Limiting" 15 10 medium 3

    # Compare two features
    $0 compare "API Rate Limiting" "Social Login"

    # Add customer feedback
    $0 feedback "API Rate Limiting" enterprise positive "Would pay extra for this" 50

EOF
}

# Main execution
main() {
    local cmd="${1:-}"

    case "$cmd" in
        init)
            init_business_intelligence
            ;;
        roi)
            shift
            calculate_roi "$@"
            ;;
        market)
            shift
            analyze_market_timing "$@"
            ;;
        revenue)
            shift
            predict_revenue_impact "$@"
            ;;
        compare)
            shift
            compare_features "$@"
            ;;
        feedback)
            shift
            add_customer_feedback "$@"
            ;;
        dashboard)
            show_dashboard
            ;;
        report)
            shift
            generate_executive_report "$@"
            ;;
        cleanup)
            shift
            cleanup_old_data "$@"
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Initialize on first run
[[ ! -d "$BI_DIR" ]] && init_business_intelligence

# Run main
main "$@"
