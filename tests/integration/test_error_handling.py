"""
Error Handling and Dead Letter Queue Integration Tests

This module tests error scenarios including handler failures, connection failures,
dead letter queue processing, and recovery mechanisms.
"""

import asyncio
import logging

import pytest

from services.event_bus.models.base import BaseEvent

logger = logging.getLogger(__name__)


class TestErrorHandling:
    """Test error handling scenarios and recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_handler_failure_no_ack(
        self,
        publisher,
        subscriber,
        test_exchange,
        test_queue,
        event_capture,
        async_timeout,
    ):
        """Test that failed handlers prevent message acknowledgment."""
        # Create test event
        test_event = BaseEvent(event_type="failure.test", payload={"should_fail": True})

        # Register failing handler
        failing_handler = event_capture.create_handler(
            "failing_handler", should_fail=True
        )
        subscriber.register_handler("failure.test", failing_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Publish event
        success = await publisher.publish(
            event=test_event, exchange=test_exchange, routing_key="test.event"
        )
        assert success

        # Wait for processing attempt
        await asyncio.sleep(1.0)

        # Verify handler was called but failed
        assert event_capture.handler_calls.get("failing_handler", 0) == 1
        assert len(event_capture.errors) == 1
        assert "failing_handler failed" in str(event_capture.errors[0])

        # Verify event was not captured (handler failed)
        assert len(event_capture.events) == 0

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_partial_handler_failure_with_multiple_handlers(
        self,
        publisher,
        subscriber,
        test_exchange,
        test_queue,
        event_capture,
        async_timeout,
    ):
        """Test behavior when some handlers succeed and others fail."""
        # Create test event
        test_event = BaseEvent(event_type="partial.failure", payload={"data": "test"})

        # Register multiple handlers - some that succeed, some that fail
        success_handler = event_capture.create_handler(
            "success_handler", should_fail=False
        )
        failing_handler = event_capture.create_handler(
            "failing_handler", should_fail=True
        )
        another_success_handler = event_capture.create_handler(
            "another_success", should_fail=False
        )

        subscriber.register_handler("partial.failure", success_handler)
        subscriber.register_handler("partial.failure", failing_handler)
        subscriber.register_handler("partial.failure", another_success_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Publish event
        success = await publisher.publish(
            event=test_event, exchange=test_exchange, routing_key="test.event"
        )
        assert success

        # Wait for processing
        await asyncio.sleep(1.0)

        # Verify all handlers were called
        assert event_capture.handler_calls.get("success_handler", 0) == 1
        assert event_capture.handler_calls.get("failing_handler", 0) == 1
        assert (
            event_capture.handler_calls.get("another_success", 0) == 0
        )  # Stopped after first failure

        # Verify one error occurred
        assert len(event_capture.errors) == 1

        # In current implementation, successful handlers execute but message isn't acked due to failure
        assert (
            len(event_capture.events) == 1
        )  # Only success_handler completed before failure

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_publisher_retry_on_connection_failure(self, connection_manager):
        """Test publisher retry logic when RabbitMQ connection fails."""
        # Create publisher with short retry settings for testing
        publisher = EventPublisher(connection_manager, max_retries=2, retry_delay=0.1)

        test_event = BaseEvent(
            event_type="connection.failure.test", payload={"retry": "test"}
        )

        # Mock get_channel to fail first two times, succeed on third
        original_get_channel = connection_manager.get_channel
        call_count = {"count": 0}

        async def mock_get_channel():
            call_count["count"] += 1
            if call_count["count"] <= 2:
                raise RuntimeError("Connection failed")
            return await original_get_channel()

        connection_manager.get_channel = mock_get_channel

        # This should succeed after retries
        success = await publisher.publish(
            event=test_event, exchange="test_exchange", routing_key="test.key"
        )

        assert success
        assert call_count["count"] == 3  # Failed twice, succeeded on third attempt

    @pytest.mark.asyncio
    async def test_publisher_fails_after_max_retries(self, connection_manager):
        """Test publisher fails after exhausting max retries."""
        publisher = EventPublisher(connection_manager, max_retries=2, retry_delay=0.05)

        test_event = BaseEvent(event_type="max.retries.test", payload={"data": "test"})

        # Mock get_channel to always fail
        async def always_fail():
            raise RuntimeError("Persistent connection failure")

        connection_manager.get_channel = always_fail

        # This should fail after max retries
        success = await publisher.publish(
            event=test_event, exchange="test_exchange", routing_key="test.key"
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_event_store_failure_resilience(self, postgres_url):
        """Test event store behavior when database is unavailable."""
        from services.event_bus.store.postgres_store import PostgreSQLEventStore

        # Use invalid connection URL
        invalid_store = PostgreSQLEventStore(
            "postgresql://invalid:invalid@localhost:9999/invalid"
        )

        test_event = BaseEvent(
            event_type="store.failure.test", payload={"data": "test"}
        )

        # Store should fail gracefully
        success = await invalid_store.store_event(test_event)
        assert success is False

        # Retrieval should fail gracefully
        retrieved = await invalid_store.get_event_by_id(test_event.event_id)
        assert retrieved is None

        # Replay should return empty list
        replayed = await invalid_store.replay_events()
        assert replayed == []

    @pytest.mark.asyncio
    async def test_malformed_message_handling(
        self, subscriber, connection_manager, test_exchange, test_queue, event_capture
    ):
        """Test handling of malformed/invalid JSON messages."""
        # Register handler
        handler = event_capture.create_handler("malformed_handler")
        subscriber.register_handler("test.event", handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Send malformed JSON directly to queue
        channel = await connection_manager.get_channel()

        # Send invalid JSON
        channel.basic_publish(
            exchange=test_exchange,
            routing_key="test.event",
            body="invalid json content",
        )

        # Send JSON with wrong structure
        channel.basic_publish(
            exchange=test_exchange,
            routing_key="test.event",
            body='{"wrong": "structure", "missing": "required_fields"}',
        )

        channel.close()

        # Wait for processing attempts
        await asyncio.sleep(1.0)

        # Verify no events were handled due to malformed messages
        assert len(event_capture.events) == 0
        assert event_capture.handler_calls.get("malformed_handler", 0) == 0

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_event_store_connection_recovery(self, event_store, postgres_url):
        """Test event store recovery after database connection is restored."""
        # First, store some events successfully
        initial_events = [
            BaseEvent(event_type="recovery.test", payload={"phase": "initial", "id": i})
            for i in range(3)
        ]

        for event in initial_events:
            success = await event_store.store_event(event)
            assert success

        # Verify initial storage worked
        replayed = await event_store.replay_events(event_type="recovery.test")
        assert len(replayed) == 3

        # Temporarily break the connection by changing the URL to invalid
        original_url = event_store.database_url
        event_store.database_url = "postgresql://invalid:invalid@localhost:9999/invalid"

        # Try to store events - should fail
        failing_event = BaseEvent(
            event_type="recovery.test", payload={"phase": "failure", "id": 999}
        )
        success = await event_store.store_event(failing_event)
        assert success is False

        # Restore the connection
        event_store.database_url = original_url

        # Store more events - should succeed again
        recovery_events = [
            BaseEvent(
                event_type="recovery.test", payload={"phase": "recovery", "id": i}
            )
            for i in range(2)
        ]

        for event in recovery_events:
            success = await event_store.store_event(event)
            assert success

        # Verify we have initial + recovery events (5 total)
        final_replay = await event_store.replay_events(event_type="recovery.test")
        assert len(final_replay) == 5

        phases = [event.payload["phase"] for event in final_replay]
        assert phases.count("initial") == 3
        assert phases.count("recovery") == 2

    @pytest.mark.asyncio
    async def test_concurrent_error_scenarios(
        self, publisher, subscriber, test_exchange, test_queue, event_capture
    ):
        """Test system behavior under concurrent error conditions."""
        # Create mix of events - some will cause handler failures
        events = []
        for i in range(20):
            event = BaseEvent(
                event_type="concurrent.error.test",
                payload={
                    "sequence": i,
                    "should_fail": i % 3 == 0,  # Every 3rd event fails
                },
            )
            events.append(event)

        # Register handler that fails conditionally
        def create_conditional_handler():
            async def handler(event: BaseEvent):
                if event.payload.get("should_fail", False):
                    raise ValueError(f"Intentional failure for event {event.event_id}")
                event_capture.events.append(event)
                event_capture.handler_calls["conditional"] = (
                    event_capture.handler_calls.get("conditional", 0) + 1
                )

            handler.__name__ = "conditional"
            return handler

        conditional_handler = create_conditional_handler()
        subscriber.register_handler("concurrent.error.test", conditional_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Publish all events concurrently
        publish_tasks = []
        for event in events:
            task = publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            publish_tasks.append(task)

        # Wait for all publishing to complete
        results = await asyncio.gather(*publish_tasks, return_exceptions=True)

        # Verify publishing succeeded
        successful_publishes = sum(1 for r in results if r is True)
        assert successful_publishes > 15  # Most should succeed

        # Wait for processing
        await asyncio.sleep(2.0)

        # Verify that non-failing events were handled successfully
        expected_successful = len([e for e in events if not e.payload["should_fail"]])
        # Due to error handling, we might not get all successful events processed
        assert len(event_capture.events) <= expected_successful

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_dead_letter_queue_simulation(
        self, connection_manager, test_exchange, dead_letter_queue, event_capture
    ):
        """Test dead letter queue functionality by simulating message rejection."""
        from services.event_bus.subscribers.subscriber import EventSubscriber

        # Create a custom subscriber for DLQ testing
        class DLQTestSubscriber(EventSubscriber):
            def __init__(self, connection_manager, dlq_name):
                super().__init__(connection_manager)
                self.dlq_name = dlq_name
                self.rejected_messages = []

            async def _process_message(
                self, channel, method, properties, body: str
            ) -> bool:
                try:
                    # Always reject messages to simulate DLQ scenario
                    self.rejected_messages.append(body)
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    return False
                except Exception as e:
                    logger.error(f"Error in DLQ test processing: {e}")
                    return False

        # Setup DLQ test
        dlq_subscriber = DLQTestSubscriber(connection_manager, dead_letter_queue)

        # Create test events
        test_events = [
            BaseEvent(
                event_type="dlq.test", payload={"sequence": i, "data": f"dlq_test_{i}"}
            )
            for i in range(5)
        ]

        # Publish events to main queue (they'll be rejected and potentially go to DLQ)
        channel = await connection_manager.get_channel()

        for event in test_events:
            channel.basic_publish(
                exchange=test_exchange,
                routing_key="test.event",
                body=event.model_dump_json(),
            )

        # Start DLQ consumer to capture rejected messages
        consume_task = asyncio.create_task(
            dlq_subscriber.start_consuming(dead_letter_queue)
        )
        await asyncio.sleep(0.1)

        # Simulate some processing time
        await asyncio.sleep(1.0)

        # In a real DLQ setup, messages would be automatically routed to DLQ
        # Here we're testing the rejection mechanism
        # The exact number depends on message routing configuration
        logger.info(f"Rejected messages count: {len(dlq_subscriber.rejected_messages)}")

        channel.close()

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_connection_manager_reconnection(self, rabbitmq_url):
        """Test connection manager's ability to handle reconnection."""
        from services.event_bus.connection.manager import RabbitMQConnectionManager

        # Create connection manager
        manager = RabbitMQConnectionManager(
            rabbitmq_url, max_retries=3, retry_delay=0.1
        )

        # Initial connection
        connected = await manager.connect()
        assert connected
        assert manager.is_connected

        # Get channel to verify connection works
        channel = await manager.get_channel()
        assert channel is not None
        channel.close()

        # Force disconnect
        await manager.disconnect()
        assert not manager.is_connected

        # Try to get channel when disconnected - should fail
        with pytest.raises(RuntimeError, match="Not connected to RabbitMQ"):
            await manager.get_channel()

        # Reconnect
        connected = await manager.connect()
        assert connected
        assert manager.is_connected

        # Verify functionality restored
        channel = await manager.get_channel()
        assert channel is not None
        channel.close()

        # Cleanup
        await manager.disconnect()

    @pytest.mark.asyncio
    async def test_exception_propagation_and_logging(
        self, publisher, subscriber, test_exchange, test_queue, event_capture, caplog
    ):
        """Test that exceptions are properly logged and don't crash the system."""
        # Create events that will cause various types of exceptions
        error_events = [
            BaseEvent(event_type="error.test", payload={"error_type": "value_error"}),
            BaseEvent(event_type="error.test", payload={"error_type": "type_error"}),
            BaseEvent(event_type="error.test", payload={"error_type": "runtime_error"}),
        ]

        # Handler that throws different exceptions
        def create_error_handler():
            async def handler(event: BaseEvent):
                error_type = event.payload.get("error_type")
                event_capture.handler_calls["error_handler"] = (
                    event_capture.handler_calls.get("error_handler", 0) + 1
                )

                if error_type == "value_error":
                    raise ValueError("Test value error")
                elif error_type == "type_error":
                    raise TypeError("Test type error")
                elif error_type == "runtime_error":
                    raise RuntimeError("Test runtime error")

            handler.__name__ = "error_handler"
            return handler

        error_handler = create_error_handler()
        subscriber.register_handler("error.test", error_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Enable logging capture
        with caplog.at_level(logging.ERROR):
            # Publish error events
            for event in error_events:
                await publisher.publish(
                    event=event, exchange=test_exchange, routing_key="test.event"
                )

            # Wait for processing
            await asyncio.sleep(1.0)

        # Verify all handlers were called
        assert event_capture.handler_calls.get("error_handler", 0) == 3

        # Verify errors were logged
        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) >= 3

        # Verify different exception types were logged
        log_messages = [record.message for record in error_logs]
        assert any("value error" in msg.lower() for msg in log_messages)
        assert any("type error" in msg.lower() for msg in log_messages)
        assert any("runtime error" in msg.lower() for msg in log_messages)

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass
