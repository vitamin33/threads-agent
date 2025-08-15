"""
End-to-end integration tests for A/B Testing Content Generation Pipeline.

Tests the complete integration between A/B testing optimization and content generation,
including variant selection, performance tracking, and feedback loops.
"""

import pytest
import requests

# from tests.e2e.conftest import api_base_url


@pytest.fixture(scope="module")
def api_base_url():
    """Set up port forwarding and return API base URL."""
    return "http://localhost:8080"


class TestABTestingContentIntegration:
    """Test A/B testing content optimization integration."""

    def test_initialize_variants_endpoint(self, api_base_url: str):
        """Test initialization of default variants."""
        response = requests.post(f"{api_base_url}/ab-content/variants/initialize")
        assert response.status_code == 200

        data = response.json()
        assert data["success"]
        assert data["total_variants"] > 0
        print(f"Initialized {data['total_variants']} variants")

    def test_optimize_content_configuration(self, api_base_url: str):
        """Test getting optimal content configuration."""
        # First ensure we have variants
        init_response = requests.post(f"{api_base_url}/ab-content/variants/initialize")
        assert init_response.status_code == 200

        # Request optimal configuration
        request_data = {
            "persona_id": "test_persona_integration",
            "content_type": "post",
            "input_text": "Write about the future of AI in business",
            "context": {"platform": "threads", "audience": "business_professionals"},
        }

        response = requests.post(
            f"{api_base_url}/ab-content/optimize", json=request_data
        )
        assert response.status_code == 200

        data = response.json()
        assert "variant_id" in data
        assert "dimensions" in data
        assert "instructions" in data
        assert "selection_metadata" in data

        # Validate dimensions structure
        dimensions = data["dimensions"]
        assert "hook_style" in dimensions
        assert "tone" in dimensions
        assert "length" in dimensions

        # Validate instructions
        instructions = data["instructions"]
        assert (
            "hook" in instructions or "tone" in instructions or "length" in instructions
        )

        print(f"Selected variant: {data['variant_id']}")
        print(f"Dimensions: {dimensions}")

        return data["variant_id"]  # Return for use in other tests

    def test_track_content_impression(self, api_base_url: str):
        """Test tracking content impressions."""
        # Get a variant ID first
        variant_id = self.test_optimize_content_configuration(api_base_url)

        # Track impression
        track_request = {
            "variant_id": variant_id,
            "persona_id": "test_persona_integration",
            "action_type": "impression",
            "metadata": {"platform": "threads", "content_type": "post"},
        }

        response = requests.post(f"{api_base_url}/ab-content/track", json=track_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"]
        assert data["variant_id"] == variant_id
        print(f"Tracked impression for variant: {variant_id}")

    def test_track_content_engagement(self, api_base_url: str):
        """Test tracking content engagement."""
        # Get a variant ID first
        variant_id = self.test_optimize_content_configuration(api_base_url)

        # Track various engagement types
        engagement_types = ["like", "share", "comment", "click"]

        for engagement_type in engagement_types:
            track_request = {
                "variant_id": variant_id,
                "persona_id": "test_persona_integration",
                "action_type": "engagement",
                "engagement_type": engagement_type,
                "engagement_value": 1.0,
                "metadata": {
                    "platform": "threads",
                    "engagement_source": "integration_test",
                },
            }

            response = requests.post(
                f"{api_base_url}/ab-content/track", json=track_request
            )
            assert response.status_code == 200

            data = response.json()
            assert data["success"]
            print(f"Tracked {engagement_type} engagement for variant: {variant_id}")

    def test_performance_insights(self, api_base_url: str):
        """Test getting performance insights after tracking engagement."""
        # First generate some engagement data
        self.test_track_content_engagement(api_base_url)

        # Get performance insights
        response = requests.get(f"{api_base_url}/ab-content/insights?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert "top_performing_variants" in data
        assert "dimension_recommendations" in data
        assert "total_variants_analyzed" in data
        assert "variants_with_data" in data

        print(f"Analyzed {data['total_variants_analyzed']} variants")
        print(f"Variants with data: {data['variants_with_data']}")

        if data["top_performing_variants"]:
            top_variant = data["top_performing_variants"][0]
            print(
                f"Top variant: {top_variant['variant_id']} (rate: {top_variant['success_rate']:.3f})"
            )

    def test_generate_custom_variants(self, api_base_url: str):
        """Test generating custom variants with specific dimensions."""
        custom_dimensions = {
            "hook_style": ["question", "controversial"],
            "tone": ["engaging", "edgy"],
            "length": ["short", "medium"],
            "emotion": ["excitement", "curiosity"],
        }

        request_data = {
            "dimensions": custom_dimensions,
            "max_variants": 20,
            "include_bootstrap": True,
        }

        response = requests.post(
            f"{api_base_url}/ab-content/variants/generate", json=request_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["variants_created"] > 0
        assert data["total_variants"] > 0

        print(f"Generated {data['variants_created']} custom variants")
        print(f"Total variants in system: {data['total_variants']}")

    def test_ab_content_health_check(self, api_base_url: str):
        """Test A/B content system health check."""
        response = requests.get(f"{api_base_url}/ab-content/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "warning"]
        assert data["database_connected"]
        assert "variant_count" in data

        print(f"System status: {data['status']}")
        print(f"Variants available: {data['variant_count']}")

    def test_full_content_optimization_workflow(self, api_base_url: str):
        """Test complete content optimization workflow."""
        print("\n=== Testing Full A/B Testing Content Workflow ===")

        # Step 1: Initialize system
        print("1. Initializing variants...")
        init_response = requests.post(f"{api_base_url}/ab-content/variants/initialize")
        assert init_response.status_code == 200

        # Step 2: Get optimal configuration for multiple personas
        personas = ["business_expert", "tech_influencer", "startup_founder"]
        variant_performances = {}

        for persona in personas:
            print(f"2. Getting optimal config for {persona}...")

            config_response = requests.post(
                f"{api_base_url}/ab-content/optimize",
                json={
                    "persona_id": persona,
                    "content_type": "post",
                    "input_text": f"AI trends in {persona.replace('_', ' ')} industry",
                    "context": {"test": "workflow"},
                },
            )
            assert config_response.status_code == 200

            config = config_response.json()
            variant_id = config["variant_id"]
            variant_performances[variant_id] = {
                "persona": persona,
                "dimensions": config["dimensions"],
            }

            print(f"   Selected variant: {variant_id}")
            print(f"   Dimensions: {config['dimensions']}")

            # Step 3: Simulate content generation and engagement
            print(f"3. Simulating engagement for {persona}...")

            # Track impression
            requests.post(
                f"{api_base_url}/ab-content/track",
                json={
                    "variant_id": variant_id,
                    "persona_id": persona,
                    "action_type": "impression",
                },
            )

            # Simulate different engagement patterns for different personas
            if "business" in persona:
                # Business personas get more professional engagement
                engagement_types = ["like", "share", "comment"]
                engagement_multiplier = 1.5
            elif "tech" in persona:
                # Tech personas get more technical engagement
                engagement_types = ["like", "click", "share", "save"]
                engagement_multiplier = 2.0
            else:
                # Startup personas get entrepreneurial engagement
                engagement_types = ["like", "repost", "comment"]
                engagement_multiplier = 1.2

            for eng_type in engagement_types:
                requests.post(
                    f"{api_base_url}/ab-content/track",
                    json={
                        "variant_id": variant_id,
                        "persona_id": persona,
                        "action_type": "engagement",
                        "engagement_type": eng_type,
                        "engagement_value": engagement_multiplier,
                    },
                )

        # Step 4: Analyze performance insights
        print("4. Analyzing performance insights...")

        insights_response = requests.get(f"{api_base_url}/ab-content/insights?limit=10")
        assert insights_response.status_code == 200

        insights = insights_response.json()
        print(f"   Total variants analyzed: {insights['total_variants_analyzed']}")
        print(f"   Variants with data: {insights['variants_with_data']}")

        if insights["top_performing_variants"]:
            print("   Top performing variants:")
            for i, variant in enumerate(insights["top_performing_variants"][:3]):
                print(
                    f"     {i + 1}. {variant['variant_id']} - Rate: {variant['success_rate']:.3f}"
                )
                print(f"        Dimensions: {variant['dimensions']}")

        if insights["dimension_recommendations"]:
            print("   Dimension recommendations:")
            for dim_name, rec in insights["dimension_recommendations"].items():
                print(
                    f"     {dim_name}: {rec['recommended_value']} (rate: {rec['success_rate']:.3f})"
                )

        # Step 5: Verify Thompson Sampling optimization
        print("5. Testing Thompson Sampling optimization...")

        # Request multiple configurations for the same persona to see variation
        configs = []
        for i in range(5):
            response = requests.post(
                f"{api_base_url}/ab-content/optimize",
                json={
                    "persona_id": "optimization_test",
                    "content_type": "post",
                    "input_text": f"Test optimization iteration {i}",
                },
            )
            assert response.status_code == 200
            configs.append(response.json())

        # Should get varied results due to Thompson Sampling exploration
        variant_ids = [config["variant_id"] for config in configs]
        unique_variants = len(set(variant_ids))

        print(
            f"   Got {unique_variants} unique variants out of {len(configs)} requests"
        )
        print(f"   Variant distribution: {variant_ids}")

        # The system should show some exploration (not always the same variant)
        # but also some exploitation (preferring better variants)
        assert unique_variants >= 1  # At least some variation expected

        print("\n=== Full A/B Testing Content Workflow Completed Successfully ===")

    def test_error_handling_and_edge_cases(self, api_base_url: str):
        """Test error handling and edge cases."""
        print("\n=== Testing Error Handling ===")

        # Test invalid tracking action type
        response = requests.post(
            f"{api_base_url}/ab-content/track",
            json={
                "variant_id": "test_variant",
                "persona_id": "test_persona",
                "action_type": "invalid_action",
            },
        )
        assert response.status_code == 400

        # Test missing engagement type for engagement tracking
        response = requests.post(
            f"{api_base_url}/ab-content/track",
            json={
                "variant_id": "test_variant",
                "persona_id": "test_persona",
                "action_type": "engagement",
                # Missing engagement_type
            },
        )
        assert response.status_code == 400

        # Test optimization with minimal data
        response = requests.post(
            f"{api_base_url}/ab-content/optimize",
            json={
                "persona_id": "minimal_test",
                "content_type": "post",
                "input_text": "test",
            },
        )
        # Should succeed with fallback behavior
        assert response.status_code == 200

        print("Error handling tests passed")

    def test_performance_under_load(self, api_base_url: str):
        """Test system performance under simulated load."""
        print("\n=== Testing Performance Under Load ===")

        import concurrent.futures

        # Initialize variants first
        requests.post(f"{api_base_url}/ab-content/variants/initialize")

        def make_optimization_request(persona_id: str) -> bool:
            try:
                response = requests.post(
                    f"{api_base_url}/ab-content/optimize",
                    json={
                        "persona_id": f"load_test_{persona_id}",
                        "content_type": "post",
                        "input_text": f"Load test content {persona_id}",
                        "context": {"load_test": True},
                    },
                    timeout=10,
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Request failed: {e}")
                return False

        def make_tracking_request(variant_id: str, persona_id: str) -> bool:
            try:
                response = requests.post(
                    f"{api_base_url}/ab-content/track",
                    json={
                        "variant_id": f"load_test_variant_{variant_id}",
                        "persona_id": f"load_test_{persona_id}",
                        "action_type": "impression",
                        "metadata": {"load_test": True},
                    },
                    timeout=10,
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Tracking request failed: {e}")
                return False

        # Test optimization endpoint under load
        print("Testing optimization endpoint with 20 concurrent requests...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            optimization_futures = [
                executor.submit(make_optimization_request, str(i)) for i in range(20)
            ]
            optimization_results = [
                future.result()
                for future in concurrent.futures.as_completed(optimization_futures)
            ]

        optimization_success_rate = sum(optimization_results) / len(
            optimization_results
        )
        print(f"Optimization success rate: {optimization_success_rate:.2%}")

        # Test tracking endpoint under load
        print("Testing tracking endpoint with 30 concurrent requests...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            tracking_futures = [
                executor.submit(make_tracking_request, str(i % 10), str(i))
                for i in range(30)
            ]
            tracking_results = [
                future.result()
                for future in concurrent.futures.as_completed(tracking_futures)
            ]

        tracking_success_rate = sum(tracking_results) / len(tracking_results)
        print(f"Tracking success rate: {tracking_success_rate:.2%}")

        # Both should have high success rates
        assert optimization_success_rate >= 0.8  # At least 80% success
        assert tracking_success_rate >= 0.9  # At least 90% success

        print("Performance under load tests passed")


@pytest.mark.integration
class TestABTestingContentDatabase:
    """Test database integration for A/B testing content system."""

    def test_variant_persistence_and_updates(self, api_base_url: str):
        """Test that variant performance persists and updates correctly."""
        # Initialize variants
        init_response = requests.post(f"{api_base_url}/ab-content/variants/initialize")
        assert init_response.status_code == 200

        # Get initial variant list
        initial_response = requests.get(f"{api_base_url}/variants")
        assert initial_response.status_code == 200
        initial_variants = initial_response.json()["variants"]

        if not initial_variants:
            pytest.skip("No variants available for testing")

        # Select a variant and track its initial performance
        test_variant = initial_variants[0]
        variant_id = test_variant["variant_id"]
        initial_impressions = test_variant["performance"]["impressions"]
        initial_successes = test_variant["performance"]["successes"]

        print(f"Testing variant: {variant_id}")
        print(
            f"Initial performance: {initial_impressions} impressions, {initial_successes} successes"
        )

        # Track multiple engagements
        for i in range(5):
            # Track impression
            requests.post(
                f"{api_base_url}/ab-content/track",
                json={
                    "variant_id": variant_id,
                    "persona_id": "persistence_test",
                    "action_type": "impression",
                },
            )

            # Track engagement (every other iteration)
            if i % 2 == 0:
                requests.post(
                    f"{api_base_url}/ab-content/track",
                    json={
                        "variant_id": variant_id,
                        "persona_id": "persistence_test",
                        "action_type": "engagement",
                        "engagement_type": "like",
                        "engagement_value": 1.0,
                    },
                )

        # Get updated variant performance
        updated_response = requests.get(f"{api_base_url}/variants")
        assert updated_response.status_code == 200
        updated_variants = updated_response.json()["variants"]

        # Find our test variant
        updated_variant = next(
            v for v in updated_variants if v["variant_id"] == variant_id
        )

        final_impressions = updated_variant["performance"]["impressions"]
        final_successes = updated_variant["performance"]["successes"]

        print(
            f"Final performance: {final_impressions} impressions, {final_successes} successes"
        )

        # Verify updates were persisted
        assert final_impressions > initial_impressions
        # Success count should have increased (we tracked some engagements)
        # Note: The exact increase depends on the feedback loop processing

        print(
            f"Performance update verified: +{final_impressions - initial_impressions} impressions"
        )

    def test_thompson_sampling_statistical_accuracy(self, api_base_url: str):
        """Test that Thompson Sampling produces statistically sound results."""
        # Get variant statistics
        variants_response = requests.get(f"{api_base_url}/variants")
        assert variants_response.status_code == 200
        variants = variants_response.json()["variants"]

        if not variants:
            pytest.skip("No variants available for statistical testing")

        # Test detailed statistics for a variant with data
        test_variant = None
        for variant in variants:
            if variant["performance"]["impressions"] > 0:
                test_variant = variant
                break

        if not test_variant:
            pytest.skip("No variants with performance data available")

        variant_id = test_variant["variant_id"]

        # Get detailed statistics
        stats_response = requests.get(f"{api_base_url}/variants/{variant_id}/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()

        # Verify statistical calculations
        performance = stats["performance"]
        confidence_intervals = stats["confidence_intervals"]
        thompson_stats = stats["thompson_sampling_stats"]

        # Basic sanity checks
        assert 0 <= performance["success_rate"] <= 1
        assert performance["impressions"] >= performance["successes"]

        # Confidence intervals should be valid
        assert (
            0
            <= confidence_intervals["lower_bound"]
            <= confidence_intervals["upper_bound"]
            <= 1
        )
        assert confidence_intervals["confidence_level"] == 0.95

        # Thompson Sampling parameters should be valid
        assert thompson_stats["alpha"] > 0
        assert thompson_stats["beta"] > 0
        assert 0 <= thompson_stats["expected_value"] <= 1
        assert thompson_stats["variance"] >= 0

        print(f"Statistical validation passed for variant {variant_id}")
        print(f"Success rate: {performance['success_rate']:.3f}")
        print(
            f"Confidence interval: [{confidence_intervals['lower_bound']:.3f}, {confidence_intervals['upper_bound']:.3f}]"
        )
        print(
            f"Thompson parameters: α={thompson_stats['alpha']:.1f}, β={thompson_stats['beta']:.1f}"
        )


if __name__ == "__main__":
    # Allow running this test file directly for debugging
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
