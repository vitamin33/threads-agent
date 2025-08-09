"""
Batch Processing Example

Demonstrates how to use batch publishing and consuming for high-throughput event processing.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List
import random
import time

from services.event_bus.service import create_event_bus_service
from services.event_bus.models.base import BaseEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_test_events(count: int) -> List[BaseEvent]:
    """Generate test events for demonstration."""
    events = []
    event_types = ["UserAction", "SystemMetric", "DataUpdate", "Notification"]

    for i in range(count):
        event = BaseEvent(
            event_type=random.choice(event_types),
            payload={
                "index": i,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "value": random.randint(1, 100),
                "user_id": f"user_{random.randint(1, 10)}",
                "metadata": {
                    "source": "batch_example",
                    "priority": random.choice(["low", "medium", "high"]),
                },
            },
        )
        events.append(event)

    return events


async def process_event_batch(events: List[BaseEvent]) -> None:
    """Example batch event processor."""
    start_time = time.time()

    # Simulate some processing work
    event_counts = {}
    total_value = 0

    for event in events:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        total_value += event.payload.get("value", 0)

    # Simulate async processing (e.g., database writes, API calls)
    await asyncio.sleep(0.01 * len(events))

    processing_time = time.time() - start_time

    logger.info(f"Processed batch of {len(events)} events in {processing_time:.3f}s")
    logger.info(f"Event types: {event_counts}")
    logger.info(f"Total value: {total_value}, Average: {total_value / len(events):.2f}")


async def run_batch_processing_demo():
    """Run the batch processing demonstration."""

    # Configuration
    rabbitmq_url = "amqp://user:pass@localhost:5672/"
    postgres_url = "postgresql://postgres:pass@localhost:5433/events"

    # Create Event Bus service with batching enabled
    event_bus = await create_event_bus_service(
        rabbitmq_url=rabbitmq_url,
        postgres_url=postgres_url,
        config={"batch_size": 50, "batch_timeout": 2.0, "enable_batching": True},
    )

    try:
        # Create batch consumer for processing events
        await event_bus.create_batch_consumer(
            name="demo_processor",
            queue_name="demo_events",
            handler=process_event_batch,
            batch_size=25,
            batch_timeout=1.0,
        )

        # Setup queue bindings
        channel = await event_bus.rabbitmq_manager._connection.channel()
        queue = await channel.get_queue("demo_events")
        await queue.bind("events", routing_key="*")
        await channel.close()

        logger.info("Starting batch processing demo...")

        # Phase 1: Steady stream of events
        logger.info("\n=== Phase 1: Steady Event Stream ===")
        for i in range(10):
            events = await generate_test_events(10)
            published = await event_bus.publish_events_batch(events)
            logger.info(f"Published batch {i + 1}: {published} events")
            await asyncio.sleep(0.5)

        # Wait for processing
        await asyncio.sleep(3)

        # Phase 2: Burst of events
        logger.info("\n=== Phase 2: Event Burst ===")
        burst_events = await generate_test_events(500)
        start_time = time.time()
        published = await event_bus.publish_events_batch(burst_events)
        publish_time = time.time() - start_time
        logger.info(
            f"Published {published} events in {publish_time:.3f}s "
            f"({published / publish_time:.0f} events/sec)"
        )

        # Wait for processing
        await asyncio.sleep(5)

        # Phase 3: Mixed event sizes
        logger.info("\n=== Phase 3: Mixed Batch Sizes ===")
        for i in range(5):
            batch_size = random.randint(5, 100)
            events = await generate_test_events(batch_size)
            published = await event_bus.publish_events_batch(events)
            logger.info(f"Published variable batch: {published} events")
            await asyncio.sleep(0.2)

        # Wait for final processing
        await asyncio.sleep(3)

        # Display metrics
        logger.info("\n=== Final Metrics ===")
        metrics = await event_bus.get_metrics()

        # Publisher metrics
        for name, pub_metrics in metrics["publishers"].items():
            logger.info(f"\nPublisher '{name}':")
            logger.info(f"  Total messages: {pub_metrics['total_messages']}")
            logger.info(f"  Total batches: {pub_metrics['total_batches']}")
            logger.info(
                f"  Average batch size: {pub_metrics['average_batch_size']:.1f}"
            )
            logger.info(f"  Total bytes: {pub_metrics['total_bytes']:,}")

        # Consumer metrics
        for name, cons_metrics in metrics["consumers"].items():
            logger.info(f"\nConsumer '{name}':")
            logger.info(f"  Total messages: {cons_metrics['total_messages']}")
            logger.info(f"  Total batches: {cons_metrics['total_batches']}")
            logger.info(
                f"  Average batch size: {cons_metrics['average_batch_size']:.1f}"
            )
            logger.info(f"  Success rate: {cons_metrics['success_rate']:.1f}%")

        # Event store metrics
        if "table_metrics" in metrics["event_store"]:
            logger.info("\nEvent Store:")
            logger.info(
                f"  Total rows: {metrics['event_store']['table_metrics']['row_count']}"
            )
            logger.info(
                f"  Table size: {metrics['event_store']['table_metrics']['table_size']}"
            )
            logger.info(
                f"  Index size: {metrics['event_store']['table_metrics']['indexes_size']}"
            )

    except Exception as e:
        logger.error(f"Demo error: {e}")
        raise
    finally:
        # Cleanup
        await event_bus.stop()


async def run_performance_comparison():
    """Compare performance with and without batching."""

    rabbitmq_url = "amqp://user:pass@localhost:5672/"
    postgres_url = "postgresql://postgres:pass@localhost:5433/events"

    # Test configuration
    num_events = 1000
    events = await generate_test_events(num_events)

    logger.info(f"\n=== Performance Comparison: {num_events} events ===")

    # Test without batching
    logger.info("\n--- Without Batching ---")
    event_bus_no_batch = await create_event_bus_service(
        rabbitmq_url=rabbitmq_url,
        postgres_url=postgres_url,
        config={"enable_batching": False},
    )

    start_time = time.time()
    for event in events:
        await event_bus_no_batch.publish_event(event)
    no_batch_time = time.time() - start_time

    await event_bus_no_batch.stop()

    logger.info(f"Time without batching: {no_batch_time:.3f}s")
    logger.info(f"Throughput: {num_events / no_batch_time:.0f} events/sec")

    # Test with batching
    logger.info("\n--- With Batching ---")
    event_bus_batch = await create_event_bus_service(
        rabbitmq_url=rabbitmq_url,
        postgres_url=postgres_url,
        config={"enable_batching": True, "batch_size": 100, "batch_timeout": 0.5},
    )

    start_time = time.time()
    await event_bus_batch.publish_events_batch(events)
    batch_time = time.time() - start_time

    await event_bus_batch.stop()

    logger.info(f"Time with batching: {batch_time:.3f}s")
    logger.info(f"Throughput: {num_events / batch_time:.0f} events/sec")

    improvement = ((no_batch_time - batch_time) / no_batch_time) * 100
    logger.info(f"\nImprovement: {improvement:.1f}% faster with batching")
    logger.info(f"Speedup factor: {no_batch_time / batch_time:.1f}x")


if __name__ == "__main__":
    # Run the main demo
    asyncio.run(run_batch_processing_demo())

    # Run performance comparison
    # asyncio.run(run_performance_comparison())
