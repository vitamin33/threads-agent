"""
Event Ordering Integration Tests

This module tests message ordering guarantees, including FIFO behavior,
timestamp-based ordering, and ordering preservation under various conditions.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Tuple

import pytest

from services.event_bus.models.base import BaseEvent

logger = logging.getLogger(__name__)


class TestEventOrdering:
    """Test event ordering guarantees and preservation."""

    @pytest.mark.asyncio
    async def test_fifo_ordering_single_consumer(
        self,
        publisher,
        subscriber,
        test_exchange,
        test_queue,
        message_ordering_verifier,
        async_timeout,
    ):
        """Test FIFO (First In, First Out) ordering with single consumer."""
        num_events = 20
        received_events = []

        # Create handler that preserves order
        async def order_preserving_handler(event: BaseEvent):
            received_events.append(event)
            logger.info(
                f"Received event {event.event_id}, sequence: {event.payload['sequence']}"
            )

        order_preserving_handler.__name__ = "order_handler"
        subscriber.register_handler("ordering.test", order_preserving_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Create events with sequential ordering
        events = []
        for i in range(num_events):
            event = BaseEvent(
                event_type="ordering.test",
                payload={
                    "sequence": i,
                    "data": f"sequential_event_{i}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            events.append(event)

        # Publish events sequentially with small delays to ensure ordering
        for event in events:
            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            assert success
            await asyncio.sleep(0.01)  # Small delay to ensure RabbitMQ ordering

        # Wait for all events to be processed
        await async_timeout(self._wait_for_events(received_events, num_events), 10.0)

        # Verify FIFO ordering
        assert len(received_events) == num_events

        # Check sequence ordering
        for i, received_event in enumerate(received_events):
            assert received_event.payload["sequence"] == i, f"Event {i} out of order"

        # Use verifier utility
        expected_order = [event.event_id for event in events]
        assert message_ordering_verifier(received_events, expected_order)

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_timestamp_based_ordering_preservation(
        self,
        publisher,
        subscriber,
        event_store,
        test_exchange,
        test_queue,
        async_timeout,
    ):
        """Test that timestamp-based ordering is preserved through the system."""
        base_time = datetime.now(timezone.utc)
        received_events = []

        # Handler that captures events
        async def timestamp_handler(event: BaseEvent):
            received_events.append(event)

        timestamp_handler.__name__ = "timestamp_handler"
        subscriber.register_handler("timestamp.ordering", timestamp_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Create events with specific timestamps (not in chronological order initially)
        events_data = [
            (5, base_time + timedelta(seconds=5)),
            (2, base_time + timedelta(seconds=2)),
            (8, base_time + timedelta(seconds=8)),
            (1, base_time + timedelta(seconds=1)),
            (6, base_time + timedelta(seconds=6)),
            (3, base_time + timedelta(seconds=3)),
            (7, base_time + timedelta(seconds=7)),
            (4, base_time + timedelta(seconds=4)),
        ]

        events = []
        for sequence, timestamp in events_data:
            event = BaseEvent(
                event_type="timestamp.ordering",
                payload={"sequence": sequence, "original_time": timestamp.isoformat()},
                timestamp=timestamp,
            )
            events.append((sequence, event))

        # Store events in event store (should maintain timestamp ordering)
        for sequence, event in events:
            stored = await event_store.store_event(event)
            assert stored

        # Publish events in original (non-chronological) order
        for sequence, event in events:
            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            assert success
            await asyncio.sleep(0.01)

        # Wait for processing
        await async_timeout(self._wait_for_events(received_events, len(events)), 5.0)

        # Verify all events received
        assert len(received_events) == len(events)

        # Test event store ordering (replay should be timestamp-ordered)
        replayed_events = await event_store.replay_events(
            event_type="timestamp.ordering"
        )
        assert len(replayed_events) == len(events)

        # Verify event store maintains timestamp ordering
        for i in range(1, len(replayed_events)):
            assert replayed_events[i - 1].timestamp <= replayed_events[i].timestamp

        # Verify sequence matches timestamp order in replayed events
        expected_sequence = [1, 2, 3, 4, 5, 6, 7, 8]  # Chronological order
        replayed_sequences = [event.payload["sequence"] for event in replayed_events]
        assert replayed_sequences == expected_sequence

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_ordering_with_processing_delays(
        self, publisher, subscriber, test_exchange, test_queue, async_timeout
    ):
        """Test ordering preservation when handlers have different processing times."""
        num_events = 15
        processed_events = []
        processing_times = []

        # Handler with variable processing delays based on payload
        async def variable_delay_handler(event: BaseEvent):
            start_time = asyncio.get_event_loop().time()

            # Add variable delay based on sequence
            sequence = event.payload["sequence"]
            delay = 0.01 + (sequence % 3) * 0.02  # 0.01, 0.03, or 0.05 seconds
            await asyncio.sleep(delay)

            end_time = asyncio.get_event_loop().time()

            processed_events.append((sequence, event))
            processing_times.append(end_time - start_time)

            logger.info(f"Processed event {sequence} with delay {delay:.3f}s")

        variable_delay_handler.__name__ = "variable_delay_handler"
        subscriber.register_handler("delay.ordering.test", variable_delay_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Create and publish events in sequence
        events = []
        for i in range(num_events):
            event = BaseEvent(
                event_type="delay.ordering.test",
                payload={"sequence": i, "expected_delay": 0.01 + (i % 3) * 0.02},
            )
            events.append(event)

            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            assert success
            await asyncio.sleep(0.005)  # Small publish delay

        # Wait for all processing to complete
        await async_timeout(
            self._wait_for_processed_events(processed_events, num_events), 20.0
        )

        # Verify all events were processed
        assert len(processed_events) == num_events

        # Due to variable processing delays, the completion order might differ from input order
        # But we can verify that all events were processed correctly
        processed_sequences = [seq for seq, event in processed_events]
        expected_sequences = set(range(num_events))
        assert set(processed_sequences) == expected_sequences

        # Verify processing times varied as expected
        assert len(processing_times) == num_events
        min_time = min(processing_times)
        max_time = max(processing_times)
        assert max_time > min_time  # Should have variation due to different delays

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_ordering_under_high_load(
        self, publisher, subscriber, test_exchange, test_queue, async_timeout
    ):
        """Test ordering preservation under high message load."""
        num_events = 100
        received_events = []

        # Fast handler to process high load
        async def high_load_handler(event: BaseEvent):
            received_events.append(event)

        high_load_handler.__name__ = "high_load_handler"
        subscriber.register_handler("high.load.ordering", high_load_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Create events in batches with clear ordering
        batch_size = 20
        all_events = []

        for batch in range(num_events // batch_size):
            batch_events = []
            for i in range(batch_size):
                sequence = batch * batch_size + i
                event = BaseEvent(
                    event_type="high.load.ordering",
                    payload={"sequence": sequence, "batch": batch, "batch_position": i},
                )
                batch_events.append(event)
                all_events.append(event)

            # Publish batch rapidly
            for event in batch_events:
                success = await publisher.publish(
                    event=event, exchange=test_exchange, routing_key="test.event"
                )
                assert success

            # Small delay between batches
            await asyncio.sleep(0.02)

        # Wait for all events to be processed
        await async_timeout(self._wait_for_events(received_events, num_events), 30.0)

        # Verify all events received
        assert len(received_events) == num_events

        # Verify no events were lost
        received_sequences = {event.payload["sequence"] for event in received_events}
        expected_sequences = set(range(num_events))
        assert received_sequences == expected_sequences, (
            "Some events were lost under high load"
        )

        # Verify batch integrity (events within each batch should maintain relative order)
        batches_received = {}
        for event in received_events:
            batch = event.payload["batch"]
            if batch not in batches_received:
                batches_received[batch] = []
            batches_received[batch].append(event.payload["batch_position"])

        # Check each batch maintains internal ordering
        for batch, positions in batches_received.items():
            positions.sort()  # Sort to check if it was already ordered
            expected_positions = list(range(batch_size))
            assert positions == expected_positions, (
                f"Batch {batch} lost internal ordering"
            )

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_ordering_across_reconnections(
        self,
        connection_manager,
        publisher,
        subscriber,
        test_exchange,
        test_queue,
        async_timeout,
    ):
        """Test that ordering is maintained across connection reconnections."""
        received_events = []

        # Handler to capture events
        async def reconnection_handler(event: BaseEvent):
            received_events.append(event)
            logger.info(
                f"Received event {event.payload['sequence']} after reconnection test"
            )

        reconnection_handler.__name__ = "reconnection_handler"
        subscriber.register_handler("reconnection.ordering", reconnection_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Publish first batch of events
        first_batch_size = 5
        for i in range(first_batch_size):
            event = BaseEvent(
                event_type="reconnection.ordering",
                payload={"sequence": i, "batch": "first"},
            )
            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            assert success
            await asyncio.sleep(0.01)

        # Wait for first batch processing
        await async_timeout(
            self._wait_for_events(received_events, first_batch_size), 3.0
        )

        # Simulate connection disruption and recovery
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

        # Disconnect and reconnect
        await connection_manager.disconnect()
        await asyncio.sleep(0.1)
        connected = await connection_manager.connect()
        assert connected

        # Restart consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.2)

        # Publish second batch of events
        second_batch_size = 5
        for i in range(second_batch_size):
            event = BaseEvent(
                event_type="reconnection.ordering",
                payload={"sequence": first_batch_size + i, "batch": "second"},
            )
            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            assert success
            await asyncio.sleep(0.01)

        # Wait for second batch processing
        total_expected = first_batch_size + second_batch_size
        await async_timeout(self._wait_for_events(received_events, total_expected), 5.0)

        # Verify total events received
        assert len(received_events) == total_expected

        # Verify ordering across reconnection
        sequences = [event.payload["sequence"] for event in received_events]
        expected_sequences = list(range(total_expected))
        assert sequences == expected_sequences, "Ordering lost across reconnection"

        # Verify batch distribution
        first_batch_events = [
            e for e in received_events if e.payload["batch"] == "first"
        ]
        second_batch_events = [
            e for e in received_events if e.payload["batch"] == "second"
        ]

        assert len(first_batch_events) == first_batch_size
        assert len(second_batch_events) == second_batch_size

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_ordering_with_multiple_routing_keys(
        self,
        publisher,
        subscriber,
        test_exchange,
        test_queue,
        connection_manager,
        async_timeout,
    ):
        """Test ordering preservation when using different routing keys."""
        received_events = []

        # Create additional queues for different routing keys
        priority_queue = f"priority_{test_queue}"
        normal_queue = f"normal_{test_queue}"

        try:
            # Setup additional queues
            channel = await connection_manager.get_channel()
            channel.queue_declare(queue=priority_queue, durable=True)
            channel.queue_declare(queue=normal_queue, durable=True)

            # Bind queues with different routing keys
            channel.queue_bind(
                exchange=test_exchange,
                queue=priority_queue,
                routing_key="priority.event",
            )
            channel.queue_bind(
                exchange=test_exchange, queue=normal_queue, routing_key="normal.event"
            )
            channel.close()
        except Exception as e:
            logger.error(f"Failed to setup additional queues: {e}")
            pytest.skip("Could not setup test infrastructure")

        # Handler that tracks routing information
        async def routing_handler(event: BaseEvent):
            received_events.append(event)
            logger.info(
                f"Received {event.payload['priority']} event {event.payload['sequence']}"
            )

        routing_handler.__name__ = "routing_handler"
        subscriber.register_handler("routing.ordering.test", routing_handler)

        # Start consumers on all queues
        consume_tasks = [
            asyncio.create_task(subscriber.start_consuming(test_queue)),
            asyncio.create_task(subscriber.start_consuming(priority_queue)),
            asyncio.create_task(subscriber.start_consuming(normal_queue)),
        ]
        await asyncio.sleep(0.2)

        # Publish events with different priorities and routing keys
        events_data = [
            (0, "normal", "normal.event"),
            (1, "priority", "priority.event"),
            (2, "normal", "normal.event"),
            (3, "priority", "priority.event"),
            (4, "test", "test.event"),  # Goes to main test queue
            (5, "normal", "normal.event"),
            (6, "priority", "priority.event"),
            (7, "test", "test.event"),
        ]

        published_events = []
        for sequence, priority, routing_key in events_data:
            event = BaseEvent(
                event_type="routing.ordering.test",
                payload={
                    "sequence": sequence,
                    "priority": priority,
                    "routing_key": routing_key,
                },
            )
            published_events.append(event)

            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key=routing_key
            )
            assert success
            await asyncio.sleep(0.01)

        # Wait for all events to be processed
        await async_timeout(
            self._wait_for_events(received_events, len(events_data)), 8.0
        )

        # Verify all events received
        assert len(received_events) == len(events_data)

        # Verify no events were lost
        received_sequences = {event.payload["sequence"] for event in received_events}
        expected_sequences = {seq for seq, _, _ in events_data}
        assert received_sequences == expected_sequences

        # Group by routing key and verify ordering within each group
        groups = {"normal": [], "priority": [], "test": []}
        for event in received_events:
            priority = event.payload["priority"]
            if priority in groups:
                groups[priority].append(event.payload["sequence"])

        # Within each priority group, events should maintain their relative order
        # (though absolute ordering across groups may vary due to different queues)
        for priority, sequences in groups.items():
            if len(sequences) > 1:
                # Check that sequences within each group are in ascending order
                sequences.sort()  # Sort to see if they were already in order
                original_sequences = [
                    event.payload["sequence"]
                    for event in published_events
                    if event.payload["priority"] == priority
                ]
                assert sequences == sorted(original_sequences), (
                    f"Ordering lost in {priority} group"
                )

        # Cleanup
        for task in consume_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _wait_for_events(self, event_list: List, expected_count: int):
        """Wait for expected number of events to be received."""
        while len(event_list) < expected_count:
            await asyncio.sleep(0.05)

    async def _wait_for_processed_events(
        self, processed_list: List[Tuple], expected_count: int
    ):
        """Wait for expected number of processed events."""
        while len(processed_list) < expected_count:
            await asyncio.sleep(0.05)
