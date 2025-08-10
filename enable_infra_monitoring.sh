#!/bin/bash
# Enable infrastructure monitoring for interview demo

echo "🔧 Enabling Infrastructure Monitoring"
echo "===================================="
echo ""

# 1. Enable RabbitMQ Prometheus plugin
echo "📊 Enabling RabbitMQ metrics..."
kubectl exec -n default rabbitmq-0 -- rabbitmq-plugins enable rabbitmq_prometheus
echo "✅ RabbitMQ metrics available at: http://rabbitmq:15692/metrics"

# 2. Apply PostgreSQL exporter
echo ""
echo "📊 Deploying PostgreSQL exporter..."
helm upgrade --install threads-agent ./chart -f chart/values-dev.yaml --wait
echo "✅ PostgreSQL metrics available at: http://postgres-exporter:9187/metrics"

# 3. Restart Prometheus to pick up new targets
echo ""
echo "🔄 Restarting Prometheus..."
if docker-compose -f docker-compose.monitoring.yml ps | grep -q prometheus; then
    docker-compose -f docker-compose.monitoring.yml restart prometheus
else
    kubectl rollout restart deployment/prometheus -n default
fi

echo ""
echo "✅ Infrastructure monitoring enabled!"
echo ""
echo "📊 New Metrics Available:"
echo "• PostgreSQL: Query performance, connection pools, table sizes"
echo "• RabbitMQ: Queue depth, message rates, consumer lag"
echo "• Redis: Hit rates, memory usage (if redis-exporter added)"
echo ""
echo "🎯 Interview Talking Points:"
echo '• "We monitor all layers from business KPIs to database queries"'
echo '• "This helps identify if slowness is from AI, DB, or queue backlog"'
echo '• "Production incidents taught us to monitor infrastructure deeply"'