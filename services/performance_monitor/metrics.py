"""Prometheus metrics for performance monitoring service."""
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Monitoring metrics
MONITORING_STARTED = Counter(
    "performance_monitor_sessions_started_total",
    "Total number of monitoring sessions started",
    ["persona_id"]
)

MONITORING_ACTIVE = Gauge(
    "performance_monitor_sessions_active",
    "Number of currently active monitoring sessions"
)

VARIANTS_KILLED = Counter(
    "performance_monitor_variants_killed_total",
    "Total number of variants killed due to poor performance",
    ["persona_id", "reason"]
)

MONITORING_DURATION = Histogram(
    "performance_monitor_session_duration_seconds",
    "Duration of monitoring sessions in seconds",
    ["outcome"]  # killed, timeout, manual_stop
)

ENGAGEMENT_RATE_AT_KILL = Histogram(
    "performance_monitor_engagement_rate_at_kill",
    "Engagement rate when variant was killed",
    buckets=[0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10]
)

EVALUATION_LATENCY = Histogram(
    "performance_monitor_evaluation_latency_seconds",
    "Time taken to evaluate variant performance"
)


def get_metrics():
    """Generate Prometheus metrics."""
    return generate_latest()