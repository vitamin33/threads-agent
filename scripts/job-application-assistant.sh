#!/bin/bash
# Smart job application assistant aligned with AI_JOB_STRATEGY.md

set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Target roles from AI_JOB_STRATEGY.md
declare -A target_roles=(
    ["MLOps Engineer"]="160-180k"
    ["Platform Engineer"]="170-190k"
    ["GenAI Engineer"]="170-190k"
    ["AI Platform Engineer"]="180-220k"
    ["Senior MLOps Engineer"]="180-200k"
    ["LLM Specialist"]="170-190k"
)

check_daily_applications() {
    local today_count=$(find .job-tracker -name "*.json" -mtime -1 | wc -l)
    local week_count=$(find .job-tracker -name "*.json" -mtime -7 | wc -l)
    
    echo "📊 Application Status"
    echo "Today: $today_count / 2 target"
    echo "This week: $week_count / 10 target"
    
    if [[ $today_count -lt 2 ]]; then
        echo ""
        echo "⚠️  Need to send $(( 2 - today_count )) more applications today!"
        suggest_companies
    fi
}

suggest_companies() {
    echo ""
    echo "🎯 Suggested Companies (from AI_JOB_STRATEGY.md):"
    echo "Remote-First Companies:"
    echo "  • Anthropic - AI Safety/Platform roles"
    echo "  • Scale AI - MLOps/Platform Engineering" 
    echo "  • Weights & Biases - ML Platform"
    echo "  • Hugging Face - LLM/GenAI roles"
    echo "  • Cohere - AI Platform Engineering"
    echo ""
    echo "Quick apply with proof pack:"
    echo "  just job-apply 'Anthropic' 'AI Platform Engineer'"
}

track_application() {
    local company="$1"
    local role="$2"
    local salary="${target_roles[$role]:-unknown}"
    
    # Create tracking entry
    local app_file=".job-tracker/$(date +%Y%m%d)_${company// /_}.json"
    
    cat > "$app_file" << EOF
{
    "company": "$company",
    "role": "$role",
    "salary_range": "$salary",
    "date_applied": "$(date +%Y-%m-%d)",
    "proof_pack_items": $(list_proof_pack),
    "agent_focus": "$(determine_agent_focus "$role")",
    "follow_up_date": "$(date -d '+1 week' +%Y-%m-%d 2>/dev/null || date -v+1w +%Y-%m-%d)",
    "status": "applied"
}
EOF
    
    echo "✅ Tracked: $company - $role ($salary)"
    
    # Check if proof pack is ready
    check_proof_pack "$role"
}

list_proof_pack() {
    local items="["
    
    [[ -f ".portfolio/mlflow_registry.png" ]] && items="$items\"mlflow_screenshot\","
    [[ -f ".portfolio/slo_gate_demo.mp4" ]] && items="$items\"slo_demo\","
    [[ -f ".portfolio/cost_comparison.xlsx" ]] && items="$items\"cost_table\","
    [[ -f ".portfolio/grafana_dashboard.png" ]] && items="$items\"dashboard\","
    
    items="${items%,}]"
    echo "$items"
}

determine_agent_focus() {
    local role="$1"
    
    case "$role" in
        *MLOps*|*Platform*)
            echo "a1"
            ;;
        *GenAI*|*LLM*)
            echo "a2"
            ;;
        *Technical*|*Documentation*)
            echo "a3"
            ;;
        *Growth*|*Revenue*)
            echo "a4"
            ;;
        *)
            echo "multi"
            ;;
    esac
}

check_proof_pack() {
    local role="$1"
    local missing=0
    
    echo ""
    echo "📦 Proof Pack Check for $role:"
    
    # Check required items based on role
    case "$role" in
        *MLOps*)
            check_item "MLflow screenshot" ".portfolio/mlflow_registry.png"
            check_item "SLO demo" ".portfolio/slo_gate_demo.mp4"
            ;;
        *GenAI*)
            check_item "vLLM benchmark" ".portfolio/vllm_benchmark.png"
            check_item "Cost comparison" ".portfolio/cost_comparison.xlsx"
            ;;
    esac
    
    if [[ $missing -gt 0 ]]; then
        echo ""
        echo "⚠️  Missing $missing items! Generate with:"
        echo "  just portfolio suggest"
    else
        echo "✅ Proof pack ready!"
    fi
}

check_item() {
    local name="$1"
    local file="$2"
    
    if [[ -f "$file" ]]; then
        echo "  ✅ $name"
    else
        echo "  ❌ $name (MISSING)"
        ((missing++))
    fi
}

generate_cover_letter() {
    local company="$1"
    local role="$2"
    
    cat > ".job-tracker/cover_${company// /_}.md" << 'EOF'
Subject: $role - [Your Name] - Proof Pack Included

Hi [Hiring Manager],

I've built production LLM platforms with the exact capabilities you need:

**Proven Results:**
- Reduced LLM costs by 60% using vLLM deployment
- Built MLflow-based model lifecycle with <1min rollbacks
- Achieved p95 < 500ms with SLO-gated deployments
- Scaled to 50M+ users with 99.9% uptime

**Attached Proof Pack:**
1. MLflow lifecycle demo (2-min Loom)
2. Cost/latency comparison (60% savings)
3. Production dashboards (Grafana)
4. Architecture documentation

GitHub: [your-github]
Portfolio: [your-portfolio]

Ready to demo the full system and discuss how I'd apply these patterns to your challenges.

Best,
[Your Name]
EOF
    
    sed -i '' "s/\$role/$role/" ".job-tracker/cover_${company// /_}.md"
    echo "✅ Cover letter template created"
}

# Main command
case "${1:-status}" in
    status)
        check_daily_applications
        ;;
    track)
        track_application "${2:-}" "${3:-}"
        ;;
    suggest)
        suggest_companies
        ;;
    cover)
        generate_cover_letter "${2:-}" "${3:-}"
        ;;
    *)
        echo "Usage: $0 [status|track|suggest|cover]"
        ;;
esac