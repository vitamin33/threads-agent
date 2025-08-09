"""
Event-Driven Architecture Foundation

A complete event bus implementation for the threads-agent microservices.

Components:
- BaseEvent: Core event model with required fields
- RabbitMQConnectionManager: Connection management with retry logic
- EventPublisher: Async event publishing with retry
- EventSubscriber: Multi-handler event subscription
- PostgreSQLEventStore: Event persistence and replay

Usage Example:

    from services.event_bus import (
        BaseEvent,
        RabbitMQConnectionManager,
        EventPublisher,
        EventSubscriber,
        PostgreSQLEventStore
    )

    # Create connection manager
    conn_mgr = RabbitMQConnectionManager("amqp://localhost")
    await conn_mgr.connect()

    # Publish events
    publisher = EventPublisher(conn_mgr)
    event = BaseEvent(event_type="user_created", payload={"user_id": "123"})
    await publisher.publish(event, "user_events", "user.created")

    # Subscribe to events
    subscriber = EventSubscriber(conn_mgr)

    async def handle_user_created(event):
        print(f"User created: {event.payload}")

    subscriber.register_handler("user_created", handle_user_created)
    await subscriber.start_consuming("user_queue")

    # Store and replay events
    event_store = PostgreSQLEventStore("postgresql://localhost/events")
    await event_store.initialize_schema()
    await event_store.store_event(event)

    # Replay events by type
    events = await event_store.replay_events(event_type="user_created")
"""

from .models import BaseEvent
from .connection import RabbitMQConnectionManager
from .publishers import EventPublisher
from .subscribers import EventSubscriber
from .store import PostgreSQLEventStore

__version__ = "1.0.0"

__all__ = [
    "BaseEvent",
    "RabbitMQConnectionManager",
    "EventPublisher",
    "EventSubscriber",
    "PostgreSQLEventStore",
]
