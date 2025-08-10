"""
Event Bus Service with Batch Processing

Main service implementation with batch publishing and consuming capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import aio_pika

from .connection.manager import RabbitMQConnectionManager
from .store.postgres_store import PostgreSQLEventStore
from .messaging.batch_publisher import BatchPublisher
from .messaging.batch_consumer import BatchConsumer
from .models.base import BaseEvent
from .publishers import EventPublisher
from .subscribers import EventSubscriber

logger = logging.getLogger(__name__)


class EventBusService:
    """
    Main Event Bus service with batch processing support.

    Features:
    - Batch publishing for high throughput
    - Batch consuming for efficient processing
    - Persistent event storage
    - Event replay capabilities
    - Comprehensive metrics
    """

    def __init__(
        self,
        rabbitmq_url: str,
        postgres_url: str,
        batch_size: int = 100,
        batch_timeout: float = 1.0,
        enable_batching: bool = True,
    ):
        """
        Initialize Event Bus service.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            postgres_url: PostgreSQL connection URL
            batch_size: Default batch size for publishers/consumers
            batch_timeout: Default batch timeout in seconds
            enable_batching: Whether to enable batch processing
        """
        self.rabbitmq_url = rabbitmq_url
        self.postgres_url = postgres_url
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.enable_batching = enable_batching

        # Connection managers
        self.rabbitmq_manager = RabbitMQConnectionManager(rabbitmq_url)
        self.event_store = PostgreSQLEventStore(postgres_url)

        # Publishers and consumers
        self.batch_publishers: Dict[str, BatchPublisher] = {}
        self.batch_consumers: Dict[str, BatchConsumer] = {}
        self.standard_publishers: Dict[str, EventPublisher] = {}
        self.subscribers: Dict[str, EventSubscriber] = {}

        # Service state
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """Start the Event Bus service."""
        logger.info("Starting Event Bus service...")

        try:
            # Initialize connections
            await self.rabbitmq_manager.connect_async()
            await self.event_store.initialize_with_pool()
            await self.event_store.initialize_schema()

            # Create default exchanges
            channel = await self.rabbitmq_manager.get_async_channel()

            # Events exchange for all events
            await channel.declare_exchange(
                "events", aio_pika.ExchangeType.TOPIC, durable=True
            )

            # Dead letter exchange for failed messages
            await channel.declare_exchange(
                "events.dlx", aio_pika.ExchangeType.TOPIC, durable=True
            )

            await channel.close()

            self._running = True
            logger.info("Event Bus service started successfully")

        except Exception as e:
            logger.error(f"Failed to start Event Bus service: {e}")
            await self.stop()
            raise

    async def create_batch_publisher(
        self,
        name: str,
        exchange_name: str = "events",
        batch_size: Optional[int] = None,
        flush_interval: Optional[float] = None,
    ) -> BatchPublisher:
        """Create a new batch publisher."""
        if not self._running:
            raise RuntimeError("Event Bus service is not running")

        if name in self.batch_publishers:
            return self.batch_publishers[name]

        publisher = BatchPublisher(
            connection=self.rabbitmq_manager._async_connection,
            exchange_name=exchange_name,
            batch_size=batch_size or self.batch_size,
            flush_interval=flush_interval or self.batch_timeout,
        )

        await publisher.initialize()
        self.batch_publishers[name] = publisher

        logger.info(f"Created batch publisher '{name}'")
        return publisher

    async def create_batch_consumer(
        self,
        name: str,
        queue_name: str,
        handler: callable,
        batch_size: Optional[int] = None,
        batch_timeout: Optional[float] = None,
    ) -> BatchConsumer:
        """Create a new batch consumer."""
        if not self._running:
            raise RuntimeError("Event Bus service is not running")

        if name in self.batch_consumers:
            raise ValueError(f"Consumer '{name}' already exists")

        consumer = BatchConsumer(
            connection=self.rabbitmq_manager._async_connection,
            queue_name=queue_name,
            batch_size=batch_size or self.batch_size,
            batch_timeout=batch_timeout or self.batch_timeout,
        )

        await consumer.initialize()
        self.batch_consumers[name] = consumer

        # Create consumer task
        task = asyncio.create_task(consumer.consume(handler), name=f"consumer_{name}")
        self._tasks.append(task)

        logger.info(f"Created batch consumer '{name}' for queue '{queue_name}'")
        return consumer

    async def publish_event(
        self,
        event: BaseEvent,
        publisher_name: str = "default",
        routing_key: Optional[str] = None,
    ) -> bool:
        """
        Publish an event using batch or standard publisher.

        Args:
            event: Event to publish
            publisher_name: Name of the publisher to use
            routing_key: Optional routing key (defaults to event type)

        Returns:
            True if event was published successfully
        """
        try:
            # Store event first
            stored = await self.event_store.store_event(event)
            if not stored:
                logger.warning(f"Failed to store event {event.event_id}")

            # Publish via batch publisher if enabled
            if self.enable_batching:
                if publisher_name not in self.batch_publishers:
                    await self.create_batch_publisher(publisher_name)

                publisher = self.batch_publishers[publisher_name]
                await publisher.publish(event, routing_key or event.event_type)
            else:
                # Use standard publisher
                if publisher_name not in self.standard_publishers:
                    publisher = EventPublisher(self.rabbitmq_manager)
                    self.standard_publishers[publisher_name] = publisher

                publisher = self.standard_publishers[publisher_name]
                await publisher.publish_event(event, routing_key or event.event_type)

            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False

    async def publish_events_batch(
        self, events: List[BaseEvent], publisher_name: str = "default"
    ) -> int:
        """
        Publish multiple events efficiently.

        Args:
            events: List of events to publish
            publisher_name: Name of the publisher to use

        Returns:
            Number of successfully published events
        """
        success_count = 0

        for event in events:
            if await self.publish_event(event, publisher_name):
                success_count += 1

        # Force flush if using batch publisher
        if self.enable_batching and publisher_name in self.batch_publishers:
            await self.batch_publishers[publisher_name].flush()

        return success_count

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics."""
        metrics = {
            "service": {
                "running": self._running,
                "enable_batching": self.enable_batching,
                "active_tasks": len([t for t in self._tasks if not t.done()]),
            },
            "connections": {
                "rabbitmq": self.rabbitmq_manager.is_connected,
                "postgres": self.event_store._pool is not None,
            },
            "publishers": {},
            "consumers": {},
            "event_store": {},
        }

        # Batch publisher metrics
        for name, publisher in self.batch_publishers.items():
            metrics["publishers"][f"batch_{name}"] = publisher.get_metrics()

        # Batch consumer metrics
        for name, consumer in self.batch_consumers.items():
            metrics["consumers"][f"batch_{name}"] = consumer.get_metrics()

        # Event store metrics
        if self.event_store._pool:
            metrics["event_store"] = await self.event_store.analyze_performance()

        return metrics

    async def stop(self) -> None:
        """Stop the Event Bus service."""
        logger.info("Stopping Event Bus service...")
        self._running = False

        # Cancel all consumer tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close batch publishers
        for publisher in self.batch_publishers.values():
            await publisher.close()

        # Stop batch consumers
        for consumer in self.batch_consumers.values():
            await consumer.stop()

        # Close connections
        await self.rabbitmq_manager.disconnect()
        if self.event_store._pool:
            await self.event_store._pool.close()

        logger.info("Event Bus service stopped")


async def create_event_bus_service(
    rabbitmq_url: str, postgres_url: str, config: Optional[Dict[str, Any]] = None
) -> EventBusService:
    """
    Factory function to create and start Event Bus service.

    Args:
        rabbitmq_url: RabbitMQ connection URL
        postgres_url: PostgreSQL connection URL
        config: Optional configuration overrides

    Returns:
        Started EventBusService instance
    """
    config = config or {}

    service = EventBusService(
        rabbitmq_url=rabbitmq_url,
        postgres_url=postgres_url,
        batch_size=config.get("batch_size", 100),
        batch_timeout=config.get("batch_timeout", 1.0),
        enable_batching=config.get("enable_batching", True),
    )

    await service.start()
    return service
