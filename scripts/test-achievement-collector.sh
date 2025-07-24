#!/bin/bash
# Test Achievement Collector Service

set -e

echo "🎯 Testing Achievement Collector Service"
echo "========================================"

# Base URL
BASE_URL="${ACHIEVEMENT_COLLECTOR_URL:-http://localhost:8000}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Helper function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "\n${YELLOW}Testing: ${description}${NC}"
    echo "Method: ${method} ${endpoint}"
    
    if [ -n "$data" ]; then
        response=$(curl -s -X "${method}" "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "${data}")
    else
        response=$(curl -s -X "${method}" "${BASE_URL}${endpoint}")
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Success${NC}"
        echo "Response: ${response}" | jq '.' 2>/dev/null || echo "${response}"
        echo "${response}" > /tmp/last_achievement_response.json
    else
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

# 1. Health Check
test_endpoint "GET" "/health" "" "Health Check"

# 2. Create Achievement
ACHIEVEMENT_DATA='{
  "title": "Test Achievement - CI Pipeline Optimization",
  "description": "Successfully reduced CI build time from 25 minutes to 5 minutes through parallel execution and caching",
  "category": "optimization",
  "started_at": "'$(date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%S')'",
  "completed_at": "'$(date -u '+%Y-%m-%dT%H:%M:%S')'",
  "source_type": "manual",
  "tags": ["ci/cd", "optimization", "github-actions", "docker"],
  "skills_demonstrated": ["GitHub Actions", "Docker", "Python", "Bash"],
  "evidence": {
    "before_time": "25 minutes",
    "after_time": "5 minutes",
    "improvement": "80% reduction"
  }
}'

test_endpoint "POST" "/achievements/" "${ACHIEVEMENT_DATA}" "Create Achievement"

# Extract achievement ID
ACHIEVEMENT_ID=$(cat /tmp/last_achievement_response.json | jq -r '.id')
echo "Created achievement ID: ${ACHIEVEMENT_ID}"

# 3. Get Achievement
test_endpoint "GET" "/achievements/${ACHIEVEMENT_ID}" "" "Get Specific Achievement"

# 4. Update Achievement
UPDATE_DATA='{
  "impact_score": 85.5,
  "complexity_score": 72.0,
  "business_value": 50000,
  "time_saved_hours": 40,
  "portfolio_ready": true,
  "ai_summary": "Dramatically improved developer productivity by optimizing CI pipeline, reducing build times by 80% and saving 40 hours per month"
}'

test_endpoint "PUT" "/achievements/${ACHIEVEMENT_ID}" "${UPDATE_DATA}" "Update Achievement"

# 5. List Achievements
test_endpoint "GET" "/achievements/?page=1&per_page=10&sort_by=impact_score&order=desc" "" "List Achievements"

# 6. Get Statistics
test_endpoint "GET" "/achievements/stats/summary" "" "Get Achievement Statistics"

# 7. Generate Portfolio
PORTFOLIO_DATA='{
  "format": "markdown",
  "portfolio_ready_only": false,
  "min_impact_score": 0
}'

test_endpoint "POST" "/portfolio/generate" "${PORTFOLIO_DATA}" "Generate Portfolio"

# Extract portfolio ID
PORTFOLIO_ID=$(cat /tmp/last_achievement_response.json | jq -r '.download_url' | grep -oE '[0-9]+$')

# 8. Test Webhook Health
test_endpoint "GET" "/webhooks/health" "" "Webhook Health Check"

# 9. Test GitHub Webhook (simulate PR merge)
WEBHOOK_DATA='{
  "action": "closed",
  "pull_request": {
    "number": 123,
    "title": "feat: Add new feature",
    "body": "This PR adds an amazing new feature",
    "merged": true,
    "created_at": "'$(date -u -d '2 days ago' '+%Y-%m-%dT%H:%M:%SZ')'",
    "merged_at": "'$(date -u '+%Y-%m-%dT%H:%M:%SZ')'",
    "html_url": "https://github.com/test/repo/pull/123",
    "additions": 500,
    "deletions": 100,
    "changed_files": 10,
    "commits": 5,
    "comments": 3,
    "review_comments": 2,
    "labels": [
      {"name": "feature"},
      {"name": "enhancement"}
    ]
  }
}'

echo -e "\n${YELLOW}Testing: GitHub Webhook (without signature verification)${NC}"
curl -s -X POST "${BASE_URL}/webhooks/github" \
    -H "Content-Type: application/json" \
    -H "X-GitHub-Event: pull_request" \
    -d "${WEBHOOK_DATA}" | jq '.'

# Summary
echo -e "\n${GREEN}========================================"
echo -e "🎉 Achievement Collector Tests Complete!"
echo -e "========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Check the generated portfolio at: ${BASE_URL}/portfolio/download/${PORTFOLIO_ID:-1}"
echo "2. View all achievements at: ${BASE_URL}/achievements/"
echo "3. Configure real GitHub webhooks for automatic tracking"
echo ""
echo "For production setup, see: docs/achievement-collector-setup.md"