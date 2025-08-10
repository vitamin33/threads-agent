#!/bin/bash
# validate-health-checks.sh - Validate that health endpoints work properly

set -e

echo "🏥 HEALTH CHECK VALIDATOR"
echo "========================"

# Function to test health endpoint
test_health_endpoint() {
    local service=$1
    local port=$2
    local path=$3
    
    echo "Testing $service health endpoint..."
    
    # Get pod for service
    POD=$(kubectl get pods -l app=$service --no-headers 2>/dev/null | head -1 | awk '{print $1}')
    
    if [ -z "$POD" ]; then
        echo "❌ No pod found for $service"
        return 1
    fi
    
    # Check if pod is running
    PHASE=$(kubectl get pod $POD -o jsonpath='{.status.phase}' 2>/dev/null)
    if [ "$PHASE" != "Running" ]; then
        echo "❌ Pod $POD is not running (phase: $PHASE)"
        return 1
    fi
    
    # Test health endpoint inside the pod
    echo "Testing health endpoint: curl http://localhost:$port$path"
    kubectl exec $POD -- curl -sf http://localhost:$port$path > /tmp/${service}_health.txt 2>&1 || {
        echo "❌ Health check failed for $service"
        echo "Response:"
        cat /tmp/${service}_health.txt || echo "No response captured"
        return 1
    }
    
    echo "✅ Health check passed for $service"
    echo "Response: $(cat /tmp/${service}_health.txt)"
    return 0
}

# Function to check readiness probe configuration  
check_probe_config() {
    local service=$1
    echo "\\nChecking probe configuration for $service:"
    
    kubectl get deployment $service -o yaml 2>/dev/null | grep -A 10 -B 5 "livenessProbe\\|readinessProbe" || {
        echo "⚠️  No deployment found or no probes configured"
        return 1
    }
}

# Test all services
services=("fake-threads:9009:/health" "persona-runtime:8080:/health" "orchestrator:8080:/health")

for service_config in "${services[@]}"; do
    IFS=':' read -r service port path <<< "$service_config"
    echo "\\n--- Testing $service ---"
    
    check_probe_config $service
    test_health_endpoint $service $port $path || echo "⚠️  Health check validation failed for $service"
done

echo "\\n📊 SUMMARY:"
echo "All configured health checks have been tested."
echo "Any failures above indicate why pods might be failing readiness/liveness probes."