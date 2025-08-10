#!/usr/bin/env python
"""
Test batch processing performance on k3d cluster.
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime, timezone
import random


async def send_event(session, event):
    """Send a single event to the Event Bus API."""
    url = "http://localhost:8000/events"
    async with session.post(url, json=event) as response:
        return await response.json()


async def test_batch_processing():
    """Test batch processing performance."""
    print("Testing Event Bus batch processing on k3d cluster...")

    async with aiohttp.ClientSession() as session:
        # Test 1: Send events individually (no batching)
        print("\n=== Test 1: Individual Events (No Batching) ===")
        start_time = time.time()

        for i in range(100):
            event = {
                "event_type": "TestEvent",
                "payload": {
                    "index": i,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "value": random.randint(1, 100),
                    "test": "individual",
                },
            }
            await send_event(session, event)

        individual_time = time.time() - start_time
        print(f"Sent 100 individual events in {individual_time:.2f}s")
        print(f"Throughput: {100 / individual_time:.0f} events/sec")

        # Test 2: Send events in batch
        print("\n=== Test 2: Batch Events ===")
        batch_events = []
        for i in range(100):
            event = {
                "event_type": "TestEvent",
                "payload": {
                    "index": i,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "value": random.randint(1, 100),
                    "test": "batch",
                },
            }
            batch_events.append(event)

        start_time = time.time()
        url = "http://localhost:8000/events/batch"
        async with session.post(url, json={"events": batch_events}) as response:
            result = await response.json()
            print(f"Batch response: {result}")

        batch_time = time.time() - start_time
        print(f"Sent 100 events in batch in {batch_time:.2f}s")
        print(f"Throughput: {100 / batch_time:.0f} events/sec")

        # Calculate improvement
        if batch_time > 0:
            improvement = ((individual_time - batch_time) / individual_time) * 100
            speedup = individual_time / batch_time
            print(f"\nImprovement: {improvement:.1f}% faster with batching")
            print(f"Speedup factor: {speedup:.1f}x")

        # Test 3: Check metrics
        print("\n=== Test 3: Event Bus Metrics ===")
        async with session.get("http://localhost:8000/metrics") as response:
            metrics = await response.json()
            print(json.dumps(metrics, indent=2))


async def test_high_throughput():
    """Test high throughput scenarios."""
    print("\n=== High Throughput Test ===")

    async with aiohttp.ClientSession() as session:
        # Send 1000 events in batches of 100
        total_events = 1000
        batch_size = 100

        start_time = time.time()

        for batch_num in range(total_events // batch_size):
            batch_events = []
            for i in range(batch_size):
                event = {
                    "event_type": "HighThroughputEvent",
                    "payload": {
                        "batch": batch_num,
                        "index": i,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "data": "x" * 100,  # Some payload
                    },
                }
                batch_events.append(event)

            url = "http://localhost:8000/events/batch"
            async with session.post(url, json={"events": batch_events}) as response:
                result = await response.json()

        total_time = time.time() - start_time
        print(f"Sent {total_events} events in {total_time:.2f}s")
        print(f"Overall throughput: {total_events / total_time:.0f} events/sec")


if __name__ == "__main__":
    asyncio.run(test_batch_processing())
    asyncio.run(test_high_throughput())
