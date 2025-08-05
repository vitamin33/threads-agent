"""
Comprehensive Cost Attribution Accuracy Tests for FinOps Engine (CRA-240)

Tests the 95% cost attribution accuracy requirement covering:
1. PostCostAttributor - Precise cost-post associations
2. Accuracy calculation methodology and validation
3. Audit trail completeness and integrity
4. Cost breakdown precision across different scenarios
5. Metadata quality impact on accuracy scores
6. Cross-service cost attribution validation

Key Accuracy Requirements:
- 95% minimum accuracy for all cost attributions
- Complete audit trail for all cost events
- Sub-second query performance for cost breakdowns
- Precise cost tracking across OpenAI, Infrastructure, Vector DB
- Metadata-driven accuracy confidence scoring
"""

import pytest
import asyncio
import time
import statistics
import random
import uuid


class TestCostAttributionAccuracyBaseline:
    """Baseline tests for cost attribution accuracy calculations."""

    @pytest.mark.asyncio
    async def test_accuracy_calculation_with_high_confidence_metadata(self):
        """Test accuracy calculation with high-confidence metadata."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()
        post_id = "high_confidence_test"

        # Track cost with comprehensive metadata (high confidence)
        high_confidence_metadata = {
            "correlation_id": str(uuid.uuid4()),
            "request_id": f"req_{uuid.uuid4()}",
            "model": "gpt-4o",
            "operation": "hook_generation",
            "persona_id": "ai_jesus",
            "input_tokens": 1000,
            "output_tokens": 500,
            "api_response_id": "chatcmpl-8xYzABC123",
            "timestamp_start": "2024-01-15T10:30:00.123Z",
            "timestamp_end": "2024-01-15T10:30:02.456Z",
            "cost_calculation_method": "token_based_precise",
            "billing_region": "us-east-1",
        }

        await attributor.track_cost_for_post(
            post_id=post_id,
            cost_type="openai_api",
            cost_amount=0.0125,
            metadata=high_confidence_metadata,
        )

        # Get cost breakdown and verify accuracy
        breakdown = await attributor.get_post_cost_breakdown(post_id)

        # Should achieve high accuracy with comprehensive metadata
        assert breakdown["accuracy_score"] >= 0.98, (
            f"Expected >98% accuracy, got {breakdown['accuracy_score']:.3f}"
        )
        assert breakdown["accuracy_score"] <= 1.0, (
            "Accuracy score should not exceed 100%"
        )

        # Verify accuracy details
        accuracy_details = breakdown["accuracy_details"]
        assert accuracy_details["total_events"] == 1
        assert accuracy_details["high_confidence_events"] >= 1

        # Verify confidence factors
        confidence_factors = accuracy_details["confidence_factors"][0]
        assert "correlation_id" in confidence_factors["factors"]
        assert "request_id" in confidence_factors["factors"]
        assert confidence_factors["confidence"] >= 0.98

    @pytest.mark.asyncio
    async def test_accuracy_calculation_with_minimal_metadata(self):
        """Test accuracy calculation with minimal metadata (still meets 95% requirement)."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()
        post_id = "minimal_metadata_test"

        # Track cost with minimal metadata
        minimal_metadata = {
            "operation": "body_generation",
            "model": "gpt-3.5-turbo-0125",
            # Missing correlation_id, request_id, etc.
        }

        await attributor.track_cost_for_post(
            post_id=post_id,
            cost_type="openai_api",
            cost_amount=0.0025,
            metadata=minimal_metadata,
        )

        # Get cost breakdown and verify accuracy
        breakdown = await attributor.get_post_cost_breakdown(post_id)

        # Should still meet 95% accuracy requirement
        assert breakdown["accuracy_score"] >= 0.95, (
            f"Expected ≥95% accuracy, got {breakdown['accuracy_score']:.3f}"
        )
        assert breakdown["accuracy_score"] < 0.98, (
            "Minimal metadata should have lower accuracy than comprehensive"
        )

        # Verify accuracy details reflect lower confidence
        accuracy_details = breakdown["accuracy_details"]
        confidence_factors = accuracy_details["confidence_factors"][0]
        assert len(confidence_factors["factors"]) < 4  # Fewer confidence factors

    @pytest.mark.asyncio
    async def test_accuracy_calculation_with_multiple_cost_events(self):
        """Test accuracy calculation across multiple cost events for one post."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()
        post_id = "multi_event_accuracy_test"

        # Track multiple cost events with varying metadata quality
        cost_events = [
            {
                "cost_type": "openai_api",
                "cost_amount": 0.0075,
                "metadata": {
                    "correlation_id": str(uuid.uuid4()),
                    "request_id": f"req_hook_{uuid.uuid4()}",
                    "model": "gpt-4o",
                    "operation": "hook_generation",
                    "input_tokens": 800,
                    "output_tokens": 400,
                },
            },
            {
                "cost_type": "openai_api",
                "cost_amount": 0.0025,
                "metadata": {
                    "correlation_id": str(uuid.uuid4()),
                    "request_id": f"req_body_{uuid.uuid4()}",
                    "model": "gpt-3.5-turbo-0125",
                    "operation": "body_generation",
                    "input_tokens": 1200,
                    "output_tokens": 800,
                },
            },
            {
                "cost_type": "kubernetes",
                "cost_amount": 0.0036,
                "metadata": {
                    "service": "persona_runtime",
                    "pod_name": f"persona-runtime-{uuid.uuid4().hex[:8]}",
                    "cpu_cores": 0.5,
                    "memory_gb": 1.0,
                    "duration_minutes": 3,
                    "k8s_namespace": "threads-agent",
                },
            },
            {
                "cost_type": "vector_db",
                "cost_amount": 0.0001,
                "metadata": {
                    "operation": "similarity_search",
                    "query_count": 500,
                    "collection": "posts_ai_jesus",
                    "query_vector_dimensions": 1536,
                },
            },
        ]

        # Track all cost events
        for event in cost_events:
            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type=event["cost_type"],
                cost_amount=event["cost_amount"],
                metadata=event["metadata"],
            )

        # Get cost breakdown and verify accuracy
        breakdown = await attributor.get_post_cost_breakdown(post_id)

        # Should maintain high accuracy across multiple events
        assert breakdown["accuracy_score"] >= 0.95, (
            f"Multi-event accuracy {breakdown['accuracy_score']:.3f} below 95%"
        )
        assert breakdown["total_cost"] == sum(e["cost_amount"] for e in cost_events)

        # Verify all events are in audit trail
        assert len(breakdown["audit_trail"]) == len(cost_events)

        # Verify accuracy details
        accuracy_details = breakdown["accuracy_details"]
        assert accuracy_details["total_events"] == len(cost_events)
        assert len(accuracy_details["confidence_factors"]) == len(cost_events)

        # Each event should have reasonable confidence
        for cf in accuracy_details["confidence_factors"]:
            assert cf["confidence"] >= 0.95

    @pytest.mark.asyncio
    async def test_accuracy_degradation_with_missing_correlation_data(self):
        """Test accuracy degradation when correlation data is missing."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Test cases with progressively less correlation data
        test_cases = [
            {
                "name": "full_correlation",
                "metadata": {
                    "correlation_id": str(uuid.uuid4()),
                    "request_id": f"req_{uuid.uuid4()}",
                    "trace_id": f"trace_{uuid.uuid4()}",
                    "span_id": f"span_{uuid.uuid4()}",
                    "model": "gpt-4o",
                    "operation": "hook_generation",
                },
                "expected_min_accuracy": 0.98,
            },
            {
                "name": "partial_correlation",
                "metadata": {
                    "correlation_id": str(uuid.uuid4()),
                    "model": "gpt-4o",
                    "operation": "hook_generation",
                },
                "expected_min_accuracy": 0.96,
            },
            {
                "name": "minimal_correlation",
                "metadata": {"model": "gpt-4o", "operation": "hook_generation"},
                "expected_min_accuracy": 0.95,
            },
            {"name": "no_correlation", "metadata": {}, "expected_min_accuracy": 0.95},
        ]

        results = []

        for i, case in enumerate(test_cases):
            post_id = f"correlation_test_{case['name']}_{i}"

            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type="openai_api",
                cost_amount=0.0125,
                metadata=case["metadata"],
            )

            breakdown = await attributor.get_post_cost_breakdown(post_id)
            accuracy = breakdown["accuracy_score"]

            # Verify minimum accuracy requirement
            assert accuracy >= case["expected_min_accuracy"], (
                f"{case['name']}: accuracy {accuracy:.3f} below expected {case['expected_min_accuracy']:.3f}"
            )

            results.append(
                {
                    "name": case["name"],
                    "accuracy": accuracy,
                    "expected": case["expected_min_accuracy"],
                }
            )

        # Verify accuracy degrades appropriately with less correlation data
        accuracies = [r["accuracy"] for r in results]
        assert accuracies[0] >= accuracies[1] >= accuracies[2] >= accuracies[3], (
            "Accuracy should degrade with less correlation data"
        )

        print("Accuracy degradation test:")
        for result in results:
            print(
                f"  {result['name']}: {result['accuracy']:.3f} (min: {result['expected']:.3f})"
            )


class TestCostAttributionPrecisionValidation:
    """Tests for cost calculation precision and validation."""

    @pytest.mark.asyncio
    async def test_cost_calculation_precision_openai_tokens(self):
        """Test precise cost calculation for OpenAI token usage."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Test precise token-based cost calculations
        test_cases = [
            {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500,
                "expected_cost": 0.0125,  # (1000/1000 * 0.005) + (500/1000 * 0.015)
                "tolerance": 0.0001,
            },
            {
                "model": "gpt-3.5-turbo-0125",
                "input_tokens": 2000,
                "output_tokens": 1000,
                "expected_cost": 0.0025,  # (2000/1000 * 0.0005) + (1000/1000 * 0.0015)
                "tolerance": 0.0001,
            },
            {
                "model": "gpt-4o",
                "input_tokens": 1500,
                "output_tokens": 750,
                "expected_cost": 0.01875,  # (1500/1000 * 0.005) + (750/1000 * 0.015)
                "tolerance": 0.0001,
            },
        ]

        for i, case in enumerate(test_cases):
            post_id = f"precision_test_{case['model']}_{i}"

            # Calculate expected cost using the same logic as the system
            metadata = {
                "model": case["model"],
                "input_tokens": case["input_tokens"],
                "output_tokens": case["output_tokens"],
                "operation": "precision_test",
                "cost_calculation_method": "token_based_precise",
            }

            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type="openai_api",
                cost_amount=case["expected_cost"],
                metadata=metadata,
            )

            breakdown = await attributor.get_post_cost_breakdown(post_id)

            # Verify precise cost calculation
            actual_cost = breakdown["total_cost"]
            cost_diff = abs(actual_cost - case["expected_cost"])

            assert cost_diff <= case["tolerance"], (
                f"Cost precision error for {case['model']}: expected {case['expected_cost']}, got {actual_cost}"
            )

            # Verify accuracy remains high with precise calculations
            assert breakdown["accuracy_score"] >= 0.95

    @pytest.mark.asyncio
    async def test_cost_attribution_infrastructure_precision(self):
        """Test precise cost attribution for infrastructure resources."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Test precise infrastructure cost calculations
        infrastructure_cases = [
            {
                "resource_type": "kubernetes",
                "cpu_cores": 0.5,
                "memory_gb": 1.0,
                "duration_minutes": 60,  # 1 hour
                "expected_cost": 0.072,  # (0.5 * 0.048) + (1.0 * 0.012) = 0.024 + 0.012 = 0.036 per hour
                "tolerance": 0.001,
            },
            {
                "resource_type": "kubernetes",
                "cpu_cores": 2.0,
                "memory_gb": 4.0,
                "duration_minutes": 30,  # 0.5 hours
                "expected_cost": 0.072,  # ((2.0 * 0.048) + (4.0 * 0.012)) * 0.5 = (0.096 + 0.048) * 0.5 = 0.072
                "tolerance": 0.001,
            },
        ]

        for i, case in enumerate(infrastructure_cases):
            post_id = f"infra_precision_test_{i}"

            metadata = {
                "resource_type": case["resource_type"],
                "cpu_cores": case["cpu_cores"],
                "memory_gb": case["memory_gb"],
                "duration_minutes": case["duration_minutes"],
                "service": "persona_runtime",
                "cost_calculation_method": "resource_usage_precise",
            }

            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type="kubernetes",
                cost_amount=case["expected_cost"],
                metadata=metadata,
            )

            breakdown = await attributor.get_post_cost_breakdown(post_id)

            # Verify precise infrastructure cost
            actual_cost = breakdown["total_cost"]
            cost_diff = abs(actual_cost - case["expected_cost"])

            assert cost_diff <= case["tolerance"], (
                f"Infrastructure cost precision error: expected {case['expected_cost']}, got {actual_cost}"
            )

            assert breakdown["accuracy_score"] >= 0.95

    @pytest.mark.asyncio
    async def test_cost_attribution_vector_db_precision(self):
        """Test precise cost attribution for vector database operations."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Test vector DB cost precision
        vector_db_cases = [
            {
                "operation": "similarity_search",
                "query_count": 1000,
                "expected_cost": 0.0002,  # 1000/1000 * 0.0002 = 0.0002
                "tolerance": 0.00001,
            },
            {
                "operation": "batch_insert",
                "query_count": 5000,
                "expected_cost": 0.001,  # 5000/1000 * 0.0002 = 0.001
                "tolerance": 0.00001,
            },
            {
                "operation": "similarity_search",
                "query_count": 250,
                "expected_cost": 0.00005,  # 250/1000 * 0.0002 = 0.00005
                "tolerance": 0.000001,
            },
        ]

        for i, case in enumerate(vector_db_cases):
            post_id = f"vector_precision_test_{i}"

            metadata = {
                "operation": case["operation"],
                "query_count": case["query_count"],
                "collection": "posts_ai_jesus",
                "vector_dimensions": 1536,
                "cost_calculation_method": "query_count_precise",
            }

            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type="vector_db",
                cost_amount=case["expected_cost"],
                metadata=metadata,
            )

            breakdown = await attributor.get_post_cost_breakdown(post_id)

            # Verify precise vector DB cost
            actual_cost = breakdown["total_cost"]
            cost_diff = abs(actual_cost - case["expected_cost"])

            assert cost_diff <= case["tolerance"], (
                f"Vector DB cost precision error: expected {case['expected_cost']}, got {actual_cost}"
            )

            assert breakdown["accuracy_score"] >= 0.95


class TestCostAttributionAuditTrailIntegrity:
    """Tests for audit trail completeness and integrity."""

    @pytest.mark.asyncio
    async def test_audit_trail_chronological_ordering(self):
        """Test that audit trail maintains chronological ordering."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()
        post_id = "chronological_test"

        # Track costs with deliberate timing
        cost_events = [
            {"type": "trend_research", "amount": 0.005, "delay": 0.0},
            {"type": "hook_generation", "amount": 0.008, "delay": 0.1},
            {"type": "body_generation", "amount": 0.003, "delay": 0.2},
            {"type": "processing", "amount": 0.004, "delay": 0.3},
            {"type": "validation", "amount": 0.001, "delay": 0.4},
        ]

        # Track events with small delays to ensure chronological order
        for event in cost_events:
            await asyncio.sleep(event["delay"])

            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type="openai_api",
                cost_amount=event["amount"],
                metadata={
                    "operation": event["type"],
                    "stage": event["type"],
                    "model": "gpt-4o",
                },
            )

        # Verify audit trail order
        breakdown = await attributor.get_post_cost_breakdown(post_id)
        audit_trail = breakdown["audit_trail"]

        # Should have all events
        assert len(audit_trail) == len(cost_events)

        # Verify chronological ordering
        timestamps = [entry["timestamp"] for entry in audit_trail]
        sorted_timestamps = sorted(timestamps)
        assert timestamps == sorted_timestamps, (
            "Audit trail should be chronologically ordered"
        )

        # Verify cost amounts match
        audit_amounts = [entry["cost_amount"] for entry in audit_trail]
        expected_amounts = [event["amount"] for event in cost_events]
        assert audit_amounts == expected_amounts, (
            "Audit trail amounts should match insertion order"
        )

        # Verify operations are in correct order
        audit_operations = [entry["metadata"]["operation"] for entry in audit_trail]
        expected_operations = [event["type"] for event in cost_events]
        assert audit_operations == expected_operations, (
            "Operations should be in chronological order"
        )

    @pytest.mark.asyncio
    async def test_audit_trail_metadata_preservation(self):
        """Test that audit trail preserves all metadata accurately."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()
        post_id = "metadata_preservation_test"

        # Complex metadata to test preservation
        complex_metadata = {
            "correlation_id": str(uuid.uuid4()),
            "request_id": f"req_{uuid.uuid4()}",
            "model": "gpt-4o",
            "operation": "complex_generation",
            "input_tokens": 1500,
            "output_tokens": 800,
            "api_response": {
                "id": "chatcmpl-8xYzABC123",
                "created": 1705396200,
                "model": "gpt-4o-2024-01-15",
                "usage": {
                    "prompt_tokens": 1500,
                    "completion_tokens": 800,
                    "total_tokens": 2300,
                },
            },
            "processing_details": {
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
            },
            "cost_breakdown": {
                "input_cost": 0.0075,
                "output_cost": 0.012,
                "total_cost": 0.0195,
            },
            "performance_metrics": {
                "latency_ms": 2340,
                "tokens_per_second": 341.88,
                "cache_hit": False,
            },
        }

        await attributor.track_cost_for_post(
            post_id=post_id,
            cost_type="openai_api",
            cost_amount=0.0195,
            metadata=complex_metadata,
        )

        # Verify metadata preservation in audit trail
        breakdown = await attributor.get_post_cost_breakdown(post_id)
        audit_entry = breakdown["audit_trail"][0]
        preserved_metadata = audit_entry["metadata"]

        # Verify all top-level metadata is preserved
        for key, value in complex_metadata.items():
            assert key in preserved_metadata, f"Missing metadata key: {key}"
            assert preserved_metadata[key] == value, (
                f"Metadata value mismatch for {key}"
            )

        # Verify nested metadata structures are preserved
        assert preserved_metadata["api_response"]["usage"]["total_tokens"] == 2300
        assert preserved_metadata["processing_details"]["temperature"] == 0.7
        assert preserved_metadata["cost_breakdown"]["total_cost"] == 0.0195
        assert preserved_metadata["performance_metrics"]["latency_ms"] == 2340

    @pytest.mark.asyncio
    async def test_audit_trail_completeness_under_concurrent_operations(self):
        """Test audit trail completeness when multiple operations track costs concurrently."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()
        post_id = "concurrent_audit_test"

        # Generate concurrent cost tracking operations
        concurrent_operations = [
            {
                "id": f"op_{i}",
                "amount": random.uniform(0.001, 0.01),
                "type": f"operation_{i}",
            }
            for i in range(20)
        ]

        async def track_concurrent_cost(operation):
            """Track a single cost concurrently."""
            metadata = {
                "operation_id": operation["id"],
                "operation_type": operation["type"],
                "concurrent_test": True,
                "model": "gpt-3.5-turbo-0125",
                "correlation_id": str(uuid.uuid4()),
            }

            return await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type="openai_api",
                cost_amount=operation["amount"],
                metadata=metadata,
            )

        # Execute all operations concurrently
        tasks = [track_concurrent_cost(op) for op in concurrent_operations]
        tracking_results = await asyncio.gather(*tasks)

        # Verify audit trail completeness
        breakdown = await attributor.get_post_cost_breakdown(post_id)
        audit_trail = breakdown["audit_trail"]

        # Should have all operations in audit trail
        assert len(audit_trail) == len(concurrent_operations)

        # Verify all operation IDs are present
        audit_operation_ids = {
            entry["metadata"]["operation_id"] for entry in audit_trail
        }
        expected_operation_ids = {op["id"] for op in concurrent_operations}
        assert audit_operation_ids == expected_operation_ids, (
            "Missing operations in audit trail"
        )

        # Verify total cost matches sum of individual costs
        audit_total = sum(entry["cost_amount"] for entry in audit_trail)
        expected_total = sum(op["amount"] for op in concurrent_operations)
        assert abs(audit_total - expected_total) < 0.0001, (
            "Audit trail total cost mismatch"
        )

        # Verify all tracking results were successful
        assert all(result is not None for result in tracking_results)


class TestCostAttributionCrossServiceValidation:
    """Tests for cost attribution accuracy across multiple services."""

    @pytest.mark.asyncio
    async def test_cross_service_cost_attribution_consistency(self):
        """Test cost attribution consistency across OpenAI, K8s, and Vector DB."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()
        post_id = "cross_service_test"
        correlation_id = str(uuid.uuid4())

        # Track costs across different services with same correlation ID
        service_costs = [
            {
                "service": "openai",
                "cost_type": "openai_api",
                "amount": 0.0125,
                "metadata": {
                    "correlation_id": correlation_id,
                    "model": "gpt-4o",
                    "operation": "hook_generation",
                    "service": "openai",
                    "request_id": f"openai_req_{uuid.uuid4()}",
                },
            },
            {
                "service": "kubernetes",
                "cost_type": "kubernetes",
                "amount": 0.0036,
                "metadata": {
                    "correlation_id": correlation_id,
                    "service": "persona_runtime",
                    "operation": "post_processing",
                    "resource_type": "pod",
                    "pod_id": f"pod_{uuid.uuid4().hex[:8]}",
                },
            },
            {
                "service": "vector_db",
                "cost_type": "vector_db",
                "amount": 0.0001,
                "metadata": {
                    "correlation_id": correlation_id,
                    "operation": "similarity_search",
                    "service": "qdrant",
                    "collection": "posts_ai_jesus",
                    "query_id": f"query_{uuid.uuid4()}",
                },
            },
        ]

        # Track all service costs
        for cost in service_costs:
            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type=cost["cost_type"],
                cost_amount=cost["amount"],
                metadata=cost["metadata"],
            )

        # Verify cross-service attribution
        breakdown = await attributor.get_post_cost_breakdown(post_id)

        # Should maintain high accuracy across services
        assert breakdown["accuracy_score"] >= 0.95

        # Verify all services are represented in cost breakdown
        cost_by_type = breakdown["cost_breakdown"]
        assert "openai_api" in cost_by_type
        assert "kubernetes" in cost_by_type
        assert "vector_db" in cost_by_type

        # Verify cost amounts match
        assert abs(cost_by_type["openai_api"] - 0.0125) < 0.0001
        assert abs(cost_by_type["kubernetes"] - 0.0036) < 0.0001
        assert abs(cost_by_type["vector_db"] - 0.0001) < 0.0001

        # Verify correlation ID is preserved across all services
        for entry in breakdown["audit_trail"]:
            assert entry["metadata"]["correlation_id"] == correlation_id

    @pytest.mark.asyncio
    async def test_cross_service_cost_attribution_with_missing_service(self):
        """Test cost attribution when one service's costs are missing."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()
        post_id = "missing_service_test"

        # Track costs for only OpenAI and K8s (missing Vector DB)
        await attributor.track_cost_for_post(
            post_id=post_id,
            cost_type="openai_api",
            cost_amount=0.0125,
            metadata={
                "model": "gpt-4o",
                "operation": "generation",
                "correlation_id": str(uuid.uuid4()),
            },
        )

        await attributor.track_cost_for_post(
            post_id=post_id,
            cost_type="kubernetes",
            cost_amount=0.0036,
            metadata={
                "service": "persona_runtime",
                "operation": "processing",
                "correlation_id": str(uuid.uuid4()),
            },
        )

        # Should still maintain 95% accuracy despite missing service
        breakdown = await attributor.get_post_cost_breakdown(post_id)
        assert breakdown["accuracy_score"] >= 0.95

        # Should have costs for tracked services
        assert breakdown["total_cost"] == 0.0161  # 0.0125 + 0.0036
        assert "openai_api" in breakdown["cost_breakdown"]
        assert "kubernetes" in breakdown["cost_breakdown"]
        assert "vector_db" not in breakdown["cost_breakdown"]

    @pytest.mark.asyncio
    async def test_cost_attribution_with_service_cost_anomalies(self):
        """Test cost attribution accuracy when individual services have cost anomalies."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Test different anomaly scenarios
        anomaly_scenarios = [
            {
                "name": "high_openai_cost",
                "post_id": "anomaly_high_openai",
                "costs": [
                    {
                        "type": "openai_api",
                        "amount": 0.150,
                        "metadata": {"model": "gpt-4o", "anomaly": "high_token_usage"},
                    },
                    {
                        "type": "kubernetes",
                        "amount": 0.0036,
                        "metadata": {"service": "persona_runtime"},
                    },
                    {
                        "type": "vector_db",
                        "amount": 0.0001,
                        "metadata": {"operation": "similarity_search"},
                    },
                ],
            },
            {
                "name": "high_k8s_cost",
                "post_id": "anomaly_high_k8s",
                "costs": [
                    {
                        "type": "openai_api",
                        "amount": 0.0125,
                        "metadata": {"model": "gpt-4o"},
                    },
                    {
                        "type": "kubernetes",
                        "amount": 0.500,
                        "metadata": {
                            "service": "persona_runtime",
                            "anomaly": "long_processing",
                        },
                    },
                    {
                        "type": "vector_db",
                        "amount": 0.0001,
                        "metadata": {"operation": "similarity_search"},
                    },
                ],
            },
            {
                "name": "zero_cost_service",
                "post_id": "anomaly_zero_cost",
                "costs": [
                    {
                        "type": "openai_api",
                        "amount": 0.0125,
                        "metadata": {"model": "gpt-4o"},
                    },
                    {
                        "type": "kubernetes",
                        "amount": 0.0000,
                        "metadata": {
                            "service": "persona_runtime",
                            "note": "cached_result",
                        },
                    },
                    {
                        "type": "vector_db",
                        "amount": 0.0001,
                        "metadata": {"operation": "similarity_search"},
                    },
                ],
            },
        ]

        for scenario in anomaly_scenarios:
            post_id = scenario["post_id"]

            # Track all costs for this scenario
            for cost in scenario["costs"]:
                await attributor.track_cost_for_post(
                    post_id=post_id,
                    cost_type=cost["type"],
                    cost_amount=cost["amount"],
                    metadata=cost["metadata"],
                )

            # Verify accuracy is maintained even with anomalies
            breakdown = await attributor.get_post_cost_breakdown(post_id)
            assert breakdown["accuracy_score"] >= 0.95, (
                f"Accuracy below 95% for {scenario['name']}: {breakdown['accuracy_score']:.3f}"
            )

            # Verify total cost calculation is correct
            expected_total = sum(cost["amount"] for cost in scenario["costs"])
            assert abs(breakdown["total_cost"] - expected_total) < 0.0001

            print(
                f"✓ {scenario['name']}: accuracy {breakdown['accuracy_score']:.3f}, total ${breakdown['total_cost']:.4f}"
            )


class TestCostAttributionPerformanceAccuracy:
    """Tests for maintaining accuracy under performance constraints."""

    @pytest.mark.asyncio
    async def test_accuracy_maintained_under_high_volume(self):
        """Test that 95% accuracy is maintained under high-volume cost tracking."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Generate high volume of cost events
        volume_test_posts = 100
        events_per_post = 5

        async def track_post_costs(post_index: int):
            """Track costs for one post."""
            post_id = f"volume_accuracy_test_{post_index:03d}"
            correlation_id = str(uuid.uuid4())

            for event_index in range(events_per_post):
                metadata = {
                    "correlation_id": correlation_id,
                    "request_id": f"req_{post_index}_{event_index}",
                    "model": random.choice(["gpt-4o", "gpt-3.5-turbo-0125"]),
                    "operation": f"operation_{event_index}",
                    "event_sequence": event_index,
                }

                await attributor.track_cost_for_post(
                    post_id=post_id,
                    cost_type="openai_api",
                    cost_amount=random.uniform(0.001, 0.01),
                    metadata=metadata,
                )

            return post_id

        # Process all posts concurrently
        start_time = time.time()
        tasks = [track_post_costs(i) for i in range(volume_test_posts)]
        post_ids = await asyncio.gather(*tasks)
        end_time = time.time()

        processing_time = end_time - start_time
        total_events = volume_test_posts * events_per_post

        print(
            f"Volume test: {total_events} events in {processing_time:.2f}s ({total_events / processing_time:.1f} events/s)"
        )

        # Verify accuracy for all posts
        accuracy_tasks = [
            attributor.get_post_cost_breakdown(post_id) for post_id in post_ids
        ]
        breakdowns = await asyncio.gather(*accuracy_tasks)

        # All posts should maintain 95% accuracy
        accuracies = [b["accuracy_score"] for b in breakdowns]
        min_accuracy = min(accuracies)
        avg_accuracy = statistics.mean(accuracies)

        assert min_accuracy >= 0.95, (
            f"Minimum accuracy {min_accuracy:.3f} below 95% under high volume"
        )
        assert avg_accuracy >= 0.96, (
            f"Average accuracy {avg_accuracy:.3f} too low under high volume"
        )

        # Verify all posts have correct event counts
        for breakdown in breakdowns:
            assert len(breakdown["audit_trail"]) == events_per_post

        print(f"Accuracy under volume: min {min_accuracy:.3f}, avg {avg_accuracy:.3f}")

    @pytest.mark.asyncio
    async def test_accuracy_maintained_with_rapid_queries(self):
        """Test accuracy maintained when cost breakdowns are queried rapidly."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Setup test posts with cost data
        test_posts = 20
        for i in range(test_posts):
            post_id = f"rapid_query_test_{i:02d}"

            # Add multiple cost events per post
            for j in range(3):
                await attributor.track_cost_for_post(
                    post_id=post_id,
                    cost_type="openai_api",
                    cost_amount=random.uniform(0.005, 0.015),
                    metadata={
                        "correlation_id": str(uuid.uuid4()),
                        "model": "gpt-4o",
                        "operation": f"operation_{j}",
                    },
                )

        # Rapidly query cost breakdowns
        post_ids = [f"rapid_query_test_{i:02d}" for i in range(test_posts)]

        start_time = time.time()

        # Multiple rapid query rounds
        for round_num in range(5):
            tasks = [
                attributor.get_post_cost_breakdown(post_id) for post_id in post_ids
            ]
            round_results = await asyncio.gather(*tasks)

            # Verify accuracy for this round
            for breakdown in round_results:
                assert breakdown["accuracy_score"] >= 0.95, (
                    f"Accuracy degraded during rapid queries: {breakdown['accuracy_score']:.3f}"
                )

        end_time = time.time()
        query_time = end_time - start_time
        total_queries = test_posts * 5
        queries_per_second = total_queries / query_time

        print(
            f"Rapid queries: {total_queries} queries in {query_time:.2f}s ({queries_per_second:.1f} queries/s)"
        )

        # Verify query performance
        assert queries_per_second > 20, (
            f"Query rate {queries_per_second:.1f}/s too slow"
        )

    @pytest.mark.asyncio
    async def test_accuracy_consistency_across_time_periods(self):
        """Test accuracy consistency across different time periods."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Simulate cost tracking over different time periods
        time_periods = [
            {"name": "morning", "posts": 10, "base_cost": 0.015},
            {"name": "afternoon", "posts": 15, "base_cost": 0.018},
            {"name": "evening", "posts": 12, "base_cost": 0.012},
            {"name": "night", "posts": 8, "base_cost": 0.020},
        ]

        period_results = []

        for period in time_periods:
            period_post_ids = []

            # Track costs for this time period
            for i in range(period["posts"]):
                post_id = f"{period['name']}_post_{i:02d}"
                period_post_ids.append(post_id)

                # Vary costs around base cost for the period
                cost_variation = random.uniform(-0.003, 0.003)
                cost_amount = period["base_cost"] + cost_variation

                metadata = {
                    "time_period": period["name"],
                    "correlation_id": str(uuid.uuid4()),
                    "model": "gpt-4o",
                    "operation": "generation",
                    "base_cost": period["base_cost"],
                }

                await attributor.track_cost_for_post(
                    post_id=post_id,
                    cost_type="openai_api",
                    cost_amount=cost_amount,
                    metadata=metadata,
                )

            # Get accuracy for this period
            period_breakdowns = []
            for post_id in period_post_ids:
                breakdown = await attributor.get_post_cost_breakdown(post_id)
                period_breakdowns.append(breakdown)

            # Calculate period accuracy statistics
            period_accuracies = [b["accuracy_score"] for b in period_breakdowns]
            period_avg_accuracy = statistics.mean(period_accuracies)
            period_min_accuracy = min(period_accuracies)

            period_results.append(
                {
                    "name": period["name"],
                    "avg_accuracy": period_avg_accuracy,
                    "min_accuracy": period_min_accuracy,
                    "post_count": len(period_post_ids),
                }
            )

            # Verify accuracy for this period
            assert period_min_accuracy >= 0.95, (
                f"{period['name']} period min accuracy {period_min_accuracy:.3f} below 95%"
            )

        # Verify consistency across periods
        all_avg_accuracies = [p["avg_accuracy"] for p in period_results]
        accuracy_variance = max(all_avg_accuracies) - min(all_avg_accuracies)

        assert accuracy_variance < 0.02, (
            f"Accuracy variance {accuracy_variance:.3f} across time periods too high"
        )

        print("Accuracy consistency across time periods:")
        for result in period_results:
            print(
                f"  {result['name']}: avg {result['avg_accuracy']:.3f}, min {result['min_accuracy']:.3f}"
            )
        print(f"  Variance: {accuracy_variance:.3f}")
