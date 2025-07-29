#!/usr/bin/env python3
"""Migration script to transition from commit-based to PR-based achievement tracking."""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("🔄 Achievement Tracking Migration Guide\n")

print(
    "This guide helps you transition from commit-based to PR-based achievement tracking.\n"
)

print("## Why PR-based tracking is better:\n")
print("1. **Quality over Quantity**: One achievement per feature, not per commit")
print("2. **Better Metrics**: Review time, discussions, iterations")
print("3. **Richer Context**: PR descriptions explain the 'why'")
print("4. **Team Collaboration**: Shows code review participation\n")

print("## Migration Steps:\n")

print("### 1. Update Environment Variables")
print("Replace these in your .env or start script:")
print("```bash")
print("# Old (commit-based)")
print("ENABLE_GIT_TRACKING=true")
print("MIN_LINES_FOR_ACHIEVEMENT=50")
print("")
print("# New (PR-based)")
print("ENABLE_GITHUB_TRACKING=true")
print("MIN_PR_CHANGES_FOR_ACHIEVEMENT=50")
print("PR_CHECK_INTERVAL=300  # Check every 5 minutes")
print("```\n")

print("### 2. Install GitHub CLI")
print("The PR tracker uses GitHub CLI for API access:")
print("```bash")
print("# macOS")
print("brew install gh")
print("")
print("# Linux")
print("sudo apt install gh  # or your package manager")
print("")
print("# Authenticate")
print("gh auth login")
print("```\n")

print("### 3. Update Auto-Tracker Script")
print("The start script now uses PR tracking:")
print("```bash")
print("python3 scripts/start-achievement-tracker.py")
print("```\n")

print("### 4. Optional: Setup GitHub Webhook")
print("For real-time PR tracking, add a webhook to your repo:")
print("1. Go to: https://github.com/{owner}/{repo}/settings/hooks")
print("2. Add webhook URL: https://your-domain.com/webhooks/github")
print("3. Select events: Pull requests, Push")
print("4. Set secret: GITHUB_WEBHOOK_SECRET env var\n")

print("### 5. Remove Git Post-Commit Hook")
print("The old commit hook is no longer needed:")
print("```bash")
print("rm .git/hooks/post-commit")
print("```\n")

print("### 6. Test the New System")
print("Run the demo to verify everything works:")
print("```bash")
print("python3 scripts/demo-github-pr-tracker.py")
print("```\n")

print("## What happens to existing achievements?\n")
print("- Existing commit-based achievements remain in your database")
print("- They will still appear in your portfolio")
print("- New achievements will be created from PRs only\n")

print("## Best Practices:\n")
print("1. **Write meaningful PR descriptions** - They become achievement descriptions")
print("2. **Use labels** - They help categorize achievements (feature, bugfix, etc.)")
print("3. **Get reviews** - More reviewers = higher complexity score")
print("4. **Use conventional PR titles** - feat:, fix:, perf: etc.\n")

print("✅ Migration guide complete!")
print("\nFor questions or issues, check the documentation or open an issue.")
