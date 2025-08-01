#!/bin/bash

# Test script for MLflow Helm chart

echo "🔍 Testing MLflow Helm Chart..."
echo "================================"

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed"
    exit 1
fi

echo "✅ Helm is installed"

# Lint the chart
echo -e "\n📋 Linting Helm chart..."
helm lint ./helm

# Dry run to check for errors
echo -e "\n🧪 Running dry-run installation..."
helm install mlflow-test ./helm --dry-run --debug --namespace test > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Helm chart validation passed"
else
    echo "❌ Helm chart validation failed"
    exit 1
fi

# Check templates
echo -e "\n📄 Checking generated templates..."
helm template mlflow-test ./helm > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Template generation successful"
else
    echo "❌ Template generation failed"
    exit 1
fi

echo -e "\n🎉 All Helm chart tests passed!"
echo "================================"
echo -e "\nTo deploy MLflow:"
echo "  1. make deps      # Update dependencies"
echo "  2. make install   # Install to k8s"
echo "  3. make port-forward  # Access UI"