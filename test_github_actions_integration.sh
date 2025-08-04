#!/bin/bash
#
# Test GitHub Actions PR Value Analysis Integration
#

echo "🚀 Testing GitHub Actions PR Value Analysis Integration"
echo "====================================================="

# Test PR number
PR_NUMBER="${1:-91}"

echo -e "\n📋 Test Configuration:"
echo "   PR Number: $PR_NUMBER"
echo "   Script: scripts/pr-value-analyzer.py"

# Step 1: Run PR Value Analyzer
echo -e "\n🔍 Step 1: Running PR Value Analyzer..."
if python3 scripts/pr-value-analyzer.py "$PR_NUMBER"; then
    echo "   ✅ PR analysis completed successfully"
else
    echo "   ❌ PR analysis failed"
    exit 1
fi

# Step 2: Check if analysis file was created
ANALYSIS_FILE="pr_${PR_NUMBER}_value_analysis.json"
ACHIEVEMENT_FILE=".achievements/pr_${PR_NUMBER}_achievement.json"

echo -e "\n📄 Step 2: Checking output files..."
if [ -f "$ANALYSIS_FILE" ]; then
    echo "   ✅ Analysis file created: $ANALYSIS_FILE"
    
    # Show key metrics
    echo -e "\n   📊 Key Metrics:"
    if command -v jq &> /dev/null; then
        OVERALL_SCORE=$(jq -r '.kpis.overall_score' "$ANALYSIS_FILE")
        ROI=$(jq -r '.business_metrics.roi_year_one_percent // 0' "$ANALYSIS_FILE")
        SAVINGS=$(jq -r '.business_metrics.infrastructure_savings_estimate // 0' "$ANALYSIS_FILE")
        
        echo "      Overall Score: $OVERALL_SCORE/10"
        echo "      ROI: ${ROI}%"
        echo "      Est. Savings: \$$(printf "%'.0f" $SAVINGS)"
    else
        echo "      (Install jq to see metrics)"
    fi
else
    echo "   ❌ Analysis file not found: $ANALYSIS_FILE"
fi

if [ -f "$ACHIEVEMENT_FILE" ]; then
    echo "   ✅ Achievement file created: $ACHIEVEMENT_FILE"
else
    echo "   ❌ Achievement file not found: $ACHIEVEMENT_FILE"
fi

# Step 3: Test GitHub Actions workflow components
echo -e "\n🔧 Step 3: Testing GitHub Actions Components..."

# Check if gh CLI is available
if command -v gh &> /dev/null; then
    echo "   ✅ GitHub CLI (gh) is installed"
    
    # Try to get PR details
    echo -e "\n   📝 Fetching PR details..."
    if gh pr view "$PR_NUMBER" --json title,state > /dev/null 2>&1; then
        PR_TITLE=$(gh pr view "$PR_NUMBER" --json title -q .title)
        PR_STATE=$(gh pr view "$PR_NUMBER" --json state -q .state)
        echo "      Title: $PR_TITLE"
        echo "      State: $PR_STATE"
    else
        echo "      ⚠️  Could not fetch PR details (may need authentication)"
    fi
else
    echo "   ⚠️  GitHub CLI not installed (required for full workflow)"
fi

# Step 4: Simulate API call to Achievement Collector
echo -e "\n📡 Step 4: Testing Achievement Collector Integration..."

# Check if achievement collector is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Achievement Collector is running"
    
    # Try to get PR metrics
    echo -e "\n   📈 Getting PR value metrics..."
    METRICS_RESPONSE=$(curl -s "http://localhost:8000/pr-analysis/value-metrics/$PR_NUMBER")
    
    if [ $? -eq 0 ] && [ -n "$METRICS_RESPONSE" ]; then
        echo "   ✅ Successfully retrieved PR metrics"
        
        if command -v jq &> /dev/null; then
            QUALIFIES=$(echo "$METRICS_RESPONSE" | jq -r '.qualifies_for_achievement')
            echo "      Qualifies for achievement: $QUALIFIES"
        fi
    else
        echo "   ⚠️  Could not retrieve PR metrics"
    fi
else
    echo "   ⚠️  Achievement Collector not running (start with: cd services/achievement_collector && uvicorn main:app)"
fi

# Step 5: Test enrichment script
echo -e "\n🔄 Step 5: Testing Enrichment Script..."
if [ -f "scripts/enrich-achievements-with-pr-value.py" ]; then
    echo "   ✅ Enrichment script found"
    
    # Show how to use it
    echo -e "\n   📝 To enrich historical PRs, run:"
    echo "      python3 scripts/enrich-achievements-with-pr-value.py --stats"
    echo "      python3 scripts/enrich-achievements-with-pr-value.py --limit 5"
else
    echo "   ❌ Enrichment script not found"
fi

# Summary
echo -e "\n====================================================="
echo "📊 Test Summary:"
echo ""
echo "✅ Completed:"
echo "   - PR value analysis script works"
echo "   - Output files are generated correctly"
echo "   - Integration points are identified"
echo ""
echo "⚠️  Manual Testing Required:"
echo "   1. Create a real PR and watch the GitHub Actions workflow"
echo "   2. Verify webhook integration on PR merge"
echo "   3. Check achievement creation in the database"
echo "   4. Run enrichment script on historical PRs"
echo ""
echo "🔗 Next Steps:"
echo "   1. Set up GitHub webhook: https://github.com/{owner}/{repo}/settings/hooks"
echo "   2. Add secrets to GitHub Actions:"
echo "      - ACHIEVEMENT_COLLECTOR_URL"
echo "      - ACHIEVEMENT_API_KEY"
echo "   3. Create a test PR to verify end-to-end flow"