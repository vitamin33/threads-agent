"""
Event Publisher

Async event publishing with retry logic for RabbitMQ.
"""

import asyncio
import json
import logging
from typing import Optional
import pika
from models.base import BaseEvent


logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Async event publisher with retry logic.
    
    Publishes events to RabbitMQ exchanges with automatic retry on failure.
    """
    
    def __init__(
        self,
        connection_manager,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the event publisher.
        
        Args:
            connection_manager: RabbitMQ connection manager instance
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.connection_manager = connection_manager
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def publish(
        self,
        event: BaseEvent,
        exchange: str,
        routing_key: str,
        persistent: bool = False
    ) -> bool:
        """
        Publish an event to RabbitMQ exchange.
        
        Args:
            event: Event to publish
            exchange: RabbitMQ exchange name
            routing_key: Routing key for the message
            persistent: Whether message should be persistent
            
        Returns:
            True if publishing successful, False otherwise
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Get channel from connection manager
                channel = await self.connection_manager.get_channel()
                
                # Serialize event to JSON with datetime handling
                message_body = event.model_dump_json()
                
                # Set message properties
                properties = pika.BasicProperties()
                if persistent:
                    properties.delivery_mode = 2  # Make message persistent
                
                # Publish the message
                channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=message_body,
                    properties=properties
                )
                
                logger.info(
                    f"Published event {event.event_id} to exchange '{exchange}' "
                    f"with routing key '{routing_key}' on attempt {attempt + 1}"
                )
                return True
                
            except Exception as e:
                logger.warning(
                    f"Publish attempt {attempt + 1} failed for event {event.event_id}: {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(
                        f"Failed to publish event {event.event_id} after {self.max_retries + 1} attempts"
                    )
                    return False