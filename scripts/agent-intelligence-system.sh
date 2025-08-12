#!/bin/bash

# Enhanced Agent Intelligence System - Integrates ALL existing AI systems
# for the 4-agent parallel development workflow

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source existing intelligent systems
source "$SCRIPT_DIR/workflow-automation.sh" 2>/dev/null || true
source "$SCRIPT_DIR/learning-system.sh" 2>/dev/null || true
source "$SCRIPT_DIR/ai-epic-planner.sh" 2>/dev/null || true
source "$SCRIPT_DIR/auto-git-integration.sh" 2>/dev/null || true
source "$SCRIPT_DIR/business-intelligence.sh" 2>/dev/null || true
source "$SCRIPT_DIR/customer-intelligence.sh" 2>/dev/null || true

# Agent configuration
source .agent.env 2>/dev/null || true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Enhanced logging
log_ai() { echo -e "${PURPLE}[AI-${AGENT_ID}]${NC} $*"; }
log_insight() { echo -e "${CYAN}[INSIGHT]${NC} $*"; }
log_recommend() { echo -e "${YELLOW}[RECOMMEND]${NC} $*"; }

# ═══════════════════════════════════════════════════════
# AI-Powered Task Planning for Agent
# ═══════════════════════════════════════════════════════

agent_ai_plan() {
    local requirement="$1"
    
    log_ai "Planning tasks for Agent $AGENT_ID ($AGENT_NAME)"
    
    # Use existing AI epic planner with agent context
    AGENT_CONTEXT="Agent: $AGENT_ID
Focus: $FOCUS_AREAS
Services: $AGENT_SERVICES
Constraints: Only work on assigned services, ignore $SKIP_SERVICES"
    
    # Call the existing AI planner
    if [[ -f "$SCRIPT_DIR/workflow-automation.sh" ]]; then
        "$SCRIPT_DIR/workflow-automation.sh" ai-plan "$requirement" --context "$AGENT_CONTEXT"
    fi
    
    # Filter tasks for this agent
    filter_tasks_for_agent
}

# ═══════════════════════════════════════════════════════
# Learning System Integration
# ═══════════════════════════════════════════════════════

agent_learn() {
    log_ai "Analyzing patterns for Agent $AGENT_ID"
    
    # Initialize learning system if needed
    if [[ -f "$SCRIPT_DIR/learning-system.sh" ]]; then
        init_learning_system
        
        # Track agent-specific patterns
        "$SCRIPT_DIR/learning-system.sh" analyze-patterns \
            --agent "$AGENT_ID" \
            --services "$AGENT_SERVICES" \
            --focus "$FOCUS_AREAS"
        
        # Get recommendations
        local recommendations=$("$SCRIPT_DIR/learning-system.sh" get-suggestions \
            --agent "$AGENT_ID" \
            --context "parallel-development")
        
        if [[ -n "$recommendations" ]]; then
            log_recommend "Personalized recommendations for Agent $AGENT_ID:"
            echo "$recommendations"
        fi
    fi
}

# ═══════════════════════════════════════════════════════
# Smart Task Assignment Based on Agent Expertise
# ═══════════════════════════════════════════════════════

assign_tasks_intelligently() {
    log_ai "Intelligently assigning tasks to Agent $AGENT_ID"
    
    # Get all pending tasks
    local pending_tasks=$(find "$WORKFLOW_DIR/tasks" -name "*.yaml" 2>/dev/null | \
        xargs grep -l "status: pending" 2>/dev/null || true)
    
    local assigned_count=0
    
    for task_file in $pending_tasks; do
        # Check if task matches agent's expertise
        if task_matches_agent "$task_file"; then
            # Assign to this agent
            sed -i '' "s/assigned_agent: .*/assigned_agent: $AGENT_ID/" "$task_file"
            sed -i '' "s/status: pending/status: assigned/" "$task_file"
            
            local task_name=$(grep "name:" "$task_file" | cut -d'"' -f2)
            log_success "Assigned task: $task_name"
            ((assigned_count++))
        fi
    done
    
    log_ai "Assigned $assigned_count tasks to Agent $AGENT_ID"
}

# Check if task matches agent's expertise
task_matches_agent() {
    local task_file="$1"
    local task_content=$(cat "$task_file")
    
    # Check for service matches
    for service in $AGENT_SERVICES; do
        if echo "$task_content" | grep -q "$service"; then
            return 0
        fi
    done
    
    # Check for focus area matches
    IFS=',' read -ra FOCUS_ARRAY <<< "$FOCUS_AREAS"
    for focus in "${FOCUS_ARRAY[@]}"; do
        if echo "$task_content" | grep -qi "$focus"; then
            return 0
        fi
    done
    
    return 1
}

# ═══════════════════════════════════════════════════════
# Business Intelligence Integration
# ═══════════════════════════════════════════════════════

agent_business_metrics() {
    log_ai "Generating business metrics for Agent $AGENT_ID"
    
    if [[ -f "$SCRIPT_DIR/business-intelligence.sh" ]]; then
        # Get agent-specific metrics
        "$SCRIPT_DIR/business-intelligence.sh" analyze \
            --agent "$AGENT_ID" \
            --services "$AGENT_SERVICES" \
            --output "$WORKFLOW_DIR/metrics/agent_${AGENT_ID}_metrics.json"
        
        # Show key metrics
        local velocity=$(jq -r '.velocity' "$WORKFLOW_DIR/metrics/agent_${AGENT_ID}_metrics.json" 2>/dev/null || echo "N/A")
        local quality=$(jq -r '.quality_score' "$WORKFLOW_DIR/metrics/agent_${AGENT_ID}_metrics.json" 2>/dev/null || echo "N/A")
        local value=$(jq -r '.business_value' "$WORKFLOW_DIR/metrics/agent_${AGENT_ID}_metrics.json" 2>/dev/null || echo "N/A")
        
        echo ""
        echo "📊 Agent $AGENT_ID Metrics:"
        echo "  Velocity: $velocity tasks/day"
        echo "  Quality: $quality%"
        echo "  Business Value: $value"
    fi
}

# ═══════════════════════════════════════════════════════
# Intelligent Daily Routine
# ═══════════════════════════════════════════════════════

agent_morning_intelligence() {
    log_ai "Running intelligent morning routine for Agent $AGENT_ID"
    
    echo "═══════════════════════════════════════════════════════"
    echo "🤖 AI-Powered Morning Brief for Agent $AGENT_ID"
    echo "═══════════════════════════════════════════════════════"
    
    # 1. Learn from yesterday
    log_ai "Analyzing yesterday's patterns..."
    agent_learn
    
    # 2. Get intelligent task assignment
    log_ai "Intelligently assigning today's tasks..."
    assign_tasks_intelligently
    
    # 3. Generate AI plan for complex tasks
    if [[ -f "$WORKFLOW_DIR/complex_requirements.txt" ]]; then
        while IFS= read -r requirement; do
            agent_ai_plan "$requirement"
        done < "$WORKFLOW_DIR/complex_requirements.txt"
    fi
    
    # 4. Show business metrics
    agent_business_metrics
    
    # 5. Get trend insights
    if [[ -f "$SCRIPT_DIR/trend-detection-workflow.sh" ]]; then
        log_ai "Detecting trends in your domain..."
        "$SCRIPT_DIR/trend-detection-workflow.sh" detect \
            --services "$AGENT_SERVICES" \
            --limit 3
    fi
    
    # 6. Quality gates check
    if [[ -f "$SCRIPT_DIR/quality-gates.sh" ]]; then
        log_ai "Checking quality gates..."
        "$SCRIPT_DIR/quality-gates.sh" check --agent "$AGENT_ID"
    fi
    
    # 7. Show prioritized task list
    show_prioritized_tasks
    
    echo "═══════════════════════════════════════════════════════"
    echo "✅ Agent $AGENT_ID ready with AI assistance!"
    echo "═══════════════════════════════════════════════════════"
}

# ═══════════════════════════════════════════════════════
# Smart Task Prioritization
# ═══════════════════════════════════════════════════════

show_prioritized_tasks() {
    log_ai "Prioritizing tasks based on business value and dependencies"
    
    echo ""
    echo "📋 Today's Prioritized Tasks:"
    echo "────────────────────────────"
    
    # Get tasks with scoring
    local tasks_with_scores=$(mktemp)
    
    # Find agent's tasks and score them
    find "$WORKFLOW_DIR/tasks" -name "*.yaml" 2>/dev/null | while read task_file; do
        if grep -q "assigned_agent: $AGENT_ID" "$task_file" 2>/dev/null; then
            local task_name=$(grep "name:" "$task_file" | cut -d'"' -f2)
            local priority=$(grep "priority:" "$task_file" | cut -d'"' -f2 || echo "medium")
            local effort=$(grep "effort:" "$task_file" | cut -d'"' -f2 || echo "medium")
            local value=$(grep "business_value:" "$task_file" | cut -d':' -f2 || echo "0")
            
            # Calculate score (higher is better)
            local score=0
            [[ "$priority" == "high" ]] && score=$((score + 10))
            [[ "$priority" == "medium" ]] && score=$((score + 5))
            [[ "$effort" == "small" ]] && score=$((score + 5))
            [[ "$effort" == "medium" ]] && score=$((score + 3))
            
            echo "$score|$task_name|$priority|$effort" >> "$tasks_with_scores"
        fi
    done
    
    # Sort and display
    if [[ -f "$tasks_with_scores" ]]; then
        sort -rn "$tasks_with_scores" | head -10 | while IFS='|' read score name priority effort; do
            echo "  🎯 [$priority] $name (effort: $effort)"
        done
    else
        echo "  No tasks assigned yet"
    fi
    
    rm -f "$tasks_with_scores"
}

# ═══════════════════════════════════════════════════════
# Auto-commit with AI-generated messages
# ═══════════════════════════════════════════════════════

agent_smart_commit() {
    log_ai "Generating intelligent commit message..."
    
    # Get changes summary
    local changes=$(git diff --cached --stat)
    local files_changed=$(git diff --cached --name-only | head -5)
    
    # Generate commit message using AI context
    local commit_msg="[$AGENT_ID] "
    
    # Analyze changes to determine type
    if echo "$files_changed" | grep -q "test"; then
        commit_msg+="test: "
    elif echo "$files_changed" | grep -q "fix"; then
        commit_msg+="fix: "
    elif echo "$files_changed" | grep -q "docs"; then
        commit_msg+="docs: "
    else
        commit_msg+="feat: "
    fi
    
    # Add intelligent description based on files
    local primary_service=$(echo "$files_changed" | grep "services/" | head -1 | cut -d'/' -f2)
    if [[ -n "$primary_service" ]]; then
        commit_msg+="update $primary_service"
    else
        commit_msg+="update $(echo "$files_changed" | head -1 | xargs basename)"
    fi
    
    # Add stats
    local num_files=$(echo "$files_changed" | wc -l)
    commit_msg+=" ($num_files files)"
    
    git commit -m "$commit_msg"
    log_success "Committed with message: $commit_msg"
}

# ═══════════════════════════════════════════════════════
# Performance Analytics
# ═══════════════════════════════════════════════════════

agent_performance() {
    log_ai "Analyzing Agent $AGENT_ID performance..."
    
    if [[ -f "$SCRIPT_DIR/show_performance_metrics.py" ]]; then
        python3 "$SCRIPT_DIR/show_performance_metrics.py" \
            --agent "$AGENT_ID" \
            --period "week"
    fi
    
    # Show git activity
    echo ""
    echo "📈 This Week's Activity:"
    git log --author="$USER" --since="1 week ago" --oneline | \
        grep "\[$AGENT_ID\]" | wc -l | \
        xargs -I {} echo "  Commits: {}"
    
    # Show test coverage if available
    if [[ -f "coverage.xml" ]]; then
        local coverage=$(grep 'line-rate' coverage.xml | head -1 | sed 's/.*line-rate="\([^"]*\)".*/\1/')
        echo "  Test Coverage: ${coverage}%"
    fi
}

# ═══════════════════════════════════════════════════════
# Main Intelligence Command
# ═══════════════════════════════════════════════════════

case "${1:-help}" in
    morning)
        agent_morning_intelligence
        ;;
    learn)
        agent_learn
        ;;
    plan)
        agent_ai_plan "${2:-}"
        ;;
    assign)
        assign_tasks_intelligently
        ;;
    metrics)
        agent_business_metrics
        ;;
    commit)
        agent_smart_commit
        ;;
    performance)
        agent_performance
        ;;
    help)
        echo "Agent Intelligence System - Commands:"
        echo "  morning     - Run intelligent morning routine"
        echo "  learn       - Learn from patterns and get recommendations"
        echo "  plan <req>  - AI-powered task planning"
        echo "  assign      - Intelligently assign tasks"
        echo "  metrics     - Show business metrics"
        echo "  commit      - Smart commit with AI message"
        echo "  performance - Show performance analytics"
        ;;
esac