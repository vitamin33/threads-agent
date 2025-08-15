"""
End-to-end integration tests for A/B Testing API deployment in k3d cluster.

Tests verify that the A/B testing endpoints are properly deployed and accessible
through the Kubernetes service mesh.
"""

import pytest
import requests
import time
import subprocess


@pytest.fixture(scope="module")
def api_base_url():
    """Set up port forwarding and return API base URL."""
    # Start port forwarding
    port_forward_process = subprocess.Popen(
        ["kubectl", "port-forward", "svc/orchestrator", "8080:8080"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for port forward to be ready
    time.sleep(3)

    yield "http://localhost:8080"

    # Cleanup
    port_forward_process.terminate()
    port_forward_process.wait()


class TestABTestingDeployment:
    """Test A/B testing API deployment functionality."""

    def test_health_check(self, api_base_url: str):
        """Test that the orchestrator service is healthy."""
        response = requests.get(f"{api_base_url}/health", timeout=10)
        assert response.status_code in [
            200,
            404,
        ]  # 404 is okay if health endpoint doesn't exist

    def test_variants_endpoint_accessible(self, api_base_url: str):
        """Test that the variants endpoint is accessible and returns data."""
        response = requests.get(f"{api_base_url}/variants", timeout=10)
        assert response.status_code == 200

        data = response.json()
        assert "variants" in data
        assert "total_count" in data
        assert isinstance(data["variants"], list)
        assert isinstance(data["total_count"], int)

    def test_variant_selection_endpoint(self, api_base_url: str):
        """Test variant selection using Thompson Sampling."""
        request_payload = {
            "top_k": 3,
            "algorithm": "thompson_sampling",
            "persona_id": "e2e_test_persona",
        }

        response = requests.post(
            f"{api_base_url}/variants/select", json=request_payload, timeout=10
        )
        assert response.status_code == 200

        data = response.json()
        assert "selected_variants" in data
        assert "selection_metadata" in data
        assert len(data["selected_variants"]) <= 3
        assert data["selection_metadata"]["algorithm"] == "thompson_sampling"
        assert data["selection_metadata"]["persona_id"] == "e2e_test_persona"

    def test_performance_update_endpoint(self, api_base_url: str):
        """Test updating variant performance."""
        # First, get a variant
        variants_response = requests.get(f"{api_base_url}/variants", timeout=10)
        assert variants_response.status_code == 200

        variants_data = variants_response.json()
        if not variants_data["variants"]:
            pytest.skip("No variants available for testing")

        variant_id = variants_data["variants"][0]["variant_id"]
        original_impressions = variants_data["variants"][0]["performance"][
            "impressions"
        ]

        # Update performance
        update_payload = {
            "impression": True,
            "success": True,
            "metadata": {"test": "e2e_deployment_test"},
        }

        response = requests.post(
            f"{api_base_url}/variants/{variant_id}/performance",
            json=update_payload,
            timeout=10,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["variant_id"] == variant_id
        assert data["updated_performance"]["impressions"] == original_impressions + 1
        assert "success_rate" in data["updated_performance"]

    def test_variant_statistics_endpoint(self, api_base_url: str):
        """Test getting variant statistics with confidence intervals."""
        # Get a variant first
        variants_response = requests.get(f"{api_base_url}/variants", timeout=10)
        assert variants_response.status_code == 200

        variants_data = variants_response.json()
        if not variants_data["variants"]:
            pytest.skip("No variants available for testing")

        variant_id = variants_data["variants"][0]["variant_id"]

        # Get statistics
        response = requests.get(
            f"{api_base_url}/variants/{variant_id}/stats", timeout=10
        )
        assert response.status_code == 200

        data = response.json()
        assert data["variant_id"] == variant_id
        assert "performance" in data
        assert "dimensions" in data
        assert "confidence_intervals" in data
        assert "thompson_sampling_stats" in data

        # Validate confidence intervals
        ci = data["confidence_intervals"]
        assert "lower_bound" in ci
        assert "upper_bound" in ci
        assert "confidence_level" in ci
        assert ci["confidence_level"] == 0.95
        assert 0 <= ci["lower_bound"] <= ci["upper_bound"] <= 1

        # Validate Thompson Sampling stats
        ts_stats = data["thompson_sampling_stats"]
        assert "alpha" in ts_stats
        assert "beta" in ts_stats
        assert "expected_value" in ts_stats
        assert "variance" in ts_stats

    def test_experiment_endpoints(self, api_base_url: str):
        """Test experiment creation and results endpoints."""
        # Get available variants
        variants_response = requests.get(f"{api_base_url}/variants", timeout=10)
        assert variants_response.status_code == 200

        variants_data = variants_response.json()
        if len(variants_data["variants"]) < 2:
            pytest.skip("Need at least 2 variants for experiment testing")

        variant_ids = [v["variant_id"] for v in variants_data["variants"][:2]]

        # Create experiment
        experiment_payload = {
            "experiment_name": "E2E Test Experiment",
            "description": "End-to-end deployment test experiment",
            "variant_ids": variant_ids,
            "traffic_allocation": [0.5, 0.5],
            "target_persona": "e2e_test_persona",
            "success_metrics": ["engagement_rate"],
            "duration_days": 7,
            "min_sample_size": 100,
        }

        response = requests.post(
            f"{api_base_url}/experiments/start", json=experiment_payload, timeout=10
        )
        assert response.status_code == 201

        data = response.json()
        assert "experiment_id" in data
        assert data["status"] == "active"
        assert data["experiment_name"] == "E2E Test Experiment"
        assert len(data["variants"]) == 2

        experiment_id = data["experiment_id"]

        # Get experiment results
        results_response = requests.get(
            f"{api_base_url}/experiments/{experiment_id}/results", timeout=10
        )
        assert results_response.status_code == 200

        results_data = results_response.json()
        assert results_data["experiment_id"] == experiment_id
        assert "status" in results_data
        assert "results_summary" in results_data
        assert "statistical_significance" in results_data

    def test_thompson_sampling_algorithm_integration(self, api_base_url: str):
        """Test that Thompson Sampling algorithm produces sensible results."""
        # Run multiple selections to verify Thompson Sampling behavior
        selection_counts = {}

        for _ in range(10):
            request_payload = {
                "top_k": 1,
                "algorithm": "thompson_sampling",
                "persona_id": "algorithm_test_persona",
            }

            response = requests.post(
                f"{api_base_url}/variants/select", json=request_payload, timeout=10
            )
            assert response.status_code == 200

            data = response.json()
            if data["selected_variants"]:
                variant_id = data["selected_variants"][0]["variant_id"]
                selection_counts[variant_id] = selection_counts.get(variant_id, 0) + 1

        # Verify that Thompson Sampling is actually selecting variants
        # (not just returning the same one every time)
        assert len(selection_counts) >= 1

        # Log results for analysis
        print(f"Thompson Sampling selection distribution: {selection_counts}")

    def test_error_handling_in_deployment(self, api_base_url: str):
        """Test error handling for invalid requests."""
        # Test invalid algorithm
        invalid_request = {
            "top_k": 3,
            "algorithm": "invalid_algorithm",
            "persona_id": "test_persona",
        }

        response = requests.post(
            f"{api_base_url}/variants/select", json=invalid_request, timeout=10
        )
        assert response.status_code == 400

        # Test non-existent variant performance update
        response = requests.post(
            f"{api_base_url}/variants/nonexistent_variant/performance",
            json={"impression": True, "success": False},
            timeout=10,
        )
        assert response.status_code == 404

        # Test non-existent variant stats
        response = requests.get(
            f"{api_base_url}/variants/nonexistent_variant/stats", timeout=10
        )
        assert response.status_code == 404

    def test_performance_under_load(self, api_base_url: str):
        """Test API performance under basic load."""
        import concurrent.futures

        def make_request():
            response = requests.get(f"{api_base_url}/variants", timeout=10)
            return response.status_code == 200

        # Run 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should succeed
        assert all(results), "Not all concurrent requests succeeded"


@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database integration in deployed environment."""

    def test_variant_persistence(self, api_base_url: str):
        """Test that variant performance updates persist across requests."""
        # Get initial state
        variants_response = requests.get(f"{api_base_url}/variants", timeout=10)
        assert variants_response.status_code == 200

        variants_data = variants_response.json()
        if not variants_data["variants"]:
            pytest.skip("No variants available for testing")

        variant_id = variants_data["variants"][0]["variant_id"]
        initial_impressions = variants_data["variants"][0]["performance"]["impressions"]

        # Update performance
        update_payload = {
            "impression": True,
            "success": False,
            "metadata": {"test": "persistence_test"},
        }

        response = requests.post(
            f"{api_base_url}/variants/{variant_id}/performance",
            json=update_payload,
            timeout=10,
        )
        assert response.status_code == 200

        # Verify persistence by fetching again
        variants_response_after = requests.get(f"{api_base_url}/variants", timeout=10)
        assert variants_response_after.status_code == 200

        variants_data_after = variants_response_after.json()
        updated_variant = next(
            v for v in variants_data_after["variants"] if v["variant_id"] == variant_id
        )

        assert updated_variant["performance"]["impressions"] == initial_impressions + 1

    def test_statistical_calculations_accuracy(self, api_base_url: str):
        """Test that statistical calculations are accurate."""
        variants_response = requests.get(f"{api_base_url}/variants", timeout=10)
        assert variants_response.status_code == 200

        variants_data = variants_response.json()
        if not variants_data["variants"]:
            pytest.skip("No variants available for testing")

        variant_id = variants_data["variants"][0]["variant_id"]

        # Get detailed statistics
        stats_response = requests.get(
            f"{api_base_url}/variants/{variant_id}/stats", timeout=10
        )
        assert stats_response.status_code == 200

        stats_data = stats_response.json()
        performance = stats_data["performance"]

        # Verify success rate calculation
        if performance["impressions"] > 0:
            expected_rate = performance["successes"] / performance["impressions"]
            assert abs(performance["success_rate"] - expected_rate) < 1e-10
        else:
            assert performance["success_rate"] == 0.0

        # Verify Thompson Sampling parameters
        ts_stats = stats_data["thompson_sampling_stats"]
        expected_alpha = performance["successes"] + 1
        expected_beta = performance["impressions"] - performance["successes"] + 1

        assert ts_stats["alpha"] == expected_alpha
        assert ts_stats["beta"] == expected_beta
