#!/bin/bash
# AI-Powered Business Intelligence System
# 80/20 Principle: Focus on metrics that drive revenue

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
metric() { echo -e "${CYAN}📊${NC} $1: ${YELLOW}$2${NC}"; }

case "${1:-dashboard}" in
    revenue-optimizer)
        log "🤖 AI Revenue Optimization Analysis"

        # Get current metrics
        engagement=$(kubectl exec deploy/postgres -- psql -U postgres -d postgres -t -c "SELECT AVG(engagement_rate) FROM posts WHERE created_at > NOW() - INTERVAL '24 hours';" 2>/dev/null | tr -d ' ' || echo "0")
        posts_today=$(kubectl exec deploy/postgres -- psql -U postgres -d postgres -t -c "SELECT COUNT(*) FROM posts WHERE created_at > NOW() - INTERVAL '24 hours';" 2>/dev/null | tr -d ' ' || echo "0")

        # Calculate projections
        revenue_per_post=0.50  # $0.50 per post average
        current_mrr=$(echo "$posts_today * 30 * $revenue_per_post" | bc)
        target_mrr=20000

        metric "Current Engagement" "${engagement}%"
        metric "Posts Today" "$posts_today"
        metric "Current MRR" "$${current_mrr}"
        metric "Target MRR" "$${target_mrr}"
        
        # AI recommendations
        log "🎯 AI Recommendations:"
        if (( $(echo "$engagement < 0.06" | bc -l) )); then
            echo "  • Boost engagement with trending topics (+2x revenue)"
            echo "  • Use search-enhanced content generation"
        fi
        
        if (( posts_today < 10 )); then
            echo "  • Increase content velocity to 10+ posts/day"
            echo "  • Enable autopilot mode: just autopilot-start"
        fi
        
        gap=$(echo "$target_mrr - $current_mrr" | bc)
        echo "  • Revenue gap to close: \$$gap"
        ;;
        
    dashboard)
        log "📊 AI Business Intelligence Dashboard"
        echo "====================================="
        
        # Key metrics with AI insights
        engagement=$(kubectl exec deploy/postgres -- psql -U postgres -d postgres -t -c "SELECT AVG(engagement_rate) FROM posts WHERE created_at > NOW() - INTERVAL '24 hours';" 2>/dev/null | tr -d ' ' || echo "0.045")
        posts_count=$(kubectl exec deploy/postgres -- psql -U postgres -d postgres -t -c "SELECT COUNT(*) FROM posts WHERE created_at > NOW() - INTERVAL '24 hours';" 2>/dev/null | tr -d ' ' || echo "8")
        
        metric "🎯 Engagement Rate" "$(echo "scale=1; $engagement * 100" | bc)% (target: 6%+)"
        metric "🚀 Content Velocity" "$posts_count posts/day (target: 10+)"
        
        # AI-powered insights
        log "🤖 AI Insights:"
        if (( $(echo "$engagement > 0.06" | bc -l) )); then
            echo "  ✅ Engagement above target - scale content production"
        else
            echo "  ⚠️  Engagement below target - use trend-enhanced posts"
        fi
        
        # Revenue projection
        daily_revenue=$(echo "scale=2; $posts_count * 100 * $engagement * 1.50" | bc)
        monthly_revenue=$(echo "scale=0; $daily_revenue * 30" | bc)
        
        metric "💰 Daily Revenue" "\$$daily_revenue"
        metric "📈 Monthly Projection" "\$$monthly_revenue (target: \$20,000)"
        
        # Quick actions
        echo
        log "⚡ Quick Actions:"
        echo "  • just create-viral ai-jesus 'trending topic'  - Create viral content"
        echo "  • just trend-check 'your niche'               - Find trending topics"
        echo "  • just autopilot-start                        - Enable autopilot mode"
        ;;
        
    trends)
        log "📈 Trending Topics Analysis"
        
        # Check for cached trends
        trending_topics=$(redis-cli -h localhost -p 6379 KEYS "trends:*" 2>/dev/null | head -5 || echo "")
        
        if [ -n "$trending_topics" ]; then
            echo "🔥 Hot Topics:"
            echo "$trending_topics" | while read topic; do
                relevance=$(redis-cli -h localhost -p 6379 GET "$topic:relevance" 2>/dev/null || echo "0.8")
                echo "  • $(echo $topic | sed 's/trends://') (relevance: $relevance)"
            done
        else
            echo "⚠️  No cached trends - run: just trend-start"
        fi
        ;;
        
    optimize)*)
        log "🎯 Revenue Optimization Recommendations"
        
        # Analyze current performance
        kubectl exec deploy/postgres -- psql -U postgres -d postgres -c "
SELECT 
    persona_id,
    COUNT(*) as posts,
    AVG(engagement_rate) as avg_engagement,
    SUM(revenue_impact) as total_revenue
FROM posts 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY persona_id
ORDER BY total_revenue DESC;
"
        
        echo
        log "💡 Optimization Strategy:"
        echo "  1. Focus on highest-performing personas"
        echo "  2. Use search-enhanced content for trending topics"
        echo "  3. Increase posting frequency during peak hours"
        echo "  4. A/B test different content formats"
        ;;
        
    *)
        echo "Usage: $0 {dashboard|revenue-optimizer|trends|optimize}"
        echo ""
        echo "Commands:"
        echo "  dashboard        - Main business intelligence dashboard"
        echo "  revenue-optimizer - AI-powered revenue optimization"
        echo "  trends          - Trending topics analysis"
        echo "  optimize        - Revenue optimization recommendations"
        exit 1
        ;;
esac
