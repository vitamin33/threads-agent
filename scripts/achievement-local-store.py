#!/usr/bin/env python3
"""
Local Achievement Storage Script
Store achievements in SQLite file that persists outside of k3d
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add service path
sys.path.append(str(Path(__file__).parent.parent))

from services.achievement_collector.db.models import Achievement
from services.achievement_collector.db.sqlite_config import (
    get_sqlite_db,
    init_sqlite_db,
)


def store_ci_achievement():
    """Store the CI improvement achievement"""

    # Initialize SQLite database
    db_path = init_sqlite_db()

    # Create achievement
    achievement_data = {
        "title": "Reduced CI/CD Pipeline Time by 66%",
        "description": """Optimized threads-agent CI/CD pipeline through intelligent parallelization, 
smart caching, and auto-fix mechanisms. Reduced average build time from 15 minutes to 5 minutes, 
saving 200+ developer hours monthly.""",
        "category": "optimization",
        "started_at": datetime(2025, 1, 20),
        "completed_at": datetime(2025, 1, 25),
        "duration_hours": 120,
        "source_type": "manual",
        "source_id": "ci-optimization-2025",
        "tags": ["ci/cd", "optimization", "automation", "k8s", "github-actions"],
        "skills_demonstrated": [
            "DevOps",
            "CI/CD",
            "Performance Optimization",
            "Kubernetes",
            "Shell Scripting",
        ],
        "impact_score": 85.0,
        "complexity_score": 75.0,
        "business_value": 50000.0,
        "time_saved_hours": 200.0,
        "portfolio_ready": True,
        "evidence": {
            "before_metrics": {
                "avg_build_time_min": 15,
                "test_run_time_min": 8,
                "deploy_time_min": 7,
                "manual_fixes_per_week": 10,
            },
            "after_metrics": {
                "avg_build_time_min": 5,
                "test_run_time_min": 2,
                "deploy_time_min": 3,
                "manual_fixes_per_week": 1,
            },
            "improvements": [
                "Implemented test parallelization (80% faster)",
                "Added smart Docker layer caching (70% cache hits)",
                "Created auto-fix system for common failures",
                "Optimized Kubernetes deployments with Helm",
            ],
            "kpis_improved": {
                "time_reduction_percent": 66,
                "cost_savings_monthly": 5000,
                "developer_hours_saved": 200,
                "deployment_reliability": 99.5,
            },
        },
    }

    # Store in SQLite
    db = next(get_sqlite_db())

    try:
        # Check if already exists
        existing = (
            db.query(Achievement)
            .filter(Achievement.source_id == "ci-optimization-2025")
            .first()
        )

        if existing:
            print(f"✅ Achievement already stored with ID: {existing.id}")
            return existing

        # Create new achievement
        achievement = Achievement(**achievement_data)
        db.add(achievement)
        db.commit()
        db.refresh(achievement)

        print(
            f"""
✅ Achievement stored successfully!

ID: {achievement.id}
Title: {achievement.title}
Impact Score: {achievement.impact_score}
Business Value: ${achievement.business_value:,.0f}
Time Saved: {achievement.time_saved_hours} hours

Database location: {db_path}

This achievement is now permanently stored and will survive:
- k3d cluster restarts
- Docker restarts  
- System reboots

To view all achievements:
python scripts/achievement-local-store.py --list
"""
        )

        return achievement

    except Exception as e:
        print(f"❌ Error storing achievement: {e}")
        db.rollback()
    finally:
        db.close()


def list_achievements():
    """List all stored achievements"""

    db = next(get_sqlite_db())

    try:
        achievements = db.query(Achievement).all()

        if not achievements:
            print("No achievements stored yet.")
            return

        print(f"\n📊 Stored Achievements ({len(achievements)} total)\n")
        print("-" * 80)

        total_value = 0
        total_hours_saved = 0

        for a in achievements:
            print(f"ID: {a.id}")
            print(f"Title: {a.title}")
            print(f"Category: {a.category}")
            print(
                f"Date: {a.completed_at.strftime('%Y-%m-%d') if a.completed_at else 'In Progress'}"
            )
            print(f"Impact: {a.impact_score}/100")
            print(
                f"Value: ${a.business_value:,.0f}"
                if a.business_value
                else "Value: Not calculated"
            )
            print(
                f"Time Saved: {a.time_saved_hours} hours" if a.time_saved_hours else ""
            )
            print("-" * 80)

            if a.business_value:
                total_value += a.business_value
            if a.time_saved_hours:
                total_hours_saved += a.time_saved_hours

        print(f"\n💰 Total Business Value: ${total_value:,.0f}")
        print(f"⏱️  Total Time Saved: {total_hours_saved:,.0f} hours")

    finally:
        db.close()


def export_achievements():
    """Export achievements to JSON for backup"""

    db = next(get_sqlite_db())

    try:
        achievements = db.query(Achievement).all()

        export_data = []
        for a in achievements:
            data = {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "category": a.category,
                "started_at": a.started_at.isoformat() if a.started_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                "impact_score": a.impact_score,
                "business_value": a.business_value,
                "time_saved_hours": a.time_saved_hours,
                "tags": a.tags,
                "skills_demonstrated": a.skills_demonstrated,
                "evidence": a.evidence,
            }
            export_data.append(data)

        # Save to file
        export_path = (
            Path.home() / ".threads-agent" / "achievements" / "achievements_export.json"
        )
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"✅ Exported {len(achievements)} achievements to: {export_path}")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Local Achievement Storage")
    parser.add_argument("--list", action="store_true", help="List all achievements")
    parser.add_argument("--export", action="store_true", help="Export to JSON")

    args = parser.parse_args()

    if args.list:
        list_achievements()
    elif args.export:
        export_achievements()
    else:
        store_ci_achievement()
