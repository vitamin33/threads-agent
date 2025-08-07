"""
Test for RabbitMQ Connection Manager

Tests the RabbitMQ connection management functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from services.event_bus.connection.manager import RabbitMQConnectionManager


class TestRabbitMQConnectionManager:
    """Test RabbitMQ connection manager functionality."""

    def test_connection_manager_initialization(self):
        """Test that RabbitMQConnectionManager can be initialized."""
        # This should fail initially - RabbitMQConnectionManager doesn't exist yet
        manager = RabbitMQConnectionManager(
            url="amqp://guest:guest@localhost:5672/"
        )
        
        assert manager.url == "amqp://guest:guest@localhost:5672/"
        assert manager.max_retries == 3  # Default value
        assert manager.retry_delay == 1.0  # Default value

    def test_connection_manager_custom_retry_settings(self):
        """Test connection manager with custom retry settings."""
        manager = RabbitMQConnectionManager(
            url="amqp://localhost",
            max_retries=5,
            retry_delay=2.0
        )
        
        assert manager.max_retries == 5
        assert manager.retry_delay == 2.0

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection to RabbitMQ."""
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        # Mock successful connection
        with patch('pika.BlockingConnection') as mock_connection:
            mock_conn = Mock()
            mock_connection.return_value = mock_conn
            
            result = await manager.connect()
            
            assert result is True
            assert manager.is_connected is True
            mock_connection.assert_called_once()

    @pytest.mark.asyncio 
    async def test_connect_with_retry_on_failure(self):
        """Test connection retry logic on failure."""
        manager = RabbitMQConnectionManager("amqp://localhost", max_retries=2)
        
        with patch('pika.BlockingConnection') as mock_connection:
            # First call fails, second succeeds
            mock_connection.side_effect = [
                ConnectionError("Connection failed"),
                Mock()  # Successful connection
            ]
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await manager.connect()
            
            assert result is True
            assert manager.is_connected is True
            assert mock_connection.call_count == 2

    @pytest.mark.asyncio
    async def test_connect_fails_after_max_retries(self):
        """Test connection fails after exceeding max retries."""
        manager = RabbitMQConnectionManager("amqp://localhost", max_retries=2)
        
        with patch('pika.BlockingConnection') as mock_connection:
            mock_connection.side_effect = ConnectionError("Connection failed")
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await manager.connect()
            
            assert result is False
            assert manager.is_connected is False
            assert mock_connection.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from RabbitMQ."""
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        # Set up a mock connection with is_closed=False
        mock_connection = Mock()
        mock_connection.is_closed = False  # Simulate open connection
        manager._connection = mock_connection
        manager._is_connected = True
        
        await manager.disconnect()
        
        assert manager.is_connected is False
        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channel(self):
        """Test getting a channel from the connection."""
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        manager._connection = mock_connection
        manager._is_connected = True
        
        channel = await manager.get_channel()
        
        assert channel == mock_channel
        mock_connection.channel.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channel_when_not_connected_raises_exception(self):
        """Test that getting channel when not connected raises exception."""
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        with pytest.raises(RuntimeError, match="Not connected to RabbitMQ"):
            await manager.get_channel()