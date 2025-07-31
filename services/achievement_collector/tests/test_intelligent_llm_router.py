"""Test suite for intelligent LLM router with advanced capabilities."""

import pytest
from unittest.mock import patch

# Import what we're going to build
from ai_pipeline.intelligent_llm_router import (
    IntelligentLLMRouter,
    CostOptimizer,
    PerformanceMonitor,
    QueryComplexityAnalyzer,
)


class TestIntelligentLLMRouter:
    """Test intelligent routing based on query complexity and cost."""

    @pytest.fixture
    def router(self):
        """Create a router instance with test configuration."""
        config = {
            "providers": {
                "openai": {"api_key": "test-key", "models": ["gpt-4", "gpt-3.5-turbo"]},
                "anthropic": {
                    "api_key": "test-key",
                    "models": ["claude-3-opus", "claude-3-sonnet"],
                },
                "local": {
                    "endpoint": "http://localhost:8080",
                    "models": ["llama-70b", "mistral-7b"],
                },
            },
            "routing_strategy": "cost_optimized",
            "fallback_enabled": True,
            "max_routing_time_ms": 500,
        }
        return IntelligentLLMRouter(config)

    @pytest.mark.asyncio
    async def test_route_simple_query_to_cheapest_model(self, router):
        """Simple queries should route to the cheapest capable model."""
        query = "What is the capital of France?"

        decision = await router.route_query(
            query=query,
            required_capabilities=["general_knowledge"],
            max_cost_per_request=0.01,
        )

        assert decision.selected_model == "mistral-7b"  # Cheapest model
        assert decision.estimated_cost < 0.001
        assert decision.routing_time_ms < 500
        assert "cost_optimized" in decision.reasoning

    @pytest.mark.asyncio
    async def test_route_complex_query_to_capable_model(self, router):
        """Complex queries should route to models with required capabilities."""
        query = """
        Analyze this code for potential security vulnerabilities and suggest 
        improvements following OWASP best practices. Include a threat model.
        """

        decision = await router.route_query(
            query=query,
            required_capabilities=["code_analysis", "security_expertise"],
            quality_threshold=0.9,
        )

        assert decision.selected_model in ["gpt-4", "claude-3-opus"]
        assert decision.complexity_score > 0.8
        assert len(decision.fallback_models) >= 2

    @pytest.mark.asyncio
    async def test_fallback_on_model_unavailability(self, router):
        """Router should fallback to next best model when primary is unavailable."""
        # Mock gpt-4 as unavailable
        with patch.object(router, "_check_model_availability", return_value=False):
            decision = await router.route_query(
                query="Complex analysis task",
                required_capabilities=["analysis"],
                preferred_models=["gpt-4"],
            )

            assert decision.selected_model != "gpt-4"
            assert decision.fallback_used is True
            assert "unavailable" in decision.reasoning

    @pytest.mark.asyncio
    async def test_load_balancing_across_models(self, router):
        """Router should distribute load across equivalent models."""
        model_usage = {}

        # Route 100 similar queries
        for i in range(100):
            decision = await router.route_query(
                query=f"Simple query {i}",
                required_capabilities=["general"],
                enable_load_balancing=True,
            )

            model = decision.selected_model
            model_usage[model] = model_usage.get(model, 0) + 1

        # Check load is distributed (no model should have >60% of requests)
        max_usage = max(model_usage.values())
        assert max_usage < 60

    @pytest.mark.asyncio
    async def test_routing_time_constraint(self, router):
        """Routing decision must be made within time constraint."""
        import time

        start = time.time()
        decision = await router.route_query(
            query="Test query",
            required_capabilities=["general"],
            max_routing_time_ms=100,
        )
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 100
        assert decision.routing_time_ms < 100


class TestCostOptimizationEngine:
    """Test cost optimization and prediction capabilities."""

    @pytest.fixture
    def optimizer(self):
        """Create cost optimizer instance."""
        return CostOptimizer()

    def test_predict_cost_for_model_combination(self, optimizer):
        """Should accurately predict costs for different model combinations."""
        models = ["gpt-4", "gpt-3.5-turbo"]
        token_estimate = {"input": 1000, "output": 500}

        cost_prediction = optimizer.predict_cost(models, token_estimate)

        assert cost_prediction["gpt-4"] == pytest.approx(
            0.06, 0.001
        )  # $0.03/1k in, $0.06/1k out
        assert cost_prediction["gpt-3.5-turbo"] == pytest.approx(0.002, 0.001)
        assert (
            cost_prediction["total_range"]["min"]
            < cost_prediction["total_range"]["max"]
        )

    def test_dynamic_model_selection_within_budget(self, optimizer):
        """Should select optimal models within budget constraints."""
        budget = 0.10  # $0.10 per request batch
        requests = [
            {"tokens": 1000, "priority": "high", "capabilities": ["analysis"]},
            {"tokens": 500, "priority": "low", "capabilities": ["general"]},
            {"tokens": 2000, "priority": "medium", "capabilities": ["code"]},
        ]

        selections = optimizer.optimize_batch_within_budget(requests, budget)

        total_cost = sum(s["estimated_cost"] for s in selections)
        assert total_cost <= budget
        assert selections[0]["model"] in ["gpt-4", "claude-3-opus"]  # High priority
        assert selections[1]["model"] in ["gpt-3.5-turbo", "mistral-7b"]  # Low priority

    def test_token_usage_tracking(self, optimizer):
        """Should track token usage and provide optimization recommendations."""
        # Simulate token usage over time
        for i in range(100):
            optimizer.track_usage(
                model="gpt-4",
                input_tokens=1000 + i * 10,
                output_tokens=500 + i * 5,
                cost=0.045,
            )

        recommendations = optimizer.get_optimization_recommendations()

        assert "reduce_gpt4_usage" in recommendations
        assert recommendations["potential_savings"] > 0
        assert "alternative_models" in recommendations


class TestPerformanceMonitoring:
    """Test performance monitoring and analytics."""

    @pytest.fixture
    def monitor(self):
        """Create performance monitor instance."""
        return PerformanceMonitor()

    @pytest.mark.asyncio
    async def test_track_response_metrics(self, monitor):
        """Should track response time, accuracy, and cost per request."""
        # Track a request
        request_id = await monitor.start_tracking(model="gpt-4", query_type="analysis")

        # Simulate processing
        await monitor.record_tokens(request_id, input_tokens=1000, output_tokens=500)
        await monitor.record_response_time(request_id, latency_ms=2500)
        await monitor.record_accuracy(request_id, confidence_score=0.95)

        metrics = await monitor.finalize_tracking(request_id)

        assert metrics["model"] == "gpt-4"
        assert metrics["latency_ms"] == 2500
        assert metrics["cost"] == pytest.approx(
            0.06, 0.001
        )  # 1000*0.03 + 500*0.06 = 0.06
        assert metrics["tokens"]["total"] == 1500

    @pytest.mark.asyncio
    async def test_ab_testing_routing_strategies(self, monitor):
        """Should support A/B testing different routing strategies."""
        # Configure A/B test
        ab_test = await monitor.create_ab_test(
            name="cost_vs_quality",
            strategies={
                "A": {"type": "cost_optimized", "weight": 0.5},
                "B": {"type": "quality_optimized", "weight": 0.5},
            },
            duration_hours=24,
        )

        # Simulate requests
        for i in range(100):
            strategy = await monitor.get_ab_test_assignment(ab_test["id"])
            await monitor.track_ab_result(
                test_id=ab_test["id"],
                strategy=strategy,
                cost=0.01 if strategy == "A" else 0.05,
                quality_score=0.8 if strategy == "A" else 0.95,
            )

        results = await monitor.get_ab_test_results(ab_test["id"])

        assert results["A"]["avg_cost"] < results["B"]["avg_cost"]
        assert results["A"]["avg_quality"] < results["B"]["avg_quality"]
        assert results["statistical_significance"] is not None

    def test_real_time_dashboard_metrics(self, monitor):
        """Should provide real-time metrics for dashboard."""
        metrics = monitor.get_dashboard_metrics()

        expected_metrics = [
            "requests_per_minute",
            "avg_latency_ms",
            "cost_per_request",
            "model_distribution",
            "error_rate",
            "cache_hit_rate",
        ]

        for metric in expected_metrics:
            assert metric in metrics


class TestMultiModelIntegration:
    """Test integration with multiple model providers."""

    @pytest.fixture
    def multi_model_router(self):
        """Create router with multiple providers configured."""
        return IntelligentLLMRouter(
            {
                "providers": {
                    "openai": {"models": ["gpt-4", "gpt-3.5-turbo"]},
                    "anthropic": {"models": ["claude-3-opus"]},
                    "cohere": {"models": ["command-r"]},
                    "huggingface": {"models": ["mixtral-8x7b"]},
                    "replicate": {"models": ["llama-2-70b"]},
                    "local": {"models": ["phi-2", "orca-mini"]},
                }
            }
        )

    def test_unified_interface_across_providers(self, multi_model_router):
        """Should provide unified interface regardless of provider."""
        providers = multi_model_router.get_available_providers()

        assert len(providers) >= 5

        for provider in providers:
            # Each provider should have standard interface
            assert hasattr(provider, "query")
            assert hasattr(provider, "stream_query")
            assert hasattr(provider, "get_model_info")
            assert hasattr(provider, "check_availability")

    @pytest.mark.asyncio
    async def test_prompt_optimization_per_model(self, multi_model_router):
        """Should optimize prompts for different model types."""
        base_prompt = "Analyze this code for bugs"

        # Get optimized prompts for different models
        gpt4_prompt = await multi_model_router.optimize_prompt(base_prompt, "gpt-4")
        claude_prompt = await multi_model_router.optimize_prompt(
            base_prompt, "claude-3-opus"
        )
        llama_prompt = await multi_model_router.optimize_prompt(
            base_prompt, "llama-2-70b"
        )

        # Each model should have different optimizations
        assert gpt4_prompt != claude_prompt != llama_prompt
        assert "```" in gpt4_prompt  # GPT-4 works well with markdown
        assert "Human:" in claude_prompt  # Claude prefers this format
        assert len(llama_prompt) < len(gpt4_prompt)  # Llama needs concise prompts

    @pytest.mark.asyncio
    async def test_model_specific_post_processing(self, multi_model_router):
        """Should apply model-specific post-processing and validation."""
        # Mock responses from different models
        responses = {
            "gpt-4": "```python\ndef hello():\n    print('world')\n```",
            "claude-3-opus": "I'll analyze this step by step:\n\n1. First...",
            "llama-2-70b": "Sure! Here is the analysis: [INST]...",
        }

        for model, raw_response in responses.items():
            processed = await multi_model_router.post_process_response(
                model=model, response=raw_response, expected_format="code_analysis"
            )

            assert processed["content"] is not None
            assert processed["confidence"] > 0
            assert "metadata" in processed

            # Model-specific validations
            if model == "gpt-4":
                assert "```" not in processed["content"]  # Code blocks extracted
            elif model == "llama-2-70b":
                assert "[INST]" not in processed["content"]  # Artifacts removed


class TestQueryComplexityAnalyzer:
    """Test query complexity analysis for routing decisions."""

    @pytest.fixture
    def analyzer(self):
        return QueryComplexityAnalyzer()

    def test_analyze_simple_query(self, analyzer):
        """Should correctly identify simple queries."""
        query = "What is 2 + 2?"

        analysis = analyzer.analyze(query)

        assert analysis["complexity_score"] < 0.3
        assert analysis["category"] == "simple"
        assert "arithmetic" in analysis["detected_patterns"]

    def test_analyze_complex_query(self, analyzer):
        """Should correctly identify complex multi-step queries."""
        query = """
        Given a distributed system with 5 nodes, where each node processes 
        1000 requests per second with a 99.9% success rate, calculate the 
        overall system reliability and suggest architectural improvements to 
        achieve 99.99% uptime considering network partitions and Byzantine failures.
        """

        analysis = analyzer.analyze(query)

        assert analysis["complexity_score"] > 0.8
        assert analysis["category"] == "complex"
        assert "multi_step_reasoning" in analysis["detected_patterns"]
        assert "technical_depth" in analysis["detected_patterns"]
        assert analysis["estimated_tokens"] > 100

    def test_detect_specific_capabilities_needed(self, analyzer):
        """Should detect specific capabilities required for queries."""
        test_cases = [
            ("Write a Python function to sort a list", ["code_generation", "python"]),
            (
                "Analyze this financial statement for risks",
                ["financial_analysis", "risk_assessment"],
            ),
            ("Translate this to French: Hello", ["translation", "french"]),
            ("Solve this differential equation", ["mathematics", "calculus"]),
        ]

        for query, expected_capabilities in test_cases:
            analysis = analyzer.analyze(query)
            for capability in expected_capabilities:
                assert capability in analysis["required_capabilities"]


class TestRequestQueueing:
    """Test request queuing and load balancing."""

    @pytest.fixture
    def router_with_queue(self):
        """Create router with queuing enabled."""
        config = {
            "providers": {
                "openai": {"models": ["gpt-4", "gpt-3.5-turbo"]},
                "anthropic": {"models": ["claude-3-opus", "claude-3-sonnet"]},
            },
            "queue_enabled": True,
            "max_concurrent_requests": 5,
            "queue_timeout_seconds": 30,
        }
        return IntelligentLLMRouter(config)

    @pytest.mark.asyncio
    async def test_request_queuing_under_load(self, router_with_queue):
        """Should queue requests when max concurrent limit reached."""
        import asyncio

        # Add a delay to internal routing to simulate processing time
        original_route = router_with_queue._route_query_internal

        async def delayed_route(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing delay
            return await original_route(*args, **kwargs)

        router_with_queue._route_query_internal = delayed_route

        # Simulate heavy load with 10 concurrent requests
        async def make_request(i):
            return await router_with_queue.route_query(
                query=f"Test query {i}", required_capabilities=["general"]
            )

        # Run 10 requests concurrently (exceeding limit of 5)
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All requests should complete successfully
        assert len(results) == 10
        assert all(r.selected_model is not None for r in results)

        # Check queue metrics
        queue_stats = router_with_queue.get_queue_statistics()
        print(f"Queue stats: {queue_stats}")
        # With delay, some requests should have been queued
        assert queue_stats["total_queued"] > 0
        assert queue_stats["priority_distribution"]["medium"] == 10

    @pytest.mark.asyncio
    async def test_request_priority_ordering(self, router_with_queue):
        """Should process high-priority requests first."""
        results = []

        # Queue several requests with different priorities
        for i in range(5):
            priority = "high" if i % 2 == 0 else "low"
            result = await router_with_queue.route_query(
                query=f"Query {i}", required_capabilities=["general"], priority=priority
            )
            results.append((i, priority, result))

        # Verify high priority requests were processed preferentially
        queue_stats = router_with_queue.get_queue_statistics()
        assert "priority_distribution" in queue_stats


class TestCostTracking:
    """Test cost tracking with sub-cent precision."""

    @pytest.fixture
    def cost_tracker(self):
        return CostOptimizer()

    def test_track_costs_with_sub_cent_precision(self, cost_tracker):
        """Should track costs with at least 4 decimal places."""
        # Track multiple small transactions
        transactions = [
            {"model": "gpt-3.5-turbo", "tokens": 100, "cost": 0.0002},
            {"model": "claude-haiku", "tokens": 50, "cost": 0.0001},
            {"model": "gpt-3.5-turbo", "tokens": 75, "cost": 0.00015},
        ]

        for txn in transactions:
            cost_tracker.track_usage(
                model=txn["model"],
                input_tokens=txn["tokens"],
                output_tokens=0,
                cost=txn["cost"],
            )

        totals = cost_tracker.get_cost_totals()

        assert totals["total"] == pytest.approx(0.00045, abs=0.00001)
        assert totals["by_model"]["gpt-3.5-turbo"] == pytest.approx(
            0.00035, abs=0.00001
        )
        assert totals["precision"] == "sub_cent"


class TestProductionFeatures:
    """Test advanced production features."""

    @pytest.fixture
    def production_router(self):
        """Create production-configured router."""
        config = {
            "providers": {
                "openai": {
                    "api_key": "test-key",
                    "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                },
                "anthropic": {
                    "api_key": "test-key",
                    "models": ["claude-3-opus", "claude-3-sonnet", "claude-haiku"],
                },
                "cohere": {"api_key": "test-key", "models": ["command-r"]},
                "local": {
                    "endpoint": "http://localhost:8080",
                    "models": ["llama-70b", "mistral-7b", "phi-2"],
                },
            },
            "routing_strategy": "balanced",
            "fallback_enabled": True,
            "queue_enabled": True,
            "max_concurrent_requests": 10,
            "cache_enabled": True,
            "error_recovery": True,
            "telemetry_enabled": True,
        }
        return IntelligentLLMRouter(config)

    @pytest.mark.asyncio
    async def test_end_to_end_routing_workflow(self, production_router):
        """Test complete routing workflow with all features."""
        # 1. Simple query - should use cheap model
        simple_result = await production_router.route_query(
            query="What is 2+2?", required_capabilities=["arithmetic"]
        )
        assert simple_result.selected_model in ["mistral-7b", "phi-2", "gpt-3.5-turbo"]
        assert simple_result.estimated_cost < 0.001

        # 2. Complex analysis - should use high-quality model
        complex_result = await production_router.route_query(
            query="Analyze the architectural patterns in this microservices system",
            required_capabilities=["code_analysis", "analysis"],
            quality_threshold=0.9,
        )
        assert complex_result.selected_model in ["gpt-4", "claude-3-opus"]

        # 3. Cost-constrained query
        budget_result = await production_router.route_query(
            query="Summarize this document", max_cost_per_request=0.005
        )
        assert budget_result.estimated_cost <= 0.005

        # 4. Get system statistics
        stats = production_router.get_system_statistics()
        assert stats["total_requests"] >= 3
        assert stats["model_distribution"] is not None
        assert stats["avg_routing_time_ms"] < 500

    @pytest.mark.asyncio
    async def test_error_recovery_and_fallback(self, production_router):
        """Test error recovery with automatic fallback."""
        # Mock a model failure
        original_check = production_router._check_model_availability

        async def mock_check(model):
            if model == "gpt-4":
                return False  # Simulate GPT-4 being down
            return await original_check(model)

        production_router._check_model_availability = mock_check

        # Should fallback to next best model
        result = await production_router.route_query(
            query="Complex task",
            preferred_models=["gpt-4"],
            required_capabilities=["analysis"],
        )

        assert result.selected_model != "gpt-4"
        assert result.fallback_used is True
        assert "fallback" in result.reasoning or "unavailable" in result.reasoning

    @pytest.mark.asyncio
    async def test_batch_processing_optimization(self, production_router):
        """Test batch processing for cost optimization."""
        queries = [
            {"query": "Simple task 1", "priority": "low"},
            {"query": "Complex analysis", "priority": "high"},
            {"query": "Medium task", "priority": "medium"},
        ]

        results = await production_router.process_batch(
            queries=queries, total_budget=0.10, optimize_for="cost"
        )

        assert len(results) == 3
        # Find the high priority result (should be first due to sorting)
        high_priority_result = next(r for r in results if r["priority"] == "high")
        assert high_priority_result["model"] in [
            "gpt-4",
            "claude-3-opus",
            "gpt-4-turbo",
        ]
        # Total cost should be within budget
        total_cost = sum(r["estimated_cost"] for r in results)
        assert total_cost <= 0.10
