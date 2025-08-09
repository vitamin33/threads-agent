"""
Test for PostgreSQL Event Store

Tests the event persistence and replay functionality.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from services.event_bus.models.base import BaseEvent
from services.event_bus.store.postgres_store import PostgreSQLEventStore


class TestPostgreSQLEventStore:
    """Test PostgreSQL Event Store functionality."""

    def test_event_store_initialization(self):
        """Test that PostgreSQLEventStore can be initialized."""
        # This should fail initially - PostgreSQLEventStore doesn't exist yet
        database_url = "postgresql://user:pass@localhost/events"
        store = PostgreSQLEventStore(database_url=database_url)

        assert store.database_url == database_url

    @pytest.mark.asyncio
    async def test_store_event(self):
        """Test storing an event to PostgreSQL."""
        database_url = "postgresql://test"
        store = PostgreSQLEventStore(database_url=database_url)

        # Mock database connection and operations
        mock_connection = AsyncMock()

        with patch("asyncpg.connect", return_value=mock_connection):
            event = BaseEvent(
                event_type="user_created",
                payload={"user_id": "123", "email": "test@example.com"},
            )

            result = await store.store_event(event)

            assert result is True
            mock_connection.execute.assert_called_once()

            # Verify the SQL and parameters
            call_args = mock_connection.execute.call_args
            sql = call_args[0][0]
            params = call_args[0][1:]

            assert "INSERT INTO events" in sql
            assert params[0] == event.event_id  # event_id
            assert params[1] == event.timestamp  # timestamp
            assert params[2] == event.event_type  # event_type
            assert event.payload == eval(params[3])  # payload (JSON)

    @pytest.mark.asyncio
    async def test_get_event_by_id(self):
        """Test retrieving an event by event_id."""
        database_url = "postgresql://test"
        store = PostgreSQLEventStore(database_url=database_url)

        # Mock database connection and results
        mock_connection = AsyncMock()

        # Mock database row result
        test_timestamp = datetime.now(timezone.utc)
        mock_row = {
            "event_id": "test-event-id-123",
            "timestamp": test_timestamp,
            "event_type": "user_created",
            "payload": '{"user_id": "123", "email": "test@example.com"}',
        }
        mock_connection.fetchone.return_value = mock_row

        with patch("asyncpg.connect", return_value=mock_connection):
            event = await store.get_event_by_id("test-event-id-123")

            assert event is not None
            assert event.event_id == "test-event-id-123"
            assert event.timestamp == test_timestamp
            assert event.event_type == "user_created"
            assert event.payload == {"user_id": "123", "email": "test@example.com"}

            # Verify the SQL query
            call_args = mock_connection.fetchone.call_args
            sql = call_args[0][0]
            assert "SELECT * FROM events WHERE event_id = $1" in sql

    @pytest.mark.asyncio
    async def test_get_event_by_id_not_found(self):
        """Test retrieving non-existent event by event_id."""
        database_url = "postgresql://test"
        store = PostgreSQLEventStore(database_url=database_url)

        mock_connection = AsyncMock()
        mock_connection.fetchone.return_value = None  # No event found

        with patch("asyncpg.connect", return_value=mock_connection):
            event = await store.get_event_by_id("non-existent-id")

            assert event is None

    @pytest.mark.asyncio
    async def test_replay_events_by_timestamp_range(self):
        """Test replaying events within a timestamp range."""
        database_url = "postgresql://test"
        store = PostgreSQLEventStore(database_url=database_url)

        mock_connection = AsyncMock()

        # Mock multiple events in results
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)

        mock_rows = [
            {
                "event_id": "event-1",
                "timestamp": start_time + timedelta(minutes=10),
                "event_type": "user_created",
                "payload": '{"user_id": "123"}',
            },
            {
                "event_id": "event-2",
                "timestamp": start_time + timedelta(minutes=20),
                "event_type": "user_updated",
                "payload": '{"user_id": "123", "name": "John"}',
            },
            {
                "event_id": "event-3",
                "timestamp": start_time + timedelta(minutes=30),
                "event_type": "user_deleted",
                "payload": '{"user_id": "123"}',
            },
        ]
        mock_connection.fetch.return_value = mock_rows

        with patch("asyncpg.connect", return_value=mock_connection):
            events = await store.replay_events(start_time=start_time, end_time=end_time)

            assert len(events) == 3
            assert events[0].event_id == "event-1"
            assert events[1].event_id == "event-2"
            assert events[2].event_id == "event-3"

            # Verify the SQL query with timestamp range
            call_args = mock_connection.fetch.call_args
            sql = call_args[0][0]
            params = call_args[0][1:]

            assert "SELECT * FROM events" in sql
            assert "WHERE timestamp BETWEEN $1 AND $2" in sql
            assert params[0] == start_time
            assert params[1] == end_time

    @pytest.mark.asyncio
    async def test_replay_events_by_event_type(self):
        """Test replaying events filtered by event type."""
        database_url = "postgresql://test"
        store = PostgreSQLEventStore(database_url=database_url)

        mock_connection = AsyncMock()

        # Mock filtered results
        test_time = datetime.now(timezone.utc)
        mock_rows = [
            {
                "event_id": "event-1",
                "timestamp": test_time,
                "event_type": "user_created",
                "payload": '{"user_id": "123"}',
            },
            {
                "event_id": "event-2",
                "timestamp": test_time,
                "event_type": "user_created",
                "payload": '{"user_id": "456"}',
            },
        ]
        mock_connection.fetch.return_value = mock_rows

        with patch("asyncpg.connect", return_value=mock_connection):
            events = await store.replay_events(event_type="user_created")

            assert len(events) == 2
            assert all(event.event_type == "user_created" for event in events)

            # Verify the SQL query with event type filter
            call_args = mock_connection.fetch.call_args
            sql = call_args[0][0]
            params = call_args[0][1:]

            assert "WHERE event_type = $1" in sql
            assert params[0] == "user_created"

    @pytest.mark.asyncio
    async def test_replay_events_with_limit(self):
        """Test replaying events with limit."""
        database_url = "postgresql://test"
        store = PostgreSQLEventStore(database_url=database_url)

        mock_connection = AsyncMock()

        # Mock limited results
        test_time = datetime.now(timezone.utc)
        mock_rows = [
            {
                "event_id": "event-1",
                "timestamp": test_time,
                "event_type": "user_created",
                "payload": '{"user_id": "123"}',
            },
            {
                "event_id": "event-2",
                "timestamp": test_time,
                "event_type": "user_updated",
                "payload": '{"user_id": "123"}',
            },
        ]
        mock_connection.fetch.return_value = mock_rows

        with patch("asyncpg.connect", return_value=mock_connection):
            events = await store.replay_events(limit=2)

            assert len(events) == 2

            # Verify LIMIT clause in SQL
            call_args = mock_connection.fetch.call_args
            sql = call_args[0][0]
            assert "LIMIT $1" in sql

    @pytest.mark.asyncio
    async def test_store_event_database_error(self):
        """Test handling database errors when storing events."""
        database_url = "postgresql://test"
        store = PostgreSQLEventStore(database_url=database_url)

        with patch(
            "asyncpg.connect", side_effect=Exception("Database connection failed")
        ):
            event = BaseEvent(event_type="test_event", payload={"key": "value"})

            result = await store.store_event(event)

            assert result is False

    @pytest.mark.asyncio
    async def test_initialize_database_schema(self):
        """Test database schema initialization."""
        database_url = "postgresql://test"
        store = PostgreSQLEventStore(database_url=database_url)

        mock_connection = AsyncMock()

        with patch("asyncpg.connect", return_value=mock_connection):
            await store.initialize_schema()

            # Verify table creation SQL was executed
            mock_connection.execute.assert_called_once()
            sql = mock_connection.execute.call_args[0][0]
            assert "CREATE TABLE IF NOT EXISTS events" in sql
            assert "event_id VARCHAR PRIMARY KEY" in sql
            assert "timestamp TIMESTAMP WITH TIME ZONE" in sql
            assert "event_type VARCHAR" in sql
            assert "payload JSONB" in sql
