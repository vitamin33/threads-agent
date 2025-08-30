"""
End-to-End Integration Tests - Validate complete vLLM service functionality
"""

import time


class TestCompleteServiceIntegration:
    """Test complete service integration from API to response."""

    def test_service_startup_and_health_check_flow(self, test_client):
        """Test complete service startup and health check integration."""
        # Health endpoint should be accessible immediately
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()

        # Should provide complete health information
        assert "status" in data
        assert "model_loaded" in data
        assert "gpu_available" in data
        assert "apple_silicon_optimized" in data
        assert "warmup_completed" in data
        assert "memory_usage" in data
        assert "uptime_seconds" in data
        assert "performance_target_met" in data

        # Memory usage should be detailed
        memory = data["memory_usage"]
        assert isinstance(memory, dict)

        # Uptime should be positive
        assert data["uptime_seconds"] >= 0

    def test_complete_inference_pipeline(self, test_client, sample_chat_request):
        """Test complete inference pipeline from request to response."""
        # Make inference request
        response = test_client.post("/v1/chat/completions", json=sample_chat_request)

        assert response.status_code == 200
        data = response.json()

        # Validate complete OpenAI-compatible response structure
        assert "id" in data
        assert "object" in data
        assert data["object"] == "chat.completion"
        assert "created" in data
        assert "model" in data
        assert "choices" in data
        assert "usage" in data
        assert "cost_info" in data

        # Validate choices structure
        choice = data["choices"][0]
        assert "index" in choice
        assert "message" in choice
        assert "finish_reason" in choice

        message = choice["message"]
        assert message["role"] == "assistant"
        assert "content" in message
        assert len(message["content"]) > 0

        # Validate usage statistics
        usage = data["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage
        assert (
            usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
        )

        # Validate cost information
        cost_info = data["cost_info"]
        assert "vllm_cost_usd" in cost_info
        assert "openai_cost_usd" in cost_info
        assert "savings_usd" in cost_info
        assert "savings_percentage" in cost_info

        # Should show meaningful cost savings
        assert cost_info["savings_usd"] > 0
        assert cost_info["savings_percentage"] > 30
        assert cost_info["vllm_cost_usd"] < cost_info["openai_cost_usd"]

    def test_multiple_sequential_requests_consistency(
        self, test_client, sample_chat_request
    ):
        """Test multiple sequential requests maintain consistency."""
        responses = []

        # Make multiple requests
        for i in range(5):
            request = sample_chat_request.copy()
            request["messages"][0]["content"] = (
                f"Request {i}: {request['messages'][0]['content']}"
            )

            response = test_client.post("/v1/chat/completions", json=request)
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be valid
        for i, response_data in enumerate(responses):
            assert "choices" in response_data
            assert "usage" in response_data
            assert "cost_info" in response_data

            # Content should be different for different requests
            content = response_data["choices"][0]["message"]["content"]
            assert len(content) > 0

            # Cost calculations should be consistent
            cost_info = response_data["cost_info"]
            assert cost_info["savings_percentage"] > 30

        # Response IDs should be unique
        response_ids = [r["id"] for r in responses]
        assert len(set(response_ids)) == len(response_ids)  # All unique

    def test_concurrent_requests_handling(self, test_client, sample_chat_request):
        """Test concurrent request handling with realistic load."""
        import threading
        import queue

        # Create queue to collect results
        results = queue.Queue()

        def make_request(request_id):
            """Make a request and store result."""
            try:
                request = sample_chat_request.copy()
                request["messages"][0]["content"] = f"Concurrent request {request_id}"

                start_time = time.time()
                response = test_client.post("/v1/chat/completions", json=request)
                end_time = time.time()

                results.put(
                    {
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                        "data": response.json()
                        if response.status_code == 200
                        else None,
                    }
                )
            except Exception as e:
                results.put(
                    {"request_id": request_id, "error": str(e), "status_code": 500}
                )

        # Launch concurrent requests
        threads = []
        num_concurrent = 10

        for i in range(num_concurrent):
            thread = threading.Thread(target=make_request, args=(i,))
            thread.start()
            threads.append(thread)

        # Wait for all requests to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout

        # Collect results
        completed_results = []
        while not results.empty():
            completed_results.append(results.get())

        # All requests should complete successfully
        assert len(completed_results) == num_concurrent

        successful_results = [r for r in completed_results if r["status_code"] == 200]
        assert (
            len(successful_results) >= num_concurrent * 0.8
        )  # At least 80% success rate

        # Response times should be reasonable
        response_times = [r["response_time"] for r in successful_results]
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 5.0  # Average under 5 seconds

    def test_error_handling_integration(self, test_client):
        """Test error handling throughout the complete pipeline."""
        # Test invalid request format
        invalid_request = {
            "model": "invalid-model",
            "messages": [],  # Empty messages
            "max_tokens": -1,  # Invalid token count
        }

        response = test_client.post("/v1/chat/completions", json=invalid_request)

        # Should handle gracefully with appropriate error code
        assert response.status_code in [400, 422, 503]

        # Test malformed JSON
        response = test_client.post("/v1/chat/completions", data="invalid json")
        assert response.status_code == 422  # Unprocessable Entity

    def test_api_endpoint_integration(self, test_client):
        """Test integration across all API endpoints."""
        # Test models endpoint
        models_response = test_client.get("/models")
        assert models_response.status_code == 200

        models_data = models_response.json()
        assert "object" in models_data
        assert "data" in models_data
        assert len(models_data["data"]) > 0

        # Test cost comparison endpoint
        cost_response = test_client.get("/cost-comparison")
        assert cost_response.status_code == 200

        # Test quality metrics endpoint
        quality_response = test_client.get("/quality-metrics")
        assert quality_response.status_code == 200

        # Test performance metrics endpoint
        perf_response = test_client.get("/performance")
        assert perf_response.status_code == 200

        # Test latency metrics endpoint
        latency_response = test_client.get("/performance/latency")
        assert latency_response.status_code == 200

        latency_data = latency_response.json()
        assert "target_latency_ms" in latency_data
        assert latency_data["target_latency_ms"] == 50  # 50ms target

    def test_prometheus_metrics_integration(self, test_client, sample_chat_request):
        """Test Prometheus metrics integration with actual requests."""
        # Make some requests to generate metrics
        for i in range(3):
            response = test_client.post(
                "/v1/chat/completions", json=sample_chat_request
            )
            assert response.status_code == 200

        # Check metrics endpoint
        metrics_response = test_client.get("/metrics")
        assert metrics_response.status_code == 200

        metrics_text = metrics_response.text

        # Should contain vLLM-specific metrics
        expected_metrics = [
            "vllm_requests_total",
            "vllm_request_duration_seconds",
            "vllm_tokens_generated_total",
            "vllm_cost_savings_usd",
        ]

        for metric in expected_metrics:
            assert metric in metrics_text, f"Missing metric: {metric}"


class TestBusinessScenarioIntegration:
    """Test integration for realistic business scenarios."""

    def test_viral_content_generation_workflow(self, test_client):
        """Test complete viral content generation workflow."""
        # Test various viral content scenarios
        viral_scenarios = [
            {
                "scenario": "productivity_hook",
                "messages": [
                    {"role": "system", "content": "You are a viral content creator."},
                    {
                        "role": "user",
                        "content": "Write a viral hook about productivity that will get 1000+ likes",
                    },
                ],
                "max_tokens": 280,
                "temperature": 0.8,
            },
            {
                "scenario": "ai_controversy",
                "messages": [
                    {
                        "role": "system",
                        "content": "Create controversial but thoughtful content.",
                    },
                    {
                        "role": "user",
                        "content": "Write a hot take about AI replacing jobs",
                    },
                ],
                "max_tokens": 300,
                "temperature": 0.9,
            },
            {
                "scenario": "tech_insight",
                "messages": [
                    {
                        "role": "user",
                        "content": "Explain why most startups fail in one viral tweet",
                    }
                ],
                "max_tokens": 250,
                "temperature": 0.7,
            },
        ]

        results = []

        for scenario in viral_scenarios:
            response = test_client.post("/v1/chat/completions", json=scenario)
            assert response.status_code == 200

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Validate viral content characteristics
            assert len(content) > 50  # Substantial content
            assert len(content) <= 350  # Social media friendly

            # Should have cost savings
            assert data["cost_info"]["savings_percentage"] > 40

            results.append(
                {
                    "scenario": scenario["scenario"],
                    "content": content,
                    "cost_savings": data["cost_info"]["savings_percentage"],
                    "response_time": data.get("performance", {}).get(
                        "inference_time_ms", 0
                    ),
                }
            )

        # All scenarios should complete successfully
        assert len(results) == len(viral_scenarios)

        # Average cost savings should meet targets
        avg_savings = sum(r["cost_savings"] for r in results) / len(results)
        assert avg_savings >= 50.0  # 50%+ average savings

    def test_high_volume_content_generation(self, test_client):
        """Test high-volume content generation scenario."""
        # Simulate content calendar generation (30 posts)
        content_calendar = []

        base_request = {"model": "llama-3-8b", "max_tokens": 200, "temperature": 0.7}

        topics = [
            "productivity tips",
            "AI insights",
            "remote work",
            "startup advice",
            "tech trends",
            "career growth",
            "entrepreneurship",
            "innovation",
            "leadership",
            "marketing",
            "design thinking",
            "work-life balance",
            "team building",
            "customer success",
            "product management",
        ]

        start_time = time.time()

        for i in range(30):  # 30 posts for monthly content calendar
            topic = topics[i % len(topics)]
            request = base_request.copy()
            request["messages"] = [
                {
                    "role": "user",
                    "content": f"Create viral content about {topic} - post #{i + 1}",
                }
            ]

            response = test_client.post("/v1/chat/completions", json=request)
            assert response.status_code == 200

            data = response.json()
            content_calendar.append(
                {
                    "post_number": i + 1,
                    "topic": topic,
                    "content": data["choices"][0]["message"]["content"],
                    "cost_savings": data["cost_info"]["savings_percentage"],
                    "tokens": data["usage"]["total_tokens"],
                }
            )

        total_time = time.time() - start_time

        # Should complete all posts
        assert len(content_calendar) == 30

        # Calculate business metrics
        total_tokens = sum(p["tokens"] for p in content_calendar)
        avg_savings = sum(p["cost_savings"] for p in content_calendar) / 30

        # Business validation
        assert avg_savings >= 50.0  # Consistent cost savings
        assert total_time < 300  # Complete within 5 minutes
        assert total_tokens > 3000  # Substantial content generated

        # Content should be varied
        contents = [p["content"] for p in content_calendar]
        unique_contents = set(contents)
        assert len(unique_contents) >= 25  # At least 25 unique pieces of content

    def test_cost_optimization_demonstration(self, test_client):
        """Test cost optimization for portfolio demonstration."""
        # Simulate realistic business usage patterns
        business_scenarios = [
            # Daily social media content
            {"posts": 10, "avg_tokens": 300, "use_case": "social_media"},
            # Weekly blog post generation
            {"posts": 2, "avg_tokens": 1500, "use_case": "blog_posts"},
            # Customer support content
            {"posts": 20, "avg_tokens": 200, "use_case": "support_content"},
        ]

        total_cost_analysis = {
            "vllm_total_cost": 0,
            "openai_equivalent_cost": 0,
            "total_tokens": 0,
            "total_requests": 0,
        }

        for scenario in business_scenarios:
            for i in range(scenario["posts"]):
                request = {
                    "model": "llama-3-8b",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Generate {scenario['use_case']} content #{i + 1}",
                        }
                    ],
                    "max_tokens": scenario["avg_tokens"],
                    "temperature": 0.7,
                }

                response = test_client.post("/v1/chat/completions", json=request)
                assert response.status_code == 200

                data = response.json()
                cost_info = data["cost_info"]

                total_cost_analysis["vllm_total_cost"] += cost_info["vllm_cost_usd"]
                total_cost_analysis["openai_equivalent_cost"] += cost_info[
                    "openai_cost_usd"
                ]
                total_cost_analysis["total_tokens"] += data["usage"]["total_tokens"]
                total_cost_analysis["total_requests"] += 1

        # Calculate portfolio metrics
        total_savings = (
            total_cost_analysis["openai_equivalent_cost"]
            - total_cost_analysis["vllm_total_cost"]
        )
        savings_percentage = (
            total_savings / total_cost_analysis["openai_equivalent_cost"] * 100
        )

        # Portfolio demonstration requirements
        assert savings_percentage >= 60.0  # 60%+ cost reduction
        assert total_savings > 0.01  # Meaningful absolute savings
        assert total_cost_analysis["total_requests"] == 32  # All requests succeeded
        assert total_cost_analysis["total_tokens"] > 10000  # Substantial content

        # Monthly projection for business case
        monthly_vllm_cost = (
            total_cost_analysis["vllm_total_cost"] * 30
        )  # Scale to monthly
        monthly_openai_cost = total_cost_analysis["openai_equivalent_cost"] * 30
        monthly_savings = monthly_openai_cost - monthly_vllm_cost

        # Should demonstrate meaningful monthly savings
        assert monthly_savings > 10.0  # At least $10/month savings for this volume


class TestProductionReadinessIntegration:
    """Test production readiness aspects of the complete service."""

    def test_service_reliability_under_load(self, test_client, sample_chat_request):
        """Test service reliability under sustained load."""
        # Sustained load test (50 requests over time)
        success_count = 0
        error_count = 0
        response_times = []

        for i in range(50):
            start_time = time.time()

            try:
                response = test_client.post(
                    "/v1/chat/completions", json=sample_chat_request
                )
                end_time = time.time()

                if response.status_code == 200:
                    success_count += 1
                    response_times.append(end_time - start_time)
                else:
                    error_count += 1

            except Exception:
                error_count += 1

            # Small delay between requests
            time.sleep(0.1)

        # Reliability requirements
        success_rate = success_count / 50 * 100
        assert success_rate >= 95.0  # 95%+ success rate

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 10.0  # Average under 10 seconds

    def test_resource_management_integration(self, test_client):
        """Test resource management across service components."""
        # Get initial resource state
        initial_health = test_client.get("/health").json()
        initial_memory = initial_health["memory_usage"]

        # Make requests to increase resource usage
        requests_made = 0
        for i in range(20):
            request = {
                "model": "llama-3-8b",
                "messages": [
                    {"role": "user", "content": f"Large content generation request {i}"}
                ],
                "max_tokens": 500,  # Larger responses
                "temperature": 0.7,
            }

            response = test_client.post("/v1/chat/completions", json=request)
            if response.status_code == 200:
                requests_made += 1

        # Check resource state after load
        final_health = test_client.get("/health").json()
        final_memory = final_health["memory_usage"]

        # Memory usage should be tracked
        assert "process_rss_mb" in final_memory
        assert "process_percent" in final_memory

        # Service should remain healthy
        assert final_health["status"] in ["healthy", "initializing"]

        # Should have processed most requests
        assert requests_made >= 15  # At least 75% success rate

    def test_monitoring_integration_completeness(
        self, test_client, sample_chat_request
    ):
        """Test complete monitoring integration for production deployment."""
        # Generate activity for monitoring
        test_client.post("/v1/chat/completions", json=sample_chat_request)

        # Test all monitoring endpoints
        monitoring_endpoints = [
            "/health",
            "/metrics",
            "/performance",
            "/performance/latency",
            "/cost-comparison",
            "/quality-metrics",
        ]

        for endpoint in monitoring_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200, f"Monitoring endpoint {endpoint} failed"

            # Should return valid data
            if endpoint == "/metrics":
                assert len(response.text) > 0  # Prometheus metrics
            else:
                data = response.json()
                assert isinstance(data, dict)
                assert len(data) > 0

    def test_graceful_degradation_integration(self, test_client):
        """Test graceful degradation when components are unavailable."""
        # Test health check when service is degraded
        health_response = test_client.get("/health")
        assert health_response.status_code == 200

        health_data = health_response.json()

        # Even in fallback mode, should report status
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "initializing", "unhealthy"]

        # Should still provide basic functionality
        basic_request = {
            "model": "llama-3-8b",
            "messages": [{"role": "user", "content": "Simple test"}],
            "max_tokens": 50,
        }

        response = test_client.post("/v1/chat/completions", json=basic_request)

        # Should handle gracefully (either succeed or fail gracefully)
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "choices" in data
            assert len(data["choices"][0]["message"]["content"]) > 0
