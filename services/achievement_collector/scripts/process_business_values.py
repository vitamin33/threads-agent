#!/usr/bin/env python3
"""
Batch process achievements to extract business values using AI.

This script processes achievements that don't have business values extracted yet.
It can be run manually or scheduled via cron/celery.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Achievement
from services.achievement_collector.services.ai_analyzer import AIAnalyzer
from services.achievement_collector.core.logging import setup_logging

logger = setup_logging(__name__)


async def process_achievements(
    limit: int = 50,
    days_back: int = 30,
    dry_run: bool = False,
    force_all: bool = False
):
    """
    Process achievements to extract business values.
    
    Args:
        limit: Maximum number of achievements to process
        days_back: Process achievements from the last N days
        dry_run: If True, don't save changes to database
        force_all: If True, reprocess even achievements with existing business values
    """
    db = next(get_db())
    analyzer = AIAnalyzer()
    
    try:
        # Build query
        query = db.query(Achievement)
        
        # Filter by source type (focus on PRs)
        query = query.filter(Achievement.source_type.in_(["github_pr", "git"]))
        
        # Filter by date if not forcing all
        if not force_all:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query = query.filter(Achievement.created_at >= cutoff_date)
            
            # Only process achievements without business value
            query = query.filter(
                (Achievement.business_value == None) | 
                (Achievement.business_value == "")
            )
        
        # Order by impact score (process high-impact first)
        query = query.order_by(Achievement.impact_score.desc())
        
        # Apply limit
        achievements = query.limit(limit).all()
        
        logger.info(f"Found {len(achievements)} achievements to process")
        
        # Process each achievement
        success_count = 0
        error_count = 0
        
        for achievement in achievements:
            try:
                logger.info(f"Processing achievement {achievement.id}: {achievement.title}")
                
                # Extract business value
                if dry_run:
                    # Just extract and log, don't save
                    business_value = await analyzer.extract_business_value(
                        achievement.description
                    )
                    logger.info(f"Would extract: {business_value}")
                else:
                    # Update achievement with extracted value
                    updated = await analyzer.update_achievement_business_value(
                        db, achievement
                    )
                    if updated:
                        logger.info(
                            f"✅ Updated achievement {achievement.id} with "
                            f"business value: {achievement.business_value}"
                        )
                        success_count += 1
                    else:
                        logger.warning(f"No business value found for {achievement.id}")
                        
            except Exception as e:
                logger.error(f"❌ Error processing achievement {achievement.id}: {e}")
                error_count += 1
                continue
        
        # Summary
        logger.info(
            f"\n📊 Processing complete:\n"
            f"   ✅ Success: {success_count}\n"
            f"   ❌ Errors: {error_count}\n"
            f"   ⏭️  Skipped: {len(achievements) - success_count - error_count}"
        )
        
    finally:
        db.close()


def main():
    """Main entry point with CLI arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process achievements to extract business values"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=50,
        help="Maximum number of achievements to process (default: 50)"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=30,
        help="Process achievements from the last N days (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract values but don't save to database"
    )
    parser.add_argument(
        "--force-all",
        action="store_true",
        help="Reprocess all achievements, even those with existing values"
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (or set OPENAI_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    # Set API key if provided
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "test":
        logger.warning(
            "⚠️  No OpenAI API key found. Will use offline pattern matching only.\n"
            "   Set OPENAI_API_KEY environment variable for AI-powered extraction."
        )
    
    # Run the async function
    asyncio.run(
        process_achievements(
            limit=args.limit,
            days_back=args.days_back,
            dry_run=args.dry_run,
            force_all=args.force_all
        )
    )


if __name__ == "__main__":
    main()