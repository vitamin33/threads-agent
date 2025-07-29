"""
Celery tasks for business value extraction.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task
from celery.utils.log import get_task_logger

from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Achievement
from services.achievement_collector.services.ai_analyzer import AIAnalyzer

logger = get_task_logger(__name__)


@shared_task(
    name="extract_business_values",
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def extract_business_values_task(
    limit: int = 20,
    days_back: int = 7
) -> dict:
    """
    Celery task to extract business values from recent achievements.
    
    This task is designed to run periodically (e.g., daily) to process
    achievements that don't have business values yet.
    
    Args:
        limit: Maximum number of achievements to process
        days_back: Process achievements from the last N days
        
    Returns:
        dict: Summary of processing results
    """
    try:
        # Run the async processing
        result = asyncio.run(
            _process_achievements_async(limit, days_back)
        )
        return result
    except Exception as e:
        logger.error(f"Error in business value extraction task: {e}")
        raise extract_business_values_task.retry(exc=e)


async def _process_achievements_async(
    limit: int,
    days_back: int
) -> dict:
    """Async helper for achievement processing."""
    db = next(get_db())
    analyzer = AIAnalyzer()
    
    try:
        # Find achievements needing processing
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        achievements = db.query(Achievement).filter(
            Achievement.source_type.in_(["github_pr", "git"]),
            Achievement.created_at >= cutoff_date,
            (Achievement.business_value == None) | (Achievement.business_value == "")
        ).order_by(
            Achievement.impact_score.desc()
        ).limit(limit).all()
        
        logger.info(f"Processing {len(achievements)} achievements")
        
        # Track results
        results = {
            "processed": 0,
            "success": 0,
            "errors": 0,
            "no_value_found": 0,
            "achievements": []
        }
        
        # Process each achievement
        for achievement in achievements:
            try:
                logger.info(f"Processing achievement {achievement.id}")
                
                # Update with AI-extracted value
                updated = await analyzer.update_achievement_business_value(
                    db, achievement
                )
                
                if updated:
                    results["success"] += 1
                    results["achievements"].append({
                        "id": achievement.id,
                        "title": achievement.title,
                        "business_value": achievement.business_value
                    })
                else:
                    results["no_value_found"] += 1
                    
                results["processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing achievement {achievement.id}: {e}")
                results["errors"] += 1
        
        logger.info(
            f"Processing complete: {results['success']} success, "
            f"{results['errors']} errors, {results['no_value_found']} no value"
        )
        
        return results
        
    finally:
        db.close()


@shared_task(
    name="process_single_achievement",
    max_retries=2,
    default_retry_delay=60
)
def process_single_achievement_task(achievement_id: int) -> Optional[str]:
    """
    Process a single achievement to extract business value.
    
    Args:
        achievement_id: ID of the achievement to process
        
    Returns:
        str: Extracted business value or None
    """
    try:
        return asyncio.run(
            _process_single_achievement_async(achievement_id)
        )
    except Exception as e:
        logger.error(f"Error processing achievement {achievement_id}: {e}")
        raise process_single_achievement_task.retry(exc=e)


async def _process_single_achievement_async(
    achievement_id: int
) -> Optional[str]:
    """Async helper for single achievement processing."""
    db = next(get_db())
    analyzer = AIAnalyzer()
    
    try:
        achievement = db.query(Achievement).filter(
            Achievement.id == achievement_id
        ).first()
        
        if not achievement:
            logger.error(f"Achievement {achievement_id} not found")
            return None
        
        # Update with AI-extracted value
        updated = await analyzer.update_achievement_business_value(
            db, achievement
        )
        
        if updated:
            logger.info(
                f"✅ Updated achievement {achievement_id} with "
                f"business value: {achievement.business_value}"
            )
            return achievement.business_value
        else:
            logger.warning(f"No business value found for achievement {achievement_id}")
            return None
            
    finally:
        db.close()


# Celery beat schedule configuration
# Add this to your celerybeat_schedule in celery config:
"""
'extract-business-values': {
    'task': 'extract_business_values',
    'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    'options': {
        'queue': 'achievement_processing'
    },
    'kwargs': {
        'limit': 50,
        'days_back': 7
    }
},
"""