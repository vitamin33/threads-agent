#!/bin/bash

# Monitor Claude Code Auto-Fix Results
# This script tracks the success rate of automated CI fixes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
METRICS_FILE="${PROJECT_ROOT}/.metrics/auto-fix-stats.json"
DAYS_TO_ANALYZE=${1:-7}

echo -e "${BLUE}🤖 Claude Code Auto-Fix Monitor${NC}"
echo "================================"

# Initialize metrics file if it doesn't exist
mkdir -p "$(dirname "$METRICS_FILE")"
if [[ ! -f "$METRICS_FILE" ]]; then
    echo '{"fixes": []}' > "$METRICS_FILE"
fi

# Function to check GitHub CLI
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
        echo "Please install it: https://cli.github.com/"
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        echo -e "${RED}Error: Not authenticated with GitHub${NC}"
        echo "Please run: gh auth login"
        exit 1
    fi
}

# Function to get auto-fix workflow runs
get_autofix_runs() {
    echo -e "\n${YELLOW}Fetching auto-fix workflow runs...${NC}"
    
    gh run list \
        --workflow="auto-fix-ci.yml" \
        --limit=100 \
        --json databaseId,status,conclusion,createdAt,headBranch,event \
        --jq ".[] | select(.createdAt > \"$(date -d "$DAYS_TO_ANALYZE days ago" -Iseconds)\")"
}

# Function to analyze fix success rate
analyze_success_rate() {
    local total_runs=0
    local successful_fixes=0
    local failed_fixes=0
    local no_fix_needed=0
    
    echo -e "\n${YELLOW}Analyzing auto-fix success rate...${NC}"
    
    # Get all auto-fix runs
    local runs=$(gh run list \
        --workflow="auto-fix-ci.yml" \
        --limit=100 \
        --json status,conclusion,createdAt)
    
    # Count outcomes
    total_runs=$(echo "$runs" | jq 'length')
    successful_fixes=$(echo "$runs" | jq '[.[] | select(.conclusion == "success")] | length')
    failed_fixes=$(echo "$runs" | jq '[.[] | select(.conclusion == "failure")] | length')
    
    # Calculate success rate
    if [[ $total_runs -gt 0 ]]; then
        success_rate=$(awk "BEGIN {printf \"%.1f\", ($successful_fixes / $total_runs) * 100}")
    else
        success_rate=0
    fi
    
    echo -e "\n📊 ${GREEN}Auto-Fix Statistics (Last $DAYS_TO_ANALYZE days)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Total Runs:        ${BLUE}$total_runs${NC}"
    echo -e "Successful Fixes:  ${GREEN}$successful_fixes${NC}"
    echo -e "Failed Attempts:   ${RED}$failed_fixes${NC}"
    echo -e "Success Rate:      ${GREEN}${success_rate}%${NC}"
}

# Function to show recent fixes
show_recent_fixes() {
    echo -e "\n${YELLOW}Recent Auto-Fix Activities:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    gh run list \
        --workflow="auto-fix-ci.yml" \
        --limit=10 \
        --json status,conclusion,createdAt,headBranch,databaseId \
        --jq '.[] | "\(.createdAt | split("T")[0]) | \(.headBranch) | \(.conclusion // .status) | Run #\(.databaseId)"' \
        | column -t -s '|' \
        | while IFS= read -r line; do
            if [[ $line == *"success"* ]]; then
                echo -e "${GREEN}✓ $line${NC}"
            elif [[ $line == *"failure"* ]]; then
                echo -e "${RED}✗ $line${NC}"
            else
                echo -e "${YELLOW}⚡ $line${NC}"
            fi
        done
}

# Function to get common fix patterns
analyze_fix_patterns() {
    echo -e "\n${YELLOW}Analyzing common fix patterns...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Get commit messages from successful auto-fixes
    local fix_commits=$(gh search commits \
        --author="Claude Code Bot" \
        --committer="Claude Code Bot" \
        --limit=50 \
        --json sha,commit \
        --jq '.[] | .commit.message' \
        2>/dev/null || echo "")
    
    if [[ -n "$fix_commits" ]]; then
        # Extract patterns
        echo -e "\n${BLUE}Most Common Fixes:${NC}"
        echo "$fix_commits" | grep -E "(fix|Fixed|Import|Type|Test)" | \
            sed 's/^[[:space:]]*//' | \
            sort | uniq -c | sort -rn | head -10 | \
            while IFS= read -r line; do
                echo "  $line"
            done
    else
        echo "No fix patterns found yet."
    fi
}

# Function to check current PR status
check_active_prs() {
    echo -e "\n${YELLOW}PRs with Recent Auto-Fix Activity:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Find PRs with auto-fix commits
    gh pr list \
        --label "auto-fixed" \
        --limit=10 \
        --json number,title,state,updatedAt \
        --jq '.[] | "#\(.number) | \(.title) | \(.state) | \(.updatedAt | split("T")[0])"' \
        | column -t -s '|' \
        | while IFS= read -r line; do
            if [[ $line == *"OPEN"* ]]; then
                echo -e "${GREEN}$line${NC}"
            else
                echo -e "${YELLOW}$line${NC}"
            fi
        done
}

# Function to generate recommendations
generate_recommendations() {
    echo -e "\n${YELLOW}💡 Recommendations:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Get failure patterns
    local recent_failures=$(gh run list \
        --workflow="auto-fix-ci.yml" \
        --status=failure \
        --limit=10 \
        --json name,conclusion)
    
    if [[ $(echo "$recent_failures" | jq 'length') -gt 5 ]]; then
        echo -e "${RED}⚠️  High failure rate detected!${NC}"
        echo "   Consider:"
        echo "   - Reviewing Claude Code configuration"
        echo "   - Adding more specific fix patterns"
        echo "   - Improving test stability"
    fi
    
    # Check for repeated fixes
    local repeated_branches=$(gh run list \
        --workflow="auto-fix-ci.yml" \
        --limit=50 \
        --json headBranch \
        --jq '.[].headBranch' | \
        sort | uniq -c | sort -rn | \
        awk '$1 > 2 {print $2}')
    
    if [[ -n "$repeated_branches" ]]; then
        echo -e "\n${YELLOW}⚠️  Branches requiring multiple fixes:${NC}"
        echo "$repeated_branches" | while IFS= read -r branch; do
            echo "   - $branch"
        done
        echo "   Consider adding more comprehensive test coverage"
    fi
}

# Function to export metrics
export_metrics() {
    echo -e "\n${YELLOW}Exporting metrics...${NC}"
    
    local timestamp=$(date -Iseconds)
    local metrics=$(cat <<EOF
{
    "timestamp": "$timestamp",
    "period_days": $DAYS_TO_ANALYZE,
    "total_runs": $total_runs,
    "successful_fixes": $successful_fixes,
    "failed_fixes": $failed_fixes,
    "success_rate": $success_rate
}
EOF
)
    
    # Append to metrics file
    jq ".fixes += [$metrics]" "$METRICS_FILE" > "$METRICS_FILE.tmp" && \
        mv "$METRICS_FILE.tmp" "$METRICS_FILE"
    
    echo -e "${GREEN}✓ Metrics exported to: $METRICS_FILE${NC}"
}

# Main execution
main() {
    check_gh_cli
    
    # Run analysis
    analyze_success_rate
    show_recent_fixes
    analyze_fix_patterns
    check_active_prs
    generate_recommendations
    
    # Export metrics if we have data
    if [[ ${total_runs:-0} -gt 0 ]]; then
        export_metrics
    fi
    
    echo -e "\n${GREEN}✓ Monitoring complete!${NC}"
}

# Run main function
main