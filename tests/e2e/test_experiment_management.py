"""
End-to-end tests for Real Experiment Management System

Tests the complete experiment lifecycle including creation, traffic allocation,
statistical significance monitoring, and result analysis.
"""

import pytest
import requests


@pytest.fixture(scope="module")
def api_base_url():
    """Set up port forwarding and return API base URL."""
    return "http://localhost:8080"


class TestExperimentManagement:
    """Test real experiment management functionality."""

    def test_experiment_system_health(self, api_base_url: str):
        """Test experiment management system health."""
        response = requests.get(f"{api_base_url}/experiments/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "warning"]
        assert data["database_connected"]

        print(f"System status: {data['status']}")
        print(f"Total experiments: {data['total_experiments']}")
        print(f"Active experiments: {data['active_experiments']}")

    def test_create_experiment(self, api_base_url: str):
        """Test creating a new experiment."""
        # First ensure we have variants
        init_response = requests.post(f"{api_base_url}/ab-content/variants/initialize")
        assert init_response.status_code == 200

        # Get available variants
        variants_response = requests.get(f"{api_base_url}/variants")
        assert variants_response.status_code == 200
        variants = variants_response.json()["variants"]

        if len(variants) < 2:
            pytest.skip("Need at least 2 variants for experiment testing")

        # Create experiment
        experiment_request = {
            "name": "E2E Test Experiment",
            "description": "End-to-end test for experiment management",
            "variant_ids": [variants[0]["variant_id"], variants[1]["variant_id"]],
            "traffic_allocation": [0.5, 0.5],
            "target_persona": "test_persona",
            "success_metrics": ["engagement_rate", "conversion_rate"],
            "duration_days": 7,
            "control_variant_id": variants[0]["variant_id"],
            "min_sample_size": 100,
            "significance_level": 0.05,
            "created_by": "e2e_test",
        }

        response = requests.post(
            f"{api_base_url}/experiments/create", json=experiment_request
        )
        assert response.status_code == 201

        data = response.json()
        assert "experiment_id" in data
        assert data["name"] == "E2E Test Experiment"
        assert data["status"] == "draft"
        assert len(data["variant_ids"]) == 2

        experiment_id = data["experiment_id"]
        print(f"Created experiment: {experiment_id}")

        return experiment_id

    def test_experiment_lifecycle(self, api_base_url: str):
        """Test complete experiment lifecycle: create -> start -> pause -> complete."""
        # Create experiment
        experiment_id = self.test_create_experiment(api_base_url)

        # Start experiment
        start_response = requests.post(
            f"{api_base_url}/experiments/{experiment_id}/start"
        )
        assert start_response.status_code == 200

        start_data = start_response.json()
        assert start_data["success"]
        assert start_data["new_status"] == "active"
        print(f"Started experiment: {experiment_id}")

        # Pause experiment
        pause_request = {"reason": "Testing pause functionality"}
        pause_response = requests.post(
            f"{api_base_url}/experiments/{experiment_id}/pause", json=pause_request
        )
        assert pause_response.status_code == 200

        pause_data = pause_response.json()
        assert pause_data["success"]
        assert pause_data["new_status"] == "paused"
        print(f"Paused experiment: {experiment_id}")

        # Complete experiment
        complete_response = requests.post(
            f"{api_base_url}/experiments/{experiment_id}/complete"
        )
        assert complete_response.status_code == 200

        complete_data = complete_response.json()
        assert complete_data["success"]
        assert complete_data["new_status"] == "completed"
        print(f"Completed experiment: {experiment_id}")

        return experiment_id

    def test_participant_assignment_and_tracking(self, api_base_url: str):
        """Test participant assignment and engagement tracking."""
        # Create and start an experiment
        experiment_id = self.test_create_experiment(api_base_url)

        # Start the experiment
        requests.post(f"{api_base_url}/experiments/{experiment_id}/start")

        # Assign multiple participants
        participants = ["user_001", "user_002", "user_003", "user_004", "user_005"]
        assignments = {}

        for participant_id in participants:
            assignment_request = {
                "participant_id": participant_id,
                "context": {"platform": "threads", "test": "traffic_allocation"},
            }

            response = requests.post(
                f"{api_base_url}/experiments/{experiment_id}/assign",
                json=assignment_request,
            )
            assert response.status_code == 200

            data = response.json()
            assert data["success"]
            assert data["assigned_variant_id"] is not None

            assignments[participant_id] = data["assigned_variant_id"]
            print(f"Assigned {participant_id} to {data['assigned_variant_id']}")

        # Verify traffic allocation is roughly 50/50
        variant_counts = {}
        for variant_id in assignments.values():
            variant_counts[variant_id] = variant_counts.get(variant_id, 0) + 1

        print(f"Traffic allocation: {variant_counts}")

        # Each variant should get some participants (might not be exactly 50/50 due to small sample)
        assert len(variant_counts) == 2  # Both variants should have participants

        # Track engagement for participants
        engagement_types = ["impression", "like", "share", "comment"]

        for participant_id, variant_id in assignments.items():
            for engagement_type in engagement_types:
                track_request = {
                    "participant_id": participant_id,
                    "variant_id": variant_id,
                    "action_taken": engagement_type,
                    "engagement_value": 1.0,
                    "metadata": {"test": "e2e_tracking"},
                }

                response = requests.post(
                    f"{api_base_url}/experiments/{experiment_id}/track",
                    json=track_request,
                )
                assert response.status_code == 200

                data = response.json()
                assert data["success"]

        print(f"Tracked engagement for {len(participants)} participants")
        return experiment_id

    def test_experiment_results_and_analysis(self, api_base_url: str):
        """Test experiment results calculation and statistical analysis."""
        # Create experiment with data
        experiment_id = self.test_participant_assignment_and_tracking(api_base_url)

        # Complete the experiment to trigger final analysis
        requests.post(f"{api_base_url}/experiments/{experiment_id}/complete")

        # Get experiment results
        results_response = requests.get(
            f"{api_base_url}/experiments/{experiment_id}/results"
        )
        assert results_response.status_code == 200

        data = results_response.json()
        assert data["experiment_id"] == experiment_id
        assert data["status"] == "completed"
        assert "results_summary" in data
        assert "variant_performance" in data

        # Validate results summary
        summary = data["results_summary"]
        assert "total_participants" in summary
        assert "experiment_duration_days" in summary
        assert "is_statistically_significant" in summary

        # Validate variant performance
        variant_performance = data["variant_performance"]
        assert len(variant_performance) == 2  # Should have 2 variants

        for variant_id, perf in variant_performance.items():
            assert "participants" in perf
            assert "impressions" in perf
            assert "conversions" in perf
            assert "conversion_rate" in perf
            assert "allocated_traffic" in perf
            assert "actual_traffic" in perf

        print("Experiment results:")
        print(f"  Total participants: {summary['total_participants']}")
        print(f"  Winner: {summary.get('winner_variant_id', 'None')}")
        print(f"  Statistically significant: {summary['is_statistically_significant']}")
        print(f"  Improvement: {summary.get('improvement_percentage', 0):.1f}%")

        return experiment_id

    def test_list_experiments(self, api_base_url: str):
        """Test listing experiments with filtering."""
        # Create a few experiments first
        for i in range(3):
            self.test_create_experiment(api_base_url)

        # List all experiments
        response = requests.get(f"{api_base_url}/experiments/list")
        assert response.status_code == 200

        experiments = response.json()
        assert isinstance(experiments, list)
        assert len(experiments) >= 3

        # Test each experiment has required fields
        for exp in experiments:
            assert "experiment_id" in exp
            assert "name" in exp
            assert "status" in exp
            assert "target_persona" in exp
            assert "variant_count" in exp
            assert "created_at" in exp

        print(f"Listed {len(experiments)} experiments")

        # Test filtering by status
        draft_response = requests.get(f"{api_base_url}/experiments/list?status=draft")
        assert draft_response.status_code == 200

        draft_experiments = draft_response.json()
        for exp in draft_experiments:
            assert exp["status"] == "draft"

        print(f"Found {len(draft_experiments)} draft experiments")

    def test_active_experiments_for_persona(self, api_base_url: str):
        """Test getting active experiments for a specific persona."""
        # Create and start an experiment
        experiment_id = self.test_create_experiment(api_base_url)
        requests.post(f"{api_base_url}/experiments/{experiment_id}/start")

        # Get active experiments for the test persona
        response = requests.get(f"{api_base_url}/experiments/active/test_persona")
        assert response.status_code == 200

        data = response.json()
        assert data["persona_id"] == "test_persona"
        assert "active_experiments" in data
        assert "count" in data

        # Should have at least 1 active experiment
        assert data["count"] >= 1
        assert experiment_id in data["active_experiments"]

        print(f"Found {data['count']} active experiments for test_persona")

    def test_traffic_allocation_accuracy(self, api_base_url: str):
        """Test that traffic allocation is accurate and consistent."""
        # Create experiment with specific traffic allocation
        experiment_id = self.test_create_experiment(api_base_url)
        requests.post(f"{api_base_url}/experiments/{experiment_id}/start")

        # Assign many participants to test allocation accuracy
        assignments = {}

        for i in range(100):  # Large sample for better accuracy
            participant_id = f"traffic_test_user_{i:03d}"

            assignment_request = {
                "participant_id": participant_id,
                "context": {"test": "traffic_allocation"},
            }

            response = requests.post(
                f"{api_base_url}/experiments/{experiment_id}/assign",
                json=assignment_request,
            )
            assert response.status_code == 200

            data = response.json()
            variant_id = data["assigned_variant_id"]
            assignments[variant_id] = assignments.get(variant_id, 0) + 1

        # Check allocation accuracy (should be close to 50/50)
        print(f"Traffic allocation results: {assignments}")

        total_assignments = sum(assignments.values())
        for variant_id, count in assignments.items():
            allocation_percentage = count / total_assignments
            print(f"  {variant_id}: {count} assignments ({allocation_percentage:.1%})")

            # Should be close to 50% (within 20% tolerance for small samples)
            assert 0.3 <= allocation_percentage <= 0.7

    def test_statistical_analysis_accuracy(self, api_base_url: str):
        """Test statistical analysis and significance calculation."""
        # Create experiment with data
        experiment_id = self.test_participant_assignment_and_tracking(api_base_url)

        # Get results before completion (should be ongoing)
        results_response = requests.get(
            f"{api_base_url}/experiments/{experiment_id}/results"
        )
        assert results_response.status_code == 200

        data = results_response.json()
        summary = data["results_summary"]

        # Verify statistical data structure
        assert "is_statistically_significant" in summary
        assert "p_value" in summary
        assert data["confidence_level"] > 0

        # Verify variant performance data
        for variant_id, perf in data["variant_performance"].items():
            # Check that conversion rate calculation is correct
            if perf["impressions"] > 0:
                expected_rate = perf["conversions"] / perf["impressions"]
                assert abs(perf["conversion_rate"] - expected_rate) < 1e-10

            # Check traffic allocation tracking
            assert 0 <= perf["actual_traffic"] <= 1.0
            assert 0 <= perf["allocated_traffic"] <= 1.0

        print(f"Statistical analysis validated for experiment {experiment_id}")

    def test_experiment_error_handling(self, api_base_url: str):
        """Test error handling for experiment management."""
        # Test creating experiment with invalid data
        invalid_request = {
            "name": "",  # Empty name
            "variant_ids": [],  # No variants
            "traffic_allocation": [],
            "target_persona": "test",
            "success_metrics": [],
            "duration_days": 0,  # Invalid duration
        }

        response = requests.post(
            f"{api_base_url}/experiments/create", json=invalid_request
        )
        assert response.status_code == 400

        # Test starting non-existent experiment
        response = requests.post(f"{api_base_url}/experiments/nonexistent/start")
        assert response.status_code == 400

        # Test getting results for non-existent experiment
        response = requests.get(f"{api_base_url}/experiments/nonexistent/results")
        assert response.status_code == 404

        print("Error handling tests passed")

    def test_full_experiment_workflow(self, api_base_url: str):
        """Test complete experiment workflow from creation to analysis."""
        print("\n=== Testing Full Experiment Management Workflow ===")

        # Initialize system
        print("1. Initializing variants...")
        init_response = requests.post(f"{api_base_url}/ab-content/variants/initialize")
        assert init_response.status_code == 200

        # Get variants
        variants_response = requests.get(f"{api_base_url}/variants")
        variants = variants_response.json()["variants"][:3]  # Use first 3 variants

        # Create experiment with 3-way split
        print("2. Creating experiment...")
        experiment_request = {
            "name": "Full Workflow Test Experiment",
            "description": "Complete workflow test with 3 variants",
            "variant_ids": [v["variant_id"] for v in variants],
            "traffic_allocation": [0.4, 0.3, 0.3],  # Uneven split for testing
            "target_persona": "workflow_test_persona",
            "success_metrics": ["engagement_rate", "click_through_rate"],
            "duration_days": 14,
            "control_variant_id": variants[0]["variant_id"],
            "min_sample_size": 200,
            "significance_level": 0.05,
            "created_by": "workflow_test",
        }

        create_response = requests.post(
            f"{api_base_url}/experiments/create", json=experiment_request
        )
        assert create_response.status_code == 201
        experiment_id = create_response.json()["experiment_id"]

        # Start experiment
        print("3. Starting experiment...")
        start_response = requests.post(
            f"{api_base_url}/experiments/{experiment_id}/start"
        )
        assert start_response.status_code == 200

        # Simulate participants and engagement
        print("4. Simulating participant engagement...")

        # Simulate different performance for each variant
        variant_configs = [
            {
                "conversion_rate": 0.12,
                "engagement_multiplier": 1.2,
            },  # Control - good performance
            {
                "conversion_rate": 0.08,
                "engagement_multiplier": 0.8,
            },  # Variant 1 - poor performance
            {
                "conversion_rate": 0.15,
                "engagement_multiplier": 1.5,
            },  # Variant 2 - best performance
        ]

        for i in range(60):  # 60 participants for statistical power
            participant_id = f"workflow_user_{i:03d}"

            # Assign participant
            assign_response = requests.post(
                f"{api_base_url}/experiments/{experiment_id}/assign",
                json={"participant_id": participant_id},
            )
            assert assign_response.status_code == 200

            assigned_variant = assign_response.json()["assigned_variant_id"]

            # Track impression
            requests.post(
                f"{api_base_url}/experiments/{experiment_id}/track",
                json={
                    "participant_id": participant_id,
                    "variant_id": assigned_variant,
                    "action_taken": "impression",
                    "engagement_value": 1.0,
                },
            )

            # Simulate conversions based on variant performance
            variant_index = None
            for idx, variant in enumerate(variants):
                if variant["variant_id"] == assigned_variant:
                    variant_index = idx
                    break

            if variant_index is not None:
                config = variant_configs[variant_index]

                # Simulate conversion based on configured rate
                import random

                if random.random() < config["conversion_rate"]:
                    # Track conversion
                    requests.post(
                        f"{api_base_url}/experiments/{experiment_id}/track",
                        json={
                            "participant_id": participant_id,
                            "variant_id": assigned_variant,
                            "action_taken": "conversion",
                            "engagement_value": config["engagement_multiplier"],
                        },
                    )

        print("5. Completing experiment and analyzing results...")

        # Complete experiment
        complete_response = requests.post(
            f"{api_base_url}/experiments/{experiment_id}/complete"
        )
        assert complete_response.status_code == 200

        # Get final results
        results_response = requests.get(
            f"{api_base_url}/experiments/{experiment_id}/results"
        )
        assert results_response.status_code == 200

        results = results_response.json()
        summary = results["results_summary"]

        print("6. Final Results:")
        print(f"   Total participants: {summary['total_participants']}")
        print(f"   Winner: {summary.get('winner_variant_id', 'No clear winner')}")
        print(f"   Improvement: {summary.get('improvement_percentage', 0):.1f}%")
        print(
            f"   Statistically significant: {summary['is_statistically_significant']}"
        )
        print(f"   P-value: {summary.get('p_value', 'N/A')}")

        print("\nVariant Performance:")
        for variant_id, perf in results["variant_performance"].items():
            print(f"   {variant_id}:")
            print(f"     Participants: {perf['participants']}")
            print(f"     Conversion Rate: {perf['conversion_rate']:.3f}")
            print(
                f"     Traffic: {perf['actual_traffic']:.1%} (allocated: {perf['allocated_traffic']:.1%})"
            )

        # Validate that results make sense
        assert summary["total_participants"] > 0
        assert len(results["variant_performance"]) == 3

        # If we have enough data, we should get meaningful results
        if summary["total_participants"] >= 30:
            # Winner should be the variant with highest conversion rate (variant 2 in our simulation)
            expected_winner = variants[2]["variant_id"]  # Best performing variant
            if summary.get("winner_variant_id"):
                print(f"   Expected winner: {expected_winner}")
                print(f"   Actual winner: {summary['winner_variant_id']}")

        print("\n=== Full Experiment Management Workflow Completed Successfully ===")

    def test_experiment_list_and_filtering(self, api_base_url: str):
        """Test experiment listing and filtering capabilities."""
        # Create experiments in different states
        self.test_create_experiment(api_base_url)

        # List all experiments
        all_response = requests.get(f"{api_base_url}/experiments/list")
        assert all_response.status_code == 200
        all_experiments = all_response.json()

        # Filter by status
        draft_response = requests.get(f"{api_base_url}/experiments/list?status=draft")
        assert draft_response.status_code == 200
        draft_experiments = draft_response.json()

        # Filter by persona
        persona_response = requests.get(
            f"{api_base_url}/experiments/list?target_persona=test_persona"
        )
        assert persona_response.status_code == 200
        persona_experiments = persona_response.json()

        print("Experiment filtering results:")
        print(f"  Total experiments: {len(all_experiments)}")
        print(f"  Draft experiments: {len(draft_experiments)}")
        print(f"  Test persona experiments: {len(persona_experiments)}")

        # Validate filtering works
        for exp in draft_experiments:
            assert exp["status"] == "draft"

        for exp in persona_experiments:
            assert exp["target_persona"] == "test_persona"

    def test_concurrent_participant_assignment(self, api_base_url: str):
        """Test concurrent participant assignment for traffic allocation accuracy."""
        # Create and start experiment
        experiment_id = self.test_create_experiment(api_base_url)
        requests.post(f"{api_base_url}/experiments/{experiment_id}/start")

        import concurrent.futures

        def assign_participant(participant_index: int) -> str:
            try:
                response = requests.post(
                    f"{api_base_url}/experiments/{experiment_id}/assign",
                    json={"participant_id": f"concurrent_user_{participant_index}"},
                    timeout=10,
                )
                if response.status_code == 200:
                    return response.json()["assigned_variant_id"]
                return "FAILED"
            except Exception:
                return "ERROR"

        # Assign 50 participants concurrently
        print("Testing concurrent participant assignment...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(assign_participant, i) for i in range(50)]
            assignments = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Count variant assignments
        variant_counts = {}
        successful_assignments = 0

        for assignment in assignments:
            if assignment not in ["FAILED", "ERROR"]:
                successful_assignments += 1
                variant_counts[assignment] = variant_counts.get(assignment, 0) + 1

        print("Concurrent assignment results:")
        print(f"  Successful assignments: {successful_assignments}/50")
        print(f"  Variant distribution: {variant_counts}")

        # Should have high success rate and reasonable distribution
        assert successful_assignments >= 45  # At least 90% success
        assert len(variant_counts) == 2  # Both variants should get assignments


if __name__ == "__main__":
    # Allow running this test file directly for debugging
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
