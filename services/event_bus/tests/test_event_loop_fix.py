"""
Test for Event Loop Performance Optimization

Tests to ensure we're not creating new event loops for each message processing.
This test will initially fail and guide our implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from services.event_bus.subscribers.subscriber import EventSubscriber
from services.event_bus.connection.manager import RabbitMQConnectionManager
from services.event_bus.models.base import BaseEvent


class TestEventLoopOptimization:
    """Test event loop performance optimization."""

    @pytest.mark.asyncio
    async def test_subscriber_does_not_create_new_event_loops(self):
        """
        Test that EventSubscriber does not create new event loops for each message.
        
        This test should FAIL initially because the current implementation creates
        a new event loop in _message_callback for every message, which is a major
        performance anti-pattern.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        subscriber = EventSubscriber(manager)
        
        # Track event loop creation
        original_new_event_loop = asyncio.new_event_loop
        event_loop_creations = []
        
        def track_event_loop_creation():
            event_loop_creations.append("created")
            return original_new_event_loop()
        
        with patch('asyncio.new_event_loop', side_effect=track_event_loop_creation):
            # Simulate message processing
            test_event_data = {
                "event_id": "test-123",
                "event_type": "test_event", 
                "timestamp": "2024-01-01T00:00:00Z",
                "payload": {"key": "value"}
            }
            
            # Mock channel and method objects
            mock_channel = Mock()
            mock_method = Mock()
            mock_method.delivery_tag = "test-delivery-tag"
            mock_properties = Mock()
            
            # This is the critical test - processing a message should NOT create a new event loop
            subscriber._message_callback(mock_channel, mock_method, mock_properties, '{"event_id": "test-123", "event_type": "test_event", "timestamp": "2024-01-01T00:00:00Z", "payload": {"key": "value"}}')
            
            # ASSERTION THAT SHOULD FAIL: No new event loops should be created
            assert len(event_loop_creations) == 0, "EventSubscriber should not create new event loops for message processing"

    def test_subscriber_message_callback_is_sync_wrapper_for_async(self):
        """
        Test the current problematic implementation to understand the issue.
        
        This test documents the current anti-pattern that we need to fix.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        subscriber = EventSubscriber(manager)
        
        # The current implementation should have this problematic pattern
        # Let's inspect the _message_callback method
        import inspect
        source = inspect.getsource(subscriber._message_callback)
        
        # This will initially pass but shows the problem
        assert "asyncio.new_event_loop()" in source, "Current implementation creates new event loop (this is the performance issue)"
        assert "loop.run_until_complete" in source, "Current implementation uses run_until_complete (blocks the thread)"

    @pytest.mark.asyncio  
    async def test_subscriber_should_use_proper_async_context(self):
        """
        Test that subscriber should use proper async context instead of creating event loops.
        
        This test will guide us toward the correct implementation.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        subscriber = EventSubscriber(manager)
        
        # Register a test handler
        async def test_handler(event):
            return f"handled: {event.event_type}"
            
        subscriber.register_handler("test_event", test_handler)
        
        # The fix should provide a proper async processing method
        assert hasattr(subscriber, '_process_message'), "Subscriber should have async _process_message method"
        
        # Test the async processing directly (without the sync wrapper)
        mock_channel = AsyncMock()
        mock_method = Mock()
        mock_method.delivery_tag = "test-delivery-tag"
        mock_properties = Mock()
        
        test_message = '{"event_id": "test-123", "event_type": "test_event", "timestamp": "2024-01-01T00:00:00Z", "payload": {"key": "value"}}'
        
        # This should work without creating new event loops
        result = await subscriber._process_message(mock_channel, mock_method, mock_properties, test_message)
        
        # The method should return True on success
        assert result is True

    @pytest.mark.asyncio
    async def test_event_loop_reuse_performance(self):
        """
        Test that reusing the existing event loop provides better performance.
        
        This test demonstrates the performance benefit of the fix.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        subscriber = EventSubscriber(manager)
        
        # Register multiple handlers to simulate load
        async def handler1(event):
            await asyncio.sleep(0.001)  # Simulate some async work
            return "handler1"
            
        async def handler2(event):
            await asyncio.sleep(0.001)  # Simulate some async work
            return "handler2"
            
        subscriber.register_handler("test_event", handler1)
        subscriber.register_handler("test_event", handler2)
        
        # Get current event loop (should be reused, not recreated)
        current_loop = asyncio.get_event_loop()
        
        # Process multiple messages concurrently (this should be efficient with proper async)
        messages = [
            '{"event_id": "test-1", "event_type": "test_event", "timestamp": "2024-01-01T00:00:00Z", "payload": {"key": "value1"}}',
            '{"event_id": "test-2", "event_type": "test_event", "timestamp": "2024-01-01T00:00:00Z", "payload": {"key": "value2"}}',
            '{"event_id": "test-3", "event_type": "test_event", "timestamp": "2024-01-01T00:00:00Z", "payload": {"key": "value3"}}'
        ]
        
        # Mock objects
        mock_channel = AsyncMock()
        mock_method = Mock()
        mock_method.delivery_tag = "test-delivery-tag"
        mock_properties = Mock()
        
        # Process all messages - should use the same event loop efficiently
        tasks = []
        for message in messages:
            task = asyncio.create_task(
                subscriber._process_message(mock_channel, mock_method, mock_properties, message)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(result is True for result in results)
        
        # Verify we're still using the same event loop
        assert asyncio.get_event_loop() is current_loop

    def test_current_implementation_blocks_event_loop(self):
        """
        Test that demonstrates how the current implementation blocks the event loop.
        
        This test shows why the current approach is a performance problem.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        subscriber = EventSubscriber(manager)
        
        # The current _message_callback creates a new event loop and runs it until complete
        # This blocks the calling thread and prevents concurrent message processing
        
        # Let's verify the current problematic implementation exists
        import inspect
        source = inspect.getsource(subscriber._message_callback)
        
        # These patterns indicate the performance problem
        assert "asyncio.new_event_loop()" in source, "Creates new event loop (performance issue)"
        assert "asyncio.set_event_loop(loop)" in source, "Sets the loop (affects global state)"  
        assert "loop.run_until_complete" in source, "Blocks the thread (prevents concurrency)"
        assert "loop.close()" in source, "Closes the loop (resource waste)"

    @pytest.mark.asyncio
    async def test_optimized_subscriber_should_handle_concurrent_messages(self):
        """
        Test that the optimized subscriber can handle concurrent messages efficiently.
        
        This test will guide the implementation of the performance fix.
        """
        manager = RabbitMQConnectionManager("amqp://localhost")
        subscriber = EventSubscriber(manager)
        
        # The optimized implementation should have a method to handle messages
        # without creating new event loops
        assert hasattr(subscriber, 'handle_message_async'), "Should have async message handler"
        
        # Test concurrent message handling
        messages_handled = []
        
        async def tracking_handler(event):
            messages_handled.append(event.event_id)
            await asyncio.sleep(0.01)  # Simulate processing time
            
        subscriber.register_handler("test_event", tracking_handler)
        
        # Simulate concurrent messages
        test_messages = [
            BaseEvent(event_type="test_event", payload={"msg": f"message_{i}"})
            for i in range(5)
        ]
        
        # Process messages concurrently using the optimized method
        tasks = [
            subscriber.handle_message_async(msg) 
            for msg in test_messages
        ]
        
        start_time = asyncio.get_event_loop().time()
        await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # All messages should be processed
        assert len(messages_handled) == 5
        
        # Should complete in reasonable time (concurrent processing)
        processing_time = end_time - start_time
        assert processing_time < 0.1, f"Concurrent processing should be fast, took {processing_time}s"