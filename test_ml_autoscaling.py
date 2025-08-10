#!/usr/bin/env python
"""
Test script for ML Autoscaling functionality
Generates load to trigger KEDA scaling
"""

import asyncio
import aiohttp
import time
import random
from datetime import datetime
import pika
import json


async def generate_http_load(url: str, duration_seconds: int = 60, rps: int = 100):
    """Generate HTTP load to trigger scaling"""
    print(f"🚀 Generating HTTP load: {rps} RPS for {duration_seconds}s to {url}")

    start_time = time.time()
    request_count = 0
    errors = 0

    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < duration_seconds:
            try:
                # Send batch of requests
                tasks = []
                for _ in range(rps // 10):  # Send in batches
                    tasks.append(session.get(url))

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                for resp in responses:
                    if isinstance(resp, Exception):
                        errors += 1
                    else:
                        request_count += 1
                        resp.close()

                # Wait to maintain RPS
                await asyncio.sleep(0.1)

                # Print progress
                if request_count % 100 == 0:
                    elapsed = time.time() - start_time
                    actual_rps = request_count / elapsed if elapsed > 0 else 0
                    print(
                        f"  📊 Sent {request_count} requests, {errors} errors, {actual_rps:.1f} RPS"
                    )

            except Exception as e:
                print(f"  ❌ Error: {e}")
                errors += 1

    total_time = time.time() - start_time
    print(f"✅ Load test complete: {request_count} requests in {total_time:.1f}s")
    print(f"   Average RPS: {request_count / total_time:.1f}, Errors: {errors}")


def generate_rabbitmq_load(queue_name: str = "celery", message_count: int = 100):
    """Generate RabbitMQ queue messages to trigger scaling"""
    print(
        f"🐰 Generating RabbitMQ load: {message_count} messages to queue '{queue_name}'"
    )

    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="localhost",
                port=30672,  # Assuming port-forward: kubectl port-forward svc/rabbitmq 30672:5672
                credentials=pika.PlainCredentials("user", "pass"),
            )
        )
        channel = connection.channel()

        # Declare queue
        channel.queue_declare(queue=queue_name, durable=True)

        # Send messages
        for i in range(message_count):
            message = {
                "id": f"test-{i}",
                "timestamp": datetime.now().isoformat(),
                "data": f"Test message {i}",
                "random": random.random(),
            }

            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                ),
            )

            if (i + 1) % 10 == 0:
                print(f"  📤 Sent {i + 1}/{message_count} messages")

        # Get queue stats
        method = channel.queue_declare(queue=queue_name, passive=True)
        queue_depth = method.method.message_count
        print(f"✅ RabbitMQ load complete: {message_count} messages sent")
        print(f"   Current queue depth: {queue_depth}")

        connection.close()

    except Exception as e:
        print(f"❌ RabbitMQ error: {e}")
        print(
            "   Make sure to port-forward: kubectl port-forward svc/rabbitmq 30672:5672"
        )


async def monitor_scaling(duration_seconds: int = 120):
    """Monitor scaling events"""
    print(f"👁️  Monitoring scaling for {duration_seconds}s...")

    start_time = time.time()
    last_check = {}

    while time.time() - start_time < duration_seconds:
        try:
            # Check replica counts (simulated - would use kubectl in real scenario)
            print(f"\n⏱️  Time: {int(time.time() - start_time)}s")
            print("   Run: kubectl get deployment celery-worker -o wide")
            print("   Run: kubectl get hpa")
            print(
                "   Run: kubectl get events --sort-by='.lastTimestamp' | grep -i scale"
            )

            await asyncio.sleep(10)

        except Exception as e:
            print(f"❌ Monitoring error: {e}")

    print("✅ Monitoring complete")


async def test_predictive_scaling():
    """Test predictive scaling with pattern simulation"""
    print("\n🔮 Testing Predictive Scaling")
    print("=" * 50)

    # Simulate daily pattern
    print("📈 Simulating daily pattern (business hours load)...")

    current_hour = datetime.now().hour
    if 9 <= current_hour < 17:
        print("   ⏰ Business hours detected - expecting higher replicas")
        load_multiplier = 2.0
    else:
        print("   🌙 Off-hours detected - expecting lower replicas")
        load_multiplier = 0.5

    # Generate load based on time
    base_rps = 50
    target_rps = int(base_rps * load_multiplier)

    await generate_http_load(
        url="http://localhost:30080/health",  # Assuming port-forward
        duration_seconds=30,
        rps=target_rps,
    )

    print("\n📊 Predictive scaling should now:")
    print(f"   - Detect {'high' if load_multiplier > 1 else 'low'} load period")
    print("   - Forecast next 30 minutes based on pattern")
    print(f"   - Proactively scale {'up' if load_multiplier > 1 else 'down'}")


def main():
    """Main test orchestration"""
    print("🚀 ML Autoscaling Test Suite")
    print("=" * 50)

    # Instructions
    print("\n📋 Prerequisites:")
    print("1. Port-forward services:")
    print("   kubectl port-forward svc/orchestrator 30080:8080 &")
    print("   kubectl port-forward svc/rabbitmq 30672:5672 &")
    print("   kubectl port-forward svc/prometheus 30090:9090 &")
    print("\n2. Watch scaling in another terminal:")
    print("   watch 'kubectl get deployment celery-worker orchestrator'")
    print("   watch 'kubectl get hpa'")
    print("   kubectl get events -w | grep -i scale")

    input("\nPress Enter to start tests...")

    # Test 1: RabbitMQ queue-based scaling
    print("\n📝 Test 1: Queue-based Scaling")
    print("-" * 40)
    generate_rabbitmq_load(queue_name="celery", message_count=50)
    print("⏳ Waiting 30s for scaling to trigger...")
    time.sleep(30)

    # Test 2: HTTP load-based scaling
    print("\n📝 Test 2: HTTP Load-based Scaling")
    print("-" * 40)
    asyncio.run(
        generate_http_load(
            url="http://localhost:30080/health", duration_seconds=60, rps=150
        )
    )

    # Test 3: Predictive scaling
    print("\n📝 Test 3: Predictive Scaling")
    print("-" * 40)
    asyncio.run(test_predictive_scaling())

    # Monitor results
    print("\n📝 Test 4: Monitoring Scaling Events")
    print("-" * 40)
    asyncio.run(monitor_scaling(duration_seconds=60))

    print("\n✅ All tests complete!")
    print("\n📊 Check results with:")
    print("   kubectl describe scaledobject ml-autoscaling-celery-worker-scaler")
    print("   kubectl describe scaledobject ml-autoscaling-orchestrator-scaler")
    print("   kubectl get events --sort-by='.lastTimestamp' | grep -i scale")


if __name__ == "__main__":
    main()
