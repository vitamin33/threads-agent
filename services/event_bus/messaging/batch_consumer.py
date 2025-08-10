"""
Batch Message Consumer

Implements message batching for efficient processing of multiple messages at once.
"""

import asyncio
import logging
from typing import List, Callable, Dict, Any, Optional
from datetime import datetime
import aio_pika
from aio_pika import IncomingMessage

from ..models.base import BaseEvent

logger = logging.getLogger(__name__)


class BatchConsumer:
    """
    Consumes messages in batches for improved processing efficiency.

    Features:
    - Configurable batch size and timeout
    - Automatic acknowledgment management
    - Error handling with retry logic
    - Metrics tracking for batch processing
    """

    def __init__(
        self,
        connection: aio_pika.Connection,
        queue_name: str,
        batch_size: int = 50,
        batch_timeout: float = 2.0,  # seconds
        prefetch_count: Optional[int] = None,
    ):
        """
        Initialize batch consumer.

        Args:
            connection: RabbitMQ connection
            queue_name: Name of the queue to consume from
            batch_size: Maximum number of messages per batch
            batch_timeout: Maximum time to wait for a full batch
            prefetch_count: Channel prefetch count (defaults to 2x batch_size)
        """
        self.connection = connection
        self.queue_name = queue_name
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.prefetch_count = prefetch_count or (batch_size * 2)

        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None

        self._current_batch: List[IncomingMessage] = []
        self._batch_lock = asyncio.Lock()
        self._processing = False
        self._consumer_tag: Optional[str] = None

        # Metrics
        self.total_messages_processed = 0
        self.total_batches_processed = 0
        self.failed_messages = 0
        self.processing_errors = 0

    async def initialize(self) -> None:
        """Initialize channel and queue."""
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.prefetch_count)

        self.queue = await self.channel.declare_queue(
            self.queue_name,
            durable=True,
            arguments={
                "x-message-ttl": 3600000,  # 1 hour TTL
                "x-max-length": 100000,  # Max 100k messages
            },
        )

        logger.info(
            f"Batch consumer initialized for queue '{self.queue_name}' "
            f"with batch_size={self.batch_size}, timeout={self.batch_timeout}s"
        )

    async def consume(
        self,
        handler: Callable[[List[BaseEvent]], asyncio.Future],
        error_handler: Optional[
            Callable[[Exception, List[IncomingMessage]], asyncio.Future]
        ] = None,
    ) -> None:
        """
        Start consuming messages in batches.

        Args:
            handler: Async function to process a batch of events
            error_handler: Optional async function to handle processing errors
        """
        self._processing = True

        # Start batch processor task
        processor_task = asyncio.create_task(
            self._batch_processor(handler, error_handler)
        )

        try:
            # Start consuming messages
            self._consumer_tag = await self.queue.consume(
                self._on_message,
                no_ack=False,  # Manual acknowledgment
            )

            logger.info(f"Started consuming from queue '{self.queue_name}'")

            # Wait for processor to complete (it won't unless stopped)
            await processor_task

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise
        finally:
            if self._consumer_tag:
                await self.queue.cancel(self._consumer_tag)
            self._processing = False

    async def _on_message(self, message: IncomingMessage) -> None:
        """Handle incoming message by adding to batch."""
        async with self._batch_lock:
            self._current_batch.append(message)

            # If batch is full, notify processor immediately
            if len(self._current_batch) >= self.batch_size:
                self._batch_lock.notify_all()

    async def _batch_processor(
        self,
        handler: Callable[[List[BaseEvent]], asyncio.Future],
        error_handler: Optional[
            Callable[[Exception, List[IncomingMessage]], asyncio.Future]
        ],
    ) -> None:
        """Process batches of messages."""
        while self._processing:
            try:
                # Wait for batch to fill or timeout
                async with self._batch_lock:
                    if len(self._current_batch) < self.batch_size:
                        try:
                            await asyncio.wait_for(
                                self._batch_lock.wait(), timeout=self.batch_timeout
                            )
                        except asyncio.TimeoutError:
                            # Timeout reached, process whatever we have
                            pass

                    # Get current batch
                    if not self._current_batch:
                        continue

                    batch = self._current_batch.copy()
                    self._current_batch.clear()

                # Process batch outside of lock
                await self._process_batch(batch, handler, error_handler)

            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

    async def _process_batch(
        self,
        messages: List[IncomingMessage],
        handler: Callable[[List[BaseEvent]], asyncio.Future],
        error_handler: Optional[
            Callable[[Exception, List[IncomingMessage]], asyncio.Future]
        ],
    ) -> None:
        """Process a batch of messages."""
        if not messages:
            return

        batch_start = datetime.utcnow()
        events = []

        try:
            # Parse all messages into events
            for message in messages:
                try:
                    event_data = message.body.decode("utf-8")
                    event = BaseEvent.model_validate_json(event_data)
                    events.append(event)
                except Exception as e:
                    logger.error(f"Failed to parse message: {e}")
                    self.failed_messages += 1
                    # Reject invalid message
                    await message.reject(requeue=False)
                    messages.remove(message)

            if events:
                # Process batch
                await handler(events)

                # Acknowledge all messages in batch
                for message in messages:
                    await message.ack()

                # Update metrics
                self.total_messages_processed += len(events)
                self.total_batches_processed += 1

                processing_time = (datetime.utcnow() - batch_start).total_seconds()
                logger.info(
                    f"Processed batch of {len(events)} messages in {processing_time:.2f}s"
                )

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            self.processing_errors += 1

            if error_handler:
                try:
                    await error_handler(e, messages)
                except Exception as eh_error:
                    logger.error(f"Error handler failed: {eh_error}")

            # Reject all messages in failed batch with requeue
            for message in messages:
                try:
                    await message.reject(requeue=True)
                except Exception as reject_error:
                    logger.error(f"Failed to reject message: {reject_error}")

    async def stop(self) -> None:
        """Stop consuming and process remaining messages."""
        self._processing = False

        # Process any remaining messages in current batch
        async with self._batch_lock:
            if self._current_batch:
                logger.info(
                    f"Processing final batch of {len(self._current_batch)} messages"
                )
                # Note: In production, you'd want to process these properly
                for message in self._current_batch:
                    await message.reject(requeue=True)
                self._current_batch.clear()

        logger.info(
            f"Batch consumer stopped. Stats: "
            f"messages={self.total_messages_processed}, "
            f"batches={self.total_batches_processed}, "
            f"failed={self.failed_messages}, "
            f"errors={self.processing_errors}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get consumer metrics."""
        avg_batch_size = (
            self.total_messages_processed / self.total_batches_processed
            if self.total_batches_processed > 0
            else 0
        )

        return {
            "total_messages": self.total_messages_processed,
            "total_batches": self.total_batches_processed,
            "failed_messages": self.failed_messages,
            "processing_errors": self.processing_errors,
            "average_batch_size": avg_batch_size,
            "current_batch_size": len(self._current_batch),
            "success_rate": (
                (self.total_messages_processed - self.failed_messages)
                / self.total_messages_processed
                * 100
                if self.total_messages_processed > 0
                else 0
            ),
        }
