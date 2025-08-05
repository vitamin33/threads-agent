#!/bin/bash
# /scripts/validate-comment-monitoring-deployment.sh
# Validation script for Comment Monitoring Pipeline (CRA-235) Kubernetes deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE=${NAMESPACE:-default}
TIMEOUT=${TIMEOUT:-300}
CHART_PATH=${CHART_PATH:-./chart}

# Logging functions
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

# Check if required tools are installed
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    for tool in kubectl helm; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Validate Helm chart templates
validate_helm_templates() {
    log_info "Validating Helm chart templates..."
    
    # Test template rendering with comment monitoring enabled
    if ! helm template test-release $CHART_PATH \
        --values $CHART_PATH/values-dev.yaml \
        --set orchestrator.commentMonitoring.enabled=true \
        --set monitoring.prometheus.enabled=true \
        --dry-run > /dev/null; then
        log_error "Helm template validation failed"
        return 1
    fi
    
    log_success "Helm templates are valid"
}

# Validate database migrations
validate_database_migrations() {
    log_info "Validating database migration configuration..."
    
    # Check if migration file exists
    if [ ! -f "services/orchestrator/db/alembic/versions/008_add_comment_monitoring_tables.py" ]; then
        log_error "Comment monitoring migration file not found"
        return 1
    fi
    
    # Validate migration file syntax
    if ! python -m py_compile services/orchestrator/db/alembic/versions/008_add_comment_monitoring_tables.py; then
        log_error "Migration file has syntax errors"
        return 1
    fi
    
    log_success "Database migrations are valid"
}

# Check Kubernetes cluster connectivity
check_cluster_connectivity() {
    log_info "Checking Kubernetes cluster connectivity..."
    
    if ! kubectl cluster-info > /dev/null 2>&1; then
        log_error "Cannot connect to Kubernetes cluster"
        return 1
    fi
    
    log_success "Connected to Kubernetes cluster"
}

# Deploy comment monitoring pipeline
deploy_comment_monitoring() {
    log_info "Deploying comment monitoring pipeline..."
    
    # Install/upgrade with comment monitoring enabled
    if ! helm upgrade --install threads-agent-test $CHART_PATH \
        --namespace $NAMESPACE \
        --create-namespace \
        --values $CHART_PATH/values-dev.yaml \
        --set orchestrator.commentMonitoring.enabled=true \
        --set monitoring.prometheus.enabled=true \
        --set postgres.enabled=true \
        --set redis.enabled=true \
        --set fakeThreads.enabled=true \
        --timeout ${TIMEOUT}s \
        --wait; then
        log_error "Deployment failed"
        return 1
    fi
    
    log_success "Deployment completed"
}

# Validate deployment status
validate_deployment_status() {
    log_info "Validating deployment status..."
    
    # Check if orchestrator pods are running
    local ready_pods=$(kubectl get pods -n $NAMESPACE -l app=orchestrator -o jsonpath='{.items[*].status.containerStatuses[*].ready}' | grep -o true | wc -l)
    local total_pods=$(kubectl get pods -n $NAMESPACE -l app=orchestrator --no-headers | wc -l)
    
    if [ "$ready_pods" -eq 0 ] || [ "$ready_pods" -ne "$total_pods" ]; then
        log_error "Orchestrator pods are not ready ($ready_pods/$total_pods)"
        kubectl get pods -n $NAMESPACE -l app=orchestrator
        return 1
    fi
    
    log_success "All orchestrator pods are ready ($ready_pods/$total_pods)"
}

# Test database connectivity
test_database_connectivity() {
    log_info "Testing database connectivity..."
    
    # Get orchestrator pod
    local pod=$(kubectl get pods -n $NAMESPACE -l app=orchestrator -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$pod" ]; then
        log_error "No orchestrator pod found"
        return 1
    fi
    
    # Test database connection
    if ! kubectl exec -n $NAMESPACE $pod -- python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.environ['POSTGRES_DSN'])
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" > /dev/null; then
        log_error "Database connectivity test failed"
        return 1
    fi
    
    log_success "Database connectivity verified"
}

# Test comment monitoring tables
test_comment_monitoring_tables() {
    log_info "Testing comment monitoring database tables..."
    
    local pod=$(kubectl get pods -n $NAMESPACE -l app=orchestrator -o jsonpath='{.items[0].metadata.name}')
    
    # Check if comments table exists
    if ! kubectl exec -n $NAMESPACE $pod -- python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.environ['POSTGRES_DSN'])
    cursor = conn.cursor()
    cursor.execute(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'comments')\")
    exists = cursor.fetchone()[0]
    if not exists:
        raise Exception('comments table does not exist')
    print('Comments table exists')
    conn.close()
except Exception as e:
    print(f'Table check failed: {e}')
    exit(1)
" > /dev/null; then
        log_error "Comment monitoring tables test failed"
        return 1
    fi
    
    log_success "Comment monitoring tables verified"
}

# Test service endpoints
test_service_endpoints() {
    log_info "Testing service endpoints..."
    
    # Port forward orchestrator service
    kubectl port-forward -n $NAMESPACE svc/orchestrator 8080:8080 &
    local pf_pid=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Test health endpoint
    if ! curl -f http://localhost:8080/health > /dev/null 2>&1; then
        kill $pf_pid 2>/dev/null || true
        log_error "Health endpoint test failed"
        return 1
    fi
    
    # Test metrics endpoint
    if ! curl -f http://localhost:8080/metrics > /dev/null 2>&1; then
        kill $pf_pid 2>/dev/null || true
        log_error "Metrics endpoint test failed"
        return 1
    fi
    
    # Clean up port forward
    kill $pf_pid 2>/dev/null || true
    
    log_success "Service endpoints verified"
}

# Test Prometheus ServiceMonitor
test_prometheus_integration() {
    log_info "Testing Prometheus integration..."
    
    # Check if ServiceMonitor exists
    if ! kubectl get servicemonitor -n $NAMESPACE orchestrator > /dev/null 2>&1; then
        log_warning "ServiceMonitor not found (Prometheus may not be installed)"
        return 0
    fi
    
    log_success "Prometheus ServiceMonitor verified"
}

# Test autoscaling configuration
test_autoscaling_config() {
    log_info "Testing autoscaling configuration..."
    
    # Check if HPA exists (only if enabled)
    if kubectl get hpa -n $NAMESPACE orchestrator > /dev/null 2>&1; then
        log_success "HorizontalPodAutoscaler verified"
    else
        log_info "HorizontalPodAutoscaler not enabled (as expected for dev)"
    fi
}

# Test resource limits
test_resource_limits() {
    log_info "Testing resource limits..."
    
    local pod=$(kubectl get pods -n $NAMESPACE -l app=orchestrator -o jsonpath='{.items[0].metadata.name}')
    
    # Check resource requests and limits
    local resources=$(kubectl get pod -n $NAMESPACE $pod -o jsonpath='{.spec.containers[0].resources}')
    
    if [ -z "$resources" ] || [ "$resources" = "{}" ]; then
        log_warning "No resource limits configured"
    else
        log_success "Resource limits configured"
    fi
}

# Performance test
run_performance_test() {
    log_info "Running basic performance test..."
    
    # Port forward orchestrator service
    kubectl port-forward -n $NAMESPACE svc/orchestrator 8080:8080 &
    local pf_pid=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Simple load test - send multiple requests
    local success_count=0
    for i in {1..10}; do
        if curl -f -s http://localhost:8080/health > /dev/null; then
            ((success_count++))
        fi
        sleep 0.1
    done
    
    # Clean up port forward
    kill $pf_pid 2>/dev/null || true
    
    if [ $success_count -lt 8 ]; then
        log_error "Performance test failed ($success_count/10 requests succeeded)"
        return 1
    fi
    
    log_success "Performance test passed ($success_count/10 requests succeeded)"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test deployment..."
    
    # Only cleanup if we're in test mode
    if [ "${CLEANUP:-true}" = "true" ]; then
        helm uninstall threads-agent-test -n $NAMESPACE || true
        kubectl delete namespace $NAMESPACE || true
    fi
    
    log_info "Cleanup completed"
}

# Main validation function
main() {
    log_info "Starting Comment Monitoring Pipeline (CRA-235) validation..."
    log_info "Namespace: $NAMESPACE"
    log_info "Timeout: ${TIMEOUT}s"
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Run validation steps
    check_prerequisites
    validate_helm_templates
    validate_database_migrations
    check_cluster_connectivity
    deploy_comment_monitoring
    validate_deployment_status
    test_database_connectivity
    test_comment_monitoring_tables
    test_service_endpoints
    test_prometheus_integration
    test_autoscaling_config
    test_resource_limits
    run_performance_test
    
    log_success "All validation tests passed!"
    log_info "Comment Monitoring Pipeline is ready for production deployment"
}

# Run main function
main "$@"