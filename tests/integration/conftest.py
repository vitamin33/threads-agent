"""
Shared fixtures for event bus integration tests.

This module provides fixtures for setting up RabbitMQ and PostgreSQL test instances,
as well as event bus components for comprehensive integration testing.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock

import asyncpg
import pika
import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.rabbitmq import RabbitMqContainer

# Import event bus components
from services.event_bus.connection.manager import RabbitMQConnectionManager
from services.event_bus.models.base import BaseEvent
from services.event_bus.publishers.publisher import EventPublisher
from services.event_bus.store.postgres_store import PostgreSQLEventStore
from services.event_bus.subscribers.subscriber import EventSubscriber

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def rabbitmq_container():
    """Start a RabbitMQ container for integration tests."""
    with RabbitMqContainer("rabbitmq:3.12-management-alpine") as rabbitmq:
        # Wait for RabbitMQ to be ready
        rabbitmq.get_connection_url()
        yield rabbitmq


@pytest.fixture(scope="session") 
def postgres_container():
    """Start a PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def rabbitmq_url(rabbitmq_container) -> str:
    """Get RabbitMQ connection URL."""
    return rabbitmq_container.get_connection_url()


@pytest.fixture(scope="session")
def postgres_url(postgres_container) -> str:
    """Get PostgreSQL connection URL."""
    return postgres_container.get_connection_url()


@pytest_asyncio.fixture
async def connection_manager(rabbitmq_url) -> RabbitMQConnectionManager:
    """Create and initialize RabbitMQ connection manager."""
    manager = RabbitMQConnectionManager(rabbitmq_url, max_retries=3, retry_delay=0.1)
    connected = await manager.connect()
    assert connected, "Failed to connect to RabbitMQ"
    
    yield manager
    
    await manager.disconnect()


@pytest_asyncio.fixture
async def event_store(postgres_url) -> PostgreSQLEventStore:
    """Create and initialize PostgreSQL event store."""
    store = PostgreSQLEventStore(postgres_url)
    await store.initialize_schema()
    
    yield store
    
    # Cleanup: Drop all events after tests
    try:
        connection = await asyncpg.connect(postgres_url)
        await connection.execute("DELETE FROM events")
        await connection.close()
    except Exception as e:
        logger.warning(f"Failed to cleanup events: {e}")


@pytest_asyncio.fixture
async def publisher(connection_manager) -> EventPublisher:
    """Create event publisher with connection manager."""
    return EventPublisher(connection_manager, max_retries=2, retry_delay=0.1)


@pytest_asyncio.fixture
async def subscriber(connection_manager) -> EventSubscriber:
    """Create event subscriber with connection manager."""
    return EventSubscriber(connection_manager)


@pytest_asyncio.fixture
async def test_exchange(connection_manager) -> str:
    """Create a test exchange for integration tests."""
    exchange_name = f"test_exchange_{uuid.uuid4().hex[:8]}"
    
    try:
        channel = await connection_manager.get_channel()
        channel.exchange_declare(exchange=exchange_name, exchange_type='direct', durable=True)
        channel.close()
    except Exception as e:
        logger.error(f"Failed to create test exchange: {e}")
        raise
    
    return exchange_name


@pytest_asyncio.fixture
async def test_queue(connection_manager, test_exchange) -> str:
    """Create a test queue bound to test exchange."""
    queue_name = f"test_queue_{uuid.uuid4().hex[:8]}"
    
    try:
        channel = await connection_manager.get_channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(exchange=test_exchange, queue=queue_name, routing_key="test.event")
        channel.close()
    except Exception as e:
        logger.error(f"Failed to create test queue: {e}")
        raise
    
    return queue_name


@pytest_asyncio.fixture
async def dead_letter_queue(connection_manager) -> str:
    """Create a dead letter queue for error handling tests."""
    dlq_name = f"test_dlq_{uuid.uuid4().hex[:8]}"
    
    try:
        channel = await connection_manager.get_channel()
        channel.queue_declare(queue=dlq_name, durable=True)
        channel.close()
    except Exception as e:
        logger.error(f"Failed to create dead letter queue: {e}")
        raise
    
    return dlq_name


@pytest.fixture
def sample_events() -> List[BaseEvent]:
    """Generate sample events for testing."""
    events = []
    event_types = ["user.created", "user.updated", "order.placed", "payment.processed"]
    
    for i, event_type in enumerate(event_types * 2):  # Create 8 events total
        event = BaseEvent(
            event_id=f"test_event_{i}_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            payload={
                "sequence": i,
                "user_id": f"user_{i % 4}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {"key": f"value_{i}"}
            },
            timestamp=datetime.now(timezone.utc)
        )
        events.append(event)
    
    return events


@pytest.fixture
def event_collector() -> Dict[str, List[BaseEvent]]:
    """Collector to store received events during tests."""
    return {"events": []}


@pytest_asyncio.fixture
async def event_handler_factory(event_collector):
    """Factory for creating event handlers that collect events."""
    def create_handler(handler_name: str = "default", should_fail: bool = False):
        async def handler(event: BaseEvent):
            if should_fail:
                raise ValueError(f"Handler {handler_name} intentionally failed")
            event_collector["events"].append(event)
            logger.info(f"Handler {handler_name} processed event {event.event_id}")
        
        handler.__name__ = handler_name
        return handler
    
    return create_handler


@pytest.fixture
def rabbitmq_management_api(rabbitmq_container):
    """Provide access to RabbitMQ Management API for advanced testing."""
    import requests
    
    # Get management API details
    host = rabbitmq_container.get_container_host_ip()
    port = rabbitmq_container.get_exposed_port(15672)  # Management port
    
    def get_queue_info(queue_name: str) -> Optional[Dict]:
        """Get queue information from management API."""
        try:
            url = f"http://{host}:{port}/api/queues/%2F/{queue_name}"
            response = requests.get(url, auth=('guest', 'guest'), timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.warning(f"Failed to get queue info: {e}")
            return None
    
    def purge_queue(queue_name: str) -> bool:
        """Purge all messages from a queue."""
        try:
            url = f"http://{host}:{port}/api/queues/%2F/{queue_name}/contents"
            response = requests.delete(url, auth=('guest', 'guest'), timeout=5)
            return response.status_code == 204
        except Exception as e:
            logger.warning(f"Failed to purge queue: {e}")
            return False
    
    return {
        "get_queue_info": get_queue_info,
        "purge_queue": purge_queue
    }


@pytest_asyncio.fixture
async def async_timeout():
    """Utility fixture for async operations with timeout."""
    async def wait_with_timeout(coro, timeout: float = 5.0):
        """Wait for coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise AssertionError(f"Operation timed out after {timeout} seconds")
    
    return wait_with_timeout


@pytest.fixture
def message_ordering_verifier():
    """Utility for verifying message ordering in tests."""
    def verify_ordering(received_events: List[BaseEvent], expected_order: List[str]) -> bool:
        """Verify that events were received in expected order."""
        if len(received_events) != len(expected_order):
            return False
        
        for i, event in enumerate(received_events):
            if event.event_id != expected_order[i]:
                logger.error(f"Order mismatch at position {i}: expected {expected_order[i]}, got {event.event_id}")
                return False
        
        return True
    
    return verify_ordering


class EventCapture:
    """Utility class for capturing and analyzing events during tests."""
    
    def __init__(self):
        self.events: List[BaseEvent] = []
        self.errors: List[Exception] = []
        self.handler_calls: Dict[str, int] = {}
    
    def create_handler(self, handler_name: str, should_fail: bool = False):
        """Create an event handler that captures events and tracks calls."""
        async def handler(event: BaseEvent):
            self.handler_calls[handler_name] = self.handler_calls.get(handler_name, 0) + 1
            
            if should_fail:
                error = ValueError(f"Handler {handler_name} failed for event {event.event_id}")
                self.errors.append(error)
                raise error
            
            self.events.append(event)
            logger.info(f"Handler {handler_name} captured event {event.event_id} (call #{self.handler_calls[handler_name]})")
        
        handler.__name__ = handler_name
        return handler
    
    def get_events_by_type(self, event_type: str) -> List[BaseEvent]:
        """Get all captured events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]
    
    def clear(self):
        """Clear all captured data."""
        self.events.clear()
        self.errors.clear()
        self.handler_calls.clear()


@pytest.fixture
def event_capture() -> EventCapture:
    """Fixture providing event capture utility."""
    return EventCapture()


# Mock fixtures for offline testing
@pytest.fixture
def mock_rabbitmq_unavailable():
    """Mock RabbitMQ being unavailable for error handling tests."""
    class UnavailableConnection:
        def __init__(self):
            self.is_closed = False
        
        def channel(self):
            raise pika.exceptions.AMQPConnectionError("RabbitMQ unavailable")
        
        def close(self):
            self.is_closed = True
    
    return UnavailableConnection()


@pytest.fixture  
def mock_postgres_unavailable():
    """Mock PostgreSQL being unavailable for error handling tests."""
    async def mock_connect(*args, **kwargs):
        raise asyncpg.exceptions.ConnectionFailureError("PostgreSQL unavailable")
    
    return mock_connect