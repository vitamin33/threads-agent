#!/bin/bash
echo "Testing PostgreSQL MCP..."

# Test query
PGPASSWORD=postgres psql -h localhost -U postgres -d threads_agent -c "
SELECT persona_id, COUNT(*) as post_count
FROM posts
GROUP BY persona_id;"

echo "Test complete."
