"""
Comprehensive unit tests for experiment management system.

Tests experiment lifecycle, traffic allocation, statistical analysis,
and database persistence for Priority 3 implementation.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.orchestrator.db.models import (
    Base,
    VariantPerformance,
    ExperimentEvent,
    ExperimentVariant,
)
from services.orchestrator.experiment_manager import (
    ExperimentConfig,
    create_experiment_manager,
)


@pytest.fixture(scope="function")
def experiment_db_engine():
    """Create in-memory SQLite database engine for experiment tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables needed for experiment management
    Base.metadata.create_all(engine)
    yield engine

    # Clean up
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def experiment_db_session(experiment_db_engine):
    """Create database session for experiment tests."""
    SessionLocal = sessionmaker(bind=experiment_db_engine, expire_on_commit=False)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def sample_variants(experiment_db_session):
    """Create sample variants for experiment testing."""
    variants = [
        VariantPerformance(
            variant_id="variant_control",
            dimensions={
                "hook_style": "question",
                "tone": "professional",
                "length": "medium",
            },
            impressions=1000,
            successes=80,  # 8% success rate
            last_used=datetime.now(timezone.utc),
        ),
        VariantPerformance(
            variant_id="variant_treatment_a",
            dimensions={
                "hook_style": "controversial",
                "tone": "edgy",
                "length": "short",
            },
            impressions=800,
            successes=96,  # 12% success rate
            last_used=datetime.now(timezone.utc),
        ),
        VariantPerformance(
            variant_id="variant_treatment_b",
            dimensions={"hook_style": "story", "tone": "engaging", "length": "long"},
            impressions=600,
            successes=54,  # 9% success rate
            last_used=datetime.now(timezone.utc),
        ),
    ]

    for variant in variants:
        experiment_db_session.add(variant)
    experiment_db_session.commit()

    return variants


@pytest.fixture(scope="function")
def experiment_manager(experiment_db_session):
    """Create experiment manager for testing."""
    return create_experiment_manager(experiment_db_session)


class TestExperimentCreation:
    """Test experiment creation and validation."""

    def test_create_experiment_success(self, experiment_manager, sample_variants):
        """Test successful experiment creation."""
        config = ExperimentConfig(
            name="Test Experiment",
            description="Testing experiment creation",
            variant_ids=["variant_control", "variant_treatment_a"],
            traffic_allocation=[0.5, 0.5],
            target_persona="test_persona",
            success_metrics=["engagement_rate"],
            duration_days=7,
            control_variant_id="variant_control",
            min_sample_size=100,
            created_by="test_user",
        )

        experiment_id = experiment_manager.create_experiment(config)

        assert experiment_id is not None
        assert experiment_id.startswith("exp_")

        # Verify experiment was created in database
        experiment = experiment_manager._get_experiment(experiment_id)
        assert experiment is not None
        assert experiment.name == "Test Experiment"
        assert experiment.status == "draft"
        assert experiment.target_persona == "test_persona"

        # Verify variant records were created
        exp_variants = (
            experiment_manager.db_session.query(ExperimentVariant)
            .filter_by(experiment_id=experiment_id)
            .all()
        )
        assert len(exp_variants) == 2

        for exp_variant in exp_variants:
            assert exp_variant.allocated_traffic == 0.5
            assert exp_variant.actual_traffic == 0.0
            assert exp_variant.participants == 0

    def test_create_experiment_validation_errors(
        self, experiment_manager, sample_variants
    ):
        """Test experiment creation validation errors."""

        # Test empty name
        with pytest.raises(ValueError, match="name cannot be empty"):
            config = ExperimentConfig(
                name="",
                variant_ids=["variant_control"],
                traffic_allocation=[1.0],
                target_persona="test",
                success_metrics=["engagement"],
                duration_days=7,
            )
            experiment_manager.create_experiment(config)

        # Test traffic allocation doesn't sum to 1
        with pytest.raises(ValueError, match="must sum to 1.0"):
            config = ExperimentConfig(
                name="Test",
                variant_ids=["variant_control", "variant_treatment_a"],
                traffic_allocation=[0.6, 0.6],  # Sums to 1.2
                target_persona="test",
                success_metrics=["engagement"],
                duration_days=7,
            )
            experiment_manager.create_experiment(config)

        # Test mismatched variants and allocation
        with pytest.raises(ValueError, match="must match traffic allocation"):
            config = ExperimentConfig(
                name="Test",
                variant_ids=["variant_control"],
                traffic_allocation=[0.5, 0.5],  # 2 allocations for 1 variant
                target_persona="test",
                success_metrics=["engagement"],
                duration_days=7,
            )
            experiment_manager.create_experiment(config)

        # Test non-existent variant
        with pytest.raises(ValueError, match="not found"):
            config = ExperimentConfig(
                name="Test",
                variant_ids=["nonexistent_variant"],
                traffic_allocation=[1.0],
                target_persona="test",
                success_metrics=["engagement"],
                duration_days=7,
            )
            experiment_manager.create_experiment(config)


class TestExperimentLifecycle:
    """Test experiment lifecycle management."""

    @pytest.fixture
    def created_experiment(self, experiment_manager, sample_variants):
        """Create a test experiment."""
        config = ExperimentConfig(
            name="Lifecycle Test Experiment",
            variant_ids=["variant_control", "variant_treatment_a"],
            traffic_allocation=[0.5, 0.5],
            target_persona="lifecycle_test",
            success_metrics=["engagement_rate"],
            duration_days=7,
        )
        return experiment_manager.create_experiment(config)

    def test_start_experiment(self, experiment_manager, created_experiment):
        """Test starting an experiment."""
        experiment_id = created_experiment

        # Start experiment
        success = experiment_manager.start_experiment(experiment_id)
        assert success

        # Verify status change
        experiment = experiment_manager._get_experiment(experiment_id)
        assert experiment.status == "active"
        assert experiment.start_time is not None
        assert experiment.expected_end_time is not None

        # Verify start event was recorded
        events = (
            experiment_manager.db_session.query(ExperimentEvent)
            .filter_by(experiment_id=experiment_id, event_type="experiment_started")
            .all()
        )
        assert len(events) == 1

    def test_pause_experiment(self, experiment_manager, created_experiment):
        """Test pausing an experiment."""
        experiment_id = created_experiment

        # Start then pause
        experiment_manager.start_experiment(experiment_id)
        success = experiment_manager.pause_experiment(experiment_id, "Testing pause")
        assert success

        # Verify status change
        experiment = experiment_manager._get_experiment(experiment_id)
        assert experiment.status == "paused"

        # Verify pause event was recorded
        events = (
            experiment_manager.db_session.query(ExperimentEvent)
            .filter_by(experiment_id=experiment_id, event_type="experiment_paused")
            .all()
        )
        assert len(events) == 1

    def test_complete_experiment(self, experiment_manager, created_experiment):
        """Test completing an experiment with results calculation."""
        experiment_id = created_experiment

        # Start experiment
        experiment_manager.start_experiment(experiment_id)

        # Add some test data by creating experiment events
        test_events = [
            ExperimentEvent(
                experiment_id=experiment_id,
                event_type="engagement",
                participant_id=f"user_{i}",
                variant_id="variant_control" if i % 2 == 0 else "variant_treatment_a",
                action_taken="conversion",
                engagement_value=1.0,
            )
            for i in range(10)
        ]

        for event in test_events:
            experiment_manager.db_session.add(event)
        experiment_manager.db_session.commit()

        # Complete experiment
        success = experiment_manager.complete_experiment(experiment_id)
        assert success

        # Verify status change
        experiment = experiment_manager._get_experiment(experiment_id)
        assert experiment.status == "completed"
        assert experiment.end_time is not None


class TestTrafficAllocation:
    """Test traffic allocation and participant assignment."""

    @pytest.fixture
    def active_experiment(self, experiment_manager, sample_variants):
        """Create and start a test experiment."""
        config = ExperimentConfig(
            name="Traffic Test",
            variant_ids=["variant_control", "variant_treatment_a"],
            traffic_allocation=[0.7, 0.3],  # 70/30 split
            target_persona="traffic_test",
            success_metrics=["engagement_rate"],
            duration_days=7,
        )
        experiment_id = experiment_manager.create_experiment(config)
        experiment_manager.start_experiment(experiment_id)
        return experiment_id

    def test_participant_assignment(self, experiment_manager, active_experiment):
        """Test participant assignment to variants."""
        experiment_id = active_experiment

        # Assign a participant
        assigned_variant = experiment_manager.assign_participant_to_variant(
            experiment_id, "test_user_001", {"platform": "threads"}
        )

        assert assigned_variant is not None
        assert assigned_variant in ["variant_control", "variant_treatment_a"]

        # Verify assignment was recorded
        events = (
            experiment_manager.db_session.query(ExperimentEvent)
            .filter_by(
                experiment_id=experiment_id,
                event_type="participant_assigned",
                participant_id="test_user_001",
            )
            .all()
        )
        assert len(events) == 1
        assert events[0].variant_id == assigned_variant

    def test_traffic_allocation_distribution(
        self, experiment_manager, active_experiment
    ):
        """Test traffic allocation accuracy over many assignments."""
        experiment_id = active_experiment

        assignments = {}

        # Assign 100 participants
        for i in range(100):
            participant_id = f"traffic_user_{i:03d}"
            assigned_variant = experiment_manager.assign_participant_to_variant(
                experiment_id, participant_id
            )

            if assigned_variant:
                assignments[assigned_variant] = assignments.get(assigned_variant, 0) + 1

        # Check distribution approximates 70/30 split
        total_assignments = sum(assignments.values())
        control_percentage = assignments.get("variant_control", 0) / total_assignments
        treatment_percentage = (
            assignments.get("variant_treatment_a", 0) / total_assignments
        )

        # Should be close to 70/30 (within 15% tolerance)
        assert 0.55 <= control_percentage <= 0.85
        assert 0.15 <= treatment_percentage <= 0.45

        print(
            f"Traffic allocation: Control={control_percentage:.1%}, Treatment={treatment_percentage:.1%}"
        )

    def test_consistent_assignment(self, experiment_manager, active_experiment):
        """Test that same participant gets same variant consistently."""
        experiment_id = active_experiment

        # Assign same participant multiple times
        participant_id = "consistent_user"

        assignments = []
        for _ in range(5):
            assigned_variant = experiment_manager.assign_participant_to_variant(
                experiment_id, participant_id
            )
            assignments.append(assigned_variant)

        # All assignments should be the same
        assert len(set(assignments)) == 1, f"Inconsistent assignments: {assignments}"


class TestEngagementTracking:
    """Test engagement tracking within experiments."""

    @pytest.fixture
    def experiment_with_participants(self, experiment_manager, sample_variants):
        """Create experiment with assigned participants."""
        config = ExperimentConfig(
            name="Engagement Test",
            variant_ids=["variant_control", "variant_treatment_a"],
            traffic_allocation=[0.5, 0.5],
            target_persona="engagement_test",
            success_metrics=["engagement_rate"],
            duration_days=7,
        )
        experiment_id = experiment_manager.create_experiment(config)
        experiment_manager.start_experiment(experiment_id)

        # Assign some participants
        participants = ["user_001", "user_002", "user_003"]
        assignments = {}

        for participant in participants:
            variant = experiment_manager.assign_participant_to_variant(
                experiment_id, participant
            )
            assignments[participant] = variant

        return experiment_id, assignments

    def test_record_engagement(self, experiment_manager, experiment_with_participants):
        """Test recording engagement events."""
        experiment_id, assignments = experiment_with_participants

        # Record various engagement types
        engagement_types = ["impression", "like", "share", "conversion"]

        for participant_id, variant_id in assignments.items():
            for engagement_type in engagement_types:
                success = experiment_manager.record_experiment_engagement(
                    experiment_id=experiment_id,
                    participant_id=participant_id,
                    variant_id=variant_id,
                    action_taken=engagement_type,
                    engagement_value=1.0,
                    metadata={"test": "engagement_tracking"},
                )
                assert success

        # Verify events were recorded
        total_events = (
            experiment_manager.db_session.query(ExperimentEvent)
            .filter_by(experiment_id=experiment_id, event_type="engagement")
            .count()
        )

        expected_events = len(assignments) * len(engagement_types)
        assert total_events == expected_events

    def test_variant_performance_updates(
        self, experiment_manager, experiment_with_participants
    ):
        """Test that variant performance updates correctly during experiments."""
        experiment_id, assignments = experiment_with_participants

        # Record impressions and conversions for one variant
        test_variant = list(assignments.values())[0]
        test_participant = list(assignments.keys())[0]

        # Get initial performance
        initial_variant = (
            experiment_manager.db_session.query(ExperimentVariant)
            .filter_by(experiment_id=experiment_id, variant_id=test_variant)
            .first()
        )
        initial_impressions = initial_variant.impressions
        initial_conversions = initial_variant.conversions

        # Record impression and conversion
        experiment_manager.record_experiment_engagement(
            experiment_id, test_participant, test_variant, "impression", 1.0
        )
        experiment_manager.record_experiment_engagement(
            experiment_id, test_participant, test_variant, "conversion", 1.0
        )

        # Check performance was updated
        updated_variant = (
            experiment_manager.db_session.query(ExperimentVariant)
            .filter_by(experiment_id=experiment_id, variant_id=test_variant)
            .first()
        )

        assert updated_variant.impressions == initial_impressions + 1
        assert updated_variant.conversions == initial_conversions + 1

        # Conversion rate should be updated
        if updated_variant.impressions > 0:
            expected_rate = updated_variant.conversions / updated_variant.impressions
            assert abs(updated_variant.conversion_rate - expected_rate) < 1e-10


class TestStatisticalAnalysis:
    """Test statistical analysis and significance calculation."""

    @pytest.fixture
    def experiment_with_data(self, experiment_manager, sample_variants):
        """Create experiment with statistical test data."""
        config = ExperimentConfig(
            name="Statistical Test",
            variant_ids=["variant_control", "variant_treatment_a"],
            traffic_allocation=[0.5, 0.5],
            target_persona="stats_test",
            success_metrics=["conversion_rate"],
            duration_days=7,
            control_variant_id="variant_control",
        )
        experiment_id = experiment_manager.create_experiment(config)
        experiment_manager.start_experiment(experiment_id)

        # Add substantial test data for statistical analysis
        # Control variant: 1000 impressions, 80 conversions (8% rate)
        control_variant = (
            experiment_manager.db_session.query(ExperimentVariant)
            .filter_by(experiment_id=experiment_id, variant_id="variant_control")
            .first()
        )
        control_variant.impressions = 1000
        control_variant.conversions = 80
        control_variant.conversion_rate = 0.08
        control_variant.participants = 1000

        # Treatment variant: 1000 impressions, 120 conversions (12% rate - significant improvement)
        treatment_variant = (
            experiment_manager.db_session.query(ExperimentVariant)
            .filter_by(experiment_id=experiment_id, variant_id="variant_treatment_a")
            .first()
        )
        treatment_variant.impressions = 1000
        treatment_variant.conversions = 120
        treatment_variant.conversion_rate = 0.12
        treatment_variant.participants = 1000

        experiment_manager.db_session.commit()

        return experiment_id

    def test_statistical_significance_calculation(
        self, experiment_manager, experiment_with_data
    ):
        """Test statistical significance calculation."""
        experiment_id = experiment_with_data

        # Get experiment results
        results = experiment_manager.get_experiment_results(experiment_id)

        assert results is not None
        assert results.experiment_id == experiment_id
        assert results.total_participants == 2000

        # With this data (8% vs 12% conversion rates, 1000 samples each),
        # the difference should be statistically significant
        assert results.winner_variant_id == "variant_treatment_a"
        assert results.improvement_percentage is not None
        assert results.improvement_percentage > 0

        # Verify variant performance data
        assert len(results.variant_performance) == 2

        control_perf = results.variant_performance["variant_control"]
        treatment_perf = results.variant_performance["variant_treatment_a"]

        assert control_perf["conversion_rate"] == 0.08
        assert treatment_perf["conversion_rate"] == 0.12
        assert treatment_perf["participants"] == 1000

    def test_insufficient_data_handling(self, experiment_manager, sample_variants):
        """Test handling of experiments with insufficient data."""
        config = ExperimentConfig(
            name="Insufficient Data Test",
            variant_ids=["variant_control", "variant_treatment_a"],
            traffic_allocation=[0.5, 0.5],
            target_persona="insufficient_test",
            success_metrics=["engagement_rate"],
            duration_days=7,
        )
        experiment_id = experiment_manager.create_experiment(config)
        experiment_manager.start_experiment(experiment_id)

        # Add minimal data (below statistical significance threshold)
        control_variant = (
            experiment_manager.db_session.query(ExperimentVariant)
            .filter_by(experiment_id=experiment_id, variant_id="variant_control")
            .first()
        )
        control_variant.impressions = 5
        control_variant.conversions = 1
        control_variant.participants = 5

        treatment_variant = (
            experiment_manager.db_session.query(ExperimentVariant)
            .filter_by(experiment_id=experiment_id, variant_id="variant_treatment_a")
            .first()
        )
        treatment_variant.impressions = 3
        treatment_variant.conversions = 2
        treatment_variant.participants = 3

        experiment_manager.db_session.commit()

        # Get results
        results = experiment_manager.get_experiment_results(experiment_id)

        # Should not claim statistical significance with so little data
        assert not results.is_statistically_significant
        assert results.p_value is None or results.p_value > 0.05


class TestExperimentManagement:
    """Test experiment management operations."""

    def test_list_experiments(self, experiment_manager, sample_variants):
        """Test listing experiments with filtering."""
        # Create experiments with different statuses
        configs = [
            ExperimentConfig(
                name="Draft Exp",
                variant_ids=["variant_control"],
                traffic_allocation=[1.0],
                target_persona="persona_a",
                success_metrics=["rate"],
                duration_days=7,
            ),
            ExperimentConfig(
                name="Active Exp",
                variant_ids=["variant_control"],
                traffic_allocation=[1.0],
                target_persona="persona_b",
                success_metrics=["rate"],
                duration_days=7,
            ),
            ExperimentConfig(
                name="Another Draft",
                variant_ids=["variant_control"],
                traffic_allocation=[1.0],
                target_persona="persona_a",
                success_metrics=["rate"],
                duration_days=7,
            ),
        ]

        experiment_ids = []
        for config in configs:
            exp_id = experiment_manager.create_experiment(config)
            experiment_ids.append(exp_id)

        # Start one experiment
        experiment_manager.start_experiment(experiment_ids[1])

        # Test listing all experiments
        all_experiments = experiment_manager.list_experiments()
        assert len(all_experiments) >= 3

        # Test filtering by status
        draft_experiments = experiment_manager.list_experiments(status="draft")
        active_experiments = experiment_manager.list_experiments(status="active")

        assert len(draft_experiments) >= 2
        assert len(active_experiments) >= 1

        # Test filtering by persona
        persona_a_experiments = experiment_manager.list_experiments(
            target_persona="persona_a"
        )
        assert len(persona_a_experiments) >= 2

    def test_get_active_experiments_for_persona(
        self, experiment_manager, sample_variants
    ):
        """Test getting active experiments for a specific persona."""
        # Create experiments for different personas
        persona_configs = [
            ExperimentConfig(
                name="Persona A Exp 1",
                variant_ids=["variant_control"],
                traffic_allocation=[1.0],
                target_persona="persona_a",
                success_metrics=["rate"],
                duration_days=7,
            ),
            ExperimentConfig(
                name="Persona A Exp 2",
                variant_ids=["variant_control"],
                traffic_allocation=[1.0],
                target_persona="persona_a",
                success_metrics=["rate"],
                duration_days=7,
            ),
            ExperimentConfig(
                name="Persona B Exp",
                variant_ids=["variant_control"],
                traffic_allocation=[1.0],
                target_persona="persona_b",
                success_metrics=["rate"],
                duration_days=7,
            ),
        ]

        experiment_ids = []
        for config in persona_configs:
            exp_id = experiment_manager.create_experiment(config)
            experiment_ids.append(exp_id)

        # Start persona A experiments
        experiment_manager.start_experiment(experiment_ids[0])
        experiment_manager.start_experiment(experiment_ids[1])

        # Get active experiments for persona A
        active_for_a = experiment_manager.get_active_experiments_for_persona(
            "persona_a"
        )
        active_for_b = experiment_manager.get_active_experiments_for_persona(
            "persona_b"
        )

        assert len(active_for_a) == 2
        assert len(active_for_b) == 0
        assert experiment_ids[0] in active_for_a
        assert experiment_ids[1] in active_for_a


class TestExperimentIntegration:
    """Test experiment system integration."""

    def test_end_to_end_experiment_workflow(self, experiment_manager, sample_variants):
        """Test complete end-to-end experiment workflow."""

        # 1. Create experiment
        config = ExperimentConfig(
            name="E2E Integration Test",
            description="Complete workflow test",
            variant_ids=[
                "variant_control",
                "variant_treatment_a",
                "variant_treatment_b",
            ],
            traffic_allocation=[0.5, 0.3, 0.2],  # 3-way split
            target_persona="e2e_test",
            success_metrics=["engagement_rate", "conversion_rate"],
            duration_days=14,
            control_variant_id="variant_control",
            min_sample_size=300,
            created_by="integration_test",
        )

        experiment_id = experiment_manager.create_experiment(config)
        assert experiment_id is not None

        # 2. Start experiment
        start_success = experiment_manager.start_experiment(experiment_id)
        assert start_success

        # 3. Assign participants and track engagement
        participants = [f"e2e_user_{i:03d}" for i in range(30)]

        for participant in participants:
            # Assign participant
            variant = experiment_manager.assign_participant_to_variant(
                experiment_id, participant
            )
            assert variant is not None

            # Track impression
            impression_success = experiment_manager.record_experiment_engagement(
                experiment_id, participant, variant, "impression", 1.0
            )
            assert impression_success

            # Simulate conversion for some participants (varying by variant)
            conversion_rates = {
                "variant_control": 0.1,
                "variant_treatment_a": 0.15,
                "variant_treatment_b": 0.08,
            }

            import random

            if random.random() < conversion_rates.get(variant, 0.1):
                conversion_success = experiment_manager.record_experiment_engagement(
                    experiment_id, participant, variant, "conversion", 2.0
                )
                assert conversion_success

        # 4. Get interim results
        interim_results = experiment_manager.get_experiment_results(experiment_id)
        assert interim_results is not None
        assert interim_results.total_participants == 30
        assert len(interim_results.variant_performance) == 3

        # 5. Complete experiment
        complete_success = experiment_manager.complete_experiment(experiment_id)
        assert complete_success

        # 6. Get final results
        final_results = experiment_manager.get_experiment_results(experiment_id)
        assert final_results.status == "completed"
        assert final_results.end_time is not None

        print("E2E Test Results:")
        print(f"  Participants: {final_results.total_participants}")
        print(f"  Winner: {final_results.winner_variant_id}")
        print(f"  Significant: {final_results.is_statistically_significant}")

        for variant_id, perf in final_results.variant_performance.items():
            print(
                f"  {variant_id}: {perf['participants']} participants, {perf['conversion_rate']:.1%} rate"
            )

    def test_experiment_error_recovery(self, experiment_manager, sample_variants):
        """Test error handling and recovery scenarios."""

        # Test starting non-existent experiment
        start_success = experiment_manager.start_experiment("nonexistent_exp")
        assert not start_success

        # Test assigning participant to non-existent experiment
        assignment = experiment_manager.assign_participant_to_variant(
            "nonexistent_exp", "test_user"
        )
        assert assignment is None

        # Test recording engagement for non-existent experiment
        engagement_success = experiment_manager.record_experiment_engagement(
            "nonexistent_exp", "test_user", "test_variant", "impression"
        )
        assert not engagement_success

        # Test getting results for non-existent experiment
        results = experiment_manager.get_experiment_results("nonexistent_exp")
        assert results is None

    def test_experiment_caching(self, experiment_manager, sample_variants):
        """Test experiment caching functionality."""
        config = ExperimentConfig(
            name="Cache Test",
            variant_ids=["variant_control"],
            traffic_allocation=[1.0],
            target_persona="cache_test",
            success_metrics=["rate"],
            duration_days=7,
        )

        experiment_id = experiment_manager.create_experiment(config)

        # First access should load from database
        exp1 = experiment_manager._get_experiment(experiment_id)
        assert exp1 is not None

        # Second access should use cache (same object)
        exp2 = experiment_manager._get_experiment(experiment_id)
        assert exp2 is not None
        assert exp1.experiment_id == exp2.experiment_id

        # Cache should be cleared after status change
        experiment_manager.start_experiment(experiment_id)
        exp3 = experiment_manager._get_experiment(experiment_id)
        assert exp3.status == "active"


class TestExperimentEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_variant_experiment(self, experiment_manager, sample_variants):
        """Test experiment with single variant (baseline measurement)."""
        config = ExperimentConfig(
            name="Single Variant Test",
            variant_ids=["variant_control"],
            traffic_allocation=[1.0],
            target_persona="single_test",
            success_metrics=["engagement"],
            duration_days=7,
        )

        experiment_id = experiment_manager.create_experiment(config)
        experiment_manager.start_experiment(experiment_id)

        # Assign participants - all should go to single variant
        for i in range(10):
            variant = experiment_manager.assign_participant_to_variant(
                experiment_id, f"single_user_{i}"
            )
            assert variant == "variant_control"

        # Results should handle single variant case
        results = experiment_manager.get_experiment_results(experiment_id)
        # With single variant, there's no winner determination (no comparison possible)
        # The system should return None for winner and improvement
        assert (
            results.winner_variant_id is None
            or results.winner_variant_id == "variant_control"
        )
        assert (
            results.improvement_percentage is None
            or results.improvement_percentage == 0
        )

        # Should have performance data for the single variant
        assert len(results.variant_performance) == 1
        assert "variant_control" in results.variant_performance

    def test_zero_traffic_allocation_edge_case(
        self, experiment_manager, sample_variants
    ):
        """Test edge case with very small traffic allocations."""
        config = ExperimentConfig(
            name="Edge Case Traffic",
            variant_ids=["variant_control", "variant_treatment_a"],
            traffic_allocation=[0.99, 0.01],  # 99% / 1% split
            target_persona="edge_test",
            success_metrics=["rate"],
            duration_days=7,
        )

        experiment_id = experiment_manager.create_experiment(config)
        experiment_manager.start_experiment(experiment_id)

        # With extreme allocation, most participants should go to control
        assignments = {}
        for i in range(100):
            variant = experiment_manager.assign_participant_to_variant(
                experiment_id, f"edge_user_{i}"
            )
            assignments[variant] = assignments.get(variant, 0) + 1

        # Control should get vast majority
        control_count = assignments.get("variant_control", 0)
        treatment_count = assignments.get("variant_treatment_a", 0)

        assert control_count > treatment_count
        assert control_count >= 90  # Should get at least 90 out of 100


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])
