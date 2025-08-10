"""
Batch Message Publisher

Implements message batching for improved throughput and reduced network overhead.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import aio_pika
from aio_pika import Message, DeliveryMode

from ..models.base import BaseEvent

logger = logging.getLogger(__name__)


class BatchPublisher:
    """
    Publishes messages in batches to improve throughput.

    Features:
    - Automatic batching based on size and time thresholds
    - Configurable batch size and flush interval
    - Async processing with proper error handling
    - Metrics tracking for batch performance
    """

    def __init__(
        self,
        connection: aio_pika.Connection,
        exchange_name: str = "events",
        batch_size: int = 100,
        flush_interval: float = 1.0,  # seconds
        max_batch_bytes: int = 1024 * 1024,  # 1MB
    ):
        """
        Initialize batch publisher.

        Args:
            connection: RabbitMQ connection
            exchange_name: Name of the exchange
            batch_size: Maximum number of messages per batch
            flush_interval: Maximum time to hold messages before flushing
            max_batch_bytes: Maximum batch size in bytes
        """
        self.connection = connection
        self.exchange_name = exchange_name
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_batch_bytes = max_batch_bytes

        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

        self._batch: List[tuple[BaseEvent, str]] = []  # (event, routing_key)
        self._batch_size_bytes = 0
        self._flush_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # Metrics
        self.total_messages_sent = 0
        self.total_batches_sent = 0
        self.total_bytes_sent = 0
        self.failed_batches = 0

    async def initialize(self) -> None:
        """Initialize channel and exchange."""
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.batch_size)

        self.exchange = await self.channel.declare_exchange(
            self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )

        # Start flush timer
        self._start_flush_timer()

        logger.info(
            f"Batch publisher initialized with batch_size={self.batch_size}, "
            f"flush_interval={self.flush_interval}s"
        )

    async def publish(self, event: BaseEvent, routing_key: str = "") -> None:
        """
        Add event to batch for publishing.

        Args:
            event: Event to publish
            routing_key: Routing key for the message
        """
        event_json = event.model_dump_json()
        event_size = len(event_json.encode("utf-8"))

        async with self._lock:
            # Check if adding this event would exceed limits
            if (
                len(self._batch) >= self.batch_size
                or self._batch_size_bytes + event_size > self.max_batch_bytes
            ):
                await self._flush_batch()

            self._batch.append((event, routing_key))
            self._batch_size_bytes += event_size

            # Reset flush timer
            self._restart_flush_timer()

    async def _flush_batch(self) -> None:
        """Flush current batch to RabbitMQ."""
        if not self._batch:
            return

        batch_to_send = self._batch.copy()
        batch_size = len(batch_to_send)
        batch_bytes = self._batch_size_bytes

        # Clear current batch
        self._batch.clear()
        self._batch_size_bytes = 0

        try:
            # Prepare all messages
            messages = []
            for event, routing_key in batch_to_send:
                message = Message(
                    body=event.model_dump_json().encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                    content_type="application/json",
                    headers={
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "batch_id": f"batch_{datetime.utcnow().timestamp()}",
                    },
                )
                messages.append((message, routing_key))

            # Publish all messages in the batch
            for message, routing_key in messages:
                await self.exchange.publish(
                    message, routing_key=routing_key or event.event_type
                )

            # Update metrics
            self.total_messages_sent += batch_size
            self.total_batches_sent += 1
            self.total_bytes_sent += batch_bytes

            logger.info(f"Flushed batch of {batch_size} messages ({batch_bytes} bytes)")

        except Exception as e:
            logger.error(f"Failed to flush batch: {e}")
            self.failed_batches += 1

            # Re-add failed messages to batch for retry
            async with self._lock:
                self._batch.extend(batch_to_send)
                self._batch_size_bytes += batch_bytes

    def _start_flush_timer(self) -> None:
        """Start the flush timer task."""
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._flush_timer())

    def _restart_flush_timer(self) -> None:
        """Cancel and restart the flush timer."""
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
        self._start_flush_timer()

    async def _flush_timer(self) -> None:
        """Timer task that flushes batch after interval."""
        try:
            await asyncio.sleep(self.flush_interval)
            async with self._lock:
                await self._flush_batch()
        except asyncio.CancelledError:
            # Timer was cancelled, this is normal
            pass

    async def flush(self) -> None:
        """Manually flush any pending messages."""
        async with self._lock:
            await self._flush_batch()

    async def close(self) -> None:
        """Close publisher and flush remaining messages."""
        # Cancel flush timer
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush any remaining messages
        await self.flush()

        # Close channel
        if self.channel and not self.channel.is_closed:
            await self.channel.close()

        logger.info(
            f"Batch publisher closed. Stats: "
            f"messages={self.total_messages_sent}, "
            f"batches={self.total_batches_sent}, "
            f"bytes={self.total_bytes_sent}, "
            f"failed={self.failed_batches}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get publisher metrics."""
        avg_batch_size = (
            self.total_messages_sent / self.total_batches_sent
            if self.total_batches_sent > 0
            else 0
        )

        return {
            "total_messages": self.total_messages_sent,
            "total_batches": self.total_batches_sent,
            "total_bytes": self.total_bytes_sent,
            "failed_batches": self.failed_batches,
            "average_batch_size": avg_batch_size,
            "current_batch_size": len(self._batch),
            "current_batch_bytes": self._batch_size_bytes,
        }
