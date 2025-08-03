"""Test configuration and fixtures for dashboard API tests."""

import pytest
import asyncio
import tempfile
import sqlite3
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """Create a mock database with realistic test data."""
    db = AsyncMock()

    # Default test data
    now = datetime.now()
    test_variants = [
        {
            "id": "test_var_1",
            "persona_id": "ai-jesus",
            "content": "Test variant 1 content",
            "predicted_er": 0.065,
            "actual_er": 0.062,
            "posted_at": now - timedelta(hours=2),
            "status": "active",
            "interaction_count": 150,
            "view_count": 2400,
        },
        {
            "id": "test_var_2",
            "persona_id": "ai-jesus",
            "content": "Test variant 2 content",
            "predicted_er": 0.052,
            "actual_er": 0.068,
            "posted_at": now - timedelta(hours=1),
            "status": "active",
            "interaction_count": 180,
            "view_count": 2650,
        },
        {
            "id": "test_var_buddha_1",
            "persona_id": "ai-buddha",
            "content": "Buddha test variant",
            "predicted_er": 0.055,
            "actual_er": 0.059,
            "posted_at": now - timedelta(hours=3),
            "status": "active",
            "interaction_count": 120,
            "view_count": 2100,
        },
    ]

    def filter_by_persona(persona_id):
        return [v for v in test_variants if v["persona_id"] == persona_id]

    # Configure database mock responses
    db.fetch_all.side_effect = lambda query, params=None: (
        filter_by_persona(params[0]) if params else test_variants
    )

    db.fetch_one.return_value = {"total_kills_today": 2, "avg_time_to_kill": 4.5}

    return db


@pytest.fixture
def mock_redis():
    """Create a mock Redis connection."""
    redis = AsyncMock()
    redis.get.return_value = None  # No cached data by default
    redis.setex.return_value = True
    redis.delete.return_value = 1
    return redis


@pytest.fixture
def mock_early_kill_monitor():
    """Create a mock EarlyKillMonitor."""
    monitor = AsyncMock()
    monitor.get_kill_statistics.return_value = {
        "total_kills_today": 3,
        "avg_time_to_kill": 5.2,
        "kill_reasons": {"low_engagement": 2, "negative_sentiment": 1},
    }
    return monitor


@pytest.fixture
def mock_fatigue_detector():
    """Create a mock PatternFatigueDetector."""
    detector = AsyncMock()
    detector.get_fatigue_warnings.return_value = [
        {
            "pattern_id": "curiosity_gap",
            "fatigue_score": 0.82,
            "warning_level": "high",
            "recommendation": "Switch to controversy patterns",
        },
        {
            "pattern_id": "social_proof",
            "fatigue_score": 0.65,
            "warning_level": "medium",
            "recommendation": "Reduce usage frequency",
        },
    ]
    return detector


@pytest.fixture
def real_test_database():
    """Create a real SQLite database for integration tests."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Create database schema and test data
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE variants (
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
        
        CREATE TABLE variant_kills (
            id TEXT PRIMARY KEY,
            variant_id TEXT NOT NULL,
            persona_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            final_engagement_rate REAL,
            sample_size INTEGER,
            killed_at TIMESTAMP NOT NULL
        );
        
        CREATE TABLE pattern_usage (
            id TEXT PRIMARY KEY,
            persona_id TEXT NOT NULL,
            pattern_id TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            last_used TIMESTAMP,
            fatigue_score REAL DEFAULT 0.0
        );
        
        CREATE TABLE dashboard_events (
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
        (
            "real_var_1",
            "ai-jesus",
            "Real test variant 1",
            0.065,
            0.062,
            now - timedelta(hours=2),
            "active",
            150,
            2400,
        ),
        (
            "real_var_2",
            "ai-jesus",
            "Real test variant 2",
            0.052,
            0.068,
            now - timedelta(hours=1),
            "active",
            180,
            2650,
        ),
        (
            "real_var_3",
            "ai-buddha",
            "Real Buddha variant",
            0.055,
            0.059,
            now - timedelta(hours=3),
            "active",
            120,
            2100,
        ),
    ]

    conn.executemany(
        "INSERT INTO variants (id, persona_id, content, predicted_er, actual_er, posted_at, status, interaction_count, view_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        test_data,
    )

    kill_data = [
        (
            "kill_1",
            "killed_var_1",
            "ai-jesus",
            "low_engagement",
            0.025,
            150,
            now - timedelta(hours=1),
        ),
        (
            "kill_2",
            "killed_var_2",
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

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def websocket_handler_with_mocks(
    mock_database, mock_redis, mock_early_kill_monitor, mock_fatigue_detector
):
    """Create WebSocket handler with all dependencies mocked."""
    from services.dashboard_api.websocket_handler import VariantDashboardWebSocket
    from services.dashboard_api.variant_metrics import VariantMetricsAPI

    with patch(
        "services.dashboard_api.variant_metrics.get_db_connection",
        return_value=mock_database,
    ):
        with patch(
            "services.dashboard_api.variant_metrics.get_redis_connection",
            return_value=mock_redis,
        ):
            handler = VariantDashboardWebSocket()

            # Setup metrics API with mocks
            metrics_api = VariantMetricsAPI()
            metrics_api.early_kill_monitor = mock_early_kill_monitor
            metrics_api.fatigue_detector = mock_fatigue_detector
            handler.metrics_api = metrics_api

            return handler


@pytest.fixture
def event_processor_with_mocks(websocket_handler_with_mocks):
    """Create event processor with mocked dependencies."""
    from services.dashboard_api.event_processor import DashboardEventProcessor

    return DashboardEventProcessor(websocket_handler_with_mocks)


@pytest.fixture
def sample_variant_data():
    """Provide sample variant data for tests."""
    now = datetime.now()
    return {
        "id": "sample_var_1",
        "persona_id": "ai-jesus",
        "content": "Sample variant content for testing",
        "predicted_er": 0.065,
        "actual_er": 0.062,
        "posted_at": now - timedelta(hours=2),
        "status": "active",
        "interaction_count": 150,
        "view_count": 2400,
        "live_metrics": {"engagement_rate": 0.062, "interactions": 150, "views": 2400},
        "time_since_post": {"hours_active": 2.0, "minutes_active": 120},
        "performance_vs_prediction": {
            "absolute_delta": -0.003,
            "relative_delta": -0.046,
            "status": "underperforming",
        },
    }


@pytest.fixture
def sample_dashboard_data(sample_variant_data):
    """Provide complete dashboard data structure for tests."""
    return {
        "summary": {
            "total_variants": 10,
            "avg_engagement_rate": 0.058,
            "active_count": 8,
            "killed_count": 2,
            "performance_trend": "stable",
            "prediction_accuracy": 0.85,
        },
        "active_variants": [sample_variant_data],
        "performance_leaders": [
            {
                "id": "leader_var_1",
                "content": "Top performing variant",
                "actual_er": 0.095,
                "predicted_er": 0.072,
                "outperformance": 0.32,
            }
        ],
        "early_kills_today": {
            "kills_today": 3,
            "avg_time_to_kill_minutes": 5.2,
            "kill_reasons": {"low_engagement": 2, "negative_sentiment": 1},
        },
        "pattern_fatigue_warnings": [
            {
                "pattern_id": "curiosity_gap",
                "fatigue_score": 0.82,
                "warning_level": "high",
                "recommendation": "Switch to controversy patterns",
            }
        ],
        "optimization_opportunities": [
            {
                "type": "prediction_calibration",
                "title": "High Early Kill Rate",
                "description": "Consider recalibrating prediction model",
                "priority": "high",
                "estimated_impact": "15% improvement in success rate",
            }
        ],
        "real_time_feed": [
            {
                "event_type": "early_kill",
                "variant_id": "killed_var_1",
                "timestamp": datetime.now().isoformat(),
                "details": {"reason": "low_engagement", "final_er": 0.025},
            }
        ],
    }


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Generate large dataset for performance testing."""
    now = datetime.now()
    return [
        {
            "id": f"perf_var_{i}",
            "persona_id": "perf-test-persona",
            "content": f"Performance test variant {i}",
            "predicted_er": 0.05 + (i % 10) * 0.001,
            "actual_er": 0.05 + (i % 8) * 0.002,
            "posted_at": now - timedelta(hours=i % 24),
            "status": "active",
            "interaction_count": 100 + i,
            "view_count": 2000 + i * 10,
        }
        for i in range(1000)  # 1000 test variants
    ]


# Test markers
pytestmark = [
    pytest.mark.asyncio,
]


# Custom assertions
class DashboardAssertions:
    """Custom assertions for dashboard testing."""

    @staticmethod
    def assert_valid_dashboard_data(data):
        """Assert that dashboard data has valid structure."""
        required_sections = [
            "summary",
            "active_variants",
            "performance_leaders",
            "early_kills_today",
            "pattern_fatigue_warnings",
            "optimization_opportunities",
            "real_time_feed",
        ]

        for section in required_sections:
            assert section in data, f"Missing required section: {section}"

        # Validate summary
        summary = data["summary"]
        assert "total_variants" in summary
        assert "avg_engagement_rate" in summary
        assert isinstance(summary["total_variants"], int)
        assert isinstance(summary["avg_engagement_rate"], (int, float))

        # Validate variants
        for variant in data["active_variants"]:
            assert "id" in variant
            assert "content" in variant
            assert "predicted_er" in variant
            assert "live_metrics" in variant

    @staticmethod
    def assert_valid_websocket_message(message):
        """Assert that WebSocket message has valid structure."""
        assert "type" in message
        assert "timestamp" in message

        if message["type"] == "initial_data":
            assert "data" in message
            DashboardAssertions.assert_valid_dashboard_data(message["data"])
        elif message["type"] == "variant_update":
            assert "data" in message
            assert "event_type" in message["data"]
        elif message["type"] == "error":
            assert "message" in message

    @staticmethod
    def assert_performance_within_limits(execution_time, max_time, operation_name):
        """Assert that operation completed within performance limits."""
        assert execution_time < max_time, (
            f"{operation_name} took {execution_time:.3f}s, expected < {max_time}s"
        )


@pytest.fixture
def dashboard_assertions():
    """Provide dashboard assertion helpers."""
    return DashboardAssertions


# Cleanup utilities
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup resources after each test."""
    yield
    # Cleanup logic here if needed
    pass


# Configuration for different test environments
@pytest.fixture(scope="session")
def test_config():
    """Test configuration."""
    return {
        "database": {"max_connections": 10, "timeout": 5.0},
        "redis": {"max_connections": 10, "timeout": 2.0},
        "websocket": {"max_connections_per_persona": 100, "broadcast_timeout": 1.0},
        "performance": {
            "max_query_time": 1.0,
            "max_broadcast_time": 0.5,
            "max_concurrent_connections": 1000,
        },
    }


# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios."""

    @staticmethod
    def generate_variants(count, persona_id="test-persona", base_time=None):
        """Generate variant test data."""
        if base_time is None:
            base_time = datetime.now()

        return [
            {
                "id": f"gen_var_{i}",
                "persona_id": persona_id,
                "content": f"Generated variant {i}",
                "predicted_er": 0.05 + (i % 10) * 0.005,
                "actual_er": 0.05 + (i % 8) * 0.006,
                "posted_at": base_time - timedelta(hours=i % 24),
                "status": "active",
                "interaction_count": 100 + i * 2,
                "view_count": 2000 + i * 15,
            }
            for i in range(count)
        ]

    @staticmethod
    def generate_websocket_connections(count):
        """Generate mock WebSocket connections."""
        return [AsyncMock() for _ in range(count)]

    @staticmethod
    def generate_events(count, persona_id="test-persona", event_types=None):
        """Generate event data for testing."""
        if event_types is None:
            event_types = ["performance_update", "early_kill"]

        events = []
        for i in range(count):
            event_type = event_types[i % len(event_types)]

            if event_type == "performance_update":
                events.append(
                    {
                        "event_type": "performance_update",
                        "variant_id": f"event_var_{i}",
                        "persona_id": persona_id,
                        "engagement_rate": 0.05 + (i % 20) * 0.002,
                        "interaction_count": 100 + i,
                        "updated_at": datetime.now().isoformat(),
                    }
                )
            elif event_type == "early_kill":
                events.append(
                    {
                        "event_type": "early_kill",
                        "variant_id": f"event_var_{i}",
                        "persona_id": persona_id,
                        "reason": ["low_engagement", "negative_sentiment"][i % 2],
                        "final_engagement_rate": 0.02 + (i % 5) * 0.005,
                        "killed_at": datetime.now().isoformat(),
                    }
                )

        return events


@pytest.fixture
def test_data_generator():
    """Provide test data generator."""
    return TestDataGenerator
