"""
End-to-End Event Flow Integration Tests

This module tests the complete event flow from publisher to subscriber,
including event persistence, message routing, and handler execution.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

import pytest
import pytest_asyncio

from services.event_bus.models.base import BaseEvent

logger = logging.getLogger(__name__)


class TestEndToEndEventFlow:
    """Test complete event flow from publisher to subscriber."""

    @pytest.mark.asyncio
    async def test_single_event_complete_flow(
        self, 
        publisher, 
        subscriber, 
        event_store,
        test_exchange, 
        test_queue,
        event_capture,
        async_timeout
    ):
        """Test complete flow with single event: publish -> store -> consume -> handle."""
        # Create test event
        test_event = BaseEvent(
            event_type="integration.test",
            payload={"message": "end-to-end test", "priority": "high"}
        )
        
        # Register event handler
        handler = event_capture.create_handler("e2e_handler")
        subscriber.register_handler("integration.test", handler)
        
        # Start consumer in background
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)  # Give consumer time to start
        
        # Publish event
        success = await publisher.publish(
            event=test_event,
            exchange=test_exchange,
            routing_key="test.event",
            persistent=True
        )
        assert success, "Failed to publish event"
        
        # Store event in event store
        stored = await event_store.store_event(test_event)
        assert stored, "Failed to store event"
        
        # Wait for event processing
        await async_timeout(self._wait_for_events(event_capture, expected_count=1), 3.0)
        
        # Verify event was handled
        assert len(event_capture.events) == 1
        received_event = event_capture.events[0]
        
        # Verify event integrity
        assert received_event.event_id == test_event.event_id
        assert received_event.event_type == test_event.event_type
        assert received_event.payload == test_event.payload
        
        # Verify event was persisted
        retrieved_event = await event_store.get_event_by_id(test_event.event_id)
        assert retrieved_event is not None
        assert retrieved_event.event_id == test_event.event_id
        
        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_multiple_events_sequential_flow(
        self,
        publisher,
        subscriber, 
        event_store,
        test_exchange,
        test_queue,
        sample_events,
        event_capture,
        async_timeout
    ):
        """Test sequential processing of multiple events."""
        # Register handlers for different event types
        user_handler = event_capture.create_handler("user_handler")
        order_handler = event_capture.create_handler("order_handler")
        payment_handler = event_capture.create_handler("payment_handler")
        
        subscriber.register_handler("user.created", user_handler)
        subscriber.register_handler("user.updated", user_handler)
        subscriber.register_handler("order.placed", order_handler)
        subscriber.register_handler("payment.processed", payment_handler)
        
        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)
        
        # Publish and store all events
        for event in sample_events:
            success = await publisher.publish(
                event=event,
                exchange=test_exchange,
                routing_key="test.event",
                persistent=True
            )
            assert success, f"Failed to publish event {event.event_id}"
            
            stored = await event_store.store_event(event)
            assert stored, f"Failed to store event {event.event_id}"
            
            # Small delay to ensure ordering
            await asyncio.sleep(0.01)
        
        # Wait for all events to be processed
        await async_timeout(
            self._wait_for_events(event_capture, expected_count=len(sample_events)), 
            10.0
        )
        
        # Verify all events were handled
        assert len(event_capture.events) == len(sample_events)
        
        # Verify handler calls
        assert event_capture.handler_calls.get("user_handler", 0) > 0
        assert event_capture.handler_calls.get("order_handler", 0) > 0
        assert event_capture.handler_calls.get("payment_handler", 0) > 0
        
        # Verify all events were persisted
        for original_event in sample_events:
            retrieved = await event_store.get_event_by_id(original_event.event_id)
            assert retrieved is not None, f"Event {original_event.event_id} not found in store"
        
        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_event_flow_with_filtering(
        self,
        publisher,
        subscriber,
        event_store, 
        test_exchange,
        test_queue,
        event_capture,
        async_timeout
    ):
        """Test event flow with selective event handling based on event type."""
        # Create events of different types
        events = [
            BaseEvent(event_type="important.event", payload={"priority": "high"}),
            BaseEvent(event_type="normal.event", payload={"priority": "normal"}),
            BaseEvent(event_type="important.event", payload={"priority": "critical"}),
            BaseEvent(event_type="ignored.event", payload={"priority": "low"}),
        ]
        
        # Register handler only for important events
        important_handler = event_capture.create_handler("important_handler")
        subscriber.register_handler("important.event", important_handler)
        
        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)
        
        # Publish all events
        for event in events:
            success = await publisher.publish(
                event=event,
                exchange=test_exchange,
                routing_key="test.event"
            )
            assert success
            
            await event_store.store_event(event)
        
        # Wait for processing (only important events should be handled)
        await async_timeout(self._wait_for_events(event_capture, expected_count=2), 5.0)
        
        # Verify only important events were handled
        assert len(event_capture.events) == 2
        assert event_capture.handler_calls["important_handler"] == 2
        
        # Verify all handled events are of the correct type
        for event in event_capture.events:
            assert event.event_type == "important.event"
        
        # Verify all events were still persisted (even if not handled)
        for original_event in events:
            retrieved = await event_store.get_event_by_id(original_event.event_id)
            assert retrieved is not None
        
        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_concurrent_publishing_and_consuming(
        self,
        publisher,
        subscriber,
        event_store,
        test_exchange, 
        test_queue,
        event_capture,
        async_timeout
    ):
        """Test concurrent event publishing and consuming under load."""
        num_events = 50
        
        # Create events
        events = [
            BaseEvent(
                event_type="load.test",
                payload={"sequence": i, "batch": "concurrent"}
            )
            for i in range(num_events)
        ]
        
        # Register handler
        handler = event_capture.create_handler("concurrent_handler")
        subscriber.register_handler("load.test", handler)
        
        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)
        
        # Create tasks for concurrent publishing and storing
        async def publish_and_store(event: BaseEvent):
            success = await publisher.publish(
                event=event,
                exchange=test_exchange,
                routing_key="test.event"
            )
            if success:
                await event_store.store_event(event)
            return success
        
        # Execute all publishing concurrently
        publish_tasks = [publish_and_store(event) for event in events]
        results = await asyncio.gather(*publish_tasks, return_exceptions=True)
        
        # Verify all publishes succeeded
        successful_publishes = sum(1 for r in results if r is True)
        assert successful_publishes == num_events, f"Only {successful_publishes}/{num_events} events published successfully"
        
        # Wait for all events to be consumed
        await async_timeout(
            self._wait_for_events(event_capture, expected_count=num_events),
            15.0
        )
        
        # Verify all events were handled
        assert len(event_capture.events) == num_events
        assert event_capture.handler_calls["concurrent_handler"] == num_events
        
        # Verify sequence numbers are present (order might vary due to concurrency)
        received_sequences = {event.payload["sequence"] for event in event_capture.events}
        expected_sequences = set(range(num_events))
        assert received_sequences == expected_sequences, "Some events were lost or duplicated"
        
        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio 
    async def test_event_flow_with_persistence_verification(
        self,
        publisher,
        subscriber,
        event_store,
        test_exchange,
        test_queue,
        event_capture,
        async_timeout
    ):
        """Test event flow with detailed persistence verification."""
        # Create time-stamped events
        now = datetime.now(timezone.utc)
        events = [
            BaseEvent(
                event_type="persistence.test",
                payload={
                    "created_at": now.isoformat(),
                    "data": f"test_data_{i}",
                    "metadata": {"version": "1.0", "source": "integration_test"}
                }
            )
            for i in range(5)
        ]
        
        # Register handler
        handler = event_capture.create_handler("persistence_handler")
        subscriber.register_handler("persistence.test", handler)
        
        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)
        
        # Publish with persistence
        for event in events:
            success = await publisher.publish(
                event=event,
                exchange=test_exchange,
                routing_key="test.event",
                persistent=True  # Ensure message persistence
            )
            assert success
            
            stored = await event_store.store_event(event)
            assert stored
        
        # Wait for processing
        await async_timeout(self._wait_for_events(event_capture, expected_count=5), 5.0)
        
        # Verify event handling
        assert len(event_capture.events) == 5
        
        # Detailed persistence verification
        for i, original_event in enumerate(events):
            # Retrieve from store
            retrieved = await event_store.get_event_by_id(original_event.event_id)
            assert retrieved is not None, f"Event {i} not found in store"
            
            # Verify all fields match
            assert retrieved.event_id == original_event.event_id
            assert retrieved.event_type == original_event.event_type
            assert retrieved.payload == original_event.payload
            assert retrieved.timestamp == original_event.timestamp
            
            # Verify handled event matches
            handled_event = next(
                (e for e in event_capture.events if e.event_id == original_event.event_id),
                None
            )
            assert handled_event is not None, f"Event {i} was not handled"
            assert handled_event.payload == original_event.payload
        
        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    async def _wait_for_events(self, event_capture, expected_count: int, check_interval: float = 0.1):
        """Helper method to wait for expected number of events to be captured."""
        while len(event_capture.events) < expected_count:
            await asyncio.sleep(check_interval)
        
        # Additional small wait to ensure no more events are coming
        await asyncio.sleep(check_interval * 2)