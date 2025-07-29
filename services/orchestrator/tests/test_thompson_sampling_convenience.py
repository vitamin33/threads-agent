from unittest.mock import patch, Mock

from services.orchestrator.thompson_sampling import (
    select_top_variants_with_engagement_predictor,
)
import services.orchestrator.thompson_sampling as ts_module


class TestThompsonSamplingConvenience:
    """Test the convenience function for Thompson Sampling with E3."""

    def setup_method(self):
        """Clear the E3 cache before each test."""
        ts_module._e3_cache.clear()

    def test_convenience_function_auto_imports_engagement_predictor(self):
        """Test that the convenience function automatically imports EngagementPredictor."""
        # Arrange
        variants = [
            {
                "variant_id": "test_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "Test content",
            }
        ]

        # Mock the EngagementPredictor import inside the function
        with patch(
            "services.viral_engine.engagement_predictor.EngagementPredictor"
        ) as mock_predictor_class:
            mock_instance = Mock()
            mock_instance.predict_engagement_rate.return_value = {
                "predicted_engagement_rate": 0.05
            }
            mock_predictor_class.return_value = mock_instance

            # Act
            selected = select_top_variants_with_engagement_predictor(variants, top_k=1)

            # Assert
            assert len(selected) == 1
            assert mock_predictor_class.called
            assert mock_instance.predict_engagement_rate.called

    def test_convenience_function_falls_back_on_import_error(self):
        """Test fallback to standard Thompson Sampling when E3 is not available."""
        # Arrange
        variants = [
            {
                "variant_id": "variant_1",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 100, "successes": 10},
            },
            {
                "variant_id": "variant_2",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 100, "successes": 5},
            },
        ]

        # Mock import failure
        with patch(
            "services.viral_engine.engagement_predictor.EngagementPredictor",
            side_effect=ImportError("Module not found"),
        ):
            # Act
            selected = select_top_variants_with_engagement_predictor(variants, top_k=1)

            # Assert - should still work
            assert len(selected) == 1
            assert selected[0] in ["variant_1", "variant_2"]

    def test_convenience_function_uses_provided_predictor_instance(self):
        """Test that we can provide our own predictor instance."""
        # Arrange
        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate.return_value = {
            "predicted_engagement_rate": 0.07
        }

        variants = [
            {
                "variant_id": "test_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "Test content",
            }
        ]

        # Act
        selected = select_top_variants_with_engagement_predictor(
            variants, top_k=1, predictor_instance=mock_predictor
        )

        # Assert
        assert len(selected) == 1
        # Check that the predictor was called with the content
        mock_predictor.predict_engagement_rate.assert_called_once_with("Test content")
