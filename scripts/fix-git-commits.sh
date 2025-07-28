#!/bin/bash
# Remove Claude co-authorship from git commits

set -e

echo "🔧 Configuring git to remove Claude co-authorship..."

# Create git commit template without co-author
cat > ~/.gitmessage << 'EOF'
# Commit message format:
# <type>: <subject>
# 
# <body>
# 
# Types: feat, fix, docs, style, refactor, test, chore
EOF

# Set global commit template
git config --global commit.template ~/.gitmessage

echo "✅ Git configured to use standard authorship only"
echo ""
echo "📝 To fix the last commit (remove co-author):"
echo "   git commit --amend"
echo ""
echo "📝 To update CLAUDE.md instructions for Claude Code:"
echo "   Update CLAUDE.md to instruct Claude not to add co-authorship"
echo ""
echo "Your commits will now only show your git config user as author."