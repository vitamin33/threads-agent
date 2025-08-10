"""
Viral Engine Event Models

Event contracts for Content Scheduler <-> Viral Engine integration.
These events enable async communication through the Event Bus.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base event model - minimal implementation"""

    event_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique event identifier"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event creation timestamp",
    )
    event_type: str = Field(..., description="Type of event")
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Event data payload"
    )


class ContentQualityCheckRequestedPayload(BaseModel):
    """Payload for content quality check request event"""

    content_id: int
    content: str
    title: str
    author_id: str
    content_type: str
    metadata: Optional[Dict[str, Any]] = None


class ContentQualityCheckRequested(BaseEvent):
    """Event triggered when content needs quality check"""

    event_type: str = Field(
        default="ContentQualityCheckRequested", description="Event type"
    )
    payload: ContentQualityCheckRequestedPayload


class ContentQualityScoredPayload(BaseModel):
    """Payload for content quality score result event"""

    content_id: int
    quality_score: float
    predicted_engagement_rate: float
    passes_quality_gate: bool
    feature_scores: Dict[str, float]
    improvement_suggestions: list[str]
    processing_time_ms: float


class ContentQualityScored(BaseEvent):
    """Event triggered when content quality scoring is complete"""

    event_type: str = Field(default="ContentQualityScored", description="Event type")
    payload: ContentQualityScoredPayload
