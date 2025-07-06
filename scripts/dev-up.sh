#!/usr/bin/env bash
# Idempotent helper: wipes any old “dev” cluster and starts a fresh one
# 1 control-plane + 2 agents, LB on localhost:8080
#!/usr/bin/env bash
set -euo pipefail
CLUSTER="dev"
HOST_PORT=8080    # change here if you prefer 8081

# If the port is busy, automatically switch to 8081
if lsof -Pi :"$HOST_PORT" -sTCP:LISTEN -t >/dev/null ; then
  echo "🔴  Port $HOST_PORT busy; falling back to $((HOST_PORT+1))"
  HOST_PORT=$((HOST_PORT+1))
fi

echo "🧹  removing old cluster (if any)…"
k3d cluster delete "$CLUSTER" 2>/dev/null || true

echo "🚀  creating k3d cluster on host port $HOST_PORT"
k3d cluster create "$CLUSTER" \
  --servers 1 \
  --agents 2 \
  --port "${HOST_PORT}:80@loadbalancer"

echo "✅  Cluster ready on http://localhost:${HOST_PORT}"
kubectl get nodes
