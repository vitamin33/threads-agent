#!/bin/bash
# Quick start script for monitoring demo

echo "🚀 Starting Threads-Agent Monitoring Demo"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Start the monitoring stack
echo "📦 Starting monitoring stack..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
echo ""

# Check Prometheus
if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus Server is Healthy"; then
    echo "✅ Prometheus is running at http://localhost:9090"
else
    echo "⚠️  Prometheus might still be starting..."
fi

# Check Grafana
if curl -s http://localhost:3000/api/health | grep -q "ok"; then
    echo "✅ Grafana is running at http://localhost:3000"
    echo "   Username: admin"
    echo "   Password: admin123"
else
    echo "⚠️  Grafana might still be starting..."
fi

# Check metrics endpoint
if curl -s http://localhost:8081/metrics | grep -q "posts_engagement_rate"; then
    echo "✅ Metrics endpoint is working at http://localhost:8081/metrics"
else
    echo "⚠️  Metrics generator might still be starting..."
fi

echo ""
echo "📊 Demo Commands:"
echo ""
echo "1. View raw metrics:"
echo "   curl http://localhost:8081/metrics | grep -E 'engagement|cost_per_follow'"
echo ""
echo "2. Open Grafana:"
echo "   open http://localhost:3000"
echo ""
echo "3. Open Prometheus:"
echo "   open http://localhost:9090"
echo ""
echo "4. Query in Prometheus:"
echo "   - avg(posts_engagement_rate)"
echo "   - avg(cost_per_follow_dollars)"
echo "   - rate(token_usage_total[5m])"
echo ""
echo "5. Stop the demo:"
echo "   docker-compose -f docker-compose.monitoring.yml down"
echo ""
echo "💡 The Business KPIs dashboard is auto-loaded in Grafana!"