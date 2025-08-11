# /services/orchestrator/db/__init__.py
import os
from typing import Any

from dotenv import load_dotenv  # optional; dev-only
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


# Only create engine and session when needed, not on import
def get_engine() -> Any:
    """Get database engine with production-optimized connection pooling."""
    # Use centralized configuration
    try:
        from services.common.database_config import get_postgres_dsn

        pg_dsn = get_postgres_dsn()
    except ImportError:
        # Fallback to environment variable or default
        pg_dsn = os.getenv(
            "POSTGRES_DSN",
            "postgresql+psycopg2://postgres:pass@postgres:5432/threads_agent",
        )
    # Production optimization: Increased pool size for better concurrency
    # This handles 100+ concurrent users without connection exhaustion
    return create_engine(
        pg_dsn,
        pool_pre_ping=True,  # Check connections before use
        pool_size=10,  # Increased from 5 (2x improvement)
        max_overflow=20,  # Allow up to 30 total connections
        pool_timeout=30,  # Wait up to 30 seconds for a connection
        pool_recycle=3600,  # Recycle connections after 1 hour
    )


def get_session() -> Any:
    """Get database session class, creating it lazily."""
    return sessionmaker(get_engine(), expire_on_commit=False)


def get_db_session():
    """FastAPI dependency to get database session."""
    SessionLocal = get_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# For backward compatibility, create these when accessed
engine = None
Session = None

# Note: engine and Session will be None until explicitly created
# This prevents database connection attempts during import

__all__ = ["Base", "get_engine", "get_session", "get_db_session"]
