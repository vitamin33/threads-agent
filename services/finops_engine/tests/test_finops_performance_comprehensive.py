"""
Comprehensive Performance Tests for FinOps Cost Tracking & Optimization Engine (CRA-240)

Tests critical performance requirements:
1. Sub-second cost event storage latency (<500ms)
2. Anomaly detection response time (<60 seconds)
3. High-throughput cost tracking under load
4. Prometheus metrics emission performance
5. Cost attribution query performance
6. System scalability limits

Key Performance Targets:
- Cost event storage: <500ms latency
- Anomaly detection pipeline: <60s end-to-end
- Cost queries: <1s response time
- Concurrent post processing: 100+ posts/minute
- Metrics emission: <100ms per event
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime
import random


class TestFinOpsStoragePerformance:
    """Performance tests for cost event storage with sub-second latency requirements."""

    @pytest.mark.asyncio
    async def test_single_cost_event_storage_latency(self):
        """Test individual cost event storage meets <500ms requirement."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Test multiple single storage operations
        latencies = []

        for i in range(10):
            start_time = time.time()

            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=500,
                operation=f"latency_test_{i}",
                persona_id="latency_test_persona",
                post_id=f"latency_test_post_{i}",
            )

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

        # Verify all latencies meet requirement
        max_latency = max(latencies)
        avg_latency = statistics.mean(latencies)
        p95_latency = (
            statistics.quantiles(latencies, n=20)[18]
            if len(latencies) >= 20
            else max_latency
        )

        assert max_latency < 500, (
            f"Max latency {max_latency:.2f}ms exceeds 500ms requirement"
        )
        assert avg_latency < 200, (
            f"Average latency {avg_latency:.2f}ms too high for production"
        )
        assert p95_latency < 400, f"P95 latency {p95_latency:.2f}ms too high"

        print(
            f"Storage latencies - Max: {max_latency:.2f}ms, Avg: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms"
        )

    @pytest.mark.asyncio
    async def test_batch_storage_performance(self):
        """Test batch storage performance for high-throughput scenarios."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Generate batch of cost events
        batch_size = 100

        async def generate_cost_batch():
            """Generate a batch of cost events concurrently."""
            tasks = []
            for i in range(batch_size):
                task = engine.track_openai_cost(
                    model="gpt-3.5-turbo-0125",
                    input_tokens=500,
                    output_tokens=300,
                    operation=f"batch_test_{i}",
                    persona_id="batch_test_persona",
                    post_id=f"batch_test_post_{i}",
                )
                tasks.append(task)
            return await asyncio.gather(*tasks)

        # Measure batch processing time
        start_time = time.time()
        cost_events = await generate_cost_batch()
        end_time = time.time()

        batch_duration = end_time - start_time
        events_per_second = batch_size / batch_duration
        avg_latency_per_event = (batch_duration / batch_size) * 1000

        # Verify batch performance
        assert len(cost_events) == batch_size, "All events should be processed"
        assert batch_duration < 10.0, (
            f"Batch processing took {batch_duration:.2f}s, too slow"
        )
        assert events_per_second > 20, (
            f"Throughput {events_per_second:.1f} events/s too low"
        )
        assert avg_latency_per_event < 100, (
            f"Per-event latency {avg_latency_per_event:.2f}ms too high"
        )

        print(
            f"Batch performance - {events_per_second:.1f} events/s, {avg_latency_per_event:.2f}ms/event"
        )

    @pytest.mark.asyncio
    async def test_concurrent_storage_performance(self):
        """Test storage performance under concurrent load from multiple personas."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Multiple personas generating costs concurrently
        personas = [f"perf_persona_{i}" for i in range(5)]
        posts_per_persona = 20

        async def generate_persona_costs(persona_id: str):
            """Generate costs for one persona."""
            start_time = time.time()
            costs = []

            for i in range(posts_per_persona):
                cost_event = await engine.track_openai_cost(
                    model="gpt-4o",
                    input_tokens=random.randint(500, 2000),
                    output_tokens=random.randint(300, 1000),
                    operation=f"concurrent_op_{i}",
                    persona_id=persona_id,
                    post_id=f"{persona_id}_post_{i}",
                )
                costs.append(cost_event)

            end_time = time.time()
            return {
                "persona_id": persona_id,
                "costs": costs,
                "duration": end_time - start_time,
            }

        # Execute concurrent cost generation
        overall_start = time.time()
        tasks = [generate_persona_costs(persona) for persona in personas]
        results = await asyncio.gather(*tasks)
        overall_end = time.time()

        # Analyze performance
        total_duration = overall_end - overall_start
        total_events = sum(len(r["costs"]) for r in results)
        overall_throughput = total_events / total_duration

        # Verify concurrent performance
        assert total_events == len(personas) * posts_per_persona
        assert total_duration < 15.0, (
            f"Concurrent processing took {total_duration:.2f}s"
        )
        assert overall_throughput > 10, (
            f"Overall throughput {overall_throughput:.1f} events/s too low"
        )

        # Check individual persona performance
        for result in results:
            persona_throughput = len(result["costs"]) / result["duration"]
            assert persona_throughput > 2, (
                f"Persona {result['persona_id']} throughput too low"
            )

        print(
            f"Concurrent performance - {overall_throughput:.1f} events/s across {len(personas)} personas"
        )

    @pytest.mark.asyncio
    async def test_storage_performance_under_memory_pressure(self):
        """Test storage performance when system is under memory pressure."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Create memory pressure by accumulating large cost metadata
        large_metadata_events = []

        for i in range(50):
            # Large metadata to simulate memory pressure
            large_metadata = {
                "large_context": "x" * 10000,  # 10KB of data per event
                "model_details": {"param_" + str(j): f"value_{j}" for j in range(100)},
                "operation_trace": [f"step_{k}" for k in range(200)],
            }

            start_time = time.time()

            cost_event = await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=500,
                operation=f"memory_pressure_test_{i}",
                persona_id="memory_test_persona",
                post_id=f"memory_test_post_{i}",
            )

            # Manually add large metadata to simulate real-world scenarios
            cost_event.update(large_metadata)
            large_metadata_events.append(cost_event)

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            # Even under memory pressure, should meet latency requirements
            assert latency_ms < 1000, (
                f"Latency {latency_ms:.2f}ms under memory pressure too high"
            )

        # Verify all events were processed successfully
        assert len(large_metadata_events) == 50

        print(
            f"Memory pressure test completed - {len(large_metadata_events)} events with large metadata"
        )


class TestFinOpsAnomalyDetectionPerformance:
    """Performance tests for anomaly detection with <60 second response requirement."""

    @pytest.mark.asyncio
    async def test_anomaly_detection_pipeline_end_to_end_timing(self):
        """Test complete anomaly detection pipeline meets <60s requirement."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine({"anomaly_detection_enabled": True})

        # Setup baseline data by tracking normal costs
        persona_id = "anomaly_timing_test"

        # Phase 1: Establish baseline (simulate historical data)
        for i in range(10):
            await engine.track_openai_cost(
                model="gpt-3.5-turbo-0125",
                input_tokens=1000,
                output_tokens=500,
                operation=f"baseline_{i}",
                persona_id=persona_id,
                post_id=f"baseline_post_{i}",
            )

        # Phase 2: Generate anomalous costs
        anomaly_start = time.time()

        # Multiple expensive operations to trigger anomaly
        for i in range(5):
            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=5000,  # Much higher than baseline
                output_tokens=3000,
                operation=f"anomaly_trigger_{i}",
                persona_id=persona_id,
                post_id=f"anomaly_post_{i}",
            )

        # Phase 3: Detect anomalies (complete pipeline)
        detection_start = time.time()
        anomaly_result = await engine.check_for_anomalies(persona_id)
        detection_end = time.time()

        # Phase 4: Process alerts and actions (if triggered)
        if anomaly_result["anomalies_detected"]:
            # Additional processing time for alerts and circuit breaker
            pass

        pipeline_end = time.time()

        # Calculate timing metrics
        total_pipeline_time = pipeline_end - anomaly_start
        detection_time = detection_end - detection_start

        # Verify performance requirements
        assert total_pipeline_time < 60.0, (
            f"Total pipeline time {total_pipeline_time:.2f}s exceeds 60s requirement"
        )
        assert detection_time < 5.0, (
            f"Pure detection time {detection_time:.2f}s too slow"
        )

        # Verify anomaly was detected
        assert len(anomaly_result["anomalies_detected"]) > 0, (
            "Should detect anomaly with expensive operations"
        )

        print(
            f"Anomaly detection timing - Total: {total_pipeline_time:.2f}s, Detection: {detection_time:.3f}s"
        )

    @pytest.mark.asyncio
    async def test_concurrent_anomaly_detection_performance(self):
        """Test anomaly detection performance across multiple personas concurrently."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine({"anomaly_detection_enabled": True})

        # Multiple personas with different cost patterns
        personas = [f"concurrent_anomaly_persona_{i}" for i in range(10)]

        async def setup_persona_and_detect(persona_id: str):
            """Setup baseline and detect anomalies for one persona."""
            # Establish baseline
            for i in range(5):
                await engine.track_openai_cost(
                    model="gpt-3.5-turbo-0125",
                    input_tokens=random.randint(800, 1200),
                    output_tokens=random.randint(400, 600),
                    operation=f"baseline_{i}",
                    persona_id=persona_id,
                    post_id=f"{persona_id}_baseline_{i}",
                )

            # Generate anomaly
            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=4000,  # Anomalous cost
                output_tokens=2500,
                operation="anomaly_trigger",
                persona_id=persona_id,
                post_id=f"{persona_id}_anomaly",
            )

            # Detect anomalies
            start_time = time.time()
            result = await engine.check_for_anomalies(persona_id)
            end_time = time.time()

            return {
                "persona_id": persona_id,
                "detection_time": end_time - start_time,
                "anomalies_detected": len(result["anomalies_detected"]),
                "result": result,
            }

        # Execute concurrent anomaly detection
        overall_start = time.time()
        tasks = [setup_persona_and_detect(persona) for persona in personas]
        results = await asyncio.gather(*tasks)
        overall_end = time.time()

        # Analyze performance
        total_time = overall_end - overall_start
        detection_times = [r["detection_time"] for r in results]
        max_detection_time = max(detection_times)
        avg_detection_time = statistics.mean(detection_times)

        # Verify performance requirements
        assert total_time < 30.0, (
            f"Concurrent detection took {total_time:.2f}s, too slow"
        )
        assert max_detection_time < 10.0, (
            f"Max detection time {max_detection_time:.2f}s too slow"
        )
        assert avg_detection_time < 2.0, (
            f"Average detection time {avg_detection_time:.2f}s too slow"
        )

        # Verify anomalies were detected
        total_anomalies = sum(r["anomalies_detected"] for r in results)
        assert total_anomalies >= len(personas) * 0.8, "Should detect most anomalies"

        print(
            f"Concurrent anomaly detection - Max: {max_detection_time:.3f}s, Avg: {avg_detection_time:.3f}s"
        )

    @pytest.mark.asyncio
    async def test_anomaly_detection_scalability_limits(self):
        """Test anomaly detection performance at scale to find limits."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine({"anomaly_detection_enabled": True})

        # Test increasing persona counts to find performance limits
        test_scales = [5, 10, 20, 50]

        for scale in test_scales:
            personas = [f"scale_test_persona_{i}" for i in range(scale)]

            # Setup all personas with baseline data
            setup_tasks = []
            for persona_id in personas:
                for i in range(3):  # Minimal baseline
                    task = engine.track_openai_cost(
                        model="gpt-3.5-turbo-0125",
                        input_tokens=1000,
                        output_tokens=500,
                        operation=f"baseline_{i}",
                        persona_id=persona_id,
                        post_id=f"{persona_id}_base_{i}",
                    )
                    setup_tasks.append(task)

            await asyncio.gather(*setup_tasks)

            # Trigger anomalies for all personas
            anomaly_tasks = []
            for persona_id in personas:
                task = engine.track_openai_cost(
                    model="gpt-4o",
                    input_tokens=3000,
                    output_tokens=2000,
                    operation="scale_anomaly",
                    persona_id=persona_id,
                    post_id=f"{persona_id}_anomaly",
                )
                anomaly_tasks.append(task)

            await asyncio.gather(*anomaly_tasks)

            # Measure detection performance at this scale
            start_time = time.time()
            detection_tasks = [
                engine.check_for_anomalies(persona) for persona in personas
            ]
            await asyncio.gather(*detection_tasks)
            end_time = time.time()

            detection_duration = end_time - start_time
            personas_per_second = scale / detection_duration

            print(
                f"Scale test - {scale} personas: {detection_duration:.2f}s ({personas_per_second:.1f} personas/s)"
            )

            # Verify reasonable performance scaling
            if scale <= 20:
                assert detection_duration < 10.0, (
                    f"Detection for {scale} personas took {detection_duration:.2f}s"
                )
            else:
                # At larger scales, accept longer times but should still be reasonable
                assert detection_duration < 30.0, (
                    f"Detection for {scale} personas took {detection_duration:.2f}s"
                )


class TestFinOpsCostAttributionPerformance:
    """Performance tests for cost attribution queries and calculations."""

    @pytest.mark.asyncio
    async def test_cost_breakdown_query_performance(self):
        """Test cost breakdown query performance meets <1s requirement."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Setup posts with various cost complexities
        test_cases = [
            {"post_id": "simple_post", "cost_events": 3},
            {"post_id": "medium_post", "cost_events": 10},
            {"post_id": "complex_post", "cost_events": 25},
            {"post_id": "large_post", "cost_events": 50},
        ]

        # Generate cost events for each test case
        for case in test_cases:
            post_id = case["post_id"]
            for i in range(case["cost_events"]):
                await engine.track_openai_cost(
                    model="gpt-4o",
                    input_tokens=1000,
                    output_tokens=500,
                    operation=f"operation_{i}",
                    persona_id="query_perf_persona",
                    post_id=post_id,
                )

        # Test query performance for each complexity level
        query_times = []

        for case in test_cases:
            post_id = case["post_id"]

            # Measure query time
            start_time = time.time()
            breakdown = await engine.post_cost_attributor.get_post_cost_breakdown(
                post_id
            )
            end_time = time.time()

            query_time = end_time - start_time
            query_times.append(query_time)

            # Verify query correctness
            assert breakdown["post_id"] == post_id
            assert len(breakdown["audit_trail"]) == case["cost_events"]
            assert breakdown["total_cost"] > 0

            # Verify performance requirement
            assert query_time < 1.0, (
                f"Query for {post_id} took {query_time:.3f}s, exceeds 1s limit"
            )

            print(
                f"Query performance - {post_id} ({case['cost_events']} events): {query_time:.3f}s"
            )

        # Verify performance scales reasonably
        max_query_time = max(query_times)
        assert max_query_time < 0.5, f"Max query time {max_query_time:.3f}s too high"

    @pytest.mark.asyncio
    async def test_bulk_cost_calculation_performance(self):
        """Test bulk cost calculation performance for multiple posts."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Generate costs for many posts
        post_count = 100
        persona_id = "bulk_calc_persona"

        # Setup posts with costs
        for i in range(post_count):
            post_id = f"bulk_post_{i:03d}"

            # 2-3 cost events per post (typical scenario)
            for j in range(random.randint(2, 4)):
                await engine.track_openai_cost(
                    model="gpt-3.5-turbo-0125",
                    input_tokens=random.randint(500, 1500),
                    output_tokens=random.randint(300, 800),
                    operation=f"op_{j}",
                    persona_id=persona_id,
                    post_id=post_id,
                )

        # Test bulk calculation performance
        post_ids = [f"bulk_post_{i:03d}" for i in range(post_count)]

        start_time = time.time()

        # Calculate costs for all posts
        calculation_tasks = [
            engine.post_cost_attributor.calculate_total_post_cost(post_id)
            for post_id in post_ids
        ]
        total_costs = await asyncio.gather(*calculation_tasks)

        end_time = time.time()

        bulk_duration = end_time - start_time
        calculations_per_second = post_count / bulk_duration
        avg_calculation_time = bulk_duration / post_count

        # Verify performance requirements
        assert bulk_duration < 10.0, (
            f"Bulk calculation took {bulk_duration:.2f}s for {post_count} posts"
        )
        assert calculations_per_second > 20, (
            f"Calculation rate {calculations_per_second:.1f} calcs/s too low"
        )
        assert avg_calculation_time < 0.1, (
            f"Average calculation time {avg_calculation_time:.3f}s too slow"
        )

        # Verify all calculations succeeded
        assert len(total_costs) == post_count
        assert all(cost > 0 for cost in total_costs)

        print(
            f"Bulk calculation - {calculations_per_second:.1f} calcs/s, {avg_calculation_time:.3f}s avg"
        )

    @pytest.mark.asyncio
    async def test_cost_attribution_accuracy_performance_tradeoff(self):
        """Test performance vs accuracy tradeoff in cost attribution."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Create posts with varying metadata complexity (affects accuracy calculation)
        complexity_levels = [
            {"name": "minimal", "metadata_size": 5},
            {"name": "standard", "metadata_size": 15},
            {"name": "detailed", "metadata_size": 30},
            {"name": "comprehensive", "metadata_size": 50},
        ]

        performance_results = []

        for level in complexity_levels:
            post_id = f"accuracy_perf_{level['name']}"

            # Track cost with varying metadata complexity
            complex_metadata = {
                f"detail_{i}": f"value_{i}" * random.randint(1, 10)
                for i in range(level["metadata_size"])
            }

            await engine.post_cost_attributor.track_cost_for_post(
                post_id=post_id,
                cost_type="openai_api",
                cost_amount=0.0125,
                metadata=complex_metadata,
            )

            # Measure breakdown calculation with accuracy scoring
            start_time = time.time()
            breakdown = await engine.post_cost_attributor.get_post_cost_breakdown(
                post_id
            )
            end_time = time.time()

            calculation_time = end_time - start_time
            accuracy_score = breakdown["accuracy_score"]

            performance_results.append(
                {
                    "complexity": level["name"],
                    "metadata_size": level["metadata_size"],
                    "calculation_time": calculation_time,
                    "accuracy_score": accuracy_score,
                }
            )

            # Verify performance doesn't degrade too much with complexity
            assert calculation_time < 0.5, (
                f"Calculation for {level['name']} complexity took {calculation_time:.3f}s"
            )
            assert accuracy_score >= 0.95, (
                f"Accuracy {accuracy_score:.3f} below 95% requirement"
            )

        # Analyze performance vs complexity relationship
        for result in performance_results:
            print(
                f"Complexity {result['complexity']}: {result['calculation_time']:.3f}s, "
                f"accuracy {result['accuracy_score']:.3f}"
            )


class TestFinOpsPrometheusMetricsPerformance:
    """Performance tests for Prometheus metrics emission."""

    @pytest.mark.asyncio
    async def test_metrics_emission_latency(self):
        """Test Prometheus metrics emission latency."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Test metrics emission for various cost types
        cost_types = ["openai_api", "kubernetes", "vector_db", "database"]
        emission_times = []

        for cost_type in cost_types:
            # Create sample cost event
            cost_event = {
                "cost_amount": 0.0125,
                "cost_type": cost_type,
                "operation": "test_operation",
                "persona_id": "metrics_test_persona",
                "timestamp": datetime.now().isoformat(),
            }

            # Measure emission time
            start_time = time.time()
            engine.prometheus_client.emit_cost_metric(cost_event)
            end_time = time.time()

            emission_time = (end_time - start_time) * 1000  # Convert to ms
            emission_times.append(emission_time)

            # Verify sub-100ms emission requirement
            assert emission_time < 100, (
                f"Metrics emission took {emission_time:.2f}ms for {cost_type}"
            )

        # Verify overall performance
        max_emission_time = max(emission_times)
        avg_emission_time = statistics.mean(emission_times)

        assert max_emission_time < 50, (
            f"Max emission time {max_emission_time:.2f}ms too high"
        )
        assert avg_emission_time < 20, (
            f"Average emission time {avg_emission_time:.2f}ms too high"
        )

        print(
            f"Metrics emission - Max: {max_emission_time:.2f}ms, Avg: {avg_emission_time:.2f}ms"
        )

    @pytest.mark.asyncio
    async def test_high_volume_metrics_emission(self):
        """Test metrics emission performance under high volume."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Generate high volume of cost events
        event_count = 1000

        start_time = time.time()

        # Generate and emit metrics for many events
        for i in range(event_count):
            cost_event = {
                "cost_amount": random.uniform(0.001, 0.05),
                "cost_type": random.choice(["openai_api", "kubernetes", "vector_db"]),
                "operation": f"high_volume_op_{i}",
                "persona_id": f"persona_{i % 10}",
                "timestamp": datetime.now().isoformat(),
            }

            engine.prometheus_client.emit_cost_metric(cost_event)

        end_time = time.time()

        total_duration = end_time - start_time
        events_per_second = event_count / total_duration
        avg_emission_time = (total_duration / event_count) * 1000

        # Verify high-volume performance
        assert total_duration < 30.0, f"High volume emission took {total_duration:.2f}s"
        assert events_per_second > 50, (
            f"Emission rate {events_per_second:.1f} events/s too low"
        )
        assert avg_emission_time < 30, (
            f"Average emission time {avg_emission_time:.2f}ms too high"
        )

        # Verify all metrics were emitted
        emitted_metrics = engine.prometheus_client.get_emitted_metrics()
        assert len(emitted_metrics) >= event_count

        print(
            f"High volume metrics - {events_per_second:.1f} events/s, {avg_emission_time:.2f}ms avg"
        )

    @pytest.mark.asyncio
    async def test_concurrent_metrics_emission(self):
        """Test concurrent metrics emission from multiple sources."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Multiple concurrent metric sources
        source_count = 10
        events_per_source = 50

        async def emit_metrics_from_source(source_id: int):
            """Emit metrics from one source concurrently."""
            start_time = time.time()

            for i in range(events_per_source):
                cost_event = {
                    "cost_amount": random.uniform(0.005, 0.025),
                    "cost_type": "openai_api",
                    "operation": f"concurrent_op_{source_id}_{i}",
                    "persona_id": f"concurrent_persona_{source_id}",
                    "timestamp": datetime.now().isoformat(),
                }

                engine.prometheus_client.emit_cost_metric(cost_event)

            end_time = time.time()
            return end_time - start_time

        # Execute concurrent emissions
        overall_start = time.time()
        tasks = [emit_metrics_from_source(i) for i in range(source_count)]
        source_durations = await asyncio.gather(*tasks)
        overall_end = time.time()

        total_duration = overall_end - overall_start
        total_events = source_count * events_per_source
        overall_throughput = total_events / total_duration

        # Verify concurrent performance
        assert total_duration < 15.0, f"Concurrent emission took {total_duration:.2f}s"
        assert overall_throughput > 30, (
            f"Concurrent throughput {overall_throughput:.1f} events/s too low"
        )

        # Verify all sources performed reasonably
        max_source_duration = max(source_durations)
        assert max_source_duration < 5.0, (
            f"Slowest source took {max_source_duration:.2f}s"
        )

        # Verify all metrics were emitted
        emitted_metrics = engine.prometheus_client.get_emitted_metrics()
        assert len(emitted_metrics) >= total_events

        print(
            f"Concurrent metrics - {overall_throughput:.1f} events/s from {source_count} sources"
        )


class TestFinOpsSystemEndToEndPerformance:
    """End-to-end performance tests for complete FinOps workflows."""

    @pytest.mark.asyncio
    async def test_complete_viral_post_workflow_performance(self):
        """Test performance of complete viral post generation workflow."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine({"anomaly_detection_enabled": True})

        # Simulate complete viral post workflow
        workflow_count = 20
        persona_id = "workflow_perf_persona"

        async def complete_post_workflow(post_index: int):
            """Execute complete post generation workflow."""
            post_id = f"workflow_post_{post_index:03d}"
            workflow_start = time.time()

            # Phase 1: Hook generation
            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=400,
                operation="hook_generation",
                persona_id=persona_id,
                post_id=post_id,
            )

            # Phase 2: Body generation
            await engine.track_openai_cost(
                model="gpt-3.5-turbo-0125",
                input_tokens=1200,
                output_tokens=800,
                operation="body_generation",
                persona_id=persona_id,
                post_id=post_id,
            )

            # Phase 3: Infrastructure processing
            await engine.track_infrastructure_cost(
                resource_type="kubernetes",
                service="persona_runtime",
                cpu_cores=0.5,
                memory_gb=1.0,
                duration_minutes=3,
                operation="post_generation",
                persona_id=persona_id,
                post_id=post_id,
            )

            # Phase 4: Vector DB operations
            await engine.track_vector_db_cost(
                operation="similarity_search",
                query_count=500,
                collection=f"posts_{persona_id}",
                persona_id=persona_id,
                post_id=post_id,
            )

            # Phase 5: Cost calculation and analysis
            total_cost = await engine.calculate_total_post_cost(post_id)
            await engine.post_cost_attributor.get_post_cost_breakdown(post_id)

            # Phase 6: Anomaly check (if enabled)
            if post_index % 5 == 0:  # Check every 5th post
                await engine.check_for_anomalies(persona_id)

            workflow_end = time.time()

            return {
                "post_id": post_id,
                "workflow_duration": workflow_end - workflow_start,
                "total_cost": total_cost,
                "cost_events": 4,  # Number of cost events tracked
            }

        # Execute workflows
        overall_start = time.time()
        tasks = [complete_post_workflow(i) for i in range(workflow_count)]
        results = await asyncio.gather(*tasks)
        overall_end = time.time()

        # Analyze performance
        total_duration = overall_end - overall_start
        workflows_per_minute = (workflow_count / total_duration) * 60
        avg_workflow_time = statistics.mean([r["workflow_duration"] for r in results])
        max_workflow_time = max([r["workflow_duration"] for r in results])

        # Verify performance requirements
        assert total_duration < 60.0, (
            f"Complete workflow suite took {total_duration:.2f}s"
        )
        assert workflows_per_minute > 30, (
            f"Workflow rate {workflows_per_minute:.1f}/min too low"
        )
        assert avg_workflow_time < 2.0, (
            f"Average workflow time {avg_workflow_time:.2f}s too slow"
        )
        assert max_workflow_time < 5.0, (
            f"Max workflow time {max_workflow_time:.2f}s too slow"
        )

        # Verify all workflows completed successfully
        assert len(results) == workflow_count
        assert all(r["total_cost"] > 0 for r in results)

        print(
            f"Workflow performance - {workflows_per_minute:.1f}/min, {avg_workflow_time:.2f}s avg"
        )

    @pytest.mark.asyncio
    async def test_system_performance_under_sustained_load(self):
        """Test system performance under sustained high load."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine({"anomaly_detection_enabled": True})

        # Sustained load test parameters
        load_duration_seconds = 30
        target_operations_per_second = 10

        operations_completed = 0
        start_time = time.time()

        async def sustained_operation(operation_id: int):
            """Single operation under sustained load."""
            nonlocal operations_completed

            await engine.track_openai_cost(
                model="gpt-3.5-turbo-0125",
                input_tokens=random.randint(500, 1500),
                output_tokens=random.randint(300, 800),
                operation=f"sustained_op_{operation_id}",
                persona_id=f"load_persona_{operation_id % 5}",
                post_id=f"load_post_{operation_id}",
            )

            operations_completed += 1

        # Generate sustained load
        operation_id = 0

        while time.time() - start_time < load_duration_seconds:
            # Launch operations to maintain target rate
            batch_size = min(5, target_operations_per_second)
            tasks = [sustained_operation(operation_id + i) for i in range(batch_size)]

            batch_start = time.time()
            await asyncio.gather(*tasks)
            batch_end = time.time()

            operation_id += batch_size

            # Rate limiting to maintain target operations per second
            batch_duration = batch_end - batch_start
            target_batch_duration = batch_size / target_operations_per_second

            if batch_duration < target_batch_duration:
                await asyncio.sleep(target_batch_duration - batch_duration)

        end_time = time.time()
        actual_duration = end_time - start_time
        actual_ops_per_second = operations_completed / actual_duration

        # Verify sustained load performance
        assert (
            operations_completed
            >= load_duration_seconds * target_operations_per_second * 0.8
        )
        assert actual_ops_per_second >= target_operations_per_second * 0.8

        # Verify system remained responsive
        final_test_start = time.time()
        await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            operation="final_responsiveness_test",
            persona_id="responsiveness_test",
            post_id="final_test",
        )
        final_test_end = time.time()

        final_test_latency = (final_test_end - final_test_start) * 1000
        assert final_test_latency < 1000, (
            f"System unresponsive after load: {final_test_latency:.2f}ms"
        )

        print(
            f"Sustained load - {operations_completed} ops in {actual_duration:.1f}s "
            f"({actual_ops_per_second:.1f} ops/s)"
        )
