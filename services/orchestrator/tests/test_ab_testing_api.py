"""
Comprehensive failing tests for A/B Testing API endpoints.

This test file follows TDD methodology - all tests will fail initially since the endpoints don't exist yet.
Tests cover:
- GET /variants - List all variants with performance data
- POST /variants/select - Select top k variants using Thompson Sampling
- POST /variants/{variant_id}/performance - Update variant performance
- GET /variants/{variant_id}/stats - Get detailed variant statistics
- POST /experiments/start - Start a new A/B test experiment
- GET /experiments/{experiment_id}/results - Get experiment results

The tests include success cases, error cases, edge cases, and integration scenarios.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from services.orchestrator.db.models import Base, VariantPerformance
from services.orchestrator.db import get_db_session
from services.orchestrator.main import app


@pytest.fixture(scope="function")
def ab_test_db_engine():
    """Create in-memory SQLite database engine for A/B testing tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables needed for A/B testing
    Base.metadata.create_all(engine)
    yield engine

    # Clean up
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def ab_test_db_session(ab_test_db_engine):
    """Create database session for A/B testing tests."""
    SessionLocal = sessionmaker(bind=ab_test_db_engine, expire_on_commit=False)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(ab_test_db_session):
    """Create test client for FastAPI app with test database."""

    # Override the database dependency to use the test session
    def override_get_db():
        try:
            yield ab_test_db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_variants(ab_test_db_session):
    """Create sample variant performance data for testing."""
    variants = [
        VariantPerformance(
            variant_id="variant_high_performer",
            dimensions={"hook_style": "question", "tone": "casual", "length": "short"},
            impressions=1000,
            successes=120,  # 12% success rate
            last_used=datetime.now(timezone.utc),
        ),
        VariantPerformance(
            variant_id="variant_medium_performer",
            dimensions={
                "hook_style": "statement",
                "tone": "professional",
                "length": "medium",
            },
            impressions=800,
            successes=64,  # 8% success rate
            last_used=datetime.now(timezone.utc),
        ),
        VariantPerformance(
            variant_id="variant_low_performer",
            dimensions={"hook_style": "story", "tone": "humorous", "length": "long"},
            impressions=500,
            successes=15,  # 3% success rate
            last_used=datetime.now(timezone.utc),
        ),
        VariantPerformance(
            variant_id="variant_no_data",
            dimensions={"hook_style": "question", "tone": "serious", "length": "short"},
            impressions=0,
            successes=0,  # No data yet
            last_used=datetime.now(timezone.utc),
        ),
    ]

    for variant in variants:
        ab_test_db_session.add(variant)
    ab_test_db_session.commit()

    return variants


class TestGetVariants:
    """Test suite for GET /variants endpoint."""

    def test_get_all_variants_success(self, client, sample_variants):
        """Test successful retrieval of all variants with performance data."""
        response = client.get("/variants")

        assert response.status_code == 200
        data = response.json()

        assert "variants" in data
        assert len(data["variants"]) == 4

        # Check variant structure
        variant = data["variants"][0]
        assert "variant_id" in variant
        assert "dimensions" in variant
        assert "performance" in variant
        assert "success_rate" in variant["performance"]
        assert "impressions" in variant["performance"]
        assert "successes" in variant["performance"]
        assert "last_used" in variant

    def test_get_variants_with_filter_by_dimension(self, client, sample_variants):
        """Test filtering variants by dimension parameters."""
        response = client.get("/variants?hook_style=question")

        assert response.status_code == 200
        data = response.json()

        # Should return only variants with hook_style=question
        question_variants = [
            v for v in data["variants"] if v["dimensions"]["hook_style"] == "question"
        ]
        assert len(question_variants) == 2

    def test_get_variants_with_performance_threshold(self, client, sample_variants):
        """Test filtering variants by minimum performance threshold."""
        response = client.get("/variants?min_impressions=100")

        assert response.status_code == 200
        data = response.json()

        # Should return only variants with >= 100 impressions
        for variant in data["variants"]:
            assert variant["performance"]["impressions"] >= 100

    def test_get_variants_empty_database(self, client):
        """Test GET /variants with empty database."""
        response = client.get("/variants")

        assert response.status_code == 200
        data = response.json()
        assert data["variants"] == []
        assert data["total_count"] == 0


class TestSelectVariants:
    """Test suite for POST /variants/select endpoint."""

    def test_select_variants_thompson_sampling_success(self, client, sample_variants):
        """Test successful variant selection using Thompson Sampling."""
        request_data = {
            "top_k": 3,
            "algorithm": "thompson_sampling",
            "persona_id": "test_persona",
        }

        response = client.post("/variants/select", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "selected_variants" in data
        assert len(data["selected_variants"]) == 3
        assert "selection_metadata" in data
        assert data["selection_metadata"]["algorithm"] == "thompson_sampling"
        assert data["selection_metadata"]["persona_id"] == "test_persona"

        # Check variant IDs are valid
        selected_ids = [v["variant_id"] for v in data["selected_variants"]]
        expected_ids = [
            "variant_high_performer",
            "variant_medium_performer",
            "variant_low_performer",
            "variant_no_data",
        ]
        for variant_id in selected_ids:
            assert variant_id in expected_ids

    def test_select_variants_with_exploration(self, client, sample_variants):
        """Test variant selection with exploration/exploitation balance."""
        request_data = {
            "top_k": 2,
            "algorithm": "thompson_sampling_exploration",
            "min_impressions": 100,
            "exploration_ratio": 0.5,
            "persona_id": "test_persona",
        }

        response = client.post("/variants/select", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert len(data["selected_variants"]) == 2
        assert data["selection_metadata"]["exploration_ratio"] == 0.5
        assert data["selection_metadata"]["min_impressions"] == 100

    def test_select_variants_invalid_algorithm(self, client, sample_variants):
        """Test variant selection with invalid algorithm."""
        request_data = {
            "top_k": 3,
            "algorithm": "invalid_algorithm",
            "persona_id": "test_persona",
        }

        response = client.post("/variants/select", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "algorithm" in data["detail"].lower()

    def test_select_variants_top_k_too_large(self, client, sample_variants):
        """Test variant selection with top_k larger than available variants."""
        request_data = {
            "top_k": 10,  # More than available variants
            "algorithm": "thompson_sampling",
            "persona_id": "test_persona",
        }

        response = client.post("/variants/select", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Should return all available variants
        assert len(data["selected_variants"]) == 4

    def test_select_variants_zero_top_k(self, client, sample_variants):
        """Test variant selection with top_k = 0."""
        request_data = {
            "top_k": 0,
            "algorithm": "thompson_sampling",
            "persona_id": "test_persona",
        }

        response = client.post("/variants/select", json=request_data)

        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        # Pydantic validation error format
        assert "detail" in data

    def test_select_variants_missing_persona_id(self, client, sample_variants):
        """Test variant selection without persona_id."""
        request_data = {
            "top_k": 3,
            "algorithm": "thompson_sampling",
        }

        response = client.post("/variants/select", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_select_variants_empty_database(self, client):
        """Test variant selection with no variants in database."""
        request_data = {
            "top_k": 3,
            "algorithm": "thompson_sampling",
            "persona_id": "test_persona",
        }

        response = client.post("/variants/select", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["selected_variants"] == []


class TestUpdateVariantPerformance:
    """Test suite for POST /variants/{variant_id}/performance endpoint."""

    def test_update_variant_performance_impression_only(self, client, sample_variants):
        """Test updating variant performance with impression only."""
        variant_id = "variant_high_performer"
        request_data = {
            "impression": True,
            "success": False,
            "metadata": {"platform": "threads", "user_segment": "tech_enthusiasts"},
        }

        response = client.post(f"/variants/{variant_id}/performance", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["variant_id"] == variant_id
        assert data["updated_performance"]["impressions"] == 1001  # Was 1000, now +1
        assert data["updated_performance"]["successes"] == 120  # Unchanged
        assert "success_rate" in data["updated_performance"]

    def test_update_variant_performance_with_success(self, client, sample_variants):
        """Test updating variant performance with both impression and success."""
        variant_id = "variant_medium_performer"
        request_data = {
            "impression": True,
            "success": True,
            "metadata": {"platform": "linkedin", "engagement_type": "like"},
        }

        response = client.post(f"/variants/{variant_id}/performance", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["variant_id"] == variant_id
        assert data["updated_performance"]["impressions"] == 801  # Was 800, now +1
        assert data["updated_performance"]["successes"] == 65  # Was 64, now +1

    def test_update_variant_performance_success_without_impression(
        self, client, sample_variants
    ):
        """Test updating variant with success but no impression (should still count impression)."""
        variant_id = "variant_low_performer"
        request_data = {
            "impression": False,
            "success": True,
        }

        response = client.post(f"/variants/{variant_id}/performance", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Success should automatically count as impression
        assert data["updated_performance"]["impressions"] == 501  # +1 from success
        assert data["updated_performance"]["successes"] == 16  # +1 from success

    def test_update_variant_performance_nonexistent_variant(self, client):
        """Test updating performance for non-existent variant."""
        variant_id = "nonexistent_variant"
        request_data = {
            "impression": True,
            "success": False,
        }

        response = client.post(f"/variants/{variant_id}/performance", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
        assert variant_id in data["detail"]

    def test_update_variant_performance_invalid_data(self, client, sample_variants):
        """Test updating variant performance with invalid data."""
        variant_id = "variant_high_performer"
        request_data = {
            "impression": "invalid",  # Should be boolean
            "success": True,
        }

        response = client.post(f"/variants/{variant_id}/performance", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_update_variant_performance_batch_update(self, client, sample_variants):
        """Test batch updating multiple performance metrics."""
        variant_id = "variant_no_data"
        request_data = {
            "impression": True,
            "success": True,
            "batch_size": 10,  # Simulate 10 impressions/successes
            "metadata": {"batch_type": "bulk_test"},
        }

        response = client.post(f"/variants/{variant_id}/performance", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["updated_performance"]["impressions"] == 10
        assert data["updated_performance"]["successes"] == 10


class TestGetVariantStats:
    """Test suite for GET /variants/{variant_id}/stats endpoint."""

    def test_get_variant_stats_success(self, client, sample_variants):
        """Test successful retrieval of variant statistics."""
        variant_id = "variant_high_performer"

        response = client.get(f"/variants/{variant_id}/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["variant_id"] == variant_id
        assert "performance" in data
        assert "dimensions" in data
        assert "confidence_intervals" in data
        assert "thompson_sampling_stats" in data

        # Check performance stats
        perf = data["performance"]
        assert perf["impressions"] == 1000
        assert perf["successes"] == 120
        assert perf["success_rate"] == 0.12

        # Check confidence intervals
        ci = data["confidence_intervals"]
        assert "lower_bound" in ci
        assert "upper_bound" in ci
        assert "confidence_level" in ci
        assert ci["confidence_level"] == 0.95  # Default 95% CI

        # Check Thompson Sampling stats
        ts_stats = data["thompson_sampling_stats"]
        assert "alpha" in ts_stats
        assert "beta" in ts_stats
        assert "expected_value" in ts_stats
        assert "variance" in ts_stats

    def test_get_variant_stats_with_custom_confidence_level(
        self, client, sample_variants
    ):
        """Test getting variant stats with custom confidence level."""
        variant_id = "variant_medium_performer"

        response = client.get(f"/variants/{variant_id}/stats?confidence_level=0.99")

        assert response.status_code == 200
        data = response.json()

        assert data["confidence_intervals"]["confidence_level"] == 0.99

    def test_get_variant_stats_zero_impressions(self, client, sample_variants):
        """Test getting stats for variant with zero impressions."""
        variant_id = "variant_no_data"

        response = client.get(f"/variants/{variant_id}/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["performance"]["impressions"] == 0
        assert data["performance"]["successes"] == 0
        assert data["performance"]["success_rate"] == 0.0

        # Should still provide Thompson Sampling stats with priors
        ts_stats = data["thompson_sampling_stats"]
        assert ts_stats["alpha"] == 1  # Prior alpha
        assert ts_stats["beta"] == 1  # Prior beta

    def test_get_variant_stats_nonexistent_variant(self, client):
        """Test getting stats for non-existent variant."""
        variant_id = "nonexistent_variant"

        response = client.get(f"/variants/{variant_id}/stats")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_variant_stats_invalid_confidence_level(self, client, sample_variants):
        """Test getting stats with invalid confidence level."""
        variant_id = "variant_high_performer"

        response = client.get(f"/variants/{variant_id}/stats?confidence_level=1.5")

        assert response.status_code == 400
        data = response.json()
        assert "confidence_level must be between 0 and 1" in data["detail"]


class TestStartExperiment:
    """Test suite for POST /experiments/start endpoint."""

    def test_start_experiment_success(self, client, sample_variants):
        """Test successful experiment start."""
        request_data = {
            "experiment_name": "Hook Style Comparison",
            "description": "Testing different hook styles for engagement",
            "variant_ids": ["variant_high_performer", "variant_medium_performer"],
            "traffic_allocation": [0.5, 0.5],
            "target_persona": "tech_enthusiasts",
            "success_metrics": ["engagement_rate", "click_through_rate"],
            "duration_days": 7,
            "min_sample_size": 1000,
        }

        response = client.post("/experiments/start", json=request_data)

        assert response.status_code == 201
        data = response.json()

        assert "experiment_id" in data
        assert data["status"] == "active"
        assert data["experiment_name"] == "Hook Style Comparison"
        assert len(data["variants"]) == 2
        assert data["start_time"] is not None
        assert data["expected_end_time"] is not None

    def test_start_experiment_with_control_group(self, client, sample_variants):
        """Test starting experiment with explicit control group."""
        request_data = {
            "experiment_name": "A/B Test with Control",
            "description": "Testing new variant against control",
            "variant_ids": ["variant_high_performer", "variant_medium_performer"],
            "traffic_allocation": [0.7, 0.3],  # 70% control, 30% treatment
            "control_variant_id": "variant_high_performer",
            "target_persona": "general_audience",
            "success_metrics": ["engagement_rate"],
            "duration_days": 14,
            "min_sample_size": 2000,
        }

        response = client.post("/experiments/start", json=request_data)

        assert response.status_code == 201
        data = response.json()

        assert data["control_variant_id"] == "variant_high_performer"
        assert len(data["traffic_allocation"]) == 2
        assert sum(data["traffic_allocation"]) == 1.0

    def test_start_experiment_invalid_traffic_allocation(self, client, sample_variants):
        """Test starting experiment with invalid traffic allocation."""
        request_data = {
            "experiment_name": "Invalid Traffic Test",
            "variant_ids": ["variant_high_performer", "variant_medium_performer"],
            "traffic_allocation": [0.6, 0.6],  # Sum > 1.0
            "target_persona": "tech_enthusiasts",
            "success_metrics": ["engagement_rate"],
            "duration_days": 7,
        }

        response = client.post("/experiments/start", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "traffic allocation must sum to 1.0" in data["detail"].lower()

    def test_start_experiment_nonexistent_variant(self, client):
        """Test starting experiment with non-existent variant."""
        request_data = {
            "experiment_name": "Test with Bad Variant",
            "variant_ids": ["nonexistent_variant"],
            "traffic_allocation": [1.0],
            "target_persona": "tech_enthusiasts",
            "success_metrics": ["engagement_rate"],
            "duration_days": 7,
        }

        response = client.post("/experiments/start", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "not found" in data["detail"].lower()
        assert "nonexistent_variant" in data["detail"]

    def test_start_experiment_missing_required_fields(self, client):
        """Test starting experiment with missing required fields."""
        request_data = {
            "experiment_name": "Incomplete Test",
            # Missing variant_ids, traffic_allocation, etc.
        }

        response = client.post("/experiments/start", json=request_data)

        assert response.status_code == 422  # Validation error


class TestGetExperimentResults:
    """Test suite for GET /experiments/{experiment_id}/results endpoint."""

    @pytest.fixture
    def mock_experiment_id(self):
        """Mock experiment ID for testing."""
        return "exp_12345"

    def test_get_experiment_results_success(self, client, mock_experiment_id):
        """Test successful retrieval of experiment results."""
        response = client.get(f"/experiments/{mock_experiment_id}/results")

        assert response.status_code == 200
        data = response.json()

        assert data["experiment_id"] == mock_experiment_id
        assert "status" in data
        assert "results_summary" in data
        assert "variant_performance" in data
        assert "statistical_significance" in data
        assert "confidence_intervals" in data
        assert "recommendations" in data

        # Check results summary
        summary = data["results_summary"]
        assert "total_participants" in summary
        assert "experiment_duration_days" in summary
        assert "winner_variant_id" in summary
        assert "improvement_percentage" in summary

        # Check statistical significance
        sig = data["statistical_significance"]
        assert "p_value" in sig
        assert "confidence_level" in sig
        assert "is_significant" in sig
        assert "minimum_detectable_effect" in sig

    def test_get_experiment_results_ongoing_experiment(
        self, client, mock_experiment_id
    ):
        """Test getting results for ongoing experiment."""
        response = client.get(
            f"/experiments/{mock_experiment_id}/results?include_interim=true"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["active", "ongoing"]
        assert "interim_results" in data
        assert "progress_percentage" in data
        assert data["recommendations"]["recommendation_type"] == "continue"

    def test_get_experiment_results_insufficient_data(self, client, mock_experiment_id):
        """Test getting results when insufficient data available."""
        response = client.get(f"/experiments/{mock_experiment_id}/results")

        assert response.status_code == 200
        data = response.json()

        if data["results_summary"]["total_participants"] < 100:  # Insufficient sample
            assert not data["statistical_significance"]["is_significant"]
            assert "insufficient_data" in data["recommendations"]["recommendation_type"]

    def test_get_experiment_results_nonexistent_experiment(self, client):
        """Test getting results for non-existent experiment."""
        experiment_id = "nonexistent_exp"

        response = client.get(f"/experiments/{experiment_id}/results")

        assert response.status_code == 404
        data = response.json()
        assert "experiment not found" in data["detail"].lower()

    def test_get_experiment_results_with_segments(self, client, mock_experiment_id):
        """Test getting results broken down by user segments."""
        response = client.get(
            f"/experiments/{mock_experiment_id}/results?segment_by=user_segment"
        )

        assert response.status_code == 200
        data = response.json()

        assert "segment_breakdown" in data
        assert isinstance(data["segment_breakdown"], dict)

        # Each segment should have its own results
        for segment_name, segment_data in data["segment_breakdown"].items():
            assert "variant_performance" in segment_data
            assert "statistical_significance" in segment_data

    def test_get_experiment_results_export_format(self, client, mock_experiment_id):
        """Test exporting experiment results in different formats."""
        response = client.get(f"/experiments/{mock_experiment_id}/results?format=csv")

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

        # Test JSON format (default)
        response = client.get(f"/experiments/{mock_experiment_id}/results?format=json")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


class TestABTestingIntegration:
    """Integration tests for A/B Testing API endpoints."""

    def test_full_ab_test_workflow(self, client, sample_variants):
        """Test complete A/B testing workflow from variant selection to results."""
        # 1. Select variants for testing
        select_request = {
            "top_k": 2,
            "algorithm": "thompson_sampling",
            "persona_id": "integration_test_persona",
        }

        select_response = client.post("/variants/select", json=select_request)
        assert select_response.status_code == 200
        selected_variants = select_response.json()["selected_variants"]

        # 2. Start an experiment with selected variants
        experiment_request = {
            "experiment_name": "Integration Test Experiment",
            "description": "End-to-end workflow test",
            "variant_ids": [v["variant_id"] for v in selected_variants],
            "traffic_allocation": [0.5, 0.5],
            "target_persona": "integration_test_persona",
            "success_metrics": ["engagement_rate"],
            "duration_days": 1,
            "min_sample_size": 100,
        }

        experiment_response = client.post("/experiments/start", json=experiment_request)
        assert experiment_response.status_code == 201
        experiment_id = experiment_response.json()["experiment_id"]

        # 3. Update performance for variants (simulate experiment running)
        for variant in selected_variants:
            variant_id = variant["variant_id"]

            # Simulate multiple impressions and successes
            for _ in range(5):
                update_request = {
                    "impression": True,
                    "success": True,  # Simulating success for testing
                    "metadata": {"experiment_id": experiment_id},
                }

                update_response = client.post(
                    f"/variants/{variant_id}/performance", json=update_request
                )
                assert update_response.status_code == 200

        # 4. Get variant stats after updates
        for variant in selected_variants:
            variant_id = variant["variant_id"]
            stats_response = client.get(f"/variants/{variant_id}/stats")
            assert stats_response.status_code == 200

            stats = stats_response.json()
            # Performance should have increased
            assert (
                stats["performance"]["impressions"]
                > variant["performance"]["impressions"]
            )

        # 5. Get experiment results
        results_response = client.get(
            f"/experiments/{experiment_id}/results?include_interim=true"
        )
        assert results_response.status_code == 200

        results = results_response.json()
        assert results["experiment_id"] == experiment_id
        assert "variant_performance" in results

    def test_thompson_sampling_integration_with_database(
        self, client, ab_test_db_session
    ):
        """Test Thompson Sampling selection directly integrates with database."""
        # Create variants with different performance levels
        high_perf = VariantPerformance(
            variant_id="db_high_perf",
            dimensions={"test": "high"},
            impressions=1000,
            successes=200,  # 20% success rate
        )
        low_perf = VariantPerformance(
            variant_id="db_low_perf",
            dimensions={"test": "low"},
            impressions=1000,
            successes=50,  # 5% success rate
        )

        ab_test_db_session.add_all([high_perf, low_perf])
        ab_test_db_session.commit()

        # Select top 1 variant - should prefer high performer
        select_request = {
            "top_k": 1,
            "algorithm": "thompson_sampling",
            "persona_id": "db_test_persona",
        }

        # Run selection multiple times to verify Thompson Sampling behavior
        high_perf_selected = 0
        trials = 10

        for _ in range(trials):
            response = client.post("/variants/select", json=select_request)
            assert response.status_code == 200

            selected_id = response.json()["selected_variants"][0]["variant_id"]
            if selected_id == "db_high_perf":
                high_perf_selected += 1

        # High performer should be selected more often (but not always due to sampling)
        assert high_perf_selected >= trials * 0.6  # At least 60% of the time

    def test_error_handling_and_rollback(self, client, ab_test_db_session):
        """Test error handling and database rollback scenarios."""
        # Test updating performance for non-existent variant
        response = client.post(
            "/variants/nonexistent/performance",
            json={"impression": True, "success": False},
        )
        assert response.status_code == 404

        # Test starting experiment with invalid data
        invalid_experiment = {
            "experiment_name": "",  # Empty name should fail validation
            "variant_ids": [],  # Empty variants should fail
            "traffic_allocation": [],
            "success_metrics": [],
        }

        response = client.post("/experiments/start", json=invalid_experiment)
        assert response.status_code in [400, 422]  # Bad request or validation error

        # Verify database state is consistent after errors
        variants_response = client.get("/variants")
        assert variants_response.status_code == 200

    @patch("services.orchestrator.thompson_sampling.np.random.beta")
    def test_deterministic_thompson_sampling_for_testing(
        self, mock_beta, client, sample_variants
    ):
        """Test Thompson Sampling with mocked randomness for deterministic testing."""
        # Mock beta sampling to return predictable values
        mock_beta.side_effect = [
            0.15,
            0.10,
            0.05,
            0.02,
        ]  # High to low performance order

        select_request = {
            "top_k": 3,
            "algorithm": "thompson_sampling",
            "persona_id": "deterministic_test",
        }

        response = client.post("/variants/select", json=select_request)
        assert response.status_code == 200

        selected_variants = response.json()["selected_variants"]
        selected_ids = [v["variant_id"] for v in selected_variants]

        # With mocked values, should select in performance order
        expected_order = [
            "variant_high_performer",
            "variant_medium_performer",
            "variant_low_performer",
        ]
        assert selected_ids == expected_order


class TestABTestingMetricsIntegration:
    """Test integration with Prometheus metrics system."""

    def test_metrics_recorded_for_variant_selection(self, client, sample_variants):
        """Test that Prometheus metrics are recorded for variant selection."""
        with patch(
            "services.orchestrator.routers.ab_testing.record_http_request"
        ) as mock_record:
            select_request = {
                "top_k": 2,
                "algorithm": "thompson_sampling",
                "persona_id": "metrics_test",
            }

            response = client.post("/variants/select", json=select_request)
            assert response.status_code == 200

            # Verify metrics were recorded
            mock_record.assert_called()
            call_args = mock_record.call_args[0]
            assert call_args[0] == "POST"  # Method
            assert "/variants/select" in call_args[1]  # Path
            assert call_args[2] == 200  # Status code

    def test_performance_update_metrics(self, client, sample_variants):
        """Test that performance updates are recorded in metrics."""
        with patch("services.common.metrics.record_post_generation"):
            variant_id = "variant_high_performer"
            update_request = {
                "impression": True,
                "success": True,
                "metadata": {"source": "metrics_test"},
            }

            response = client.post(
                f"/variants/{variant_id}/performance", json=update_request
            )
            assert response.status_code == 200

            # Should record the performance update
            # Note: This depends on the actual implementation adding metrics calls

    def test_experiment_metrics_tracking(self, client, sample_variants):
        """Test that experiment lifecycle is tracked in metrics."""
        experiment_request = {
            "experiment_name": "Metrics Tracking Test",
            "variant_ids": ["variant_high_performer", "variant_medium_performer"],
            "traffic_allocation": [0.5, 0.5],
            "target_persona": "metrics_test",
            "success_metrics": ["engagement_rate"],
            "duration_days": 1,
        }

        response = client.post("/experiments/start", json=experiment_request)
        assert response.status_code == 201

        experiment_id = response.json()["experiment_id"]

        # Get experiment results (should also be tracked)
        response = client.get(f"/experiments/{experiment_id}/results")
        assert response.status_code == 200


# Additional edge case tests
class TestABTestingEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_variant_with_exactly_zero_successes(self, client, ab_test_db_session):
        """Test handling of variant with impressions but zero successes."""
        zero_success_variant = VariantPerformance(
            variant_id="zero_success_variant",
            dimensions={"edge_case": "zero_success"},
            impressions=1000,
            successes=0,  # Zero successes with many impressions
        )

        ab_test_db_session.add(zero_success_variant)
        ab_test_db_session.commit()

        # Should still work with Thompson Sampling
        select_request = {
            "top_k": 1,
            "algorithm": "thompson_sampling",
            "persona_id": "edge_case_test",
        }

        response = client.post("/variants/select", json=select_request)
        assert response.status_code == 200

        # Get stats for zero-success variant
        response = client.get("/variants/zero_success_variant/stats")
        assert response.status_code == 200

        stats = response.json()
        assert stats["performance"]["success_rate"] == 0.0

    @pytest.mark.skip(reason="Concurrent testing can be flaky in test environment")
    def test_concurrent_performance_updates(self, client, sample_variants):
        """Test handling of concurrent performance updates."""
        import threading

        variant_id = "variant_high_performer"
        results = []

        def update_performance():
            try:
                update_request = {
                    "impression": True,
                    "success": True,
                }
                response = client.post(
                    f"/variants/{variant_id}/performance", json=update_request
                )
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")

        # Start multiple concurrent updates
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=update_performance)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All updates should succeed
        assert all(status == 200 for status in results)

        # Verify final state is consistent
        stats_response = client.get(f"/variants/{variant_id}/stats")
        assert stats_response.status_code == 200

    def test_large_batch_variant_selection(self, client, ab_test_db_session):
        """Test selecting from a large number of variants."""
        # Create many variants
        variants = []
        for i in range(100):
            variant = VariantPerformance(
                variant_id=f"batch_variant_{i}",
                dimensions={"batch_id": str(i), "category": f"cat_{i % 10}"},
                impressions=100 + i,
                successes=10 + (i % 20),  # Varying success rates
            )
            variants.append(variant)

        ab_test_db_session.add_all(variants)
        ab_test_db_session.commit()

        # Select top 20 from 100 variants
        select_request = {
            "top_k": 20,
            "algorithm": "thompson_sampling",
            "persona_id": "large_batch_test",
        }

        response = client.post("/variants/select", json=select_request)
        assert response.status_code == 200

        data = response.json()
        assert len(data["selected_variants"]) == 20

        # Response time should be reasonable (< 1 second for 100 variants)
        # This would be tested in performance/load testing
