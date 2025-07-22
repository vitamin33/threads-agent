#!/bin/bash
echo "Testing Redis MCP..."

# Test basic operations
echo "SET test:key 'Hello MCP'"
echo "GET test:key"
echo "INCR test:counter"
echo "ZADD trending:topics 95 'AI productivity'"

echo "Test complete. Check Redis for stored values."
