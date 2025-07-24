#!/usr/bin/env bash
# scripts/cluster-manager.sh ── Manage multiple k3d clusters for different developers/repos
set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

CLUSTER_META_DIR="$HOME/.config/threads-agent/clusters"
mkdir -p "$CLUSTER_META_DIR"

# Function to get current cluster from KUBECONFIG
get_current_cluster() {
    if [ -n "${KUBECONFIG:-}" ] && [ -f "$KUBECONFIG" ]; then
        kubectl config current-context 2>/dev/null | sed 's/^k3d-//' || echo "none"
    else
        echo "none"
    fi
}

# Function to display cluster info
display_cluster_info() {
    local cluster_name=$1
    local meta_file="$CLUSTER_META_DIR/${cluster_name}.json"

    if [ -f "$meta_file" ]; then
        local repo=$(jq -r '.repository' "$meta_file")
        local dev=$(jq -r '.developer' "$meta_file")
        local email=$(jq -r '.email' "$meta_file")
        local lb_port=$(jq -r '.lb_port' "$meta_file")
        local api_port=$(jq -r '.api_port' "$meta_file")
        local created=$(jq -r '.created_at' "$meta_file")
        local shared=$(jq -r '.shared' "$meta_file")

        echo -e "${CYAN}Cluster:${NC} $cluster_name"
        echo -e "  ${BLUE}Repository:${NC} $repo"
        echo -e "  ${BLUE}Developer:${NC} $dev <$email>"
        echo -e "  ${BLUE}Type:${NC} $([ "$shared" = "true" ] && echo "Shared" || echo "Personal")"
        echo -e "  ${BLUE}LoadBalancer:${NC} http://localhost:$lb_port"
        echo -e "  ${BLUE}API Server:${NC} https://localhost:$api_port"
        echo -e "  ${BLUE}Created:${NC} $created"
    else
        echo -e "${CYAN}Cluster:${NC} $cluster_name (no metadata available)"
    fi
}

# List all clusters
list_clusters() {
    local current_cluster=$(get_current_cluster)

    echo "Available k3d clusters:"
    echo ""

    local clusters=$(k3d cluster list -o json | jq -r '.[].name' 2>/dev/null || echo "")

    if [ -z "$clusters" ]; then
        warn "No k3d clusters found"
        echo "Run 'just bootstrap-multi' to create a cluster"
        return
    fi

    for cluster in $clusters; do
        if [ "$cluster" = "$current_cluster" ]; then
            echo -e "${GREEN}● Active:${NC}"
            display_cluster_info "$cluster" | sed 's/^/  /'
        else
            echo -e "${YELLOW}○ Inactive:${NC}"
            display_cluster_info "$cluster" | sed 's/^/  /'
        fi
        echo ""
    done
}

# Switch to a different cluster
switch_cluster() {
    local cluster_name=$1
    local meta_file="$CLUSTER_META_DIR/${cluster_name}.json"

    # Check if cluster exists
    if ! k3d cluster list | grep -q "^$cluster_name "; then
        error "Cluster '$cluster_name' not found"
        echo "Available clusters:"
        k3d cluster list | grep -v NAME | awk '{print "  - " $1}'
        exit 1
    fi

    # Get cluster info
    if [ -f "$meta_file" ]; then
        local kubeconfig=$(jq -r '.kubeconfig' "$meta_file")
        local lb_port=$(jq -r '.lb_port' "$meta_file")

        if [ -f "$kubeconfig" ]; then
            export KUBECONFIG="$kubeconfig"
            kubectl config use-context "k3d-${cluster_name}" &>/dev/null

            success "Switched to cluster '$cluster_name'"
            echo ""
            display_cluster_info "$cluster_name"
            echo ""
            echo "Run this in your shell:"
            echo "  export KUBECONFIG=\"$kubeconfig\""
        else
            error "Kubeconfig not found at $kubeconfig"
            echo "Regenerating kubeconfig..."
            k3d kubeconfig get "$cluster_name" > "$kubeconfig"
            switch_cluster "$cluster_name"  # Retry
        fi
    else
        warn "No metadata found for cluster '$cluster_name'"
        echo "Using k3d to get kubeconfig..."
        local temp_config="/tmp/kubeconfig-$cluster_name"
        k3d kubeconfig get "$cluster_name" > "$temp_config"
        export KUBECONFIG="$temp_config"
        kubectl config use-context "k3d-${cluster_name}" &>/dev/null
        success "Switched to cluster '$cluster_name'"
        echo "Run this in your shell:"
        echo "  export KUBECONFIG=\"$temp_config\""
    fi
}

# Delete a cluster
delete_cluster() {
    local cluster_name=$1

    read -p "Are you sure you want to delete cluster '$cluster_name'? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        return
    fi

    log "Deleting cluster '$cluster_name'..."
    k3d cluster delete "$cluster_name"

    # Remove metadata
    rm -f "$CLUSTER_META_DIR/${cluster_name}.json"

    success "Cluster '$cluster_name' deleted"
}

# Show cluster resources
show_resources() {
    local cluster_name=${1:-$(get_current_cluster)}

    if [ "$cluster_name" = "none" ]; then
        error "No active cluster. Use 'cluster-manager switch <name>' first"
        exit 1
    fi

    echo "Resources in cluster '$cluster_name':"
    echo ""

    echo -e "${CYAN}Nodes:${NC}"
    kubectl get nodes -o wide
    echo ""

    echo -e "${CYAN}Namespaces:${NC}"
    kubectl get namespaces
    echo ""

    echo -e "${CYAN}Deployments (all namespaces):${NC}"
    kubectl get deployments -A
    echo ""

    echo -e "${CYAN}Services (all namespaces):${NC}"
    kubectl get services -A
}

# Clean up orphaned clusters
cleanup() {
    log "Checking for orphaned cluster metadata..."

    for meta_file in "$CLUSTER_META_DIR"/*.json; do
        if [ -f "$meta_file" ]; then
            cluster_name=$(basename "$meta_file" .json)
            if ! k3d cluster list | grep -q "^$cluster_name "; then
                warn "Removing orphaned metadata for '$cluster_name'"
                rm -f "$meta_file"
            fi
        fi
    done

    success "Cleanup complete"
}

# Main command handling
case "${1:-help}" in
    list|ls)
        list_clusters
        ;;

    switch|use)
        if [ -z "${2:-}" ]; then
            error "Usage: $0 switch <cluster-name>"
            exit 1
        fi
        switch_cluster "$2"
        ;;

    current)
        current=$(get_current_cluster)
        if [ "$current" = "none" ]; then
            warn "No active cluster"
        else
            display_cluster_info "$current"
        fi
        ;;

    delete|rm)
        if [ -z "${2:-}" ]; then
            error "Usage: $0 delete <cluster-name>"
            exit 1
        fi
        delete_cluster "$2"
        ;;

    resources|res)
        show_resources "${2:-}"
        ;;

    cleanup)
        cleanup
        ;;

    info)
        if [ -z "${2:-}" ]; then
            error "Usage: $0 info <cluster-name>"
            exit 1
        fi
        display_cluster_info "$2"
        ;;

    *)
        echo "Threads-Agent Cluster Manager"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  list, ls              List all clusters"
        echo "  switch, use <name>    Switch to a different cluster"
        echo "  current               Show current active cluster"
        echo "  delete, rm <name>     Delete a cluster"
        echo "  resources, res [name] Show cluster resources"
        echo "  info <name>           Show detailed cluster info"
        echo "  cleanup               Remove orphaned metadata"
        echo ""
        echo "Examples:"
        echo "  $0 list                    # List all clusters"
        echo "  $0 switch threads-john     # Switch to john's cluster"
        echo "  $0 current                 # Show current cluster"
        echo "  $0 resources               # Show resources in current cluster"
        echo "  $0 delete threads-test     # Delete test cluster"
        ;;
esac
