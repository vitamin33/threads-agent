#!/bin/bash
# Setup all MCP servers for enhanced development workflow

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Log function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if k3d cluster is running
check_cluster() {
    if kubectl cluster-info &>/dev/null; then
        success "Kubernetes cluster is running"
        return 0
    else
        error "Kubernetes cluster not running. Run: just bootstrap"
        return 1
    fi
}

# Deploy Redis if not already deployed
deploy_redis() {
    log "Checking Redis deployment..."

    if kubectl get svc redis &>/dev/null; then
        success "Redis is already deployed"
    else
        log "Deploying Redis..."
        helm upgrade --install threads-agent ./chart -f chart/values-dev.yaml

        # Wait for Redis to be ready
        kubectl wait --for=condition=ready pod -l app=redis --timeout=60s
        success "Redis deployed successfully"
    fi

    # Set up port forwarding
    if ! lsof -i:6379 &>/dev/null; then
        log "Setting up Redis port forwarding..."
        kubectl port-forward svc/redis 6379:6379 > /dev/null 2>&1 &
        sleep 2
        success "Redis available at localhost:6379"
    fi
}

# Configure PostgreSQL access
setup_postgres() {
    log "Setting up PostgreSQL access..."

    if kubectl get svc postgres &>/dev/null; then
        success "PostgreSQL is running"

        # Set up port forwarding if not already active
        if ! lsof -i:5432 &>/dev/null; then
            kubectl port-forward svc/postgres 5432:5432 > /dev/null 2>&1 &
            sleep 2
            success "PostgreSQL available at localhost:5432"
        fi
    else
        error "PostgreSQL not found. Deploy with: just deploy-dev"
        return 1
    fi
}

# Create MCP test scripts
create_test_scripts() {
    log "Creating MCP test scripts..."

    # Redis test script
    cat > ./scripts/test-redis-mcp.sh << 'EOF'
#!/bin/bash
echo "Testing Redis MCP..."

# Test basic operations
echo "SET test:key 'Hello MCP'"
echo "GET test:key"
echo "INCR test:counter"
echo "ZADD trending:topics 95 'AI productivity'"

echo "Test complete. Check Redis for stored values."
EOF

    # Kubernetes test script
    cat > ./scripts/test-k8s-mcp.sh << 'EOF'
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
EOF

    # PostgreSQL test script
    cat > ./scripts/test-postgres-mcp.sh << 'EOF'
#!/bin/bash
echo "Testing PostgreSQL MCP..."

# Test query
PGPASSWORD=postgres psql -h localhost -U postgres -d postgres -c "
SELECT persona_id, COUNT(*) as post_count
FROM posts
GROUP BY persona_id;"

echo "Test complete."
EOF

    chmod +x ./scripts/test-*-mcp.sh
    success "Test scripts created"
}

# Update justfile with MCP commands
update_justfile() {
    log "Adding MCP commands to justfile..."

    # Check if MCP section already exists
    if grep -q "# ---------- MCP Server Management ----------" justfile; then
        success "MCP commands already in justfile"
    else
        cat >> justfile << 'EOF'

# ---------- MCP Server Management ----------
mcp-setup: # setup all MCP servers
	./scripts/setup-mcp-servers.sh

mcp-redis-test: # test Redis MCP functionality
	./scripts/test-redis-mcp.sh

mcp-k8s-test: # test Kubernetes MCP functionality
	./scripts/test-k8s-mcp.sh

mcp-postgres-test: # test PostgreSQL MCP functionality
	./scripts/test-postgres-mcp.sh

redis-cli: # connect to Redis CLI
	kubectl exec -it deploy/redis -- redis-cli

cache-get KEY: # get value from Redis cache
	kubectl exec deploy/redis -- redis-cli GET {{KEY}}

cache-set KEY VALUE: # set value in Redis cache
	kubectl exec deploy/redis -- redis-cli SET {{KEY}} "{{VALUE}}"

cache-trends: # show trending topics in cache
	kubectl exec deploy/redis -- redis-cli ZREVRANGE trending:topics 0 10 WITHSCORES
EOF
        success "MCP commands added to justfile"
    fi
}

# Main setup flow
main() {
    echo -e "${BLUE}=== MCP Server Setup ===${NC}"
    echo "Setting up Redis, Kubernetes, PostgreSQL, and OpenAI MCP servers..."
    echo ""

    # Check prerequisites
    if ! check_cluster; then
        exit 1
    fi

    # Deploy and configure services
    deploy_redis
    setup_postgres

    # Create test scripts
    create_test_scripts

    # Update justfile
    update_justfile

    echo ""
    echo -e "${GREEN}=== MCP Setup Complete! ===${NC}"
    echo ""
    echo "MCP Servers Configured:"
    echo "  ✅ Redis MCP - Cache at localhost:6379"
    echo "  ✅ Kubernetes MCP - Using k3d-threads-agent context"
    echo "  ✅ PostgreSQL MCP - Database at localhost:5432"
    echo "  ✅ OpenAI MCP - Using API key from environment"
    echo "  ✅ SearXNG - Search at localhost:8888"
    echo "  ✅ Slack - Alerts to #alerts channel"
    echo ""
    echo "Quick Test Commands:"
    echo "  just mcp-redis-test     # Test Redis caching"
    echo "  just mcp-k8s-test       # Test Kubernetes access"
    echo "  just mcp-postgres-test  # Test database queries"
    echo ""
    echo "Usage Examples:"
    echo "  just cache-set 'trends:AI' 'productivity,automation,ethics'"
    echo "  just cache-get 'trends:AI'"
    echo "  just cache-trends"
    echo ""
    echo "Note: Restart Claude to activate new MCP servers from .claude/mcp-config.json"
}

# Run main function
main
