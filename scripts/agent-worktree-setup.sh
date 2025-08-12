#!/bin/bash
# Setup script for agent-specific worktrees with clear differentiation
# Each agent has specific services, goals, and portfolio priorities

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo "🚀 Setting up Agent-Specific Worktrees"
echo "======================================"

# ═══════════════════════════════════════════════════════
# Create Agent Configuration Files
# ═══════════════════════════════════════════════════════

setup_agent_a1() {
    local WORKTREE_DIR="$1"
    
    echo -e "${BLUE}Setting up Agent A1 - MLOps/Orchestrator${NC}"
    
    # Create agent environment file
    cat > "$WORKTREE_DIR/.agent.env" << 'EOF'
# Agent A1 Configuration - MLOps/Orchestrator
export AGENT_ID="a1"
export AGENT_NAME="MLOps"
export AGENT_SERVICES="orchestrator celery_worker persona_runtime"
export FOCUS_AREAS="mlflow,slo-gates,monitoring,performance"
export SKIP_SERVICES="rag_pipeline achievement_collector revenue"
export PORT_OFFSET=0
export DB_SCHEMA="agent_a1"

# Job Strategy Focus
export JOB_PRIORITY="MLflow lifecycle, SLO-gated CI, Performance monitoring"
export PORTFOLIO_FOCUS="mlflow_registry.png slo_gate_demo.mp4 grafana_dashboard.png"
EOF
    
    # Create agent-specific task file
    cat > "$WORKTREE_DIR/AGENT_TASKS.md" << 'EOF'
# Agent A1 - MLOps/Orchestrator Tasks

## Primary Responsibilities
- [ ] Set up MLflow tracking and model registry
- [ ] Implement SLO-gated CI/CD pipeline
- [ ] Create performance monitoring dashboards
- [ ] Optimize orchestrator service latency

## Portfolio Artifacts to Generate
1. **MLflow Registry Screenshot** - Show 2+ model versions
2. **SLO Gate Demo Video** - Catch and block bad deployment
3. **Grafana Dashboard** - P95 latency, error rate, throughput

## Weekly Goals (for job applications)
- Deploy 2 models to MLflow registry
- Achieve <500ms p95 latency
- Create automated rollback system
- Document deployment patterns

## Commands
```bash
just mlflow-train        # Train and track model
just slo-check          # Check real SLO metrics
just grafana            # Open monitoring dashboard
```
EOF
    
    # Create AI planning context
    cat > "$WORKTREE_DIR/.ai-context.json" << 'EOF'
{
    "agent": "a1",
    "focus": "MLOps and Platform Engineering",
    "keywords": ["MLflow", "SLO", "monitoring", "Grafana", "Prometheus", "latency", "reliability"],
    "ignore_patterns": ["**/rag_*", "**/achievement_*", "**/revenue*"],
    "priority_services": ["orchestrator", "celery_worker", "persona_runtime"],
    "job_targets": ["MLOps Engineer", "Platform Engineer", "SRE"],
    "proof_items": ["mlflow_demo", "slo_gates", "monitoring_dashboard"]
}
EOF
}

setup_agent_a2() {
    local WORKTREE_DIR="$1"
    
    echo -e "${BLUE}Setting up Agent A2 - GenAI/RAG${NC}"
    
    cat > "$WORKTREE_DIR/.agent.env" << 'EOF'
# Agent A2 Configuration - GenAI/RAG
export AGENT_ID="a2"
export AGENT_NAME="GenAI"
export AGENT_SERVICES="rag_pipeline vllm_service viral_engine"
export FOCUS_AREAS="vllm,rag,embeddings,token-optimization"
export SKIP_SERVICES="orchestrator achievement_collector revenue"
export PORT_OFFSET=100
export DB_SCHEMA="agent_a2"

# Job Strategy Focus
export JOB_PRIORITY="vLLM optimization, RAG accuracy, Token cost reduction"
export PORTFOLIO_FOCUS="vllm_benchmark.png cost_comparison.xlsx token_usage.png"
EOF
    
    cat > "$WORKTREE_DIR/AGENT_TASKS.md" << 'EOF'
# Agent A2 - GenAI/RAG Tasks

## Primary Responsibilities
- [ ] Deploy vLLM service for cost optimization
- [ ] Implement RAG pipeline with Qdrant
- [ ] Optimize token usage and costs
- [ ] Build semantic search capabilities

## Portfolio Artifacts to Generate
1. **vLLM Benchmark Chart** - Latency vs cost comparison
2. **Cost Comparison Table** - vLLM vs OpenAI/Anthropic
3. **Token Usage Dashboard** - Show 60% cost reduction

## Weekly Goals (for job applications)
- Deploy vLLM with Llama-70B
- Reduce token costs by 60%
- Implement semantic caching
- Create RAG evaluation metrics

## Commands
```bash
just vllm-deploy        # Deploy vLLM service
just token-optimize     # Analyze token usage
just rag-benchmark      # Test RAG accuracy
```
EOF
    
    cat > "$WORKTREE_DIR/.ai-context.json" << 'EOF'
{
    "agent": "a2",
    "focus": "Generative AI and RAG Systems",
    "keywords": ["vLLM", "RAG", "embeddings", "Qdrant", "token", "cost", "Llama", "semantic"],
    "ignore_patterns": ["**/orchestrator*", "**/achievement_*", "**/revenue*"],
    "priority_services": ["rag_pipeline", "vllm_service", "viral_engine"],
    "job_targets": ["GenAI Engineer", "LLM Specialist", "AI/ML Engineer"],
    "proof_items": ["vllm_cost_reduction", "rag_accuracy", "token_optimization"]
}
EOF
}

setup_agent_a3() {
    local WORKTREE_DIR="$1"
    
    echo -e "${BLUE}Setting up Agent A3 - Analytics/Documentation${NC}"
    
    cat > "$WORKTREE_DIR/.agent.env" << 'EOF'
# Agent A3 Configuration - Analytics/Documentation
export AGENT_ID="a3"
export AGENT_NAME="Analytics"
export AGENT_SERVICES="achievement_collector tech_doc_generator dashboard_api"
export FOCUS_AREAS="portfolio,documentation,achievements,visualization"
export SKIP_SERVICES="orchestrator rag_pipeline revenue"
export PORT_OFFSET=200
export DB_SCHEMA="agent_a3"

# Job Strategy Focus
export JOB_PRIORITY="Portfolio generation, Achievement tracking, Documentation"
export PORTFOLIO_FOCUS="achievement_report.pdf documentation.md portfolio_site.png"
EOF
    
    cat > "$WORKTREE_DIR/AGENT_TASKS.md" << 'EOF'
# Agent A3 - Analytics/Documentation Tasks

## Primary Responsibilities
- [ ] Collect and visualize PR achievements
- [ ] Generate technical documentation
- [ ] Build portfolio website
- [ ] Create data visualizations

## Portfolio Artifacts to Generate
1. **Achievement Report PDF** - Quantified impact from PRs
2. **Technical Documentation** - Architecture and decisions
3. **Portfolio Website** - Interactive showcase

## Weekly Goals (for job applications)
- Process 20+ PRs for achievements
- Generate 3 technical one-pagers
- Update portfolio website
- Create impact visualizations

## Commands
```bash
just collect-achievements   # Process PR data
just generate-docs         # Create documentation
just portfolio-site        # Build portfolio
```
EOF
    
    cat > "$WORKTREE_DIR/.ai-context.json" << 'EOF'
{
    "agent": "a3",
    "focus": "Analytics and Documentation",
    "keywords": ["portfolio", "achievements", "documentation", "visualization", "impact", "metrics"],
    "ignore_patterns": ["**/orchestrator*", "**/rag_*", "**/revenue*"],
    "priority_services": ["achievement_collector", "tech_doc_generator", "dashboard_api"],
    "job_targets": ["Technical Writer", "Data Analyst", "Developer Advocate"],
    "proof_items": ["portfolio_website", "achievement_metrics", "documentation"]
}
EOF
}

setup_agent_a4() {
    local WORKTREE_DIR="$1"
    
    echo -e "${BLUE}Setting up Agent A4 - Platform/Revenue${NC}"
    
    cat > "$WORKTREE_DIR/.agent.env" << 'EOF'
# Agent A4 Configuration - Platform/Revenue
export AGENT_ID="a4"
export AGENT_NAME="Platform"
export AGENT_SERVICES="revenue finops_engine event_bus threads_adaptor"
export FOCUS_AREAS="ab-testing,revenue,cost-optimization,platform"
export SKIP_SERVICES="orchestrator rag_pipeline achievement_collector"
export PORT_OFFSET=300
export DB_SCHEMA="agent_a4"

# Job Strategy Focus
export JOB_PRIORITY="A/B testing, Revenue optimization, FinOps, Platform scaling"
export PORTFOLIO_FOCUS="ab_test_results.png revenue_dashboard.png cost_analysis.xlsx"
EOF
    
    cat > "$WORKTREE_DIR/AGENT_TASKS.md" << 'EOF'
# Agent A4 - Platform/Revenue Tasks

## Primary Responsibilities
- [ ] Implement A/B testing framework
- [ ] Build revenue tracking system
- [ ] Optimize platform costs (FinOps)
- [ ] Create event-driven architecture

## Portfolio Artifacts to Generate
1. **A/B Test Results** - Show statistical significance
2. **Revenue Dashboard** - MRR, CAC, LTV metrics
3. **Cost Analysis** - AWS/K8s optimization savings

## Weekly Goals (for job applications)
- Run 3 A/B tests with significance
- Track $20k MRR progress
- Reduce infrastructure costs 30%
- Implement event sourcing

## Commands
```bash
just ab-test-run        # Execute A/B test
just revenue-metrics    # Show revenue KPIs
just finops-report      # Cost optimization report
```
EOF
    
    cat > "$WORKTREE_DIR/.ai-context.json" << 'EOF'
{
    "agent": "a4",
    "focus": "Platform Engineering and Revenue",
    "keywords": ["A/B testing", "revenue", "MRR", "CAC", "FinOps", "event-driven", "platform"],
    "ignore_patterns": ["**/orchestrator*", "**/rag_*", "**/achievement_*"],
    "priority_services": ["revenue", "finops_engine", "event_bus", "threads_adaptor"],
    "job_targets": ["Platform Engineer", "Growth Engineer", "FinOps Engineer"],
    "proof_items": ["ab_testing", "revenue_metrics", "cost_optimization"]
}
EOF
}

# ═══════════════════════════════════════════════════════
# Main Setup Function
# ═══════════════════════════════════════════════════════

main() {
    echo "Creating differentiated agent worktrees..."
    
    # Base directory (one level up)
    BASE_DIR="$(dirname "$PROJECT_ROOT")"
    
    # Set up each worktree
    for agent in a1 a2 a3 a4; do
        case $agent in
            a1) 
                WORKTREE="wt-a1-mlops"
                setup_func="setup_agent_a1"
                ;;
            a2) 
                WORKTREE="wt-a2-genai"
                setup_func="setup_agent_a2"
                ;;
            a3) 
                WORKTREE="wt-a3-analytics"
                setup_func="setup_agent_a3"
                ;;
            a4) 
                WORKTREE="wt-a4-platform"
                setup_func="setup_agent_a4"
                ;;
        esac
        
        WORKTREE_PATH="$BASE_DIR/$WORKTREE"
        
        # Create worktree if it doesn't exist
        if [[ ! -d "$WORKTREE_PATH" ]]; then
            echo "Creating worktree: $WORKTREE"
            git worktree add "$WORKTREE_PATH" -b "agent-$agent-work"
        fi
        
        # Set up agent-specific configuration
        $setup_func "$WORKTREE_PATH"
        
        echo -e "${GREEN}✅ Configured $WORKTREE${NC}"
    done
    
    # Create coordination file
    cat > "$BASE_DIR/.agent-coordination.md" << 'EOF'
# Agent Coordination & Communication

## Agent Responsibilities

| Agent | Focus | Services | Portfolio Priority |
|-------|-------|----------|-------------------|
| A1 | MLOps | orchestrator, celery, persona | MLflow, SLO gates |
| A2 | GenAI | RAG, vLLM, viral | Cost optimization, vLLM |
| A3 | Analytics | achievements, docs | Portfolio, documentation |
| A4 | Platform | revenue, finops, events | A/B testing, revenue |

## Coordination Rules

1. **File Locks**: Check `.locks/` before editing shared files
2. **Database**: Only A1 modifies schema (Alembic owner)
3. **Branches**: Use `feat/<agent>/<feature>` naming
4. **PRs**: Tag with `[A1]`, `[A2]`, etc.
5. **Daily Sync**: Check `.agent-coordination.log`

## Communication

- Async: Use `.agent-coordination.log`
- Urgent: Create issue with `@agent-X` mention
- Blockers: Add to `BLOCKERS.md`
EOF
    
    echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ All 4 Agent Worktrees Configured!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    
    echo -e "\n${YELLOW}Next Steps for Each Warp Window:${NC}"
    echo ""
    echo "Window 1 (A1 - MLOps):"
    echo "  cd $BASE_DIR/wt-a1-mlops"
    echo "  source .agent.env"
    echo "  just ai-morning"
    echo ""
    echo "Window 2 (A2 - GenAI):"
    echo "  cd $BASE_DIR/wt-a2-genai"
    echo "  source .agent.env"
    echo "  just ai-morning"
    echo ""
    echo "Window 3 (A3 - Analytics):"
    echo "  cd $BASE_DIR/wt-a3-analytics"
    echo "  source .agent.env"
    echo "  just ai-morning"
    echo ""
    echo "Window 4 (A4 - Platform):"
    echo "  cd $BASE_DIR/wt-a4-platform"
    echo "  source .agent.env"
    echo "  just ai-morning"
}

# Run setup
main "$@"