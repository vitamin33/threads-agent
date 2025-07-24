#!/usr/bin/env bash
# scripts/dev-up-multi.sh ── Multi-developer k3d cluster management
# Creates unique clusters per git repo/user combination
set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# Get git repository and user info
get_cluster_identity() {
    local git_remote git_repo git_user git_email

    # Get git remote URL and extract repo name
    if git_remote=$(git config --get remote.origin.url 2>/dev/null); then
        # Extract repo name from URL (works with both HTTPS and SSH)
        git_repo=$(basename "$git_remote" .git | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
    else
        # Fallback to current directory name
        git_repo=$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
    fi

    # Get git user info
    git_user=$(git config --get user.name 2>/dev/null || echo "unknown")
    git_email=$(git config --get user.email 2>/dev/null || echo "unknown@example.com")

    # Create a short hash from email for uniqueness
    email_hash=$(echo -n "$git_email" | md5sum | cut -c1-6)

    # Clean up user name for cluster name
    git_user_clean=$(echo "$git_user" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | cut -c1-10)

    echo "{\"repo\":\"$git_repo\",\"user\":\"$git_user_clean\",\"email\":\"$git_email\",\"hash\":\"$email_hash\",\"full_user\":\"$git_user\"}"
}

# Parse command line arguments
TAG=${TAG:-local}
FORCE_RECREATE=${FORCE_RECREATE:-false}
SHARE_CLUSTER=${SHARE_CLUSTER:-false}

while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE_RECREATE=true
            shift
            ;;
        --share|-s)
            SHARE_CLUSTER=true
            shift
            ;;
        --tag|-t)
            TAG="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--force|-f] [--share|-s] [--tag|-t TAG]"
            echo "  --force    Force recreate cluster even if exists"
            echo "  --share    Use shared cluster name (just repo, no user)"
            echo "  --tag      Docker image tag (default: local)"
            exit 1
            ;;
    esac
done

# Get cluster identity
identity_json=$(get_cluster_identity)
git_repo=$(echo "$identity_json" | jq -r '.repo')
git_user=$(echo "$identity_json" | jq -r '.user')
git_email=$(echo "$identity_json" | jq -r '.email')
email_hash=$(echo "$identity_json" | jq -r '.hash')
full_user=$(echo "$identity_json" | jq -r '.full_user')

# Determine cluster name
if [ "$SHARE_CLUSTER" = "true" ]; then
    CLUSTER="${git_repo}"
    log "Using shared cluster mode: $CLUSTER"
else
    CLUSTER="${git_repo}-${git_user}-${email_hash}"
    log "Using personal cluster mode: $CLUSTER"
fi

# Ensure cluster name is valid for k3d (max 63 chars, alphanumeric + dash)
CLUSTER=$(echo "$CLUSTER" | cut -c1-63 | sed 's/[^a-z0-9-]/-/g' | sed 's/-*$//')

log "Repository: $git_repo"
log "Developer: $full_user <$git_email>"
log "Cluster name: $CLUSTER"

# Images to preload
IMAGES=(
  "ghcr.io/threads-agent-stack/orchestrator:$TAG"
  "ghcr.io/threads-agent-stack/celery-worker:$TAG"
  "ghcr.io/threads-agent-stack/persona-runtime:$TAG"
  "ghcr.io/threads-agent-stack/fake-threads:$TAG"
  "bitnami/postgresql:16"
  "rabbitmq:3.13-management-alpine"
  "qdrant/qdrant:v1.9.4"
)

# Dynamic port allocation based on cluster hash
BASE_LB_PORT=8080
BASE_API_PORT=6445
PORT_OFFSET=$(echo -n "$CLUSTER" | cksum | cut -d' ' -f1)
PORT_OFFSET=$((PORT_OFFSET % 100))  # Keep offset between 0-99

LB_PORT=$((BASE_LB_PORT + PORT_OFFSET))
API_PORT=$((BASE_API_PORT + PORT_OFFSET))

# Find free ports if calculated ones are busy
find_free_port() {
    local port=$1
    while lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; do
        port=$((port + 1))
    done
    echo $port
}

LB_PORT=$(find_free_port $LB_PORT)
API_PORT=$(find_free_port $API_PORT)

log "LoadBalancer port: $LB_PORT"
log "API port: $API_PORT"

# Kubeconfig path - unique per cluster
KCFG_DIR="$HOME/.kube/threads-agent"
mkdir -p "$KCFG_DIR"
KCFG="$KCFG_DIR/config-$CLUSTER"

# Check if cluster already exists
if k3d cluster list | grep -q "^$CLUSTER "; then
    if [ "$FORCE_RECREATE" = "true" ]; then
        warn "Cluster exists, forcing recreation..."
        k3d cluster delete "$CLUSTER"
    else
        success "Cluster '$CLUSTER' already exists!"
        log "Use --force to recreate"

        # Update kubeconfig and show info
        k3d kubeconfig get "$CLUSTER" \
          | sed -e "s/host\.docker\.internal/localhost/" \
                -e "s/127\.0\.0\.1:[0-9]*/localhost:${API_PORT}/" \
          > "$KCFG"

        export KUBECONFIG="$KCFG"
        kubectl config use-context "k3d-${CLUSTER}" &>/dev/null

        echo ""
        success "Cluster ready!"
        echo "🌐 LoadBalancer: http://localhost:${LB_PORT}"
        echo "🔑 Kubeconfig: export KUBECONFIG=\"$KCFG\""
        echo "📦 Context: k3d-${CLUSTER}"
        echo ""
        kubectl get nodes -o wide
        exit 0
    fi
fi

# Create cluster
log "Creating k3d cluster '$CLUSTER'..."
k3d cluster create "$CLUSTER" \
  --servers 1 --agents 2 \
  -p "${LB_PORT}:80@loadbalancer" \
  --api-port "${API_PORT}" \
  --k3s-arg "--tls-san=localhost@server:*" \
  --k3s-arg "--disable=traefik@server:*" \
  --wait

# Configure kubeconfig
k3d kubeconfig get "$CLUSTER" \
  | sed -e "s/host\.docker\.internal/localhost/" \
        -e "s/127\.0\.0\.1:[0-9]*/localhost:${API_PORT}/" \
  > "$KCFG"

export KUBECONFIG="$KCFG"
kubectl config use-context "k3d-${CLUSTER}" &>/dev/null

# Label nodes with developer info
kubectl label nodes --all "developer=${git_user}" "email-hash=${email_hash}" "repository=${git_repo}" --overwrite

# Import images
log "Importing images (this may take a while)..."
for IMAGE in "${IMAGES[@]}"; do
    if docker image inspect "$IMAGE" &>/dev/null; then
        k3d image import "$IMAGE" -c "$CLUSTER" || warn "Failed to import $IMAGE"
    else
        warn "Image $IMAGE not found locally, skipping import"
    fi
done

# Wait for cluster to be ready
printf "⏳ Waiting for cluster to be ready"
for i in {1..30}; do
    if kubectl --request-timeout=2s get --raw=/readyz &>/dev/null; then
        printf " ✓\n"
        break
    fi
    printf '.'
    sleep 1
done

# Create cluster info ConfigMap
kubectl create configmap cluster-info \
  --from-literal=cluster-name="$CLUSTER" \
  --from-literal=developer="$full_user" \
  --from-literal=email="$git_email" \
  --from-literal=repository="$git_repo" \
  --from-literal=created-at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -n default

# Save cluster metadata
CLUSTER_META_DIR="$HOME/.config/threads-agent/clusters"
mkdir -p "$CLUSTER_META_DIR"
cat > "$CLUSTER_META_DIR/$CLUSTER.json" <<EOF
{
  "name": "$CLUSTER",
  "repository": "$git_repo",
  "developer": "$full_user",
  "email": "$git_email",
  "lb_port": $LB_PORT,
  "api_port": $API_PORT,
  "kubeconfig": "$KCFG",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "k3d_version": "$(k3d version | grep 'k3d version' | awk '{print $3}')",
  "shared": $SHARE_CLUSTER
}
EOF

echo ""
success "Cluster '$CLUSTER' created successfully!"
echo ""
echo "📋 Cluster Details:"
echo "  Repository: $git_repo"
echo "  Developer: $full_user <$git_email>"
echo "  Cluster: $CLUSTER"
echo ""
echo "🔗 Access Points:"
echo "  LoadBalancer: http://localhost:${LB_PORT}"
echo "  API Server: https://localhost:${API_PORT}"
echo ""
echo "🔑 Kubeconfig:"
echo "  export KUBECONFIG=\"$KCFG\""
echo "  kubectl config use-context k3d-${CLUSTER}"
echo ""
echo "📦 Next steps:"
echo "  1. Export the KUBECONFIG as shown above"
echo "  2. Run 'just images' to build and import application images"
echo "  3. Run 'just deploy-dev' to deploy the application"
echo ""
kubectl get nodes -o wide
