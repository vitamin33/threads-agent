"""Error handling and recovery tests for Thompson Sampling."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, IntegrityError

from services.orchestrator.db import Base
from services.orchestrator.db.models import VariantPerformance
from services.orchestrator.thompson_sampling import (
    select_top_variants,
    load_variants_from_db,
    update_variant_performance,
    select_top_variants_with_e3_predictions,
    select_top_variants_with_engagement_predictor,
)


class TestThompsonSamplingErrorRecovery:
    """Test error handling and recovery scenarios."""

    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_handle_corrupted_variant_data(self):
        """Test handling of corrupted variant data structures."""
        # Arrange - Various corrupted data scenarios
        corrupted_variants = [
            # Missing required fields
            {"variant_id": "missing_performance"},
            # Missing variant_id
            {"performance": {"impressions": 100, "successes": 50}},
            # Performance is None
            {"variant_id": "null_performance", "performance": None},
            # Performance missing impressions
            {"variant_id": "missing_impressions", "performance": {"successes": 10}},
            # Non-dict performance
            {"variant_id": "string_performance", "performance": "not a dict"},
            # Valid variant for comparison
            {
                "variant_id": "valid_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 100, "successes": 50},
            },
        ]

        # Act - Should handle gracefully
        with pytest.raises((KeyError, TypeError)):
            select_top_variants(corrupted_variants, top_k=5)

    def test_database_connection_failure(self, db_session):
        """Test handling of database connection failures."""
        # Arrange - Mock a failing database connection
        with patch.object(
            db_session,
            "query",
            side_effect=OperationalError("Connection failed", None, None),
        ):
            # Act & Assert
            with pytest.raises(OperationalError):
                load_variants_from_db(db_session)

    def test_database_integrity_error_on_update(self, db_session):
        """Test handling of database integrity errors during updates."""
        # Arrange - Create a variant
        variant = VariantPerformance(
            variant_id="test_variant",
            dimensions={"hook_style": "question"},
            impressions=100,
            successes=50,
        )
        db_session.add(variant)
        db_session.commit()

        # Mock integrity error on commit
        with patch.object(
            db_session,
            "commit",
            side_effect=IntegrityError("Constraint violation", None, None),
        ):
            # Act - Try to update
            update_variant_performance(
                db_session, variant_id="test_variant", impression=True, success=True
            )

            # The function should handle the error internally
            # Verify the variant wasn't updated
            db_session.rollback()
            updated_variant = (
                db_session.query(VariantPerformance)
                .filter_by(variant_id="test_variant")
                .first()
            )
            assert updated_variant.impressions == 100  # Unchanged

    def test_update_nonexistent_variant(self, db_session):
        """Test updating a variant that doesn't exist."""
        # Act - Update non-existent variant
        update_variant_performance(
            db_session, variant_id="nonexistent_variant", impression=True, success=True
        )

        # Assert - Should not create the variant or raise error
        variant = (
            db_session.query(VariantPerformance)
            .filter_by(variant_id="nonexistent_variant")
            .first()
        )
        assert variant is None

    def test_e3_predictor_timeout_recovery(self):
        """Test recovery when E3 predictor times out."""
        # Arrange
        mock_predictor = Mock()

        # Simulate timeout
        def timeout_side_effect(content):
            import time

            time.sleep(2)  # Simulate long delay
            return {"predicted_engagement_rate": 0.05}

        mock_predictor.predict_engagement_rate.side_effect = timeout_side_effect

        variants = [
            {
                "variant_id": "timeout_test",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "test content",
            }
        ]

        # Act - Should fallback to uniform prior
        with patch(
            "services.orchestrator.thompson_sampling._get_e3_prediction"
        ) as mock_get:
            mock_get.return_value = None  # Simulate timeout returning None
            selected = select_top_variants_with_e3_predictions(
                variants, predictor=mock_predictor, top_k=1
            )

        # Assert
        assert len(selected) == 1
        assert selected[0] == "timeout_test"

    def test_e3_predictor_invalid_response(self):
        """Test handling of invalid E3 predictor responses."""
        # Arrange
        mock_predictor = Mock()

        # Various invalid responses
        invalid_responses = [
            {},  # Missing key
            {"wrong_key": 0.05},  # Wrong key
            {"predicted_engagement_rate": "not a number"},  # Wrong type
            None,  # Null response
            {"predicted_engagement_rate": {"nested": "object"}},  # Nested object
        ]

        mock_predictor.predict_engagement_rate.side_effect = invalid_responses

        variants = [
            {
                "variant_id": f"invalid_response_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": f"content {i}",
            }
            for i in range(5)
        ]

        # Act - Should handle all invalid responses gracefully
        selected = select_top_variants_with_e3_predictions(
            variants, predictor=mock_predictor, top_k=5
        )

        # Assert
        assert len(selected) == 5

    def test_numpy_random_state_corruption(self):
        """Test recovery from numpy random state issues."""
        # Arrange
        variants = [
            {
                "variant_id": f"v_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 100, "successes": 50},
            }
            for i in range(10)
        ]

        # Corrupt numpy random state
        with patch("numpy.random.beta", side_effect=ValueError("Invalid parameters")):
            # Act & Assert - Should raise the numpy error
            with pytest.raises(ValueError):
                select_top_variants(variants, top_k=5)

    def test_json_serialization_error_in_dimensions(self, db_session):
        """Test handling of non-JSON-serializable dimensions."""

        # Arrange - Create variant with problematic dimensions
        class NonSerializable:
            def __init__(self):
                self.data = "test"

        # This would normally fail during database operations
        variant = VariantPerformance(
            variant_id="json_error_variant",
            dimensions={"hook_style": "question", "obj": NonSerializable()},
            impressions=100,
            successes=50,
        )

        # Act & Assert - Should fail when trying to save
        with pytest.raises(Exception):  # Could be various exceptions
            db_session.add(variant)
            db_session.commit()

    def test_select_variants_with_infinite_values(self):
        """Test handling of infinite values in performance data."""
        # Arrange
        variants = [
            {
                "variant_id": "infinite_impressions",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": float("inf"), "successes": 50},
            },
            {
                "variant_id": "infinite_successes",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 100, "successes": float("inf")},
            },
            {
                "variant_id": "normal_variant",
                "dimensions": {"hook_style": "story"},
                "performance": {"impressions": 100, "successes": 50},
            },
        ]

        # Act - Should handle infinity gracefully
        with pytest.raises(ValueError):  # Beta distribution can't handle inf
            select_top_variants(variants, top_k=3)

    def test_engagement_predictor_import_failure(self):
        """Test fallback when EngagementPredictor can't be imported."""
        # Arrange
        variants = [
            {
                "variant_id": "test_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 100, "successes": 50},
            }
        ]

        # Mock import failure
        with patch(
            "services.orchestrator.thompson_sampling.select_top_variants"
        ) as mock_select:
            mock_select.return_value = ["test_variant"]

            with patch(
                "builtins.__import__", side_effect=ImportError("Module not found")
            ):
                # Act
                result = select_top_variants_with_engagement_predictor(
                    variants, top_k=1
                )

                # Assert - Should fallback to regular selection
                assert result == ["test_variant"]

    def test_database_query_malformed_dimensions(self, db_session):
        """Test handling of malformed dimensions in database."""
        # Arrange - Insert variant with malformed dimensions
        db_session.execute(
            """
            INSERT INTO variant_performance (variant_id, dimensions, impressions, successes)
            VALUES ('malformed_variant', 'not valid json', 100, 50)
            """
        )
        db_session.commit()

        # Also add a valid variant
        valid_variant = VariantPerformance(
            variant_id="valid_variant",
            dimensions={"hook_style": "question"},
            impressions=100,
            successes=50,
        )
        db_session.add(valid_variant)
        db_session.commit()

        # Act - Try to load variants
        with pytest.raises(Exception):  # JSON decode error
            variants = load_variants_from_db(db_session)

    def test_recovery_from_partial_update_failure(self, db_session):
        """Test recovery when variant update partially fails."""
        # Arrange - Create variants
        for i in range(3):
            variant = VariantPerformance(
                variant_id=f"partial_fail_{i}",
                dimensions={"hook_style": "question"},
                impressions=100,
                successes=50,
            )
            db_session.add(variant)
        db_session.commit()

        update_count = 0

        def failing_commit():
            nonlocal update_count
            update_count += 1
            if update_count == 2:
                raise OperationalError("Database locked", None, None)
            # Otherwise, do nothing (simulate successful commit)

        # Mock commit to fail on second update
        with patch.object(db_session, "commit", side_effect=failing_commit):
            # Update multiple variants
            for i in range(3):
                try:
                    update_variant_performance(
                        db_session,
                        variant_id=f"partial_fail_{i}",
                        impression=True,
                        success=True,
                    )
                except:
                    pass  # Continue with other updates

        # Verify state after partial failure
        # First variant should be updated, second failed, third depends on implementation
        assert update_count >= 2  # At least two attempts were made

    def test_cache_overflow_handling(self):
        """Test handling when cache size limits are exceeded."""
        # Arrange
        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate.return_value = {
            "predicted_engagement_rate": 0.05
        }

        # Create many variants with unique content to overflow cache
        variants = [
            {
                "variant_id": f"cache_overflow_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": f"Unique content string {i} " * 100,  # Large content
            }
            for i in range(1000)  # Many variants
        ]

        # Act - Process all variants (should handle cache overflow)
        try:
            # Process in batches to stress cache
            for i in range(0, 1000, 100):
                batch = variants[i : i + 100]
                selected = select_top_variants_with_e3_predictions(
                    batch, predictor=mock_predictor, top_k=10, use_cache=True
                )
                assert len(selected) == 10
        except MemoryError:
            pytest.fail("Cache overflow not handled properly")

    def test_beta_distribution_edge_case_parameters(self):
        """Test beta distribution with edge case parameters."""
        # Arrange - Edge cases for beta distribution
        edge_case_variants = [
            # Alpha or beta = 0 (should be handled as 1)
            {
                "variant_id": "zero_alpha",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 1, "successes": 0},
            },
            # Very large values
            {
                "variant_id": "large_values",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 1000000, "successes": 999999},
            },
            # Both parameters very small
            {
                "variant_id": "tiny_params",
                "dimensions": {"hook_style": "story"},
                "performance": {"impressions": 1, "successes": 1},
            },
        ]

        # Act - Should handle all cases
        selected = select_top_variants(edge_case_variants, top_k=3)

        # Assert
        assert len(selected) == 3
        assert all(isinstance(v, str) for v in selected)
