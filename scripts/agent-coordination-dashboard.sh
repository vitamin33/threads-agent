#!/bin/bash
# Real-time coordination dashboard for 4 agents

set -euo pipefail

show_dashboard() {
    clear
    echo "════════════════════════════════════════════════════════════════"
    echo "              🚀 4-AGENT COORDINATION DASHBOARD"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    # Show each agent's status
    for agent in a1 a2 a3 a4; do
        show_agent_status "$agent"
    done
    
    echo "════════════════════════════════════════════════════════════════"
    echo "                    📊 PORTFOLIO PROGRESS"
    echo "════════════════════════════════════════════════════════════════"
    
    # Overall portfolio status
    local total_artifacts=$(ls .portfolio/*.{png,mp4,pdf,xlsx} 2>/dev/null | wc -l)
    local job_apps=$(find .job-tracker -name "*.json" 2>/dev/null | wc -l)
    
    echo "Portfolio Artifacts: $total_artifacts / 12 target"
    echo "Job Applications: $job_apps ($(find .job-tracker -name "*.json" -mtime -7 | wc -l) this week)"
    echo ""
    
    # Show coordination locks
    echo "🔒 Coordination Locks:"
    if [[ -d ".locks" ]]; then
        ls .locks/ 2>/dev/null | head -5 || echo "  No active locks"
    else
        echo "  No locks directory"
    fi
    
    echo ""
    echo "Press Ctrl+C to exit, refreshes every 30s..."
}

show_agent_status() {
    local agent="$1"
    local worktree="../wt-${agent}-*"
    
    echo "──────────────────────────────────────────────────────"
    
    # Get agent details
    case $agent in
        a1)
            echo "👤 Agent A1 - MLOps/Orchestrator"
            local services="orchestrator, celery_worker"
            local focus="MLflow, SLO gates"
            ;;
        a2)
            echo "👤 Agent A2 - GenAI/RAG"
            local services="rag_pipeline, vllm_service"
            local focus="vLLM, cost optimization"
            ;;
        a3)
            echo "👤 Agent A3 - Analytics/Docs"
            local services="achievement_collector"
            local focus="Portfolio, documentation"
            ;;
        a4)
            echo "👤 Agent A4 - Platform/Revenue"
            local services="revenue, finops_engine"
            local focus="A/B testing, revenue"
            ;;
    esac
    
    echo "Services: $services"
    echo "Focus: $focus"
    
    # Check if worktree exists and get status
    if [[ -d $worktree ]]; then
        cd $worktree 2>/dev/null && {
            # Get current branch
            local branch=$(git branch --show-current 2>/dev/null || echo "unknown")
            echo "Branch: $branch"
            
            # Count today's commits
            local commits_today=$(git log --since="midnight" --oneline 2>/dev/null | wc -l)
            echo "Commits today: $commits_today"
            
            # Check for uncommitted changes
            local changes=$(git status --porcelain 2>/dev/null | wc -l)
            [[ $changes -gt 0 ]] && echo "⚠️  Uncommitted changes: $changes files"
            
            # Check AGENT_FOCUS.md for current task
            if [[ -f "AGENT_FOCUS.md" ]]; then
                local current_task=$(grep -A 1 "Today's Focus" AGENT_FOCUS.md 2>/dev/null | grep "- \[ \]" | head -1)
                [[ -n "$current_task" ]] && echo "Current: ${current_task:6}"
            fi
            
            cd - > /dev/null
        } || echo "❌ Worktree not accessible"
    else
        echo "❌ Worktree not found"
    fi
    
    echo ""
}

# Run dashboard with auto-refresh
while true; do
    show_dashboard
    sleep 30
done