#!/bin/bash
echo "Testing Kubernetes MCP..."

# Test basic operations
echo "Getting pods:"
kubectl get pods -A | head -10

echo "Getting services:"
kubectl get svc

echo "Getting deployments:"
kubectl get deployments

echo "Test complete."
