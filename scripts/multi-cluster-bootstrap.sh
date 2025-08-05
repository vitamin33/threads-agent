#!/bin/bash

# Multi-cluster bootstrap script for threads-agent
# Creates named clusters based on git config for better isolation

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get developer name from git config
get_developer_name() {
    local git_name=$(git config user.name 2>/dev/null || echo "")
    if [ -z "$git_name" ]; then
        log_error "Git user.name not configured. Please set it with: git config user.name 'Your Name'"
        exit 1
    fi
    
    # Convert to lowercase and replace spaces with hyphens
    echo "$git_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g'
}

# Main function
main() {
    log_info "🚀 Starting multi-cluster bootstrap for threads-agent"
    
    # Get developer name
    DEV_NAME=$(get_developer_name)
    CLUSTER_NAME="threads-agent-${DEV_NAME}"
    
    log_info "Developer: $(git config user.name)"
    log_info "Cluster name: ${CLUSTER_NAME}"
    
    # Check if cluster already exists
    if k3d cluster list | grep -q "^${CLUSTER_NAME}"; then
        log_warning "Cluster '${CLUSTER_NAME}' already exists"
        read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deleting existing cluster..."
            k3d cluster delete "${CLUSTER_NAME}"
        else
            log_info "Using existing cluster '${CLUSTER_NAME}'"
            kubectl config use-context "k3d-${CLUSTER_NAME}"
            log_success "Switched to cluster: ${CLUSTER_NAME}"
            return 0
        fi
    fi
    
    # Create the cluster
    log_info "Creating k3d cluster: ${CLUSTER_NAME}"
    
    k3d cluster create "${CLUSTER_NAME}" \
        --api-port 6444 \
        --port "8080:80@loadbalancer" \
        --port "8443:443@loadbalancer" \
        --agents 1 \
        --registry-create "${CLUSTER_NAME}-registry:0.0.0.0:5111"
    
    log_success "✅ Multi-cluster '${CLUSTER_NAME}' created successfully!"
    
    # Set kubectl context
    kubectl config use-context "k3d-${CLUSTER_NAME}"
    
    # Display cluster info
    echo ""
    log_info "📋 Cluster Information:"
    echo "  • Name: ${CLUSTER_NAME}"
    echo "  • Context: k3d-${CLUSTER_NAME}"
    echo "  • Registry: ${CLUSTER_NAME}-registry:5111"
    echo "  • Load Balancer: localhost:8080 -> cluster:80"
    echo "  • API Server: localhost:6444"
    
    # Show available clusters
    echo ""
    log_info "📊 Available threads-agent clusters:"
    k3d cluster list | grep threads-agent || echo "  None found"
    
    echo ""
    log_success "🎉 Multi-cluster setup complete!"
    log_info "Next steps:"
    echo "  1. Deploy services: just deploy-dev"
    echo "  2. Switch clusters: just cluster-switch <name>"
    echo "  3. List clusters: just cluster-list"
    echo "  4. Current cluster: just cluster-current"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"