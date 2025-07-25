#!/bin/bash
set -e

PROJECT_ROOT="/Users/vitaliiserbyn/development/threads-agent"
cd "$PROJECT_ROOT"

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT"
export OPENAI_API_KEY="test"

# Check if cluster exists
if ! k3d cluster list | grep -q "threads-agent-jordan-kim-b4aec7"; then
    echo "Error: k3d cluster not found. Please run 'just bootstrap' first."
    exit 1
fi

# Start cluster if needed
k3d cluster start threads-agent-jordan-kim-b4aec7 || true

# Switch context
kubectl config use-context k3d-threads-agent-jordan-kim-b4aec7

# Check if services are deployed
if ! kubectl get pods -A | grep -q "orchestrator"; then
    echo "Error: Services not deployed. Please run 'just deploy-dev' first."
    exit 1
fi

# Run e2e tests (excluding achievement_collector for now)
pytest -s -m e2e --ignore=services/achievement_collector