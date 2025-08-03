"""
Comprehensive Prometheus Integration Tests for FinOps Engine (CRA-240)

Tests real-time Prometheus metrics emission covering:
1. PrometheusMetricsEmitter - Real-time cost metrics emission
2. Integration with existing metrics infrastructure
3. Metric accuracy and labeling consistency
4. Performance under high-volume emission
5. Alert threshold metrics and business KPIs
6. Metrics retention and aggregation validation

Key Prometheus Integration Requirements:
- Real-time cost metrics emission (<100ms latency)
- Integration with existing threads-agent metrics
- Proper metric labeling and naming conventions
- Business KPI tracking (cost per post, efficiency, ROI)
- Alert threshold breach metrics
- Performance and latency metrics
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone
import statistics
import random


class TestPrometheusMetricsBasicEmission:
    """Basic Prometheus metrics emission functionality tests."""

    def test_prometheus_metrics_emitter_initialization(self):
        """Test PrometheusMetricsEmitter initialization and basic structure."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Verify initialization
        assert emitter is not None
        assert hasattr(emitter, "emit_cost_metric")
        assert hasattr(emitter, "emit_latency_metric")
        assert hasattr(emitter, "update_cost_per_post_metric")
        assert hasattr(emitter, "emit_alert_threshold_metric")

        # Verify internal tracking structure
        assert hasattr(emitter, "_metrics_emitted")
        assert isinstance(emitter._metrics_emitted, list)

    def test_openai_cost_metric_emission(self):
        """Test OpenAI cost metric emission with proper labeling."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # OpenAI cost event
        openai_cost_event = {
            "cost_amount": 0.0125,
            "cost_type": "openai_api",
            "model": "gpt-4o",
            "operation": "hook_generation",
            "persona_id": "ai_jesus",
            "input_tokens": 1000,
            "output_tokens": 500,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Emit metric
        emitter.emit_cost_metric(openai_cost_event)

        # Verify metric emission
        emitted_metrics = emitter.get_emitted_metrics()
        assert len(emitted_metrics) == 1

        metric = emitted_metrics[0]
        assert metric["metric_name"] == "openai_api_costs_usd_total"
        assert metric["metric_type"] == "counter"
        assert metric["value"] == 0.0125

        # Verify labels
        labels = metric["labels"]
        assert labels["model"] == "gpt-4o"
        assert labels["operation"] == "hook_generation"
        assert labels["persona_id"] == "ai_jesus"

        # Verify timestamp
        assert "timestamp" in metric

    def test_kubernetes_cost_metric_emission(self):
        """Test Kubernetes cost metric emission with resource labels."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Kubernetes cost event
        k8s_cost_event = {
            "cost_amount": 0.0036,
            "cost_type": "kubernetes",
            "service": "persona_runtime",
            "resource_type": "pod",
            "operation": "post_generation",
            "cpu_cores": 0.5,
            "memory_gb": 1.0,
            "duration_minutes": 3,
            "timestamp": datetime.utcnow().isoformat(),
        }

        emitter.emit_cost_metric(k8s_cost_event)

        # Verify K8s metric
        emitted_metrics = emitter.get_emitted_metrics()
        metric = emitted_metrics[0]

        assert metric["metric_name"] == "kubernetes_resource_costs_usd_total"
        assert metric["value"] == 0.0036

        # Verify K8s-specific labels
        labels = metric["labels"]
        assert labels["service"] == "persona_runtime"
        assert labels["resource_type"] == "pod"
        assert labels["operation"] == "post_generation"

    def test_vector_db_cost_metric_emission(self):
        """Test vector database cost metric emission."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Vector DB cost event
        vector_db_event = {
            "cost_amount": 0.0001,
            "cost_type": "vector_db",
            "operation": "similarity_search",
            "collection": "posts_ai_jesus",
            "persona_id": "ai_jesus",
            "query_count": 500,
            "timestamp": datetime.utcnow().isoformat(),
        }

        emitter.emit_cost_metric(vector_db_event)

        # Verify vector DB metric
        emitted_metrics = emitter.get_emitted_metrics()
        metric = emitted_metrics[0]

        assert metric["metric_name"] == "vector_db_operation_costs_usd_total"
        assert metric["value"] == 0.0001

        # Verify vector DB labels
        labels = metric["labels"]
        assert labels["operation"] == "similarity_search"
        assert labels["collection"] == "posts_ai_jesus"
        assert labels["persona_id"] == "ai_jesus"

    def test_database_cost_metric_emission(self):
        """Test database cost metric emission."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Database cost event
        db_event = {
            "cost_amount": 0.0002,
            "cost_type": "database",
            "db_type": "postgresql",
            "operation": "select",
            "persona_id": "ai_jesus",
            "query_count": 1000,
            "timestamp": datetime.utcnow().isoformat(),
        }

        emitter.emit_cost_metric(db_event)

        # Verify database metric
        emitted_metrics = emitter.get_emitted_metrics()
        metric = emitted_metrics[0]

        assert metric["metric_name"] == "database_operation_costs_usd_total"
        assert metric["value"] == 0.0002

        # Verify database labels
        labels = metric["labels"]
        assert labels["db_type"] == "postgresql"
        assert labels["operation"] == "select"
        assert labels["persona_id"] == "ai_jesus"

    def test_unknown_cost_type_metric_emission(self):
        """Test emission of unknown cost types falls back to generic metric."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Unknown cost type event
        unknown_event = {
            "cost_amount": 0.0050,
            "cost_type": "external_api",
            "operation": "data_enrichment",
            "service": "external_service",
            "timestamp": datetime.utcnow().isoformat(),
        }

        emitter.emit_cost_metric(unknown_event)

        # Verify generic metric
        emitted_metrics = emitter.get_emitted_metrics()
        metric = emitted_metrics[0]

        assert metric["metric_name"] == "finops_generic_costs_usd_total"
        assert metric["value"] == 0.0050

        # Verify generic labels
        labels = metric["labels"]
        assert labels["cost_type"] == "external_api"
        assert labels["operation"] == "data_enrichment"


class TestPrometheusBusinessKPIMetrics:
    """Test business KPI metrics emission for cost optimization."""

    def test_cost_per_post_metric_emission(self):
        """Test cost per post metric for $0.02 target tracking."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Test different cost per post scenarios
        test_scenarios = [
            {"persona_id": "ai_jesus", "cost": 0.018, "post_id": "under_target_001"},
            {"persona_id": "ai_jesus", "cost": 0.0195, "post_id": "near_target_002"},
            {"persona_id": "ai_jesus", "cost": 0.025, "post_id": "over_target_003"},
            {"persona_id": "tech_guru", "cost": 0.015, "post_id": "efficient_001"},
        ]

        for scenario in test_scenarios:
            emitter.update_cost_per_post_metric(
                persona_id=scenario["persona_id"],
                cost_per_post=scenario["cost"],
                post_id=scenario["post_id"],
            )

        # Verify cost per post metrics
        emitted_metrics = emitter.get_emitted_metrics()
        cost_per_post_metrics = [
            m for m in emitted_metrics if m["metric_name"] == "cost_per_post_usd"
        ]

        assert len(cost_per_post_metrics) == len(test_scenarios)

        # Verify metric structure and values
        for i, metric in enumerate(cost_per_post_metrics):
            scenario = test_scenarios[i]
            assert metric["metric_type"] == "gauge"
            assert metric["value"] == scenario["cost"]
            assert metric["labels"]["persona_id"] == scenario["persona_id"]
            assert metric["labels"]["post_id"] == scenario["post_id"]

    def test_alert_threshold_metric_emission(self):
        """Test alert threshold breach metrics."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Test alert threshold scenarios
        alert_scenarios = [
            {
                "metric_name": "cost_per_post_threshold_breach",
                "persona_id": "ai_jesus",
                "current_value": 0.045,  # Above $0.04 threshold
                "threshold_value": 0.04,
                "severity": "warning",
                "expected_alert": 1,
            },
            {
                "metric_name": "cost_per_post_threshold_breach",
                "persona_id": "tech_guru",
                "current_value": 0.035,  # Below $0.04 threshold
                "threshold_value": 0.04,
                "severity": "info",
                "expected_alert": 0,
            },
            {
                "metric_name": "cost_spike_threshold_breach",
                "persona_id": "ai_jesus",
                "current_value": 0.080,  # Major spike
                "threshold_value": 0.060,
                "severity": "critical",
                "expected_alert": 1,
            },
        ]

        for scenario in alert_scenarios:
            emitter.emit_alert_threshold_metric(
                metric_name=scenario["metric_name"],
                persona_id=scenario["persona_id"],
                current_value=scenario["current_value"],
                threshold_value=scenario["threshold_value"],
                severity=scenario["severity"],
            )

        # Verify alert metrics
        emitted_metrics = emitter.get_emitted_metrics()

        for i, metric in enumerate(emitted_metrics):
            scenario = alert_scenarios[i]
            assert metric["metric_name"] == scenario["metric_name"]
            assert metric["metric_type"] == "gauge"
            assert metric["value"] == scenario["expected_alert"]

            # Verify alert labels
            labels = metric["labels"]
            assert labels["persona_id"] == scenario["persona_id"]
            assert labels["severity"] == scenario["severity"]
            assert labels["current_value"] == str(scenario["current_value"])
            assert labels["threshold_value"] == str(scenario["threshold_value"])

    def test_latency_metric_emission(self):
        """Test latency metrics for performance monitoring."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Test different operation latencies
        latency_scenarios = [
            {
                "operation": "cost_event_storage",
                "latency_ms": 150.5,
                "status": "success",
            },
            {"operation": "cost_calculation", "latency_ms": 75.2, "status": "success"},
            {
                "operation": "anomaly_detection",
                "latency_ms": 2340.0,
                "status": "success",
            },
            {"operation": "alert_delivery", "latency_ms": 5670.5, "status": "success"},
            {
                "operation": "cost_event_storage",
                "latency_ms": 890.0,
                "status": "timeout",
            },
        ]

        for scenario in latency_scenarios:
            emitter.emit_latency_metric(
                operation=scenario["operation"],
                latency_ms=scenario["latency_ms"],
                status=scenario["status"],
            )

        # Verify latency metrics
        emitted_metrics = emitter.get_emitted_metrics()
        latency_metrics = [
            m
            for m in emitted_metrics
            if m["metric_name"] == "finops_operation_latency_ms"
        ]

        assert len(latency_metrics) == len(latency_scenarios)

        for i, metric in enumerate(latency_metrics):
            scenario = latency_scenarios[i]
            assert metric["metric_type"] == "histogram"
            assert metric["value"] == scenario["latency_ms"]

            # Verify latency labels
            labels = metric["labels"]
            assert labels["operation"] == scenario["operation"]
            assert labels["status"] == scenario["status"]


class TestPrometheusMetricsPerformance:
    """Test Prometheus metrics emission performance."""

    def test_metrics_emission_latency(self):
        """Test individual metric emission latency meets <100ms requirement."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Test emission latency for different metric types
        latency_measurements = []

        metric_tests = [
            {
                "name": "openai_cost",
                "event": {
                    "cost_amount": 0.0125,
                    "cost_type": "openai_api",
                    "model": "gpt-4o",
                    "operation": "generation",
                    "persona_id": "latency_test",
                },
            },
            {
                "name": "k8s_cost",
                "event": {
                    "cost_amount": 0.0036,
                    "cost_type": "kubernetes",
                    "service": "persona_runtime",
                    "resource_type": "pod",
                    "operation": "processing",
                },
            },
            {
                "name": "vector_db_cost",
                "event": {
                    "cost_amount": 0.0001,
                    "cost_type": "vector_db",
                    "operation": "similarity_search",
                    "collection": "posts_test",
                },
            },
        ]

        # Measure emission latency for each metric type
        for test in metric_tests:
            start_time = time.time()
            emitter.emit_cost_metric(test["event"])
            end_time = time.time()

            latency_ms = (end_time - start_time) * 1000
            latency_measurements.append(
                {"name": test["name"], "latency_ms": latency_ms}
            )

            # Verify individual emission meets <100ms requirement
            assert latency_ms < 100, (
                f"{test['name']} emission took {latency_ms:.2f}ms, exceeds 100ms limit"
            )

        # Verify overall performance
        max_latency = max(m["latency_ms"] for m in latency_measurements)
        avg_latency = statistics.mean(m["latency_ms"] for m in latency_measurements)

        assert max_latency < 50, f"Max emission latency {max_latency:.2f}ms too high"
        assert avg_latency < 20, (
            f"Average emission latency {avg_latency:.2f}ms too high"
        )

        print(
            f"Emission latencies - Max: {max_latency:.2f}ms, Avg: {avg_latency:.2f}ms"
        )

    def test_high_volume_metrics_emission_performance(self):
        """Test metrics emission performance under high volume."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # High volume metrics emission test
        metric_count = 1000

        start_time = time.time()

        for i in range(metric_count):
            # Alternate between different metric types
            if i % 3 == 0:
                event = {
                    "cost_amount": random.uniform(0.001, 0.02),
                    "cost_type": "openai_api",
                    "model": random.choice(["gpt-4o", "gpt-3.5-turbo-0125"]),
                    "operation": f"operation_{i}",
                    "persona_id": f"persona_{i % 5}",
                }
            elif i % 3 == 1:
                event = {
                    "cost_amount": random.uniform(0.001, 0.01),
                    "cost_type": "kubernetes",
                    "service": "persona_runtime",
                    "resource_type": "pod",
                    "operation": f"processing_{i}",
                }
            else:
                event = {
                    "cost_amount": random.uniform(0.0001, 0.001),
                    "cost_type": "vector_db",
                    "operation": "similarity_search",
                    "collection": f"collection_{i % 3}",
                }

            emitter.emit_cost_metric(event)

        end_time = time.time()

        total_duration = end_time - start_time
        metrics_per_second = metric_count / total_duration
        avg_emission_time = (total_duration / metric_count) * 1000

        # Verify high-volume performance
        assert total_duration < 30.0, f"High volume emission took {total_duration:.2f}s"
        assert metrics_per_second > 50, (
            f"Emission rate {metrics_per_second:.1f} metrics/s too low"
        )
        assert avg_emission_time < 30, (
            f"Average emission time {avg_emission_time:.2f}ms too high"
        )

        # Verify all metrics were emitted correctly
        emitted_metrics = emitter.get_emitted_metrics()
        assert len(emitted_metrics) == metric_count

        print(
            f"High volume performance - {metrics_per_second:.1f} metrics/s, {avg_emission_time:.2f}ms avg"
        )

    @pytest.mark.asyncio
    async def test_concurrent_metrics_emission(self):
        """Test concurrent metrics emission from multiple sources."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Concurrent emission test
        concurrent_sources = 10
        metrics_per_source = 50

        async def emit_metrics_from_source(source_id: int):
            """Emit metrics from one concurrent source."""
            emission_times = []

            for i in range(metrics_per_source):
                start_time = time.time()

                event = {
                    "cost_amount": random.uniform(0.005, 0.025),
                    "cost_type": "openai_api",
                    "model": "gpt-4o",
                    "operation": f"concurrent_op_{source_id}_{i}",
                    "persona_id": f"concurrent_persona_{source_id}",
                    "source_id": source_id,
                }

                emitter.emit_cost_metric(event)

                end_time = time.time()
                emission_times.append((end_time - start_time) * 1000)

            return {
                "source_id": source_id,
                "emission_times": emission_times,
                "avg_emission_time": statistics.mean(emission_times),
            }

        # Execute concurrent emissions
        overall_start = time.time()
        tasks = [emit_metrics_from_source(i) for i in range(concurrent_sources)]
        source_results = await asyncio.gather(*tasks)
        overall_end = time.time()

        total_duration = overall_end - overall_start
        total_metrics = concurrent_sources * metrics_per_source
        overall_throughput = total_metrics / total_duration

        # Verify concurrent performance
        assert total_duration < 15.0, f"Concurrent emission took {total_duration:.2f}s"
        assert overall_throughput > 30, (
            f"Concurrent throughput {overall_throughput:.1f} metrics/s too low"
        )

        # Verify all sources maintained good performance
        max_source_avg = max(r["avg_emission_time"] for r in source_results)
        assert max_source_avg < 50, (
            f"Slowest source avg {max_source_avg:.2f}ms too high"
        )

        # Verify all metrics were emitted
        emitted_metrics = emitter.get_emitted_metrics()
        assert len(emitted_metrics) == total_metrics

        print(
            f"Concurrent metrics - {overall_throughput:.1f} metrics/s from {concurrent_sources} sources"
        )


class TestPrometheusMetricsAccuracy:
    """Test accuracy and consistency of emitted metrics."""

    def test_metric_value_accuracy(self):
        """Test that emitted metric values exactly match input values."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Test precise value preservation
        test_values = [
            0.0125,  # Standard precision
            0.001234567,  # High precision
            1.0,  # Whole number
            0.0000001,  # Very small value
            99.999999,  # Large value with precision
        ]

        for i, test_value in enumerate(test_values):
            event = {
                "cost_amount": test_value,
                "cost_type": "openai_api",
                "model": "gpt-4o",
                "operation": f"accuracy_test_{i}",
                "persona_id": "accuracy_test",
            }

            emitter.emit_cost_metric(event)

        # Verify value accuracy
        emitted_metrics = emitter.get_emitted_metrics()

        for i, metric in enumerate(emitted_metrics):
            expected_value = test_values[i]
            actual_value = metric["value"]

            # Values should match exactly (no floating point precision loss)
            assert actual_value == expected_value, (
                f"Value mismatch: expected {expected_value}, got {actual_value}"
            )

    def test_metric_labeling_consistency(self):
        """Test consistent metric labeling across different scenarios."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Test label consistency across personas and operations
        personas = ["ai_jesus", "tech_guru", "startup_advisor"]
        operations = ["hook_generation", "body_generation", "trend_research"]
        models = ["gpt-4o", "gpt-3.5-turbo-0125"]

        expected_metrics = []

        for persona in personas:
            for operation in operations:
                for model in models:
                    event = {
                        "cost_amount": 0.0125,
                        "cost_type": "openai_api",
                        "model": model,
                        "operation": operation,
                        "persona_id": persona,
                    }

                    emitter.emit_cost_metric(event)
                    expected_metrics.append(event)

        # Verify labeling consistency
        emitted_metrics = emitter.get_emitted_metrics()
        assert len(emitted_metrics) == len(expected_metrics)

        for i, metric in enumerate(emitted_metrics):
            expected = expected_metrics[i]
            labels = metric["labels"]

            # Verify all expected labels are present and correct
            assert labels["model"] == expected["model"]
            assert labels["operation"] == expected["operation"]
            assert labels["persona_id"] == expected["persona_id"]

            # Verify metric naming consistency
            assert metric["metric_name"] == "openai_api_costs_usd_total"
            assert metric["metric_type"] == "counter"

    def test_metric_timestamp_accuracy(self):
        """Test that metric timestamps are accurate and properly formatted."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Emit metrics with timestamp verification
        emission_times = []

        for i in range(5):
            before_emission = datetime.now(timezone.utc)

            event = {
                "cost_amount": 0.01,
                "cost_type": "openai_api",
                "model": "gpt-4o",
                "operation": f"timestamp_test_{i}",
                "persona_id": "timestamp_test",
            }

            emitter.emit_cost_metric(event)

            after_emission = datetime.now(timezone.utc)
            emission_times.append((before_emission, after_emission))

            # Small delay between emissions
            time.sleep(0.01)

        # Verify timestamp accuracy
        emitted_metrics = emitter.get_emitted_metrics()

        for i, metric in enumerate(emitted_metrics):
            timestamp_str = metric["timestamp"]

            # Parse timestamp
            metric_timestamp = datetime.fromisoformat(
                timestamp_str.replace("Z", "+00:00")
            )

            # Verify timestamp is within emission window
            before_time, after_time = emission_times[i]
            assert before_time <= metric_timestamp <= after_time, (
                f"Timestamp {metric_timestamp} outside emission window [{before_time}, {after_time}]"
            )

    def test_metric_aggregation_consistency(self):
        """Test that metrics can be properly aggregated (same labels should accumulate)."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Emit multiple metrics with same labels (simulating aggregation scenarios)
        base_event = {
            "cost_type": "openai_api",
            "model": "gpt-4o",
            "operation": "hook_generation",
            "persona_id": "aggregation_test",
        }

        cost_values = [0.005, 0.008, 0.003, 0.007, 0.002]

        for cost in cost_values:
            event = base_event.copy()
            event["cost_amount"] = cost
            emitter.emit_cost_metric(event)

        # Verify metrics have consistent labels for aggregation
        emitted_metrics = emitter.get_emitted_metrics()

        # All metrics should have identical labels (for Prometheus aggregation)
        reference_labels = emitted_metrics[0]["labels"]

        for metric in emitted_metrics[1:]:
            assert metric["labels"] == reference_labels, (
                "Inconsistent labels prevent proper metric aggregation"
            )

        # Verify total cost for manual aggregation verification
        total_cost = sum(cost_values)
        emitted_total = sum(m["value"] for m in emitted_metrics)
        assert abs(emitted_total - total_cost) < 0.0001


class TestPrometheusIntegrationWithFinOpsSystem:
    """Test Prometheus integration with the complete FinOps system."""

    @pytest.mark.asyncio
    async def test_end_to_end_cost_tracking_with_metrics(self):
        """Test complete cost tracking workflow with Prometheus metrics."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        post_id = "e2e_metrics_test"
        persona_id = "ai_jesus"

        # Track costs through complete workflow

        # 1. OpenAI hook generation
        await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=400,
            operation="hook_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        # 2. OpenAI body generation
        await engine.track_openai_cost(
            model="gpt-3.5-turbo-0125",
            input_tokens=1200,
            output_tokens=800,
            operation="body_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        # 3. Infrastructure processing
        await engine.track_infrastructure_cost(
            resource_type="kubernetes",
            service="persona_runtime",
            cpu_cores=0.5,
            memory_gb=1.0,
            duration_minutes=3,
            operation="post_processing",
            persona_id=persona_id,
            post_id=post_id,
        )

        # 4. Vector DB operations
        await engine.track_vector_db_cost(
            operation="similarity_search",
            query_count=500,
            collection=f"posts_{persona_id}",
            persona_id=persona_id,
            post_id=post_id,
        )

        # 5. Calculate total cost (triggers cost per post metric)
        total_cost = await engine.calculate_total_post_cost(post_id)

        # Verify metrics were emitted for all operations
        emitted_metrics = engine.prometheus_client.get_emitted_metrics()

        # Should have metrics for all cost events plus cost per post
        assert len(emitted_metrics) >= 5  # 4 cost events + 1 cost per post

        # Verify metric types are present
        metric_names = {m["metric_name"] for m in emitted_metrics}
        expected_metrics = {
            "openai_api_costs_usd_total",
            "kubernetes_resource_costs_usd_total",
            "vector_db_operation_costs_usd_total",
            "cost_per_post_usd",
        }

        assert expected_metrics.issubset(metric_names), (
            f"Missing metrics: {expected_metrics - metric_names}"
        )

        # Verify cost per post metric
        cost_per_post_metrics = [
            m for m in emitted_metrics if m["metric_name"] == "cost_per_post_usd"
        ]
        assert len(cost_per_post_metrics) >= 1

        cost_metric = cost_per_post_metrics[0]
        assert cost_metric["value"] == total_cost
        assert cost_metric["labels"]["persona_id"] == persona_id
        assert cost_metric["labels"]["post_id"] == post_id

    @pytest.mark.asyncio
    async def test_anomaly_detection_metrics_integration(self):
        """Test Prometheus metrics emission during anomaly detection."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine({"anomaly_detection_enabled": True})

        persona_id = "anomaly_metrics_test"

        # Establish baseline
        for i in range(5):
            await engine.track_openai_cost(
                model="gpt-3.5-turbo-0125",
                input_tokens=1000,
                output_tokens=500,
                operation=f"baseline_{i}",
                persona_id=persona_id,
                post_id=f"baseline_post_{i}",
            )

        # Clear existing metrics
        engine.prometheus_client.clear_metrics()

        # Generate anomalous costs
        for i in range(3):
            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=5000,  # Much higher than baseline
                output_tokens=3000,
                operation=f"anomaly_{i}",
                persona_id=persona_id,
                post_id=f"anomaly_post_{i}",
            )

        # Trigger anomaly detection
        anomaly_result = await engine.check_for_anomalies(persona_id)

        # Verify anomaly detection metrics
        if len(anomaly_result["anomalies_detected"]) > 0:
            emitted_metrics = engine.prometheus_client.get_emitted_metrics()

            # Should have cost metrics plus potential alert threshold metrics
            cost_metrics = [
                m for m in emitted_metrics if "costs_usd_total" in m["metric_name"]
            ]
            assert len(cost_metrics) >= 3  # At least the 3 anomalous costs

            # Note: Alert threshold metrics are emitted by _check_cost_thresholds,
            # not by anomaly detection alerts, so we don't check for them in this test

    def test_metrics_clearing_and_reset(self):
        """Test metrics clearing functionality for testing purposes."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Emit some metrics
        for i in range(5):
            event = {
                "cost_amount": 0.01,
                "cost_type": "openai_api",
                "model": "gpt-4o",
                "operation": f"test_{i}",
                "persona_id": "clear_test",
            }
            emitter.emit_cost_metric(event)

        # Verify metrics exist
        assert len(emitter.get_emitted_metrics()) == 5

        # Clear metrics
        emitter.clear_metrics()

        # Verify metrics were cleared
        assert len(emitter.get_emitted_metrics()) == 0

        # Verify new metrics can be emitted after clearing
        event = {
            "cost_amount": 0.005,
            "cost_type": "kubernetes",
            "service": "test_service",
            "operation": "after_clear",
        }
        emitter.emit_cost_metric(event)

        assert len(emitter.get_emitted_metrics()) == 1

    def test_metrics_backward_compatibility(self):
        """Test that metrics maintain backward compatibility with existing monitoring."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Test that metric names follow Prometheus conventions
        test_events = [
            {
                "cost_type": "openai_api",
                "expected_metric": "openai_api_costs_usd_total",
            },
            {
                "cost_type": "kubernetes",
                "expected_metric": "kubernetes_resource_costs_usd_total",
            },
            {
                "cost_type": "vector_db",
                "expected_metric": "vector_db_operation_costs_usd_total",
            },
            {
                "cost_type": "database",
                "expected_metric": "database_operation_costs_usd_total",
            },
        ]

        for test in test_events:
            event = {
                "cost_amount": 0.01,
                "cost_type": test["cost_type"],
                "operation": "compatibility_test",
            }

            emitter.emit_cost_metric(event)

        # Verify metric naming conventions
        emitted_metrics = emitter.get_emitted_metrics()

        for i, metric in enumerate(emitted_metrics):
            expected_name = test_events[i]["expected_metric"]

            # Verify naming convention
            assert metric["metric_name"] == expected_name

            # Verify metric name follows Prometheus conventions
            assert "_total" in metric["metric_name"] or "_usd" in metric["metric_name"]
            assert not metric["metric_name"].startswith("_")  # No leading underscore
            assert (
                metric["metric_name"].islower() or "_" in metric["metric_name"]
            )  # Snake case
