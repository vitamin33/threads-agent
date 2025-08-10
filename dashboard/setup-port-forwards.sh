#!/usr/bin/env bash
set -euo pipefail

echo "🔗 Setting up port forwards for Threads Agent Dashboard..."

# Kill any existing port forwards
pkill -f "kubectl port-forward" || true
sleep 2

# Start port forwards in background
echo "📡 Forwarding orchestrator (8080)..."
kubectl port-forward svc/orchestrator 8080:8080 > /dev/null 2>&1 &

echo "📡 Forwarding achievement-collector (8000)..."
kubectl port-forward svc/achievement-collector 8000:8090 > /dev/null 2>&1 &

echo "📡 Forwarding viral-engine (8003)..."
kubectl port-forward svc/viral-engine 8003:8090 > /dev/null 2>&1 &

echo "📡 Forwarding fake-threads (9009)..."
kubectl port-forward svc/fake-threads 9009:9009 > /dev/null 2>&1 &

echo "📡 Forwarding postgres (5432)..."
kubectl port-forward svc/postgres 5432:5432 > /dev/null 2>&1 &

echo "📡 Forwarding redis (6379)..."
kubectl port-forward svc/redis 6379:6379 > /dev/null 2>&1 &

echo "📡 Forwarding prometheus (9090)..."
kubectl port-forward svc/prometheus 9090:9090 > /dev/null 2>&1 &

echo "📡 Forwarding grafana (3000)..."
kubectl port-forward svc/grafana 3000:3000 > /dev/null 2>&1 &

echo "📡 Forwarding qdrant (6333)..."
kubectl port-forward svc/qdrant 6333:6333 > /dev/null 2>&1 &

echo "📡 Forwarding performance-monitor (8085)..."
kubectl port-forward svc/performance-monitor 8085:8085 > /dev/null 2>&1 &

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Test connections
echo "🧪 Testing connections..."
for port in 8080 8000 8003 9009 5432 6379 9090 3000 6333 8085; do
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ Port $port is accessible"
    else
        echo "❌ Port $port is not accessible"
    fi
done

echo "
✅ Port forwards established!

Service URLs:
- Orchestrator: http://localhost:8080
- Achievement Collector: http://localhost:8000
- Viral Engine: http://localhost:8003
- Fake Threads: http://localhost:9009
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Qdrant: http://localhost:6333
- Performance Monitor: http://localhost:8085

Press Ctrl+C to stop all port forwards
"

# Keep running
wait