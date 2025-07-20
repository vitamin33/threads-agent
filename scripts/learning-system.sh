#!/bin/bash

# scripts/learning-system.sh - AI-powered development learning and optimization system
# Tracks patterns, analyzes workflows, and provides intelligent suggestions

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LEARNING_DIR="$PROJECT_ROOT/.learning"
ANALYTICS_DIR="$LEARNING_DIR/analytics"
PATTERNS_DIR="$LEARNING_DIR/patterns"
SUGGESTIONS_DIR="$LEARNING_DIR/suggestions"
MODELS_DIR="$LEARNING_DIR/models"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SESSION_ID="${SESSION_ID:-$(date +%s)_$$}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[LEARN]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_insight() { echo -e "${PURPLE}[INSIGHT]${NC} $*"; }
log_suggest() { echo -e "${CYAN}[SUGGEST]${NC} $*"; }

# Initialize learning system
init_learning_system() {
    mkdir -p "$ANALYTICS_DIR" "$PATTERNS_DIR" "$SUGGESTIONS_DIR" "$MODELS_DIR"
    
    # Initialize analytics database files
    touch "$ANALYTICS_DIR/commands.log"
    touch "$ANALYTICS_DIR/workflows.log" 
    touch "$ANALYTICS_DIR/failures.log"
    touch "$ANALYTICS_DIR/successes.log"
    touch "$ANALYTICS_DIR/timings.log"
    touch "$ANALYTICS_DIR/context.log"
    
    # Initialize pattern files
    touch "$PATTERNS_DIR/command_sequences.json"
    touch "$PATTERNS_DIR/timing_patterns.json"
    touch "$PATTERNS_DIR/failure_patterns.json"
    touch "$PATTERNS_DIR/success_patterns.json"
    
    log_info "Learning system initialized"
}

# Helper: Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Helper: Get git context
get_git_context() {
    local context=""
    if git rev-parse --git-dir >/dev/null 2>&1; then
        local branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        local status=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
        local behind=$(git rev-list --count HEAD..@{upstream} 2>/dev/null || echo "0")
        local ahead=$(git rev-list --count @{upstream}..HEAD 2>/dev/null || echo "0")
        context="branch:$branch,changes:$status,behind:$behind,ahead:$ahead"
    fi
    echo "$context"
}

# Helper: Get system context
get_system_context() {
    local context=""
    local load=$(uptime | awk '{print $(NF-2)}' | sed 's/,//')
    local memory=$(free 2>/dev/null | awk '/^Mem:/{printf "%.0f", $3/$2*100}' || echo "unknown")
    local disk=$(df . | awk 'NR==2{print $5}' | sed 's/%//')
    context="load:$load,memory:$memory%,disk:$disk%"
    echo "$context"
}

# Track command execution
track_command() {
    local command="$1"
    local exit_code="${2:-0}"
    local duration="${3:-0}"
    local context="${4:-}"
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local git_ctx=$(get_git_context)
    local sys_ctx=$(get_system_context)
    
    # Log command execution
    echo "$timestamp|$SESSION_ID|$command|$exit_code|$duration|$git_ctx|$sys_ctx|$context" >> "$ANALYTICS_DIR/commands.log"
    
    # Track success/failure
    if [[ $exit_code -eq 0 ]]; then
        echo "$timestamp|$SESSION_ID|$command|$duration|$git_ctx|$context" >> "$ANALYTICS_DIR/successes.log"
        log_success "Command tracked: $command (${duration}s)"
    else
        echo "$timestamp|$SESSION_ID|$command|$exit_code|$git_ctx|$context" >> "$ANALYTICS_DIR/failures.log"
        log_warn "Failure tracked: $command (exit $exit_code)"
    fi
    
    # Track timing patterns
    echo "$timestamp|$command|$duration" >> "$ANALYTICS_DIR/timings.log"
}

# Track workflow sequence
track_workflow() {
    local workflow_name="$1"
    local steps="$2"
    local success="${3:-true}"
    local duration="${4:-0}"
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local git_ctx=$(get_git_context)
    
    echo "$timestamp|$SESSION_ID|$workflow_name|$steps|$success|$duration|$git_ctx" >> "$ANALYTICS_DIR/workflows.log"
    
    if [[ "$success" == "true" ]]; then
        log_success "Workflow tracked: $workflow_name (${duration}s)"
    else
        log_warn "Failed workflow tracked: $workflow_name"
    fi
}

# Analyze command patterns
analyze_command_patterns() {
    log_info "Analyzing command usage patterns..."
    
    if [[ ! -s "$ANALYTICS_DIR/commands.log" ]]; then
        log_warn "No command data available for analysis"
        return 0
    fi
    
    local analysis_file="$PATTERNS_DIR/command_analysis_$TIMESTAMP.json"
    
    # Analyze most used commands
    local top_commands=$(tail -1000 "$ANALYTICS_DIR/commands.log" | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -10)
    
    # Analyze failure rates
    local total_commands=$(tail -1000 "$ANALYTICS_DIR/commands.log" | wc -l)
    local failed_commands=$(tail -1000 "$ANALYTICS_DIR/commands.log" | awk -F'|' '$4 != "0"' | wc -l)
    local failure_rate=$(echo "scale=2; $failed_commands * 100 / $total_commands" | bc -l 2>/dev/null || echo "0")
    
    # Analyze timing patterns
    local avg_duration=$(tail -1000 "$ANALYTICS_DIR/timings.log" | awk -F'|' '{sum+=$3; count++} END {if(count>0) print sum/count; else print 0}')
    
    # Generate JSON analysis
    cat > "$analysis_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "analysis_period": "last_1000_commands",
  "summary": {
    "total_commands": $total_commands,
    "failed_commands": $failed_commands,
    "failure_rate_percent": $failure_rate,
    "avg_duration_seconds": $avg_duration
  },
  "top_commands": [
$(echo "$top_commands" | head -5 | awk '{printf "    {\"command\": \"%s\", \"count\": %d}", $2, $1; if(NR<5) printf ","; printf "\n"}')
  ],
  "insights": [
$(if (( $(echo "$failure_rate > 10" | bc -l 2>/dev/null || echo 0) )); then
    echo '    "High failure rate detected - consider workflow optimization",'
fi)
$(if (( $(echo "$avg_duration > 30" | bc -l 2>/dev/null || echo 0) )); then
    echo '    "Long average command duration - consider performance optimization",'
fi)
    "Analysis complete"
  ]
}
EOF
    
    log_insight "Command analysis saved to: $analysis_file"
    
    # Display key insights
    echo "$top_commands" | head -3 | while read count cmd; do
        log_insight "Top command: '$cmd' used $count times"
    done
    
    if (( $(echo "$failure_rate > 5" | bc -l 2>/dev/null || echo 0) )); then
        log_warn "High failure rate: ${failure_rate}% - consider workflow optimization"
    fi
}

# Analyze workflow patterns
analyze_workflow_patterns() {
    log_info "Analyzing workflow patterns..."
    
    if [[ ! -s "$ANALYTICS_DIR/workflows.log" ]]; then
        log_warn "No workflow data available for analysis"
        return 0
    fi
    
    local patterns_file="$PATTERNS_DIR/workflow_patterns_$TIMESTAMP.json"
    
    # Analyze successful workflows
    local successful_workflows=$(tail -500 "$ANALYTICS_DIR/workflows.log" | awk -F'|' '$5=="true"' | cut -d'|' -f3 | sort | uniq -c | sort -nr)
    
    # Analyze failed workflows
    local failed_workflows=$(tail -500 "$ANALYTICS_DIR/workflows.log" | awk -F'|' '$5=="false"' | cut -d'|' -f3 | sort | uniq -c | sort -nr)
    
    # Analyze workflow timing
    local avg_workflow_time=$(tail -500 "$ANALYTICS_DIR/workflows.log" | awk -F'|' '$5=="true" {sum+=$6; count++} END {if(count>0) print sum/count; else print 0}')
    
    cat > "$patterns_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "successful_workflows": [
$(echo "$successful_workflows" | head -5 | awk '{printf "    {\"workflow\": \"%s\", \"count\": %d}", $2, $1; if(NR<5) printf ","; printf "\n"}')
  ],
  "failed_workflows": [
$(echo "$failed_workflows" | head -3 | awk '{printf "    {\"workflow\": \"%s\", \"count\": %d}", $2, $1; if(NR<3) printf ","; printf "\n"}')
  ],
  "avg_successful_duration": $avg_workflow_time,
  "patterns": [
$(echo "$successful_workflows" | head -1 | awk '{printf "    \"Most reliable workflow: %s (success rate analysis needed)\"", $2}')
  ]
}
EOF
    
    log_insight "Workflow patterns saved to: $patterns_file"
    
    # Display insights
    echo "$successful_workflows" | head -3 | while read count workflow; do
        log_insight "Successful workflow: '$workflow' completed $count times"
    done
    
    if [[ -n "$failed_workflows" ]]; then
        echo "$failed_workflows" | head -2 | while read count workflow; do
            log_warn "Problematic workflow: '$workflow' failed $count times"
        done
    fi
}

# Generate optimization suggestions
generate_suggestions() {
    log_info "Generating optimization suggestions..."
    
    local suggestions_file="$SUGGESTIONS_DIR/suggestions_$TIMESTAMP.md"
    local current_hour=$(date +%H)
    local git_ctx=$(get_git_context)
    
    # Analyze recent patterns
    local recent_failures=$(tail -100 "$ANALYTICS_DIR/failures.log" 2>/dev/null | wc -l)
    local recent_commands=$(tail -100 "$ANALYTICS_DIR/commands.log" 2>/dev/null | wc -l)
    local recent_failure_rate=0
    
    if [[ $recent_commands -gt 0 ]]; then
        recent_failure_rate=$(echo "scale=2; $recent_failures * 100 / $recent_commands" | bc -l 2>/dev/null || echo "0")
    fi
    
    # Generate suggestions based on patterns
    cat > "$suggestions_file" << EOF
# Development Optimization Suggestions
*Generated: $(date)*
*Session: $SESSION_ID*

## 📊 Current Analysis

**Recent Activity:**
- Commands executed: $recent_commands
- Failures: $recent_failures  
- Failure rate: ${recent_failure_rate}%
- Git context: $git_ctx

## 🎯 Personalized Suggestions

### Immediate Optimizations
EOF
    
    # Time-based suggestions
    if [[ $current_hour -ge 18 || $current_hour -le 6 ]]; then
        echo "- 🌙 **Late hours detected** - Consider shorter, focused tasks to maintain code quality" >> "$suggestions_file"
    fi
    
    # Failure-rate based suggestions
    if (( $(echo "$recent_failure_rate > 15" | bc -l 2>/dev/null || echo 0) )); then
        cat >> "$suggestions_file" << EOF
- ⚠️ **High failure rate** - Try running \`just pre-commit-fix\` before complex operations
- 🔄 **Break down workflows** - Consider splitting complex tasks into smaller steps
EOF
    fi
    
    # Git-based suggestions
    if echo "$git_ctx" | grep -q "changes:[^0]"; then
        echo "- 💾 **Uncommitted changes detected** - Consider \`just ship \"<message>\"\` to save progress" >> "$suggestions_file"
    fi
    
    if echo "$git_ctx" | grep -q "behind:[^0]"; then
        echo "- ⬇️ **Behind remote** - Run \`git pull\` to sync latest changes" >> "$suggestions_file"
    fi
    
    # Pattern-based suggestions
    local top_failed_cmd=$(tail -50 "$ANALYTICS_DIR/failures.log" 2>/dev/null | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -1 | awk '{print $2}')
    if [[ -n "$top_failed_cmd" ]]; then
        echo "- 🚨 **Frequent failure:** \`$top_failed_cmd\` - Check logs or try alternative approach" >> "$suggestions_file"
    fi
    
    cat >> "$suggestions_file" << EOF

### Workflow Optimizations
- 🧪 **Quality gates:** Use \`just pre-commit-fix\` for auto-fixing + validation
- 🔍 **Testing:** Run \`just test-watch\` for continuous feedback
- 📊 **Monitoring:** Check \`just health\` for system status

### Learning Insights
$(if [[ -f "$PATTERNS_DIR/command_analysis_$TIMESTAMP.json" ]]; then
    echo "- 📈 **Command analysis** available in learning patterns"
fi)
$(if [[ -f "$PATTERNS_DIR/workflow_patterns_$TIMESTAMP.json" ]]; then
    echo "- 🔄 **Workflow patterns** analyzed and saved"
fi)

### Next Steps
1. Review failing patterns: \`learning-system.sh analyze-failures\`
2. Check optimization impact: \`learning-system.sh benchmark\`
3. Export insights: \`learning-system.sh report\`

---
*Learning system tracking $(wc -l < "$ANALYTICS_DIR/commands.log" 2>/dev/null || echo 0) total commands*
EOF
    
    log_suggest "Suggestions generated: $suggestions_file"
    
    # Display key suggestions
    if (( $(echo "$recent_failure_rate > 10" | bc -l 2>/dev/null || echo 0) )); then
        log_suggest "High failure rate detected - run 'just pre-commit-fix' before complex operations"
    fi
    
    if echo "$git_ctx" | grep -q "changes:[^0]"; then
        log_suggest "Uncommitted changes detected - consider saving progress with 'just ship'"
    fi
}

# Analyze failure patterns
analyze_failures() {
    log_info "Analyzing failure patterns..."
    
    if [[ ! -s "$ANALYTICS_DIR/failures.log" ]]; then
        log_info "No failure data to analyze - system is performing well!"
        return 0
    fi
    
    local failures_analysis="$PATTERNS_DIR/failure_analysis_$TIMESTAMP.json"
    
    # Analyze most common failures
    local common_failures=$(tail -100 "$ANALYTICS_DIR/failures.log" | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -5)
    
    # Analyze failure by time of day
    local failure_hours=$(tail -100 "$ANALYTICS_DIR/failures.log" | cut -d'|' -f1 | cut -d' ' -f2 | cut -d':' -f1 | sort | uniq -c | sort -nr)
    
    # Analyze failure by git context
    local failure_contexts=$(tail -100 "$ANALYTICS_DIR/failures.log" | cut -d'|' -f6 | sort | uniq -c | sort -nr | head -3)
    
    cat > "$failures_analysis" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "analysis": {
    "total_failures": $(wc -l < "$ANALYTICS_DIR/failures.log"),
    "recent_failures": $(tail -100 "$ANALYTICS_DIR/failures.log" | wc -l),
    "common_failure_commands": [
$(echo "$common_failures" | awk '{printf "      {\"command\": \"%s\", \"count\": %d}", $2, $1; if(NR<5) printf ","; printf "\n"}')
    ],
    "failure_prone_hours": [
$(echo "$failure_hours" | head -3 | awk '{printf "      {\"hour\": \"%s\", \"count\": %d}", $2, $1; if(NR<3) printf ","; printf "\n"}')
    ]
  },
  "recommendations": [
    "Focus on top failing commands for optimization",
    "Consider workflow adjustments during high-failure hours",
    "Review git context patterns for systematic issues"
  ]
}
EOF
    
    log_insight "Failure analysis saved to: $failures_analysis"
    
    # Display top insights
    echo "$common_failures" | head -3 | while read count cmd; do
        log_warn "Command '$cmd' failed $count times recently"
    done
    
    if [[ -n "$failure_hours" ]]; then
        local peak_hour=$(echo "$failure_hours" | head -1 | awk '{print $2}')
        log_insight "Peak failure hour: ${peak_hour}:00"
    fi
}

# Benchmark and performance tracking
benchmark_performance() {
    log_info "Running performance benchmark..."
    
    local benchmark_file="$ANALYTICS_DIR/benchmark_$TIMESTAMP.json"
    local start_time=$(date +%s.%N)
    
    # Test common operations
    local lint_time=0
    local test_time=0
    local build_time=0
    
    log_info "Benchmarking lint performance..."
    if command_exists ruff && [[ -f .venv/bin/activate ]]; then
        local lint_start=$(date +%s.%N)
        source .venv/bin/activate && ruff check . --quiet >/dev/null 2>&1 || true
        local lint_end=$(date +%s.%N)
        lint_time=$(echo "$lint_end - $lint_start" | bc -l)
    fi
    
    log_info "Benchmarking test discovery..."
    if command_exists pytest && [[ -f .venv/bin/activate ]]; then
        local test_start=$(date +%s.%N)
        source .venv/bin/activate && python -m pytest --collect-only -q >/dev/null 2>&1 || true
        local test_end=$(date +%s.%N)
        test_time=$(echo "$test_end - $test_start" | bc -l)
    fi
    
    # Git operations benchmark
    local git_status_time=0
    if git rev-parse --git-dir >/dev/null 2>&1; then
        local git_start=$(date +%s.%N)
        git status --porcelain >/dev/null 2>&1
        local git_end=$(date +%s.%N)
        git_status_time=$(echo "$git_end - $git_start" | bc -l)
    fi
    
    local total_time=$(date +%s.%N)
    total_time=$(echo "$total_time - $start_time" | bc -l)
    
    cat > "$benchmark_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "session_id": "$SESSION_ID",
  "benchmarks": {
    "lint_check_seconds": $lint_time,
    "test_discovery_seconds": $test_time,
    "git_status_seconds": $git_status_time,
    "total_benchmark_seconds": $total_time
  },
  "system_info": {
    "load": "$(uptime | awk '{print $(NF-2)}' | sed 's/,//')",
    "git_repo_size": "$(du -sh .git 2>/dev/null | cut -f1 || echo 'unknown')",
    "project_files": $(find . -name "*.py" | wc -l)
  },
  "performance_insights": [
$(if (( $(echo "$lint_time > 5" | bc -l 2>/dev/null || echo 0) )); then
    echo '    "Lint performance slow - consider file exclusions or faster linter",'
fi)
$(if (( $(echo "$test_time > 3" | bc -l 2>/dev/null || echo 0) )); then
    echo '    "Test discovery slow - consider test organization optimization",'
fi)
    "Benchmark complete"
  ]
}
EOF
    
    log_success "Benchmark completed in ${total_time}s"
    log_insight "Results saved to: $benchmark_file"
    
    # Display performance insights
    printf "Performance Summary:\n"
    printf "  Lint check: %.2fs\n" "$lint_time"
    printf "  Test discovery: %.2fs\n" "$test_time" 
    printf "  Git status: %.2fs\n" "$git_status_time"
}

# Generate comprehensive report
generate_report() {
    log_info "Generating comprehensive learning report..."
    
    local report_file="$LEARNING_DIR/learning_report_$TIMESTAMP.md"
    local total_commands=$(wc -l < "$ANALYTICS_DIR/commands.log" 2>/dev/null || echo 0)
    local total_sessions=$(cut -d'|' -f2 "$ANALYTICS_DIR/commands.log" 2>/dev/null | sort -u | wc -l || echo 0)
    local first_tracked=$(head -1 "$ANALYTICS_DIR/commands.log" 2>/dev/null | cut -d'|' -f1 || echo "N/A")
    
    cat > "$report_file" << EOF
# 🧠 Development Learning Report
*Generated: $(date)*

## 📊 Overview
- **Total Commands Tracked:** $total_commands
- **Development Sessions:** $total_sessions  
- **First Activity:** $first_tracked
- **Learning Period:** Active tracking

## 🎯 Key Insights

### Command Usage Patterns
$(if [[ -s "$ANALYTICS_DIR/commands.log" ]]; then
    echo "**Most Used Commands:**"
    tail -500 "$ANALYTICS_DIR/commands.log" | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -5 | awk '{printf "- `%s`: %d times\n", $2, $1}'
fi)

### Workflow Analysis
$(if [[ -s "$ANALYTICS_DIR/workflows.log" ]]; then
    echo "**Successful Workflows:**"
    tail -200 "$ANALYTICS_DIR/workflows.log" | awk -F'|' '$5=="true"' | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -3 | awk '{printf "- %s: %d successes\n", $2, $1}'
fi)

### Performance Metrics
$(if [[ -s "$ANALYTICS_DIR/timings.log" ]]; then
    local avg_time=$(tail -200 "$ANALYTICS_DIR/timings.log" | awk -F'|' '{sum+=$3} END {print sum/NR}')
    echo "- **Average Command Duration:** ${avg_time}s"
fi)
$(if [[ -s "$ANALYTICS_DIR/failures.log" ]]; then
    local failure_rate=$(echo "scale=2; $(wc -l < "$ANALYTICS_DIR/failures.log") * 100 / $total_commands" | bc -l 2>/dev/null || echo "0")
    echo "- **Overall Failure Rate:** ${failure_rate}%"
fi)

## 🚀 Optimization Opportunities

$(if [[ $total_commands -gt 100 ]]; then
    echo "### Pattern-Based Suggestions"
    tail -100 "$ANALYTICS_DIR/commands.log" | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -3 | while read count cmd; do
        echo "- Consider creating alias for frequently used: \`$cmd\` ($count uses)"
    done
fi)

### Workflow Improvements
- **Quality Gates:** Integrate learning hooks with quality-gates.sh
- **Automation:** Consider scripting frequently repeated command sequences
- **Monitoring:** Set up alerts for unusual failure patterns

## 📈 Trends and Patterns

### Recent Activity (Last 24 hours)
$(tail -200 "$ANALYTICS_DIR/commands.log" | awk -F'|' -v cutoff="$(date -d '24 hours ago' '+%Y-%m-%d %H:%M:%S')" '$1 >= cutoff' | wc -l) commands executed

### Success Patterns
$(if [[ -s "$ANALYTICS_DIR/successes.log" ]]; then
    echo "Recent successful workflows show consistent patterns in:"
    tail -50 "$ANALYTICS_DIR/successes.log" | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -3 | awk '{printf "- %s operations\n", $2}'
fi)

## 🎓 Learning Recommendations

1. **Focus Areas:** Optimize most-used commands and workflows
2. **Automation:** Script repetitive tasks (3+ manual repetitions)  
3. **Quality:** Maintain <5% failure rate through better practices
4. **Monitoring:** Regular learning system analysis (weekly)

## 📁 Data Files
- Analytics: \`$ANALYTICS_DIR/\`
- Patterns: \`$PATTERNS_DIR/\`
- Suggestions: \`$SUGGESTIONS_DIR/\`

---
*Learning system v1.0 - Continuous improvement through pattern analysis*
EOF
    
    log_success "Comprehensive report generated: $report_file"
    
    # Display summary
    log_insight "Learning Summary:"
    log_insight "  Commands tracked: $total_commands"
    log_insight "  Sessions analyzed: $total_sessions"
    if [[ $total_commands -gt 0 ]]; then
        local failure_rate=$(echo "scale=1; $(wc -l < "$ANALYTICS_DIR/failures.log" 2>/dev/null || echo 0) * 100 / $total_commands" | bc -l 2>/dev/null || echo "0")
        log_insight "  Success rate: $(echo "100 - $failure_rate" | bc -l)%"
    fi
}

# Export data for external analysis
export_data() {
    local format="${1:-json}"
    local export_file="$LEARNING_DIR/export_$TIMESTAMP.$format"
    
    log_info "Exporting learning data to $format format..."
    
    case "$format" in
        json)
            cat > "$export_file" << EOF
{
  "export_timestamp": "$(date -Iseconds)",
  "session_id": "$SESSION_ID",
  "commands": [
$(tail -1000 "$ANALYTICS_DIR/commands.log" 2>/dev/null | awk -F'|' '{printf "    {\"timestamp\":\"%s\",\"session\":\"%s\",\"command\":\"%s\",\"exit_code\":%s,\"duration\":%s}", $1, $2, $3, $4, $5; if(NR<1000) printf ","; printf "\n"}' | head -999)
  ],
  "workflows": [
$(tail -500 "$ANALYTICS_DIR/workflows.log" 2>/dev/null | awk -F'|' '{printf "    {\"timestamp\":\"%s\",\"session\":\"%s\",\"workflow\":\"%s\",\"success\":%s,\"duration\":%s}", $1, $2, $3, $5, $6; if(NR<500) printf ","; printf "\n"}' | head -499)
  ]
}
EOF
            ;;
        csv)
            echo "timestamp,session_id,command,exit_code,duration,git_context,system_context" > "$export_file"
            tail -1000 "$ANALYTICS_DIR/commands.log" 2>/dev/null >> "$export_file"
            ;;
        *)
            log_error "Unsupported export format: $format"
            return 1
            ;;
    esac
    
    log_success "Data exported to: $export_file"
}

# Clean old data
cleanup_data() {
    local days="${1:-30}"
    log_info "Cleaning learning data older than $days days..."
    
    local cutoff_date=$(date -d "$days days ago" '+%Y-%m-%d')
    local cleaned=0
    
    # Clean analytics files
    for file in "$ANALYTICS_DIR"/*.log; do
        if [[ -f "$file" ]]; then
            local temp_file=$(mktemp)
            awk -F'|' -v cutoff="$cutoff_date" '$1 >= cutoff' "$file" > "$temp_file"
            local old_size=$(wc -l < "$file")
            local new_size=$(wc -l < "$temp_file")
            mv "$temp_file" "$file"
            cleaned=$((cleaned + old_size - new_size))
        fi
    done
    
    # Clean old pattern files
    find "$PATTERNS_DIR" -name "*_*.json" -mtime +$days -delete
    find "$SUGGESTIONS_DIR" -name "*_*.md" -mtime +$days -delete
    
    log_success "Cleaned $cleaned old records"
}

# Interactive learning dashboard
dashboard() {
    log_info "🎛️  Learning System Dashboard"
    echo
    
    # Current status
    local total_commands=$(wc -l < "$ANALYTICS_DIR/commands.log" 2>/dev/null || echo 0)
    local recent_commands=$(tail -100 "$ANALYTICS_DIR/commands.log" 2>/dev/null | wc -l)
    local recent_failures=$(tail -100 "$ANALYTICS_DIR/failures.log" 2>/dev/null | wc -l)
    
    printf "📊 Current Status:\n"
    printf "   Total commands tracked: %s\n" "$total_commands"
    printf "   Recent activity: %s commands\n" "$recent_commands"
    printf "   Recent failures: %s\n" "$recent_failures"
    echo
    
    if [[ $total_commands -gt 10 ]]; then
        printf "🔥 Hot Commands:\n"
        tail -200 "$ANALYTICS_DIR/commands.log" | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -5 | awk '{printf "   %s: %d uses\n", $2, $1}'
        echo
    fi
    
    if [[ $recent_failures -gt 0 ]]; then
        printf "⚠️  Recent Issues:\n"
        tail -20 "$ANALYTICS_DIR/failures.log" | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -3 | awk '{printf "   %s: %d failures\n", $2, $1}'
        echo
    fi
    
    printf "🎯 Quick Actions:\n"
    printf "   learning-system.sh analyze    - Analyze all patterns\n"
    printf "   learning-system.sh suggest    - Get optimization suggestions\n"
    printf "   learning-system.sh benchmark  - Run performance tests\n"
    printf "   learning-system.sh report     - Generate full report\n"
    echo
}

# Show help
show_help() {
    cat << EOF
🧠 Learning System - AI-powered development optimization

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    track <cmd> <exit> <time>  Track command execution
    workflow <name> <steps>    Track workflow completion
    analyze                    Analyze all patterns and generate insights
    suggest                    Generate optimization suggestions  
    analyze-failures           Analyze failure patterns
    benchmark                  Run performance benchmarks
    report                     Generate comprehensive report
    export [json|csv]          Export data for external analysis
    cleanup [days]             Clean data older than N days (default: 30)
    dashboard                  Show interactive learning dashboard
    init                       Initialize learning system
    help                       Show this help

EXAMPLES:
    # Track a command execution
    $0 track "just test" 0 15.2

    # Track workflow
    $0 workflow "full-deployment" "lint,test,build,deploy" true 120.5

    # Get optimization suggestions
    $0 suggest

    # Full analysis and reporting
    $0 analyze && $0 report

    # Performance benchmarking
    $0 benchmark

    # Export for external tools
    $0 export json

INTEGRATION:
    # Hook into justfile commands
    just command-name && learning-system.sh track "just command-name" \$? \$duration

    # Automatic workflow tracking
    learning-system.sh workflow "ci-pipeline" "lint,test,deploy" \$success \$total_time

    # Scheduled analysis
    crontab: 0 9 * * * cd $PROJECT_ROOT && ./scripts/learning-system.sh analyze

ENVIRONMENT VARIABLES:
    SESSION_ID=<id>           Set custom session identifier
    LEARNING_LEVEL=<level>    Set learning verbosity (1-3)

EOF
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    case "${1:-help}" in
        init)
            init_learning_system
            ;;
        track)
            shift
            track_command "$@"
            ;;
        workflow)
            shift
            track_workflow "$@"
            ;;
        analyze)
            init_learning_system
            analyze_command_patterns
            analyze_workflow_patterns
            ;;
        suggest)
            init_learning_system
            generate_suggestions
            ;;
        analyze-failures)
            init_learning_system
            analyze_failures
            ;;
        benchmark)
            init_learning_system
            benchmark_performance
            ;;
        report)
            init_learning_system
            generate_report
            ;;
        export)
            init_learning_system
            export_data "${2:-json}"
            ;;
        cleanup)
            cleanup_data "${2:-30}"
            ;;
        dashboard)
            init_learning_system
            dashboard
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Trap cleanup
cleanup() {
    log_info "Learning system session $SESSION_ID completed"
}

trap cleanup EXIT

main "$@"