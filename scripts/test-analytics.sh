#!/bin/bash
# Test Achievement Collector Phase 3.1 Analytics Features

set -e

echo "🧪 Testing Achievement Collector Phase 3.1 - Advanced Analytics"
echo "=============================================================="

# Base URL for local testing
BASE_URL="http://localhost:8004"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "\n${BLUE}Testing: ${description}${NC}"
    echo "Endpoint: ${method} ${endpoint}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -X GET "${BASE_URL}${endpoint}" -H "Content-Type: application/json")
    else
        response=$(curl -s -X POST "${BASE_URL}${endpoint}" -H "Content-Type: application/json" -d "${data}")
    fi
    
    echo -e "${GREEN}Response:${NC}"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
}

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
until curl -s "${BASE_URL}/health" > /dev/null 2>&1; do
    sleep 1
done

echo -e "${GREEN}✅ Service is ready!${NC}"

# Test Career Prediction
test_endpoint "GET" "/analytics/career-prediction?time_horizon_months=24" "" \
    "Career Trajectory Prediction (24 months)"

# Test Skill Gap Analysis
test_endpoint "GET" "/analytics/skill-gap-analysis?target_role=Staff%20Engineer" "" \
    "Skill Gap Analysis for Staff Engineer"

# Test Industry Benchmarking
test_endpoint "GET" "/analytics/industry-benchmark?time_period_days=365" "" \
    "Industry Benchmark (Last Year)"

# Test Compensation Benchmark
compensation_data='{
  "role": "Senior Software Engineer",
  "years_experience": 5,
  "skills": ["Python", "Kubernetes", "AWS", "React"],
  "location": "San Francisco",
  "achievements_count": 25
}'
test_endpoint "POST" "/analytics/compensation-benchmark" "$compensation_data" \
    "Compensation Benchmark"

# Test Skill Market Analysis
skills_data='["AI/ML", "Kubernetes", "Python", "React", "Rust"]'
test_endpoint "POST" "/analytics/skill-market-analysis" "$skills_data" \
    "Skill Market Analysis"

# Test Dashboard Metrics
test_endpoint "GET" "/analytics/dashboard-metrics?time_period_days=180" "" \
    "Dashboard Metrics (Last 6 Months)"

# Test Executive Summary
test_endpoint "GET" "/analytics/executive-summary" "" \
    "Executive Summary"

# Test Career Insights
test_endpoint "GET" "/analytics/career-insights" "" \
    "Comprehensive Career Insights"

# Test Trending Skills
test_endpoint "GET" "/analytics/trending-skills" "" \
    "Currently Trending Skills"

echo -e "\n${GREEN}✅ All analytics tests completed!${NC}"

# Create sample achievement for testing
echo -e "\n${YELLOW}Creating sample achievement for analytics...${NC}"

achievement_data='{
  "title": "Implemented Advanced Analytics for Achievement Collector",
  "description": "Developed Phase 3.1 features including career prediction, industry benchmarking, and performance dashboards",
  "category": "feature",
  "impact_score": 90,
  "complexity_score": 85,
  "skills_demonstrated": ["Python", "FastAPI", "AI/ML", "Data Analytics"],
  "business_value": "Enables data-driven career decisions",
  "started_at": "'$(date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%SZ')'",
  "completed_at": "'$(date -u '+%Y-%m-%dT%H:%M:%SZ')'"
}'

create_response=$(curl -s -X POST "${BASE_URL}/achievements/" \
    -H "Content-Type: application/json" \
    -d "${achievement_data}")

achievement_id=$(echo "$create_response" | jq -r '.id')

if [ "$achievement_id" != "null" ]; then
    echo -e "${GREEN}✅ Created achievement ID: ${achievement_id}${NC}"
    
    # Test AI analysis on the new achievement
    echo -e "\n${YELLOW}Running AI analysis on achievement...${NC}"
    test_endpoint "POST" "/analysis/${achievement_id}" "" \
        "AI Analysis of Achievement"
else
    echo -e "⚠️  Failed to create achievement"
fi

echo -e "\n${GREEN}🎉 Phase 3.1 Analytics Testing Complete!${NC}"
echo -e "\nKey Features Tested:"
echo "✓ Career trajectory prediction with AI"
echo "✓ Skill gap analysis for target roles"
echo "✓ Industry benchmarking and percentiles"
echo "✓ Compensation analysis with market data"
echo "✓ Real-time skill market trends"
echo "✓ Comprehensive dashboard metrics"
echo "✓ Executive summaries"
echo "✓ Integrated career insights"