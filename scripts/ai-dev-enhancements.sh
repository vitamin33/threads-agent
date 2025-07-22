#!/bin/bash
# AI Development Enhancement Tools

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

case "${1:-help}" in
    hot-reload)
        log "Starting Persona Hot-Reload System..."
        cd services/persona_runtime
        python persona_hot_reload.py &
        HOT_PID=$!
        success "Hot-reload running at http://localhost:8001"
        echo "PID: $HOT_PID"
        echo $HOT_PID > .hot-reload.pid
        ;;
    
    auto-test)
        log "Generating AI-powered tests..."
        python -c "
from services.common.ai_test_generator import auto_generate_tests
import asyncio
persona = '${2:-ai-jesus}'
asyncio.run(auto_generate_tests(persona))
print(f'Tests generated for {persona}')
"
        success "Tests generated in tests/auto_generated/"
        ;;
    
    dashboard)
        log "Starting Real-time Dashboard..."
        cd services/dashboard
        python realtime_dashboard.py &
        DASH_PID=$!
        success "Dashboard running at http://localhost:8002"
        echo "PID: $DASH_PID"
        echo $DASH_PID > .dashboard.pid
        sleep 2
        open http://localhost:8002 || xdg-open http://localhost:8002
        ;;
    
    smart-deploy)
        log "Starting Smart Deployment..."
        ./scripts/smart-deploy.sh ${2:-canary}
        ;;
    
    stop-all)
        log "Stopping all AI dev tools..."
        [ -f .hot-reload.pid ] && kill $(cat .hot-reload.pid) && rm .hot-reload.pid
        [ -f .dashboard.pid ] && kill $(cat .dashboard.pid) && rm .dashboard.pid
        success "All tools stopped"
        ;;
    
    *)
        echo "AI Development Enhancement Tools"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  hot-reload      Start persona hot-reload system"
        echo "  auto-test       Generate AI-powered tests for persona"
        echo "  dashboard       Start real-time performance dashboard"
        echo "  smart-deploy    Run intelligent deployment"
        echo "  stop-all        Stop all running tools"
        echo ""
        echo "Examples:"
        echo "  $0 hot-reload"
        echo "  $0 auto-test ai-elon"
        echo "  $0 dashboard"
        echo "  $0 smart-deploy blue-green"
        ;;
esac