#!/usr/bin/env python3
"""
Demo script to showcase FinOps Engine functionality
"""
import asyncio
import json
from datetime import datetime
from viral_finops_engine import ViralFinOpsEngine

async def main():
    print("=== FinOps Engine Demo ===\n")
    
    # Initialize the engine
    engine = ViralFinOpsEngine()
    
    # Demo 1: Track OpenAI API costs
    print("1. Tracking OpenAI API Costs:")
    print("-" * 40)
    
    # Simulate hook generation
    hook_result = await engine.track_openai_cost(
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=150,
        persona_id="tech_guru",
        post_id="demo_post_001",
        operation="hook_generation"
    )
    hook_cost = hook_result["cost_amount"]
    print(f"✓ Hook generation cost: ${hook_cost:.4f}")
    
    # Simulate body generation
    body_result = await engine.track_openai_cost(
        model="gpt-3.5-turbo-0125",
        input_tokens=1200,
        output_tokens=800,
        persona_id="tech_guru",
        post_id="demo_post_001",
        operation="body_generation"
    )
    body_cost = body_result["cost_amount"]
    print(f"✓ Body generation cost: ${body_cost:.4f}")
    
    # Demo 2: Track infrastructure costs
    print("\n2. Tracking Infrastructure Costs:")
    print("-" * 40)
    
    infra_result = await engine.track_infrastructure_cost(
        resource_type="kubernetes",
        service="persona_runtime",
        cpu_cores=0.5,
        memory_gb=1.0,
        duration_minutes=10,
        operation="post_generation",
        persona_id="tech_guru",
        post_id="demo_post_001"
    )
    infra_cost = infra_result["cost_amount"]
    print(f"✓ Kubernetes compute cost: ${infra_cost:.4f}")
    
    # Demo 3: Calculate total post cost
    print("\n3. Total Post Cost Attribution:")
    print("-" * 40)
    
    total_cost = await engine.calculate_total_post_cost("demo_post_001")
    print(f"✓ Total cost for post: ${total_cost:.4f}")
    
    breakdown = await engine.post_cost_attributor.get_post_cost_breakdown("demo_post_001")
    print("\nCost breakdown by type:")
    for cost_type, amount in breakdown.items():
        if isinstance(amount, (int, float)):
            print(f"  - {cost_type}: ${amount:.4f}")
    
    # Demo 4: Check for anomalies
    print("\n4. Anomaly Detection:")
    print("-" * 40)
    
    # First, let's add some baseline data
    print("Adding baseline cost data...")
    for i in range(5):
        await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=150,
            persona_id="tech_guru",
            post_id=f"baseline_post_{i}",
            operation="hook_generation"
        )
    
    # Now simulate an expensive post (anomaly)
    print("\nSimulating expensive post...")
    expensive_result = await engine.track_openai_cost(
        model="gpt-4o",
        input_tokens=10000,  # 10x normal
        output_tokens=2000,  # 10x normal
        persona_id="tech_guru",
        post_id="expensive_post_001",
        operation="hook_generation"
    )
    expensive_cost = expensive_result["cost_amount"]
    print(f"✓ Expensive post cost: ${expensive_cost:.4f}")
    
    # Check for anomalies
    anomaly_result = await engine.check_for_anomalies("tech_guru")
    
    if anomaly_result.get("anomalies_detected", []):
        print("\n🚨 ANOMALY DETECTED!")
        for anomaly in anomaly_result["anomalies_detected"]:
            print(f"Type: {anomaly.get('anomaly_type', 'unknown')}")
            print(f"Severity: {anomaly.get('severity', 'unknown')}")
            print(f"Current cost: ${anomaly.get('current_cost', 0):.4f}")
            if 'multiplier' in anomaly:
                print(f"Multiplier: {anomaly['multiplier']:.2f}x baseline")
    else:
        print("\n✓ No anomalies detected")
    
    # Demo 5: Cost efficiency metrics
    print("\n5. Cost Efficiency Metrics:")
    print("-" * 40)
    
    # Calculate cost per 1000 tokens
    tokens_used = 1000 + 150 + 1200 + 800  # Total from demo
    cost_per_1k_tokens = (hook_cost + body_cost) / (tokens_used / 1000)
    print(f"✓ Average cost per 1k tokens: ${cost_per_1k_tokens:.4f}")
    
    # ROI calculation (simulated engagement)
    simulated_engagement_rate = 0.065  # 6.5%
    simulated_follows = 100
    cost_per_follow = total_cost / simulated_follows if simulated_follows > 0 else 0
    
    print(f"✓ Simulated engagement rate: {simulated_engagement_rate:.1%}")
    print(f"✓ Cost per follow: ${cost_per_follow:.4f}")
    
    # Check against target KPIs
    target_cost_per_follow = 0.01
    if cost_per_follow <= target_cost_per_follow:
        print(f"✅ Meeting cost target of ${target_cost_per_follow}/follow")
    else:
        print(f"❌ Exceeding cost target by ${cost_per_follow - target_cost_per_follow:.4f}/follow")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    asyncio.run(main())