#!/bin/bash
# Auto-generate PRs with portfolio impact for job applications

set -euo pipefail
source .agent.env 2>/dev/null || true

create_portfolio_pr() {
    local title="$1"
    local body=""
    
    # Add portfolio impact based on agent
    case "$AGENT_ID" in
        a1)
            body="## MLOps Portfolio Impact
- ✅ Demonstrates SLO-gated CI/CD
- ✅ Shows MLflow integration 
- ✅ Proves <500ms p95 latency

**Job Relevance**: MLOps Engineer, Platform Engineer
**Salary Range**: \$160-180k"
            ;;
        a2)
            body="## GenAI Portfolio Impact  
- ✅ Shows 60% cost reduction with vLLM
- ✅ Demonstrates RAG pipeline
- ✅ Proves token optimization

**Job Relevance**: GenAI Engineer, LLM Specialist
**Salary Range**: \$170-190k"
            ;;
        a3)
            body="## Analytics Portfolio Impact
- ✅ Adds to achievement collection
- ✅ Enhances documentation
- ✅ Builds portfolio site

**Job Relevance**: Technical Writer, Developer Advocate"
            ;;
        a4)
            body="## Platform Portfolio Impact
- ✅ Shows A/B testing capability
- ✅ Demonstrates revenue tracking
- ✅ Proves FinOps savings

**Job Relevance**: Platform Engineer, Growth Engineer
**Salary Range**: \$170-190k"
            ;;
    esac
    
    # Add metrics if available
    if [[ -f ".metrics/latest_slo.json" ]]; then
        body="$body

## Real Metrics
$(cat .metrics/latest_slo.json | jq -r '"\(.p95_latency)ms p95, \(.error_rate)% errors"')"
    fi
    
    # Create PR with portfolio context
    gh pr create \
        --title "[$AGENT_ID] $title" \
        --body "$body" \
        --label "portfolio-artifact,agent-$AGENT_ID"
}

# Usage
create_portfolio_pr "${1:-Feature implementation}"