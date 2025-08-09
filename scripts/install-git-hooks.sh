#!/bin/bash
# Install git hooks for pre-push quality checks

set -e

HOOKS_DIR=".git/hooks"
PRE_PUSH_HOOK="$HOOKS_DIR/pre-push"

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Create pre-push hook
cat > "$PRE_PUSH_HOOK" << 'EOF'
#!/bin/bash
# Pre-push hook: Run quick checks before pushing

echo "🔍 Running pre-push checks..."

# 1. Check for debug prints
if grep -r "print(" services/ --include="*.py" | grep -v "# noqa" | grep -v "__pycache__"; then
    echo "❌ Found debug print statements. Please remove them."
    exit 1
fi

# 2. Check for merge conflicts
if grep -r "<<<<<<< HEAD" . --exclude-dir=.git; then
    echo "❌ Found merge conflict markers"
    exit 1
fi

# 3. Run quick format check (if ruff is installed)
if command -v ruff &> /dev/null; then
    echo "🧹 Running ruff check..."
    if ! ruff check . --select=E,W,F --quiet; then
        echo "❌ Ruff found issues. Run 'ruff check .' to see details"
        exit 1
    fi
fi

# 4. Check for large files
LARGE_FILES=$(find . -type f -size +5M -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*")
if [ -n "$LARGE_FILES" ]; then
    echo "❌ Found large files (>5MB):"
    echo "$LARGE_FILES"
    echo "Consider using Git LFS or excluding them"
    exit 1
fi

# 5. Validate no secrets
if grep -r "OPENAI_API_KEY\s*=\s*['\"][^'\"]\+['\"]" . --include="*.py" --include="*.yml" --include="*.yaml" --exclude-dir=.git; then
    echo "❌ Found hardcoded API keys. Use environment variables instead."
    exit 1
fi

echo "✅ All pre-push checks passed!"
EOF

# Make hook executable
chmod +x "$PRE_PUSH_HOOK"

echo "✅ Git hooks installed successfully!"
echo "   Pre-push hook will run quick checks before each push"
echo ""
echo "To bypass hooks in emergency: git push --no-verify"