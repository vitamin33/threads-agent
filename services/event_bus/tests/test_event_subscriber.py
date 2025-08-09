"""
Test for Event Subscriber

Tests the async event subscription functionality with multiple handlers.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.event_bus.models.base import BaseEvent
from services.event_bus.subscribers.subscriber import EventSubscriber


class TestEventSubscriber:
    """Test Event Subscriber functionality."""

    def test_event_subscriber_initialization(self):
        """Test that EventSubscriber can be initialized."""
        # This should fail initially - EventSubscriber doesn't exist yet
        mock_connection_manager = Mock()
        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        assert subscriber.connection_manager == mock_connection_manager
        assert isinstance(subscriber._handlers, dict)
        assert len(subscriber._handlers) == 0

    def test_event_subscriber_register_handler(self):
        """Test registering event handlers."""
        mock_connection_manager = Mock()
        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        async def test_handler(event: BaseEvent):
            pass

        subscriber.register_handler("test_event", test_handler)

        assert "test_event" in subscriber._handlers
        assert test_handler in subscriber._handlers["test_event"]

    def test_event_subscriber_register_multiple_handlers_same_event(self):
        """Test registering multiple handlers for the same event type."""
        mock_connection_manager = Mock()
        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        async def handler1(event: BaseEvent):
            pass

        async def handler2(event: BaseEvent):
            pass

        subscriber.register_handler("test_event", handler1)
        subscriber.register_handler("test_event", handler2)

        assert "test_event" in subscriber._handlers
        assert handler1 in subscriber._handlers["test_event"]
        assert handler2 in subscriber._handlers["test_event"]
        assert len(subscriber._handlers["test_event"]) == 2

    @pytest.mark.asyncio
    async def test_process_message_with_registered_handler(self):
        """Test processing message with registered handler."""
        mock_connection_manager = Mock()
        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        # Mock handler
        handler_mock = AsyncMock()
        subscriber.register_handler("test_event", handler_mock)

        # Create test event JSON message body
        event = BaseEvent(event_type="test_event", payload={"key": "value"})
        message_body = event.model_dump_json()

        # Mock RabbitMQ method and properties
        mock_method = Mock()
        mock_method.routing_key = "test.routing.key"
        mock_properties = Mock()

        # Mock channel for ack
        mock_channel = Mock()

        result = await subscriber._process_message(
            channel=mock_channel,
            method=mock_method,
            properties=mock_properties,
            body=message_body,
        )

        assert result is True
        handler_mock.assert_called_once()
        # Verify the event passed to handler is correct
        call_args = handler_mock.call_args[0][0]
        assert call_args.event_type == "test_event"
        assert call_args.payload == {"key": "value"}

        # Verify message was acknowledged
        mock_channel.basic_ack.assert_called_once_with(
            delivery_tag=mock_method.delivery_tag
        )

    @pytest.mark.asyncio
    async def test_process_message_with_multiple_handlers(self):
        """Test processing message with multiple handlers."""
        mock_connection_manager = Mock()
        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        # Mock handlers
        handler1_mock = AsyncMock()
        handler2_mock = AsyncMock()
        subscriber.register_handler("test_event", handler1_mock)
        subscriber.register_handler("test_event", handler2_mock)

        # Create test event
        event = BaseEvent(event_type="test_event", payload={"key": "value"})
        message_body = event.model_dump_json()

        mock_method = Mock()
        mock_method.routing_key = "test.routing.key"
        mock_properties = Mock()
        mock_channel = Mock()

        result = await subscriber._process_message(
            channel=mock_channel,
            method=mock_method,
            properties=mock_properties,
            body=message_body,
        )

        assert result is True
        handler1_mock.assert_called_once()
        handler2_mock.assert_called_once()
        mock_channel.basic_ack.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_no_handler_for_event_type(self):
        """Test processing message with no registered handler."""
        mock_connection_manager = Mock()
        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        # Create event with unregistered event type
        event = BaseEvent(event_type="unknown_event", payload={"key": "value"})
        message_body = event.model_dump_json()

        mock_method = Mock()
        mock_method.routing_key = "test.routing.key"
        mock_properties = Mock()
        mock_channel = Mock()

        result = await subscriber._process_message(
            channel=mock_channel,
            method=mock_method,
            properties=mock_properties,
            body=message_body,
        )

        assert result is True  # Should still ack message
        mock_channel.basic_ack.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_handler_exception(self):
        """Test processing message when handler raises exception."""
        mock_connection_manager = Mock()
        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        # Handler that raises exception
        async def failing_handler(event: BaseEvent):
            raise ValueError("Handler failed")

        subscriber.register_handler("test_event", failing_handler)

        event = BaseEvent(event_type="test_event", payload={"key": "value"})
        message_body = event.model_dump_json()

        mock_method = Mock()
        mock_method.routing_key = "test.routing.key"
        mock_properties = Mock()
        mock_channel = Mock()

        result = await subscriber._process_message(
            channel=mock_channel,
            method=mock_method,
            properties=mock_properties,
            body=message_body,
        )

        assert result is False  # Should return False on handler failure
        # Should NOT ack message when handler fails
        mock_channel.basic_ack.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_message_invalid_json(self):
        """Test processing message with invalid JSON."""
        mock_connection_manager = Mock()
        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        mock_method = Mock()
        mock_method.routing_key = "test.routing.key"
        mock_properties = Mock()
        mock_channel = Mock()

        result = await subscriber._process_message(
            channel=mock_channel,
            method=mock_method,
            properties=mock_properties,
            body="invalid json",
        )

        assert result is False
        mock_channel.basic_ack.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_consuming(self):
        """Test starting message consumption."""
        mock_connection_manager = Mock()
        mock_channel = Mock()
        mock_connection_manager.get_channel = AsyncMock(return_value=mock_channel)

        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        with patch.object(subscriber, "_setup_consumer") as mock_setup:
            await subscriber.start_consuming(queue_name="test_queue")

            mock_connection_manager.get_channel.assert_called_once()
            mock_setup.assert_called_once_with(mock_channel, "test_queue")

    def test_setup_consumer(self):
        """Test setting up the consumer."""
        mock_connection_manager = Mock()
        subscriber = EventSubscriber(connection_manager=mock_connection_manager)

        mock_channel = Mock()

        subscriber._setup_consumer(mock_channel, "test_queue")

        # Verify consumer is set up
        mock_channel.basic_consume.assert_called_once_with(
            queue="test_queue", on_message_callback=subscriber._message_callback
        )
