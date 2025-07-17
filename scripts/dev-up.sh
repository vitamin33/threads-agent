#!/usr/bin/env bash
# scripts/dev-up.sh ── spin a fresh local “dev” k3d cluster + preload image
set -euo pipefail

TAG=${TAG:-local}

CLUSTER="dev"
IMAGES=(
  "ghcr.io/threads-agent-stack/orchestrator:$TAG"
  "ghcr.io/threads-agent-stack/celery-worker:$TAG"
  "ghcr.io/threads-agent-stack/persona-runtime:$TAG"
)
IMAGES+=("qdrant/qdrant:v1.9.4")

LB_PORT=8080          # HTTP entry-point you’ll curl
API_PORT=6445         # k3s API exposed on localhost
KCFG="$HOME/.kube/config"  # we overwrite/append here

# ── pick a free LoadBalancer port ────────────────────────────────────
if lsof -Pi :"$LB_PORT" -sTCP:LISTEN -t >/dev/null; then
  echo "🔴  $LB_PORT busy → switching to $((LB_PORT+1))"
  LB_PORT=$((LB_PORT+1))
fi

echo "🧹 deleting any previous cluster…"
k3d cluster delete "$CLUSTER" &>/dev/null || true

echo "🚀 creating k3d cluster"
k3d cluster create "$CLUSTER" \
  --servers 1 --agents 2 \
  -p "${LB_PORT}:80@loadbalancer" \
  --api-port "${API_PORT}" \
  --k3s-arg "--tls-san=localhost@server:*"  \
  --wait

# ── kube-config: keep everything but change host → localhost:6445 ─────
k3d kubeconfig get "$CLUSTER" \
  | sed -e "s/host\.docker\.internal/localhost/" \
        -e "s/127\.0\.0\.1:64../localhost:${API_PORT}/" \
  > "$KCFG"

export KUBECONFIG="$KCFG"
kubectl config use-context "k3d-${CLUSTER}" &>/dev/null

# ── best-effort: preload the dev image into the cluster cache ─────────
echo "📦 importing dev image (best effort)…"
for IMAGE in "${IMAGES[@]}"; do
  k3d image import "$IMAGE" -c "$CLUSTER" || echo "ℹ︎  image not present locally"
done

# ── wait (≤15 s) for /readyz so that subsequent kubectl/helm are instant
printf "⏳ waiting for kube-api"
for i in {1..15}; do
  if kubectl --request-timeout=2s get --raw=/readyz &>/dev/null; then
    printf " ✓\n"; break
  fi
  printf '.'; sleep 1
done

echo "✅ cluster ready ▼"
kubectl get nodes -o wide
echo "🌐 LB http://localhost:${LB_PORT}"
echo "🔑 KUBECONFIG ${KCFG}"
