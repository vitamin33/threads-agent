"""
FinOps Engine Main Entry Point - Real-time Cost Data Collection Engine (CRA-240)

Demo usage of the ViralFinOpsEngine for cost tracking.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from viral_finops_engine import ViralFinOpsEngine


async def demo_cost_tracking():
    """Demonstrate complete cost tracking workflow."""
    print("🚀 Starting FinOps Engine Demo...")

    # Initialize the engine
    config = {
        "cost_threshold_per_post": 0.02,  # $0.02 target
        "alert_threshold_multiplier": 2.0,  # Alert at $0.04
        "storage_latency_target_ms": 500,
    }

    engine = ViralFinOpsEngine(config=config)

    # Demo post generation cost tracking
    post_id = "demo_post_001"
    persona_id = "ai_jesus"

    print(f"📊 Tracking costs for post: {post_id}")

    # 1. Track OpenAI costs
    print("💰 Tracking OpenAI API costs...")
    await engine.track_openai_cost(
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=500,
        operation="hook_generation",
        persona_id=persona_id,
        post_id=post_id,
    )

    await engine.track_openai_cost(
        model="gpt-3.5-turbo-0125",
        input_tokens=1500,
        output_tokens=800,
        operation="body_generation",
        persona_id=persona_id,
        post_id=post_id,
    )

    # 2. Track infrastructure costs
    print("🏗️ Tracking infrastructure costs...")
    await engine.track_infrastructure_cost(
        resource_type="kubernetes",
        service="persona_runtime",
        cpu_cores=1.0,
        memory_gb=2.0,
        duration_minutes=5,
        operation="post_generation",
        persona_id=persona_id,
        post_id=post_id,
    )

    # 3. Track vector DB costs
    print("🔍 Tracking vector DB costs...")
    await engine.track_vector_db_cost(
        operation="similarity_search",
        query_count=1000,
        collection=f"posts_{persona_id}",
        persona_id=persona_id,
        post_id=post_id,
    )

    # 4. Calculate total cost
    total_cost = await engine.calculate_total_post_cost(post_id)

    print(f"💵 Total cost for post {post_id}: ${total_cost:.4f}")
    print(f"🎯 Target: ${config['cost_threshold_per_post']:.2f}")
    print(
        f"⚠️ Alert threshold: ${config['cost_threshold_per_post'] * config['alert_threshold_multiplier']:.2f}"
    )

    # 5. Show emitted metrics
    metrics = engine.prometheus_client.get_emitted_metrics()
    print(f"📈 Total metrics emitted: {len(metrics)}")

    # Show cost breakdown by type
    openai_metrics = [m for m in metrics if "openai" in m["metric_name"]]
    k8s_metrics = [m for m in metrics if "kubernetes" in m["metric_name"]]
    vector_metrics = [m for m in metrics if "vector" in m["metric_name"]]

    print(f"   - OpenAI metrics: {len(openai_metrics)}")
    print(f"   - Kubernetes metrics: {len(k8s_metrics)}")
    print(f"   - Vector DB metrics: {len(vector_metrics)}")

    # Show cost per post metric
    cost_per_post_metrics = [
        m for m in metrics if m["metric_name"] == "cost_per_post_usd"
    ]
    if cost_per_post_metrics:
        print(f"📊 Cost per post metric: ${cost_per_post_metrics[0]['value']:.4f}")

    # Check for alerts
    alert_metrics = [m for m in metrics if "threshold_breach" in m["metric_name"]]
    if alert_metrics:
        active_alerts = [m for m in alert_metrics if m["value"] == 1]
        print(f"🚨 Active alerts: {len(active_alerts)}")
    else:
        print("✅ No cost threshold alerts")

    print("✨ FinOps Engine Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo_cost_tracking())
