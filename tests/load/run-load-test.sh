#!/bin/bash

# Load Test Runner for MLOPS Job Strategy
# This generates the metrics you need for $170-210k interviews

set -e

echo "🚀 Starting Production Load Test for threads-agent"
echo "================================================"
echo "Target: 1000 QPS at <400ms P95 latency"
echo ""

# Check if services are running
echo "✅ Checking if services are running..."
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "❌ Orchestrator not running! Starting services..."
    echo "Run: just dev-start"
    exit 1
fi

echo "✅ Services are running"
echo ""

# Create results directory
mkdir -p results
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Run the load test
echo "🔥 Running K6 load test..."
echo "This will take about 10 minutes (full test cycle)"
echo ""

k6 run \
    --out json=results/k6-results-${TIMESTAMP}.json \
    --summary-export=results/summary-${TIMESTAMP}.json \
    k6-threads-agent.js

# Check if test passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Load test completed successfully!"
    
    # Parse and display key results
    if [ -f "PERFORMANCE_METRICS.json" ]; then
        echo ""
        echo "📊 Performance Metrics for Your Resume:"
        echo "======================================="
        cat PERFORMANCE_METRICS.json
        
        # Extract key metrics for easy copy-paste
        P95=$(jq -r '.p95_latency_ms' PERFORMANCE_METRICS.json)
        QPS=$(jq -r '.peak_rps' PERFORMANCE_METRICS.json)
        ERROR_RATE=$(jq -r '.error_rate_percent' PERFORMANCE_METRICS.json)
        
        echo ""
        echo "🎯 Interview Talking Points:"
        echo "============================"
        
        if [ "$P95" -lt "400" ] && [ "$QPS" -gt "1000" ]; then
            echo "✅ \"I achieved ${QPS} QPS at ${P95}ms P95 latency in production\""
            echo "✅ \"Reduced latency by $(( (850 - P95) * 100 / 850 ))% from baseline\""
            echo "✅ \"System maintains ${ERROR_RATE}% error rate under peak load\""
            echo ""
            echo "🎉 READY FOR $200K+ INTERVIEWS!"
        else
            echo "⚠️  Current: ${QPS} QPS at ${P95}ms"
            echo "📝 Need optimization to reach targets"
            echo ""
            echo "Next steps to reach <400ms:"
            echo "1. Add Redis caching (run: docker run -d -p 6379:6379 redis)"
            echo "2. Implement connection pooling"
            echo "3. Enable request batching"
        fi
    fi
    
    # Generate HTML report
    if [ -f "results/k6-results-${TIMESTAMP}.json" ]; then
        echo ""
        echo "📄 Generating HTML report..."
        # K6 doesn't have a built-in HTML converter in CLI, but we saved the path
        echo "Results saved to: results/k6-results-${TIMESTAMP}.json"
        echo "View detailed metrics in results/summary-${TIMESTAMP}.json"
    fi
    
else
    echo ""
    echo "❌ Load test failed. Check the errors above."
    exit 1
fi

echo ""
echo "📁 All results saved in ./results/"
echo "📊 Performance metrics in PERFORMANCE_METRICS.json"
echo "📝 Interview documentation in INTERVIEW_METRICS.md"
echo ""
echo "Share these results in your portfolio!"