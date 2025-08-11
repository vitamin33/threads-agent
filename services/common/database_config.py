"""
Centralized database configuration for all services.

This module provides a single source of truth for database configuration,
preventing inconsistencies across services.
"""

import os
from urllib.parse import urlparse


class DatabaseConfig:
    """Centralized database configuration."""

    # Default values that match our Helm chart defaults
    DEFAULT_USERNAME = "postgres"
    DEFAULT_PASSWORD = "pass"
    DEFAULT_DATABASE = "threads_agent"
    DEFAULT_HOST = "postgres"
    DEFAULT_PORT = 5432

    def __init__(self):
        """Initialize database configuration from environment."""
        # Try to get DATABASE_URL first (standard format)
        self.database_url = os.getenv("DATABASE_URL")

        # Try POSTGRES_DSN as fallback (SQLAlchemy format)
        self.postgres_dsn = os.getenv("POSTGRES_DSN")

        # Parse configuration
        if self.database_url:
            self._parse_database_url(self.database_url)
        elif self.postgres_dsn:
            self._parse_postgres_dsn(self.postgres_dsn)
        else:
            # Use defaults
            self.username = self.DEFAULT_USERNAME
            self.password = self.DEFAULT_PASSWORD
            self.database = self.DEFAULT_DATABASE
            self.host = self.DEFAULT_HOST
            self.port = self.DEFAULT_PORT

    def _parse_database_url(self, url: str):
        """Parse standard DATABASE_URL format."""
        parsed = urlparse(url)
        self.username = parsed.username or self.DEFAULT_USERNAME
        self.password = parsed.password or self.DEFAULT_PASSWORD
        self.database = (
            parsed.path.lstrip("/") if parsed.path else self.DEFAULT_DATABASE
        )
        self.host = parsed.hostname or self.DEFAULT_HOST
        self.port = parsed.port or self.DEFAULT_PORT

    def _parse_postgres_dsn(self, dsn: str):
        """Parse SQLAlchemy POSTGRES_DSN format."""
        # Handle postgresql+psycopg2:// format
        if dsn.startswith("postgresql+"):
            dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
            dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")
        self._parse_database_url(dsn)

    def get_database_url(self) -> str:
        """Get standard DATABASE_URL format."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_postgres_dsn(self, driver: str = "psycopg2") -> str:
        """Get SQLAlchemy DSN format."""
        return f"postgresql+{driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_async_dsn(self) -> str:
        """Get async SQLAlchemy DSN format."""
        return self.get_postgres_dsn(driver="asyncpg")

    @property
    def is_available(self) -> bool:
        """Check if database configuration is available."""
        return bool(self.database_url or self.postgres_dsn)

    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"DatabaseConfig(host={self.host}, port={self.port}, "
            f"database={self.database}, username={self.username})"
        )


# Global instance for easy import
db_config = DatabaseConfig()


def get_database_url() -> str:
    """Get the database URL for the current environment."""
    return db_config.get_database_url()


def get_postgres_dsn(driver: str = "psycopg2") -> str:
    """Get the PostgreSQL DSN for SQLAlchemy."""
    return db_config.get_postgres_dsn(driver)


def get_async_postgres_dsn() -> str:
    """Get the async PostgreSQL DSN for SQLAlchemy."""
    return db_config.get_async_dsn()
