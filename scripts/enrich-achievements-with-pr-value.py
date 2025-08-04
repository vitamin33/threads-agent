#!/usr/bin/env python3
"""
Enrich existing achievements with PR value analysis.

This script finds all GitHub PR achievements and enriches them with
business value metrics using the PR value analyzer.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Achievement
from services.achievement_collector.services.pr_value_analyzer_integration import (
    pr_value_integration,
)
from services.achievement_collector.core.logging import setup_logging

logger = setup_logging(__name__)


async def enrich_pr_achievements(limit: int = None, force_update: bool = False):
    """Enrich PR achievements with value analysis."""
    db = next(get_db())
    enriched_count = 0
    skipped_count = 0
    failed_count = 0

    try:
        # Query all GitHub PR achievements
        query = db.query(Achievement).filter_by(source_type="github_pr")

        if limit:
            query = query.limit(limit)

        achievements = query.all()
        total = len(achievements)

        print(f"🔍 Found {total} GitHub PR achievements to process")

        for i, achievement in enumerate(achievements, 1):
            # Extract PR number from source_id (format: "PR-123")
            if not achievement.source_id or not achievement.source_id.startswith("PR-"):
                print(
                    f"⚠️  Skipping achievement {achievement.id}: Invalid source_id format"
                )
                skipped_count += 1
                continue

            pr_number = achievement.source_id.replace("PR-", "")

            # Check if already has value analysis (unless force update)
            if not force_update:
                metadata = achievement.metadata or {}
                if metadata.get("value_analysis"):
                    print(f"⏭️  Skipping PR #{pr_number}: Already has value analysis")
                    skipped_count += 1
                    continue

            print(f"[{i}/{total}] 🔄 Analyzing PR #{pr_number}...")

            try:
                # Run value analysis
                enriched = await pr_value_integration.analyze_and_create_achievement(
                    pr_number
                )

                if enriched:
                    print(
                        f"✅ Enriched achievement {achievement.id} for PR #{pr_number}"
                    )
                    enriched_count += 1

                    # Display key metrics
                    metrics = enriched.metrics_after or {}
                    if metrics.get("overall_score"):
                        print(f"   📊 Overall Score: {metrics['overall_score']}/10")
                    if metrics.get("roi_year_one_percent"):
                        print(f"   💰 ROI: {metrics['roi_year_one_percent']:.0f}%")
                    if metrics.get("infrastructure_savings_estimate"):
                        print(
                            f"   💵 Savings: ${metrics['infrastructure_savings_estimate']:,.0f}"
                        )
                else:
                    print(f"⚠️  PR #{pr_number} analysis returned no results")
                    skipped_count += 1

            except Exception as e:
                print(f"❌ Failed to analyze PR #{pr_number}: {e}")
                failed_count += 1

            # Add small delay to avoid overwhelming GitHub API
            await asyncio.sleep(1)

        print("\n📊 Summary:")
        print(f"   Total processed: {total}")
        print(f"   ✅ Enriched: {enriched_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        print(f"   ❌ Failed: {failed_count}")

    finally:
        db.close()


async def show_enrichment_stats():
    """Show statistics about enriched achievements."""
    db = next(get_db())

    try:
        # Get all PR achievements
        all_pr_achievements = (
            db.query(Achievement).filter_by(source_type="github_pr").count()
        )

        # Get enriched achievements (those with value_analysis in metadata)
        enriched_achievements = 0
        high_value_achievements = 0
        total_roi = 0
        total_savings = 0

        achievements = db.query(Achievement).filter_by(source_type="github_pr").all()

        for achievement in achievements:
            metadata = achievement.metadata or {}
            if metadata.get("value_analysis"):
                enriched_achievements += 1

                # Extract metrics
                metrics = achievement.metrics_after or {}
                score = metrics.get("overall_score", 0)
                roi = metrics.get("roi_year_one_percent", 0)
                savings = metrics.get("infrastructure_savings_estimate", 0)

                if score >= 7:
                    high_value_achievements += 1

                total_roi += roi
                total_savings += savings

        print("📊 Enrichment Statistics:")
        print(f"   Total PR Achievements: {all_pr_achievements}")
        print(
            f"   Enriched Achievements: {enriched_achievements} ({enriched_achievements / all_pr_achievements * 100:.1f}%)"
        )
        print(f"   High-Value Achievements (score >= 7): {high_value_achievements}")

        if enriched_achievements > 0:
            print("\n💰 Business Value Metrics:")
            print(f"   Average ROI: {total_roi / enriched_achievements:.0f}%")
            print(f"   Total Estimated Savings: ${total_savings:,.0f}")
            print(
                f"   Average Savings per PR: ${total_savings / enriched_achievements:,.0f}"
            )

    finally:
        db.close()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enrich PR achievements with value analysis"
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of achievements to process"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-analysis of already enriched achievements",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show enrichment statistics only"
    )

    args = parser.parse_args()

    if args.stats:
        asyncio.run(show_enrichment_stats())
    else:
        asyncio.run(enrich_pr_achievements(limit=args.limit, force_update=args.force))


if __name__ == "__main__":
    main()
