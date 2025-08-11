"""
Event Subscriber

Async event subscription with multiple handlers support for RabbitMQ.
"""

import asyncio
import json
import logging
from typing import Dict, List, Callable
from collections import defaultdict
from ..models.base import BaseEvent


logger = logging.getLogger(__name__)


class EventSubscriber:
    """
    Async event subscriber supporting multiple handlers per event type.

    Subscribes to RabbitMQ queues and dispatches events to registered handlers.
    """

    def __init__(self, connection_manager):
        """
        Initialize the event subscriber.

        Args:
            connection_manager: RabbitMQ connection manager instance
        """
        self.connection_manager = connection_manager
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._current_loop = None

    def register_handler(self, event_type: str, handler: Callable):
        """
        Register an event handler for a specific event type.

        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")

    async def _process_message(self, channel, method, properties, body: str) -> bool:
        """
        Process incoming message and dispatch to handlers.

        Args:
            channel: RabbitMQ channel
            method: Message method
            properties: Message properties
            body: Message body (JSON string)

        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Parse JSON message body
            try:
                event_data = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message JSON: {e}")
                return False

            # Reconstruct BaseEvent from JSON data
            try:
                event = BaseEvent(**event_data)
            except Exception as e:
                logger.error(f"Failed to reconstruct event: {e}")
                return False

            # Get handlers for this event type
            handlers = self._handlers.get(event.event_type, [])

            if not handlers:
                logger.info(
                    f"No handlers registered for event type: {event.event_type}"
                )
            else:
                # Execute all handlers for this event type
                for handler in handlers:
                    try:
                        await handler(event)
                        logger.debug(
                            f"Handler {handler.__name__} executed successfully for event {event.event_id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Handler {handler.__name__} failed for event {event.event_id}: {e}"
                        )
                        return False  # Don't ack message if handler fails

            # Acknowledge message after successful processing
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return True

        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}")
            return False

    async def handle_message_async(self, event: BaseEvent) -> bool:
        """
        Handle a message asynchronously without creating new event loops.

        This is the optimized version that reuses the existing event loop.

        Args:
            event: The event to handle

        Returns:
            True if handling successful, False otherwise
        """
        try:
            # Get handlers for this event type
            handlers = self._handlers.get(event.event_type, [])

            if not handlers:
                logger.info(
                    f"No handlers registered for event type: {event.event_type}"
                )
            else:
                # Execute all handlers for this event type
                for handler in handlers:
                    try:
                        await handler(event)
                        logger.debug(
                            f"Handler {handler.__name__} executed successfully for event {event.event_id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Handler {handler.__name__} failed for event {event.event_id}: {e}"
                        )
                        return False

            return True

        except Exception as e:
            logger.error(f"Unexpected error handling message: {e}")
            return False

    def _message_callback(self, channel, method, properties, body):
        """
        Callback for RabbitMQ message consumption (sync wrapper).

        This is called by pika and needs to be synchronous, so we create
        an event loop to run the async processing.
        """
        # Create new event loop for async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                self._process_message(channel, method, properties, body)
            )
        finally:
            loop.close()

    async def start_consuming(self, queue_name: str) -> None:
        """
        Start consuming messages from a queue.

        Args:
            queue_name: Name of the queue to consume from
        """
        try:
            channel = await self.connection_manager.get_channel()
            self._setup_consumer(channel, queue_name)
            logger.info(f"Started consuming from queue: {queue_name}")
        except Exception as e:
            logger.error(f"Failed to start consuming from queue {queue_name}: {e}")
            raise

    def _setup_consumer(self, channel, queue_name: str) -> None:
        """
        Setup the consumer for a queue.

        Args:
            channel: RabbitMQ channel
            queue_name: Name of the queue to consume from
        """
        channel.basic_consume(
            queue=queue_name, on_message_callback=self._message_callback
        )

    async def start_consuming_async(self, queue_name: str) -> None:
        """
        Start consuming messages from a queue using async aio-pika.

        Args:
            queue_name: Name of the queue to consume from
        """
        try:
            channel = await self.connection_manager.get_async_channel()
            queue = await channel.declare_queue(queue_name)

            async def async_message_handler(message):
                async with message.process():
                    try:
                        # Parse JSON message body
                        event_data = json.loads(message.body.decode())

                        # Reconstruct BaseEvent from JSON data
                        event = BaseEvent(**event_data)

                        # Handle the message using our optimized async handler
                        success = await self.handle_message_async(event)

                        if not success:
                            # If handler fails, reject the message
                            message.reject()

                    except Exception as e:
                        logger.error(f"Failed to process async message: {e}")
                        message.reject()

            # Start consuming with the async handler
            await queue.consume(async_message_handler)
            logger.info(f"Started async consuming from queue: {queue_name}")

        except Exception as e:
            logger.error(
                f"Failed to start async consuming from queue {queue_name}: {e}"
            )
            raise
