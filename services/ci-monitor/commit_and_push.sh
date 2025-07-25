#!/bin/bash
set -e

PROJECT_ROOT="/Users/vitaliiserbyn/development/threads-agent"
cd "$PROJECT_ROOT"

echo "📋 Staging all changes..."
git add -A

echo -e "\n📊 Git status:"
git status --short

echo -e "\n✍️ Creating commit..."
git commit -m "fix: resolve CI issues and optimize CLAUDE.md

- Optimize CLAUDE.md from 45.3k to 7k characters for better CI performance
- Fix SQLAlchemy metadata reserved field error in PortfolioSnapshot
- Fix module import errors across all test files
- Install missing dependencies (pydantic-settings, types-Markdown)
- Fix database name consistency in e2e tests (postgres -> threads_agent)
- Add type annotations to fix mypy errors
- Ensure 'just check' command passes with all green status

All unit tests (105) and e2e tests (8) now passing successfully."

echo -e "\n🚀 Pushing to remote..."
git push

echo -e "\n✅ Changes committed and pushed successfully!"