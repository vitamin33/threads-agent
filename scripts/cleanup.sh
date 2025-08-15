#!/bin/bash

# Project Cleanup Script
# Removes temporary files, cache, and test artifacts

set -e

echo "🧹 Starting project cleanup..."

# Function to safely remove files/directories
safe_remove() {
    if [ -e "$1" ]; then
        echo "  Removing: $1"
        rm -rf "$1"
    fi
}

# Python cache cleanup
echo "📁 Cleaning Python cache files..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true

# Test artifacts
echo "🧪 Cleaning test artifacts..."
safe_remove "htmlcov/"
safe_remove ".coverage"
safe_remove ".pytest_cache/"
safe_remove "coverage.xml"

# Quality logs older than 7 days
echo "📊 Cleaning old quality logs..."
if [ -d ".quality-logs" ]; then
    find .quality-logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
fi

# Docker cleanup (if requested)
if [ "$1" = "--docker" ]; then
    echo "🐳 Cleaning Docker resources..."
    docker system prune -f 2>/dev/null || true
fi

# Kubernetes cleanup (if requested)
if [ "$1" = "--k8s" ]; then
    echo "☸️  Cleaning Kubernetes resources..."
    kubectl delete pods --field-selector=status.phase=Succeeded 2>/dev/null || true
    kubectl delete pods --field-selector=status.phase=Failed 2>/dev/null || true
fi

# Temporary files
echo "🗑️  Cleaning temporary files..."
safe_remove "setup.log"
safe_remove "temp_portfolio.json"
safe_remove "temp_achievements.json"
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "temp_*" -not -path "./.venv/*" -delete 2>/dev/null || true

# Node.js cleanup (if exists)
if [ -f "package.json" ]; then
    echo "📦 Cleaning Node.js cache..."
    safe_remove "node_modules/.cache"
    safe_remove ".next"
    safe_remove "dist"
    safe_remove "build"
fi

# Git cleanup
echo "🔧 Cleaning Git artifacts..."
git gc --prune=now --quiet 2>/dev/null || true

echo "✅ Cleanup completed!"
echo "💾 Disk space freed: $(du -sh . | cut -f1)"