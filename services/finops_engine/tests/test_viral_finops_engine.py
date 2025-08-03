"""
Test suite for ViralFinOpsEngine - Real-time Cost Data Collection Engine (CRA-240)

Following TDD methodology to implement cost tracking for:
- OpenAI API calls with token-level granularity
- Kubernetes resources
- Vector DB queries
- Monitoring infrastructure

Target: $0.02 per post cost with sub-second latency storage.
"""

import pytest


class TestViralFinOpsEngine:
    """Test suite for ViralFinOpsEngine main orchestrator class."""

    def test_viral_finops_engine_initialization(self):
        """Test that ViralFinOpsEngine can be instantiated with default configuration.

        This is our first failing test - the class doesn't exist yet!
        """
        # This will fail because ViralFinOpsEngine doesn't exist
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Basic assertions about the engine structure
        assert engine is not None
        assert hasattr(engine, "openai_tracker")
        assert hasattr(engine, "infrastructure_tracker")
        assert hasattr(engine, "cost_storage")
        assert hasattr(engine, "prometheus_client")

    def test_viral_finops_engine_initialization_with_config(self):
        """Test ViralFinOpsEngine initialization with custom configuration."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        config = {
            "cost_threshold_per_post": 0.02,  # Target: $0.02 per post
            "alert_threshold_multiplier": 2.0,  # 2x alert threshold
            "storage_latency_target_ms": 500,  # Sub-second latency
        }

        engine = ViralFinOpsEngine(config=config)

        assert engine.config["cost_threshold_per_post"] == 0.02
        assert engine.config["alert_threshold_multiplier"] == 2.0
        assert engine.config["storage_latency_target_ms"] == 500

    def test_viral_finops_engine_has_required_components(self):
        """Test that ViralFinOpsEngine contains all required tracking components."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Verify all required components are present
        assert hasattr(engine, "openai_tracker"), "Missing OpenAI cost tracker"
        assert hasattr(engine, "infrastructure_tracker"), (
            "Missing infrastructure cost tracker"
        )
        assert hasattr(engine, "vector_db_tracker"), "Missing vector DB cost tracker"
        assert hasattr(engine, "monitoring_tracker"), "Missing monitoring cost tracker"
        assert hasattr(engine, "cost_storage"), "Missing cost event storage"
        assert hasattr(engine, "prometheus_client"), "Missing Prometheus client"

        # Verify cost tracking method exists
        assert hasattr(engine, "track_cost_event"), "Missing cost tracking method"


class TestOpenAICostTracker:
    """Test suite for OpenAI cost tracking with token-level granularity."""

    def test_openai_cost_tracker_initialization(self):
        """Test that OpenAICostTracker can be instantiated with pricing config.

        This will fail because OpenAICostTracker doesn't exist yet!
        """
        from services.finops_engine.openai_cost_tracker import OpenAICostTracker

        # Pricing config with token-level granularity
        pricing_config = {
            "gpt-4o": {
                "input_tokens_per_1k": 0.005,  # $0.005 per 1K input tokens
                "output_tokens_per_1k": 0.015,  # $0.015 per 1K output tokens
            },
            "gpt-3.5-turbo-0125": {
                "input_tokens_per_1k": 0.0005,  # $0.0005 per 1K input tokens
                "output_tokens_per_1k": 0.0015,  # $0.0015 per 1K output tokens
            },
        }

        tracker = OpenAICostTracker(pricing_config=pricing_config)

        assert tracker is not None
        assert tracker.pricing_config == pricing_config
        assert hasattr(tracker, "track_api_call")
        assert hasattr(tracker, "calculate_cost")

    def test_openai_cost_tracker_calculate_cost_gpt4o(self):
        """Test cost calculation for GPT-4o with token counts."""
        from services.finops_engine.openai_cost_tracker import OpenAICostTracker

        tracker = OpenAICostTracker()

        # Test cost calculation for GPT-4o
        cost = tracker.calculate_cost(
            model="gpt-4o",
            input_tokens=1000,  # 1K input tokens
            output_tokens=500,  # 0.5K output tokens
        )

        # Expected: (1000/1000 * 0.005) + (500/1000 * 0.015) = 0.005 + 0.0075 = 0.0125
        expected_cost = 0.0125
        assert abs(cost - expected_cost) < 0.0001, (
            f"Expected {expected_cost}, got {cost}"
        )

    def test_openai_cost_tracker_calculate_cost_gpt35_turbo(self):
        """Test cost calculation for GPT-3.5-turbo with token counts."""
        from services.finops_engine.openai_cost_tracker import OpenAICostTracker

        tracker = OpenAICostTracker()

        # Test cost calculation for GPT-3.5-turbo
        cost = tracker.calculate_cost(
            model="gpt-3.5-turbo-0125",
            input_tokens=2000,  # 2K input tokens
            output_tokens=1000,  # 1K output tokens
        )

        # Expected: (2000/1000 * 0.0005) + (1000/1000 * 0.0015) = 0.001 + 0.0015 = 0.0025
        expected_cost = 0.0025
        assert abs(cost - expected_cost) < 0.0001, (
            f"Expected {expected_cost}, got {cost}"
        )

    def test_openai_cost_tracker_track_api_call(self):
        """Test tracking an API call with metadata."""
        from services.finops_engine.openai_cost_tracker import OpenAICostTracker

        tracker = OpenAICostTracker()

        # Track an API call
        cost_event = tracker.track_api_call(
            model="gpt-4o",
            input_tokens=1500,
            output_tokens=800,
            operation="hook_generation",
            persona_id="ai_jesus",
            post_id="test_post_123",
        )

        # Verify cost event structure
        assert "cost_amount" in cost_event
        assert "timestamp" in cost_event
        assert "model" in cost_event
        assert "operation" in cost_event
        assert "persona_id" in cost_event
        assert "post_id" in cost_event
        assert "input_tokens" in cost_event
        assert "output_tokens" in cost_event

        # Verify cost calculation is correct
        expected_cost = (1500 / 1000 * 0.005) + (
            800 / 1000 * 0.015
        )  # 0.0075 + 0.012 = 0.0195
        assert abs(cost_event["cost_amount"] - expected_cost) < 0.0001


class TestInfrastructureCostTracker:
    """Test suite for Infrastructure cost tracking (K8s resources, monitoring, etc)."""

    def test_infrastructure_cost_tracker_initialization(self):
        """Test that InfrastructureCostTracker can be instantiated with K8s pricing config.

        This will fail because InfrastructureCostTracker doesn't exist yet!
        """
        from services.finops_engine.infrastructure_cost_tracker import (
            InfrastructureCostTracker,
        )

        # K8s resource pricing config
        pricing_config = {
            "kubernetes": {
                "cpu_hour_cost": 0.048,  # $0.048 per CPU hour
                "memory_gb_hour_cost": 0.012,  # $0.012 per GB memory hour
                "storage_gb_month_cost": 0.10,  # $0.10 per GB storage per month
            },
            "postgresql": {
                "query_cost_per_1k": 0.0001,  # $0.0001 per 1K queries
                "storage_gb_month_cost": 0.15,  # $0.15 per GB storage per month
            },
            "qdrant": {
                "query_cost_per_1k": 0.0002,  # $0.0002 per 1K vector queries
                "storage_gb_month_cost": 0.25,  # $0.25 per GB vector storage per month
            },
        }

        tracker = InfrastructureCostTracker(pricing_config=pricing_config)

        assert tracker is not None
        assert tracker.pricing_config == pricing_config
        assert hasattr(tracker, "track_k8s_resource_usage")
        assert hasattr(tracker, "track_database_operation")
        assert hasattr(tracker, "track_vector_db_operation")
        assert hasattr(tracker, "calculate_resource_cost")

    def test_infrastructure_cost_tracker_k8s_resource_cost(self):
        """Test K8s resource cost calculation."""
        from services.finops_engine.infrastructure_cost_tracker import (
            InfrastructureCostTracker,
        )

        tracker = InfrastructureCostTracker()

        # Test K8s resource cost for persona-runtime pod
        cost_event = tracker.track_k8s_resource_usage(
            resource_type="pod",
            resource_name="persona-runtime-abc123",
            service="persona_runtime",
            cpu_cores=1.0,  # 1 CPU core
            memory_gb=2.0,  # 2 GB memory
            duration_minutes=60,  # 1 hour
            operation="post_generation",
        )

        # Expected cost: (1.0 * 0.048) + (2.0 * 0.012) = 0.048 + 0.024 = 0.072 per hour
        expected_cost = 0.072
        assert abs(cost_event["cost_amount"] - expected_cost) < 0.0001
        assert cost_event["resource_type"] == "pod"
        assert cost_event["service"] == "persona_runtime"
        assert cost_event["cost_type"] == "kubernetes"

    def test_infrastructure_cost_tracker_database_operation(self):
        """Test database operation cost tracking."""
        from services.finops_engine.infrastructure_cost_tracker import (
            InfrastructureCostTracker,
        )

        tracker = InfrastructureCostTracker()

        # Test PostgreSQL query cost
        cost_event = tracker.track_database_operation(
            db_type="postgresql",
            operation="select",
            query_count=5000,  # 5K queries
            table="posts",
            persona_id="ai_jesus",
        )

        # Expected cost: 5000/1000 * 0.0001 = 5 * 0.0001 = 0.0005
        expected_cost = 0.0005
        assert abs(cost_event["cost_amount"] - expected_cost) < 0.0001
        assert cost_event["db_type"] == "postgresql"
        assert cost_event["operation"] == "select"
        assert cost_event["cost_type"] == "database"

    def test_infrastructure_cost_tracker_vector_db_operation(self):
        """Test vector database operation cost tracking."""
        from services.finops_engine.infrastructure_cost_tracker import (
            InfrastructureCostTracker,
        )

        tracker = InfrastructureCostTracker()

        # Test Qdrant vector search cost
        cost_event = tracker.track_vector_db_operation(
            operation="similarity_search",
            query_count=2500,  # 2.5K vector queries
            collection="posts_ai_jesus",
            persona_id="ai_jesus",
        )

        # Expected cost: 2500/1000 * 0.0002 = 2.5 * 0.0002 = 0.0005
        expected_cost = 0.0005
        assert abs(cost_event["cost_amount"] - expected_cost) < 0.0001
        assert cost_event["operation"] == "similarity_search"
        assert cost_event["collection"] == "posts_ai_jesus"
        assert cost_event["cost_type"] == "vector_db"


class TestCostEventStorage:
    """Test suite for cost event storage with sub-second latency requirements."""

    def test_cost_event_storage_initialization(self):
        """Test that CostEventStorage can be instantiated with database config.

        This will fail because CostEventStorage doesn't exist yet!
        """
        from services.finops_engine.cost_event_storage import CostEventStorage

        # Storage config for sub-second latency
        storage_config = {
            "database_url": "postgresql://localhost:5432/threads_agent",
            "max_connections": 10,
            "connection_timeout": 5.0,
            "query_timeout": 1.0,  # 1 second max for queries
            "batch_size": 100,  # Batch inserts for performance
            "target_latency_ms": 500,  # Sub-second latency target
        }

        storage = CostEventStorage(config=storage_config)

        assert storage is not None
        assert storage.config == storage_config
        assert hasattr(storage, "store_cost_event")
        assert hasattr(storage, "store_cost_events_batch")
        assert hasattr(storage, "get_cost_events")

    @pytest.mark.asyncio
    async def test_cost_event_storage_store_single_event(self):
        """Test storing a single cost event with sub-second latency."""
        from services.finops_engine.cost_event_storage import CostEventStorage
        import time

        storage = CostEventStorage()

        # Create a cost event
        cost_event = {
            "cost_amount": 0.0125,
            "timestamp": "2024-01-01T12:00:00Z",
            "cost_type": "openai_api",
            "model": "gpt-4o",
            "operation": "hook_generation",
            "persona_id": "ai_jesus",
            "post_id": "test_post_123",
            "input_tokens": 1000,
            "output_tokens": 500,
        }

        # Measure storage latency
        start_time = time.time()
        event_id = await storage.store_cost_event(cost_event)
        end_time = time.time()

        # Verify sub-second latency (500ms target)
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 500, (
            f"Storage latency {latency_ms:.2f}ms exceeds 500ms target"
        )

        # Verify event was stored
        assert event_id is not None
        assert isinstance(event_id, (int, str))

    @pytest.mark.asyncio
    async def test_cost_event_storage_batch_events(self):
        """Test storing multiple cost events in batch for better performance."""
        from services.finops_engine.cost_event_storage import CostEventStorage
        import time

        storage = CostEventStorage()

        # Create multiple cost events
        cost_events = [
            {
                "cost_amount": 0.0125,
                "timestamp": "2024-01-01T12:00:00Z",
                "cost_type": "openai_api",
                "model": "gpt-4o",
                "operation": f"hook_generation_{i}",
                "persona_id": "ai_jesus",
                "post_id": f"test_post_{i}",
                "input_tokens": 1000,
                "output_tokens": 500,
            }
            for i in range(10)
        ]

        # Measure batch storage latency
        start_time = time.time()
        event_ids = await storage.store_cost_events_batch(cost_events)
        end_time = time.time()

        # Verify reasonable latency for batch operation (should be faster per event than individual)
        latency_ms = (end_time - start_time) * 1000
        per_event_latency = latency_ms / len(cost_events)
        assert per_event_latency < 100, (
            f"Batch per-event latency {per_event_latency:.2f}ms too high"
        )

        # Verify all events were stored
        assert len(event_ids) == len(cost_events)
        assert all(event_id is not None for event_id in event_ids)

    @pytest.mark.asyncio
    async def test_cost_event_storage_query_events(self):
        """Test querying cost events by time range and filters."""
        from services.finops_engine.cost_event_storage import CostEventStorage

        storage = CostEventStorage()

        # Store some test events first
        test_events = [
            {
                "cost_amount": 0.0125,
                "timestamp": "2024-01-01T12:00:00Z",
                "cost_type": "openai_api",
                "persona_id": "ai_jesus",
                "operation": "hook_generation",
            },
            {
                "cost_amount": 0.072,
                "timestamp": "2024-01-01T12:01:00Z",
                "cost_type": "kubernetes",
                "persona_id": "ai_jesus",
                "operation": "post_generation",
            },
        ]

        await storage.store_cost_events_batch(test_events)

        # Query events by persona_id
        events = await storage.get_cost_events(
            persona_id="ai_jesus",
            start_time="2024-01-01T11:59:00Z",
            end_time="2024-01-01T12:02:00Z",
        )

        # Verify query results
        assert len(events) >= 2  # Should find at least our test events
        assert all(event["persona_id"] == "ai_jesus" for event in events)

    def test_cost_event_storage_database_schema(self):
        """Test that the database schema supports all required cost event fields."""
        from services.finops_engine.cost_event_storage import CostEventStorage

        storage = CostEventStorage()

        # Verify schema supports all required fields
        required_fields = [
            "id",
            "cost_amount",
            "timestamp",
            "cost_type",
            "persona_id",
            "operation",
            "metadata",
            "created_at",
        ]

        schema = storage.get_table_schema()
        for field in required_fields:
            assert field in schema, f"Missing required field in schema: {field}"


class TestPrometheusMetricsEmitter:
    """Test suite for Prometheus metrics emission for real-time monitoring."""

    def test_prometheus_metrics_emitter_initialization(self):
        """Test that PrometheusMetricsEmitter can be instantiated.

        This will fail because PrometheusMetricsEmitter doesn't exist yet!
        """
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        assert emitter is not None
        assert hasattr(emitter, "emit_cost_metric")
        assert hasattr(emitter, "emit_latency_metric")
        assert hasattr(emitter, "emit_alert_threshold_metric")
        assert hasattr(emitter, "update_cost_per_post_metric")

    def test_prometheus_emit_openai_cost_metric(self):
        """Test emitting OpenAI cost metrics to Prometheus."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Emit OpenAI cost metric
        cost_event = {
            "cost_amount": 0.0125,
            "cost_type": "openai_api",
            "model": "gpt-4o",
            "operation": "hook_generation",
            "persona_id": "ai_jesus",
        }

        emitter.emit_cost_metric(cost_event)

        # Verify metric was emitted (would check Prometheus registry in real implementation)
        assert hasattr(emitter, "_metrics_emitted")
        assert len(emitter._metrics_emitted) > 0

        # Check specific metric
        openai_metrics = [
            m
            for m in emitter._metrics_emitted
            if m["metric_name"] == "openai_api_costs_usd_total"
        ]
        assert len(openai_metrics) == 1
        assert openai_metrics[0]["value"] == 0.0125
        assert openai_metrics[0]["labels"]["model"] == "gpt-4o"

    def test_prometheus_emit_infrastructure_cost_metric(self):
        """Test emitting infrastructure cost metrics to Prometheus."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Emit K8s cost metric
        cost_event = {
            "cost_amount": 0.072,
            "cost_type": "kubernetes",
            "service": "persona_runtime",
            "resource_type": "pod",
            "operation": "post_generation",
        }

        emitter.emit_cost_metric(cost_event)

        # Verify K8s metric was emitted
        k8s_metrics = [
            m
            for m in emitter._metrics_emitted
            if m["metric_name"] == "kubernetes_resource_costs_usd_total"
        ]
        assert len(k8s_metrics) == 1
        assert k8s_metrics[0]["value"] == 0.072
        assert k8s_metrics[0]["labels"]["service"] == "persona_runtime"

    def test_prometheus_emit_cost_per_post_metric(self):
        """Test emitting cost per post metrics for $0.02 target tracking."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Update cost per post for a persona
        emitter.update_cost_per_post_metric(
            persona_id="ai_jesus",
            cost_per_post=0.018,  # Under the $0.02 target
            post_id="test_post_123",
        )

        # Verify cost per post metric
        cost_per_post_metrics = [
            m
            for m in emitter._metrics_emitted
            if m["metric_name"] == "cost_per_post_usd"
        ]
        assert len(cost_per_post_metrics) == 1
        assert cost_per_post_metrics[0]["value"] == 0.018
        assert cost_per_post_metrics[0]["labels"]["persona_id"] == "ai_jesus"

    def test_prometheus_emit_alert_threshold_metric(self):
        """Test emitting alert threshold metrics for cost monitoring."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Emit alert for cost threshold breach
        emitter.emit_alert_threshold_metric(
            metric_name="cost_per_post_threshold_breach",
            persona_id="ai_jesus",
            current_value=0.045,  # Above $0.02 * 2 = $0.04 threshold
            threshold_value=0.04,
            severity="warning",
        )

        # Verify alert metric
        alert_metrics = [
            m
            for m in emitter._metrics_emitted
            if m["metric_name"] == "cost_per_post_threshold_breach"
        ]
        assert len(alert_metrics) == 1
        assert alert_metrics[0]["value"] == 1  # Alert active
        assert alert_metrics[0]["labels"]["persona_id"] == "ai_jesus"
        assert alert_metrics[0]["labels"]["severity"] == "warning"

    def test_prometheus_emit_latency_metric(self):
        """Test emitting storage latency metrics."""
        from services.finops_engine.prometheus_metrics_emitter import (
            PrometheusMetricsEmitter,
        )

        emitter = PrometheusMetricsEmitter()

        # Emit storage latency metric
        emitter.emit_latency_metric(
            operation="cost_event_storage",
            latency_ms=150.5,  # Sub-second latency
            status="success",
        )

        # Verify latency metric
        latency_metrics = [
            m
            for m in emitter._metrics_emitted
            if m["metric_name"] == "finops_operation_latency_ms"
        ]
        assert len(latency_metrics) == 1
        assert latency_metrics[0]["value"] == 150.5
        assert latency_metrics[0]["labels"]["operation"] == "cost_event_storage"


class TestIntegratedCostTrackingWithAlerts:
    """Integration test for complete cost tracking with $0.02 target and 2x alert threshold."""

    @pytest.mark.asyncio
    async def test_complete_post_generation_cost_tracking_under_threshold(self):
        """Test complete cost tracking for a post generation that stays under $0.02 threshold.

        This will fail until we integrate all components in ViralFinOpsEngine!
        """
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        # Initialize the complete system
        config = {
            "cost_threshold_per_post": 0.02,  # $0.02 target
            "alert_threshold_multiplier": 2.0,  # Alert at $0.04
            "storage_latency_target_ms": 500,
        }

        engine = ViralFinOpsEngine(config=config)

        # Simulate a complete post generation workflow
        post_id = "test_post_integration_001"
        persona_id = "ai_jesus"

        # 1. Track OpenAI costs (hook + body generation)
        await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=800,  # Hook generation
            output_tokens=400,
            operation="hook_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        await engine.track_openai_cost(
            model="gpt-3.5-turbo-0125",
            input_tokens=1200,  # Body generation
            output_tokens=800,
            operation="body_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        # 2. Track infrastructure costs (K8s pod usage)
        await engine.track_infrastructure_cost(
            resource_type="kubernetes",
            service="persona_runtime",
            cpu_cores=0.5,
            memory_gb=1.0,
            duration_minutes=3,  # 3 minutes processing
            operation="post_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        # 3. Track vector DB costs (deduplication check)
        await engine.track_vector_db_cost(
            operation="similarity_search",
            query_count=500,
            collection=f"posts_{persona_id}",
            persona_id=persona_id,
            post_id=post_id,
        )

        # 4. Calculate total cost per post
        total_cost = await engine.calculate_total_post_cost(post_id)

        # Verify total cost is under $0.02 threshold
        assert total_cost < 0.02, (
            f"Total cost ${total_cost:.4f} exceeds $0.02 threshold"
        )

        # 5. Verify metrics were emitted
        assert len(engine.prometheus_client._metrics_emitted) > 0

        # 6. Verify no alert was triggered (under 2x threshold)
        alert_metrics = [
            m
            for m in engine.prometheus_client._metrics_emitted
            if "threshold_breach" in m["metric_name"]
        ]
        if alert_metrics:
            assert all(m["value"] == 0 for m in alert_metrics), (
                "No alerts should be active under threshold"
            )

    @pytest.mark.asyncio
    async def test_complete_post_generation_cost_tracking_over_threshold(self):
        """Test complete cost tracking that triggers 2x alert threshold ($0.04)."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Simulate expensive post generation (multiple iterations, complex processing)
        post_id = "test_post_expensive_002"
        persona_id = "ai_jesus"

        # High OpenAI costs (multiple revisions)
        for i in range(5):  # 5 revision cycles
            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=2000,  # Large context
                output_tokens=1000,  # Detailed output
                operation=f"revision_{i}",
                persona_id=persona_id,
                post_id=post_id,
            )

        # High infrastructure costs (long processing time)
        await engine.track_infrastructure_cost(
            resource_type="kubernetes",
            service="persona_runtime",
            cpu_cores=2.0,  # High CPU usage
            memory_gb=4.0,  # High memory usage
            duration_minutes=30,  # Long processing time
            operation="complex_post_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        # Calculate total cost per post
        total_cost = await engine.calculate_total_post_cost(post_id)

        # Verify total cost exceeds 2x threshold ($0.04)
        threshold = 0.02 * 2.0  # $0.04
        assert total_cost > threshold, (
            f"Total cost ${total_cost:.4f} should exceed ${threshold:.2f} threshold"
        )

        # Verify alert was triggered
        alert_metrics = [
            m
            for m in engine.prometheus_client._metrics_emitted
            if "threshold_breach" in m["metric_name"]
        ]
        assert len(alert_metrics) > 0, (
            "Alert should be triggered for cost threshold breach"
        )
        assert any(m["value"] == 1 for m in alert_metrics), "Alert should be active"

    @pytest.mark.asyncio
    async def test_cost_tracking_performance_requirements(self):
        """Test that cost tracking meets sub-second latency requirements."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine
        import time

        engine = ViralFinOpsEngine()

        # Test single cost event performance
        start_time = time.time()

        await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            operation="performance_test",
            persona_id="ai_jesus",
            post_id="perf_test_001",
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Verify sub-second latency requirement
        assert latency_ms < 500, (
            f"Cost tracking latency {latency_ms:.2f}ms exceeds 500ms requirement"
        )

        # Test batch performance (10 events)
        start_time = time.time()

        for i in range(10):
            await engine.track_openai_cost(
                model="gpt-3.5-turbo-0125",
                input_tokens=500,
                output_tokens=300,
                operation=f"batch_test_{i}",
                persona_id="ai_jesus",
                post_id=f"batch_test_{i}",
            )

        end_time = time.time()
        batch_latency_ms = (end_time - start_time) * 1000
        per_event_latency = batch_latency_ms / 10

        # Verify reasonable batch performance
        assert per_event_latency < 100, (
            f"Batch per-event latency {per_event_latency:.2f}ms too high"
        )
