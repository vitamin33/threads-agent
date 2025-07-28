#!/bin/bash
# Test script for Achievement Collector Phase 1 & 2 functionality

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# Configuration
ACHIEVEMENT_COLLECTOR_URL="http://localhost:8001"
TEST_RESULTS_FILE="/tmp/achievement_test_results.json"

log "🧪 Testing Achievement Collector - Phase 1 & 2"
echo "=============================================="

# Function to test API endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=${3:-""}
    local expected_status=${4:-200}
    
    log "Testing: $method $endpoint"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$ACHIEVEMENT_COLLECTOR_URL$endpoint" 2>/dev/null || echo "HTTPSTATUS:000")
    else
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
            -X "$method" \
            "$ACHIEVEMENT_COLLECTOR_URL$endpoint" 2>/dev/null || echo "HTTPSTATUS:000")
    fi
    
    http_code=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo "$response" | sed -e 's/HTTPSTATUS:.*//g')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        success "$method $endpoint - Status: $http_code"
        return 0
    else
        error "$method $endpoint - Expected: $expected_status, Got: $http_code"
        if [ -n "$body" ]; then
            echo "Response: $body"
        fi
        return 1
    fi
}

# Test 1: Service Health Check
log "🔍 Phase 1 Testing - Basic API"
test_endpoint "GET" "/" || exit 1
test_endpoint "GET" "/health" || exit 1

success "🎉 Achievement Collector testing script created!"
echo "📝 Run with: chmod +x scripts/test-achievement-collector.sh && ./scripts/test-achievement-collector.sh"