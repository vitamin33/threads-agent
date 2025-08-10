#!/bin/bash

echo "🚀 Testing Monitoring Stack"
echo "=========================="

# Option 1: Docker Compose (Quickest)
echo -e "\nOption 1: Testing with Docker Compose"
echo "-------------------------------------"
echo "Starting monitoring stack..."
docker-compose -f docker-compose.monitoring.yml up -d

echo -e "\nWaiting for services to start (10 seconds)..."
sleep 10

echo -e "\nChecking services:"
curl -s http://localhost:9090/-/healthy && echo "✅ Prometheus is healthy" || echo "❌ Prometheus not responding"
curl -s http://localhost:3000/api/health && echo "✅ Grafana is healthy" || echo "❌ Grafana not responding"
curl -s http://localhost:8081/metrics | grep -q "posts_engagement_rate" && echo "✅ Metrics are being generated" || echo "❌ No metrics found"

echo -e "\n📊 Access points:"
echo "- Grafana: http://localhost:3000 (admin/admin123)"
echo "- Prometheus: http://localhost:9090"
echo "- Metrics: http://localhost:8081/metrics"

echo -e "\n🎯 To see business metrics:"
echo "curl http://localhost:8081/metrics | grep -E 'posts_engagement_rate|cost_per_follow|revenue_projection'"

echo -e "\n🛑 To stop:"
echo "docker-compose -f docker-compose.monitoring.yml down"