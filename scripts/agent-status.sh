#\!/bin/bash
echo "🤖 4-Agent Status Dashboard"
echo "==========================="
echo ""
echo "Worktrees:"
for wt in ../wt-a*; do
  [ -d "$wt" ] && echo "  $(basename $wt): $(git -C "$wt" branch --show-current) ($(git -C "$wt" status -s | wc -l | tr -d ' ') changes)"
done
echo ""
echo "Locks:"
[ -d .locks ] && ls .locks/.common-lock-* 2>/dev/null | xargs -n1 basename 2>/dev/null || echo "  No locks"
