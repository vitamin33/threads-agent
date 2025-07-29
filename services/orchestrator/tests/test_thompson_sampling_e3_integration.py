import numpy as np
from unittest.mock import Mock

from services.orchestrator.thompson_sampling import (
    select_top_variants_with_e3_predictions,
)


class TestThompsonSamplingE3Integration:
    """Test Thompson Sampling integration with E3 Engagement Predictor."""

    def test_select_variants_with_e3_predictions_uses_predicted_engagement_as_prior(
        self,
    ):
        """Test that E3 predictions are used to create informed priors for new variants."""
        # Arrange
        mock_predictor = Mock()

        # Mock E3 predictions for different variants
        def mock_predict(post_content):
            if "high_quality" in post_content:
                return {"predicted_engagement_rate": 0.08}  # 8% predicted
            else:
                return {"predicted_engagement_rate": 0.02}  # 2% predicted

        mock_predictor.predict_engagement_rate.side_effect = mock_predict

        # Create variants with no performance history
        variants = [
            {
                "variant_id": "high_quality_variant",
                "dimensions": {"hook_style": "question", "emotion": "curiosity"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "high_quality hook that drives engagement",
            },
            {
                "variant_id": "low_quality_variant",
                "dimensions": {"hook_style": "statement", "emotion": "neutral"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "low quality basic statement",
            },
        ]

        # Add more variants for selection
        for i in range(8):
            variants.append(
                {
                    "variant_id": f"neutral_variant_{i}",
                    "dimensions": {"hook_style": "story", "emotion": "excitement"},
                    "performance": {"impressions": 0, "successes": 0},
                    "sample_content": "average quality content",
                }
            )

        # Act - Run selection multiple times to check probability
        selections = []
        np.random.seed(42)  # For reproducible tests

        for _ in range(100):
            selected = select_top_variants_with_e3_predictions(
                variants, predictor=mock_predictor, top_k=5
            )
            selections.extend(selected)

        # Assert
        high_quality_count = selections.count("high_quality_variant")
        low_quality_count = selections.count("low_quality_variant")

        # High quality variant (8% predicted) should be selected more often than low quality (2%)
        assert high_quality_count > low_quality_count
        # High quality should be selected significantly more
        assert high_quality_count > 55  # At least 11% of selections

    def test_e3_predictions_blend_with_observed_data(self):
        """Test that E3 predictions are blended with observed performance data."""
        # Arrange
        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate.return_value = {
            "predicted_engagement_rate": 0.02  # Low prediction
        }

        # Variant with good observed performance despite low E3 prediction
        variants = [
            {
                "variant_id": "good_observed",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 100, "successes": 80},  # 80% observed
                "sample_content": "actually good content",
            },
            {
                "variant_id": "no_history",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "new content",
            },
        ]

        # Act
        selected = select_top_variants_with_e3_predictions(
            variants, predictor=mock_predictor, top_k=1
        )

        # Assert - observed data should override low E3 prediction
        assert selected[0] == "good_observed"

    def test_e3_predictions_cached_to_avoid_repeated_calls(self):
        """Test that E3 predictions are cached for the same content."""
        # Arrange
        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate.return_value = {
            "predicted_engagement_rate": 0.05
        }

        variants = [
            {
                "variant_id": "test_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "test content",
            }
        ]

        # Act - Call multiple times
        for _ in range(3):
            select_top_variants_with_e3_predictions(
                variants, predictor=mock_predictor, top_k=1, use_cache=True
            )

        # Assert - Predictor should only be called once due to caching
        assert mock_predictor.predict_engagement_rate.call_count == 1

    def test_fallback_to_uniform_prior_when_e3_fails(self):
        """Test graceful fallback when E3 predictor fails."""
        # Arrange
        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate.side_effect = Exception("API Error")

        variants = [
            {
                "variant_id": "test_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "test content",
            }
        ]

        # Act & Assert - Should not raise exception
        selected = select_top_variants_with_e3_predictions(
            variants, predictor=mock_predictor, top_k=1
        )
        assert len(selected) == 1

    def test_e3_predictions_blend_gradually_with_more_data(self):
        """Test that E3 influence decreases as we get more observed data."""
        # Arrange
        mock_predictor = Mock()

        # E3 predicts low engagement for all
        mock_predictor.predict_engagement_rate.return_value = {
            "predicted_engagement_rate": 0.01  # 1% predicted
        }

        variants = [
            {
                "variant_id": "few_impressions",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 10, "successes": 6},  # 60% observed
                "sample_content": "content with few impressions",
            },
            {
                "variant_id": "many_impressions",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 1000, "successes": 600},  # 60% observed
                "sample_content": "content with many impressions",
            },
            {
                "variant_id": "no_impressions",
                "dimensions": {"hook_style": "story"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "new content",
            },
        ]

        # Act - Run multiple times
        selections = []
        np.random.seed(42)

        for _ in range(100):
            selected = select_top_variants_with_e3_predictions(
                variants, predictor=mock_predictor, top_k=1
            )
            selections.append(selected[0])

        # Assert
        few_count = selections.count("few_impressions")
        many_count = selections.count("many_impressions")
        no_count = selections.count("no_impressions")

        # Variant with many impressions should be selected most (least influenced by E3)
        assert many_count > few_count
        # Variant with no impressions should be selected least (most influenced by low E3)
        assert few_count > no_count
