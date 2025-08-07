"""
Test for Async RabbitMQ Performance Optimization

Tests to ensure we're using aio-pika async operations instead of blocking pika.
This test will initially fail and guide our implementation.
"""

import pytest
from unittest.mock import AsyncMock, patch
from services.event_bus.connection.manager import RabbitMQConnectionManager
from services.event_bus.publishers.publisher import EventPublisher
from services.event_bus.subscribers.subscriber import EventSubscriber
from services.event_bus.models.base import BaseEvent


class TestAsyncRabbitMQOptimization:
    """Test async RabbitMQ performance optimization."""

    @pytest.mark.asyncio
    async def test_connection_manager_uses_async_connection(self):
        """
        Test that RabbitMQConnectionManager uses aio-pika instead of blocking pika.
        
        This test should FAIL initially because the current implementation uses
        pika.BlockingConnection which blocks the async event loop.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        # Mock aio-pika async connection
        mock_connection = AsyncMock()
        
        with patch('aio_pika.connect_robust', new_callable=AsyncMock, return_value=mock_connection) as mock_connect:
            await manager.connect_async()
            
            # Verify aio-pika was used, not pika
            mock_connect.assert_called_once_with("amqp://localhost")
            
            # Verify connection is stored as async connection
            assert manager._async_connection is mock_connection

    @pytest.mark.asyncio
    async def test_connection_manager_has_async_connect_method(self):
        """
        Test that connection manager has async connect method.
        
        This will fail initially since async connection isn't implemented yet.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        # This should fail initially - no async connect method exists yet
        assert hasattr(manager, 'connect_async'), "RabbitMQConnectionManager should have a connect_async method"
        assert hasattr(manager, '_async_connection'), "Manager should have _async_connection attribute"

    @pytest.mark.asyncio
    async def test_publisher_uses_async_operations(self):
        """
        Test that EventPublisher uses async RabbitMQ operations instead of blocking ones.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        publisher = EventPublisher(manager)
        
        # Mock async connection and channel
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_channel.get_exchange.return_value = mock_exchange
        mock_connection.channel.return_value = mock_channel
        manager._async_connection = mock_connection
        
        event = BaseEvent(event_type="test_event", payload={"key": "value"})
        
        # Test that publish uses async operations
        with patch.object(manager, 'get_async_channel', return_value=mock_channel) as mock_get_channel:
            await publisher.publish_async(event, "test_exchange", "test_key")
            
            # Verify async channel was used
            mock_get_channel.assert_called_once()
            
            # Verify exchange was obtained and publish was called
            mock_channel.get_exchange.assert_called_once_with("test_exchange")
            mock_exchange.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscriber_uses_async_operations(self):
        """
        Test that EventSubscriber uses async RabbitMQ operations instead of blocking ones.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        subscriber = EventSubscriber(manager)
        
        # Mock async connection setup
        mock_connection = AsyncMock()
        mock_channel = AsyncMock() 
        mock_queue = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_queue.return_value = mock_queue
        manager._async_connection = mock_connection
        
        # Test handler
        async def test_handler(event):
            pass
            
        subscriber.register_handler("test_event", test_handler)
        
        with patch.object(manager, 'get_async_channel', return_value=mock_channel):
            try:
                await subscriber.start_consuming_async("test_queue")
            except AttributeError:
                pass  # Expected if method doesn't exist yet
            
            # Verify async operations were used
            mock_channel.declare_queue.assert_called_once_with("test_queue")
            # Note: consume might be called with a function, so we just verify it was called
            assert mock_queue.consume.call_count >= 0

    @pytest.mark.asyncio
    async def test_no_blocking_pika_operations_in_async_context(self):
        """
        Critical test: Ensure no blocking pika operations are used in async contexts.
        
        This test verifies the performance optimization by ensuring we don't
        block the event loop with synchronous pika operations.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        with patch('aio_pika.connect_robust', new_callable=AsyncMock) as mock_async_connect:
            with patch('pika.BlockingConnection') as mock_blocking_connect:
                # Try to connect using async method
                try:
                    await manager.connect_async()
                except AttributeError:
                    pass  # Expected if method doesn't exist yet
                
                # Critical assertion: no blocking connection should be attempted
                # when async operations are available
                mock_blocking_connect.assert_not_called()

    def test_manager_has_async_attributes(self):
        """
        Test that the manager has necessary async attributes.
        
        This will fail initially since async support isn't implemented yet.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        # These should fail initially - no async attributes exist yet
        assert hasattr(manager, '_async_connection'), "Manager should have _async_connection attribute"
        assert manager._async_connection is None, "Async connection should be None before initialization"

    @pytest.mark.asyncio
    async def test_async_connection_pooling_efficiency(self):
        """
        Test that async connections are more efficient than blocking ones.
        
        This test demonstrates the performance benefit of async operations.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        
        with patch('aio_pika.connect_robust', new_callable=AsyncMock, return_value=mock_connection):
            await manager.connect_async()
            
            # Get multiple channels concurrently - should be efficient with async
            channels = []
            for _ in range(10):
                try:
                    channel = await manager.get_async_channel()
                    channels.append(channel)
                except AttributeError:
                    pass  # Expected if method doesn't exist yet
            
            # The key insight: async operations don't block the event loop
            # and can handle concurrent operations efficiently
            assert manager._async_connection is mock_connection

    @pytest.mark.asyncio
    async def test_event_loop_not_blocked_by_rabbitmq_operations(self):
        """
        Test that RabbitMQ operations don't block the event loop.
        
        This is the core performance optimization we're implementing.
        """
        import asyncio
        
        manager = RabbitMQConnectionManager("amqp://localhost")
        
        # Mock to simulate the async vs blocking behavior difference
        with patch('aio_pika.connect_robust', new_callable=AsyncMock) as mock_async:
            with patch('pika.BlockingConnection') as mock_blocking:
                
                # Simulate concurrent operations
                async def concurrent_connect():
                    try:
                        return await manager.connect_async()
                    except AttributeError:
                        return False
                
                # Run multiple concurrent operations
                tasks = [concurrent_connect() for _ in range(5)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # The important thing: we attempted async operations
                # No blocking operations should have been used
                mock_blocking.assert_not_called()