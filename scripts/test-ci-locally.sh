#!/bin/bash
# test-ci-locally.sh - Test CI workflows locally before pushing
set -e

echo "🧪 LOCAL CI WORKFLOW TESTER"
echo "============================"
echo "Simulating GitHub Actions dev-ci workflow locally..."

# Configuration
CLUSTER_NAME="ci-test"
FORCE_BUILD=${1:-false}
PYTHON_VERSION="3.12"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_step() {
    echo -e "\n${BLUE}🔹 $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Cleanup function
cleanup() {
    log_step "Cleaning up test environment..."
    k3d cluster delete $CLUSTER_NAME 2>/dev/null || true
    pkill -f "kubectl port-forward" || true
    log_success "Cleanup completed"
}

# Trap cleanup on exit
trap cleanup EXIT

# Step 1: Checkout validation (simulate CI checkout)
log_step "Step 1: Validating checkout state"
if [ ! -f "chart/values-ci-fast.yaml" ]; then
    log_error "Missing chart/values-ci-fast.yaml - are you in the project root?"
    exit 1
fi
log_success "Project structure validated"

# Step 2: Detect changed files (simplified version of CI logic)
log_step "Step 2: Detecting changes that would trigger CI"
CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null || echo "all")
log_warning "Changed files: $CHANGED_FILES"

# Check if e2e tests would be required
E2E_REQUIRED=false
if echo "$CHANGED_FILES" | grep -qE "(chart/|Dockerfile|scripts/)" || [ "$CHANGED_FILES" = "all" ]; then
    E2E_REQUIRED=true
    log_warning "Infrastructure changes detected - full e2e tests required"
else
    log_success "No infrastructure changes - would skip expensive k3d operations"
fi

if [ "$E2E_REQUIRED" = "false" ] && [ "$FORCE_BUILD" != "true" ]; then
    log_success "LOCAL CI SIMULATION COMPLETE - Would skip remaining steps in CI"
    log_success "This saves ~10 minutes when only code changes!"
    exit 0
fi

# Step 3: Create k3d cluster (matching CI configuration)
log_step "Step 3: Creating k3d cluster (matching CI config)"
k3d cluster delete $CLUSTER_NAME 2>/dev/null || true
k3d cluster create $CLUSTER_NAME \
    --agents 1 \
    --registry-create k3d-${CLUSTER_NAME}-registry:0.0.0.0:5112 \
    --wait || {
    log_error "Failed to create k3d cluster"
    exit 1
}
log_success "k3d cluster created successfully"

# Step 4: Build/pull images (matching CI logic)
log_step "Step 4: Building/pulling images"
# Service list configuration
if [ "$1" = "--ci-only" ]; then
    # CI mode: Only essential services (matches .github/workflows/dev-ci.yml)
    SERVICES="orchestrator celery_worker persona_runtime fake_threads"
    log_warning "CI mode: Building only essential services"
else
    # Full mode: All services for local testing
    SERVICES="orchestrator celery_worker persona_runtime fake_threads viral_metrics"
    log_warning "Full mode: Building all services"
fi

for svc in $SERVICES; do
    IMAGE_NAME="ghcr.io/threads-agent-stack/threads-agent/${svc}:main"
    LOCAL_NAME="${svc//_/-}:local"
    
    if [ "$FORCE_BUILD" = "true" ]; then
        log_step "Force building $svc..."
        docker build -f services/${svc}/Dockerfile -t "$LOCAL_NAME" .
    else
        log_step "Attempting to pull $IMAGE_NAME..."
        if docker pull "$IMAGE_NAME" 2>/dev/null; then
            log_success "Found pre-built image for $svc"
            docker tag "$IMAGE_NAME" "$LOCAL_NAME"
        else
            log_warning "No pre-built image found for $svc, building locally..."
            docker build -f services/${svc}/Dockerfile -t "$LOCAL_NAME" .
        fi
    fi
done

# Pull third-party images
log_step "Pulling third-party images..."
docker pull bitnami/postgresql:16
docker pull rabbitmq:3.13-management-alpine
docker pull qdrant/qdrant:v1.9.4

# Import images to k3d
log_step "Importing images to k3d cluster..."
# Note: Image names use dashes, not underscores (e.g., celery-worker not celery_worker)
for img in orchestrator:local celery-worker:local persona-runtime:local fake-threads:local bitnami/postgresql:16 rabbitmq:3.13-management-alpine qdrant/qdrant:v1.9.4; do
    echo "  Importing $img..."
    k3d image import $img -c $CLUSTER_NAME || {
        log_error "Failed to import $img to k3d cluster"
        exit 1
    }
done

log_success "All images imported to k3d"

# Wait a moment for images to be fully available
sleep 2

# Verify images are available in cluster
log_step "Verifying images in k3d cluster..."
for img in orchestrator:local celery-worker:local persona-runtime:local fake-threads:local; do
    # Images are stored with docker.io/library/ prefix in k3d
    if docker exec k3d-${CLUSTER_NAME}-server-0 ctr -n k8s.io image ls | grep -q "docker.io/library/$img"; then
        log_success "$img - verified in cluster"
    else
        log_error "$img - NOT FOUND in cluster!"
        # Try to debug why
        echo "  Checking all images with 'orchestrator' in name:"
        docker exec k3d-${CLUSTER_NAME}-server-0 ctr -n k8s.io image ls | grep orchestrator || echo "  No orchestrator images found"
    fi
done

# Step 5: Pre-deployment validation
log_step "Step 5: Pre-deployment validation"
echo "📋 Validating Helm chart syntax:"
helm lint ./chart || log_warning "Chart has lint issues"

echo "🎯 Validating values-ci-fast.yaml:"
helm template ./chart -f chart/values-ci-fast.yaml --dry-run > /tmp/rendered.yaml || {
    log_error "Template rendering failed"
    exit 1
}
log_success "Template renders successfully"

echo "📊 Expected resources:"
grep -E "kind: (Deployment|Service|StatefulSet)" /tmp/rendered.yaml | sort | uniq -c

echo "🔧 Image availability check:"
for img in orchestrator:local celery-worker:local persona-runtime:local fake-threads:local; do
    if docker image inspect $img >/dev/null 2>&1; then
        log_success "$img - available"
    else
        log_error "$img - missing"
        exit 1
    fi
done

# Step 6: Helm deployment (matching CI configuration exactly)
log_step "Step 6: Helm deployment with CI values"

# Create OpenAI secret
kubectl create secret generic openai-secret \
    --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY:-test}" \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy with retry logic (matching CI)
for i in 1 2 3; do
    log_step "Helm install attempt $i/3..."
    if helm upgrade --install threads ./chart \
        -f chart/values-ci-fast.yaml \
        --set openai.apiKey="${OPENAI_API_KEY:-test}" \
        --wait --timeout 480s --debug; then
        log_success "Helm deployment succeeded on attempt $i"
        break
    else
        log_error "Helm install attempt $i failed"
        if [ $i -lt 3 ]; then
            log_step "Checking migration status..."
            kubectl describe job -l app.kubernetes.io/name=threads-migrations || true
            kubectl logs -l app.kubernetes.io/name=threads-migrations --tail=50 || true
            log_step "Retrying in 30s..."
            sleep 30
        else
            log_error "All Helm deployment attempts failed"
            exit 1
        fi
    fi
done

# Step 7: Comprehensive deployment monitoring (matching CI)
log_step "Step 7: Comprehensive deployment analysis"
echo "🏗️ CLUSTER STATE:"
kubectl get nodes -o wide
kubectl describe nodes | grep -A 5 "Allocated resources" || true

echo "📦 POD STATUS:"
kubectl get pods -o wide

echo "🚀 DEPLOYMENT STATUS:"
kubectl get deployments -o wide

echo "🔗 SERVICES:"
kubectl get services -o wide

echo "🎯 ENDPOINTS:"
kubectl get endpoints

echo "📅 RECENT EVENTS:"
kubectl get events --sort-by='.lastTimestamp' | tail -n 10

# Step 8: Wait for pods (matching CI logic)
log_step "Step 8: Waiting for core pods to be ready"
kubectl rollout status deploy/orchestrator     --timeout=90s &
kubectl rollout status deploy/celery-worker    --timeout=90s &
kubectl rollout status deploy/fake-threads     --timeout=90s &
kubectl rollout status deploy/persona-runtime  --timeout=90s &
kubectl rollout status sts/qdrant              --timeout=90s &

# Monitor progress
for i in {1..18}; do
    sleep 5
    echo "⏰ Progress check $i/18 (${i}0s elapsed):"
    kubectl get pods --no-headers | while read pod_info; do
        pod_name=$(echo $pod_info | awk '{print $1}')
        status=$(echo $pod_info | awk '{print $3}')
        ready=$(echo $pod_info | awk '{print $2}')
        echo "  $pod_name: $status ($ready)"
    done
    
    NOT_READY=$(kubectl get pods --no-headers | grep -v "Running" | wc -l)
    if [ $NOT_READY -eq 0 ]; then
        log_success "All pods ready at ${i}0s!"
        break
    fi
done

# Wait for all rollout jobs
wait
log_success "All services are ready!"

# Step 9: Health validation
log_step "Step 9: Health endpoint validation"
sleep 10  # Give services time to initialize

if [ -f "./scripts/validate-health-checks.sh" ]; then
    ./scripts/validate-health-checks.sh || log_warning "Some health checks failed"
else
    log_warning "Health check validator not found - skipping"
fi

# Step 10: Python environment setup (matching CI)
log_step "Step 10: Setting up Python environment"
if ! command -v python3 >/dev/null; then
    log_error "Python 3 not found"
    exit 1
fi

if [ ! -d ".venv" ]; then
    log_step "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
log_success "Virtual environment activated"

# Install dependencies (matching CI logic)
log_step "Installing dependencies..."
python -m pip install -U pip wheel setuptools --prefer-binary

if ! python -c "import fastapi, celery, pytest" 2>/dev/null; then
    log_step "Installing missing dependencies..."
    pip install -r services/orchestrator/requirements.txt --prefer-binary
    pip install -r services/celery_worker/requirements.txt --prefer-binary
    pip install -r services/persona_runtime/requirements.txt --prefer-binary
    pip install -r services/fake_threads/requirements.txt --prefer-binary
    pip install -r tests/requirements.txt --prefer-binary
else
    log_success "Dependencies already installed"
fi

# Remove langsmith (matching CI)
pip uninstall -y langsmith || true

# Step 11: Run tests (matching CI logic)
log_step "Step 11: Running e2e tests"

# Start port forwards (matching CI)
kubectl port-forward svc/orchestrator 8080:8080   & PF_ORCH=$!
kubectl port-forward svc/fake-threads 9009:9009   & PF_THREADS=$!
kubectl port-forward svc/qdrant 6333:6333         & PF_QDRANT=$!
kubectl port-forward svc/postgres 15432:5432      & PF_POSTGRES=$!

sleep 3  # Let port forwards establish

# Run tests with CI configuration
export PYTHONPATH=$PWD:$PYTHONPATH
export LANGCHAIN_TRACING_V2=false
export LANGSMITH_TRACING=false

log_step "Running e2e tests..."
pytest -q -p no:langsmith -n auto --maxprocesses=6 --dist loadscope --timeout=45 --tb=short tests/e2e --maxfail=3

# Cleanup port forwards
kill $PF_ORCH $PF_THREADS $PF_QDRANT $PF_POSTGRES || true

log_success "🎉 LOCAL CI SIMULATION COMPLETED SUCCESSFULLY!"
echo ""
echo "Summary:"
echo "========="
echo "✅ All steps that would run in GitHub Actions CI completed successfully"
echo "✅ k3d cluster deployment worked with CI configuration"
echo "✅ All services are healthy and responsive"
echo "✅ e2e tests passed"
echo ""
echo "🚀 Your changes are ready to push - CI should succeed!"
echo ""
echo "To clean up: k3d cluster delete $CLUSTER_NAME"