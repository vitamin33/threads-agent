#!/bin/bash
# Automated Trend Detection Workflow for Threads-Agent
# Discovers trends and triggers content generation automatically

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
ORCHESTRATOR_URL=${ORCHESTRATOR_URL:-"http://localhost:8080"}
SEARXNG_URL=${SEARXNG_URL:-"http://localhost:8888"}
TREND_CHECK_INTERVAL=${TREND_CHECK_INTERVAL:-3600}  # Check every hour
PERSONAS=("ai-jesus" "ai-elon")
TOPICS_FILE="${TOPICS_FILE:-./data/trending_topics.json}"

# Ensure data directory exists
mkdir -p ./data

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

# Check if SearXNG is running
check_searxng() {
    if curl -s "${SEARXNG_URL}/search?q=test&format=json" > /dev/null 2>&1; then
        success "SearXNG is running at ${SEARXNG_URL}"
        return 0
    else
        error "SearXNG is not running. Start it with: just searxng-start"
        return 1
    fi
}

# Check if orchestrator is running
check_orchestrator() {
    if curl -s "${ORCHESTRATOR_URL}/health" | grep -q "ok"; then
        success "Orchestrator is running at ${ORCHESTRATOR_URL}"
        return 0
    else
        error "Orchestrator is not running. Deploy with: just deploy-dev"
        return 1
    fi
}

# Discover trends for a topic
discover_trends() {
    local topic="$1"
    local timeframe="${2:-day}"
    
    log "Discovering trends for: ${topic} (${timeframe})"
    
    response=$(curl -s -X POST "${ORCHESTRATOR_URL}/search/trends" \
        -H "Content-Type: application/json" \
        -d "{
            \"topic\": \"${topic}\",
            \"timeframe\": \"${timeframe}\",
            \"limit\": 5
        }")
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq -r '.data.trends[] | "\(.topic) (score: \(.score))"'
        
        # Save trends to file
        echo "$response" | jq '.data.trends' > "${TOPICS_FILE}.${topic// /_}.json"
        return 0
    else
        error "Failed to discover trends for ${topic}"
        return 1
    fi
}

# Analyze viral patterns
analyze_viral() {
    local topic="$1"
    
    log "Analyzing viral patterns for: ${topic}"
    
    response=$(curl -s -X POST "${ORCHESTRATOR_URL}/search/competitive" \
        -H "Content-Type: application/json" \
        -d "{
            \"topic\": \"${topic}\",
            \"platform\": \"threads\",
            \"analyze_patterns\": true
        }")
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq -r '.data.common_keywords[:5][]' 2>/dev/null || echo "No keywords found"
        return 0
    else
        error "Failed to analyze viral patterns"
        return 1
    fi
}

# Generate content based on trends
generate_trending_content() {
    local persona="$1"
    local topic="$2"
    
    log "Generating trending content for ${persona} on topic: ${topic}"
    
    response=$(curl -s -X POST "${ORCHESTRATOR_URL}/search/enhanced-task" \
        -H "Content-Type: application/json" \
        -d "{
            \"persona_id\": \"${persona}\",
            \"topic\": \"${topic}\",
            \"enable_search\": true,
            \"trend_timeframe\": \"day\"
        }")
    
    if [ $? -eq 0 ]; then
        task_id=$(echo "$response" | jq -r '.task_id')
        success "Created enhanced task: ${task_id}"
        echo "$task_id"
        return 0
    else
        error "Failed to create enhanced task"
        return 1
    fi
}

# Main trend detection loop
run_trend_detection() {
    local base_topics=("AI and technology" "Mental health and wellness" "Productivity tips" "Future predictions")
    
    while true; do
        log "=== Starting Trend Detection Cycle ==="
        
        # Check each base topic
        for topic in "${base_topics[@]}"; do
            echo -e "\n${YELLOW}Topic: ${topic}${NC}"
            
            # Discover trends
            if trends=$(discover_trends "$topic" "day"); then
                echo "Found trends:"
                echo "$trends" | head -5
                
                # Analyze viral patterns
                echo -e "\nViral keywords:"
                analyze_viral "$topic"
                
                # Generate content for each persona based on top trend
                top_trend=$(echo "$trends" | head -1 | cut -d' ' -f1)
                if [ -n "$top_trend" ]; then
                    for persona in "${PERSONAS[@]}"; do
                        log "Generating content for ${persona} about ${top_trend}"
                        generate_trending_content "$persona" "${topic} ${top_trend}"
                        sleep 2  # Rate limiting
                    done
                fi
            fi
            
            echo -e "\n---"
            sleep 5  # Small delay between topics
        done
        
        log "=== Trend Detection Cycle Complete ==="
        log "Next check in ${TREND_CHECK_INTERVAL} seconds..."
        sleep "$TREND_CHECK_INTERVAL"
    done
}

# Dashboard mode - show current trends
show_dashboard() {
    clear
    echo -e "${BLUE}=== Threads-Agent Trend Dashboard ===${NC}"
    echo -e "Updated: $(date)"
    echo ""
    
    # Check services
    check_searxng > /dev/null 2>&1 && searxng_status="${GREEN}✓${NC}" || searxng_status="${RED}✗${NC}"
    check_orchestrator > /dev/null 2>&1 && orch_status="${GREEN}✓${NC}" || orch_status="${RED}✗${NC}"
    
    echo -e "Services: SearXNG $searxng_status | Orchestrator $orch_status"
    echo ""
    
    # Show trends for each topic
    for topic in "AI and technology" "Mental health" "Productivity"; do
        echo -e "${YELLOW}${topic}:${NC}"
        
        if [ -f "${TOPICS_FILE}.${topic// /_}.json" ]; then
            jq -r '.[] | "  • \(.topic) (score: \(.score))"' "${TOPICS_FILE}.${topic// /_}.json" 2>/dev/null | head -3
        else
            echo "  No data available"
        fi
        echo ""
    done
    
    # Show recent tasks
    echo -e "${YELLOW}Recent Enhanced Tasks:${NC}"
    # This would query actual task status in production
    echo "  • Task abc123: ai-jesus - AI and spirituality (completed)"
    echo "  • Task def456: ai-elon - Space technology (in progress)"
}

# Single trend check
check_single_trend() {
    local topic="$1"
    
    if ! check_searxng || ! check_orchestrator; then
        exit 1
    fi
    
    discover_trends "$topic" "week"
    echo ""
    echo "Viral patterns:"
    analyze_viral "$topic"
}

# Main script logic
case "${1:-}" in
    "start")
        log "Starting automated trend detection workflow..."
        if check_searxng && check_orchestrator; then
            run_trend_detection
        else
            error "Please ensure all services are running"
            exit 1
        fi
        ;;
    
    "check")
        if [ -z "${2:-}" ]; then
            error "Usage: $0 check <topic>"
            exit 1
        fi
        check_single_trend "$2"
        ;;
    
    "dashboard")
        show_dashboard
        ;;
    
    "generate")
        if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
            error "Usage: $0 generate <persona> <topic>"
            exit 1
        fi
        if check_orchestrator; then
            generate_trending_content "$2" "$3"
        fi
        ;;
    
    *)
        echo "Threads-Agent Trend Detection Workflow"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start              Start automated trend detection loop"
        echo "  check <topic>      Check trends for a specific topic"
        echo "  dashboard          Show trend dashboard"
        echo "  generate <persona> <topic>  Generate trending content"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 check 'AI and mental health'"
        echo "  $0 generate ai-jesus 'spirituality and technology'"
        echo ""
        echo "Environment variables:"
        echo "  ORCHESTRATOR_URL   Orchestrator service URL (default: http://localhost:8080)"
        echo "  SEARXNG_URL        SearXNG service URL (default: http://localhost:8888)"
        echo "  TREND_CHECK_INTERVAL  Seconds between trend checks (default: 3600)"
        ;;
esac