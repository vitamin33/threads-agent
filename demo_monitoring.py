#!/usr/bin/env python3
"""
Demo script to show Prometheus metrics for interviews
Run this to demonstrate the monitoring capabilities
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Business Metrics
engagement_rate = Gauge("posts_engagement_rate", "Current engagement rate of posts")
cost_per_follow = Gauge("cost_per_follow_dollars", "Cost per follower in USD")
revenue_projection = Gauge("revenue_projection_monthly", "Monthly revenue projection")

# Technical Metrics
request_latency = Histogram(
    "request_latency_seconds", "Request latency in seconds", ["service", "endpoint"]
)
token_usage = Counter("token_usage_total", "Total tokens used", ["model", "service"])
error_rate = Counter(
    "request_errors_total", "Total request errors", ["service", "error_type"]
)

# Performance Metrics
active_conversations = Gauge(
    "active_conversations", "Number of active DM conversations"
)
cache_hit_rate = Gauge("cache_hit_rate", "Cache hit rate percentage")
db_query_duration = Histogram(
    "database_query_duration_seconds", "Database query duration", ["query_type"]
)


def simulate_metrics():
    """Simulate realistic metrics for demo"""

    # Set business KPIs
    engagement_rate.set(6.2)  # 6.2% engagement (above 6% target)
    cost_per_follow.set(0.009)  # $0.009 per follow (below $0.01 target)
    revenue_projection.set(22500)  # $22.5k MRR

    # Record some API calls
    request_latency.labels(service="orchestrator", endpoint="/task").observe(0.145)
    request_latency.labels(service="viral_engine", endpoint="/analyze").observe(0.089)
    request_latency.labels(service="conversation_engine", endpoint="/respond").observe(
        0.234
    )

    # Token usage
    token_usage.labels(model="gpt-4o", service="persona_runtime").inc(1250)
    token_usage.labels(model="gpt-3.5-turbo", service="conversation_engine").inc(850)

    # Active conversations
    active_conversations.set(47)

    # Cache performance
    cache_hit_rate.set(87.5)

    # Database queries
    db_query_duration.labels(query_type="select").observe(0.012)
    db_query_duration.labels(query_type="insert").observe(0.023)
    db_query_duration.labels(query_type="update").observe(0.018)


def main():
    print("🚀 Threads-Agent Monitoring Demo")
    print("=" * 50)
    print()

    # Simulate metrics
    simulate_metrics()

    # Generate Prometheus format
    metrics_output = generate_latest().decode("utf-8")

    print("📊 Current Metrics (Prometheus Format):")
    print("-" * 50)

    # Show key metrics in readable format
    for line in metrics_output.split("\n"):
        if line and not line.startswith("#"):
            print(line)

    print()
    print("🎯 Business KPIs:")
    print("  • Engagement Rate: 6.2% (✅ > 6% target)")
    print("  • Cost per Follow: $0.009 (✅ < $0.01 target)")
    print("  • Monthly Revenue: $22.5k (📈 trending up)")
    print()
    print("⚡ Performance Metrics:")
    print("  • Average Latency: 145ms (✅ < 500ms SLA)")
    print("  • Cache Hit Rate: 87.5% (✅ good)")
    print("  • Active DM Conversations: 47")
    print()
    print("🔗 In production, these metrics are:")
    print("  • Scraped by Prometheus every 15s")
    print("  • Visualized in Grafana dashboards")
    print("  • Alert on SLA violations via AlertManager")
    print()
    print("💡 Try: curl localhost:8080/metrics (when services are running)")


if __name__ == "__main__":
    main()
