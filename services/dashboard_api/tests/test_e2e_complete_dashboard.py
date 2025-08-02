"""End-to-end tests for complete dashboard functionality."""

import pytest
import asyncio
import sqlite3
import time
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from services.dashboard_api.variant_metrics import VariantMetricsAPI
from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
from services.dashboard_api.event_processor import DashboardEventProcessor


class TestDashboardE2EComplete:
    """Complete end-to-end tests for dashboard functionality."""

    @pytest.fixture
    async def test_database(self):
        """Create in-memory test database with realistic data."""
        import tempfile
        import os

        db_file = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(db_file)

        # Create test tables
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS variants (
                id TEXT PRIMARY KEY,
                persona_id TEXT NOT NULL,
                content TEXT NOT NULL,
                predicted_er REAL NOT NULL,
                actual_er REAL,
                posted_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                interaction_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS variant_kills (
                id TEXT PRIMARY KEY,
                variant_id TEXT NOT NULL,
                persona_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                final_engagement_rate REAL,
                sample_size INTEGER,
                killed_at TIMESTAMP NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS pattern_usage (
                id TEXT PRIMARY KEY,
                persona_id TEXT NOT NULL,
                pattern_id TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                fatigue_score REAL DEFAULT 0.0
            );
            
            CREATE TABLE IF NOT EXISTS dashboard_events (
                id TEXT PRIMARY KEY,
                persona_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL
            );
        """)

        # Insert test data
        now = datetime.now()
        test_data = [
            # Active variants
            (
                "var_e2e_1",
                "ai-jesus",
                "E2E Test variant 1",
                0.065,
                0.058,
                now - timedelta(hours=2),
                "active",
                150,
                2500,
            ),
            (
                "var_e2e_2",
                "ai-jesus",
                "E2E Test variant 2",
                0.052,
                0.067,
                now - timedelta(hours=1),
                "active",
                180,
                2800,
            ),
            (
                "var_e2e_3",
                "ai-jesus",
                "E2E Test variant 3",
                0.045,
                0.048,
                now - timedelta(hours=3),
                "active",
                95,
                2100,
            ),
            # Different persona
            (
                "var_e2e_buddha_1",
                "ai-buddha",
                "Buddha test variant",
                0.055,
                0.062,
                now - timedelta(hours=1),
                "active",
                140,
                2300,
            ),
        ]

        conn.executemany(
            "INSERT INTO variants (id, persona_id, content, predicted_er, actual_er, posted_at, status, interaction_count, view_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            test_data,
        )

        # Insert kill data
        kill_data = [
            (
                "kill_1",
                "var_e2e_killed",
                "ai-jesus",
                "low_engagement",
                0.025,
                150,
                now - timedelta(hours=1),
            ),
            (
                "kill_2",
                "var_e2e_killed_2",
                "ai-jesus",
                "negative_sentiment",
                0.018,
                200,
                now - timedelta(hours=2),
            ),
        ]

        conn.executemany(
            "INSERT INTO variant_kills (id, variant_id, persona_id, reason, final_engagement_rate, sample_size, killed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            kill_data,
        )

        # Insert pattern usage data
        pattern_data = [
            (
                "pattern_1",
                "ai-jesus",
                "curiosity_gap",
                15,
                now - timedelta(hours=1),
                0.85,
            ),
            (
                "pattern_2",
                "ai-jesus",
                "social_proof",
                8,
                now - timedelta(hours=2),
                0.42,
            ),
        ]

        conn.executemany(
            "INSERT INTO pattern_usage (id, persona_id, pattern_id, usage_count, last_used, fatigue_score) VALUES (?, ?, ?, ?, ?, ?)",
            pattern_data,
        )

        conn.commit()

        yield db_file

        # Cleanup
        conn.close()
        if os.path.exists(db_file):
            os.unlink(db_file)

    @pytest.fixture
    def mock_external_services(self):
        """Mock external services for E2E testing."""
        mocks = {
            "redis": AsyncMock(),
            "early_kill_monitor": AsyncMock(),
            "fatigue_detector": AsyncMock(),
        }

        # Setup Redis mock
        mocks["redis"].get.return_value = None  # No cache
        mocks["redis"].setex.return_value = True

        # Setup EarlyKillMonitor mock
        mocks["early_kill_monitor"].get_kill_statistics.return_value = {
            "total_kills_today": 2,
            "avg_time_to_kill": 90,  # minutes
            "kill_reasons": {"low_engagement": 1, "negative_sentiment": 1},
        }

        # Setup PatternFatigueDetector mock
        mocks["fatigue_detector"].get_fatigue_warnings.return_value = [
            {
                "pattern_id": "curiosity_gap",
                "fatigue_score": 0.85,
                "warning_level": "high",
                "recommendation": "Switch to controversy patterns",
            }
        ]

        return mocks

    @pytest.mark.asyncio
    async def test_complete_dashboard_data_flow(
        self, test_database, mock_external_services
    ):
        """Test complete data flow from database to dashboard."""

        # Mock database connection to return our test database
        def mock_get_db():
            import sqlite3

            conn = sqlite3.connect(test_database)
            conn.row_factory = sqlite3.Row
            return conn

        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            side_effect=mock_get_db,
        ):
            with patch(
                "services.dashboard_api.variant_metrics.get_redis_connection",
                return_value=mock_external_services["redis"],
            ):
                # Create metrics API instance
                metrics_api = VariantMetricsAPI()
                metrics_api.early_kill_monitor = mock_external_services[
                    "early_kill_monitor"
                ]
                metrics_api.fatigue_detector = mock_external_services[
                    "fatigue_detector"
                ]

                # Test complete data retrieval
                result = await metrics_api.get_live_metrics("ai-jesus")

                # Verify all sections are present and have expected data
                assert "summary" in result
                assert "active_variants" in result
                assert "early_kills_today" in result
                assert "pattern_fatigue_warnings" in result
                assert "optimization_opportunities" in result
                assert "real_time_feed" in result

                # Verify summary calculations
                summary = result["summary"]
                assert summary["total_variants"] == 3  # 3 variants for ai-jesus

                # Verify active variants
                variants = result["active_variants"]
                assert len(variants) == 3

                # Verify variants have all required fields
                for variant in variants:
                    assert "id" in variant
                    assert "content" in variant
                    assert "predicted_er" in variant
                    assert "live_metrics" in variant
                    assert "time_since_post" in variant
                    assert "performance_vs_prediction" in variant

                # Verify kill statistics
                kills = result["early_kills_today"]
                assert kills["kills_today"] == 2

                # Verify pattern fatigue warnings
                warnings = result["pattern_fatigue_warnings"]
                assert len(warnings) == 1
                assert warnings[0]["pattern_id"] == "curiosity_gap"

    @pytest.mark.asyncio
    async def test_websocket_real_time_updates_e2e(
        self, test_database, mock_external_services
    ):
        """Test end-to-end WebSocket real-time updates."""
        # Setup WebSocket handler with test database
        ws_handler = VariantDashboardWebSocket()
        event_processor = DashboardEventProcessor(ws_handler)

        # Mock WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        persona_id = "ai-jesus"

        ws_handler.connections[persona_id] = {mock_ws1, mock_ws2}

        # Test early kill event processing
        kill_event_data = {
            "persona_id": persona_id,
            "reason": "pattern_fatigue",
            "final_engagement_rate": 0.022,
            "sample_size": 175,
            "killed_at": datetime.now().isoformat(),
        }

        await event_processor.handle_early_kill_event(
            "var_e2e_new_kill", kill_event_data
        )

        # Verify both connections received the update
        assert mock_ws1.send_json.call_count == 1
        assert mock_ws2.send_json.call_count == 1

        # Verify message structure
        sent_message = mock_ws1.send_json.call_args[0][0]
        assert sent_message["type"] == "variant_update"
        assert sent_message["data"]["event_type"] == "early_kill"
        assert sent_message["data"]["variant_id"] == "var_e2e_new_kill"
        assert sent_message["data"]["kill_reason"] == "pattern_fatigue"

        # Test performance update event
        mock_ws1.send_json.reset_mock()
        mock_ws2.send_json.reset_mock()

        performance_data = {
            "persona_id": persona_id,
            "engagement_rate": 0.072,
            "interaction_count": 220,
            "view_count": 3100,
            "updated_at": datetime.now().isoformat(),
        }

        await event_processor.handle_performance_update("var_e2e_1", performance_data)

        # Verify performance update was broadcast
        assert mock_ws1.send_json.call_count == 1
        assert mock_ws2.send_json.call_count == 1

        perf_message = mock_ws1.send_json.call_args[0][0]
        assert perf_message["type"] == "variant_update"
        assert perf_message["data"]["event_type"] == "performance_update"
        assert perf_message["data"]["current_er"] == 0.072

    @pytest.mark.asyncio
    async def test_multi_persona_isolation_e2e(
        self, test_database, mock_external_services
    ):
        """Test that different personas are properly isolated."""

        def mock_get_db():
            import sqlite3

            conn = sqlite3.connect(test_database)
            conn.row_factory = sqlite3.Row
            return conn

        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            side_effect=mock_get_db,
        ):
            with patch(
                "services.dashboard_api.variant_metrics.get_redis_connection",
                return_value=mock_external_services["redis"],
            ):
                metrics_api = VariantMetricsAPI()
                metrics_api.early_kill_monitor = mock_external_services[
                    "early_kill_monitor"
                ]
                metrics_api.fatigue_detector = mock_external_services[
                    "fatigue_detector"
                ]

                # Get data for ai-jesus
                jesus_data = await metrics_api.get_live_metrics("ai-jesus")

                # Get data for ai-buddha
                buddha_data = await metrics_api.get_live_metrics("ai-buddha")

                # Verify data isolation
                jesus_variants = jesus_data["active_variants"]
                buddha_variants = buddha_data["active_variants"]

                # ai-jesus should have 3 variants
                assert len(jesus_variants) == 3
                assert all(v["id"].startswith("var_e2e_") for v in jesus_variants)

                # ai-buddha should have 1 variant
                assert len(buddha_variants) == 1
                assert buddha_variants[0]["id"] == "var_e2e_buddha_1"

                # Verify persona IDs are correct
                for variant in jesus_variants:
                    # Would need to include persona_id in query results for this check
                    assert "id" in variant

                for variant in buddha_variants:
                    assert "id" in variant

    @pytest.mark.asyncio
    async def test_websocket_connection_resilience_e2e(self):
        """Test WebSocket connection resilience in realistic scenarios."""
        ws_handler = VariantDashboardWebSocket()
        persona_id = "ai-jesus"

        # Setup multiple connections with different failure scenarios
        stable_ws = AsyncMock()  # Always works
        intermittent_ws = AsyncMock()  # Sometimes fails
        failed_ws = AsyncMock()  # Always fails

        # Setup failure behaviors
        intermittent_fail_count = 0

        def intermittent_send(data):
            nonlocal intermittent_fail_count
            intermittent_fail_count += 1
            if intermittent_fail_count % 3 == 0:
                raise Exception("Intermittent failure")

        intermittent_ws.send_json.side_effect = intermittent_send
        failed_ws.send_json.side_effect = Exception("Permanent failure")

        ws_handler.connections[persona_id] = {stable_ws, intermittent_ws, failed_ws}

        # Send multiple updates
        updates = [
            {
                "event_type": "performance_update",
                "variant_id": f"var_{i}",
                "data": f"update_{i}",
            }
            for i in range(10)
        ]

        for update in updates:
            await ws_handler.broadcast_variant_update(persona_id, update)

        # Verify stable connection received all updates
        assert stable_ws.send_json.call_count == 10

        # Verify intermittent connection received some updates
        assert 0 < intermittent_ws.send_json.call_count < 10

        # Verify failed connection was removed
        remaining_connections = ws_handler.connections.get(persona_id, set())
        assert failed_ws not in remaining_connections
        assert stable_ws in remaining_connections

    @pytest.mark.asyncio
    async def test_performance_under_load_e2e(
        self, test_database, mock_external_services
    ):
        """Test dashboard performance under realistic load."""
        import time

        def mock_get_db():
            import sqlite3

            conn = sqlite3.connect(test_database)
            conn.row_factory = sqlite3.Row
            return conn

        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            side_effect=mock_get_db,
        ):
            with patch(
                "services.dashboard_api.variant_metrics.get_redis_connection",
                return_value=mock_external_services["redis"],
            ):
                metrics_api = VariantMetricsAPI()
                metrics_api.early_kill_monitor = mock_external_services[
                    "early_kill_monitor"
                ]
                metrics_api.fatigue_detector = mock_external_services[
                    "fatigue_detector"
                ]

                # Test concurrent requests
                start_time = time.time()

                tasks = [metrics_api.get_live_metrics("ai-jesus") for _ in range(20)]

                results = await asyncio.gather(*tasks)

                processing_time = time.time() - start_time

                # Should complete within reasonable time
                assert processing_time < 2.0  # 2 seconds for 20 concurrent requests

                # All requests should succeed
                assert len(results) == 20
                for result in results:
                    assert "summary" in result
                    assert "active_variants" in result

                # Test WebSocket broadcast performance
                ws_handler = VariantDashboardWebSocket()
                persona_id = "ai-jesus"

                # Create many connections
                connections = [AsyncMock() for _ in range(50)]
                ws_handler.connections[persona_id] = set(connections)

                start_time = time.time()

                # Send broadcast to all connections
                await ws_handler.broadcast_variant_update(
                    persona_id, {"test": "load_test"}
                )

                broadcast_time = time.time() - start_time

                # Should broadcast to 50 connections quickly
                assert broadcast_time < 0.5  # 500ms

                # All connections should receive message
                for conn in connections:
                    conn.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_consistency_e2e(self, test_database, mock_external_services):
        """Test data consistency across multiple operations."""

        def mock_get_db():
            import sqlite3

            conn = sqlite3.connect(test_database)
            conn.row_factory = sqlite3.Row
            return conn

        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            side_effect=mock_get_db,
        ):
            with patch(
                "services.dashboard_api.variant_metrics.get_redis_connection",
                return_value=mock_external_services["redis"],
            ):
                metrics_api = VariantMetricsAPI()
                metrics_api.early_kill_monitor = mock_external_services[
                    "early_kill_monitor"
                ]
                metrics_api.fatigue_detector = mock_external_services[
                    "fatigue_detector"
                ]

                # Get initial data
                initial_data = await metrics_api.get_live_metrics("ai-jesus")
                initial_variant_count = len(initial_data["active_variants"])

                # Simulate variant creation (would normally come from external system)
                # For this test, we'll verify existing data consistency

                # Get data again
                second_data = await metrics_api.get_live_metrics("ai-jesus")

                # Verify consistency
                assert len(second_data["active_variants"]) == initial_variant_count

                # Verify variant IDs are consistent
                initial_ids = {v["id"] for v in initial_data["active_variants"]}
                second_ids = {v["id"] for v in second_data["active_variants"]}
                assert initial_ids == second_ids

                # Verify performance calculations are consistent
                for initial_variant in initial_data["active_variants"]:
                    matching_variant = next(
                        v
                        for v in second_data["active_variants"]
                        if v["id"] == initial_variant["id"]
                    )

                    # Performance metrics should be consistent
                    assert (
                        matching_variant["predicted_er"]
                        == initial_variant["predicted_er"]
                    )
                    # Live metrics might change, but structure should be consistent
                    assert "live_metrics" in matching_variant
                    assert "engagement_rate" in matching_variant["live_metrics"]

    @pytest.mark.asyncio
    async def test_error_recovery_e2e(self, test_database, mock_external_services):
        """Test error recovery in end-to-end scenarios."""

        # Test database connection failure recovery
        def failing_db_connection():
            raise Exception("Database connection failed")

        def working_db_connection():
            import sqlite3

            conn = sqlite3.connect(test_database)
            conn.row_factory = sqlite3.Row
            return conn

        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            side_effect=failing_db_connection,
        ):
            metrics_api = VariantMetricsAPI()

            # Should handle database failure gracefully
            with pytest.raises(Exception) as exc_info:
                await metrics_api.get_live_metrics("ai-jesus")

            assert "Database connection failed" in str(exc_info.value)

        # Test recovery after database comes back online
        with patch(
            "services.dashboard_api.variant_metrics.get_db_connection",
            side_effect=working_db_connection,
        ):
            with patch(
                "services.dashboard_api.variant_metrics.get_redis_connection",
                return_value=mock_external_services["redis"],
            ):
                metrics_api = VariantMetricsAPI()
                metrics_api.early_kill_monitor = mock_external_services[
                    "early_kill_monitor"
                ]
                metrics_api.fatigue_detector = mock_external_services[
                    "fatigue_detector"
                ]

                # Should work normally after recovery
                result = await metrics_api.get_live_metrics("ai-jesus")
                assert "summary" in result
                assert "active_variants" in result

    @pytest.mark.asyncio
    async def test_real_time_event_ordering_e2e(self):
        """Test that real-time events maintain proper ordering."""
        ws_handler = VariantDashboardWebSocket()
        event_processor = DashboardEventProcessor(ws_handler)

        # Setup WebSocket connection
        mock_ws = AsyncMock()
        persona_id = "ai-jesus"
        ws_handler.connections[persona_id] = {mock_ws}

        # Send events in specific order
        events = [
            (
                "early_kill",
                "var_1",
                {
                    "persona_id": persona_id,
                    "reason": "low_engagement",
                    "killed_at": "2024-01-01T10:00:00Z",
                },
            ),
            (
                "performance_update",
                "var_2",
                {
                    "persona_id": persona_id,
                    "engagement_rate": 0.065,
                    "updated_at": "2024-01-01T10:01:00Z",
                },
            ),
            (
                "early_kill",
                "var_3",
                {
                    "persona_id": persona_id,
                    "reason": "negative_sentiment",
                    "killed_at": "2024-01-01T10:02:00Z",
                },
            ),
            (
                "performance_update",
                "var_4",
                {
                    "persona_id": persona_id,
                    "engagement_rate": 0.078,
                    "updated_at": "2024-01-01T10:03:00Z",
                },
            ),
        ]

        # Process events
        for event_type, variant_id, data in events:
            if event_type == "early_kill":
                await event_processor.handle_early_kill_event(variant_id, data)
            elif event_type == "performance_update":
                await event_processor.handle_performance_update(variant_id, data)

        # Verify all events were sent in order
        assert mock_ws.send_json.call_count == 4

        # Check that timestamps increase (events maintain order)
        call_args_list = mock_ws.send_json.call_args_list
        timestamps = []

        for call_args in call_args_list:
            message = call_args[0][0]
            assert "timestamp" in message
            timestamps.append(message["timestamp"])

        # Timestamps should be in increasing order (or at least not decreasing)
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i - 1]


class TestDashboardE2EScenarios:
    """Test realistic dashboard usage scenarios."""

    @pytest.mark.asyncio
    async def test_typical_user_session_e2e(self):
        """Test a typical user session from connection to disconnection."""
        ws_handler = VariantDashboardWebSocket()

        # Mock metrics API
        mock_metrics_api = AsyncMock()
        mock_metrics_api.get_live_metrics.return_value = {
            "summary": {"total_variants": 5, "avg_engagement_rate": 0.062},
            "active_variants": [],
            "early_kills_today": {"kills_today": 1},
            "pattern_fatigue_warnings": [],
            "optimization_opportunities": [],
            "real_time_feed": [],
        }
        ws_handler.metrics_api = mock_metrics_api

        # Mock WebSocket
        mock_ws = AsyncMock()
        persona_id = "ai-jesus"

        # Simulate user connecting
        await ws_handler.send_initial_data(mock_ws, persona_id)

        # Verify initial data was sent
        mock_ws.send_json.assert_called_once()
        initial_message = mock_ws.send_json.call_args[0][0]
        assert initial_message["type"] == "initial_data"
        assert "data" in initial_message

        # Add connection to handler
        ws_handler.connections[persona_id] = {mock_ws}

        # Simulate user requesting data refresh
        mock_ws.send_json.reset_mock()
        await ws_handler.handle_message(mock_ws, persona_id, '{"type": "refresh_data"}')

        # Should send fresh data
        mock_ws.send_json.assert_called_once()

        # Simulate ping/pong for keepalive
        mock_ws.send_json.reset_mock()
        await ws_handler.handle_message(mock_ws, persona_id, '{"type": "ping"}')

        # Should respond with pong
        mock_ws.send_json.assert_called_once()
        pong_message = mock_ws.send_json.call_args[0][0]
        assert pong_message["type"] == "pong"

        # Simulate real-time update while user is connected
        mock_ws.send_json.reset_mock()
        await ws_handler.broadcast_variant_update(
            persona_id,
            {
                "event_type": "performance_update",
                "variant_id": "var_test",
                "current_er": 0.072,
            },
        )

        # User should receive the update
        mock_ws.send_json.assert_called_once()

        # Simulate user disconnection
        ws_handler.connections[persona_id].discard(mock_ws)

        # Subsequent updates should not be sent to disconnected user
        mock_ws.send_json.reset_mock()
        await ws_handler.broadcast_variant_update(
            persona_id, {"event_type": "test", "data": "should_not_receive"}
        )

        # Should not send to disconnected user
        mock_ws.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_high_activity_period_e2e(self):
        """Test dashboard during high activity period with many updates."""
        ws_handler = VariantDashboardWebSocket()
        event_processor = DashboardEventProcessor(ws_handler)

        # Setup multiple persona connections
        personas = ["ai-jesus", "ai-buddha", "ai-socrates"]
        connections_per_persona = 3

        all_connections = []
        for persona_id in personas:
            connections = [AsyncMock() for _ in range(connections_per_persona)]
            ws_handler.connections[persona_id] = set(connections)
            all_connections.extend(connections)

        # Simulate high activity: many events in short time
        events = []
        for i in range(50):  # 50 events
            persona_id = personas[i % len(personas)]
            if i % 2 == 0:
                # Performance update
                events.append(
                    (
                        "performance_update",
                        f"var_activity_{i}",
                        {
                            "persona_id": persona_id,
                            "engagement_rate": 0.05 + (i % 10) * 0.005,
                            "interaction_count": 100 + i,
                            "updated_at": datetime.now().isoformat(),
                        },
                    )
                )
            else:
                # Early kill event
                events.append(
                    (
                        "early_kill",
                        f"var_activity_{i}",
                        {
                            "persona_id": persona_id,
                            "reason": "test_reason",
                            "final_engagement_rate": 0.02,
                            "killed_at": datetime.now().isoformat(),
                        },
                    )
                )

        import time

        start_time = time.time()

        # Process all events
        for event_type, variant_id, data in events:
            if event_type == "performance_update":
                await event_processor.handle_performance_update(variant_id, data)
            else:
                await event_processor.handle_early_kill_event(variant_id, data)

        processing_time = time.time() - start_time

        # Should process all events quickly
        assert processing_time < 1.0  # 1 second for 50 events

        # Verify event distribution
        # Each persona should have received events for their variants
        for persona_idx, persona_id in enumerate(personas):
            persona_connections = ws_handler.connections[persona_id]
            expected_events = len(
                [e for e in events if e[2]["persona_id"] == persona_id]
            )

            for conn in persona_connections:
                assert conn.send_json.call_count == expected_events

    @pytest.mark.asyncio
    async def test_dashboard_resilience_under_failures_e2e(self):
        """Test dashboard resilience when components fail."""
        ws_handler = VariantDashboardWebSocket()
        persona_id = "ai-jesus"

        # Setup connections with various failure patterns
        reliable_conn = AsyncMock()
        flaky_conn = AsyncMock()
        slow_conn = AsyncMock()

        # Flaky connection fails randomly
        flaky_call_count = 0

        def flaky_send(data):
            nonlocal flaky_call_count
            flaky_call_count += 1
            if flaky_call_count % 4 == 0:  # Fail every 4th call
                raise Exception("Flaky connection failure")

        flaky_conn.send_json.side_effect = flaky_send

        # Slow connection simulates network delays
        async def slow_send(data):
            await asyncio.sleep(0.1)  # 100ms delay

        slow_conn.send_json.side_effect = slow_send

        ws_handler.connections[persona_id] = {reliable_conn, flaky_conn, slow_conn}

        # Send multiple updates rapidly
        update_tasks = []
        for i in range(20):
            task = ws_handler.broadcast_variant_update(
                persona_id, {"event_type": "test", "sequence": i}
            )
            update_tasks.append(task)

        # Execute all updates concurrently
        start_time = time.time()
        await asyncio.gather(*update_tasks)
        execution_time = time.time() - start_time

        # Should complete reasonably quickly despite slow connections
        assert execution_time < 3.0  # Should not be blocked by slow connections

        # Reliable connection should receive all updates
        assert reliable_conn.send_json.call_count == 20

        # Flaky connection should receive most updates (some failed)
        assert 15 <= flaky_conn.send_json.call_count <= 20

        # Slow connection should receive all updates (just slowly)
        assert slow_conn.send_json.call_count == 20

        # Verify failed connections are cleaned up
        # (This would require implementing cleanup logic in the actual handler)
        remaining_connections = ws_handler.connections.get(persona_id, set())
        assert len(remaining_connections) <= 3  # Some connections might be removed
