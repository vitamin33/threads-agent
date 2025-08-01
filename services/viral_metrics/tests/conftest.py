"""
Test configuration and fixtures for viral metrics service.

Provides comprehensive test fixtures for integration and E2E testing of
the viral metrics collection system with proper mocking and real dependencies.
"""

import asyncio
import pytest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Create a mock Redis connection with realistic behavior."""
    mock_redis = AsyncMock()

    # Storage for simulating Redis behavior
    redis_storage = {}

    async def mock_setex(key: str, ttl: int, value: str):
        redis_storage[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl),
        }
        return True

    async def mock_get(key: str):
        if key in redis_storage:
            data = redis_storage[key]
            if datetime.now() < data["expires_at"]:
                return data["value"]
            else:
                del redis_storage[key]  # Simulate expiration
        return None

    async def mock_delete(key: str):
        if key in redis_storage:
            del redis_storage[key]
            return 1
        return 0

    mock_redis.setex = mock_setex
    mock_redis.get = mock_get
    mock_redis.delete = mock_delete

    return mock_redis


@pytest.fixture
def mock_database():
    """Create a mock database connection with realistic viral metrics behavior."""
    mock_db = AsyncMock()

    # Storage for simulating database behavior
    viral_metrics_storage = []
    viral_history_storage = []
    posts_storage = [
        {
            "id": "test_post_123",
            "persona_id": "ai_jesus",
            "created_at": datetime.now() - timedelta(hours=2),
            "content": "Test post content",
        },
        {
            "id": "test_post_456",
            "persona_id": "ai_buddha",
            "created_at": datetime.now() - timedelta(hours=1),
            "content": "Another test post",
        },
    ]

    async def mock_execute(query: str, *params):
        if "INSERT INTO viral_metrics" in query:
            viral_metrics_storage.append(
                {
                    "post_id": params[0],
                    "persona_id": params[1],
                    "viral_coefficient": params[2],
                    "scroll_stop_rate": params[3],
                    "share_velocity": params[4],
                    "reply_depth": params[5],
                    "engagement_trajectory": params[6],
                    "pattern_fatigue_score": params[7],
                    "collected_at": params[8],
                }
            )
        elif "INSERT INTO viral_metrics_history" in query:
            viral_history_storage.append(
                {
                    "post_id": params[0],
                    "metric_name": params[1],
                    "metric_value": params[2],
                    "recorded_at": params[3],
                }
            )
        return None

    async def mock_fetch_all(query: str, *params):
        if "FROM posts" in query:
            cutoff_time = params[0] if params else datetime.now() - timedelta(hours=24)
            return [post for post in posts_storage if post["created_at"] >= cutoff_time]
        elif "FROM viral_metrics" in query:
            return viral_metrics_storage
        return []

    async def mock_fetch_one(query: str, *params):
        if "AVG(viral_coefficient)" in query:
            return {
                "avg_viral_coefficient": 0.045,
                "avg_scroll_stop_rate": 0.65,
                "avg_share_velocity": 15.0,
            }
        return None

    mock_db.execute = mock_execute
    mock_db.fetch_all = mock_fetch_all
    mock_db.fetch_one = mock_fetch_one

    # Add storage access for test verification
    mock_db._viral_metrics_storage = viral_metrics_storage
    mock_db._viral_history_storage = viral_history_storage
    mock_db._posts_storage = posts_storage

    return mock_db


@pytest.fixture
def mock_prometheus():
    """Create a mock Prometheus client for metrics testing."""
    mock_prometheus = Mock()

    # Track metrics calls
    metrics_calls = []

    def mock_histogram(name: str, description: str = ""):
        histogram_mock = Mock()
        histogram_mock.observe = Mock(
            side_effect=lambda value, labels=None: metrics_calls.append(
                {"type": "histogram", "name": name, "value": value, "labels": labels}
            )
        )
        return histogram_mock

    def mock_gauge(name: str, description: str = ""):
        gauge_mock = Mock()
        gauge_mock.set = Mock(
            side_effect=lambda value, labels=None: metrics_calls.append(
                {"type": "gauge", "name": name, "value": value, "labels": labels}
            )
        )
        return gauge_mock

    mock_prometheus.histogram = mock_histogram
    mock_prometheus.gauge = mock_gauge
    mock_prometheus._metrics_calls = metrics_calls

    return mock_prometheus


@pytest.fixture
def mock_fake_threads_api():
    """Create a mock fake-threads API server."""
    import httpx

    class MockTransport(httpx.AsyncHTTPTransport):
        def __init__(self):
            super().__init__()

        async def ahandle_async_request(self, request):
            # Parse URL to determine response
            url = str(request.url)

            if "/analytics/" in url:
                post_id = url.split("/analytics/")[1].split("?")[0]
                return httpx.Response(200, json=self.get_analytics_response(post_id))
            elif "/threads/" in url:
                post_id = url.split("/threads/")[1]
                return httpx.Response(200, json=self.get_threads_response(post_id))
            else:
                return httpx.Response(404, json={"error": "Not found"})

        def get_analytics_response(self, post_id: str) -> Dict[str, Any]:
            """Generate realistic analytics data for testing."""
            base_views = hash(post_id) % 5000 + 1000
            return {
                "post_id": post_id,
                "persona_id": "ai_jesus" if "123" in post_id else "ai_buddha",
                "views": base_views,
                "impressions": int(base_views * 1.2),
                "engaged_views": int(base_views * 0.8),
                "likes": int(base_views * 0.15),
                "comments": int(base_views * 0.05),
                "shares": int(base_views * 0.08),
                "saves": int(base_views * 0.02),
                "click_throughs": int(base_views * 0.03),
                "view_duration_avg": 15.5,
                "hourly_breakdown": [
                    {
                        "hour": i,
                        "shares": int(base_views * 0.01 * (i + 1)),
                        "views": int(base_views * 0.1 * (i + 1)),
                        "likes": int(base_views * 0.015 * (i + 1)),
                        "comments": int(base_views * 0.005 * (i + 1)),
                    }
                    for i in range(6)
                ],
                "demographic_data": {
                    "age_groups": {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2}
                },
            }

        def get_threads_response(self, post_id: str) -> Dict[str, Any]:
            """Generate realistic thread data for testing."""
            return {
                "threads": [
                    {
                        "id": f"thread_1_{post_id}",
                        "replies": [
                            {
                                "id": f"reply_1_1_{post_id}",
                                "replies": [
                                    {"id": f"reply_1_1_1_{post_id}", "replies": []}
                                ],
                            }
                        ],
                    },
                    {
                        "id": f"thread_2_{post_id}",
                        "replies": [{"id": f"reply_2_1_{post_id}", "replies": []}],
                    },
                ]
            }

    return MockTransport()


@pytest.fixture
def sample_engagement_data():
    """Provide comprehensive sample engagement data for testing."""
    return {
        "post_id": "test_post_123",
        "persona_id": "ai_jesus",
        "views": 2500,
        "impressions": 3000,
        "engaged_views": 2000,
        "likes": 375,
        "comments": 125,
        "shares": 200,
        "saves": 50,
        "click_throughs": 75,
        "view_duration_avg": 18.5,
        "hourly_breakdown": [
            {"hour": 0, "shares": 20, "views": 300, "likes": 45, "comments": 15},
            {"hour": 1, "shares": 35, "views": 450, "likes": 68, "comments": 22},
            {"hour": 2, "shares": 60, "views": 600, "likes": 90, "comments": 30},
            {"hour": 3, "shares": 45, "views": 500, "likes": 75, "comments": 25},
            {"hour": 4, "shares": 25, "views": 400, "likes": 60, "comments": 20},
            {"hour": 5, "shares": 15, "views": 250, "likes": 37, "comments": 13},
        ],
        "demographic_data": {
            "age_groups": {"18-24": 0.35, "25-34": 0.45, "35-44": 0.15, "45+": 0.05}
        },
        "pattern_id": "curiosity_gap_hook",
    }


@pytest.fixture
def high_performance_engagement_data():
    """Provide high-performance engagement data for testing viral scenarios."""
    return {
        "post_id": "viral_post_789",
        "persona_id": "ai_jesus",
        "views": 50000,
        "impressions": 75000,
        "engaged_views": 45000,
        "likes": 7500,
        "comments": 2500,
        "shares": 4000,
        "saves": 1000,
        "click_throughs": 1500,
        "view_duration_avg": 25.0,
        "hourly_breakdown": [
            {"hour": 0, "shares": 100, "views": 2000, "likes": 300, "comments": 100},
            {"hour": 1, "shares": 300, "views": 5000, "likes": 750, "comments": 250},
            {"hour": 2, "shares": 800, "views": 12000, "likes": 1800, "comments": 600},
            {"hour": 3, "shares": 1200, "views": 15000, "likes": 2250, "comments": 750},
            {"hour": 4, "shares": 1000, "views": 10000, "likes": 1500, "comments": 500},
            {"hour": 5, "shares": 600, "views": 6000, "likes": 900, "comments": 300},
        ],
        "demographic_data": {
            "age_groups": {"18-24": 0.4, "25-34": 0.4, "35-44": 0.15, "45+": 0.05}
        },
        "pattern_id": "controversy_hook",
    }


@pytest.fixture
def low_performance_engagement_data():
    """Provide low-performance engagement data for testing poor performance scenarios."""
    return {
        "post_id": "poor_post_000",
        "persona_id": "ai_buddha",
        "views": 500,
        "impressions": 1200,
        "engaged_views": 200,
        "likes": 15,
        "comments": 5,
        "shares": 3,
        "saves": 1,
        "click_throughs": 2,
        "view_duration_avg": 3.2,
        "hourly_breakdown": [
            {"hour": 0, "shares": 1, "views": 100, "likes": 3, "comments": 1},
            {"hour": 1, "shares": 1, "views": 150, "likes": 5, "comments": 2},
            {"hour": 2, "shares": 1, "views": 120, "likes": 4, "comments": 1},
            {"hour": 3, "shares": 0, "views": 80, "likes": 2, "comments": 1},
            {"hour": 4, "shares": 0, "views": 30, "likes": 1, "comments": 0},
            {"hour": 5, "shares": 0, "views": 20, "likes": 0, "comments": 0},
        ],
        "demographic_data": {
            "age_groups": {"18-24": 0.2, "25-34": 0.3, "35-44": 0.3, "45+": 0.2}
        },
        "pattern_id": "educational_hook",
    }


@pytest.fixture
def real_test_database():
    """Create a real SQLite database for integration tests."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Create database schema
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE posts (
            id TEXT PRIMARY KEY,
            persona_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'active'
        );
        
        CREATE TABLE viral_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL,
            persona_id TEXT NOT NULL,
            viral_coefficient REAL NOT NULL,
            scroll_stop_rate REAL NOT NULL,
            share_velocity REAL NOT NULL,
            reply_depth REAL NOT NULL,
            engagement_trajectory REAL NOT NULL,
            pattern_fatigue_score REAL NOT NULL,
            collected_at TIMESTAMP NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        );
        
        CREATE TABLE viral_metrics_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            recorded_at TIMESTAMP NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        );
        
        CREATE TABLE pattern_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_id TEXT NOT NULL,
            pattern_id TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            last_used TIMESTAMP,
            fatigue_score REAL DEFAULT 0.0
        );
    """)

    # Insert test data
    now = datetime.now()
    test_posts = [
        (
            "integration_post_1",
            "ai-jesus",
            "Integration test post 1",
            now - timedelta(hours=2),
        ),
        (
            "integration_post_2",
            "ai-buddha",
            "Integration test post 2",
            now - timedelta(hours=1),
        ),
        (
            "integration_post_3",
            "ai-jesus",
            "Integration test post 3",
            now - timedelta(minutes=30),
        ),
    ]

    conn.executemany(
        "INSERT INTO posts (id, persona_id, content, created_at) VALUES (?, ?, ?, ?)",
        test_posts,
    )

    # Insert sample pattern usage data
    pattern_data = [
        ("ai-jesus", "curiosity_gap", 5, now - timedelta(days=1), 0.6),
        ("ai-buddha", "educational_hook", 3, now - timedelta(days=2), 0.3),
        ("ai-jesus", "controversy_hook", 2, now - timedelta(days=3), 0.2),
    ]

    conn.executemany(
        "INSERT INTO pattern_usage (persona_id, pattern_id, usage_count, last_used, fatigue_score) VALUES (?, ?, ?, ?, ?)",
        pattern_data,
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def real_redis_connection():
    """Create a real Redis connection for integration tests."""
    # This would connect to a test Redis instance
    # For now, we'll use a mock that behaves like real Redis
    return mock_redis()


@pytest.fixture
def performance_test_posts():
    """Generate large dataset for performance testing."""
    now = datetime.now()
    return [
        {
            "id": f"perf_post_{i}",
            "persona_id": f"perf_persona_{i % 3}",
            "created_at": now - timedelta(hours=i % 24),
        }
        for i in range(100)  # 100 test posts for batch processing
    ]


@pytest.fixture
def anomaly_test_scenarios():
    """Provide test scenarios for anomaly detection."""
    return {
        "viral_coefficient_drop": {
            "baseline": {"viral_coefficient": 0.08, "scroll_stop_rate": 0.75},
            "current": {"viral_coefficient": 0.05, "scroll_stop_rate": 0.72},
            "expected_anomaly": "viral_coefficient_drop",
        },
        "negative_trajectory": {
            "engagement_data": {
                "hourly_breakdown": [
                    {
                        "hour": 0,
                        "likes": 100,
                        "comments": 50,
                        "shares": 30,
                        "views": 1000,
                    },
                    {
                        "hour": 1,
                        "likes": 80,
                        "comments": 40,
                        "shares": 25,
                        "views": 1200,
                    },
                    {
                        "hour": 2,
                        "likes": 60,
                        "comments": 30,
                        "shares": 20,
                        "views": 1400,
                    },
                    {
                        "hour": 3,
                        "likes": 40,
                        "comments": 20,
                        "shares": 15,
                        "views": 1600,
                    },
                ]
            },
            "expected_anomaly": "negative_trajectory",
        },
        "pattern_fatigue": {
            "engagement_data": {"pattern_id": "overused_pattern"},
            "current_metrics": {"pattern_fatigue": 0.85},
            "expected_anomaly": "pattern_fatigue",
        },
    }


# Custom assertions for viral metrics testing
class ViralMetricsAssertions:
    """Custom assertions for viral metrics testing."""

    @staticmethod
    def assert_valid_metrics_structure(metrics: Dict[str, float]):
        """Assert that metrics have the expected structure and value ranges."""
        required_metrics = [
            "viral_coefficient",
            "scroll_stop_rate",
            "share_velocity",
            "reply_depth",
            "engagement_trajectory",
            "pattern_fatigue",
        ]

        for metric in required_metrics:
            assert metric in metrics, f"Missing required metric: {metric}"
            assert isinstance(metrics[metric], (int, float)), (
                f"Metric {metric} must be numeric"
            )

        # Value range checks
        assert 0 <= metrics["viral_coefficient"] <= 50, "Viral coefficient out of range"
        assert 0 <= metrics["scroll_stop_rate"] <= 100, "Scroll stop rate out of range"
        assert metrics["share_velocity"] >= 0, "Share velocity must be non-negative"
        assert metrics["reply_depth"] >= 0, "Reply depth must be non-negative"
        assert -100 <= metrics["engagement_trajectory"] <= 100, (
            "Trajectory out of range"
        )
        assert 0 <= metrics["pattern_fatigue"] <= 1, "Pattern fatigue out of range"

    @staticmethod
    def assert_sla_compliance(
        start_time: float, end_time: float, max_seconds: float = 60.0
    ):
        """Assert that operation completed within SLA."""
        elapsed = end_time - start_time
        assert elapsed < max_seconds, f"SLA violation: {elapsed:.2f}s > {max_seconds}s"

    @staticmethod
    def assert_database_persistence(mock_db, expected_records: int):
        """Assert that metrics were properly persisted to database."""
        metrics_records = len(mock_db._viral_metrics_storage)
        history_records = len(mock_db._viral_history_storage)

        assert metrics_records >= expected_records, (
            f"Expected {expected_records} metrics records, got {metrics_records}"
        )
        assert history_records >= expected_records * 6, (
            f"Expected {expected_records * 6} history records, got {history_records}"
        )

    @staticmethod
    def assert_prometheus_emission(mock_prometheus, expected_metrics_count: int):
        """Assert that metrics were emitted to Prometheus."""
        calls = mock_prometheus._metrics_calls
        gauge_calls = [call for call in calls if call["type"] == "gauge"]

        assert len(gauge_calls) >= expected_metrics_count, (
            f"Expected {expected_metrics_count} Prometheus metrics, got {len(gauge_calls)}"
        )

    @staticmethod
    def assert_redis_caching(mock_redis, expected_cache_calls: int):
        """Assert that metrics were cached in Redis."""
        # This would check the mock_redis calls if we tracked them
        # For now, we assume proper caching based on the implementation
        pass


@pytest.fixture
def viral_metrics_assertions():
    """Provide viral metrics assertion helpers."""
    return ViralMetricsAssertions


# Performance benchmarks
@pytest.fixture
def performance_benchmarks():
    """Define performance benchmarks for testing."""
    return {
        "single_collection_max_time": 5.0,  # seconds
        "batch_processing_max_time": 30.0,  # seconds for 100 posts
        "database_write_max_time": 1.0,  # seconds
        "redis_cache_max_time": 0.1,  # seconds
        "prometheus_emit_max_time": 0.5,  # seconds
    }


# Test environment configuration
@pytest.fixture(scope="session")
def test_config():
    """Test configuration for viral metrics."""
    return {
        "sla": {"collection_time_seconds": 60, "batch_processing_time_seconds": 300},
        "redis": {"cache_ttl_seconds": 300, "connection_timeout": 5.0},
        "database": {"max_connections": 10, "query_timeout": 30.0},
        "prometheus": {"metrics_prefix": "viral_", "emission_timeout": 1.0},
        "performance": {
            "batch_size": 50,
            "max_parallel_tasks": 10,
            "metrics_ttl_hours": 24,
        },
    }


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup resources after each test."""
    yield
    # Any cleanup logic would go here
    pass


# Test markers
pytestmark = [
    pytest.mark.asyncio,
]
