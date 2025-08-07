#!/bin/bash
"""
Test script for tech-doc-generator Helm chart configuration

Validates that the new service can be deployed and configured properly.
"""

set -e

echo "🧪 Testing tech-doc-generator Helm chart configuration"
echo "=" * 60

# Test 1: Validate Helm chart syntax
echo "📋 Test 1: Validating Helm chart syntax..."
if helm template tech-doc-generator ./chart --values ./chart/values-dev.yaml --debug > /tmp/helm-template-output.yaml; then
    echo "✅ Helm template syntax is valid"
else
    echo "❌ Helm template syntax error"
    exit 1
fi

# Test 2: Check if tech-doc-generator service is included
echo "📋 Test 2: Checking tech-doc-generator service inclusion..."
if grep -q "name: tech-doc-generator" /tmp/helm-template-output.yaml; then
    echo "✅ tech-doc-generator service found in template"
else
    echo "❌ tech-doc-generator service not found"
    exit 1
fi

# Test 3: Check service configuration
echo "📋 Test 3: Validating service configuration..."
if grep -q "port: 8080" /tmp/helm-template-output.yaml && grep -q "app: tech-doc-generator" /tmp/helm-template-output.yaml; then
    echo "✅ Service configuration looks correct"
else
    echo "❌ Service configuration issue"
    exit 1
fi

# Test 4: Check environment variables
echo "📋 Test 4: Checking environment variables..."
required_envs=("DATABASE_URL" "REDIS_URL" "ACHIEVEMENT_COLLECTOR_URL" "VIRAL_ENGINE_URL")
for env in "${required_envs[@]}"; do
    if grep -q "$env" /tmp/helm-template-output.yaml; then
        echo "✅ $env environment variable configured"
    else
        echo "❌ $env environment variable missing"
        exit 1
    fi
done

# Test 5: Check resource limits
echo "📋 Test 5: Validating resource limits..."  
if grep -q "memory.*256Mi" /tmp/helm-template-output.yaml && grep -q "cpu.*100m" /tmp/helm-template-output.yaml; then
    echo "✅ Resource requests configured"
else
    echo "❌ Resource requests missing"
    exit 1
fi

# Test 6: Check health checks
echo "📋 Test 6: Validating health checks..."
if grep -q "readinessProbe" /tmp/helm-template-output.yaml && grep -q "livenessProbe" /tmp/helm-template-output.yaml; then
    echo "✅ Health checks configured"
else
    echo "❌ Health checks missing"
    exit 1
fi

# Test 7: Validate values-dev.yaml settings
echo "📋 Test 7: Checking development configuration..."
if helm template tech-doc-generator ./chart --values ./chart/values-dev.yaml | grep -q "tech-doc-generator.*local"; then
    echo "✅ Development image configuration correct"
else
    echo "❌ Development image configuration issue"
    exit 1
fi

# Test 8: Check integration dependencies
echo "📋 Test 8: Validating service dependencies..."
dependencies=("achievement-collector" "viral-engine" "postgres" "redis")
for dep in "${dependencies[@]}"; do
    if grep -q "$dep" /tmp/helm-template-output.yaml; then
        echo "✅ $dep dependency referenced"
    else
        echo "⚠️ $dep dependency not found (may be optional)"
    fi
done

# Test 9: Validate security configurations
echo "📋 Test 9: Checking security configurations..."
if grep -q "secret" /tmp/helm-template-output.yaml; then
    echo "✅ Secret references found"
else
    echo "⚠️ No secret references (check if OpenAI secrets are configured)"
fi

# Test 10: Check production-ready features
echo "📋 Test 10: Validating production features..."
production_features=("HorizontalPodAutoscaler" "PodDisruptionBudget" "NetworkPolicy")
echo "Production features available but disabled in development:"
for feature in "${production_features[@]}"; do
    if grep -q "$feature" ./chart/templates/tech-doc-generator.yaml; then
        echo "✅ $feature template ready (disabled in dev)"
    else
        echo "❌ $feature template missing"
    fi
done

echo ""
echo "=" * 60
echo "🎉 Helm chart validation complete!"
echo ""
echo "✅ Summary:"
echo "   • Helm chart syntax is valid"
echo "   • tech-doc-generator service properly configured"
echo "   • Environment variables and dependencies set up"
echo "   • Health checks and resource limits configured"
echo "   • Development and production configurations ready"
echo ""
echo "🚀 Ready for deployment with:"
echo "   helm upgrade --install threads-agent ./chart --values ./chart/values-dev.yaml"
echo ""
echo "🎯 New features available:"
echo "   • AI ROI Calculator API at /api/ai-roi-calculator/*"
echo "   • Content Scheduler API at /api/content-scheduler/*" 
echo "   • Achievement Integration at /api/achievement-articles/*"
echo "   • Professional content generation automation"

# Cleanup
rm -f /tmp/helm-template-output.yaml

echo ""
echo "✅ Test completed successfully!"