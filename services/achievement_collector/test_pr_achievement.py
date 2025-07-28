#!/usr/bin/env python3
"""Test PR achievement creation manually."""

import os

# Set environment variables before imports
os.environ["USE_SQLITE"] = "true"
os.environ["OPENAI_API_KEY"] = "test"

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.achievement_collector.db.config import engine, get_db
from services.achievement_collector.db.models import Base
from services.achievement_collector.services.db_operations import (
    create_achievement_from_pr,
)


def test_pr_achievement_creation():
    """Test creating PR achievement."""

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Mock PR data
    pr_data = {
        "number": 123,
        "title": "Optimize API performance",
        "body": "Reduced latency by implementing caching",
        "created_at": "2025-01-28T10:00:00Z",
        "merged_at": "2025-01-28T14:00:00Z",
        "html_url": "https://github.com/test/repo/pull/123",
        "user": {"login": "test_user"},
    }

    # Mock analysis data
    analysis = {
        "metadata": pr_data,
        "code_metrics": {
            "languages": {"Python": 50, "JavaScript": 30},
            "files_changed": 5,
            "total_lines_added": 100,
            "total_lines_deleted": 50,
            "change_categories": {"feature": 3, "refactor": 2},
        },
        "performance_metrics": {
            "latency_changes": {
                "reported": {"before": 200, "after": 150, "improvement_percentage": 25}
            }
        },
        "business_metrics": {
            "financial_impact": {"cost_savings": 15000},
            "user_impact": {"users_affected": 1000},
        },
        "quality_metrics": {"test_coverage": {"delta": 10, "after": 85}},
        "composite_scores": {"overall_impact": 85, "technical_excellence": 78},
        "ai_insights": {
            "summary": "Significant performance improvement",
            "impact_analysis": ["Reduced server load", "Improved user experience"],
            "technical_analysis": [
                "Implemented Redis caching",
                "Optimized database queries",
            ],
        },
    }

    # Create achievement
    db = next(get_db())
    try:
        achievement = create_achievement_from_pr(db, pr_data, analysis)
        print(f"✅ Created achievement: {achievement.id}")
        print(f"   Title: {achievement.title}")
        print(f"   Category: {achievement.category}")
        print(f"   Impact Score: {achievement.impact_score}")
        print(f"   Source: {achievement.source_type} - {achievement.source_id}")
        print(f"   Metadata: {achievement.metadata_json is not None}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_pr_achievement_creation()
    sys.exit(0 if success else 1)