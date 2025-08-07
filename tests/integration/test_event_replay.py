"""
Event Replay Integration Tests

This module tests the event store's replay functionality, including
time-based filtering, event type filtering, and replay ordering guarantees.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List

import pytest
import pytest_asyncio

from services.event_bus.models.base import BaseEvent

logger = logging.getLogger(__name__)


class TestEventReplay:
    """Test event store replay functionality."""

    @pytest.mark.asyncio
    async def test_basic_event_replay(self, event_store, sample_events):
        """Test basic event replay functionality."""
        # Store all sample events
        for event in sample_events:
            stored = await event_store.store_event(event)
            assert stored, f"Failed to store event {event.event_id}"
        
        # Replay all events
        replayed_events = await event_store.replay_events()
        
        # Verify all events were replayed
        assert len(replayed_events) == len(sample_events)
        
        # Verify events are ordered by timestamp
        for i in range(1, len(replayed_events)):
            assert replayed_events[i-1].timestamp <= replayed_events[i].timestamp
        
        # Verify event integrity
        original_ids = {event.event_id for event in sample_events}
        replayed_ids = {event.event_id for event in replayed_events}
        assert original_ids == replayed_ids

    @pytest.mark.asyncio
    async def test_replay_with_time_range_filtering(self, event_store):
        """Test event replay with time-based filtering."""
        # Create events with specific timestamps
        base_time = datetime.now(timezone.utc)
        events = [
            BaseEvent(
                event_type="time.test",
                payload={"sequence": i},
                timestamp=base_time + timedelta(minutes=i)
            )
            for i in range(10)
        ]
        
        # Store events
        for event in events:
            await event_store.store_event(event)
        
        # Define time ranges
        start_time = base_time + timedelta(minutes=2)
        end_time = base_time + timedelta(minutes=6)
        
        # Replay events within time range
        replayed = await event_store.replay_events(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify correct events were replayed (sequences 2, 3, 4, 5, 6)
        assert len(replayed) == 5
        sequences = [event.payload["sequence"] for event in replayed]
        assert sequences == [2, 3, 4, 5, 6]
        
        # Verify all replayed events are within time range
        for event in replayed:
            assert start_time <= event.timestamp <= end_time

    @pytest.mark.asyncio
    async def test_replay_with_start_time_only(self, event_store):
        """Test replay with only start time specified."""
        base_time = datetime.now(timezone.utc)
        events = [
            BaseEvent(
                event_type="start.time.test",
                payload={"sequence": i},
                timestamp=base_time + timedelta(seconds=i * 10)
            )
            for i in range(8)
        ]
        
        # Store events
        for event in events:
            await event_store.store_event(event)
        
        # Replay from middle timestamp
        start_time = base_time + timedelta(seconds=30)  # After 3rd event
        replayed = await event_store.replay_events(start_time=start_time)
        
        # Should get events 3, 4, 5, 6, 7 (5 events)
        assert len(replayed) == 5
        sequences = [event.payload["sequence"] for event in replayed]
        assert sequences == [3, 4, 5, 6, 7]

    @pytest.mark.asyncio
    async def test_replay_with_end_time_only(self, event_store):
        """Test replay with only end time specified."""
        base_time = datetime.now(timezone.utc)
        events = [
            BaseEvent(
                event_type="end.time.test",
                payload={"sequence": i},
                timestamp=base_time + timedelta(seconds=i * 5)
            )
            for i in range(6)
        ]
        
        # Store events
        for event in events:
            await event_store.store_event(event)
        
        # Replay up to middle timestamp
        end_time = base_time + timedelta(seconds=15)  # Before 4th event
        replayed = await event_store.replay_events(end_time=end_time)
        
        # Should get events 0, 1, 2, 3 (4 events)
        assert len(replayed) == 4
        sequences = [event.payload["sequence"] for event in replayed]
        assert sequences == [0, 1, 2, 3]

    @pytest.mark.asyncio
    async def test_replay_with_event_type_filtering(self, event_store):
        """Test replay with event type filtering."""
        # Create events of different types
        events = []
        event_types = ["user.created", "order.placed", "user.updated", "payment.processed"]
        
        for i in range(12):
            event = BaseEvent(
                event_type=event_types[i % 4],
                payload={"sequence": i},
                timestamp=datetime.now(timezone.utc) + timedelta(milliseconds=i * 100)
            )
            events.append(event)
        
        # Store all events
        for event in events:
            await event_store.store_event(event)
        
        # Replay only user events
        user_events = await event_store.replay_events(event_type="user.created")
        assert len(user_events) == 3  # Events at indices 0, 4, 8
        sequences = [event.payload["sequence"] for event in user_events]
        assert sequences == [0, 4, 8]
        
        # Replay only order events
        order_events = await event_store.replay_events(event_type="order.placed")
        assert len(order_events) == 3  # Events at indices 1, 5, 9
        sequences = [event.payload["sequence"] for event in order_events]
        assert sequences == [1, 5, 9]

    @pytest.mark.asyncio
    async def test_replay_with_combined_filters(self, event_store):
        """Test replay with both time and event type filtering."""
        base_time = datetime.now(timezone.utc)
        events = []
        
        # Create events across different times and types
        for i in range(20):
            event = BaseEvent(
                event_type="important.event" if i % 3 == 0 else "normal.event",
                payload={"sequence": i, "importance": "high" if i % 3 == 0 else "low"},
                timestamp=base_time + timedelta(seconds=i * 2)
            )
            events.append(event)
        
        # Store all events
        for event in events:
            await event_store.store_event(event)
        
        # Replay important events in specific time range
        start_time = base_time + timedelta(seconds=10)  # After 5th event
        end_time = base_time + timedelta(seconds=30)    # Before 16th event
        
        filtered_events = await event_store.replay_events(
            start_time=start_time,
            end_time=end_time,
            event_type="important.event"
        )
        
        # Important events in range: indices 6, 9, 12, 15
        # Time range covers events with indices 5-15
        # So we should get important events at indices 6, 9, 12
        assert len(filtered_events) == 3
        sequences = [event.payload["sequence"] for event in filtered_events]
        assert sequences == [6, 9, 12]
        
        # Verify all are important events
        for event in filtered_events:
            assert event.event_type == "important.event"
            assert event.payload["importance"] == "high"

    @pytest.mark.asyncio
    async def test_replay_with_limit(self, event_store):
        """Test replay with result limit."""
        # Create many events
        events = [
            BaseEvent(
                event_type="limit.test",
                payload={"sequence": i},
                timestamp=datetime.now(timezone.utc) + timedelta(milliseconds=i * 50)
            )
            for i in range(100)
        ]
        
        # Store all events
        for event in events:
            await event_store.store_event(event)
        
        # Replay with various limits
        limited_10 = await event_store.replay_events(limit=10)
        assert len(limited_10) == 10
        sequences = [event.payload["sequence"] for event in limited_10]
        assert sequences == list(range(10))  # First 10 events
        
        limited_25 = await event_store.replay_events(limit=25)
        assert len(limited_25) == 25
        sequences = [event.payload["sequence"] for event in limited_25]
        assert sequences == list(range(25))  # First 25 events
        
        # Verify ordering is maintained
        for i in range(1, len(limited_25)):
            assert limited_25[i-1].timestamp <= limited_25[i].timestamp

    @pytest.mark.asyncio
    async def test_replay_empty_results(self, event_store):
        """Test replay scenarios that return no results."""
        # Store some events
        events = [
            BaseEvent(
                event_type="existing.event",
                payload={"data": f"test_{i}"},
                timestamp=datetime.now(timezone.utc)
            )
            for i in range(3)
        ]
        
        for event in events:
            await event_store.store_event(event)
        
        # Test various empty result scenarios
        
        # Non-existent event type
        no_events = await event_store.replay_events(event_type="nonexistent.event")
        assert len(no_events) == 0
        
        # Time range with no events
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        no_events = await event_store.replay_events(start_time=future_time)
        assert len(no_events) == 0
        
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        no_events = await event_store.replay_events(end_time=past_time)
        assert len(no_events) == 0
        
        # Limit of 0
        no_events = await event_store.replay_events(limit=0)
        assert len(no_events) == 0

    @pytest.mark.asyncio
    async def test_replay_ordering_consistency(self, event_store):
        """Test that replay maintains consistent ordering across multiple calls."""
        # Create events with carefully controlled timestamps
        base_time = datetime.now(timezone.utc)
        events = []
        
        for i in range(50):
            # Add some millisecond variations but maintain order
            timestamp = base_time + timedelta(milliseconds=i * 100 + (i % 3))
            event = BaseEvent(
                event_type="ordering.test",
                payload={"sequence": i, "batch": i // 10},
                timestamp=timestamp
            )
            events.append(event)
        
        # Store events (intentionally out of order)
        import random
        shuffled_events = events.copy()
        random.shuffle(shuffled_events)
        
        for event in shuffled_events:
            await event_store.store_event(event)
        
        # Replay multiple times and verify consistent ordering
        replays = []
        for _ in range(5):
            replay = await event_store.replay_events(event_type="ordering.test")
            replays.append(replay)
        
        # All replays should have same length
        assert all(len(replay) == 50 for replay in replays)
        
        # All replays should have same ordering
        for replay in replays[1:]:
            for i, event in enumerate(replay):
                assert event.event_id == replays[0][i].event_id
                assert event.payload["sequence"] == replays[0][i].payload["sequence"]
        
        # Verify ordering is by timestamp
        for replay in replays:
            for i in range(1, len(replay)):
                assert replay[i-1].timestamp <= replay[i].timestamp

    @pytest.mark.asyncio
    async def test_replay_with_complex_payload_integrity(self, event_store):
        """Test that complex payloads maintain integrity during replay."""
        # Create events with complex nested payloads
        complex_events = []
        
        for i in range(10):
            complex_payload = {
                "user": {
                    "id": f"user_{i}",
                    "profile": {
                        "name": f"Test User {i}",
                        "preferences": {
                            "notifications": True,
                            "theme": "dark" if i % 2 == 0 else "light",
                            "languages": ["en", "es"] if i % 3 == 0 else ["en"]
                        }
                    }
                },
                "metadata": {
                    "source": "integration_test",
                    "version": "2.1.0",
                    "tags": [f"tag_{j}" for j in range(i % 4)],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "metrics": {
                    "score": float(i * 1.5),
                    "count": i ** 2,
                    "ratio": i / 10.0 if i > 0 else 0.0
                }
            }
            
            event = BaseEvent(
                event_type="complex.payload",
                payload=complex_payload
            )
            complex_events.append(event)
        
        # Store events
        for event in complex_events:
            stored = await event_store.store_event(event)
            assert stored, f"Failed to store complex event {event.event_id}"
        
        # Replay events
        replayed = await event_store.replay_events(event_type="complex.payload")
        assert len(replayed) == 10
        
        # Verify payload integrity for each event
        for i, replayed_event in enumerate(replayed):
            original_event = complex_events[i]
            
            # Deep comparison of complex nested structure
            assert replayed_event.payload["user"]["id"] == original_event.payload["user"]["id"]
            assert replayed_event.payload["user"]["profile"]["name"] == original_event.payload["user"]["profile"]["name"]
            assert replayed_event.payload["user"]["profile"]["preferences"] == original_event.payload["user"]["profile"]["preferences"]
            assert replayed_event.payload["metadata"]["tags"] == original_event.payload["metadata"]["tags"]
            assert replayed_event.payload["metrics"]["score"] == original_event.payload["metrics"]["score"]
            assert replayed_event.payload["metrics"]["count"] == original_event.payload["metrics"]["count"]
            
            # Verify the entire payload matches
            assert replayed_event.payload == original_event.payload

    @pytest.mark.asyncio
    async def test_concurrent_store_and_replay(self, event_store):
        """Test concurrent event storage and replay operations."""
        num_events = 30
        
        # Create events
        events = [
            BaseEvent(
                event_type="concurrent.test",
                payload={"sequence": i, "data": f"concurrent_data_{i}"}
            )
            for i in range(num_events)
        ]
        
        # Function to store events concurrently
        async def store_events(event_batch):
            for event in event_batch:
                await event_store.store_event(event)
        
        # Function to replay events concurrently
        async def replay_events():
            return await event_store.replay_events(event_type="concurrent.test")
        
        # Store events in batches while simultaneously replaying
        batch_size = 10
        batches = [events[i:i+batch_size] for i in range(0, num_events, batch_size)]
        
        store_tasks = [store_events(batch) for batch in batches]
        replay_tasks = [replay_events() for _ in range(3)]  # Multiple concurrent replays
        
        # Execute storage and replay concurrently
        results = await asyncio.gather(*store_tasks, *replay_tasks, return_exceptions=True)
        
        # Verify no exceptions occurred
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent operation failed: {result}")
        
        # Final replay to verify all events were stored
        final_replay = await event_store.replay_events(event_type="concurrent.test")
        assert len(final_replay) == num_events
        
        # Verify all sequences are present
        sequences = {event.payload["sequence"] for event in final_replay}
        assert sequences == set(range(num_events))