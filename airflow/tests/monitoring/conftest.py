"""
Pytest configuration and fixtures for Airflow monitoring tests.

This module provides shared fixtures, mocks, and configuration for all
monitoring integration tests including Prometheus, Grafana, AlertManager,
and KPI monitoring components.
"""

import pytest
import os
from unittest.mock import MagicMock, patch, mock_open

# Import optional dependencies with fallback
try:
    import requests_mock
except ImportError:
    requests_mock = None

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

# Disable langsmith/langchain tracing for tests
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"


@pytest.fixture(scope="session")
def monitoring_config():
    """Global monitoring system configuration."""
    return {
        "prometheus": {
            "url": "http://prometheus:9090",
            "push_gateway": "http://pushgateway:9091",
            "scrape_interval": "30s",
            "evaluation_interval": "30s",
        },
        "grafana": {
            "url": "http://grafana:3000",
            "admin_user": "admin",
            "admin_password": "admin",
            "api_key": "test-grafana-api-key",
            "organization": "Viral Learning",
        },
        "alertmanager": {
            "url": "http://alertmanager:9093",
            "api_version": "v2",
            "cluster_peers": ["alertmanager-1:9094", "alertmanager-2:9094"],
        },
        "notification_channels": {
            "slack_webhook": "https://hooks.slack.com/services/test/test/test",
            "email_smtp": "smtp.gmail.com:587",
            "pagerduty_key": "test-pagerduty-integration-key",
        },
    }


@pytest.fixture
def mock_prometheus_response():
    """Mock Prometheus API response data."""
    return {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {
                        "__name__": "posts_engagement_rate",
                        "persona_id": "tech_influencer_001",
                        "instance": "orchestrator:8080",
                    },
                    "value": [1642611600, "0.067"],
                },
                {
                    "metric": {
                        "__name__": "cost_per_follow_dollars",
                        "persona_id": "tech_influencer_001",
                        "instance": "orchestrator:8080",
                    },
                    "value": [1642611600, "0.009"],
                },
            ],
        },
    }


@pytest.fixture
def mock_grafana_dashboard():
    """Mock Grafana dashboard configuration."""
    return {
        "dashboard": {
            "id": 1,
            "uid": "viral-learning-kpis",
            "title": "Viral Learning KPIs",
            "tags": ["airflow", "viral-learning", "business"],
            "timezone": "UTC",
            "panels": [
                {
                    "id": 1,
                    "title": "Engagement Rate",
                    "type": "stat",
                    "targets": [{"expr": "posts_engagement_rate", "refId": "A"}],
                    "fieldConfig": {
                        "defaults": {
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "yellow", "value": 0.04},
                                    {"color": "green", "value": 0.06},
                                ]
                            }
                        }
                    },
                }
            ],
            "time": {"from": "now-24h", "to": "now"},
            "refresh": "30s",
        },
        "meta": {
            "type": "db",
            "canSave": True,
            "canEdit": True,
            "canAdmin": True,
            "canStar": True,
            "slug": "viral-learning-kpis",
            "url": "/d/viral-learning-kpis/viral-learning-kpis",
            "expires": "0001-01-01T00:00:00Z",
            "created": "2024-01-15T10:00:00Z",
            "updated": "2024-01-15T15:30:00Z",
            "updatedBy": "admin",
            "createdBy": "admin",
            "version": 1,
        },
    }


@pytest.fixture
def mock_alertmanager_alerts():
    """Mock AlertManager alerts data."""
    return [
        {
            "labels": {
                "alertname": "LowEngagementRate",
                "severity": "warning",
                "service": "viral-learning",
                "persona_id": "tech_influencer_001",
            },
            "annotations": {
                "summary": "Engagement rate below 4%",
                "description": "Posts engagement rate has been below 4% for 15 minutes",
            },
            "startsAt": "2024-01-15T10:00:00Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "http://prometheus:9090/graph?g0.expr=posts_engagement_rate+%3C+0.04",
            "fingerprint": "123456789abcdef",
        },
        {
            "labels": {
                "alertname": "HighCostPerFollow",
                "severity": "critical",
                "service": "viral-learning",
                "persona_id": "tech_influencer_001",
            },
            "annotations": {
                "summary": "Cost per follow exceeds $0.025",
                "description": "Cost per follow critically high - pause campaigns",
            },
            "startsAt": "2024-01-15T11:30:00Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "http://prometheus:9090/graph?g0.expr=cost_per_follow_dollars+%3E+0.025",
            "fingerprint": "abcdef123456789",
        },
    ]


@pytest.fixture
def sample_kpi_time_series():
    """Sample KPI time series data for testing."""
    if pd is None or np is None:
        # Fallback data when pandas/numpy not available
        return {
            "engagement_rate": {
                "timestamps": [
                    "2024-01-01T00:00:00",
                    "2024-01-02T00:00:00",
                    "2024-01-03T00:00:00",
                ],
                "values": [0.065, 0.067, 0.063],
            },
            "cost_per_follow": {
                "timestamps": [
                    "2024-01-01T00:00:00",
                    "2024-01-02T00:00:00",
                    "2024-01-03T00:00:00",
                ],
                "values": [0.009, 0.008, 0.010],
            },
            "viral_coefficient": {
                "timestamps": [
                    "2024-01-01T00:00:00",
                    "2024-01-02T00:00:00",
                    "2024-01-03T00:00:00",
                ],
                "values": [1.25, 1.30, 1.22],
            },
        }

    dates = pd.date_range(start="2024-01-01", end="2024-01-30", freq="D")
    np.random.seed(42)  # For reproducible tests

    return {
        "engagement_rate": {
            "timestamps": [d.isoformat() for d in dates],
            "values": np.random.normal(0.065, 0.01, len(dates))
            .clip(0.02, 0.12)
            .tolist(),
        },
        "cost_per_follow": {
            "timestamps": [d.isoformat() for d in dates],
            "values": np.random.normal(0.009, 0.002, len(dates))
            .clip(0.005, 0.02)
            .tolist(),
        },
        "viral_coefficient": {
            "timestamps": [d.isoformat() for d in dates],
            "values": np.random.normal(1.25, 0.15, len(dates)).clip(0.8, 2.0).tolist(),
        },
    }


@pytest.fixture
def mock_airflow_dag_runs():
    """Mock Airflow DAG run data."""
    return [
        {
            "dag_id": "viral_learning_pipeline",
            "run_id": "scheduled__2024-01-15T10:00:00+00:00",
            "state": "success",
            "execution_date": "2024-01-15T10:00:00Z",
            "start_date": "2024-01-15T10:01:00Z",
            "end_date": "2024-01-15T10:25:00Z",
            "duration": 1440.0,  # 24 minutes
            "tasks": [
                {
                    "task_id": "collect_metrics",
                    "state": "success",
                    "start_date": "2024-01-15T10:01:00Z",
                    "end_date": "2024-01-15T10:03:00Z",
                    "duration": 120.0,
                },
                {
                    "task_id": "generate_content",
                    "state": "success",
                    "start_date": "2024-01-15T10:03:00Z",
                    "end_date": "2024-01-15T10:20:00Z",
                    "duration": 1020.0,
                },
                {
                    "task_id": "analyze_patterns",
                    "state": "success",
                    "start_date": "2024-01-15T10:20:00Z",
                    "end_date": "2024-01-15T10:25:00Z",
                    "duration": 300.0,
                },
            ],
        }
    ]


@pytest.fixture
def mock_service_health_data():
    """Mock service health check data."""
    return {
        "orchestrator": {
            "status": "healthy",
            "response_time_ms": 45,
            "uptime_seconds": 86400,
            "cpu_usage_percent": 15.2,
            "memory_usage_mb": 512,
            "last_check": "2024-01-15T15:30:00Z",
        },
        "viral_scraper": {
            "status": "healthy",
            "response_time_ms": 78,
            "uptime_seconds": 82800,
            "cpu_usage_percent": 23.1,
            "memory_usage_mb": 256,
            "last_check": "2024-01-15T15:30:00Z",
        },
        "viral_engine": {
            "status": "degraded",
            "response_time_ms": 1250,
            "uptime_seconds": 75600,
            "cpu_usage_percent": 85.7,
            "memory_usage_mb": 1024,
            "last_check": "2024-01-15T15:30:00Z",
            "issues": ["high_cpu_usage", "slow_response_time"],
        },
    }


@pytest.fixture
def mock_business_metrics():
    """Mock business metrics data."""
    return {
        "daily_metrics": {
            "posts_created": 24,
            "total_engagement": 3456,
            "new_followers": 89,
            "cost_spent_usd": 1.25,
            "revenue_generated_usd": 0.00,  # Revenue lags behind
            "content_generation_time_minutes": 145,
        },
        "weekly_trends": {
            "engagement_growth_rate": 0.12,
            "follower_growth_rate": 0.08,
            "cost_efficiency_improvement": 0.15,
            "content_quality_score": 0.87,
        },
        "monthly_projections": {
            "projected_followers": 2850,
            "projected_revenue_usd": 18500.00,
            "projected_cost_usd": 285.00,
            "roi_projection": 64.9,
        },
    }


@pytest.fixture
def mock_thompson_sampling_data():
    """Mock Thompson sampling optimization data."""
    return {
        "experiment_id": "content_hook_optimization_001",
        "variants": [
            {
                "id": "curiosity_gap",
                "description": "Curiosity gap hook pattern",
                "trials": 150,
                "successes": 12,
                "success_rate": 0.08,
                "confidence_interval": [0.045, 0.125],
                "posterior_alpha": 13,
                "posterior_beta": 139,
            },
            {
                "id": "controversy",
                "description": "Controversial opinion hook",
                "trials": 140,
                "successes": 7,
                "success_rate": 0.05,
                "confidence_interval": [0.020, 0.095],
                "posterior_alpha": 8,
                "posterior_beta": 134,
            },
            {
                "id": "story_hook",
                "description": "Personal story hook",
                "trials": 160,
                "successes": 18,
                "success_rate": 0.112,
                "confidence_interval": [0.070, 0.170],
                "posterior_alpha": 19,
                "posterior_beta": 143,
            },
        ],
        "best_variant": "story_hook",
        "convergence_probability": 0.89,
        "expected_lift": 0.062,
        "experiment_duration_days": 14,
        "statistical_significance": 0.95,
    }


@pytest.fixture
def mock_alert_rules():
    """Mock alert rule configurations."""
    return [
        {
            "alert": "LowEngagementRate",
            "expr": "posts_engagement_rate < 0.04",
            "for": "15m",
            "labels": {
                "severity": "warning",
                "service": "viral-learning",
                "category": "business-kpi",
            },
            "annotations": {
                "summary": "Engagement rate below 4%",
                "description": "Posts engagement rate has been below 4% for {{ $value }} for 15 minutes",
                "runbook_url": "https://wiki.company.com/runbooks/low-engagement",
            },
        },
        {
            "alert": "CriticalLowEngagementRate",
            "expr": "posts_engagement_rate < 0.02",
            "for": "5m",
            "labels": {
                "severity": "critical",
                "service": "viral-learning",
                "category": "business-kpi",
            },
            "annotations": {
                "summary": "Critical: Engagement rate below 2%",
                "description": "Posts engagement rate critically low at {{ $value }} - immediate action required",
                "runbook_url": "https://wiki.company.com/runbooks/critical-engagement",
            },
        },
        {
            "alert": "AirflowDAGFailure",
            "expr": "increase(airflow_dag_run_failed_total[5m]) > 0",
            "for": "1m",
            "labels": {
                "severity": "critical",
                "service": "airflow",
                "category": "infrastructure",
            },
            "annotations": {
                "summary": "Airflow DAG failure detected",
                "description": "DAG {{ $labels.dag_id }} has failed",
                "runbook_url": "https://wiki.company.com/runbooks/airflow-failures",
            },
        },
    ]


@pytest.fixture
def requests_mock_setup():
    """Set up requests mock for HTTP calls."""
    if requests_mock is None:
        yield None
        return

    with requests_mock.Mocker() as m:
        # Mock Prometheus endpoints
        m.get(
            "http://prometheus:9090/api/v1/query",
            json={"status": "success", "data": {}},
        )
        m.get(
            "http://prometheus:9090/api/v1/query_range",
            json={"status": "success", "data": {}},
        )
        m.post(
            "http://pushgateway:9091/metrics/job/airflow-viral-learning", text="success"
        )

        # Mock Grafana endpoints
        m.get("http://grafana:3000/api/health", json={"status": "ok"})
        m.post(
            "http://grafana:3000/api/dashboards/db", json={"status": "success", "id": 1}
        )
        m.get("http://grafana:3000/api/dashboards/uid/test", json={"dashboard": {}})

        # Mock AlertManager endpoints
        m.get("http://alertmanager:9093/api/v2/status", json={"status": "success"})
        m.get("http://alertmanager:9093/api/v2/alerts", json=[])
        m.post(
            "http://alertmanager:9093/api/v2/silences", json={"silenceID": "test123"}
        )

        # Mock service health endpoints
        m.get("http://orchestrator:8080/health", json={"status": "ok"})
        m.get("http://viral-scraper:8080/health", json={"status": "ok"})
        m.get("http://viral-engine:8080/health", json={"status": "ok"})

        yield m


@pytest.fixture
def mock_file_operations():
    """Mock file system operations for config files."""
    with patch("builtins.open", mock_open()) as mock_file:
        with patch("os.path.exists", return_value=True):
            with patch("os.makedirs"):
                with patch("yaml.safe_load", return_value={}):
                    with patch("yaml.safe_dump"):
                        with patch("json.load", return_value={}):
                            with patch("json.dump"):
                                yield mock_file


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "AIRFLOW_HOME": "/opt/airflow",
        "PROMETHEUS_URL": "http://prometheus:9090",
        "GRAFANA_URL": "http://grafana:3000",
        "ALERTMANAGER_URL": "http://alertmanager:9093",
        "TESTING": "true",
    }

    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def capture_logs(caplog):
    """Capture and provide access to log messages."""
    caplog.set_level("INFO")
    return caplog


class MockAsyncContext:
    """Mock async context manager for testing."""

    def __init__(self, return_value=None):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_async_session():
    """Mock async HTTP session for testing."""
    mock_session = MagicMock()
    mock_session.get.return_value = MockAsyncContext({"status": "success"})
    mock_session.post.return_value = MockAsyncContext({"status": "success"})
    return mock_session
