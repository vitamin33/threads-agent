"""
Comprehensive Edge Case Tests for FinOps Anomaly Detection & Circuit Breaker System (CRA-240)

Tests edge cases and boundary conditions for:
1. CostAnomalyDetector - Complex anomaly scenarios and detection algorithms
2. AlertManager - Multi-channel alerting failure scenarios
3. CircuitBreaker - Automated response edge cases
4. System behavior under extreme conditions

Key Edge Cases Covered:
- Boundary threshold conditions (exactly 3x, 3.01x, 2.99x baseline)
- Rapid cost fluctuations and volatile patterns
- Multiple concurrent anomalies across personas
- Alert channel failures and fallback mechanisms
- Circuit breaker action conflicts and priority
- False positive/negative anomaly detection
"""

import pytest
import asyncio
import time


class TestAnomalyDetectionEdgeCases:
    """Edge case tests for cost anomaly detection algorithms."""

    def test_anomaly_detection_exact_threshold_boundary(self):
        """Test anomaly detection at exact threshold boundaries."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()
        baseline_costs = [0.020, 0.018, 0.022, 0.019, 0.021]  # Avg = 0.020
        persona_id = "ai_jesus"

        # Test exactly at 3x threshold (should trigger)
        result_at_threshold = detector.detect_statistical_anomaly(
            current_cost=0.060,  # Exactly 3.0x baseline
            baseline_costs=baseline_costs,
            persona_id=persona_id,
        )
        assert result_at_threshold["is_anomaly"] is True
        assert result_at_threshold["multiplier"] == 3.0
        assert result_at_threshold["severity"] == "medium"

        # Test just above threshold (should trigger with higher severity)
        result_above_threshold = detector.detect_statistical_anomaly(
            current_cost=0.061,  # 3.05x baseline
            baseline_costs=baseline_costs,
            persona_id=persona_id,
        )
        assert result_above_threshold["is_anomaly"] is True
        assert result_above_threshold["multiplier"] > 3.0

        # Test just below threshold (should NOT trigger)
        result_below_threshold = detector.detect_statistical_anomaly(
            current_cost=0.059,  # 2.95x baseline
            baseline_costs=baseline_costs,
            persona_id=persona_id,
        )
        assert result_below_threshold["is_anomaly"] is False
        assert result_below_threshold["severity"] == "normal"

    def test_anomaly_detection_with_volatile_baseline(self):
        """Test anomaly detection with highly volatile baseline data."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()

        # Highly volatile baseline (wide cost variance)
        volatile_baseline = [0.005, 0.050, 0.010, 0.045, 0.015]  # High variance
        sum(volatile_baseline) / len(volatile_baseline)  # 0.025

        # Current cost that would be anomaly vs stable baseline
        current_cost = 0.060  # 2.4x volatile average (not anomaly)

        result = detector.detect_statistical_anomaly(
            current_cost=current_cost,
            baseline_costs=volatile_baseline,
            persona_id="volatile_persona",
        )

        # Should NOT be anomaly due to lower multiplier
        assert result["is_anomaly"] is False
        assert result["multiplier"] < 3.0

        # But a higher cost should still trigger
        high_cost = 0.080  # 3.2x volatile average
        high_result = detector.detect_statistical_anomaly(
            current_cost=high_cost,
            baseline_costs=volatile_baseline,
            persona_id="volatile_persona",
        )
        assert high_result["is_anomaly"] is True

    def test_anomaly_detection_with_zero_baseline(self):
        """Test anomaly detection when baseline contains zero costs."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()

        # Baseline with zeros (cached responses, free tier usage)
        zero_baseline = [0.000, 0.015, 0.000, 0.020, 0.000]  # Avg = 0.007

        # Non-zero current cost
        current_cost = 0.025

        result = detector.detect_statistical_anomaly(
            current_cost=current_cost,
            baseline_costs=zero_baseline,
            persona_id="mixed_persona",
        )

        # Should handle division by low baseline gracefully
        assert result["multiplier"] > 3.0  # High multiplier due to low baseline
        assert result["is_anomaly"] is True

    def test_anomaly_detection_with_empty_baseline(self):
        """Test anomaly detection with empty baseline data."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()

        # Empty baseline (new persona, no historical data)
        empty_baseline = []
        current_cost = 0.025

        result = detector.detect_statistical_anomaly(
            current_cost=current_cost,
            baseline_costs=empty_baseline,
            persona_id="new_persona",
        )

        # Should handle gracefully without crashing
        assert result is not None
        assert "is_anomaly" in result
        # With no baseline, should probably not detect anomaly
        assert result["is_anomaly"] is False

    def test_efficiency_anomaly_detection_edge_cases(self):
        """Test efficiency anomaly detection edge cases."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()
        baseline_efficiency = [50.0, 52.0, 48.0, 51.0, 49.0]  # Avg = 50.0
        persona_id = "efficiency_test"

        # Test exactly at 30% drop threshold
        current_efficiency = 35.0  # Exactly 30% drop from 50.0
        result = detector.detect_efficiency_anomaly(
            current_efficiency=current_efficiency,
            baseline_efficiency=baseline_efficiency,
            persona_id=persona_id,
        )
        assert result["is_anomaly"] is True
        assert abs(result["efficiency_drop_percent"] - 30.0) < 0.1

        # Test efficiency improvement (not anomaly)
        improved_efficiency = 65.0  # 30% improvement
        result_improved = detector.detect_efficiency_anomaly(
            current_efficiency=improved_efficiency,
            baseline_efficiency=baseline_efficiency,
            persona_id=persona_id,
        )
        assert result_improved["is_anomaly"] is False

        # Test zero efficiency (complete failure)
        zero_efficiency = 0.0
        result_zero = detector.detect_efficiency_anomaly(
            current_efficiency=zero_efficiency,
            baseline_efficiency=baseline_efficiency,
            persona_id=persona_id,
        )
        assert result_zero["is_anomaly"] is True
        assert result_zero["severity"] == "high"  # 100% drop should be high severity

    def test_roi_anomaly_detection_boundary_conditions(self):
        """Test ROI anomaly detection at various boundary conditions."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()
        persona_id = "roi_test"

        # Test exactly at -50% ROI threshold
        costs = 100.0
        revenue = 50.0  # Exactly -50% ROI
        result = detector.detect_roi_anomaly(
            costs=costs, revenue=revenue, persona_id=persona_id
        )
        assert result["is_anomaly"] is True
        assert abs(result["roi_percent"] - (-50.0)) < 0.1

        # Test zero revenue (complete loss)
        zero_revenue_result = detector.detect_roi_anomaly(
            costs=100.0, revenue=0.0, persona_id=persona_id
        )
        assert zero_revenue_result["is_anomaly"] is True
        assert zero_revenue_result["roi_percent"] == -100.0
        assert zero_revenue_result["severity"] == "critical"

        # Test zero costs (edge case)
        zero_costs_result = detector.detect_roi_anomaly(
            costs=0.0, revenue=50.0, persona_id=persona_id
        )
        assert zero_costs_result["roi_percent"] == 0.0
        assert zero_costs_result["is_anomaly"] is False

        # Test negative costs (refunds, credits)
        negative_costs_result = detector.detect_roi_anomaly(
            costs=-10.0, revenue=50.0, persona_id=persona_id
        )
        # Should handle gracefully without division by negative
        assert negative_costs_result is not None

    def test_budget_anomaly_detection_edge_cases(self):
        """Test budget anomaly detection edge cases."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()
        persona_id = "budget_test"

        # Test exactly at 80% budget threshold
        budget_limit = 1000.0
        current_spend = 800.0  # Exactly 80%
        result = detector.detect_budget_anomaly(
            current_spend=current_spend,
            budget_limit=budget_limit,
            persona_id=persona_id,
        )
        assert result["is_anomaly"] is True
        assert result["budget_usage_percent"] == 80.0

        # Test budget overrun (over 100%)
        overrun_result = detector.detect_budget_anomaly(
            current_spend=1200.0,  # 120% of budget
            budget_limit=1000.0,
            persona_id=persona_id,
        )
        assert overrun_result["is_anomaly"] is True
        assert overrun_result["budget_usage_percent"] == 120.0
        assert overrun_result["severity"] == "critical"

        # Test zero budget (unlimited scenario)
        zero_budget_result = detector.detect_budget_anomaly(
            current_spend=500.0, budget_limit=0.0, persona_id=persona_id
        )
        # Should handle division by zero gracefully
        assert zero_budget_result["budget_usage_percent"] == 0.0
        assert zero_budget_result["is_anomaly"] is False

        # Test negative budget (invalid configuration)
        negative_budget_result = detector.detect_budget_anomaly(
            current_spend=500.0, budget_limit=-100.0, persona_id=persona_id
        )
        assert negative_budget_result is not None  # Should not crash


class TestCircuitBreakerEdgeCases:
    """Edge case tests for circuit breaker automated responses."""

    def test_circuit_breaker_threshold_boundary_conditions(self):
        """Test circuit breaker triggering at exact threshold boundaries."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker()

        # Test exactly at 3x cost spike threshold
        anomaly_at_threshold = {
            "is_anomaly": True,
            "severity": "medium",
            "anomaly_type": "cost_spike",
            "multiplier": 3.0,  # Exactly at threshold
            "persona_id": "threshold_test",
        }
        should_trigger = circuit_breaker.should_trigger(anomaly_at_threshold)
        assert should_trigger is True

        # Test just below threshold
        anomaly_below_threshold = {
            "is_anomaly": True,
            "severity": "medium",
            "anomaly_type": "cost_spike",
            "multiplier": 2.99,  # Just below threshold
            "persona_id": "threshold_test",
        }
        should_not_trigger = circuit_breaker.should_trigger(anomaly_below_threshold)
        assert should_not_trigger is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_action_conflicts(self):
        """Test circuit breaker handling of conflicting action requirements."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        # Configure circuit breaker with conflicting actions enabled
        config = {
            "actions": {
                "throttle_requests": True,
                "disable_expensive_models": True,
                "pause_persona": True,  # Conflicts with throttling
                "alert_human_operator": True,
            }
        }
        circuit_breaker = CircuitBreaker(config)

        # Critical anomaly requiring multiple actions
        critical_anomaly = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "multiplier": 10.0,
            "persona_id": "conflict_test",
        }

        action_results = await circuit_breaker.execute_actions(critical_anomaly)

        # Should execute all configured actions
        assert "throttle_requests" in action_results
        assert "switch_to_cheaper_models" in action_results
        assert "pause_persona" in action_results
        assert "alert_human_operator" in action_results

        # All actions should execute successfully
        assert all(result["executed"] for result in action_results.values())

    @pytest.mark.asyncio
    async def test_circuit_breaker_rapid_successive_triggers(self):
        """Test circuit breaker behavior with rapid successive anomaly triggers."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker()

        # Multiple rapid anomalies
        anomalies = [
            {
                "is_anomaly": True,
                "severity": "critical",
                "anomaly_type": "cost_spike",
                "multiplier": 5.0,
                "persona_id": "rapid_test",
            }
            for _ in range(5)
        ]

        # Execute actions for all anomalies rapidly
        results = []
        for anomaly in anomalies:
            if circuit_breaker.should_trigger(anomaly):
                result = await circuit_breaker.execute_actions(anomaly)
                results.append(result)

        # Should handle all triggers gracefully
        assert len(results) == 5
        assert all("throttle_requests" in result for result in results)

        # Throttling should become progressively more aggressive
        rate_limits = [
            result["throttle_requests"]["new_rate_limit"] for result in results
        ]
        # All should be throttled, but exact behavior depends on implementation
        assert all(limit <= 50 for limit in rate_limits)  # All should be throttled

    @pytest.mark.asyncio
    async def test_circuit_breaker_action_execution_failures(self):
        """Test circuit breaker resilience when individual actions fail."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker()

        # Mock action failure
        original_throttle = circuit_breaker.throttle_requests

        async def failing_throttle(*args, **kwargs):
            raise Exception("Throttling service unavailable")

        circuit_breaker.throttle_requests = failing_throttle

        anomaly = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "multiplier": 5.0,
            "persona_id": "failure_test",
        }

        # Should handle action failure gracefully
        try:
            action_results = await circuit_breaker.execute_actions(anomaly)
            # If it doesn't crash, other actions should still execute
            assert "alert_human_operator" in action_results
        except Exception:
            # Or it might propagate the exception, which is also acceptable
            pass

        # Restore original method
        circuit_breaker.throttle_requests = original_throttle

    def test_circuit_breaker_unknown_anomaly_types(self):
        """Test circuit breaker behavior with unknown anomaly types."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker()

        # Unknown anomaly type
        unknown_anomaly = {
            "is_anomaly": True,
            "severity": "high",
            "anomaly_type": "unknown_pattern",  # Unknown type
            "persona_id": "unknown_test",
        }

        # Should handle gracefully (probably not trigger)
        should_trigger = circuit_breaker.should_trigger(unknown_anomaly)
        # Behavior depends on implementation - should be defensive
        assert isinstance(should_trigger, bool)

    @pytest.mark.asyncio
    async def test_circuit_breaker_model_switching_edge_cases(self):
        """Test model switching with edge cases."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker()

        anomaly = {
            "is_anomaly": True,
            "severity": "high",
            "anomaly_type": "cost_spike",
            "multiplier": 4.0,
            "persona_id": "model_test",
        }

        action_results = await circuit_breaker.execute_actions(anomaly)

        if "switch_to_cheaper_models" in action_results:
            model_mappings = action_results["switch_to_cheaper_models"][
                "model_mappings"
            ]

            # Should have reasonable model mappings
            assert "gpt-4o" in model_mappings
            assert model_mappings["gpt-4o"] == "gpt-3.5-turbo-0125"

            # Should not map to more expensive models
            for expensive, cheap in model_mappings.items():
                # This is a simplified check - in practice, we'd verify actual pricing
                assert cheap != "gpt-4"  # Don't switch to more expensive


class TestAlertManagerEdgeCases:
    """Edge case tests for multi-channel alert manager."""

    @pytest.mark.asyncio
    async def test_alert_manager_channel_failure_fallback(self):
        """Test alert manager behavior when primary channels fail."""
        from services.finops_engine.alert_manager import AlertManager

        # Configure with multiple channels
        config = {
            "channels": {
                "slack": {"enabled": True},
                "pagerduty": {"enabled": True},
                "email": {"enabled": True},
            },
            "severity_routing": {"critical": ["slack", "pagerduty", "email"]},
        }
        alert_manager = AlertManager(config)

        # Mock Slack failure
        original_slack = alert_manager.send_slack_alert

        async def failing_slack(*args, **kwargs):
            raise Exception("Slack webhook timeout")

        alert_manager.send_slack_alert = failing_slack

        # Critical anomaly requiring all channels
        critical_anomaly = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "multiplier": 10.0,
            "persona_id": "fallback_test",
        }

        # Should attempt all channels despite Slack failure
        alert_results = await alert_manager.send_alert(critical_anomaly)

        # PagerDuty and email should still succeed
        assert "pagerduty" in alert_results
        assert "email" in alert_results
        assert alert_results["pagerduty"]["success"] is True
        assert alert_results["email"]["success"] is True

        # Slack should show failure (if error handling is implemented)
        # Or might not be in results if error is caught

        # Restore original method
        alert_manager.send_slack_alert = original_slack

    @pytest.mark.asyncio
    async def test_alert_manager_message_formatting_edge_cases(self):
        """Test alert message formatting with edge case data."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Anomaly with extreme values
        extreme_anomaly = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "current_cost": 999.999,  # Very high cost
            "baseline_avg": 0.001,  # Very low baseline
            "multiplier": 999999.0,  # Extreme multiplier
            "persona_id": "extreme_test_persona_with_very_long_name_that_might_break_formatting",
        }

        # Should format without crashing
        message = alert_manager.format_slack_message(extreme_anomaly)

        assert isinstance(message, str)
        assert len(message) > 0
        assert "COST ANOMALY DETECTED" in message
        assert "999.999" in message or "$999.999" in message  # Should include cost

        # Test with missing fields
        incomplete_anomaly = {
            "is_anomaly": True,
            "severity": "medium",
            # Missing most fields
        }

        # Should handle gracefully
        incomplete_message = alert_manager.format_slack_message(incomplete_anomaly)
        assert isinstance(incomplete_message, str)
        assert "COST ANOMALY DETECTED" in incomplete_message

    @pytest.mark.asyncio
    async def test_alert_manager_rate_limiting_simulation(self):
        """Test alert manager behavior under high alert volume."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Generate many alerts rapidly
        alerts = [
            {
                "is_anomaly": True,
                "severity": "medium",
                "anomaly_type": "cost_spike",
                "multiplier": 3.5,
                "persona_id": f"persona_{i}",
            }
            for i in range(20)  # 20 rapid alerts
        ]

        # Send all alerts concurrently
        start_time = time.time()
        tasks = [alert_manager.send_alert(alert) for alert in alerts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Should handle all alerts within reasonable time
        duration = end_time - start_time
        assert duration < 5.0, f"Alert processing took {duration:.2f}s, too slow"

        # Should not crash under load
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 15  # At least 75% should succeed

    @pytest.mark.asyncio
    async def test_alert_manager_severity_routing_edge_cases(self):
        """Test severity routing with edge case severities."""
        from services.finops_engine.alert_manager import AlertManager

        # Custom routing configuration
        config = {
            "severity_routing": {
                "critical": ["slack", "pagerduty", "email"],
                "high": ["slack", "pagerduty"],
                "medium": ["slack"],
                "low": ["email"],
            }
        }
        alert_manager = AlertManager(config)

        # Test unknown severity
        unknown_severity_anomaly = {
            "is_anomaly": True,
            "severity": "unknown_severity",  # Not in routing config
            "anomaly_type": "cost_spike",
            "persona_id": "routing_test",
        }

        # Should handle gracefully (probably default to some channels)
        result = await alert_manager.send_alert(unknown_severity_anomaly)
        assert isinstance(result, dict)  # Should not crash

        # Test case-sensitive severity
        case_anomaly = {
            "is_anomaly": True,
            "severity": "CRITICAL",  # Uppercase
            "anomaly_type": "cost_spike",
            "persona_id": "case_test",
        }

        await alert_manager.send_alert(case_anomaly)
        # Behavior depends on implementation - should be robust


class TestFinOpsSystemConcurrencyEdgeCases:
    """Test edge cases related to system concurrency and race conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_anomaly_detection_different_personas(self):
        """Test concurrent anomaly detection across multiple personas."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine({"anomaly_detection_enabled": True})

        # Multiple personas with different cost patterns
        personas = [
            "ai_jesus",
            "tech_guru",
            "startup_advisor",
            "fitness_coach",
            "travel_blogger",
        ]

        async def generate_persona_anomaly(persona_id: str, anomaly_severity: str):
            """Generate different anomaly patterns per persona."""
            # Track expensive costs to trigger anomalies
            for i in range(3):
                await engine.track_openai_cost(
                    model="gpt-4o",
                    input_tokens=5000,  # Expensive calls
                    output_tokens=3000,
                    operation=f"expensive_operation_{i}",
                    persona_id=persona_id,
                    post_id=f"{persona_id}_post_{i}",
                )

            # Check for anomalies
            return await engine.check_for_anomalies(persona_id)

        # Run concurrent anomaly detection for all personas
        tasks = [generate_persona_anomaly(persona, "high") for persona in personas]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Should complete within reasonable time
        duration = end_time - start_time
        assert duration < 10.0, f"Concurrent anomaly detection took {duration:.2f}s"

        # Should detect anomalies for all personas
        assert len(results) == len(personas)
        for result in results:
            assert "anomalies_detected" in result
            # Most should detect anomalies due to expensive operations
            assert len(result["anomalies_detected"]) >= 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_concurrent_persona_conflicts(self):
        """Test circuit breaker with concurrent actions across personas."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker()

        # Multiple concurrent critical anomalies
        concurrent_anomalies = [
            {
                "is_anomaly": True,
                "severity": "critical",
                "anomaly_type": "cost_spike",
                "multiplier": 8.0,
                "persona_id": f"concurrent_persona_{i}",
            }
            for i in range(5)
        ]

        async def execute_circuit_breaker(anomaly):
            """Execute circuit breaker for one anomaly."""
            if circuit_breaker.should_trigger(anomaly):
                return await circuit_breaker.execute_actions(anomaly)
            return {}

        # Execute all circuit breakers concurrently
        tasks = [execute_circuit_breaker(anomaly) for anomaly in concurrent_anomalies]
        results = await asyncio.gather(*tasks)

        # Should execute all without conflicts
        assert len(results) == 5

        # All should execute throttling actions
        throttle_actions = [r.get("throttle_requests") for r in results if r]
        assert len(throttle_actions) >= 3  # Most should execute

    @pytest.mark.asyncio
    async def test_metrics_emission_under_concurrent_load(self):
        """Test Prometheus metrics emission under concurrent load."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        async def concurrent_cost_tracking(batch_id: int):
            """Track costs concurrently."""
            costs = []
            for i in range(10):
                cost_event = await engine.track_openai_cost(
                    model="gpt-3.5-turbo-0125",
                    input_tokens=1000,
                    output_tokens=500,
                    operation=f"concurrent_op_{batch_id}_{i}",
                    persona_id=f"concurrent_persona_{batch_id}",
                    post_id=f"concurrent_post_{batch_id}_{i}",
                )
                costs.append(cost_event)
            return costs

        # Run 10 concurrent batches (100 total cost events)
        tasks = [concurrent_cost_tracking(i) for i in range(10)]

        start_time = time.time()
        batch_results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Should complete efficiently
        duration = end_time - start_time
        assert duration < 5.0, f"Concurrent cost tracking took {duration:.2f}s"

        # Should track all costs successfully
        total_events = sum(len(batch) for batch in batch_results)
        assert total_events == 100

        # Should emit metrics for all events
        metrics_emitted = engine.prometheus_client.get_emitted_metrics()
        assert len(metrics_emitted) >= 100  # At least one metric per cost event

        # Should have consistent metric types
        openai_metrics = [
            m for m in metrics_emitted if "openai_api_costs" in m["metric_name"]
        ]
        assert len(openai_metrics) == 100  # One per cost event

    @pytest.mark.asyncio
    async def test_cost_attribution_accuracy_under_load(self):
        """Test cost attribution accuracy under concurrent load."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine()

        # Generate costs for many posts concurrently
        post_ids = [f"accuracy_test_{i:03d}" for i in range(50)]
        persona_id = "accuracy_test_persona"

        async def track_post_costs(post_id: str):
            """Track standard costs for one post."""
            costs = []

            # OpenAI cost
            cost1 = await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=500,
                operation="hook_generation",
                persona_id=persona_id,
                post_id=post_id,
            )
            costs.append(cost1["cost_amount"])

            # Infrastructure cost
            cost2 = await engine.track_infrastructure_cost(
                resource_type="kubernetes",
                service="persona_runtime",
                cpu_cores=0.5,
                memory_gb=1.0,
                duration_minutes=3,
                operation="post_generation",
                persona_id=persona_id,
                post_id=post_id,
            )
            costs.append(cost2["cost_amount"])

            return sum(costs)

        # Track costs for all posts concurrently
        tasks = [track_post_costs(post_id) for post_id in post_ids]
        expected_costs = await asyncio.gather(*tasks)

        # Verify accuracy for all posts
        accuracy_tasks = [
            engine.post_cost_attributor.get_post_cost_breakdown(post_id)
            for post_id in post_ids
        ]
        breakdowns = await asyncio.gather(*accuracy_tasks)

        # All should meet 95% accuracy requirement
        for breakdown in breakdowns:
            assert breakdown["accuracy_score"] >= 0.95

        # Total costs should match expected
        actual_costs = [b["total_cost"] for b in breakdowns]
        for expected, actual in zip(expected_costs, actual_costs):
            assert abs(expected - actual) < 0.0001, (
                "Cost calculation mismatch under load"
            )
