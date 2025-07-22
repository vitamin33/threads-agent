#!/bin/bash
# Autopilot Mode - Set it and forget it
# Runs your entire business on autopilot with AI

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[AUTOPILOT]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }

MODE="${1:-start}"
PERSONA="${2:-ai-jesus}"
INTERVAL="${3:-3600}"  # Default 1 hour

case "$MODE" in
    start)
        log "🚁 Starting Autopilot Mode..."
        
        # Create autopilot script
        cat > /tmp/autopilot-loop.sh << 'EOF'
#!/bin/bash
while true; do
    echo "[$(date)] Running autopilot cycle..."
    
    # 1. Check trends
    TREND=$(just trend-check "AI" | head -1)
    
    # 2. Create viral content
    just create-viral "$PERSONA" "$TREND"
    
    # 3. Deploy if tests pass
    if just check; then
        just smart-deploy canary
    fi
    
    # 4. Analyze performance
    just ai-biz revenue
    
    # 5. Cache results
    just cache-set "autopilot:last-run" "$(date)"
    just cache-set "autopilot:last-trend" "$TREND"
    
    # Sleep
    sleep $INTERVAL
done
EOF
        
        chmod +x /tmp/autopilot-loop.sh
        nohup /tmp/autopilot-loop.sh > ~/.autopilot.log 2>&1 &
        echo $! > ~/.autopilot.pid
        
        success "Autopilot started! PID: $(cat ~/.autopilot.pid)"
        log "Generating content every $(($INTERVAL/3600)) hours"
        log "View logs: tail -f ~/.autopilot.log"
        ;;
    
    stop)
        if [ -f ~/.autopilot.pid ]; then
            kill $(cat ~/.autopilot.pid) 2>/dev/null || true
            rm -f ~/.autopilot.pid
            success "Autopilot stopped"
        else
            log "Autopilot not running"
        fi
        ;;
    
    status)
        if [ -f ~/.autopilot.pid ] && ps -p $(cat ~/.autopilot.pid) > /dev/null; then
            success "Autopilot running (PID: $(cat ~/.autopilot.pid))"
            echo ""
            echo "Last 5 operations:"
            tail -5 ~/.autopilot.log | grep -E "Running|created|deployed" || true
            
            echo ""
            echo "Last trend analyzed:"
            just cache-get "autopilot:last-trend" 2>/dev/null || echo "None"
        else
            log "Autopilot not running"
            echo "Start with: just autopilot start"
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|status} [persona] [interval_seconds]"
        echo "Example: $0 start ai-elon 7200  # Every 2 hours"
        ;;
esac