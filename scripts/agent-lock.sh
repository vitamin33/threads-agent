#\!/bin/bash
AGENT_ID=${1:-$AGENT_ID}
ACTION=${2:-status}
[ "$ACTION" = "lock" ] && touch .locks/.common-lock-$AGENT_ID && echo "✅ Locked for $AGENT_ID"
[ "$ACTION" = "unlock" ] && rm -f .locks/.common-lock-$AGENT_ID && echo "🔓 Unlocked"
[ "$ACTION" = "status" ] && (ls .locks/.common-lock-* 2>/dev/null || echo "No locks")
