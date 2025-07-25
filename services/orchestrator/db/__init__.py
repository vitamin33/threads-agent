# /services/orchestrator/db/__init__.py
import os

from dotenv import load_dotenv  # optional; dev-only
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


# Only create engine and session when needed, not on import
def get_engine():
    """Get database engine, creating it lazily."""
    pg_dsn = os.getenv(
        "POSTGRES_DSN",
        "postgresql+psycopg2://postgres:pass@postgres:5432/threads_agent",
    )
    return create_engine(pg_dsn, pool_pre_ping=True, pool_size=5)


def get_session():
    """Get database session class, creating it lazily."""
    return sessionmaker(get_engine(), expire_on_commit=False)


# For backward compatibility, create these when accessed
engine = None
Session = None

# Note: engine and Session will be None until explicitly created
# This prevents database connection attempts during import

__all__ = ["Base", "get_engine", "get_session"]
