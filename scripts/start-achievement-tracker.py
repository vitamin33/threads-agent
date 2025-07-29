#!/usr/bin/env python3
"""Start the achievement auto-tracker service."""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set environment variables for testing
os.environ["GIT_REPO_PATH"] = project_root
os.environ["MIN_PR_CHANGES_FOR_ACHIEVEMENT"] = "50"  # Min changes for PR achievement
os.environ["ENABLE_GITHUB_TRACKING"] = "true"
os.environ["PR_CHECK_INTERVAL"] = "300"  # Check every 5 minutes
os.environ["LINEAR_CHECK_INTERVAL"] = "60"  # Check every minute for testing

# Database URL for SQLite (for testing)
os.environ["DATABASE_URL"] = f"sqlite:///{project_root}/test_achievements.db"

print("🚀 Starting Achievement Auto-Tracker")
print(f"📁 Repository: {project_root}")
print(f"🗄️  Database: {os.environ['DATABASE_URL']}")
print(
    f"📊 Min PR changes for achievement: {os.environ['MIN_PR_CHANGES_FOR_ACHIEVEMENT']}"
)
print(f"⏱️  PR check interval: {os.environ['PR_CHECK_INTERVAL']}s")
print("")

try:
    import asyncio
    from services.achievement_collector.services.auto_tracker import main

    # Run the tracker
    asyncio.run(main())

except KeyboardInterrupt:
    print("\n\n👋 Shutting down Achievement Auto-Tracker")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()
