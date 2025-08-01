"""Database connection utilities for viral metrics service."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_db_connection():
    """Get database connection for viral metrics."""
    # Use the same pattern as orchestrator
    pg_dsn = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:pass@postgres:5432/threads_agent",
    )
    engine = create_engine(pg_dsn, pool_pre_ping=True, pool_size=5)
    Session = sessionmaker(engine, expire_on_commit=False)
    return Session()
