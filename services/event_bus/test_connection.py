#!/usr/bin/env python
"""
Test database connection.
"""

import asyncio
import asyncpg
import os


async def test_connection():
    """Test database connection."""
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/events"
    )
    print(f"Testing connection to: {database_url}")

    try:
        connection = await asyncpg.connect(database_url)
        print("Connection successful!")

        # Test query
        result = await connection.fetchval("SELECT version()")
        print(f"PostgreSQL version: {result}")

        await connection.close()
    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
