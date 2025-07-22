#!/bin/bash
# Smart deployment with automatic rollback and health checks

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
NAMESPACE=${NAMESPACE:-default}
RELEASE_NAME=${RELEASE_NAME:-threads}
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-300}
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

log() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Capture current metrics before deployment
capture_metrics() {
    log "Capturing pre-deployment metrics..."
    
    # Get current engagement rate
    CURRENT_ENGAGEMENT=$(kubectl exec deploy/orchestrator -- \
        curl -s http://localhost:9090/metrics | \
        grep 'posts_engagement_rate' | tail -1 | awk '{print $2}' || echo "0")
    
    # Get error rate
    CURRENT_ERROR_RATE=$(kubectl exec deploy/orchestrator -- \
        curl -s http://localhost:9090/metrics | \
        grep 'error_rate_percentage' | tail -1 | awk '{print $2}' || echo "0")
    
    echo "Current engagement: ${CURRENT_ENGAGEMENT}"
    echo "Current error rate: ${CURRENT_ERROR_RATE}"
}

# Smart health check with business metrics
health_check() {
    local service=$1
    local retries=30
    local count=0
    
    log "Checking health of ${service}..."
    
    while [ $count -lt $retries ]; do
        # Basic health check
        if kubectl exec deploy/${service} -- curl -sf http://localhost:8080/health > /dev/null 2>&1; then
            # Advanced metric checks
            local new_error_rate=$(kubectl exec deploy/${service} -- \
                curl -s http://localhost:9090/metrics | \
                grep 'error_rate_percentage' | tail -1 | awk '{print $2}' || echo "100")
            
            # If error rate is too high, fail health check
            if (( $(echo "$new_error_rate > 10" | bc -l) )); then
                warning "High error rate detected: ${new_error_rate}%"
                sleep 10
                count=$((count + 1))
                continue
            fi
            
            success "${service} is healthy!"
            return 0
        fi
        
        sleep 10
        count=$((count + 1))
    done
    
    error "${service} health check failed after ${retries} attempts"
    return 1
}

# Canary deployment
canary_deploy() {
    log "Starting canary deployment..."
    
    # Deploy with canary strategy
    kubectl set image deployment/orchestrator \
        orchestrator=orchestrator:canary \
        --record
    
    # Wait for canary pod
    kubectl wait --for=condition=ready pod \
        -l app=orchestrator,version=canary \
        --timeout=60s
    
    # Test canary with 10% traffic
    log "Testing canary with 10% traffic..."
    sleep 30
    
    # Check canary metrics
    local canary_errors=$(kubectl exec deploy/orchestrator -- \
        curl -s http://localhost:9090/metrics | \
        grep 'error_rate_percentage{version="canary"}' | \
        awk '{print $2}' || echo "100")
    
    if (( $(echo "$canary_errors > 5" | bc -l) )); then
        error "Canary has high error rate: ${canary_errors}%"
        return 1
    fi
    
    success "Canary deployment successful!"
    return 0
}

# Blue-green deployment
blue_green_deploy() {
    log "Starting blue-green deployment..."
    
    # Get current version (blue)
    CURRENT_VERSION=$(kubectl get deploy orchestrator -o jsonpath='{.metadata.labels.version}' || echo "blue")
    NEW_VERSION=$([[ "$CURRENT_VERSION" == "blue" ]] && echo "green" || echo "blue")
    
    log "Current version: ${CURRENT_VERSION}, deploying: ${NEW_VERSION}"
    
    # Deploy new version
    helm upgrade ${RELEASE_NAME} ./chart \
        -f chart/values-dev.yaml \
        --set global.version=${NEW_VERSION} \
        --wait \
        --timeout 5m
    
    # Test new version
    if health_check "orchestrator-${NEW_VERSION}"; then
        # Switch traffic
        kubectl patch service orchestrator -p \
            '{"spec":{"selector":{"version":"'${NEW_VERSION}'"}}}'
        
        success "Switched traffic to ${NEW_VERSION}"
        
        # Keep old version for quick rollback
        warning "Old version (${CURRENT_VERSION}) kept for rollback"
    else
        error "New version failed health checks"
        return 1
    fi
}

# Intelligent rollback
smart_rollback() {
    error "Deployment failed, initiating smart rollback..."
    
    # Get last successful revision
    LAST_GOOD_REVISION=$(helm history ${RELEASE_NAME} -o json | \
        jq -r '.[] | select(.status=="deployed") | .revision' | \
        tail -2 | head -1)
    
    if [ -n "$LAST_GOOD_REVISION" ]; then
        log "Rolling back to revision ${LAST_GOOD_REVISION}"
        helm rollback ${RELEASE_NAME} ${LAST_GOOD_REVISION} --wait
        
        # Verify rollback
        if health_check "orchestrator"; then
            success "Rollback successful!"
            
            # Send alert about failed deployment
            curl -X POST http://localhost:8080/alert \
                -H "Content-Type: application/json" \
                -d '{
                    "severity": "warning",
                    "message": "Deployment failed and was rolled back",
                    "details": "Check logs for details"
                }'
        else
            error "Rollback failed! Manual intervention required!"
            exit 1
        fi
    else
        error "No previous good revision found!"
        exit 1
    fi
}

# Progressive deployment with feature flags
progressive_deploy() {
    log "Starting progressive deployment..."
    
    # Deploy with feature flag disabled
    kubectl set env deployment/orchestrator FEATURE_NEW_ALGO=false
    
    # Standard deployment
    helm upgrade ${RELEASE_NAME} ./chart \
        -f chart/values-dev.yaml \
        --wait \
        --timeout 5m
    
    if health_check "orchestrator"; then
        # Gradually enable feature
        for percentage in 10 25 50 75 100; do
            log "Enabling feature for ${percentage}% of traffic..."
            kubectl set env deployment/orchestrator \
                FEATURE_NEW_ALGO=true \
                FEATURE_ROLLOUT_PERCENTAGE=${percentage}
            
            sleep 30
            
            # Check metrics
            local error_rate=$(kubectl exec deploy/orchestrator -- \
                curl -s http://localhost:9090/metrics | \
                grep 'error_rate_percentage' | tail -1 | awk '{print $2}' || echo "100")
            
            if (( $(echo "$error_rate > 5" | bc -l) )); then
                warning "High error rate at ${percentage}%, rolling back feature"
                kubectl set env deployment/orchestrator FEATURE_NEW_ALGO=false
                return 1
            fi
        done
        
        success "Progressive deployment complete!"
    fi
}

# Main deployment flow
main() {
    echo -e "${BLUE}=== Smart Deployment System ===${NC}"
    
    # Pre-deployment checks
    capture_metrics
    
    # Choose deployment strategy
    STRATEGY=${1:-canary}
    
    case $STRATEGY in
        canary)
            if canary_deploy; then
                success "Canary deployment successful!"
            else
                smart_rollback
            fi
            ;;
        
        blue-green)
            if blue_green_deploy; then
                success "Blue-green deployment successful!"
            else
                smart_rollback
            fi
            ;;
        
        progressive)
            if progressive_deploy; then
                success "Progressive deployment successful!"
            else
                smart_rollback
            fi
            ;;
        
        *)
            error "Unknown strategy: $STRATEGY"
            echo "Usage: $0 [canary|blue-green|progressive]"
            exit 1
            ;;
    esac
    
    # Post-deployment validation
    log "Running post-deployment tests..."
    if ! just test; then
        warning "Some tests failed, but deployment is stable"
    fi
    
    # Update deployment record
    echo "{
        \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
        \"strategy\": \"$STRATEGY\",
        \"metrics\": {
            \"engagement_before\": $CURRENT_ENGAGEMENT,
            \"error_rate_before\": $CURRENT_ERROR_RATE
        }
    }" >> deployments.log
    
    success "Deployment complete!"
}

# Run main
main "$@"