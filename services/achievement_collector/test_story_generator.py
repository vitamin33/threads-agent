#!/usr/bin/env python3
"""Test story generator."""

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

from services.achievement_collector.services.story_generator import StoryGenerator  # noqa: E402


async def test_story_generator():
    """Test story generation with mock responses."""

    generator = StoryGenerator()  # Mock mode auto-detected from OPENAI_API_KEY=test

    # Mock analysis data
    analysis = {
        "metadata": {
            "pr_number": 123,
            "title": "Optimize API performance with Redis caching",
            "description": "This PR implements Redis caching to reduce database load and improve API response times by 40%.",
            "author": "test_user",
        },
        "code_metrics": {
            "languages": {"Python": 150, "JavaScript": 50},
            "files_changed": 8,
            "total_lines_added": 200,
            "total_lines_deleted": 50,
            "complexity_reduction": 15,
        },
        "performance_metrics": {
            "latency_changes": {
                "reported": {"before": 200, "after": 120, "improvement_percentage": 40}
            }
        },
        "business_metrics": {
            "financial_impact": {"cost_savings": 25000},
            "user_impact": {"users_affected": 5000},
        },
        "team_metrics": {
            "collaboration": {"reviewers_count": 3, "cross_team_collaboration": True},
            "mentorship": {"teaching_moments": 2},
        },
        "composite_scores": {
            "overall_impact": 85,
            "technical_excellence": 78,
            "business_value": 90,
        },
    }

    try:
        # Test technical story generation
        technical_story = await generator.generate_technical_story(analysis)
        print("✅ Technical story generated")
        print(f"   Key points: {len(technical_story.get('key_points', []))}")
        print(f"   Has full story: {bool(technical_story.get('full_story'))}")

        # Test business story generation
        business_story = await generator.generate_business_story(
            analysis["metadata"], analysis["business_metrics"]
        )
        print("✅ Business story generated")
        print(f"   Key points: {len(business_story.get('key_points', []))}")
        print(f"   Has full story: {bool(business_story.get('full_story'))}")

        # Test leadership story generation
        leadership_story = await generator.generate_leadership_story(
            analysis["metadata"], analysis.get("team_metrics", {})
        )
        print("✅ Leadership story generated")
        print(f"   Key points: {len(leadership_story.get('key_points', []))}")
        print(f"   Has full story: {bool(leadership_story.get('full_story'))}")

        # Test comprehensive story generation (use full analysis dict)
        all_stories = await generator.generate_persona_stories(analysis)
        print("✅ Comprehensive story generation completed")
        print(f"   Stories generated: {list(all_stories.keys())}")

        # Verify all expected stories are present
        expected_stories = ["technical", "business", "leadership"]
        missing_stories = [
            story for story in expected_stories if story not in all_stories
        ]

        if missing_stories:
            print(f"⚠️  Missing stories: {missing_stories}")
        else:
            print("✅ All expected stories generated")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_story_generator())
    sys.exit(0 if success else 1)
