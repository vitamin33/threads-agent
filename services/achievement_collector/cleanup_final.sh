#!/bin/bash
set -e

cd /Users/vitaliiserbyn/development/threads-agent

echo "🧹 Final cleanup of ci-monitor references..."

# Remove ci-monitor helm template if it still exists
if [ -f "chart/templates/ci-monitor.yaml" ]; then
    echo "Removing chart/templates/ci-monitor.yaml..."
    rm -f chart/templates/ci-monitor.yaml
fi

# Remove ci-monitor documentation
if [ -f "docs/ci-monitor-comparison.md" ]; then
    echo "Removing docs/ci-monitor-comparison.md..."
    rm -f docs/ci-monitor-comparison.md
fi

if [ -f "docs/ci-autofix-setup-guide.md" ]; then
    echo "Removing docs/ci-autofix-setup-guide.md..."
    rm -f docs/ci-autofix-setup-guide.md
fi

# Remove mypy_output.txt if exists
if [ -f "mypy_output.txt" ]; then
    echo "Removing mypy_output.txt..."
    rm -f mypy_output.txt
fi

# Stage all changes
git add -A

# Show status
echo -e "\n📊 Git status:"
git status --short

# Only commit if there are changes
if ! git diff --cached --quiet; then
    echo -e "\n📝 Creating commit..."
    git commit -m "chore: remove ci-monitor service and related files

- Remove ci-monitor Helm template
- Remove ci-monitor documentation files
- Clean up temporary files"

    echo -e "\n🚀 Pushing to remote..."
    git push
    
    echo -e "\n✅ Cleanup complete!"
else
    echo -e "\n✅ Nothing to commit - cleanup already done!"
fi