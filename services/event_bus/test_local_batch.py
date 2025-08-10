#!/usr/bin/env python
"""
Test batch processing locally.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from services.event_bus.service import create_event_bus_service
from services.event_bus.models.base import BaseEvent
from datetime import datetime, timezone
import time
import random


async def test_batch_performance():
    """Test batch processing performance locally."""
    print("Testing Event Bus batch processing locally...")

    # Use local services
    rabbitmq_url = "amqp://user:pass@localhost:5672/"
    postgres_url = "postgresql://postgres:postgres@localhost:5433/events"

    # Create Event Bus service
    event_bus = await create_event_bus_service(
        rabbitmq_url=rabbitmq_url,
        postgres_url=postgres_url,
        config={"batch_size": 100, "batch_timeout": 1.0, "enable_batching": True},
    )

    try:
        # Test 1: Individual events (no batching)
        print("\n=== Test 1: Individual Events ===")
        start_time = time.time()

        for i in range(100):
            event = BaseEvent(
                event_type="TestEvent",
                payload={
                    "index": i,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "value": random.randint(1, 100),
                    "test": "individual",
                },
            )
            await event_bus.publish_event(event)

        individual_time = time.time() - start_time
        print(f"Published 100 individual events in {individual_time:.2f}s")
        print(f"Throughput: {100 / individual_time:.0f} events/sec")

        # Test 2: Batch events
        print("\n=== Test 2: Batch Events ===")
        events = []
        for i in range(100):
            event = BaseEvent(
                event_type="TestEvent",
                payload={
                    "index": i,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "value": random.randint(1, 100),
                    "test": "batch",
                },
            )
            events.append(event)

        start_time = time.time()
        published = await event_bus.publish_events_batch(events)
        batch_time = time.time() - start_time

        print(f"Published {published} events in batch in {batch_time:.2f}s")
        print(f"Throughput: {published / batch_time:.0f} events/sec")

        # Calculate improvement
        improvement = ((individual_time - batch_time) / individual_time) * 100
        speedup = individual_time / batch_time
        print(f"\nImprovement: {improvement:.1f}% faster with batching")
        print(f"Speedup factor: {speedup:.1f}x")

        # Test 3: High throughput
        print("\n=== Test 3: High Throughput (1000 events) ===")
        events = []
        for i in range(1000):
            event = BaseEvent(
                event_type="HighThroughputEvent",
                payload={
                    "index": i,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": "x" * 100,
                },
            )
            events.append(event)

        start_time = time.time()
        published = await event_bus.publish_events_batch(events)
        high_throughput_time = time.time() - start_time

        print(f"Published {published} events in {high_throughput_time:.2f}s")
        print(f"Throughput: {published / high_throughput_time:.0f} events/sec")

        # Get metrics
        print("\n=== Event Bus Metrics ===")
        metrics = await event_bus.get_metrics()

        # Display key metrics
        if "publishers" in metrics:
            for name, pub_metrics in metrics["publishers"].items():
                print(f"\nPublisher '{name}':")
                print(f"  Total messages: {pub_metrics.get('total_messages', 0)}")
                print(f"  Total batches: {pub_metrics.get('total_batches', 0)}")
                print(
                    f"  Average batch size: {pub_metrics.get('average_batch_size', 0):.1f}"
                )

        if "event_store" in metrics and "table_metrics" in metrics["event_store"]:
            store_metrics = metrics["event_store"]["table_metrics"]
            print("\nEvent Store:")
            print(f"  Total events: {store_metrics.get('row_count', 0)}")
            print(f"  Table size: {store_metrics.get('table_size', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await event_bus.stop()


if __name__ == "__main__":
    asyncio.run(test_batch_performance())
