#!/usr/bin/env python3
"""Integration test for achievement creation."""

import os
import sys
import asyncio
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_achievement_creation():
    """Test creating an achievement from scratch."""
    from services.achievement_collector.db.config import get_db, engine
    from services.achievement_collector.db.models import Base, Achievement
    from services.achievement_collector.api.schemas import AchievementCreate
    from services.achievement_collector.api.routes.achievements import (
        create_achievement_sync,
    )

    print("🔍 Testing Achievement Creation...")

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Create test achievement
    achievement_data = AchievementCreate(
        title="Test: Implemented Achievement Auto-Collection",
        category="feature",
        description="Successfully implemented git commit and Linear issue tracking with automatic achievement generation",
        started_at=datetime.now().replace(hour=10, minute=0),
        completed_at=datetime.now(),
        source_type="git",
        source_id="test_commit_123",
        tags=["test", "feature", "achievement-collector"],
        skills_demonstrated=["Python", "SQLAlchemy", "Testing", "Git Integration"],
        metrics_after={
            "files_changed": 10,
            "lines_added": 500,
            "lines_deleted": 50,
            "test_coverage": 95,
        },
        impact_score=85.0,
        complexity_score=75.0,
        portfolio_ready=True,
    )

    # Create achievement
    db = next(get_db())
    try:
        # Check if achievement already exists
        existing = db.query(Achievement).filter_by(source_id="test_commit_123").first()
        if existing:
            print(f"⚠️  Achievement already exists: {existing.title}")
            achievement = existing
        else:
            achievement = create_achievement_sync(db, achievement_data)
            print(f"✅ Created achievement: {achievement.title}")

        # Display achievement details
        print("\n📋 Achievement Details:")
        print(f"  ID: {achievement.id}")
        print(f"  Category: {achievement.category}")
        print(f"  Impact Score: {achievement.impact_score}")
        print(f"  Complexity Score: {achievement.complexity_score}")
        print(f"  Skills: {', '.join(achievement.skills_demonstrated)}")
        print(f"  Portfolio Ready: {achievement.portfolio_ready}")

        # Query all achievements
        all_achievements = db.query(Achievement).all()
        print(f"\n📊 Total achievements in database: {len(all_achievements)}")

        # Show recent achievements
        recent = (
            db.query(Achievement).order_by(Achievement.created_at.desc()).limit(5).all()
        )
        print("\n🕒 Recent achievements:")
        for ach in recent:
            print(
                f"  - {ach.title} ({ach.category}) - {ach.created_at.strftime('%Y-%m-%d %H:%M')}"
            )

    finally:
        db.close()

    print("\n✅ Integration test completed!")


async def test_github_pr_tracker_e2e():
    """Test GitHub PR tracker end-to-end."""
    from services.achievement_collector.services.github_pr_tracker import (
        GitHubPRTracker,
    )

    print("\n\n🔍 Testing GitHub PR Tracker E2E...")

    tracker = GitHubPRTracker()

    # Create a test PR
    test_pr = {
        "number": 999,
        "title": "feat(achievement): add PR-based achievement tracking",
        "body": "## Summary\nRefactored achievement system to track PRs instead of individual commits.\n\n## Changes\n- Replaced git commit tracker with GitHub PR tracker\n- Added PR metrics analysis\n- Updated scoring algorithms",
        "author": {"login": "testuser"},
        "mergedAt": datetime.now().isoformat() + "Z",
        "additions": 450,
        "deletions": 200,
        "files": [
            {
                "filename": "services/achievement_collector/services/github_pr_tracker.py"
            },
            {
                "filename": "services/achievement_collector/tests/test_github_pr_tracker.py"
            },
            {"filename": "scripts/test-achievement-integration.py"},
        ],
        "labels": [{"name": "feature"}, {"name": "enhancement"}],
        "reviews": [
            {"login": "reviewer1", "state": "APPROVED"},
            {"login": "reviewer2", "state": "APPROVED"},
        ],
        "commits": [
            {"sha": "abc123"},
            {"sha": "def456"},
            {"sha": "ghi789"},
            {"sha": "jkl012"},
        ],
        "url": "https://github.com/test/repo/pull/999",
    }

    # Check if significant
    if tracker._is_significant_pr(test_pr):
        print("✅ PR is significant")
        print(f"   - Total changes: {test_pr['additions'] + test_pr['deletions']}")
        print(f"   - Files changed: {len(test_pr['files'])}")
        print(f"   - Reviews: {len(test_pr['reviews'])}")
        print(f"   - Commits: {len(test_pr['commits'])}")

        # Create achievement
        await tracker._create_pr_achievement(test_pr)
        print(f"✅ Achievement created for PR #{test_pr['number']}")
    else:
        print("❌ PR not significant enough")


async def main():
    """Run all integration tests."""
    print("🚀 Achievement Collector Integration Test\n")

    # Set up test database
    os.environ["DATABASE_URL"] = f"sqlite:///{project_root}/test_achievements.db"

    # Run tests
    await test_achievement_creation()
    await test_github_pr_tracker_e2e()

    print("\n\n✅ All integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
