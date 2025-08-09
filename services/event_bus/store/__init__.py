"""
Event Storage

Event persistence layer for the Event-Driven Architecture.
"""

from .postgres_store import PostgreSQLEventStore

__all__ = [
    "PostgreSQLEventStore",
]
