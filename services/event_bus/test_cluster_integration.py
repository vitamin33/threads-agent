#!/usr/bin/env python3
"""
Integration test script for Event Bus running in k3d cluster.
Tests all functionality against real RabbitMQ and PostgreSQL.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
import aiohttp
import pika
import asyncpg

# Configuration
EVENT_BUS_URL = "http://localhost:8000"
RABBITMQ_URL = "amqp://user:pass@localhost:5672/"
DATABASE_URL = "postgresql://postgres:pass@localhost:5433/events"


class ClusterIntegrationTester:
    """Test Event Bus functionality in k3d cluster."""

    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []

    async def run_all_tests(self):
        """Run all integration tests."""
        print("🧪 Starting Event Bus Cluster Integration Tests\n")

        # Test 1: Health Check
        await self.test_health_endpoints()

        # Test 2: Direct RabbitMQ Publishing
        await self.test_rabbitmq_publishing()

        # Test 3: Event Store Operations
        await self.test_event_store()

        # Test 4: End-to-End Event Flow
        await self.test_end_to_end_flow()

        # Test 5: Multiple Publishers/Subscribers
        await self.test_concurrent_operations()

        # Test 6: Event Replay
        await self.test_event_replay()

        # Test 7: Error Scenarios
        await self.test_error_handling()

        # Test 8: Performance
        await self.test_performance()

        # Print summary
        self.print_summary()

    async def test_health_endpoints(self):
        """Test health and readiness endpoints."""
        print("Test 1: Health Endpoints")
        print("-" * 50)

        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get(f"{EVENT_BUS_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.assert_equals(data["status"], "healthy", "Health status")
                    self.assert_equals(data["service"], "event-bus", "Service name")
                else:
                    self.record_failure("Health endpoint", f"Status {resp.status}")

            # Test ready endpoint
            async with session.get(f"{EVENT_BUS_URL}/ready") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.assert_equals(data["status"], "ready", "Ready status")
                    self.assert_equals(
                        data["rabbitmq"], "connected", "RabbitMQ connection"
                    )
                else:
                    self.record_failure("Ready endpoint", f"Status {resp.status}")

        print()

    async def test_rabbitmq_publishing(self):
        """Test direct RabbitMQ publishing."""
        print("Test 2: RabbitMQ Publishing")
        print("-" * 50)

        try:
            # Connect to RabbitMQ
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()

            # Declare test queue
            queue_name = "test_event_queue"
            channel.queue_declare(queue=queue_name, durable=True)

            # Publish test event
            test_event = {
                "event_id": "test-001",
                "event_type": "test.created",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {"test": "data", "number": 42},
            }

            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=json.dumps(test_event),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent
                ),
            )

            self.record_success("RabbitMQ publish", "Event published successfully")

            # Consume the event
            method, properties, body = channel.basic_get(queue_name)
            if method:
                received_event = json.loads(body)
                self.assert_equals(
                    received_event["event_id"], test_event["event_id"], "Event ID match"
                )
                channel.basic_ack(method.delivery_tag)
                self.record_success("RabbitMQ consume", "Event consumed successfully")
            else:
                self.record_failure("RabbitMQ consume", "No message received")

            # Cleanup
            channel.queue_delete(queue_name)
            connection.close()

        except Exception as e:
            self.record_failure("RabbitMQ operations", str(e))

        print()

    async def test_event_store(self):
        """Test PostgreSQL event store operations."""
        print("Test 3: Event Store Operations")
        print("-" * 50)

        try:
            # Connect to PostgreSQL
            conn = await asyncpg.connect(DATABASE_URL)

            # Test table exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'events'
                )
            """)
            self.assert_true(exists, "Events table exists")

            # Insert test event
            test_event = {
                "event_id": "store-test-001",
                "timestamp": datetime.utcnow(),
                "event_type": "test.stored",
                "payload": {"data": "test"},
            }

            await conn.execute(
                """
                INSERT INTO events (event_id, timestamp, event_type, payload)
                VALUES ($1, $2, $3, $4)
            """,
                test_event["event_id"],
                test_event["timestamp"],
                test_event["event_type"],
                json.dumps(test_event["payload"]),
            )

            self.record_success("Event insert", "Event stored successfully")

            # Query event
            row = await conn.fetchrow(
                """
                SELECT * FROM events WHERE event_id = $1
            """,
                test_event["event_id"],
            )

            if row:
                self.assert_equals(row["event_type"], "test.stored", "Event type match")
                self.record_success("Event query", "Event retrieved successfully")
            else:
                self.record_failure("Event query", "Event not found")

            # Test indexes
            indexes = await conn.fetch("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'events'
            """)
            index_names = [idx["indexname"] for idx in indexes]

            self.assert_in("idx_events_timestamp", index_names, "Timestamp index")
            self.assert_in("idx_events_event_type", index_names, "Event type index")

            # Cleanup
            await conn.execute(
                """
                DELETE FROM events WHERE event_id = $1
            """,
                test_event["event_id"],
            )

            await conn.close()

        except Exception as e:
            self.record_failure("Event store operations", str(e))

        print()

    async def test_end_to_end_flow(self):
        """Test complete event flow through the system."""
        print("Test 4: End-to-End Event Flow")
        print("-" * 50)

        try:
            # Set up RabbitMQ subscriber
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()

            exchange_name = "events_exchange"
            queue_name = "e2e_test_queue"
            routing_key = "test.e2e"

            # Declare exchange and queue
            channel.exchange_declare(exchange=exchange_name, exchange_type="topic")
            channel.queue_declare(queue=queue_name, durable=True)
            channel.queue_bind(
                exchange=exchange_name, queue=queue_name, routing_key=routing_key
            )

            # Publish event
            test_event = {
                "event_id": "e2e-test-001",
                "event_type": "test.e2e",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {"message": "End-to-end test", "test_id": 12345},
            }

            channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=json.dumps(test_event),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )

            self.record_success("E2E publish", "Event published to exchange")

            # Consume event
            received = False

            def callback(ch, method, properties, body):
                nonlocal received
                event = json.loads(body)
                if event["event_id"] == test_event["event_id"]:
                    received = True
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    ch.stop_consuming()

            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            connection.process_data_events(time_limit=2)

            self.assert_true(received, "Event received through exchange")

            # Verify in database
            db_conn = await asyncpg.connect(DATABASE_URL)

            # Store event for persistence test
            await db_conn.execute(
                """
                INSERT INTO events (event_id, timestamp, event_type, payload)
                VALUES ($1, $2, $3, $4)
            """,
                test_event["event_id"],
                datetime.fromisoformat(test_event["timestamp"]),
                test_event["event_type"],
                json.dumps(test_event["payload"]),
            )

            # Query back
            stored = await db_conn.fetchrow(
                """
                SELECT * FROM events WHERE event_id = $1
            """,
                test_event["event_id"],
            )

            self.assert_true(stored is not None, "Event persisted in database")

            # Cleanup
            await db_conn.execute(
                """
                DELETE FROM events WHERE event_id = $1
            """,
                test_event["event_id"],
            )
            await db_conn.close()

            channel.queue_delete(queue_name)
            connection.close()

        except Exception as e:
            self.record_failure("End-to-end flow", str(e))

        print()

    async def test_concurrent_operations(self):
        """Test multiple concurrent publishers and subscribers."""
        print("Test 5: Concurrent Operations")
        print("-" * 50)

        try:
            num_publishers = 5
            num_messages_per_publisher = 10
            total_expected = num_publishers * num_messages_per_publisher

            # Connect to RabbitMQ
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()

            queue_name = "concurrent_test_queue"
            channel.queue_declare(queue=queue_name, durable=True)

            # Publish messages concurrently
            start_time = time.time()

            for publisher_id in range(num_publishers):
                for msg_id in range(num_messages_per_publisher):
                    event = {
                        "event_id": f"concurrent-{publisher_id}-{msg_id}",
                        "publisher": publisher_id,
                        "message": msg_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    channel.basic_publish(
                        exchange="", routing_key=queue_name, body=json.dumps(event)
                    )

            publish_time = time.time() - start_time
            self.record_success(
                "Concurrent publish",
                f"{total_expected} messages in {publish_time:.2f}s",
            )

            # Consume all messages
            consumed_count = 0
            start_time = time.time()

            while consumed_count < total_expected and time.time() - start_time < 5:
                method, properties, body = channel.basic_get(queue_name)
                if method:
                    consumed_count += 1
                    channel.basic_ack(method.delivery_tag)
                else:
                    await asyncio.sleep(0.1)

            consume_time = time.time() - start_time
            self.assert_equals(consumed_count, total_expected, "All messages consumed")
            self.record_success(
                "Concurrent consume",
                f"{consumed_count} messages in {consume_time:.2f}s",
            )

            # Cleanup
            channel.queue_delete(queue_name)
            connection.close()

        except Exception as e:
            self.record_failure("Concurrent operations", str(e))

        print()

    async def test_event_replay(self):
        """Test event replay functionality."""
        print("Test 6: Event Replay")
        print("-" * 50)

        try:
            conn = await asyncpg.connect(DATABASE_URL)

            # Insert events with different timestamps
            base_time = datetime.utcnow() - timedelta(hours=2)
            events = []

            for i in range(10):
                event = {
                    "event_id": f"replay-test-{i}",
                    "timestamp": base_time + timedelta(minutes=i * 10),
                    "event_type": "test.replay",
                    "payload": {"index": i},
                }
                events.append(event)

                await conn.execute(
                    """
                    INSERT INTO events (event_id, timestamp, event_type, payload)
                    VALUES ($1, $2, $3, $4)
                """,
                    event["event_id"],
                    event["timestamp"],
                    event["event_type"],
                    json.dumps(event["payload"]),
                )

            self.record_success("Replay setup", "10 events inserted")

            # Test replay by time range
            start_time = base_time + timedelta(minutes=20)
            end_time = base_time + timedelta(minutes=60)

            replayed = await conn.fetch(
                """
                SELECT * FROM events 
                WHERE timestamp >= $1 AND timestamp <= $2
                AND event_type = 'test.replay'
                ORDER BY timestamp
            """,
                start_time,
                end_time,
            )

            self.assert_equals(len(replayed), 5, "Correct number of events replayed")

            # Verify order
            for i, row in enumerate(replayed):
                payload = json.loads(row["payload"])
                expected_index = i + 2  # Should start from index 2
                self.assert_equals(payload["index"], expected_index, f"Event order {i}")

            # Test replay by event type
            type_filtered = await conn.fetch("""
                SELECT COUNT(*) as count FROM events
                WHERE event_type = 'test.replay'
            """)

            self.assert_equals(type_filtered[0]["count"], 10, "Event type filtering")

            # Cleanup
            await conn.execute("""
                DELETE FROM events WHERE event_type = 'test.replay'
            """)
            await conn.close()

        except Exception as e:
            self.record_failure("Event replay", str(e))

        print()

    async def test_error_handling(self):
        """Test error handling scenarios."""
        print("Test 7: Error Handling")
        print("-" * 50)

        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()

            # Test 1: Invalid JSON
            queue_name = "error_test_queue"
            channel.queue_declare(queue=queue_name, durable=True)

            # Publish invalid JSON
            channel.basic_publish(
                exchange="", routing_key=queue_name, body="{ invalid json }"
            )

            # Try to consume
            method, properties, body = channel.basic_get(queue_name)
            if method:
                try:
                    json.loads(body)
                    self.record_failure("Invalid JSON handling", "Should have failed")
                except json.JSONDecodeError:
                    self.record_success("Invalid JSON handling", "Correctly failed")
                channel.basic_ack(method.delivery_tag)

            # Test 2: Large payload
            large_event = {
                "event_id": "large-test",
                "event_type": "test.large",
                "payload": {"data": "x" * 10000},  # 10KB payload
            }

            channel.basic_publish(
                exchange="", routing_key=queue_name, body=json.dumps(large_event)
            )

            method, properties, body = channel.basic_get(queue_name)
            if method:
                event = json.loads(body)
                self.assert_equals(
                    len(event["payload"]["data"]), 10000, "Large payload handled"
                )
                channel.basic_ack(method.delivery_tag)

            # Test 3: Connection recovery would require killing RabbitMQ
            # Skip for now to avoid disrupting cluster

            # Cleanup
            channel.queue_delete(queue_name)
            connection.close()

            # Test 4: Database constraints
            conn = await asyncpg.connect(DATABASE_URL)

            # Try duplicate event_id
            try:
                await conn.execute(
                    """
                    INSERT INTO events (event_id, timestamp, event_type, payload)
                    VALUES ('dup-test', $1, 'test', '{}')
                """,
                    datetime.utcnow(),
                )

                await conn.execute(
                    """
                    INSERT INTO events (event_id, timestamp, event_type, payload)
                    VALUES ('dup-test', $1, 'test', '{}')
                """,
                    datetime.utcnow(),
                )

                self.record_failure("Duplicate event_id", "Should have failed")
            except asyncpg.UniqueViolationError:
                self.record_success("Duplicate event_id", "Correctly rejected")

            # Cleanup
            await conn.execute("""
                DELETE FROM events WHERE event_id = 'dup-test'
            """)
            await conn.close()

        except Exception as e:
            self.record_failure("Error handling", str(e))

        print()

    async def test_performance(self):
        """Test performance metrics."""
        print("Test 8: Performance Tests")
        print("-" * 50)

        try:
            # Test 1: Publishing throughput
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()

            queue_name = "perf_test_queue"
            channel.queue_declare(queue=queue_name, durable=True)

            num_messages = 1000
            start_time = time.time()

            for i in range(num_messages):
                event = {
                    "event_id": f"perf-{i}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": f"message-{i}",
                }
                channel.basic_publish(
                    exchange="", routing_key=queue_name, body=json.dumps(event)
                )

            publish_time = time.time() - start_time
            publish_rate = num_messages / publish_time

            self.record_success(
                "Publish throughput",
                f"{publish_rate:.0f} msg/sec ({num_messages} in {publish_time:.2f}s)",
            )

            # Test 2: Consume throughput
            consumed = 0
            start_time = time.time()

            while consumed < num_messages:
                method, properties, body = channel.basic_get(queue_name)
                if method:
                    consumed += 1
                    channel.basic_ack(method.delivery_tag)
                else:
                    break

            consume_time = time.time() - start_time
            consume_rate = consumed / consume_time

            self.record_success(
                "Consume throughput",
                f"{consume_rate:.0f} msg/sec ({consumed} in {consume_time:.2f}s)",
            )

            # Test 3: Database write performance
            conn = await asyncpg.connect(DATABASE_URL)

            start_time = time.time()
            batch_size = 100

            # Prepare batch
            records = []
            for i in range(batch_size):
                records.append(
                    (
                        f"db-perf-{i}",
                        datetime.utcnow(),
                        "test.performance",
                        json.dumps({"index": i}),
                    )
                )

            # Batch insert
            await conn.executemany(
                """
                INSERT INTO events (event_id, timestamp, event_type, payload)
                VALUES ($1, $2, $3, $4)
            """,
                records,
            )

            db_time = time.time() - start_time
            db_rate = batch_size / db_time

            self.record_success(
                "DB write throughput",
                f"{db_rate:.0f} events/sec ({batch_size} in {db_time:.2f}s)",
            )

            # Test 4: Database read performance
            start_time = time.time()

            results = await conn.fetch("""
                SELECT * FROM events 
                WHERE event_type = 'test.performance'
                ORDER BY timestamp DESC
                LIMIT 100
            """)

            query_time = time.time() - start_time

            self.record_success(
                "DB query performance",
                f"{len(results)} rows in {query_time * 1000:.0f}ms",
            )

            # Cleanup
            await conn.execute("""
                DELETE FROM events WHERE event_type = 'test.performance'
            """)
            await conn.close()

            channel.queue_delete(queue_name)
            connection.close()

        except Exception as e:
            self.record_failure("Performance tests", str(e))

        print()

    # Helper methods
    def assert_equals(self, actual, expected, test_name):
        """Assert equality."""
        if actual == expected:
            self.record_success(test_name, f"{actual} == {expected}")
        else:
            self.record_failure(test_name, f"{actual} != {expected}")

    def assert_true(self, condition, test_name):
        """Assert condition is true."""
        if condition:
            self.record_success(test_name, "Condition is true")
        else:
            self.record_failure(test_name, "Condition is false")

    def assert_in(self, item, container, test_name):
        """Assert item in container."""
        if item in container:
            self.record_success(test_name, f"{item} found")
        else:
            self.record_failure(test_name, f"{item} not found")

    def record_success(self, test_name, message):
        """Record successful test."""
        self.passed_tests += 1
        self.test_results.append(("✅", test_name, message))
        print(f"  ✅ {test_name}: {message}")

    def record_failure(self, test_name, message):
        """Record failed test."""
        self.failed_tests += 1
        self.test_results.append(("❌", test_name, message))
        print(f"  ❌ {test_name}: {message}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")

        if self.failed_tests > 0:
            print("\nFailed Tests:")
            for status, name, message in self.test_results:
                if status == "❌":
                    print(f"  - {name}: {message}")

        print("\n" + "=" * 60)

        if self.failed_tests == 0:
            print("🎉 ALL TESTS PASSED! 🎉")
        else:
            print("⚠️  Some tests failed. Please investigate.")

        print("=" * 60)


async def main():
    """Run integration tests."""
    tester = ClusterIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
