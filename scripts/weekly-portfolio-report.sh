#!/bin/bash
# Generate weekly portfolio report for job applications

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

generate_weekly_report() {
    local week_num=$(date +%U)
    local report_file="$PROJECT_ROOT/.portfolio/weekly_report_week${week_num}.md"
    
    cat > "$report_file" << EOF
# 📊 Weekly Portfolio Report - Week $week_num
Generated: $(date)

## 🎯 Job Application Progress (Target: 10/week)

### Applications Sent
$(find .job-tracker -name "*.json" -mtime -7 2>/dev/null | wc -l) / 10

### Portfolio Artifacts Created
EOF
    
    # Check each agent's portfolio items
    for agent in a1 a2 a3 a4; do
        echo "" >> "$report_file"
        echo "### Agent $agent Progress" >> "$report_file"
        
        case $agent in
            a1)
                check_artifact "MLflow screenshot" "mlflow_registry.png"
                check_artifact "SLO demo video" "slo_gate_demo.mp4"
                check_artifact "Grafana dashboard" "grafana_dashboard.png"
                ;;
            a2)
                check_artifact "vLLM benchmark" "vllm_benchmark.png"
                check_artifact "Cost comparison" "cost_comparison.xlsx"
                check_artifact "Token dashboard" "token_usage.png"
                ;;
            a3)
                check_artifact "Achievement report" "achievement_report.pdf"
                check_artifact "Portfolio site" "portfolio_site.png"
                check_artifact "Documentation" "technical_docs.md"
                ;;
            a4)
                check_artifact "A/B test results" "ab_test_results.png"
                check_artifact "Revenue dashboard" "revenue_dashboard.png"
                check_artifact "FinOps report" "finops_savings.xlsx"
                ;;
        esac
    done
    
    # Add recommendations
    cat >> "$report_file" << EOF

## 🚀 Recommendations for Next Week

### High Priority (for job applications)
$(analyze_gaps)

### Quick Wins
$(find_quick_wins)

## 📈 Metrics Summary
- Total Portfolio Items: $(ls .portfolio/*.{png,mp4,pdf,xlsx} 2>/dev/null | wc -l)
- Job Applications Total: $(find .job-tracker -name "*.json" | wc -l)
- This Week's PRs: $(git log --since="1 week ago" --oneline | wc -l)

## 🎯 Next Week Goals
1. Send 10 tailored applications
2. Complete 2 portfolio artifacts
3. Record 1 demo video
4. Update LinkedIn with achievements
EOF
    
    echo "✅ Report generated: $report_file"
}

check_artifact() {
    local name="$1"
    local file="$2"
    if [[ -f "$PROJECT_ROOT/.portfolio/$file" ]]; then
        echo "- ✅ $name" >> "$report_file"
    else
        echo "- ❌ $name (NEEDED for applications!)" >> "$report_file"
    fi
}

analyze_gaps() {
    # Analyze what's missing for job applications
    local gaps=""
    
    if [[ ! -f "$PROJECT_ROOT/.portfolio/mlflow_registry.png" ]]; then
        gaps="1. MLflow screenshot (A1 priority)"
    fi
    
    if [[ ! -f "$PROJECT_ROOT/.portfolio/vllm_benchmark.png" ]]; then
        gaps="$gaps
2. vLLM cost comparison (A2 priority)"
    fi
    
    echo "$gaps"
}

find_quick_wins() {
    echo "1. Generate cost table from real metrics
2. Screenshot existing dashboards
3. Export achievement report as PDF"
}

# Run report
generate_weekly_report