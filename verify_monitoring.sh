#!/bin/bash

echo "🔍 Verifying Monitoring Setup"
echo "============================"

# Check if monitoring stack is configured
echo -e "\n1️⃣ Checking monitoring configuration..."
if grep -q "enabled: true" chart/values-dev.yaml | grep -A1 -B1 "prometheus"; then
    echo "✅ Prometheus enabled in Helm values"
else
    echo "❌ Prometheus not enabled"
fi

# Check service metrics endpoints
echo -e "\n2️⃣ Checking service metrics endpoints..."
echo "Fake Threads:"
grep -n "@app.get.*metrics" services/fake_threads/main.py || echo "❌ No metrics endpoint"

echo -e "\nPersona Runtime:"
grep -n "@api.get.*metrics" services/persona_runtime/main.py || echo "❌ No metrics endpoint"

echo -e "\nOrchestrator:"
grep -n "@app.get.*metrics" services/orchestrator/main.py || echo "❌ No metrics endpoint"

# Check for business metrics
echo -e "\n3️⃣ Checking business metrics implementation..."
grep -n "record_engagement_rate\|record_cost_per_follow\|update_revenue_projection" services/fake_threads/main.py

# Check monitoring files
echo -e "\n4️⃣ Checking monitoring files..."
[ -f "docker-compose.monitoring.yml" ] && echo "✅ docker-compose.monitoring.yml exists" || echo "❌ Missing"
[ -f "INTERVIEW_MONITORING_DEMO.md" ] && echo "✅ INTERVIEW_MONITORING_DEMO.md exists" || echo "❌ Missing"
[ -f "monitoring/prometheus.yml" ] && echo "✅ prometheus.yml exists" || echo "❌ Missing"
[ -f "monitoring/grafana/dashboards/business-kpis.json" ] && echo "✅ Grafana dashboards exist" || echo "❌ Missing"

# Check interview docs
echo -e "\n5️⃣ Checking interview documentation..."
[ -f "docs/INTERVIEW_PREPARATION_GUIDE.md" ] && echo "✅ Interview prep guide exists" || echo "❌ Missing"
[ -f "docs/INTERVIEW_QUICK_REFERENCE.md" ] && echo "✅ Quick reference exists" || echo "❌ Missing"

echo -e "\n📊 To test the monitoring stack:"
echo "1. Start k3d: just k3d-start"
echo "2. Deploy services: just deploy-dev"
echo "3. Or use Docker Compose: docker-compose -f docker-compose.monitoring.yml up -d"
echo "4. Access Grafana: http://localhost:3000 (admin/admin123)"
echo "5. Check metrics: curl http://localhost:8081/metrics | grep posts_"