"""
Base Event Model

Core event model that all events inherit from.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """
    Base event model with required fields.
    
    All events in the system inherit from this base model.
    """
    
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Event creation timestamp")
    event_type: str = Field(..., description="Type of event")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event data payload")