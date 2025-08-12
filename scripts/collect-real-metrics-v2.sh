#!/bin/bash
# Collect ONLY REAL metrics - NO TEMPLATES OR FAKE DATA
# Shows "NO DATA" when services aren't running

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Create metrics directory
mkdir -p "$PROJECT_ROOT/.metrics"
mkdir -p "$PROJECT_ROOT/.portfolio/data"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Load agent environment to know which agent is running
source .agent.env 2>/dev/null || AGENT_ID="unknown"

echo "📊 Collecting Real Metrics for Agent $AGENT_ID"
echo "=========================================="
echo "⚠️  ONLY showing real data - no templates!"
echo ""

# ═══════════════════════════════════════════════════════
# Agent-Specific Context
# ═══════════════════════════════════════════════════════

show_agent_context() {
    echo -e "${YELLOW}Agent $AGENT_ID Focus Areas:${NC}"
    
    case "$AGENT_ID" in
        a1)
            echo "  📍 MLOps/Orchestrator Agent"
            echo "  Services: orchestrator, celery_worker, persona_runtime"
            echo "  Focus: MLflow, SLO gates, performance monitoring"
            echo "  Portfolio Priority: MLflow screenshots, SLO gate demos"
            ;;
        a2)
            echo "  📍 GenAI/RAG Agent"
            echo "  Services: rag_pipeline, vllm_service, viral_engine"
            echo "  Focus: vLLM optimization, token costs, RAG accuracy"
            echo "  Portfolio Priority: Cost comparison tables, vLLM benchmarks"
            ;;
        a3)
            echo "  📍 Analytics/Documentation Agent"
            echo "  Services: achievement_collector, tech_doc_generator"
            echo "  Focus: Portfolio generation, documentation, dashboards"
            echo "  Portfolio Priority: Achievement tracking, documentation"
            ;;
        a4)
            echo "  📍 Platform/Revenue Agent"
            echo "  Services: revenue, finops_engine, event_bus, threads_adaptor"
            echo "  Focus: A/B testing, revenue metrics, cost optimization"
            echo "  Portfolio Priority: A/B test results, revenue dashboards"
            ;;
        *)
            echo "  ⚠️  Unknown agent - run: source .agent.env"
            ;;
    esac
    echo ""
}

# ═══════════════════════════════════════════════════════
# 1. MLflow Metrics (Agent A1 priority)
# ═══════════════════════════════════════════════════════

collect_mlflow_metrics() {
    echo -e "${YELLOW}MLflow Status (Agent A1 focus):${NC}"
    
    if [[ -f "$PROJECT_ROOT/mlflow.db" ]]; then
        # Real data from MLflow database
        MODEL_COUNT=$(sqlite3 "$PROJECT_ROOT/mlflow.db" "SELECT COUNT(DISTINCT name) FROM registered_models" 2>/dev/null || echo 0)
        VERSION_COUNT=$(sqlite3 "$PROJECT_ROOT/mlflow.db" "SELECT COUNT(*) FROM model_versions" 2>/dev/null || echo 0)
        
        if [[ "$MODEL_COUNT" -gt 0 ]]; then
            echo "  ✅ REAL DATA: $MODEL_COUNT models, $VERSION_COUNT versions"
            
            # List actual models
            echo "  Models registered:"
            sqlite3 "$PROJECT_ROOT/mlflow.db" "SELECT name, max_version FROM registered_models" 2>/dev/null | head -5
        else
            echo "  ❌ NO MODELS IN MLFLOW YET"
            echo "  Action: cd services/viral_engine && python train_model.py"
        fi
    else
        echo "  ❌ MLFLOW NOT INITIALIZED"
        echo "  Action for A1: mlflow server --backend-store-uri sqlite:///mlflow.db"
    fi
}

# ═══════════════════════════════════════════════════════
# 2. Service Metrics (All agents)
# ═══════════════════════════════════════════════════════

collect_service_metrics() {
    echo -e "\n${YELLOW}Service Health & Metrics:${NC}"
    
    # Check each service based on agent
    case "$AGENT_ID" in
        a1)
            SERVICES=("orchestrator:8080" "celery-worker:5555" "persona-runtime:8082")
            ;;
        a2)
            SERVICES=("rag-pipeline:8083" "vllm-service:8084" "viral-engine:8085")
            ;;
        a3)
            SERVICES=("achievement-collector:8086" "dashboard-api:8087")
            ;;
        a4)
            SERVICES=("revenue:8088" "threads-adaptor:8089" "event-bus:8090")
            ;;
        *)
            SERVICES=("orchestrator:8080")
            ;;
    esac
    
    for service_port in "${SERVICES[@]}"; do
        IFS=':' read -r service port <<< "$service_port"
        
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "  ✅ $service: RUNNING"
            
            # Get real metrics
            METRICS=$(curl -s "http://localhost:$port/metrics" 2>/dev/null || echo "")
            if [[ -n "$METRICS" ]]; then
                # Extract real values
                REQUESTS=$(echo "$METRICS" | grep -c "http_request" || echo "0")
                echo "     Real requests tracked: $REQUESTS"
            fi
        else
            echo "  ❌ $service: NOT RUNNING (port $port)"
        fi
    done
}

# ═══════════════════════════════════════════════════════
# 3. vLLM Metrics (Agent A2 priority)
# ═══════════════════════════════════════════════════════

collect_vllm_metrics() {
    echo -e "\n${YELLOW}vLLM Status (Agent A2 focus):${NC}"
    
    if kubectl get svc vllm-service -n default 2>/dev/null; then
        echo "  ✅ vLLM service deployed in Kubernetes"
        
        # Try to get real metrics
        kubectl port-forward svc/vllm-service 8001:8000 -n default &
        PF_PID=$!
        sleep 3
        
        if curl -s http://localhost:8001/health 2>/dev/null; then
            echo "  ✅ vLLM responding, collecting metrics..."
            VLLM_METRICS=$(curl -s http://localhost:8001/metrics 2>/dev/null)
            
            # Parse real metrics
            if [[ -n "$VLLM_METRICS" ]]; then
                echo "  📊 Real vLLM metrics collected"
            fi
        else
            echo "  ⚠️  vLLM deployed but not responding"
        fi
        
        kill $PF_PID 2>/dev/null || true
    else
        echo "  ❌ vLLM NOT DEPLOYED"
        echo "  Action for A2: cd services/vllm_service && just deploy"
    fi
}

# ═══════════════════════════════════════════════════════
# 4. Database Metrics (All agents)
# ═══════════════════════════════════════════════════════

collect_database_metrics() {
    echo -e "\n${YELLOW}Database Metrics:${NC}"
    
    if [[ -n "${DATABASE_URL:-}" ]]; then
        # Try to connect and get real counts
        POSTS=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM posts" 2>/dev/null || echo "")
        TASKS=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM tasks" 2>/dev/null || echo "")
        
        if [[ -n "$POSTS" ]]; then
            echo "  ✅ PostgreSQL connected"
            echo "     Posts: $POSTS"
            echo "     Tasks: $TASKS"
        else
            echo "  ❌ Cannot connect to PostgreSQL"
        fi
    else
        echo "  ❌ DATABASE_URL not configured"
        echo "  Action: export DATABASE_URL=postgresql://..."
    fi
}

# ═══════════════════════════════════════════════════════
# 5. Achievement Stats (Agent A3 priority)
# ═══════════════════════════════════════════════════════

collect_achievement_stats() {
    echo -e "\n${YELLOW}Achievement Collection (Agent A3 focus):${NC}"
    
    if [[ -f "$PROJECT_ROOT/.achievements/summary.json" ]]; then
        TOTAL=$(jq '.achievements | length' "$PROJECT_ROOT/.achievements/summary.json" 2>/dev/null || echo 0)
        
        if [[ "$TOTAL" -gt 0 ]]; then
            echo "  ✅ Real achievements: $TOTAL"
            
            # Show recent achievements
            jq -r '.achievements[-3:] | .[] | "     • \(.title)"' "$PROJECT_ROOT/.achievements/summary.json" 2>/dev/null
        else
            echo "  ❌ No achievements collected yet"
        fi
    else
        echo "  ❌ Achievement collector not initialized"
        echo "  Action for A3: cd services/achievement_collector && python collect.py"
    fi
}

# ═══════════════════════════════════════════════════════
# 6. Portfolio Artifacts (All agents)
# ═══════════════════════════════════════════════════════

check_portfolio_artifacts() {
    echo -e "\n${YELLOW}Portfolio Artifacts Status:${NC}"
    
    # Required artifacts per agent
    case "$AGENT_ID" in
        a1)
            REQUIRED=("mlflow_registry.png" "slo_gate_demo.mp4" "grafana_dashboard.png")
            ;;
        a2)
            REQUIRED=("vllm_benchmark.png" "cost_comparison.xlsx" "token_usage.png")
            ;;
        a3)
            REQUIRED=("achievement_report.pdf" "documentation.md" "portfolio_site.png")
            ;;
        a4)
            REQUIRED=("ab_test_results.png" "revenue_dashboard.png" "cost_analysis.xlsx")
            ;;
        *)
            REQUIRED=("mlflow_registry.png" "cost_comparison.xlsx")
            ;;
    esac
    
    for artifact in "${REQUIRED[@]}"; do
        if [[ -f "$PROJECT_ROOT/.portfolio/$artifact" ]]; then
            SIZE=$(ls -lh "$PROJECT_ROOT/.portfolio/$artifact" | awk '{print $5}')
            echo "  ✅ $artifact ($SIZE)"
        else
            echo "  ❌ MISSING: $artifact"
        fi
    done
}

# ═══════════════════════════════════════════════════════
# 7. Generate REAL Cost Table (NO FAKE DATA)
# ═══════════════════════════════════════════════════════

generate_real_cost_table() {
    echo -e "\n${YELLOW}Cost Analysis:${NC}"
    
    # Check if we have real data
    HAS_OPENAI_DATA=false
    HAS_VLLM_DATA=false
    
    # Check for OpenAI usage
    if [[ -f "$PROJECT_ROOT/.metrics/openai_usage.json" ]]; then
        HAS_OPENAI_DATA=true
        OPENAI_TOKENS=$(jq -r '.total_tokens' "$PROJECT_ROOT/.metrics/openai_usage.json" 2>/dev/null)
        OPENAI_COST=$(jq -r '.total_cost' "$PROJECT_ROOT/.metrics/openai_usage.json" 2>/dev/null)
    fi
    
    # Check for vLLM usage
    if [[ -f "$PROJECT_ROOT/.metrics/vllm_usage.json" ]]; then
        HAS_VLLM_DATA=true
        VLLM_TOKENS=$(jq -r '.total_tokens' "$PROJECT_ROOT/.metrics/vllm_usage.json" 2>/dev/null)
        VLLM_COST=$(jq -r '.total_cost' "$PROJECT_ROOT/.metrics/vllm_usage.json" 2>/dev/null)
    fi
    
    if [[ "$HAS_OPENAI_DATA" == "true" ]] || [[ "$HAS_VLLM_DATA" == "true" ]]; then
        echo "  ✅ REAL cost data available"
        
        cat > "$PROJECT_ROOT/.portfolio/real_cost_analysis.md" << EOF
# REAL Cost Analysis - Agent $AGENT_ID

## Actual Usage Data (NO ESTIMATES)

| Provider | Tokens Used | Total Cost | Per 1k Tokens |
|----------|-------------|------------|---------------|
EOF
        
        if [[ "$HAS_OPENAI_DATA" == "true" ]]; then
            echo "| OpenAI | $OPENAI_TOKENS | \$$OPENAI_COST | \$$(echo "scale=4; $OPENAI_COST * 1000 / $OPENAI_TOKENS" | bc) |" >> "$PROJECT_ROOT/.portfolio/real_cost_analysis.md"
        fi
        
        if [[ "$HAS_VLLM_DATA" == "true" ]]; then
            echo "| vLLM | $VLLM_TOKENS | \$$VLLM_COST | \$$(echo "scale=4; $VLLM_COST * 1000 / $VLLM_TOKENS" | bc) |" >> "$PROJECT_ROOT/.portfolio/real_cost_analysis.md"
        fi
        
        echo "" >> "$PROJECT_ROOT/.portfolio/real_cost_analysis.md"
        echo "Data collected: $(date)" >> "$PROJECT_ROOT/.portfolio/real_cost_analysis.md"
        echo "Agent: $AGENT_ID" >> "$PROJECT_ROOT/.portfolio/real_cost_analysis.md"
    else
        echo "  ❌ NO REAL COST DATA AVAILABLE"
        echo "  Cannot generate portfolio artifact without real data!"
        echo ""
        echo "  To collect real data:"
        echo "    1. Run services: just dev-start"
        echo "    2. Generate some posts: just create-viral"
        echo "    3. Wait for metrics: sleep 60"
        echo "    4. Try again: just real-metrics"
    fi
}

# ═══════════════════════════════════════════════════════
# Main Report
# ═══════════════════════════════════════════════════════

main() {
    show_agent_context
    
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}REAL METRICS REPORT - AGENT $AGENT_ID${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    
    # Collect based on agent focus
    case "$AGENT_ID" in
        a1)
            collect_mlflow_metrics
            collect_service_metrics
            collect_database_metrics
            ;;
        a2)
            collect_vllm_metrics
            collect_service_metrics
            generate_real_cost_table
            ;;
        a3)
            collect_achievement_stats
            check_portfolio_artifacts
            ;;
        a4)
            collect_database_metrics
            collect_service_metrics
            ;;
        *)
            # Unknown agent - collect everything
            collect_service_metrics
            collect_database_metrics
            ;;
    esac
    
    echo -e "\n${RED}═══════════════════════════════════════════════════════${NC}"
    echo -e "${RED}NEXT ACTIONS FOR AGENT $AGENT_ID${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
    
    # Agent-specific recommendations
    case "$AGENT_ID" in
        a1)
            echo "  1. Initialize MLflow if not done"
            echo "  2. Deploy services and collect SLO metrics"
            echo "  3. Generate Grafana dashboard screenshots"
            ;;
        a2)
            echo "  1. Deploy vLLM service"
            echo "  2. Run cost comparison benchmarks"
            echo "  3. Generate token optimization reports"
            ;;
        a3)
            echo "  1. Run achievement collector on recent PRs"
            echo "  2. Generate portfolio documentation"
            echo "  3. Create achievement visualizations"
            ;;
        a4)
            echo "  1. Set up A/B testing framework"
            echo "  2. Collect revenue metrics"
            echo "  3. Generate cost analysis reports"
            ;;
    esac
}

# Run command
case "${1:-all}" in
    all)
        main
        ;;
    *)
        echo "Collecting specific metrics: $1"
        collect_$1 2>/dev/null || echo "❌ Unknown metric type: $1"
        ;;
esac