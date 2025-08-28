"""
Tests for Thompson Sampling Visualization Service

Tests the comprehensive Thompson Sampling visualization including
Beta distributions, confidence intervals, and algorithm performance metrics.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.orchestrator.db.models import Base, VariantPerformance, Experiment, ExperimentVariant
from services.dashboard_api.thompson_sampling_visualizer import ThompsonSamplingVisualizer, create_thompson_sampling_visualizer


@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create database session for testing."""
    SessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def sample_variants(test_db_session):
    """Create sample variant data for testing."""
    variants = [
        VariantPerformance(
            variant_id="high_performer",
            dimensions={"hook_style": "question", "tone": "engaging"},
            impressions=1000,
            successes=150,  # 15% success rate
            last_used=datetime.now(timezone.utc),
        ),
        VariantPerformance(
            variant_id="medium_performer", 
            dimensions={"hook_style": "statement", "tone": "professional"},
            impressions=800,
            successes=80,   # 10% success rate
            last_used=datetime.now(timezone.utc),
        ),
        VariantPerformance(
            variant_id="low_performer",
            dimensions={"hook_style": "story", "tone": "casual"},
            impressions=500,
            successes=25,   # 5% success rate
            last_used=datetime.now(timezone.utc),
        ),
    ]

    for variant in variants:
        test_db_session.add(variant)
    test_db_session.commit()

    return variants


@pytest.fixture(scope="function")
def sample_experiments(test_db_session, sample_variants):
    """Create sample experiment data."""
    experiment = Experiment(
        experiment_id="test_exp_001",
        name="Test Experiment",
        variant_ids={"values": ["high_performer", "medium_performer"]},
        traffic_allocation={"values": [0.5, 0.5]},
        target_persona="test_persona",
        success_metrics={"values": ["engagement_rate"]},
        status="completed",
        duration_days=7,
        total_participants=500,
        winner_variant_id="high_performer",
        improvement_percentage=50.0,
        is_statistically_significant=True,
        p_value=0.001
    )
    
    test_db_session.add(experiment)
    
    # Add experiment variants
    exp_variants = [
        ExperimentVariant(
            experiment_id="test_exp_001",
            variant_id="high_performer",
            allocated_traffic=0.5,
            participants=250,
            impressions=250,
            conversions=37,
            conversion_rate=0.148
        ),
        ExperimentVariant(
            experiment_id="test_exp_001", 
            variant_id="medium_performer",
            allocated_traffic=0.5,
            participants=250,
            impressions=250,
            conversions=25,
            conversion_rate=0.10
        )
    ]
    
    for exp_variant in exp_variants:
        test_db_session.add(exp_variant)
    
    test_db_session.commit()
    return experiment


class TestThompsonSamplingVisualizer:
    """Test Thompson Sampling visualization functionality."""

    def test_create_visualizer(self, test_db_session):
        """Test visualizer creation."""
        visualizer = create_thompson_sampling_visualizer(test_db_session)
        assert visualizer is not None
        assert isinstance(visualizer, ThompsonSamplingVisualizer)

    @pytest.mark.asyncio
    async def test_get_algorithm_visualization_data(self, test_db_session, sample_variants):
        """Test getting comprehensive algorithm visualization data."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        data = await visualizer.get_algorithm_visualization_data()
        
        assert "algorithm_state" in data
        assert "beta_distributions" in data
        assert "confidence_intervals" in data
        assert "algorithm_metrics" in data
        
        # Check algorithm state
        assert data["algorithm_state"]["total_variants"] == 3
        assert data["algorithm_state"]["algorithm_type"] == "Thompson Sampling Multi-Armed Bandit"
        
        # Check Beta distributions
        assert len(data["beta_distributions"]) == 3
        for variant_id, dist_data in data["beta_distributions"].items():
            assert "curve_data" in dist_data
            assert "statistical_measures" in dist_data
            assert "sampling_weight" in dist_data
            assert "variant_info" in dist_data

    @pytest.mark.asyncio
    async def test_beta_distribution_calculations(self, test_db_session, sample_variants):
        """Test Beta distribution parameter calculations."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        variant_data = await visualizer._get_variant_beta_parameters()
        
        assert len(variant_data) == 3
        
        # Check high performer Beta parameters
        high_performer = next(v for v in variant_data if v["variant_id"] == "high_performer")
        assert high_performer["beta_parameters"]["alpha"] == 151  # 150 successes + 1
        assert high_performer["beta_parameters"]["beta"] == 851   # 850 failures + 1
        assert abs(high_performer["beta_parameters"]["mean"] - 0.15) < 0.01  # ~15% success rate

    @pytest.mark.asyncio
    async def test_confidence_intervals(self, test_db_session, sample_variants):
        """Test confidence interval calculations."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        variant_data = await visualizer._get_variant_beta_parameters()
        confidence_data = await visualizer._calculate_confidence_intervals(variant_data)
        
        assert len(confidence_data) == 3
        
        for variant_id, ci_data in confidence_data.items():
            assert "intervals" in ci_data
            assert "mean" in ci_data
            assert "uncertainty_score" in ci_data
            
            # Check 95% confidence interval exists
            if "95%" in ci_data["intervals"]:
                interval = ci_data["intervals"]["95%"]
                assert interval["lower"] >= 0
                assert interval["upper"] <= 1
                assert interval["lower"] < interval["upper"]

    @pytest.mark.asyncio
    async def test_sampling_demo(self, test_db_session, sample_variants):
        """Test real-time sampling demonstration."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        demo_data = await visualizer.get_real_time_sampling_demo()
        
        assert "sampling_demonstration" in demo_data
        assert "algorithm_explanation" in demo_data
        assert "mathematical_foundation" in demo_data
        assert "business_interpretation" in demo_data
        
        # Check sampling demonstration
        sampling_results = demo_data["sampling_demonstration"]
        assert len(sampling_results) == 5  # 5 rounds as configured
        
        for result in sampling_results:
            assert "selected_variant" in result
            assert "selection_value" in result
            assert "all_samples" in result
            assert len(result["all_samples"]) <= 4  # Top 4 variants

    @pytest.mark.asyncio
    async def test_algorithm_performance_metrics(self, test_db_session, sample_variants, sample_experiments):
        """Test algorithm performance metrics calculation."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        metrics = await visualizer._get_algorithm_performance_metrics()
        
        assert "experiment_performance" in metrics
        assert "exploration_exploitation" in metrics
        assert "performance_distribution" in metrics
        assert "algorithm_efficiency" in metrics
        
        # Check experiment performance
        exp_perf = metrics["experiment_performance"]
        assert exp_perf["total_experiments"] == 1
        assert exp_perf["statistically_significant"] == 1
        assert exp_perf["significance_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_statistical_significance_visualization(self, test_db_session, sample_experiments):
        """Test statistical significance visualization data."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        sig_data = await visualizer.get_statistical_significance_visualization()
        
        assert "experiments" in sig_data
        assert "statistical_summary" in sig_data
        assert "methodology" in sig_data
        
        # Check experiment data
        experiments = sig_data["experiments"]
        assert len(experiments) == 1
        
        exp = experiments[0]
        assert exp["experiment_id"] == "test_exp_001"
        assert exp["statistical_results"]["is_significant"] == True
        assert exp["statistical_results"]["p_value"] == 0.001

    @pytest.mark.asyncio
    async def test_algorithm_comparison(self, test_db_session, sample_variants):
        """Test algorithm comparison functionality."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        comparison = await visualizer._compare_algorithm_performance()
        
        assert "algorithm_rankings" in comparison
        assert "thompson_sampling_advantages" in comparison
        assert "performance_summary" in comparison
        
        # Thompson Sampling should be ranked first
        rankings = comparison["algorithm_rankings"]
        assert rankings[0][0] == "thompson_sampling"
        assert rankings[0][1]["performance_score"] == 95

    @pytest.mark.asyncio
    async def test_error_handling(self, test_db_session):
        """Test error handling in visualization service."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        # Test with no data
        data = await visualizer.get_algorithm_visualization_data()
        
        # Should handle gracefully with empty data
        assert isinstance(data, dict)
        # May have error key or empty data structures

    @pytest.mark.asyncio
    async def test_real_time_updates(self, test_db_session, sample_variants):
        """Test real-time data updates for visualizations."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        # Get initial data
        initial_data = await visualizer.get_algorithm_visualization_data()
        initial_variant_count = initial_data["algorithm_state"]["total_variants"]
        
        # Add new variant
        new_variant = VariantPerformance(
            variant_id="new_variant",
            dimensions={"hook_style": "urgent", "tone": "edgy"},
            impressions=100,
            successes=12,
            last_used=datetime.now(timezone.utc),
        )
        test_db_session.add(new_variant)
        test_db_session.commit()
        
        # Get updated data
        updated_data = await visualizer.get_algorithm_visualization_data()
        updated_variant_count = updated_data["algorithm_state"]["total_variants"]
        
        # Should reflect new variant
        assert updated_variant_count == initial_variant_count + 1
        assert "new_variant" in updated_data["beta_distributions"]


class TestVisualizationIntegration:
    """Test integration with existing dashboard infrastructure."""

    @pytest.mark.asyncio
    async def test_dashboard_api_integration(self, test_db_session, sample_variants):
        """Test integration with dashboard API endpoints."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        # Test all visualization endpoints
        viz_data = await visualizer.get_algorithm_visualization_data()
        demo_data = await visualizer.get_real_time_sampling_demo()
        sig_data = await visualizer.get_statistical_significance_visualization()
        
        # All should return valid data structures
        assert isinstance(viz_data, dict)
        assert isinstance(demo_data, dict)
        assert isinstance(sig_data, dict)
        
        # Check for required keys
        assert "algorithm_state" in viz_data
        assert "sampling_demonstration" in demo_data
        assert "methodology" in sig_data

    def test_visualization_data_format(self, test_db_session, sample_variants):
        """Test visualization data format compatibility with frontend."""
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        # Test data format matches frontend expectations
        # This test ensures the data structure matches React component interfaces
        
        # Run async function in sync test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            viz_data = loop.run_until_complete(visualizer.get_algorithm_visualization_data())
            
            # Check Beta distributions format
            if "beta_distributions" in viz_data:
                for variant_id, dist in viz_data["beta_distributions"].items():
                    # Should match BetaDistribution interface
                    assert "curve_data" in dist
                    assert "x_values" in dist["curve_data"]
                    assert "y_values" in dist["curve_data"]
                    assert "statistical_measures" in dist
                    assert "variant_info" in dist
                    
                    # Arrays should be same length
                    assert len(dist["curve_data"]["x_values"]) == len(dist["curve_data"]["y_values"])
        finally:
            loop.close()

    @pytest.mark.asyncio
    async def test_performance_optimization(self, test_db_session, sample_variants):
        """Test visualization performance with larger datasets."""
        # Add many variants to test performance
        for i in range(50):
            variant = VariantPerformance(
                variant_id=f"variant_{i:03d}",
                dimensions={"hook_style": "test", "tone": "test"},
                impressions=100 + i,
                successes=10 + i,
                last_used=datetime.now(timezone.utc),
            )
            test_db_session.add(variant)
        
        test_db_session.commit()
        
        visualizer = ThompsonSamplingVisualizer(test_db_session)
        
        # Test performance with large dataset
        start_time = datetime.now()
        data = await visualizer.get_algorithm_visualization_data()
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time
        assert execution_time < 5.0  # Less than 5 seconds
        assert len(data.get("beta_distributions", {})) == 53  # 3 original + 50 new


if __name__ == "__main__":
    pytest.main([__file__, "-v"])