#!/usr/bin/env python3
"""Integration test for the complete PR-based achievement system."""

import os

# Set environment variables before imports
os.environ["USE_SQLITE"] = "true"
os.environ["OPENAI_API_KEY"] = "test"

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.achievement_collector.db.config import get_db  # noqa: E402
from services.achievement_collector.services.comprehensive_pr_analyzer import (  # noqa: E402
    ComprehensivePRAnalyzer,
)
from services.achievement_collector.services.db_operations import (  # noqa: E402
    create_achievement_from_pr,
)
from services.achievement_collector.services.story_generator import StoryGenerator  # noqa: E402


async def test_full_integration():
    """Test the complete workflow from PR data to stored achievement."""

    print("🧪 Starting Integration Test: PR → Analysis → Stories → Database")

    # Mock PR data
    pr_data = {
        "number": 456,
        "title": "Add comprehensive user analytics dashboard",
        "body": "This PR adds a new analytics dashboard with real-time metrics, user behavior tracking, and A/B test results visualization.",
        "created_at": "2025-01-28T09:00:00Z",
        "merged_at": "2025-01-28T16:30:00Z",
        "html_url": "https://github.com/test/repo/pull/456",
        "user": {"login": "senior_dev"},
        "labels": [{"name": "feature"}, {"name": "analytics"}, {"name": "frontend"}],
        "requested_reviewers": [
            {"login": "tech_lead"},
            {"login": "product_manager"},
            {"login": "data_scientist"},
        ],
    }

    try:
        # Step 1: Comprehensive PR Analysis
        print("📊 Step 1: Analyzing PR with ComprehensivePRAnalyzer...")
        analyzer = ComprehensivePRAnalyzer()
        analysis = await analyzer.analyze_pr(pr_data, "base123", "head456")

        print(f"   ✅ Analysis completed with {len(analysis)} sections")
        print(f"   📈 Impact Score: {analysis['composite_scores']['overall_impact']}")
        print(
            f"   🏆 Technical Excellence: {analysis['composite_scores']['technical_excellence']}"
        )

        # Step 2: Generate Stories
        print("📝 Step 2: Generating persona-based stories...")
        story_generator = StoryGenerator()
        stories = await story_generator.generate_persona_stories(analysis)

        print(f"   ✅ Generated {len(stories)} story types")
        print(f"   📖 Available stories: {list(stories.keys())}")

        # Step 3: Create Achievement in Database
        print("💾 Step 3: Creating achievement in database...")
        db = next(get_db())

        # Add stories to pr_data for storage
        pr_data_with_stories = {**pr_data, "stories": stories}

        achievement = create_achievement_from_pr(db, pr_data_with_stories, analysis)

        print(f"   ✅ Achievement created with ID: {achievement.id}")
        print(f"   📝 Title: {achievement.title}")
        print(f"   🏷️  Category: {achievement.category}")
        print(f"   ⏱️  Duration: {achievement.duration_hours} hours")
        print(f"   💼 Business Value: {achievement.business_value}")
        print(f"   🎯 Portfolio Ready: {achievement.portfolio_ready}")

        # Step 4: Verify Data Completeness
        print("🔍 Step 4: Verifying data completeness...")

        checks = {
            "Has metadata": bool(achievement.metadata_json),
            "Has AI summaries": bool(achievement.ai_summary),
            "Has technical analysis": bool(achievement.ai_technical_analysis),
            "Has impact analysis": bool(achievement.ai_impact_analysis),
            "Has tags": len(achievement.tags or []) > 0,
            "Has skills": len(achievement.skills_demonstrated or []) > 0,
            "Has evidence": bool(achievement.evidence),
            "Has metrics": bool(achievement.metrics_after),
            "Valid impact score": 0 <= achievement.impact_score <= 100,
            "Valid complexity score": 0 <= achievement.complexity_score <= 100,
        }

        passed_checks = sum(checks.values())
        total_checks = len(checks)

        print(f"   ✅ Data Quality: {passed_checks}/{total_checks} checks passed")

        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"      {status} {check}")

        # Step 5: Test Achievement Retrieval
        print("🔍 Step 5: Testing achievement retrieval...")

        from services.achievement_collector.services.db_operations import (
            get_achievement_by_pr,
        )

        retrieved = get_achievement_by_pr(db, 456)

        if retrieved and retrieved.id == achievement.id:
            print("   ✅ Achievement successfully retrieved by PR number")
        else:
            print("   ❌ Failed to retrieve achievement by PR number")

        db.close()

        print("\n🎉 Integration Test PASSED!")
        print("   📊 Complete workflow: PR → Analysis → Stories → Database ✅")
        print("   🏗️  System ready for production PR-based achievement collection")

        return True

    except Exception as e:
        print(f"\n❌ Integration Test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_integration())
    sys.exit(0 if success else 1)
