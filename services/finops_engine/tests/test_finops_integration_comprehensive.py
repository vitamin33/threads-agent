"""
Comprehensive Integration Tests for FinOps Cost Tracking & Optimization Engine (CRA-240)

Tests the complete system integration covering:
1. ViralFinOpsEngine - Main orchestrator
2. PostCostAttributor - 95% accuracy cost tracking per post
3. CostAnomalyDetector - <60s anomaly detection with multiple algorithms
4. AlertManager - Multi-channel notifications (Slack, PagerDuty, Email)
5. CircuitBreaker - Automated cost control with throttling

Key Requirements Validated:
- $0.02 per post cost target with 2x alert threshold ($0.04)
- Sub-second cost event storage latency
- Real-time Prometheus metrics emission
- End-to-end cost tracking from generation through publication
"""

import pytest
import asyncio
import time


class TestFinOpsIntegrationWorkflow:
    """Integration tests for complete FinOps workflow scenarios."""

    @pytest.mark.asyncio
    async def test_complete_viral_post_generation_under_cost_target(self):
        """
        Test complete viral post generation staying under $0.02 cost target.

        Validates entire workflow:
        1. Track OpenAI costs (hook + body generation)
        2. Track infrastructure costs (K8s pods)
        3. Track vector DB costs (deduplication)
        4. Calculate total cost per post
        5. Verify metrics emission
        6. Confirm no alerts triggered
        """
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        # Initialize FinOps engine with strict cost controls
        config = {
            "cost_threshold_per_post": 0.02,  # $0.02 target
            "alert_threshold_multiplier": 2.0,  # Alert at $0.04
            "storage_latency_target_ms": 500,  # Sub-second latency
            "anomaly_detection_enabled": True,
            "anomaly_check_interval_seconds": 30,
        }

        engine = ViralFinOpsEngine(config=config)

        # Test data for viral post generation
        post_id = "viral_post_001"
        persona_id = "ai_jesus"

        # Phase 1: Hook Generation (GPT-4o for quality)
        start_time = time.time()
        hook_cost_event = await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=800,  # Context + persona + trend data
            output_tokens=400,  # Generated hook
            operation="hook_generation",
            persona_id=persona_id,
            post_id=post_id,
        )
        hook_latency = (time.time() - start_time) * 1000

        # Verify hook generation cost and latency
        assert hook_cost_event["cost_amount"] <= 0.012  # Should be ~$0.011
        assert hook_latency < 500  # Sub-second latency
        assert hook_cost_event["cost_type"] == "openai_api"
        assert hook_cost_event["model"] == "gpt-4o"

        # Phase 2: Body Generation (GPT-3.5-turbo for efficiency)
        body_cost_event = await engine.track_openai_cost(
            model="gpt-3.5-turbo-0125",
            input_tokens=1200,  # Hook + context + instructions
            output_tokens=800,  # Generated body content
            operation="body_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        # Verify body generation cost
        assert body_cost_event["cost_amount"] <= 0.0025  # Should be ~$0.0018

        # Phase 3: Infrastructure Costs (K8s processing)
        infra_cost_event = await engine.track_infrastructure_cost(
            resource_type="kubernetes",
            service="persona_runtime",
            cpu_cores=0.5,  # Half CPU core
            memory_gb=1.0,  # 1GB memory
            duration_minutes=3,  # 3 minutes processing
            operation="post_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        # Verify infrastructure cost
        assert infra_cost_event["cost_amount"] <= 0.004  # Should be ~$0.0036

        # Phase 4: Vector DB Deduplication Check
        vector_cost_event = await engine.track_vector_db_cost(
            operation="similarity_search",
            query_count=500,  # Check against existing posts
            collection=f"posts_{persona_id}",
            persona_id=persona_id,
            post_id=post_id,
        )

        # Verify vector DB cost
        assert vector_cost_event["cost_amount"] <= 0.0002  # Should be ~$0.0001

        # Phase 5: Calculate total cost and verify target
        total_cost = await engine.calculate_total_post_cost(post_id)

        # Verify total cost meets $0.02 target
        assert total_cost <= 0.02, f"Total cost ${total_cost:.4f} exceeds $0.02 target"
        assert total_cost > 0.010, (
            f"Total cost ${total_cost:.4f} seems too low, check calculations"
        )

        # Phase 6: Verify cost breakdown through PostCostAttributor
        cost_breakdown = await engine.post_cost_attributor.get_post_cost_breakdown(
            post_id
        )

        assert cost_breakdown["post_id"] == post_id
        assert cost_breakdown["total_cost"] == total_cost
        assert cost_breakdown["accuracy_score"] >= 0.95  # 95% accuracy requirement
        assert len(cost_breakdown["audit_trail"]) == 4  # 4 cost events tracked

        # Verify cost breakdown by type
        assert "openai_api" in cost_breakdown["cost_breakdown"]
        assert "kubernetes" in cost_breakdown["cost_breakdown"]
        assert "vector_db" in cost_breakdown["cost_breakdown"]

        # Phase 7: Verify Prometheus metrics emission
        metrics_emitted = engine.prometheus_client.get_emitted_metrics()
        assert len(metrics_emitted) >= 4  # At least 4 metrics emitted

        # Check specific metrics
        openai_metrics = [
            m for m in metrics_emitted if "openai_api_costs" in m["metric_name"]
        ]
        assert len(openai_metrics) >= 2  # Hook + body generation

        k8s_metrics = [
            m
            for m in metrics_emitted
            if "kubernetes_resource_costs" in m["metric_name"]
        ]
        assert len(k8s_metrics) >= 1

        # Phase 8: Verify no alerts triggered (under threshold)
        alert_metrics = [
            m for m in metrics_emitted if "threshold_breach" in m["metric_name"]
        ]
        if alert_metrics:
            assert all(m["value"] == 0 for m in alert_metrics), (
                "No alerts should be active under threshold"
            )

        # Phase 9: Verify anomaly detection returns normal
        anomaly_result = await engine.check_for_anomalies(persona_id)
        assert len(anomaly_result["anomalies_detected"]) == 0
        assert len(anomaly_result["alerts_sent"]) == 0
        assert len(anomaly_result["actions_taken"]) == 0

    @pytest.mark.asyncio
    async def test_expensive_post_generation_triggers_anomaly_detection_and_alerts(
        self,
    ):
        """
        Test expensive post generation that triggers anomaly detection and alerts.

        Simulates scenario where costs exceed thresholds:
        1. Multiple expensive OpenAI calls (revisions)
        2. High infrastructure usage (complex processing)
        3. Extensive vector DB operations
        4. Anomaly detection triggers
        5. Alerts sent to multiple channels
        6. Circuit breaker activates cost controls
        """
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine(
            {
                "cost_threshold_per_post": 0.02,
                "alert_threshold_multiplier": 2.0,
                "anomaly_detection_enabled": True,
            }
        )

        post_id = "expensive_post_002"
        persona_id = "ai_jesus"

        # First establish baseline costs with normal posts
        for i in range(5):
            await engine.track_openai_cost(
                model="gpt-3.5-turbo-0125",
                input_tokens=1000,
                output_tokens=500,
                operation=f"baseline_{i}",
                persona_id=persona_id,
                post_id=f"baseline_post_{i}",
            )

        # Simulate expensive scenario: Multiple revision cycles
        for revision in range(5):  # 5 revision cycles due to quality issues
            # Expensive hook revisions with GPT-4o
            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=2000,  # Large context each time
                output_tokens=1000,  # Detailed output
                operation=f"hook_revision_{revision}",
                persona_id=persona_id,
                post_id=post_id,
            )

            # Body regeneration each cycle
            await engine.track_openai_cost(
                model="gpt-4o",  # Using expensive model due to quality issues
                input_tokens=1500,
                output_tokens=1200,
                operation=f"body_revision_{revision}",
                persona_id=persona_id,
                post_id=post_id,
            )

        # Expensive infrastructure usage (complex AI processing)
        await engine.track_infrastructure_cost(
            resource_type="kubernetes",
            service="persona_runtime",
            cpu_cores=2.0,  # High CPU for complex processing
            memory_gb=4.0,  # High memory usage
            duration_minutes=30,  # Long processing time (30 minutes)
            operation="complex_post_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        # Extensive vector DB operations (multiple similarity checks)
        for search_batch in range(10):  # 10 search batches
            await engine.track_vector_db_cost(
                operation="similarity_search",
                query_count=1000,  # 1K queries per batch
                collection=f"posts_{persona_id}",
                persona_id=persona_id,
                post_id=post_id,
            )

        # Calculate total cost (should exceed thresholds)
        total_cost = await engine.calculate_total_post_cost(post_id)

        # Verify cost exceeds 2x threshold ($0.04)
        alert_threshold = 0.02 * 2.0  # $0.04
        assert total_cost > alert_threshold, (
            f"Total cost ${total_cost:.4f} should exceed ${alert_threshold:.2f}"
        )

        # Verify cost is significantly higher than normal
        assert total_cost > 0.10, (
            f"Total cost ${total_cost:.4f} should be significantly elevated"
        )

        # Check that anomaly detection triggers
        anomaly_result = await engine.check_for_anomalies(persona_id)

        # Should detect statistical anomalies
        assert len(anomaly_result["anomalies_detected"]) > 0
        anomaly = anomaly_result["anomalies_detected"][0]
        assert anomaly["is_anomaly"] is True
        assert anomaly["severity"] in ["high", "critical"]

        # Should send alerts through configured channels
        assert len(anomaly_result["alerts_sent"]) > 0
        alert_result = anomaly_result["alerts_sent"][0]
        assert "slack" in alert_result  # At minimum, Slack alert

        # Should trigger circuit breaker actions
        if anomaly["severity"] == "critical":
            assert len(anomaly_result["actions_taken"]) > 0
            actions = anomaly_result["actions_taken"][0]
            assert (
                "throttle_requests" in actions or "switch_to_cheaper_models" in actions
            )

        # Verify alert metrics were emitted
        metrics_emitted = engine.prometheus_client.get_emitted_metrics()
        alert_metrics = [
            m for m in metrics_emitted if "threshold_breach" in m["metric_name"]
        ]
        assert len(alert_metrics) > 0
        assert any(m["value"] == 1 for m in alert_metrics), "Alert should be active"

    @pytest.mark.asyncio
    async def test_finops_system_performance_under_load(self):
        """
        Test FinOps system performance under realistic load.

        Simulates concurrent post generations to validate:
        1. Sub-second latency maintained under load
        2. Accurate cost tracking across concurrent operations
        3. Metrics emission performance
        4. No performance degradation in anomaly detection
        """
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Test concurrent post generations
        concurrent_posts = 10
        persona_id = "ai_jesus"

        async def generate_post_costs(post_index: int):
            """Simulate cost tracking for a single post generation."""
            post_id = f"concurrent_post_{post_index:03d}"

            start_time = time.time()

            # Track typical costs for a post
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
                input_tokens=1200,
                output_tokens=800,
                operation="body_generation",
                persona_id=persona_id,
                post_id=post_id,
            )

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

            total_cost = await engine.calculate_total_post_cost(post_id)
            end_time = time.time()

            return {
                "post_id": post_id,
                "total_cost": total_cost,
                "processing_time": end_time - start_time,
            }

        # Execute concurrent post generations
        start_time = time.time()

        tasks = [generate_post_costs(i) for i in range(concurrent_posts)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_duration = end_time - start_time

        # Verify performance requirements
        assert total_duration < 10.0, (
            f"Concurrent processing took {total_duration:.2f}s, too slow"
        )

        # Verify all posts were processed successfully
        assert len(results) == concurrent_posts
        assert all(r["total_cost"] > 0 for r in results)

        # Verify individual post processing times are reasonable
        max_processing_time = max(r["processing_time"] for r in results)
        assert max_processing_time < 2.0, (
            f"Max processing time {max_processing_time:.2f}s too high"
        )

        # Verify cost calculations are accurate and consistent
        costs = [r["total_cost"] for r in results]
        avg_cost = sum(costs) / len(costs)
        assert 0.015 <= avg_cost <= 0.02, (
            f"Average cost ${avg_cost:.4f} outside expected range"
        )

        # Verify minimal cost variance (should be consistent)
        cost_variance = max(costs) - min(costs)
        assert cost_variance < 0.005, (
            f"Cost variance {cost_variance:.4f} too high, inconsistent tracking"
        )

        # Verify metrics were emitted for all posts
        metrics_emitted = engine.prometheus_client.get_emitted_metrics()
        assert (
            len(metrics_emitted) >= concurrent_posts * 3
        )  # At least 3 metrics per post

        # Test anomaly detection performance under load
        anomaly_start = time.time()
        await engine.check_for_anomalies(persona_id)
        anomaly_duration = time.time() - anomaly_start

        # Verify anomaly detection remains fast
        assert anomaly_duration < 1.0, (
            f"Anomaly detection took {anomaly_duration:.2f}s, too slow"
        )

    @pytest.mark.asyncio
    async def test_finops_system_integration_with_cost_attribution_api(self):
        """
        Test integration between FinOps engine and cost attribution API.

        Validates complete end-to-end flow:
        1. Track costs through ViralFinOpsEngine
        2. Query costs through PostCostAttributor API
        3. Verify data consistency and accuracy
        4. Test API performance requirements
        """
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Generate costs for multiple posts
        test_posts = ["api_test_001", "api_test_002", "api_test_003"]
        persona_id = "ai_jesus"

        for post_id in test_posts:
            # Track diverse cost types
            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=500,
                operation="hook_generation",
                persona_id=persona_id,
                post_id=post_id,
            )

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

            await engine.track_vector_db_cost(
                operation="similarity_search",
                query_count=500,
                collection=f"posts_{persona_id}",
                persona_id=persona_id,
                post_id=post_id,
            )

        # Test individual post cost queries
        for post_id in test_posts:
            query_start = time.time()
            breakdown = await engine.post_cost_attributor.get_post_cost_breakdown(
                post_id
            )
            query_duration = time.time() - query_start

            # Verify query performance
            assert query_duration < 0.5, (
                f"Cost query took {query_duration:.3f}s, exceeds 500ms limit"
            )

            # Verify data structure
            assert breakdown["post_id"] == post_id
            assert breakdown["total_cost"] > 0
            assert breakdown["accuracy_score"] >= 0.95
            assert len(breakdown["audit_trail"]) == 3  # 3 cost events per post

            # Verify cost breakdown completeness
            assert "openai_api" in breakdown["cost_breakdown"]
            assert "kubernetes" in breakdown["cost_breakdown"]
            assert "vector_db" in breakdown["cost_breakdown"]

            # Verify audit trail chronological order
            timestamps = [entry["timestamp"] for entry in breakdown["audit_trail"]]
            assert timestamps == sorted(timestamps), (
                "Audit trail should be chronologically ordered"
            )

        # Test bulk cost calculations
        bulk_start = time.time()
        total_costs = []
        for post_id in test_posts:
            total_cost = await engine.post_cost_attributor.calculate_total_post_cost(
                post_id
            )
            total_costs.append(total_cost)
        bulk_duration = time.time() - bulk_start

        # Verify bulk calculation performance
        assert bulk_duration < 1.0, (
            f"Bulk cost calculation took {bulk_duration:.3f}s too long"
        )

        # Verify cost consistency (roughly the expected range)
        assert all(0.010 <= cost <= 0.030 for cost in total_costs), (
            f"Costs out of range: {total_costs}"
        )

        # Test data integrity between engine and attributor
        for i, post_id in enumerate(test_posts):
            engine_total = await engine.calculate_total_post_cost(post_id)
            attributor_total = total_costs[i]

            # Should match within floating-point precision
            assert abs(engine_total - attributor_total) < 0.0001, (
                f"Cost mismatch: engine={engine_total}, attributor={attributor_total}"
            )


class TestFinOpsSystemEdgeCases:
    """Test edge cases and error scenarios in the FinOps system."""

    @pytest.mark.asyncio
    async def test_missing_cost_data_graceful_handling(self):
        """Test system behavior when cost data is missing or incomplete."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Test querying non-existent post
        breakdown = await engine.post_cost_attributor.get_post_cost_breakdown(
            "nonexistent_post"
        )

        assert breakdown["post_id"] == "nonexistent_post"
        assert breakdown["total_cost"] == 0.0
        assert breakdown["cost_breakdown"] == {}
        assert breakdown["accuracy_score"] >= 0.95  # Should still meet accuracy target

        # Test calculating cost for post with no data
        total_cost = await engine.calculate_total_post_cost("empty_post")
        assert total_cost == 0.0

        # Test anomaly detection with insufficient baseline data
        anomaly_result = await engine.check_for_anomalies("unknown_persona")
        assert len(anomaly_result["anomalies_detected"]) == 0

    @pytest.mark.asyncio
    async def test_extremely_high_cost_scenario(self):
        """Test system behavior with extremely high costs (e.g., runaway AI)."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine(
            {
                "anomaly_detection_enabled": True,
                "cost_threshold_per_post": 0.02,
            }
        )

        post_id = "runaway_cost_001"
        persona_id = "ai_jesus"

        # First establish baseline costs
        for i in range(5):
            await engine.track_openai_cost(
                model="gpt-3.5-turbo-0125",
                input_tokens=1000,
                output_tokens=500,
                operation=f"baseline_{i}",
                persona_id=persona_id,
                post_id=f"baseline_post_{i}",
            )

        # Simulate runaway AI scenario with massive token usage
        await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=50000,  # 50K input tokens
            output_tokens=30000,  # 30K output tokens
            operation="runaway_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        total_cost = await engine.calculate_total_post_cost(post_id)

        # Should be extremely high cost (50K input + 30K output tokens with gpt-4o = $0.70)
        assert total_cost > 0.5, f"Cost ${total_cost:.4f} should be extremely high"

        # Should trigger critical anomaly detection
        anomaly_result = await engine.check_for_anomalies(persona_id)
        assert len(anomaly_result["anomalies_detected"]) > 0

        anomaly = anomaly_result["anomalies_detected"][0]
        assert anomaly["severity"] == "critical"
        assert anomaly["multiplier"] > 30.0  # Should be massive multiplier

        # Should trigger circuit breaker with aggressive actions
        assert len(anomaly_result["actions_taken"]) > 0
        actions = anomaly_result["actions_taken"][0]
        assert "throttle_requests" in actions
        assert (
            actions["throttle_requests"]["new_rate_limit"] <= 10
        )  # Aggressive throttling

    @pytest.mark.asyncio
    async def test_zero_and_negative_cost_handling(self):
        """Test handling of zero costs and validation of negative costs."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        post_id = "zero_cost_001"

        # Test zero-cost tracking (cached results, free tier, etc.)
        await engine.post_cost_attributor.track_cost_for_post(
            post_id=post_id,
            cost_type="cached_api_call",
            cost_amount=0.0,  # Zero cost
            metadata={"cache_hit": True, "model": "gpt-4o"},
        )

        breakdown = await engine.post_cost_attributor.get_post_cost_breakdown(post_id)
        assert breakdown["total_cost"] == 0.0
        assert breakdown["accuracy_score"] >= 0.95

        # Test that negative costs raise appropriate errors
        with pytest.raises(ValueError):
            await engine.post_cost_attributor.track_cost_for_post(
                post_id="negative_cost_001",
                cost_type="invalid_cost",
                cost_amount=-0.01,  # Negative cost should be invalid
                metadata={},
            )

    @pytest.mark.asyncio
    async def test_concurrent_cost_tracking_race_conditions(self):
        """Test concurrent cost tracking for the same post to check for race conditions."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        post_id = "race_condition_001"
        persona_id = "ai_jesus"

        async def track_concurrent_cost(cost_index: int):
            """Track a cost event concurrently."""
            return await engine.track_openai_cost(
                model="gpt-3.5-turbo-0125",
                input_tokens=1000,
                output_tokens=500,
                operation=f"concurrent_operation_{cost_index}",
                persona_id=persona_id,
                post_id=post_id,
            )

        # Track 5 concurrent cost events for the same post
        tasks = [track_concurrent_cost(i) for i in range(5)]
        cost_events = await asyncio.gather(*tasks)

        # Verify all events were tracked
        assert len(cost_events) == 5
        assert all(event["post_id"] == post_id for event in cost_events)

        # Verify total cost calculation is correct
        total_cost = await engine.calculate_total_post_cost(post_id)
        expected_cost = 5 * cost_events[0]["cost_amount"]  # All should be identical

        assert abs(total_cost - expected_cost) < 0.0001, (
            f"Race condition detected: expected={expected_cost}, actual={total_cost}"
        )

        # Verify audit trail completeness
        breakdown = await engine.post_cost_attributor.get_post_cost_breakdown(post_id)
        assert len(breakdown["audit_trail"]) == 5, (
            "All concurrent events should be tracked"
        )


class TestFinOpsSystemRecovery:
    """Test system recovery and resilience scenarios."""

    @pytest.mark.asyncio
    async def test_system_recovery_after_storage_failure(self):
        """Test system behavior during and after storage failures."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Simulate storage failure
        original_store_method = engine.cost_storage.store_cost_event

        async def failing_store_method(*args, **kwargs):
            raise Exception("Database connection failed")

        engine.cost_storage.store_cost_event = failing_store_method

        # Attempt to track cost during failure
        with pytest.raises(Exception, match="Database connection failed"):
            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=500,
                operation="test_during_failure",
                persona_id="ai_jesus",
                post_id="failure_test_001",
            )

        # Restore storage functionality
        engine.cost_storage.store_cost_event = original_store_method

        # Verify system recovery
        cost_event = await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            operation="test_after_recovery",
            persona_id="ai_jesus",
            post_id="recovery_test_001",
        )

        assert cost_event is not None
        assert cost_event["cost_amount"] > 0

    @pytest.mark.asyncio
    async def test_metrics_emission_resilience(self):
        """Test metrics emission continues even if individual metrics fail."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Test that cost tracking continues even if metrics emission fails
        original_emit_method = engine.prometheus_client.emit_cost_metric

        def failing_emit_method(*args, **kwargs):
            raise Exception("Prometheus server unreachable")

        engine.prometheus_client.emit_cost_metric = failing_emit_method

        # Should still track costs successfully despite metrics failure
        cost_event = await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            operation="test_metrics_failure",
            persona_id="ai_jesus",
            post_id="metrics_failure_001",
        )

        assert cost_event is not None
        assert cost_event["cost_amount"] > 0

        # Cost calculation should still work
        total_cost = await engine.calculate_total_post_cost("metrics_failure_001")
        assert total_cost > 0

        # Restore metrics functionality
        engine.prometheus_client.emit_cost_metric = original_emit_method
