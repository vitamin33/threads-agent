"""Celery tasks for async content publishing.

This module provides the async task infrastructure for publishing content
across multiple platforms with retry logic, error handling, and status tracking.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from contextlib import contextmanager

from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import and_

from services.orchestrator.db.models import ContentSchedule
from services.orchestrator.publishing.engine import PublishingEngine


@contextmanager
def get_db_session():
    """Get database session for tasks."""
    # Import here to avoid circular imports
    from services.orchestrator.db import get_session
    
    SessionLocal = get_session()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@shared_task(name="orchestrator.publish_content")
def publish_content_task(schedule_id: int) -> Dict[str, Any]:
    """Publish content for a specific schedule."""
    with get_db_session() as db:
        # Get the schedule
        schedule = db.query(ContentSchedule).filter(
            ContentSchedule.id == schedule_id
        ).first()
        
        if not schedule:
            return {
                "success": False,
                "error": f"Schedule {schedule_id} not found"
            }
        
        # Check if already published
        if schedule.status == "published":
            return {
                "success": True,
                "message": "Already published",
                "platform": schedule.platform
            }
        
        # Initialize publishing engine
        engine = PublishingEngine()
        
        try:
            # Publish content
            result = asyncio.run(engine.publish_to_platform(
                content_item=schedule.content_item,
                platform=schedule.platform,
                platform_config=schedule.platform_config or {}
            ))
            
            if result.success:
                # Update schedule with success
                schedule.status = "published"
                schedule.published_at = datetime.now(timezone.utc)
                schedule.error_message = None
                
                db.commit()
                
                return {
                    "success": True,
                    "platform": result.platform,
                    "external_id": result.external_id,
                    "url": result.url,
                    "schedule_id": schedule_id
                }
            else:
                # Handle failure with retry logic
                return _handle_publishing_failure(db, schedule, result.error_message)
                
        except Exception as e:
            return _handle_publishing_failure(db, schedule, str(e))


@shared_task(name="orchestrator.publish_scheduled_content")
def publish_scheduled_content_task() -> Dict[str, Any]:
    """Find and publish all due scheduled content."""
    with get_db_session() as db:
        # Find schedules that are due for publishing
        now = datetime.now(timezone.utc)
        
        due_schedules = db.query(ContentSchedule).filter(
            and_(
                ContentSchedule.scheduled_time <= now,
                ContentSchedule.status == "scheduled"
            )
        ).all()
        
        scheduled_count = 0
        for schedule in due_schedules:
            # Schedule individual publishing task
            publish_content_task.delay(schedule_id=schedule.id)
            scheduled_count += 1
        
        return {
            "processed_count": len(due_schedules),
            "scheduled_count": scheduled_count,
            "timestamp": now.isoformat()
        }


@shared_task(name="orchestrator.retry_failed_publication")
def retry_failed_publication_task(schedule_id: int) -> Dict[str, Any]:
    """Retry a failed publication."""
    with get_db_session() as db:
        # Get the schedule
        schedule = db.query(ContentSchedule).filter(
            ContentSchedule.id == schedule_id
        ).first()
        
        if not schedule:
            return {
                "success": False,
                "error": f"Schedule {schedule_id} not found"
            }
        
        # Check if retry is due
        now = datetime.now(timezone.utc)
        if schedule.next_retry_time and schedule.next_retry_time > now:
            return {
                "success": False,
                "error": "Retry not due yet",
                "next_retry_time": schedule.next_retry_time.isoformat()
            }
        
        # Increment retry count
        schedule.retry_count += 1
        
        # Check if max retries exceeded
        if schedule.retry_count > schedule.max_retries:
            schedule.status = "failed"
            schedule.error_message = f"Max retries ({schedule.max_retries}) exceeded"
            db.commit()
            
            return {
                "success": False,
                "error": "Max retries exceeded",
                "retry_attempt": schedule.retry_count
            }
        
        # Initialize publishing engine
        engine = PublishingEngine()
        
        try:
            # Attempt retry
            result = asyncio.run(engine.publish_to_platform(
                content_item=schedule.content_item,
                platform=schedule.platform,
                platform_config=schedule.platform_config or {}
            ))
            
            if result.success:
                # Update schedule with success
                schedule.status = "published"
                schedule.published_at = datetime.now(timezone.utc)
                schedule.error_message = None
                schedule.next_retry_time = None
                
                db.commit()
                
                return {
                    "success": True,
                    "platform": result.platform,
                    "external_id": result.external_id,
                    "url": result.url,
                    "retry_attempt": schedule.retry_count
                }
            else:
                # Schedule another retry if within limits
                return _handle_publishing_failure(db, schedule, result.error_message)
                
        except Exception as e:
            return _handle_publishing_failure(db, schedule, str(e))


def _handle_publishing_failure(
    db: Session, 
    schedule: ContentSchedule, 
    error_message: str
) -> Dict[str, Any]:
    """Handle publishing failure with retry logic."""
    schedule.error_message = error_message
    
    # Check if we can retry
    if schedule.retry_count < schedule.max_retries:
        # Schedule retry with exponential backoff
        schedule.retry_count += 1
        schedule.status = "retry_scheduled"
        
        retry_delay_seconds = calculate_retry_delay(schedule.retry_count - 1)
        schedule.next_retry_time = datetime.now(timezone.utc) + timedelta(seconds=retry_delay_seconds)
        
        db.commit()
        
        # Schedule the retry task
        retry_failed_publication_task.apply_async(
            args=[schedule.id],
            countdown=retry_delay_seconds
        )
        
        return {
            "success": False,
            "error": error_message,
            "retry_scheduled": True,
            "retry_attempt": schedule.retry_count,
            "next_retry_time": schedule.next_retry_time.isoformat()
        }
    else:
        # Max retries exceeded
        schedule.status = "failed"
        db.commit()
        
        return {
            "success": False,
            "error": error_message,
            "max_retries_exceeded": True,
            "retry_attempt": schedule.retry_count
        }


def calculate_retry_delay(retry_count: int) -> int:
    """Calculate retry delay using exponential backoff.
    
    Args:
        retry_count: Number of previous retry attempts (0-based)
        
    Returns:
        Delay in seconds
    """
    base_delay = 60  # 1 minute base delay
    max_delay = 3600  # 1 hour maximum delay
    
    # Exponential backoff: 1m, 2m, 4m, 8m, 16m, etc.
    delay = base_delay * (2 ** retry_count)
    
    # Cap at maximum delay
    return min(delay, max_delay)