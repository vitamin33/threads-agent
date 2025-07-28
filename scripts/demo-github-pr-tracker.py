#!/usr/bin/env python3
"""Demo script for GitHub PR tracker functionality."""

import os
import sys
import asyncio
import subprocess
import json

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def demo_pr_tracker():
    """Demonstrate GitHub PR tracker functionality."""
    from services.achievement_collector.services.github_pr_tracker import (
        GitHubPRTracker,
    )
    from services.achievement_collector.db.config import get_db, engine
    from services.achievement_collector.db.models import Base, Achievement

    print("🔍 GitHub PR Tracker Demo\n")

    # Create tables if needed
    Base.metadata.create_all(bind=engine)

    # Create tracker
    tracker = GitHubPRTracker()

    # Check gh CLI availability
    try:
        result = subprocess.run(
            ["gh", "--version"], capture_output=True, text=True, check=True
        )
        print("✅ GitHub CLI is installed")
        print(f"   {result.stdout.strip()}\n")
    except subprocess.CalledProcessError:
        print("⚠️  GitHub CLI (gh) not found. Please install it:")
        print("   brew install gh")
        print("   gh auth login\n")
        return

    # Try to get recent merged PRs
    print("📋 Checking for recent merged PRs...")
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "merged",
                "--limit",
                "5",
                "--json",
                "number,title,author,additions,deletions,mergedAt",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        prs = json.loads(result.stdout)

        if prs:
            print(f"Found {len(prs)} recently merged PRs:\n")

            for pr in prs:
                print(f"  PR #{pr['number']}: {pr['title']}")
                print(f"     Author: {pr['author']['login']}")
                print(f"     Changes: +{pr['additions']} -{pr['deletions']}")
                print(f"     Merged: {pr['mergedAt'][:10]}")
                print()
        else:
            print("No recently merged PRs found")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting PRs: {e}")
        print("   Make sure you're in a git repository with GitHub remote")

    # Demo with mock PR data
    print("\n📊 Demo: Processing a mock PR...\n")

    mock_pr = {
        "number": 52,
        "title": "feat(achievement): implement auto-collection system",
        "body": """## Summary
- Implemented Git commit tracker for automatic achievement creation
- Added Linear issue/epic tracking with MCP-ready integration
- Created LinkedIn auto-publisher with AI content generation

## Features
1. Automatic tracking of development work
2. Portfolio-ready achievement generation
3. Social media integration
""",
        "author": {"login": "developer"},
        "mergedAt": "2025-01-28T15:30:00Z",
        "additions": 2500,
        "deletions": 500,
        "files": [
            {"filename": "services/achievement_collector/services/git_tracker.py"},
            {"filename": "services/achievement_collector/services/linear_tracker.py"},
            {
                "filename": "services/achievement_collector/publishers/linkedin_publisher.py"
            },
            {"filename": "services/achievement_collector/tests/test_git_tracker.py"},
            {"filename": "services/achievement_collector/tests/test_linear_tracker.py"},
        ],
        "labels": [
            {"name": "feature"},
            {"name": "enhancement"},
            {"name": "ai-powered"},
        ],
        "reviews": [
            {"login": "reviewer1", "state": "APPROVED"},
            {"login": "reviewer2", "state": "APPROVED"},
            {"login": "reviewer3", "state": "APPROVED"},
        ],
        "commits": [
            {"sha": "abc123"},
            {"sha": "def456"},
            {"sha": "ghi789"},
            {"sha": "jkl012"},
            {"sha": "mno345"},
            {"sha": "pqr678"},
        ],
        "url": "https://github.com/example/repo/pull/52",
    }

    # Check significance
    is_significant = tracker._is_significant_pr(mock_pr)
    print(f"✨ PR Significance: {'Yes' if is_significant else 'No'}")

    if is_significant:
        # Extract skills
        skills = tracker._extract_skills_from_pr(mock_pr)
        print(f"\n🛠️  Extracted Skills: {', '.join(skills[:8])}")

        # Determine category
        category = tracker._determine_category_from_pr(mock_pr)
        print(f"\n🏷️  Category: {category}")

        # Calculate scores
        impact_score = tracker._calculate_pr_impact_score(mock_pr)
        complexity_score = tracker._calculate_complexity_score(
            {
                "files_changed": len(mock_pr["files"]),
                "total_changes": mock_pr["additions"] + mock_pr["deletions"],
                "reviewers_count": len(mock_pr["reviews"]),
                "commits_count": len(mock_pr["commits"]),
            }
        )

        print("\n📈 Scores:")
        print(f"   Impact: {impact_score}/100")
        print(f"   Complexity: {complexity_score}/100")
        print(f"   Portfolio Ready: {'Yes' if impact_score >= 70 else 'No'}")

    # Show achievements in database
    print("\n\n📚 Achievements in Database:")
    db = next(get_db())
    try:
        pr_achievements = (
            db.query(Achievement)
            .filter_by(source_type="github_pr")
            .order_by(Achievement.created_at.desc())
            .limit(5)
            .all()
        )

        if pr_achievements:
            for ach in pr_achievements:
                print(f"\n🏆 {ach.title}")
                print(f"   Source: PR {ach.source_id}")
                print(f"   Impact: {ach.impact_score}/100")
                print(f"   Skills: {', '.join(ach.skills_demonstrated[:5])}")
        else:
            print("   No PR achievements found yet")

    finally:
        db.close()

    print("\n\n✅ GitHub PR Tracker demo completed!")


async def main():
    """Run the demo."""
    print("🚀 Achievement Collector - GitHub PR Tracker Demo\n")

    # Set up test database
    os.environ["DATABASE_URL"] = f"sqlite:///{project_root}/test_achievements.db"

    await demo_pr_tracker()


if __name__ == "__main__":
    asyncio.run(main())
