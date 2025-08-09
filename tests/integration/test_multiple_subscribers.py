"""
Multiple Subscribers Integration Tests

This module tests scenarios with multiple subscribers, multiple handlers per event type,
load balancing, and concurrent processing patterns.
"""

import asyncio
import logging
from typing import Dict, List, Set

import pytest

from services.event_bus.models.base import BaseEvent
from services.event_bus.subscribers.subscriber import EventSubscriber

logger = logging.getLogger(__name__)


class TestMultipleSubscribers:
    """Test multiple subscriber scenarios and load balancing."""

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event_type(
        self,
        publisher,
        subscriber,
        test_exchange,
        test_queue,
        event_capture,
        async_timeout,
    ):
        """Test multiple handlers registered for the same event type."""
        # Create test event
        test_event = BaseEvent(
            event_type="multi.handler.test", payload={"data": "shared event"}
        )

        # Register multiple handlers for the same event type
        handler_1 = event_capture.create_handler("handler_1")
        handler_2 = event_capture.create_handler("handler_2")
        handler_3 = event_capture.create_handler("handler_3")

        subscriber.register_handler("multi.handler.test", handler_1)
        subscriber.register_handler("multi.handler.test", handler_2)
        subscriber.register_handler("multi.handler.test", handler_3)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Publish event
        success = await publisher.publish(
            event=test_event, exchange=test_exchange, routing_key="test.event"
        )
        assert success

        # Wait for processing
        await async_timeout(
            self._wait_for_handler_calls(event_capture, expected_calls=3), 3.0
        )

        # Verify all handlers were called
        assert event_capture.handler_calls["handler_1"] == 1
        assert event_capture.handler_calls["handler_2"] == 1
        assert event_capture.handler_calls["handler_3"] == 1

        # All handlers should receive the same event (3 total events captured)
        assert len(event_capture.events) == 3

        # Verify all events have the same ID and payload
        for captured_event in event_capture.events:
            assert captured_event.event_id == test_event.event_id
            assert captured_event.payload == test_event.payload

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_queue(
        self, connection_manager, publisher, test_exchange, test_queue, async_timeout
    ):
        """Test multiple subscriber instances consuming from the same queue (load balancing)."""
        num_events = 20

        # Create multiple subscribers
        subscriber_1 = EventSubscriber(connection_manager)
        subscriber_2 = EventSubscriber(connection_manager)
        subscriber_3 = EventSubscriber(connection_manager)

        # Create separate event captures for each subscriber
        capture_1 = {"events": [], "handler_calls": {}}
        capture_2 = {"events": [], "handler_calls": {}}
        capture_3 = {"events": [], "handler_calls": {}}

        def create_handler_for_capture(capture, handler_name):
            async def handler(event: BaseEvent):
                capture["events"].append(event)
                capture["handler_calls"][handler_name] = (
                    capture["handler_calls"].get(handler_name, 0) + 1
                )
                logger.info(f"Handler {handler_name} processed event {event.event_id}")

            handler.__name__ = handler_name
            return handler

        # Register handlers
        handler_1 = create_handler_for_capture(capture_1, "subscriber_1_handler")
        handler_2 = create_handler_for_capture(capture_2, "subscriber_2_handler")
        handler_3 = create_handler_for_capture(capture_3, "subscriber_3_handler")

        subscriber_1.register_handler("load.balance.test", handler_1)
        subscriber_2.register_handler("load.balance.test", handler_2)
        subscriber_3.register_handler("load.balance.test", handler_3)

        # Start all consumers
        consume_tasks = [
            asyncio.create_task(subscriber_1.start_consuming(test_queue)),
            asyncio.create_task(subscriber_2.start_consuming(test_queue)),
            asyncio.create_task(subscriber_3.start_consuming(test_queue)),
        ]
        await asyncio.sleep(0.2)

        # Create and publish events
        events = [
            BaseEvent(
                event_type="load.balance.test",
                payload={"sequence": i, "data": f"load_test_{i}"},
            )
            for i in range(num_events)
        ]

        for event in events:
            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            assert success
            await asyncio.sleep(0.01)  # Small delay to spread processing

        # Wait for all events to be processed
        await async_timeout(
            self._wait_for_total_events(
                [capture_1, capture_2, capture_3], expected_total=num_events
            ),
            10.0,
        )

        # Verify load balancing occurred
        total_processed = (
            len(capture_1["events"])
            + len(capture_2["events"])
            + len(capture_3["events"])
        )
        assert total_processed == num_events

        # Each subscriber should process some events (load balancing)
        # In practice, distribution might not be perfectly even
        processed_counts = [
            len(capture_1["events"]),
            len(capture_2["events"]),
            len(capture_3["events"]),
        ]

        # Verify all subscribers got at least some events (unless very unlucky timing)
        active_subscribers = sum(1 for count in processed_counts if count > 0)
        assert active_subscribers >= 2, (
            "Load balancing should distribute events across multiple subscribers"
        )

        # Verify no duplicate processing (each event processed exactly once)
        all_processed_ids = set()
        for capture in [capture_1, capture_2, capture_3]:
            for event in capture["events"]:
                assert event.event_id not in all_processed_ids, (
                    f"Duplicate processing of event {event.event_id}"
                )
                all_processed_ids.add(event.event_id)

        # Verify all original events were processed
        original_ids = {event.event_id for event in events}
        assert all_processed_ids == original_ids

        # Cleanup
        for task in consume_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_selective_event_handling_multiple_subscribers(
        self, connection_manager, publisher, test_exchange, test_queue, async_timeout
    ):
        """Test multiple subscribers handling different event types selectively."""
        # Create specialized subscribers
        user_subscriber = EventSubscriber(connection_manager)
        order_subscriber = EventSubscriber(connection_manager)
        notification_subscriber = EventSubscriber(connection_manager)

        # Event captures
        user_capture = {"events": [], "handler_calls": {}}
        order_capture = {"events": [], "handler_calls": {}}
        notification_capture = {"events": [], "handler_calls": {}}

        def create_specialized_handler(capture, handler_name, event_types: Set[str]):
            async def handler(event: BaseEvent):
                if event.event_type in event_types:
                    capture["events"].append(event)
                    capture["handler_calls"][handler_name] = (
                        capture["handler_calls"].get(handler_name, 0) + 1
                    )
                    logger.info(
                        f"Specialized handler {handler_name} processed {event.event_type}"
                    )

            handler.__name__ = handler_name
            return handler

        # Register specialized handlers
        user_handler = create_specialized_handler(
            user_capture, "user_specialist", {"user.created", "user.updated"}
        )
        order_handler = create_specialized_handler(
            order_capture, "order_specialist", {"order.placed", "order.shipped"}
        )
        notification_handler = create_specialized_handler(
            notification_capture,
            "notification_specialist",
            {"notification.sent", "notification.failed"},
        )

        user_subscriber.register_handler("user.created", user_handler)
        user_subscriber.register_handler("user.updated", user_handler)

        order_subscriber.register_handler("order.placed", order_handler)
        order_subscriber.register_handler("order.shipped", order_handler)

        notification_subscriber.register_handler(
            "notification.sent", notification_handler
        )
        notification_subscriber.register_handler(
            "notification.failed", notification_handler
        )

        # Start consumers
        consume_tasks = [
            asyncio.create_task(user_subscriber.start_consuming(test_queue)),
            asyncio.create_task(order_subscriber.start_consuming(test_queue)),
            asyncio.create_task(notification_subscriber.start_consuming(test_queue)),
        ]
        await asyncio.sleep(0.2)

        # Create mixed events
        events = [
            BaseEvent(event_type="user.created", payload={"user_id": "u1"}),
            BaseEvent(event_type="order.placed", payload={"order_id": "o1"}),
            BaseEvent(
                event_type="notification.sent", payload={"notification_id": "n1"}
            ),
            BaseEvent(event_type="user.updated", payload={"user_id": "u1"}),
            BaseEvent(event_type="order.shipped", payload={"order_id": "o1"}),
            BaseEvent(
                event_type="notification.failed", payload={"notification_id": "n2"}
            ),
            BaseEvent(
                event_type="unknown.event", payload={"data": "ignored"}
            ),  # Should be ignored
        ]

        # Publish all events
        for event in events:
            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            assert success

        # Wait for processing (expect 6 events processed, 1 ignored)
        await async_timeout(
            self._wait_for_total_events(
                [user_capture, order_capture, notification_capture], expected_total=6
            ),
            5.0,
        )

        # Verify specialized handling
        assert len(user_capture["events"]) == 2  # user.created, user.updated
        assert len(order_capture["events"]) == 2  # order.placed, order.shipped
        assert (
            len(notification_capture["events"]) == 2
        )  # notification.sent, notification.failed

        # Verify correct event types were handled
        user_types = {event.event_type for event in user_capture["events"]}
        assert user_types == {"user.created", "user.updated"}

        order_types = {event.event_type for event in order_capture["events"]}
        assert order_types == {"order.placed", "order.shipped"}

        notification_types = {
            event.event_type for event in notification_capture["events"]
        }
        assert notification_types == {"notification.sent", "notification.failed"}

        # Cleanup
        for task in consume_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_handler_failure_isolation_multiple_subscribers(
        self, connection_manager, publisher, test_exchange, test_queue, async_timeout
    ):
        """Test that handler failures in one subscriber don't affect others."""
        # Create subscribers
        reliable_subscriber = EventSubscriber(connection_manager)
        unreliable_subscriber = EventSubscriber(connection_manager)

        # Event captures
        reliable_capture = {"events": [], "handler_calls": {}, "errors": []}
        unreliable_capture = {"events": [], "handler_calls": {}, "errors": []}

        # Reliable handler (always succeeds)
        async def reliable_handler(event: BaseEvent):
            reliable_capture["events"].append(event)
            reliable_capture["handler_calls"]["reliable"] = (
                reliable_capture["handler_calls"].get("reliable", 0) + 1
            )
            logger.info(f"Reliable handler processed {event.event_id}")

        reliable_handler.__name__ = "reliable_handler"

        # Unreliable handler (fails on certain events)
        async def unreliable_handler(event: BaseEvent):
            unreliable_capture["handler_calls"]["unreliable"] = (
                unreliable_capture["handler_calls"].get("unreliable", 0) + 1
            )

            if event.payload.get("should_fail", False):
                error = ValueError(f"Unreliable handler failed for {event.event_id}")
                unreliable_capture["errors"].append(error)
                raise error

            unreliable_capture["events"].append(event)
            logger.info(f"Unreliable handler processed {event.event_id}")

        unreliable_handler.__name__ = "unreliable_handler"

        # Register handlers for same event type
        reliable_subscriber.register_handler("isolation.test", reliable_handler)
        unreliable_subscriber.register_handler("isolation.test", unreliable_handler)

        # Start consumers
        consume_tasks = [
            asyncio.create_task(reliable_subscriber.start_consuming(test_queue)),
            asyncio.create_task(unreliable_subscriber.start_consuming(test_queue)),
        ]
        await asyncio.sleep(0.2)

        # Create events - some will cause failures in unreliable handler
        events = [
            BaseEvent(
                event_type="isolation.test", payload={"id": 1, "should_fail": False}
            ),
            BaseEvent(
                event_type="isolation.test", payload={"id": 2, "should_fail": True}
            ),
            BaseEvent(
                event_type="isolation.test", payload={"id": 3, "should_fail": False}
            ),
            BaseEvent(
                event_type="isolation.test", payload={"id": 4, "should_fail": True}
            ),
            BaseEvent(
                event_type="isolation.test", payload={"id": 5, "should_fail": False}
            ),
        ]

        # Publish events
        for event in events:
            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            assert success
            await asyncio.sleep(0.05)  # Small delay between events

        # Wait for processing
        await asyncio.sleep(2.0)

        # Verify reliable subscriber processed events successfully
        # Due to load balancing, it might not get all events, but should succeed on those it gets
        assert reliable_capture["handler_calls"].get("reliable", 0) >= 2
        assert len(reliable_capture["errors"]) == 0

        # Verify unreliable subscriber encountered failures but didn't crash
        assert unreliable_capture["handler_calls"].get("unreliable", 0) >= 2
        assert len(unreliable_capture["errors"]) >= 1  # Should have some failures

        # Verify that some events were still processed successfully by unreliable handler
        # (those that didn't have should_fail=True)
        successful_unreliable = len(unreliable_capture["events"])
        failed_unreliable = len(unreliable_capture["errors"])

        logger.info(
            f"Unreliable handler: {successful_unreliable} successful, {failed_unreliable} failed"
        )

        # Both subscribers should have been active despite failures
        total_processed = len(reliable_capture["events"]) + len(
            unreliable_capture["events"]
        )
        assert total_processed >= 3, (
            "Despite failures, some events should have been processed"
        )

        # Cleanup
        for task in consume_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_concurrent_handler_execution(
        self, publisher, subscriber, test_exchange, test_queue, async_timeout
    ):
        """Test concurrent execution of multiple handlers for the same event."""
        num_events = 10
        processing_times = {
            "handler_slow": [],
            "handler_fast": [],
            "handler_medium": [],
        }

        # Create handlers with different processing speeds
        async def create_timed_handler(name: str, delay: float):
            async def handler(event: BaseEvent):
                start_time = asyncio.get_event_loop().time()
                await asyncio.sleep(delay)  # Simulate processing time
                end_time = asyncio.get_event_loop().time()

                processing_times[name].append(end_time - start_time)
                logger.info(
                    f"Handler {name} processed {event.event_id} in {end_time - start_time:.3f}s"
                )

            handler.__name__ = name
            return handler

        # Register handlers with different delays
        slow_handler = await create_timed_handler("handler_slow", 0.1)
        fast_handler = await create_timed_handler("handler_fast", 0.01)
        medium_handler = await create_timed_handler("handler_medium", 0.05)

        subscriber.register_handler("concurrent.processing", slow_handler)
        subscriber.register_handler("concurrent.processing", fast_handler)
        subscriber.register_handler("concurrent.processing", medium_handler)

        # Start consumer
        consume_task = asyncio.create_task(subscriber.start_consuming(test_queue))
        await asyncio.sleep(0.1)

        # Publish events and measure total processing time
        start_time = asyncio.get_event_loop().time()

        for i in range(num_events):
            event = BaseEvent(
                event_type="concurrent.processing", payload={"sequence": i}
            )
            success = await publisher.publish(
                event=event, exchange=test_exchange, routing_key="test.event"
            )
            assert success

        # Wait for all processing to complete
        await async_timeout(
            self._wait_for_handler_processing(
                processing_times, expected_events=num_events
            ),
            15.0,
        )

        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time

        # Verify all handlers processed all events
        assert len(processing_times["handler_slow"]) == num_events
        assert len(processing_times["handler_fast"]) == num_events
        assert len(processing_times["handler_medium"]) == num_events

        # Verify concurrent processing occurred (total time should be less than sequential)
        sequential_time_estimate = num_events * (0.1 + 0.01 + 0.05)  # Sum of all delays
        logger.info(
            f"Total processing time: {total_time:.3f}s, Sequential estimate: {sequential_time_estimate:.3f}s"
        )

        # Due to concurrent execution, total time should be significantly less than sequential
        assert total_time < sequential_time_estimate * 0.8, (
            "Concurrent processing should be faster than sequential"
        )

        # Verify processing times are as expected
        avg_slow = sum(processing_times["handler_slow"]) / len(
            processing_times["handler_slow"]
        )
        avg_fast = sum(processing_times["handler_fast"]) / len(
            processing_times["handler_fast"]
        )
        avg_medium = sum(processing_times["handler_medium"]) / len(
            processing_times["handler_medium"]
        )

        assert avg_fast < avg_medium < avg_slow, (
            "Handler timing should reflect their delays"
        )

        # Cleanup
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

    async def _wait_for_handler_calls(self, event_capture, expected_calls: int):
        """Wait for expected number of total handler calls."""
        while sum(event_capture.handler_calls.values()) < expected_calls:
            await asyncio.sleep(0.05)

    async def _wait_for_total_events(self, captures: List[Dict], expected_total: int):
        """Wait for expected total number of events across all captures."""
        while True:
            total_events = sum(len(capture["events"]) for capture in captures)
            if total_events >= expected_total:
                break
            await asyncio.sleep(0.05)

    async def _wait_for_handler_processing(
        self, processing_times: Dict, expected_events: int
    ):
        """Wait for all handlers to process expected number of events."""
        while True:
            total_processed = sum(len(times) for times in processing_times.values())
            expected_total = expected_events * len(processing_times)

            if total_processed >= expected_total:
                break
            await asyncio.sleep(0.05)
