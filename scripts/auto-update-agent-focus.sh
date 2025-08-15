#!/bin/bash

# Auto-update AGENT_FOCUS.md based on actual development activity
# Uses learning system data + git history + current state

set -e

AGENT_ID=${AGENT_ID:-"main-dev"}
FOCUS_FILE="AGENT_FOCUS.md"
LEARNING_DIR=".learning"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${BLUE}[FOCUS-AUTO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[SMART]${NC} $1"; }

# Analyze today's development activity
analyze_todays_work() {
    local today=$(date +%Y-%m-%d)
    local yesterday=$(date -d "1 day ago" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
    
    # Git activity analysis
    local commits_today=$(git log --since="$today 00:00:00" --oneline | wc -l)
    local files_changed=$(git log --since="$today 00:00:00" --name-only --pretty=format: | sort -u | grep -v "^$" | wc -l)
    local top_areas=$(git log --since="$today 00:00:00" --name-only --pretty=format: | sort | uniq -c | sort -nr | head -3 | awk '{print $2}' | cut -d'/' -f1-2 | sort -u)
    
    # Learning system insights
    local recent_commands=""
    local success_rate=100
    if [[ -f "$LEARNING_DIR/analytics/commands.log" ]]; then
        recent_commands=$(tail -20 "$LEARNING_DIR/analytics/commands.log" 2>/dev/null | grep "$today" | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -3 | awk '{print $2}' | tr '\n' ' ')
        local failures=$(tail -50 "$LEARNING_DIR/analytics/failures.log" 2>/dev/null | grep "$today" | wc -l || echo "0")
        local total=$(tail -50 "$LEARNING_DIR/analytics/commands.log" 2>/dev/null | grep "$today" | wc -l || echo "1")
        success_rate=$(echo "scale=0; (($total - $failures) * 100) / $total" | bc -l 2>/dev/null || echo "100")
    fi
    
    # Current branch context
    local current_branch=$(git branch --show-current)
    local branch_type="maintenance"
    case "$current_branch" in
        feat/*|feature/*) branch_type="feature development" ;;
        fix/*|bugfix/*) branch_type="bug fixing" ;;
        refactor/*) branch_type="code refactoring" ;;
        docs/*) branch_type="documentation" ;;
        test/*) branch_type="testing" ;;
        *) branch_type="general development" ;;
    esac
    
    # Outstanding TODOs and FIXMEs
    local todo_count=$(grep -r "TODO\|FIXME\|XXX" . --include="*.py" --include="*.js" --include="*.ts" 2>/dev/null | wc -l || echo "0")
    
    # Current quality issues
    local quality_issues=""
    if command -v ruff >/dev/null 2>&1; then
        quality_issues=$(ruff check . --quiet 2>/dev/null | wc -l || echo "0")
    fi
    
    # Package current analysis
    cat > .daily-analysis.json << EOF
{
    "date": "$today",
    "activity": {
        "commits": $commits_today,
        "files_changed": $files_changed,
        "top_areas": [$(echo "$top_areas" | sed 's/^/"/g' | sed 's/$/"/g' | tr '\n' ',' | sed 's/,$//')],
        "branch_type": "$branch_type",
        "current_branch": "$current_branch"
    },
    "learning": {
        "recent_commands": [$(echo "$recent_commands" | sed 's/ /","/g' | sed 's/^/"/g' | sed 's/$/"/g')],
        "success_rate": $success_rate
    },
    "quality": {
        "todo_count": $todo_count,
        "quality_issues": $quality_issues
    }
}
EOF
    
    log "📊 Today's analysis: $commits_today commits, $files_changed files, ${success_rate}% success rate"
}

# Generate smart goals based on activity
generate_smart_goals() {
    local analysis=$(cat .daily-analysis.json)
    local commits=$(echo "$analysis" | jq -r '.activity.commits')
    local quality_issues=$(echo "$analysis" | jq -r '.quality.quality_issues')
    local branch_type=$(echo "$analysis" | jq -r '.activity.branch_type')
    local success_rate=$(echo "$analysis" | jq -r '.learning.success_rate')
    
    local goals=""
    
    # Activity-based goals
    if [[ $commits -gt 5 ]]; then
        goals="$goals\n- Maintain high development velocity (${commits} commits today)"
    elif [[ $commits -gt 0 ]]; then
        goals="$goals\n- Continue focused development work"
    else
        goals="$goals\n- Begin active development session"
    fi
    
    # Quality-based goals
    if [[ $quality_issues -gt 10 ]]; then
        goals="$goals\n- Address code quality issues ($quality_issues lint issues)"
    elif [[ $quality_issues -gt 0 ]]; then
        goals="$goals\n- Clean up minor quality issues ($quality_issues remaining)"
    fi
    
    # Branch-specific goals
    case "$branch_type" in
        "feature development")
            goals="$goals\n- Complete feature implementation and testing" ;;
        "bug fixing")
            goals="$goals\n- Resolve bugs and improve system reliability" ;;
        "code refactoring")
            goals="$goals\n- Improve code structure and maintainability" ;;
    esac
    
    # Performance-based goals
    if [[ $success_rate -lt 90 ]]; then
        goals="$goals\n- Improve development success rate (currently ${success_rate}%)"
    fi
    
    # Learning system integration
    goals="$goals\n- Leverage AI acceleration tools for productivity"
    
    echo -e "$goals"
}

# Generate smart blockers/issues
generate_current_issues() {
    local analysis=$(cat .daily-analysis.json)
    local quality_issues=$(echo "$analysis" | jq -r '.quality.quality_issues')
    local todo_count=$(echo "$analysis" | jq -r '.quality.todo_count')
    local success_rate=$(echo "$analysis" | jq -r '.learning.success_rate')
    
    local issues=""
    
    # Quality issues
    if [[ $quality_issues -gt 0 ]]; then
        issues="$issues\n- Code quality: $quality_issues linting issues need attention"
    fi
    
    # TODO backlog
    if [[ $todo_count -gt 20 ]]; then
        issues="$issues\n- Technical debt: $todo_count TODO/FIXME items in codebase"
    fi
    
    # Success rate issues
    if [[ $success_rate -lt 85 ]]; then
        issues="$issues\n- Development efficiency: ${success_rate}% success rate indicates process issues"
    fi
    
    # Check for test failures (last quality gate)
    if [[ -f ".dev-insights.json" ]]; then
        local last_quality=$(jq -r '.ai_acceleration.quality_gates_enabled // false' .dev-insights.json 2>/dev/null)
        if [[ "$last_quality" == "false" ]]; then
            issues="$issues\n- Quality gates: Last run detected failures"
        fi
    fi
    
    # Check for stale branches
    local branch_age=$(git log -1 --format=%ct 2>/dev/null || echo $(date +%s))
    local days_old=$(echo "($(date +%s) - $branch_age) / 86400" | bc 2>/dev/null || echo "0")
    if [[ $days_old -gt 3 ]]; then
        issues="$issues\n- Branch staleness: Current branch is $days_old days old"
    fi
    
    if [[ -z "$issues" ]]; then
        issues="\n- No significant blockers identified"
    fi
    
    echo -e "$issues"
}

# Generate next session priorities
generate_next_priorities() {
    local analysis=$(cat .daily-analysis.json)
    local branch_type=$(echo "$analysis" | jq -r '.activity.branch_type')
    local quality_issues=$(echo "$analysis" | jq -r '.quality.quality_issues')
    
    local priorities=""
    
    # Priority 1: Quality first
    if [[ $quality_issues -gt 0 ]]; then
        priorities="1. Run \`just lint --fix\` to resolve $quality_issues code quality issues"
    else
        priorities="1. Continue development with clean quality baseline"
    fi
    
    # Priority 2: Branch-specific work
    case "$branch_type" in
        "feature development")
            priorities="$priorities\n2. Complete feature testing and documentation" ;;
        "bug fixing")
            priorities="$priorities\n2. Verify bug fixes and add regression tests" ;;
        "code refactoring")
            priorities="$priorities\n2. Validate refactoring with comprehensive tests" ;;
        *)
            priorities="$priorities\n2. Plan next development milestone" ;;
    esac
    
    # Priority 3: AI acceleration usage
    priorities="$priorities\n3. Use \`just dev-boost\` to accelerate development workflow"
    
    # Priority 4: Learning system integration
    priorities="$priorities\n4. Review learning insights with \`just dev-insights\`"
    
    echo -e "$priorities"
}

# Update AGENT_FOCUS.md with smart content
update_focus_file() {
    local backup_file="${FOCUS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Backup current file
    if [[ -f "$FOCUS_FILE" ]]; then
        cp "$FOCUS_FILE" "$backup_file"
        log "📋 Backup created: $backup_file"
    fi
    
    # Analyze current state
    analyze_todays_work
    
    # Generate smart content
    local smart_goals=$(generate_smart_goals)
    local current_issues=$(generate_current_issues)
    local next_priorities=$(generate_next_priorities)
    local update_timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Preserve existing static content and update dynamic sections
    cat > "$FOCUS_FILE" << EOF
# Agent Focus Areas

## Current Sprint Goals
- Implement AI development acceleration system
- Integrate learning system with development workflows
- Optimize 4-agent parallel development process
- Build portfolio automation for US remote AI roles

## Technical Specialization
- MLOps and AI system optimization
- Development workflow automation
- Performance monitoring and metrics
- AI-powered tooling integration

## Current Priorities
1. **AI Development Acceleration**: Complete integration of top AI company practices
2. **Learning System Enhancement**: Leverage existing analytics for development insights
3. **Quality Gates**: Implement automated quality checking workflows
4. **Portfolio Integration**: Connect achievement collector with development metrics

## Focus Keywords
- AI development acceleration
- Learning system integration
- Development workflow optimization
- Quality automation
- Performance metrics

## Success Criteria
- 60% faster development cycles
- Automated quality gates operational
- Learning system providing actionable insights
- Portfolio automatically updated with achievements

## Current Context (Auto-Updated: $update_timestamp)
### Today's Goals$smart_goals

### Current Issues/Blockers$current_issues

### Next Session Priorities
$next_priorities

## Technologies in Use
- Python 3.13, FastAPI, Celery
- Kubernetes, k3d, Helm
- Ruff (linting), pytest (testing)
- AI tools: OpenAI API, Claude Code
- Learning system: custom analytics

---
*Auto-updated by smart focus system based on development activity*
EOF
    
    success "✨ AGENT_FOCUS.md updated with smart insights"
    warn "📈 Based on: $(cat .daily-analysis.json | jq -r '.activity.commits') commits, $(cat .daily-analysis.json | jq -r '.learning.success_rate')% success rate"
}

# Main execution
main() {
    log "🤖 Smart Agent Focus Update starting..."
    
    # Ensure we're in git repo
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "❌ Not in a git repository"
        exit 1
    fi
    
    # Update focus file with smart analysis
    update_focus_file
    
    # Clean up temporary files
    rm -f .daily-analysis.json
    
    # Optionally reload AI context
    if [[ "${1:-}" == "--reload-context" ]]; then
        log "🧠 Reloading AI context with updated focus..."
        export AGENT_ID="$AGENT_ID"
        ./scripts/ai-dev-acceleration.sh context
    fi
    
    success "🎯 Smart focus update complete!"
}

main "$@"