-- Performance indexes for Event Bus PostgreSQL store
-- Based on query patterns in replay_events method

-- Composite index for time range + event type queries
-- This covers: WHERE timestamp BETWEEN ? AND ? AND event_type = ?
CREATE INDEX IF NOT EXISTS idx_events_timestamp_event_type 
ON events(timestamp, event_type);

-- Composite index for event type + timestamp queries  
-- This covers: WHERE event_type = ? ORDER BY timestamp
CREATE INDEX IF NOT EXISTS idx_events_event_type_timestamp
ON events(event_type, timestamp);

-- Covering index for full event retrieval by ID
-- Includes all columns to avoid table lookups
CREATE INDEX IF NOT EXISTS idx_events_event_id_covering
ON events(event_id) 
INCLUDE (timestamp, event_type, payload, created_at);

-- Partial index for recent events (last 7 days)
-- Optimizes queries for recent data which are most common
CREATE INDEX IF NOT EXISTS idx_events_recent
ON events(timestamp DESC)
WHERE timestamp > (CURRENT_TIMESTAMP - INTERVAL '7 days');

-- Index for payload JSONB queries (if needed in future)
-- Example: searching for specific event properties
CREATE INDEX IF NOT EXISTS idx_events_payload_gin
ON events USING gin(payload);

-- Analyze table to update statistics after index creation
ANALYZE events;