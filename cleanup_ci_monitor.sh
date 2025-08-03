#!/bin/bash
set -e

PROJECT_ROOT="$(pwd)"
cd "$PROJECT_ROOT"

echo "🧹 Cleaning up remaining ci-monitor references..."

# Remove documentation files
echo "Removing ci-monitor documentation..."
rm -f docs/ci-monitor-comparison.md
rm -f docs/ci-autofix-setup-guide.md

# Remove any mypy_output.txt that might have been created
rm -f mypy_output.txt

# Show current status
echo -e "\n📊 Current git status:"
git status --short

echo -e "\n✅ Cleanup complete!"