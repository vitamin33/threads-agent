"""Edge case and performance tests for dashboard system."""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import psutil
import gc

from services.dashboard_api.variant_metrics import VariantMetricsAPI
from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
from services.dashboard_api.event_processor import DashboardEventProcessor


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def metrics_api(self):
        """Create VariantMetricsAPI for edge case testing."""
        with patch('services.dashboard_api.variant_metrics.get_db_connection'):
            with patch('services.dashboard_api.variant_metrics.get_redis_connection'):
                return VariantMetricsAPI()

    @pytest.mark.asyncio
    async def test_null_and_empty_inputs(self, metrics_api):
        """Test handling of null and empty inputs."""
        # Test null persona_id
        result = await metrics_api.get_live_metrics(None)
        assert result["summary"]["total_variants"] == 0
        assert result["active_variants"] == []
        
        # Test empty persona_id
        result = await metrics_api.get_live_metrics("")
        assert result["summary"]["total_variants"] == 0
        
        # Test whitespace-only persona_id
        result = await metrics_api.get_live_metrics("   ")
        assert result["summary"]["total_variants"] == 0

    @pytest.mark.asyncio
    async def test_malformed_database_responses(self, metrics_api):
        """Test handling of malformed database responses."""
        mock_db = AsyncMock()
        
        # Test database returning None
        mock_db.fetch_all.return_value = None
        
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            api = VariantMetricsAPI()
            result = await api.get_active_variants("test-persona")
            assert result == []
        
        # Test database returning malformed records
        mock_db.fetch_all.return_value = [
            {"id": "var_1"},  # Missing required fields
            {"content": "test", "predicted_er": "invalid"},  # Invalid data types
            None,  # Null record
            {"id": "var_2", "content": "valid", "predicted_er": 0.05, "actual_er": 0.06}  # Valid record
        ]
        
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            api = VariantMetricsAPI()
            result = await api.get_active_variants("test-persona")
            
            # Should filter out malformed records and keep valid ones
            assert isinstance(result, list)
            # Implementation should handle gracefully

    @pytest.mark.asyncio
    async def test_database_connection_failures(self, metrics_api):
        """Test various database connection failure scenarios."""
        # Test connection timeout
        mock_db = AsyncMock()
        mock_db.fetch_all.side_effect = asyncio.TimeoutError("Database timeout")
        
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            api = VariantMetricsAPI()
            
            with pytest.raises(asyncio.TimeoutError):
                await api.get_active_variants("test-persona")
        
        # Test connection refused
        mock_db.fetch_all.side_effect = ConnectionRefusedError("Connection refused")
        
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            api = VariantMetricsAPI()
            
            with pytest.raises(ConnectionRefusedError):
                await api.get_active_variants("test-persona")
        
        # Test intermittent failures
        call_count = 0
        def intermittent_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise Exception("Intermittent failure")
            return []
        
        mock_db.fetch_all.side_effect = intermittent_failure
        
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            api = VariantMetricsAPI()
            
            # Some calls should succeed, others fail
            success_count = 0
            failure_count = 0
            
            for i in range(10):
                try:
                    await api.get_active_variants("test-persona")
                    success_count += 1
                except Exception:
                    failure_count += 1
            
            assert success_count > 0
            assert failure_count > 0

    @pytest.mark.asyncio
    async def test_redis_connection_failures(self, metrics_api):
        """Test Redis connection failure scenarios."""
        mock_redis = AsyncMock()
        mock_db = AsyncMock()
        mock_db.fetch_all.return_value = [{"id": "test", "total_variants": 1}]
        
        # Test Redis completely unavailable
        mock_redis.get.side_effect = Exception("Redis unavailable")
        mock_redis.setex.side_effect = Exception("Redis unavailable")
        
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            with patch('services.dashboard_api.variant_metrics.get_redis_connection', return_value=mock_redis):
                api = VariantMetricsAPI()
                
                # Should work without caching
                result = await api.get_performance_summary("test-persona")
                assert isinstance(result, dict)
        
        # Test Redis intermittent failures
        redis_call_count = 0
        def redis_intermittent_failure(*args, **kwargs):
            nonlocal redis_call_count
            redis_call_count += 1
            if redis_call_count % 2 == 0:
                raise Exception("Redis intermittent failure")
            return None
        
        mock_redis.get.side_effect = redis_intermittent_failure
        mock_redis.setex.return_value = True
        
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            with patch('services.dashboard_api.variant_metrics.get_redis_connection', return_value=mock_redis):
                api = VariantMetricsAPI()
                
                # Should handle Redis failures gracefully
                for _ in range(5):
                    result = await api.get_performance_summary("test-persona")
                    assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_websocket_extreme_disconnect_scenarios(self):
        """Test WebSocket handling under extreme disconnect scenarios."""
        ws_handler = VariantDashboardWebSocket()
        persona_id = "test-persona"
        
        # Test massive connection churn
        for cycle in range(100):
            # Add connection
            mock_ws = AsyncMock()
            if persona_id not in ws_handler.connections:
                ws_handler.connections[persona_id] = set()
            ws_handler.connections[persona_id].add(mock_ws)
            
            # Immediately remove (simulating rapid disconnect)
            ws_handler.connections[persona_id].discard(mock_ws)
        
        # Should handle gracefully without memory leaks
        assert len(ws_handler.connections.get(persona_id, set())) == 0
        
        # Test all connections failing simultaneously
        failing_connections = [AsyncMock() for _ in range(50)]
        for conn in failing_connections:
            conn.send_json.side_effect = Exception("Connection failed")
        
        ws_handler.connections[persona_id] = set(failing_connections)
        
        # Broadcast should handle all failures
        await ws_handler.broadcast_variant_update(persona_id, {"test": "data"})
        
        # All connections should be cleaned up
        assert len(ws_handler.connections.get(persona_id, set())) == 0

    @pytest.mark.asyncio
    async def test_malformed_websocket_messages(self):
        """Test handling of malformed WebSocket messages."""
        ws_handler = VariantDashboardWebSocket()
        mock_ws = AsyncMock()
        persona_id = "test-persona"
        
        malformed_messages = [
            "not json",
            "{invalid json}",
            "null",
            "",
            "{'single_quotes': 'invalid'}",
            '{"unclosed": "json',
            '{"type": null}',
            '{"type": 123}',
            '{"data": [1, 2, {"nested": "broken}]'
        ]
        
        for message in malformed_messages:
            # Should not crash
            await ws_handler.handle_message(mock_ws, persona_id, message)
            
            # Should send error response
            if mock_ws.send_json.called:
                error_response = mock_ws.send_json.call_args[0][0]
                assert error_response.get("type") == "error"
                mock_ws.send_json.reset_mock()

    @pytest.mark.asyncio
    async def test_extreme_data_values(self, metrics_api):
        """Test handling of extreme data values."""
        extreme_values = [
            float('inf'),
            float('-inf'),
            float('nan'),
            1e100,
            -1e100,
            0.0,
            -0.0
        ]
        
        for value in extreme_values:
            # Test performance delta calculation with extreme values
            try:
                delta = metrics_api.calculate_performance_delta(value, 0.05)
                # Should either return a valid number or handle gracefully
                assert isinstance(delta, (int, float)) or delta is None
            except (ValueError, ZeroDivisionError, OverflowError):
                # These exceptions are acceptable for extreme values
                pass

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self, metrics_api):
        """Test handling of Unicode and special characters."""
        special_personas = [
            "persona-with-émojis-🚀",
            "persona\nwith\nnewlines",
            "persona\twith\ttabs",
            "persona with spaces",
            "persona-with-ñ-and-ü",
            "persona\x00with\x00nulls",
            "persona'with'quotes",
            'persona"with"doublequotes',
            "persona;with;semicolons",
            "persona<with>brackets"
        ]
        
        for persona_id in special_personas:
            # Should handle special characters gracefully
            try:
                result = await metrics_api.get_live_metrics(persona_id)
                assert isinstance(result, dict)
            except (UnicodeError, ValueError):
                # Some special characters might be rejected, which is acceptable
                pass


class TestPerformanceCharacteristics:
    """Test performance under various load conditions."""

    @pytest.fixture
    def performance_metrics_api(self):
        """Create metrics API with performance-focused mocks."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        
        # Mock large dataset
        large_dataset = [
            {
                "id": f"var_{i}",
                "persona_id": "perf-test",
                "content": f"Performance test variant {i}",
                "predicted_er": 0.05 + (i % 10) * 0.001,
                "actual_er": 0.05 + (i % 8) * 0.002,
                "posted_at": datetime.now() - timedelta(hours=i % 24),
                "status": "active",
                "interaction_count": 100 + i,
                "view_count": 2000 + i * 10
            }
            for i in range(1000)  # 1000 variants
        ]
        
        mock_db.fetch_all.return_value = large_dataset
        mock_redis.get.return_value = None  # No cache
        
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            with patch('services.dashboard_api.variant_metrics.get_redis_connection', return_value=mock_redis):
                api = VariantMetricsAPI()
                api.early_kill_monitor = AsyncMock()
                api.fatigue_detector = AsyncMock()
                api.early_kill_monitor.get_kill_statistics.return_value = {"total_kills_today": 0}
                api.fatigue_detector.get_fatigue_warnings.return_value = []
                return api

    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, performance_metrics_api):
        """Test performance with large datasets."""
        start_time = time.time()
        
        result = await performance_metrics_api.get_live_metrics("perf-test")
        
        processing_time = time.time() - start_time
        
        # Should process 1000 variants within reasonable time
        assert processing_time < 2.0  # 2 seconds
        
        # Verify data integrity
        assert len(result["active_variants"]) == 1000
        assert result["summary"]["total_variants"] == 1000
        
        # Verify calculations are correct
        expected_avg_er = sum(v["live_metrics"]["engagement_rate"] for v in result["active_variants"]) / 1000
        assert abs(result["summary"]["avg_engagement_rate"] - expected_avg_er) < 0.001

    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self, performance_metrics_api):
        """Test performance under concurrent load."""
        num_concurrent_requests = 50
        
        start_time = time.time()
        
        # Create concurrent requests
        tasks = [
            performance_metrics_api.get_live_metrics(f"persona-{i % 5}")
            for i in range(num_concurrent_requests)
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Should handle 50 concurrent requests efficiently
        assert total_time < 5.0  # 5 seconds
        assert len(results) == num_concurrent_requests
        
        # All requests should succeed
        for result in results:
            assert isinstance(result, dict)
            assert "summary" in result
            assert "active_variants" in result

    @pytest.mark.asyncio
    async def test_websocket_broadcast_performance(self):
        """Test WebSocket broadcast performance with many clients."""
        ws_handler = VariantDashboardWebSocket()
        persona_id = "perf-test"
        
        # Create many connections
        num_connections = 500
        connections = [AsyncMock() for _ in range(num_connections)]
        ws_handler.connections[persona_id] = set(connections)
        
        # Measure broadcast time
        start_time = time.time()
        
        await ws_handler.broadcast_variant_update(persona_id, {
            "event_type": "performance_test",
            "data": "test_payload"
        })
        
        broadcast_time = time.time() - start_time
        
        # Should broadcast to 500 connections quickly
        assert broadcast_time < 1.0  # 1 second
        
        # All connections should receive message
        for conn in connections:
            conn.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage patterns under load."""
        ws_handler = VariantDashboardWebSocket()
        
        # Measure initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create and destroy many connections
        for cycle in range(100):
            persona_id = f"memory-test-{cycle % 10}"
            
            # Add many connections
            connections = [AsyncMock() for _ in range(50)]
            ws_handler.connections[persona_id] = set(connections)
            
            # Broadcast to all
            await ws_handler.broadcast_variant_update(persona_id, {"cycle": cycle})
            
            # Remove all connections
            del ws_handler.connections[persona_id]
            
            # Force garbage collection periodically
            if cycle % 10 == 0:
                gc.collect()
        
        # Measure final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB

    @pytest.mark.asyncio
    async def test_rapid_event_processing_performance(self):
        """Test performance of rapid event processing."""
        ws_handler = VariantDashboardWebSocket()
        event_processor = DashboardEventProcessor(ws_handler)
        
        # Setup connections
        persona_id = "rapid-test"
        connections = [AsyncMock() for _ in range(10)]
        ws_handler.connections[persona_id] = set(connections)
        
        # Generate many events
        num_events = 1000
        events = [
            {
                "persona_id": persona_id,
                "engagement_rate": 0.05 + (i % 100) * 0.001,
                "interaction_count": 100 + i,
                "updated_at": datetime.now().isoformat()
            }
            for i in range(num_events)
        ]
        
        start_time = time.time()
        
        # Process all events
        tasks = [
            event_processor.handle_performance_update(f"var_{i}", event_data)
            for i, event_data in enumerate(events)
        ]
        
        await asyncio.gather(*tasks)
        
        processing_time = time.time() - start_time
        
        # Should process 1000 events quickly
        assert processing_time < 2.0  # 2 seconds
        
        # All connections should receive all events
        for conn in connections:
            assert conn.send_json.call_count == num_events

    @pytest.mark.asyncio
    async def test_database_query_optimization(self, performance_metrics_api):
        """Test database query performance characteristics."""
        # Test multiple calls to ensure query optimization
        times = []
        
        for i in range(10):
            start_time = time.time()
            await performance_metrics_api.get_active_variants("perf-test")
            query_time = time.time() - start_time
            times.append(query_time)
        
        # Later queries might be faster due to caching/optimization
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0  # Average query time < 1 second
        
        # Verify performance consistency
        max_time = max(times)
        min_time = min(times)
        assert max_time / min_time < 5.0  # Max shouldn't be more than 5x min

    @pytest.mark.asyncio
    async def test_cpu_intensive_calculations_performance(self, performance_metrics_api):
        """Test performance of CPU-intensive calculations."""
        # Test performance delta calculations with large dataset
        start_time = time.time()
        
        # Simulate many performance delta calculations
        for i in range(10000):
            actual_er = 0.05 + (i % 100) * 0.0001
            predicted_er = 0.05 + (i % 80) * 0.0002
            
            delta = performance_metrics_api.calculate_performance_delta(actual_er, predicted_er)
            assert isinstance(delta, (int, float))
        
        calculation_time = time.time() - start_time
        
        # Should perform 10k calculations quickly
        assert calculation_time < 1.0  # 1 second

    @pytest.mark.asyncio
    async def test_network_simulation_performance(self):
        """Test performance under simulated network conditions."""
        ws_handler = VariantDashboardWebSocket()
        persona_id = "network-test"
        
        # Create connections with simulated network delays
        fast_conn = AsyncMock()
        medium_conn = AsyncMock()
        slow_conn = AsyncMock()
        
        async def fast_send(data):
            await asyncio.sleep(0.001)  # 1ms
        
        async def medium_send(data):
            await asyncio.sleep(0.01)  # 10ms
        
        async def slow_send(data):
            await asyncio.sleep(0.1)  # 100ms
        
        fast_conn.send_json.side_effect = fast_send
        medium_conn.send_json.side_effect = medium_send
        slow_conn.send_json.side_effect = slow_send
        
        ws_handler.connections[persona_id] = {fast_conn, medium_conn, slow_conn}
        
        # Test broadcast performance with mixed connection speeds
        start_time = time.time()
        
        broadcast_tasks = [
            ws_handler.broadcast_variant_update(persona_id, {"test": i})
            for i in range(10)
        ]
        
        await asyncio.gather(*broadcast_tasks)
        
        total_time = time.time() - start_time
        
        # Should complete reasonably quickly despite slow connections
        # (assuming broadcasts don't wait for slow connections)
        assert total_time < 2.0  # 2 seconds
        
        # All connections should receive all messages
        assert fast_conn.send_json.call_count == 10
        assert medium_conn.send_json.call_count == 10
        assert slow_conn.send_json.call_count == 10


class TestStressTests:
    """Stress tests for extreme conditions."""

    @pytest.mark.asyncio
    async def test_connection_flood_stress(self):
        """Test handling of connection flood attacks."""
        ws_handler = VariantDashboardWebSocket()
        
        # Simulate many personas with many connections each
        num_personas = 100
        connections_per_persona = 50
        
        start_time = time.time()
        
        # Create connections for all personas
        for persona_idx in range(num_personas):
            persona_id = f"stress-persona-{persona_idx}"
            connections = [AsyncMock() for _ in range(connections_per_persona)]
            ws_handler.connections[persona_id] = set(connections)
        
        setup_time = time.time() - start_time
        
        # Should handle large number of connections
        assert setup_time < 5.0  # 5 seconds to set up 5000 connections
        
        # Test broadcast to all
        broadcast_start = time.time()
        
        broadcast_tasks = [
            ws_handler.broadcast_variant_update(f"stress-persona-{i}", {"stress": "test"})
            for i in range(num_personas)
        ]
        
        await asyncio.gather(*broadcast_tasks)
        
        broadcast_time = time.time() - broadcast_start
        
        # Should broadcast to all personas quickly
        assert broadcast_time < 10.0  # 10 seconds for 5000 total connections
        
        # Verify total connections
        total_connections = sum(len(conns) for conns in ws_handler.connections.values())
        assert total_connections == num_personas * connections_per_persona

    @pytest.mark.asyncio
    async def test_data_volume_stress(self):
        """Test handling of large data volumes."""
        # Create metrics API with very large dataset
        mock_db = AsyncMock()
        
        # 10,000 variants with large content
        large_content = "A" * 1000  # 1KB per variant
        huge_dataset = [
            {
                "id": f"stress_var_{i}",
                "persona_id": "stress-test",
                "content": f"{large_content} {i}",
                "predicted_er": 0.05 + (i % 1000) * 0.00001,
                "actual_er": 0.05 + (i % 800) * 0.00002,
                "posted_at": datetime.now() - timedelta(seconds=i),
                "status": "active",
                "interaction_count": 100 + i,
                "view_count": 2000 + i * 5
            }
            for i in range(10000)  # 10,000 variants
        ]
        
        mock_db.fetch_all.return_value = huge_dataset
        
        with patch('services.dashboard_api.variant_metrics.get_db_connection', return_value=mock_db):
            with patch('services.dashboard_api.variant_metrics.get_redis_connection'):
                api = VariantMetricsAPI()
                api.early_kill_monitor = AsyncMock()
                api.fatigue_detector = AsyncMock()
                api.early_kill_monitor.get_kill_statistics.return_value = {"total_kills_today": 0}
                api.fatigue_detector.get_fatigue_warnings.return_value = []
                
                start_time = time.time()
                
                result = await api.get_live_metrics("stress-test")
                
                processing_time = time.time() - start_time
                
                # Should handle 10,000 variants with 1KB each (~10MB data)
                assert processing_time < 5.0  # 5 seconds
                
                # Verify data integrity
                assert len(result["active_variants"]) == 10000
                assert result["summary"]["total_variants"] == 10000

    @pytest.mark.asyncio
    async def test_concurrent_stress_with_failures(self):
        """Test system under stress with concurrent failures."""
        ws_handler = VariantDashboardWebSocket()
        event_processor = DashboardEventProcessor(ws_handler)
        
        # Setup personas with mixed connection reliability
        num_personas = 20
        for persona_idx in range(num_personas):
            persona_id = f"stress-persona-{persona_idx}"
            
            # Mix of reliable and unreliable connections
            reliable_conns = [AsyncMock() for _ in range(5)]
            unreliable_conns = [AsyncMock() for _ in range(5)]
            
            # Make unreliable connections fail randomly
            for conn in unreliable_conns:
                def random_failure(data):
                    import random
                    if random.random() < 0.3:  # 30% failure rate
                        raise Exception("Random connection failure")
                
                conn.send_json.side_effect = random_failure
            
            ws_handler.connections[persona_id] = set(reliable_conns + unreliable_conns)
        
        # Generate many concurrent events
        num_events = 500
        events = []
        
        for i in range(num_events):
            persona_id = f"stress-persona-{i % num_personas}"
            if i % 2 == 0:
                events.append((
                    'performance_update',
                    f'stress_var_{i}',
                    {
                        'persona_id': persona_id,
                        'engagement_rate': 0.05 + (i % 100) * 0.001,
                        'interaction_count': 100 + i,
                        'updated_at': datetime.now().isoformat()
                    }
                ))
            else:
                events.append((
                    'early_kill',
                    f'stress_var_{i}',
                    {
                        'persona_id': persona_id,
                        'reason': 'stress_test',
                        'final_engagement_rate': 0.02,
                        'killed_at': datetime.now().isoformat()
                    }
                ))
        
        start_time = time.time()
        
        # Process all events concurrently
        tasks = []
        for event_type, variant_id, data in events:
            if event_type == 'performance_update':
                task = event_processor.handle_performance_update(variant_id, data)
            else:
                task = event_processor.handle_early_kill_event(variant_id, data)
            tasks.append(task)
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Should handle 500 concurrent events with failures
        assert total_time < 10.0  # 10 seconds
        
        # Most events should succeed despite some connection failures
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > len(results) * 0.7  # At least 70% success
        
        # Verify system stability after stress
        assert len(ws_handler.connections) <= num_personas
        for persona_connections in ws_handler.connections.values():
            assert len(persona_connections) <= 10  # Some unreliable connections should be removed
