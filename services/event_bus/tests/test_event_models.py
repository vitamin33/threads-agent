"""
Test for Event Models

Tests the base event model and event schema validation.
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID
from pydantic import ValidationError

from services.event_bus.models.base import BaseEvent


class TestBaseEvent:
    """Test BaseEvent model functionality."""

    def test_base_event_creation_with_required_fields(self):
        """Test that BaseEvent can be created with required fields."""
        # This should fail initially - BaseEvent doesn't exist yet
        event = BaseEvent(
            event_type="test_event",
            payload={"key": "value"}
        )
        
        # Should have auto-generated UUID
        assert event.event_id is not None
        assert isinstance(event.event_id, str)
        assert len(event.event_id) == 36  # UUID format
        
        # Should have current timestamp
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
        assert event.timestamp <= datetime.now(timezone.utc)
        
        # Should have provided event_type
        assert event.event_type == "test_event"
        
        # Should have payload
        assert event.payload == {"key": "value"}

    def test_base_event_missing_event_type_raises_validation_error(self):
        """Test that missing event_type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            BaseEvent(payload={"key": "value"})
        
        assert "event_type" in str(exc_info.value)

    def test_base_event_json_serializable(self):
        """Test that BaseEvent can be serialized to JSON."""
        event = BaseEvent(
            event_type="test_event",
            payload={"key": "value"}
        )
        
        json_data = event.model_dump()
        assert "event_id" in json_data
        assert "timestamp" in json_data
        assert "event_type" in json_data
        assert "payload" in json_data
        
        # Should be able to recreate from JSON
        recreated_event = BaseEvent(**json_data)
        assert recreated_event.event_id == event.event_id
        assert recreated_event.event_type == event.event_type
        assert recreated_event.payload == event.payload

    def test_base_event_custom_event_id_and_timestamp(self):
        """Test that custom event_id and timestamp can be provided."""
        custom_id = "custom-event-id-123"
        custom_timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        event = BaseEvent(
            event_id=custom_id,
            timestamp=custom_timestamp,
            event_type="custom_event",
            payload={"custom": "data"}
        )
        
        assert event.event_id == custom_id
        assert event.timestamp == custom_timestamp
        assert event.event_type == "custom_event"
        assert event.payload == {"custom": "data"}