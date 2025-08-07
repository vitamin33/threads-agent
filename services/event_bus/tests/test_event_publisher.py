"""
Test for Event Publisher

Tests the async event publishing functionality with retry logic.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from services.event_bus.models.base import BaseEvent
from services.event_bus.publishers.publisher import EventPublisher


class TestEventPublisher:
    """Test Event Publisher functionality."""

    def test_event_publisher_initialization(self):
        """Test that EventPublisher can be initialized."""
        # This should fail initially - EventPublisher doesn't exist yet
        mock_connection_manager = Mock()
        publisher = EventPublisher(connection_manager=mock_connection_manager)
        
        assert publisher.connection_manager == mock_connection_manager
        assert publisher.max_retries == 3  # Default value
        assert publisher.retry_delay == 1.0  # Default value

    def test_event_publisher_custom_retry_settings(self):
        """Test publisher with custom retry settings."""
        mock_connection_manager = Mock()
        publisher = EventPublisher(
            connection_manager=mock_connection_manager,
            max_retries=5,
            retry_delay=2.0
        )
        
        assert publisher.max_retries == 5
        assert publisher.retry_delay == 2.0

    @pytest.mark.asyncio
    async def test_publish_event_success(self):
        """Test successful event publishing."""
        mock_connection_manager = Mock()
        mock_channel = Mock()
        mock_connection_manager.get_channel = AsyncMock(return_value=mock_channel)
        
        publisher = EventPublisher(connection_manager=mock_connection_manager)
        
        event = BaseEvent(
            event_type="test_event",
            payload={"key": "value"}
        )
        
        result = await publisher.publish(
            event=event,
            exchange="test_exchange",
            routing_key="test.routing.key"
        )
        
        assert result is True
        mock_connection_manager.get_channel.assert_called_once()
        mock_channel.basic_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_event_with_retry_on_failure(self):
        """Test event publishing retry logic on failure."""
        mock_connection_manager = Mock()
        mock_channel = Mock()
        mock_connection_manager.get_channel = AsyncMock(return_value=mock_channel)
        
        # First call fails, second succeeds
        mock_channel.basic_publish.side_effect = [
            Exception("Publish failed"),
            None  # Success
        ]
        
        publisher = EventPublisher(
            connection_manager=mock_connection_manager,
            max_retries=2
        )
        
        event = BaseEvent(event_type="test_event", payload={"key": "value"})
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await publisher.publish(
                event=event,
                exchange="test_exchange",
                routing_key="test.key"
            )
        
        assert result is True
        assert mock_channel.basic_publish.call_count == 2

    @pytest.mark.asyncio
    async def test_publish_event_fails_after_max_retries(self):
        """Test publishing fails after exceeding max retries."""
        mock_connection_manager = Mock()
        mock_channel = Mock()
        mock_connection_manager.get_channel = AsyncMock(return_value=mock_channel)
        mock_channel.basic_publish.side_effect = Exception("Publish failed")
        
        publisher = EventPublisher(
            connection_manager=mock_connection_manager,
            max_retries=2
        )
        
        event = BaseEvent(event_type="test_event", payload={"key": "value"})
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await publisher.publish(
                event=event,
                exchange="test_exchange", 
                routing_key="test.key"
            )
        
        assert result is False
        assert mock_channel.basic_publish.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_publish_event_serialization(self):
        """Test that events are properly serialized for publishing."""
        mock_connection_manager = Mock()
        mock_channel = Mock()
        mock_connection_manager.get_channel = AsyncMock(return_value=mock_channel)
        
        publisher = EventPublisher(connection_manager=mock_connection_manager)
        
        event = BaseEvent(
            event_type="user_created",
            payload={"user_id": "123", "email": "test@example.com"}
        )
        
        await publisher.publish(
            event=event,
            exchange="user_events",
            routing_key="user.created"
        )
        
        # Verify that basic_publish was called with proper arguments
        mock_channel.basic_publish.assert_called_once()
        call_args = mock_channel.basic_publish.call_args
        
        assert call_args[1]['exchange'] == "user_events"
        assert call_args[1]['routing_key'] == "user.created"
        # Body should be JSON-serialized event
        assert 'body' in call_args[1]
        body = call_args[1]['body']
        assert '"event_type":"user_created"' in body
        assert '"user_id":"123"' in body

    @pytest.mark.asyncio
    async def test_publish_event_with_properties(self):
        """Test publishing with custom properties."""
        mock_connection_manager = Mock()
        mock_channel = Mock()
        mock_connection_manager.get_channel = AsyncMock(return_value=mock_channel)
        
        publisher = EventPublisher(connection_manager=mock_connection_manager)
        
        event = BaseEvent(event_type="test_event", payload={"key": "value"})
        
        await publisher.publish(
            event=event,
            exchange="test_exchange",
            routing_key="test.key",
            persistent=True
        )
        
        # Verify properties are set
        call_args = mock_channel.basic_publish.call_args
        properties = call_args[1]['properties']
        assert properties.delivery_mode == 2  # Persistent message

    @pytest.mark.asyncio
    async def test_publish_connection_manager_not_connected_raises_exception(self):
        """Test that publishing when connection manager is not connected raises exception."""
        mock_connection_manager = Mock()
        mock_connection_manager.get_channel = AsyncMock(
            side_effect=RuntimeError("Not connected to RabbitMQ")
        )
        
        publisher = EventPublisher(connection_manager=mock_connection_manager)
        event = BaseEvent(event_type="test_event", payload={"key": "value"})
        
        result = await publisher.publish(
            event=event,
            exchange="test_exchange",
            routing_key="test.key"
        )
        
        # Should return False when unable to get channel
        assert result is False