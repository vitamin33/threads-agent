"""
RabbitMQ Connection Manager

Handles connections, reconnections, and connection pooling for RabbitMQ.
"""

import asyncio
import logging
from typing import Optional
import pika
import aio_pika


logger = logging.getLogger(__name__)


class RabbitMQConnectionManager:
    """
    Manages RabbitMQ connections with retry logic and automatic reconnection.
    """

    def __init__(self, url: str, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the connection manager.

        Args:
            url: RabbitMQ connection URL
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.url = url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._connection: Optional[pika.BlockingConnection] = None
        self._async_connection: Optional[aio_pika.Connection] = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if connected to RabbitMQ."""
        return self._is_connected

    async def connect(self) -> bool:
        """
        Connect to RabbitMQ with retry logic.

        Returns:
            True if connection successful, False otherwise
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Parse URL and create connection parameters
                parameters = pika.URLParameters(self.url)
                self._connection = pika.BlockingConnection(parameters)
                self._is_connected = True
                logger.info(f"Connected to RabbitMQ on attempt {attempt + 1}")
                return True

            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("Failed to connect after maximum retries")
                    self._is_connected = False
                    return False

    async def connect_async(self) -> bool:
        """
        Connect to RabbitMQ using async aio-pika with retry logic.

        Returns:
            True if connection successful, False otherwise
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Use aio-pika for async connections
                self._async_connection = await aio_pika.connect_robust(self.url)
                self._is_connected = True
                logger.info(f"Connected to RabbitMQ (async) on attempt {attempt + 1}")
                return True

            except Exception as e:
                logger.warning(f"Async connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("Failed to connect async after maximum retries")
                    self._is_connected = False
                    return False

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self._connection:
            try:
                # Try to check if connection is closed, if not close it
                if not getattr(self._connection, "is_closed", False):
                    self._connection.close()
            except AttributeError:
                # For mock objects or objects without is_closed attribute
                self._connection.close()
        self._connection = None
        self._is_connected = False
        logger.info("Disconnected from RabbitMQ")

    async def get_channel(self):
        """
        Get a channel from the connection.

        Returns:
            pika.channel.Channel: RabbitMQ channel

        Raises:
            RuntimeError: If not connected to RabbitMQ
        """
        if not self._is_connected or not self._connection:
            raise RuntimeError("Not connected to RabbitMQ")

        return self._connection.channel()

    async def get_async_channel(self):
        """
        Get an async channel from the aio-pika connection.

        Returns:
            aio_pika.Channel: Async RabbitMQ channel

        Raises:
            RuntimeError: If not connected to RabbitMQ via async connection
        """
        if not self._async_connection:
            raise RuntimeError("Not connected to RabbitMQ via async connection")

        return await self._async_connection.channel()
