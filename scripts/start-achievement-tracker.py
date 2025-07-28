#!/usr/bin/env python3
"""Start the achievement auto-tracker service."""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set environment variables for testing
os.environ["GIT_REPO_PATH"] = project_root
os.environ["MIN_LINES_FOR_ACHIEVEMENT"] = "20"  # Lower threshold for testing
os.environ["ENABLE_GIT_TRACKING"] = "true"
os.environ["LINEAR_CHECK_INTERVAL"] = "60"  # Check every minute for testing

# Database URL for SQLite (for testing)
os.environ["DATABASE_URL"] = f"sqlite:///{project_root}/test_achievements.db"

print("🚀 Starting Achievement Auto-Tracker")
print(f"📁 Repository: {project_root}")
print(f"🗄️  Database: {os.environ['DATABASE_URL']}")
print(f"📊 Min lines for achievement: {os.environ['MIN_LINES_FOR_ACHIEVEMENT']}")
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
