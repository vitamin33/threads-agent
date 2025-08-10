"""
PostgreSQL Event Store

Event persistence and replay functionality using PostgreSQL.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncpg
from ..models.base import BaseEvent


logger = logging.getLogger(__name__)


class PostgreSQLEventStore:
    """
    PostgreSQL-based event store for event persistence and replay.

    Provides event storage, retrieval, and replay capabilities with filtering.
    """

    def __init__(self, database_url: str):
        """
        Initialize the PostgreSQL event store.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self._pool = None

    async def initialize_with_pool(
        self, min_size: int = 5, max_size: int = 20, command_timeout: int = 30
    ) -> None:
        """
        Initialize the event store with connection pooling.

        Args:
            min_size: Minimum number of connections in pool
            max_size: Maximum number of connections in pool
            command_timeout: Command timeout in seconds
        """
        self._pool = await asyncpg.create_pool(
            self.database_url,
            min_size=min_size,
            max_size=max_size,
            command_timeout=command_timeout,
        )

    async def initialize_schema(self) -> None:
        """
        Initialize the database schema for event storage.

        Creates the events table if it doesn't exist.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS events (
            event_id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            event_type VARCHAR NOT NULL,
            payload JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Single column indexes
        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
        
        -- Composite indexes for common query patterns
        CREATE INDEX IF NOT EXISTS idx_events_timestamp_event_type 
            ON events(timestamp, event_type);
        CREATE INDEX IF NOT EXISTS idx_events_event_type_timestamp
            ON events(event_type, timestamp);
        
        -- Index for recent events queries (ordered by timestamp)
        CREATE INDEX IF NOT EXISTS idx_events_recent
            ON events(timestamp DESC);
        
        -- GIN index for JSONB payload queries
        CREATE INDEX IF NOT EXISTS idx_events_payload_gin
            ON events USING gin(payload);
        """

        try:
            connection = await asyncpg.connect(self.database_url)
            try:
                await connection.execute(create_table_sql)
                logger.info("Event store schema initialized successfully")
            finally:
                await connection.close()
        except Exception as e:
            logger.error(f"Failed to initialize event store schema: {e}")
            raise

    async def store_event(self, event: BaseEvent) -> bool:
        """
        Store an event in PostgreSQL.

        Args:
            event: Event to store

        Returns:
            True if storage successful, False otherwise
        """
        insert_sql = """
        INSERT INTO events (event_id, timestamp, event_type, payload)
        VALUES ($1, $2, $3, $4)
        """

        try:
            if self._pool is not None:
                # Use connection pool for better performance
                async with self._pool.acquire() as connection:
                    await connection.execute(
                        insert_sql,
                        event.event_id,
                        event.timestamp,
                        event.event_type,
                        json.dumps(event.payload),
                    )
            else:
                # Fallback to individual connection for backwards compatibility
                connection = await asyncpg.connect(self.database_url)
                try:
                    await connection.execute(
                        insert_sql,
                        event.event_id,
                        event.timestamp,
                        event.event_type,
                        json.dumps(event.payload),
                    )
                finally:
                    await connection.close()

            logger.info(f"Stored event {event.event_id} of type {event.event_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to store event {event.event_id}: {e}")
            return False

    async def get_event_by_id(self, event_id: str) -> Optional[BaseEvent]:
        """
        Retrieve an event by its ID.

        Args:
            event_id: ID of the event to retrieve

        Returns:
            BaseEvent if found, None otherwise
        """
        select_sql = "SELECT * FROM events WHERE event_id = $1"

        try:
            connection = await asyncpg.connect(self.database_url)
            try:
                row = await connection.fetchone(select_sql, event_id)

                if row:
                    return BaseEvent(
                        event_id=row["event_id"],
                        timestamp=row["timestamp"],
                        event_type=row["event_type"],
                        payload=json.loads(row["payload"]),
                    )
                return None
            finally:
                await connection.close()

        except Exception as e:
            logger.error(f"Failed to retrieve event {event_id}: {e}")
            return None

    async def replay_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[BaseEvent]:
        """
        Replay events with optional filtering.

        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of events matching the criteria
        """
        # Build dynamic query based on filters
        query_parts = ["SELECT * FROM events"]
        conditions = []
        params = []
        param_counter = 1

        if start_time and end_time:
            conditions.append(
                f"timestamp BETWEEN ${param_counter} AND ${param_counter + 1}"
            )
            params.extend([start_time, end_time])
            param_counter += 2
        elif start_time:
            conditions.append(f"timestamp >= ${param_counter}")
            params.append(start_time)
            param_counter += 1
        elif end_time:
            conditions.append(f"timestamp <= ${param_counter}")
            params.append(end_time)
            param_counter += 1

        if event_type:
            conditions.append(f"event_type = ${param_counter}")
            params.append(event_type)
            param_counter += 1

        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))

        query_parts.append("ORDER BY timestamp ASC")

        if limit:
            query_parts.append(f"LIMIT ${param_counter}")
            params.append(limit)

        query = " ".join(query_parts)

        try:
            connection = await asyncpg.connect(self.database_url)
            try:
                rows = await connection.fetch(query, *params)

                events = []
                for row in rows:
                    event = BaseEvent(
                        event_id=row["event_id"],
                        timestamp=row["timestamp"],
                        event_type=row["event_type"],
                        payload=json.loads(row["payload"]),
                    )
                    events.append(event)

                logger.info(f"Replayed {len(events)} events")
                return events
            finally:
                await connection.close()

        except Exception as e:
            logger.error(f"Failed to replay events: {e}")
            return []

    async def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze index usage and query performance.

        Returns:
            Dictionary with performance metrics
        """
        try:
            connection = await asyncpg.connect(self.database_url)
            try:
                # Get table size
                size_query = """
                SELECT 
                    pg_size_pretty(pg_total_relation_size('events')) as total_size,
                    pg_size_pretty(pg_relation_size('events')) as table_size,
                    pg_size_pretty(pg_indexes_size('events')) as indexes_size,
                    count(*) as row_count
                FROM events
                """
                size_result = await connection.fetchone(size_query)

                # Get index usage statistics
                index_usage_query = """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                WHERE tablename = 'events'
                ORDER BY idx_scan DESC
                """
                index_stats = await connection.fetch(index_usage_query)

                # Get unused indexes
                unused_indexes_query = """
                SELECT 
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                WHERE tablename = 'events' AND idx_scan = 0
                """
                unused_indexes = await connection.fetch(unused_indexes_query)

                return {
                    "table_metrics": {
                        "total_size": size_result["total_size"],
                        "table_size": size_result["table_size"],
                        "indexes_size": size_result["indexes_size"],
                        "row_count": size_result["row_count"],
                    },
                    "index_usage": [dict(row) for row in index_stats],
                    "unused_indexes": [dict(row) for row in unused_indexes],
                }

            finally:
                await connection.close()

        except Exception as e:
            logger.error(f"Failed to analyze performance: {e}")
            return {}
