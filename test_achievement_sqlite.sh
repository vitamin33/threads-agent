#!/bin/bash
# Test Achievement Collector with SQLite

echo "🧪 Testing Achievement Collector with SQLite Backend"
echo "=================================================="

# Set environment variables
export USE_SQLITE=true
export DATABASE_URL="sqlite:///$HOME/.threads-agent/achievements/achievements.db"
export OPENAI_API_KEY="${OPENAI_API_KEY:-test-key}"

# Create directory
mkdir -p ~/.threads-agent/achievements

# Function to make API calls
test_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -z "$data" ]; then
        curl -s -X $method "http://localhost:8084$endpoint" \
            -H "Content-Type: application/json"
    else
        curl -s -X $method "http://localhost:8084$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

# Start the service in background
echo "🚀 Starting Achievement Collector with SQLite..."
cd services/achievement_collector
uvicorn main:app --host 0.0.0.0 --port 8084 > /tmp/achievement_collector.log 2>&1 &
API_PID=$!

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check if service is running
if ! curl -s http://localhost:8084/health > /dev/null; then
    echo "❌ Service failed to start. Check logs:"
    cat /tmp/achievement_collector.log
    exit 1
fi

echo "✅ Service is running!"

# Test 1: Create achievements
echo -e "\n📝 Test 1: Creating achievements..."

# CI Optimization Achievement
CI_ACHIEVEMENT=$(test_api POST /achievements '{
    "title": "Reduced CI/CD Pipeline Time by 66%",
    "description": "Optimized threads-agent CI/CD pipeline through parallelization and caching",
    "category": "optimization",
    "started_at": "2025-01-20T00:00:00Z",
    "completed_at": "2025-01-25T00:00:00Z",
    "source_type": "manual",
    "source_id": "ci-optimization-2025",
    "tags": ["ci/cd", "optimization", "automation"],
    "skills_demonstrated": ["DevOps", "CI/CD", "Performance Optimization"],
    "portfolio_ready": true,
    "evidence": {
        "before": {"build_time_min": 15, "test_time_min": 8},
        "after": {"build_time_min": 5, "test_time_min": 2},
        "improvement_percent": 66,
        "developer_hours_saved": 200
    }
}')

CI_ID=$(echo $CI_ACHIEVEMENT | jq -r '.id')
echo "✅ Created CI achievement with ID: $CI_ID"

# Achievement System Achievement
SYSTEM_ACHIEVEMENT=$(test_api POST /achievements '{
    "title": "Implemented Achievement Collection System",
    "description": "Built comprehensive achievement tracking system with AI analysis and portfolio generation",
    "category": "feature",
    "started_at": "2025-01-15T00:00:00Z",
    "completed_at": "2025-01-25T00:00:00Z",
    "source_type": "manual",
    "source_id": "achievement-system-2025",
    "tags": ["python", "fastapi", "ai", "portfolio"],
    "skills_demonstrated": ["Python", "FastAPI", "System Design", "AI Integration"],
    "portfolio_ready": true,
    "evidence": {
        "features": ["CRUD API", "AI Analysis", "Portfolio Generation", "GitHub Webhooks"],
        "tech_stack": ["Python", "FastAPI", "SQLAlchemy", "OpenAI", "SQLite"]
    }
}')

SYSTEM_ID=$(echo $SYSTEM_ACHIEVEMENT | jq -r '.id')
echo "✅ Created Achievement System with ID: $SYSTEM_ID"

# Test 2: Read achievements
echo -e "\n📖 Test 2: Reading achievements..."

# List all achievements
ALL_ACHIEVEMENTS=$(test_api GET /achievements)
TOTAL_COUNT=$(echo $ALL_ACHIEVEMENTS | jq -r '.total')
echo "✅ Total achievements: $TOTAL_COUNT"

# Get specific achievement
SPECIFIC=$(test_api GET /achievements/$CI_ID)
echo "✅ Retrieved achievement: $(echo $SPECIFIC | jq -r '.title')"

# Filter by category
OPTIMIZATIONS=$(test_api GET "/achievements?category=optimization")
OPT_COUNT=$(echo $OPTIMIZATIONS | jq -r '.total')
echo "✅ Optimization achievements: $OPT_COUNT"

# Test 3: Update achievement
echo -e "\n✏️  Test 3: Updating achievement..."

UPDATE_RESULT=$(test_api PUT /achievements/$CI_ID '{
    "impact_score": 95,
    "business_value": 75000,
    "time_saved_hours": 250
}')

echo "✅ Updated impact score to: $(echo $UPDATE_RESULT | jq -r '.impact_score')"
echo "✅ Updated business value to: $$(echo $UPDATE_RESULT | jq -r '.business_value')"

# Test 4: Stats API
echo -e "\n📊 Test 4: Statistics API..."

STATS=$(test_api GET /achievements/stats/summary)
echo "✅ Total achievements: $(echo $STATS | jq -r '.total_achievements')"
echo "✅ Total value generated: $$(echo $STATS | jq -r '.total_value_generated')"
echo "✅ Average impact score: $(echo $STATS | jq -r '.average_impact_score')"

# Test 5: Analysis (if OpenAI key available)
echo -e "\n🤖 Test 5: AI Analysis..."

if [ "$OPENAI_API_KEY" != "test-key" ]; then
    ANALYSIS=$(test_api POST /analysis/analyze "{
        \"achievement_id\": $CI_ID,
        \"analyze_impact\": true,
        \"analyze_technical\": true,
        \"generate_summary\": true
    }")
    
    if [ $? -eq 0 ]; then
        echo "✅ AI Analysis completed"
        echo "   Impact Score: $(echo $ANALYSIS | jq -r '.impact_score')"
        echo "   Summary: $(echo $ANALYSIS | jq -r '.summary' | head -c 100)..."
    else
        echo "⚠️  AI Analysis skipped (API error)"
    fi
else
    echo "⚠️  AI Analysis skipped (no OpenAI API key)"
fi

# Test 6: Portfolio Generation
echo -e "\n📄 Test 6: Portfolio Generation..."

# HTML Portfolio
HTML_PORTFOLIO=$(test_api GET /portfolio/generate?format=html)
if [ $? -eq 0 ]; then
    echo "$HTML_PORTFOLIO" > ~/.threads-agent/achievements/portfolio.html
    echo "✅ HTML portfolio saved to: ~/.threads-agent/achievements/portfolio.html"
fi

# Markdown Portfolio
MD_PORTFOLIO=$(test_api GET /portfolio/generate?format=markdown)
if [ $? -eq 0 ]; then
    echo "$MD_PORTFOLIO" > ~/.threads-agent/achievements/portfolio.md
    echo "✅ Markdown portfolio saved to: ~/.threads-agent/achievements/portfolio.md"
fi

# Test 7: Data Persistence
echo -e "\n💾 Test 7: Testing data persistence..."

# Kill and restart the service
kill $API_PID
sleep 2

echo "🔄 Restarting service..."
uvicorn main:app --host 0.0.0.0 --port 8084 > /tmp/achievement_collector.log 2>&1 &
API_PID=$!
sleep 5

# Check if data persists
PERSISTED=$(test_api GET /achievements)
PERSISTED_COUNT=$(echo $PERSISTED | jq -r '.total')

if [ "$PERSISTED_COUNT" = "$TOTAL_COUNT" ]; then
    echo "✅ Data persisted successfully! Found $PERSISTED_COUNT achievements"
else
    echo "❌ Data persistence issue: Expected $TOTAL_COUNT, found $PERSISTED_COUNT"
fi

# Cleanup
kill $API_PID

echo -e "\n✅ All tests completed!"
echo "📁 Database location: $HOME/.threads-agent/achievements/achievements.db"
echo "📄 Portfolio files saved in: $HOME/.threads-agent/achievements/"
echo ""
echo "To view your achievements database:"
echo "  sqlite3 ~/.threads-agent/achievements/achievements.db 'SELECT * FROM achievements;'"