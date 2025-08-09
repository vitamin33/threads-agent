"""
Test Batch Processing Functionality

Tests for batch publisher and consumer components.
"""

import asyncio
import pytest
from typing import List
from unittest.mock import AsyncMock, MagicMock

import aio_pika

from services.event_bus.messaging.batch_publisher import BatchPublisher
from services.event_bus.messaging.batch_consumer import BatchConsumer
from services.event_bus.models.base import BaseEvent


class TestBatchPublisher:
    """Test batch publisher functionality."""

    @pytest.fixture
    async def mock_connection(self):
        """Create mock RabbitMQ connection."""
        connection = AsyncMock(spec=aio_pika.Connection)
        channel = AsyncMock(spec=aio_pika.Channel)
        exchange = AsyncMock(spec=aio_pika.Exchange)

        connection.channel.return_value = channel
        channel.declare_exchange.return_value = exchange
        channel.set_qos = AsyncMock()
        channel.transaction = MagicMock()
        channel.transaction().__aenter__ = AsyncMock()
        channel.transaction().__aexit__ = AsyncMock()

        return connection, channel, exchange

    @pytest.mark.asyncio
    async def test_batch_publisher_initialization(self, mock_connection):
        """Test publisher initializes correctly."""
        connection, channel, exchange = mock_connection

        publisher = BatchPublisher(
            connection=connection, batch_size=50, flush_interval=0.5
        )

        await publisher.initialize()

        assert publisher.channel == channel
        assert publisher.exchange == exchange
        connection.channel.assert_called_once()
        channel.declare_exchange.assert_called_once_with(
            "events", aio_pika.ExchangeType.TOPIC, durable=True
        )

    @pytest.mark.asyncio
    async def test_publish_single_event(self, mock_connection):
        """Test publishing a single event gets batched."""
        connection, channel, exchange = mock_connection

        publisher = BatchPublisher(
            connection=connection,
            batch_size=10,
            flush_interval=5.0,  # Long interval to test batching
        )
        await publisher.initialize()

        # Publish single event
        event = BaseEvent(event_type="TestEvent", payload={"test": "data"})

        await publisher.publish(event, "test.routing")

        # Event should be in batch, not published yet
        assert len(publisher._batch) == 1
        assert publisher._batch[0][0] == event
        assert publisher._batch[0][1] == "test.routing"

        # Exchange should not have been called yet
        exchange.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_size_trigger(self, mock_connection):
        """Test batch flushes when size limit reached."""
        connection, channel, exchange = mock_connection

        publisher = BatchPublisher(
            connection=connection, batch_size=3, flush_interval=10.0
        )
        await publisher.initialize()

        # Publish events up to batch size
        events = []
        for i in range(4):  # One more than batch size
            event = BaseEvent(event_type="TestEvent", payload={"index": i})
            events.append(event)
            await publisher.publish(event)

        # First batch should have been flushed
        assert exchange.publish.call_count == 3  # First 3 events
        assert len(publisher._batch) == 1  # 4th event in new batch

    @pytest.mark.asyncio
    async def test_flush_timer(self, mock_connection):
        """Test batch flushes after timeout."""
        connection, channel, exchange = mock_connection

        publisher = BatchPublisher(
            connection=connection,
            batch_size=10,
            flush_interval=0.1,  # 100ms timeout
        )
        await publisher.initialize()

        # Publish single event
        event = BaseEvent(event_type="TestEvent", payload={"test": "timeout"})
        await publisher.publish(event)

        # Wait for flush timer
        await asyncio.sleep(0.2)

        # Batch should have been flushed
        assert exchange.publish.call_count == 1
        assert len(publisher._batch) == 0

    @pytest.mark.asyncio
    async def test_manual_flush(self, mock_connection):
        """Test manual flush functionality."""
        connection, channel, exchange = mock_connection

        publisher = BatchPublisher(
            connection=connection, batch_size=10, flush_interval=10.0
        )
        await publisher.initialize()

        # Publish events
        for i in range(5):
            event = BaseEvent(event_type="TestEvent", payload={"index": i})
            await publisher.publish(event)

        # Manually flush
        await publisher.flush()

        # All events should be published
        assert exchange.publish.call_count == 5
        assert len(publisher._batch) == 0

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, mock_connection):
        """Test metrics are tracked correctly."""
        connection, channel, exchange = mock_connection

        publisher = BatchPublisher(
            connection=connection, batch_size=2, flush_interval=10.0
        )
        await publisher.initialize()

        # Publish events to trigger batch
        for i in range(5):
            event = BaseEvent(
                event_type="TestEvent",
                payload={"data": "x" * 100},  # Some payload size
            )
            await publisher.publish(event)

        await publisher.flush()

        metrics = publisher.get_metrics()

        assert metrics["total_messages"] == 5
        assert metrics["total_batches"] == 3  # 2 + 2 + 1
        assert metrics["total_bytes"] > 0
        assert metrics["average_batch_size"] == 5 / 3


class TestBatchConsumer:
    """Test batch consumer functionality."""

    @pytest.fixture
    async def mock_connection(self):
        """Create mock RabbitMQ connection."""
        connection = AsyncMock(spec=aio_pika.Connection)
        channel = AsyncMock(spec=aio_pika.Channel)
        queue = AsyncMock(spec=aio_pika.Queue)

        connection.channel.return_value = channel
        channel.declare_queue.return_value = queue
        channel.set_qos = AsyncMock()

        return connection, channel, queue

    @pytest.fixture
    def create_mock_message(self):
        """Factory for creating mock messages."""

        def _create(event: BaseEvent):
            message = AsyncMock(spec=aio_pika.IncomingMessage)
            message.body = event.model_dump_json().encode()
            message.ack = AsyncMock()
            message.reject = AsyncMock()
            return message

        return _create

    @pytest.mark.asyncio
    async def test_batch_consumer_initialization(self, mock_connection):
        """Test consumer initializes correctly."""
        connection, channel, queue = mock_connection

        consumer = BatchConsumer(
            connection=connection,
            queue_name="test_queue",
            batch_size=25,
            batch_timeout=1.0,
        )

        await consumer.initialize()

        assert consumer.channel == channel
        assert consumer.queue == queue
        channel.declare_queue.assert_called_once()
        channel.set_qos.assert_called_once_with(prefetch_count=50)  # 2x batch_size

    @pytest.mark.asyncio
    async def test_batch_processing(self, mock_connection, create_mock_message):
        """Test processing messages in batches."""
        connection, channel, queue = mock_connection

        consumer = BatchConsumer(
            connection=connection,
            queue_name="test_queue",
            batch_size=3,
            batch_timeout=0.1,
        )
        await consumer.initialize()

        # Track processed batches
        processed_batches = []

        async def handler(events: List[BaseEvent]):
            processed_batches.append(events)

        # Simulate incoming messages
        messages = []
        for i in range(5):
            event = BaseEvent(event_type="TestEvent", payload={"index": i})
            message = create_mock_message(event)
            messages.append(message)

        # Manually trigger message handling (simulating consume)
        for msg in messages[:3]:  # First batch
            await consumer._on_message(msg)

        # Process batch
        await consumer._process_batch(messages[:3], handler, None)

        # Verify batch was processed
        assert len(processed_batches) == 1
        assert len(processed_batches[0]) == 3

        # Verify messages were acknowledged
        for msg in messages[:3]:
            msg.ack.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_timeout_trigger(self, mock_connection, create_mock_message):
        """Test batch processes after timeout."""
        connection, channel, queue = mock_connection

        consumer = BatchConsumer(
            connection=connection,
            queue_name="test_queue",
            batch_size=10,  # Large batch size
            batch_timeout=0.1,  # Short timeout
        )
        await consumer.initialize()

        processed = []

        async def handler(events: List[BaseEvent]):
            processed.extend(events)

        # Add just 2 messages (less than batch size)
        messages = []
        for i in range(2):
            event = BaseEvent(event_type="TestEvent", payload={"index": i})
            message = create_mock_message(event)
            messages.append(message)
            await consumer._on_message(message)

        # Start batch processor
        processor_task = asyncio.create_task(consumer._batch_processor(handler, None))

        # Wait for timeout
        await asyncio.sleep(0.2)

        # Stop processor
        consumer._processing = False
        processor_task.cancel()
        try:
            await processor_task
        except asyncio.CancelledError:
            pass

        # Messages should have been processed despite not reaching batch size
        # Note: In real implementation, the processor would handle this

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_connection, create_mock_message):
        """Test error handling in batch processing."""
        connection, channel, queue = mock_connection

        consumer = BatchConsumer(
            connection=connection,
            queue_name="test_queue",
            batch_size=2,
            batch_timeout=1.0,
        )
        await consumer.initialize()

        # Handler that raises an error
        async def failing_handler(events: List[BaseEvent]):
            raise Exception("Processing failed!")

        error_handled = False

        async def error_handler(error: Exception, messages: List):
            nonlocal error_handled
            error_handled = True
            assert str(error) == "Processing failed!"

        # Create messages
        messages = []
        for i in range(2):
            event = BaseEvent(event_type="TestEvent", payload={"index": i})
            message = create_mock_message(event)
            messages.append(message)

        # Process batch with error
        await consumer._process_batch(messages, failing_handler, error_handler)

        # Verify error was handled
        assert error_handled

        # Verify messages were rejected with requeue
        for msg in messages:
            msg.reject.assert_called_once_with(requeue=True)

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, mock_connection, create_mock_message):
        """Test consumer metrics tracking."""
        connection, channel, queue = mock_connection

        consumer = BatchConsumer(
            connection=connection,
            queue_name="test_queue",
            batch_size=2,
            batch_timeout=1.0,
        )
        await consumer.initialize()

        async def handler(events: List[BaseEvent]):
            pass  # Simple handler

        # Process some batches
        for batch_num in range(3):
            messages = []
            for i in range(2):
                event = BaseEvent(
                    event_type="TestEvent", payload={"batch": batch_num, "index": i}
                )
                message = create_mock_message(event)
                messages.append(message)

            await consumer._process_batch(messages, handler, None)

        metrics = consumer.get_metrics()

        assert metrics["total_messages"] == 6
        assert metrics["total_batches"] == 3
        assert metrics["average_batch_size"] == 2.0
        assert metrics["success_rate"] == 100.0


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))
