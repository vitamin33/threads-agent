"""
Test PostgreSQL indexes for Event Bus performance
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone
import time
from typing import List
import uuid
import json

from services.event_bus.store.postgres_store import PostgreSQLEventStore
from services.event_bus.models.base import BaseEvent


class TestPostgreSQLIndexPerformance:
    """Test that indexes improve query performance."""

    @pytest.fixture
    async def event_store(self):
        """Create event store with test database."""
        store = PostgreSQLEventStore(
            "postgresql://postgres:pass@localhost:5433/test_events"
        )

        # Initialize schema with indexes
        await store.initialize_with_pool()
        await store.initialize_schema()

        yield store

        # Cleanup
        if store._pool:
            await store._pool.close()

    @pytest.fixture
    async def bulk_events(self) -> List[BaseEvent]:
        """Generate bulk test events for performance testing."""
        events = []
        event_types = [
            "UserAction",
            "SystemEvent",
            "DataUpdate",
            "Notification",
            "Error",
        ]

        # Generate 10,000 events over 30 days
        base_time = datetime.now(timezone.utc) - timedelta(days=30)

        for i in range(10000):
            time_offset = timedelta(
                days=i // 333,  # Distribute over 30 days
                hours=(i % 24),
                minutes=(i % 60),
            )

            event = BaseEvent(
                event_id=str(uuid.uuid4()),
                timestamp=base_time + time_offset,
                event_type=event_types[i % len(event_types)],
                payload={
                    "user_id": f"user_{i % 100}",
                    "action": f"action_{i % 50}",
                    "value": i,
                    "metadata": {"source": "test", "version": "1.0"},
                },
            )
            events.append(event)

        return events

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, event_store, bulk_events):
        """Test bulk insert performance with indexes."""
        start_time = time.time()

        # Insert events in batches
        batch_size = 100
        for i in range(0, len(bulk_events), batch_size):
            batch = bulk_events[i : i + batch_size]

            # Use connection from pool for batch insert
            async with event_store._pool.acquire() as connection:
                await connection.executemany(
                    """
                    INSERT INTO events (event_id, timestamp, event_type, payload)
                    VALUES ($1, $2, $3, $4)
                    """,
                    [
                        (e.event_id, e.timestamp, e.event_type, json.dumps(e.payload))
                        for e in batch
                    ],
                )

        insert_time = time.time() - start_time

        # Performance assertion - should complete in reasonable time
        assert insert_time < 30.0, (
            f"Bulk insert took {insert_time:.2f}s, expected < 30s"
        )

        # Verify all events were inserted
        async with event_store._pool.acquire() as connection:
            count = await connection.fetchval("SELECT COUNT(*) FROM events")
            assert count == len(bulk_events)

    @pytest.mark.asyncio
    async def test_time_range_query_performance(self, event_store, bulk_events):
        """Test time range query performance with composite index."""
        # First insert test data
        await self._insert_bulk_events(event_store, bulk_events[:1000])

        # Test query for last 7 days (should use idx_events_recent)
        start_time = time.time()

        recent_time = datetime.now(timezone.utc) - timedelta(days=7)
        events = await event_store.replay_events(start_time=recent_time, limit=100)

        query_time = time.time() - start_time

        # Should be very fast with index
        assert query_time < 0.1, (
            f"Recent events query took {query_time:.2f}s, expected < 0.1s"
        )
        assert len(events) <= 100

    @pytest.mark.asyncio
    async def test_event_type_query_performance(self, event_store, bulk_events):
        """Test event type query performance with composite index."""
        # Insert test data
        await self._insert_bulk_events(event_store, bulk_events[:1000])

        # Test query by event type (should use idx_events_event_type_timestamp)
        start_time = time.time()

        events = await event_store.replay_events(event_type="UserAction", limit=50)

        query_time = time.time() - start_time

        # Should be fast with index
        assert query_time < 0.05, (
            f"Event type query took {query_time:.2f}s, expected < 0.05s"
        )
        assert all(e.event_type == "UserAction" for e in events)

    @pytest.mark.asyncio
    async def test_combined_filter_performance(self, event_store, bulk_events):
        """Test combined time range + event type query performance."""
        # Insert test data
        await self._insert_bulk_events(event_store, bulk_events[:1000])

        # Test combined query (should use idx_events_timestamp_event_type)
        start_time = time.time()

        start_date = datetime.now(timezone.utc) - timedelta(days=14)
        end_date = datetime.now(timezone.utc) - timedelta(days=7)

        events = await event_store.replay_events(
            start_time=start_date, end_time=end_date, event_type="SystemEvent", limit=25
        )

        query_time = time.time() - start_time

        # Should be very fast with composite index
        assert query_time < 0.05, (
            f"Combined query took {query_time:.2f}s, expected < 0.05s"
        )
        assert all(e.event_type == "SystemEvent" for e in events)
        assert all(start_date <= e.timestamp <= end_date for e in events)

    @pytest.mark.asyncio
    async def test_analyze_performance_metrics(self, event_store, bulk_events):
        """Test performance analysis functionality."""
        # Insert some test data
        await self._insert_bulk_events(event_store, bulk_events[:500])

        # Run some queries to generate index usage stats
        await event_store.replay_events(limit=10)
        await event_store.replay_events(event_type="Error", limit=5)
        await event_store.replay_events(
            start_time=datetime.now(timezone.utc) - timedelta(days=3), limit=20
        )

        # Analyze performance
        metrics = await event_store.analyze_performance()

        assert "table_metrics" in metrics
        assert "index_usage" in metrics
        assert "unused_indexes" in metrics

        # Verify table metrics
        assert metrics["table_metrics"]["row_count"] == 500

        # Verify we have index usage stats
        assert len(metrics["index_usage"]) > 0

        # Check that our composite indexes are being used
        index_names = [idx["indexname"] for idx in metrics["index_usage"]]
        assert any("timestamp_event_type" in name for name in index_names)

    async def _insert_bulk_events(self, event_store, events: List[BaseEvent]):
        """Helper to insert events in bulk."""
        async with event_store._pool.acquire() as connection:
            await connection.executemany(
                """
                INSERT INTO events (event_id, timestamp, event_type, payload)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (event_id) DO NOTHING
                """,
                [
                    (e.event_id, e.timestamp, e.event_type, json.dumps(e.payload))
                    for e in events
                ],
            )


if __name__ == "__main__":
    # Run performance tests
    asyncio.run(pytest.main([__file__, "-v"]))
