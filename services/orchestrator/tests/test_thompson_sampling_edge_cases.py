"""Edge case tests for Thompson Sampling implementation."""

import numpy as np
from unittest.mock import Mock

from services.orchestrator.thompson_sampling import (
    select_top_variants,
    select_top_variants_with_exploration,
    select_top_variants_with_e3_predictions,
)


class TestThompsonSamplingEdgeCases:
    """Test edge cases not covered by existing tests."""

    def test_select_variants_empty_list_returns_empty(self):
        """Test that empty variant list returns empty result."""
        # Arrange
        variants = []

        # Act
        selected = select_top_variants(variants, top_k=10)

        # Assert
        assert selected == []

    def test_select_variants_fewer_than_top_k_returns_all(self):
        """Test that when variants < top_k, all variants are returned."""
        # Arrange
        variants = [
            {
                "variant_id": f"v_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 10, "successes": 5},
            }
            for i in range(3)
        ]

        # Act
        selected = select_top_variants(variants, top_k=10)

        # Assert
        assert len(selected) == 3
        assert set(selected) == {"v_0", "v_1", "v_2"}

    def test_select_variants_with_negative_successes_handles_gracefully(self):
        """Test handling of invalid data (negative successes)."""
        # Arrange
        variants = [
            {
                "variant_id": "invalid_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 100, "successes": -10},  # Invalid!
            },
            {
                "variant_id": "valid_variant",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 100, "successes": 50},
            },
        ]

        # Act - Should not crash
        selected = select_top_variants(variants, top_k=2)

        # Assert
        assert len(selected) == 2
        assert "valid_variant" in selected
        assert "invalid_variant" in selected

    def test_select_variants_with_more_successes_than_impressions(self):
        """Test handling of invalid data (successes > impressions)."""
        # Arrange
        variants = [
            {
                "variant_id": "impossible_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 50, "successes": 100},  # Impossible!
            }
        ]

        # Act - Should not crash, beta parameter would be negative
        selected = select_top_variants(variants, top_k=1)

        # Assert
        assert len(selected) == 1
        assert selected[0] == "impossible_variant"

    def test_select_variants_with_exploration_all_experienced(self):
        """Test exploration when all variants are experienced."""
        # Arrange
        variants = [
            {
                "variant_id": f"experienced_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 200, "successes": 100},
            }
            for i in range(20)
        ]

        # Act
        selected = select_top_variants_with_exploration(
            variants,
            top_k=10,
            min_impressions=100,
            exploration_ratio=0.3,  # Should still select from experienced
        )

        # Assert
        assert len(selected) == 10
        assert all("experienced_" in vid for vid in selected)

    def test_select_variants_with_exploration_all_new(self):
        """Test exploration when all variants are new."""
        # Arrange
        variants = [
            {
                "variant_id": f"new_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 5, "successes": 1},
            }
            for i in range(20)
        ]

        # Act
        selected = select_top_variants_with_exploration(
            variants,
            top_k=10,
            min_impressions=100,
            exploration_ratio=0.3,  # Should select all from new
        )

        # Assert
        assert len(selected) == 10
        assert all("new_" in vid for vid in selected)

    def test_select_variants_with_extreme_exploration_ratios(self):
        """Test with extreme exploration ratios (0.0 and 1.0)."""
        # Arrange
        variants = [
            {
                "variant_id": f"exp_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 200, "successes": 100},
            }
            for i in range(5)
        ]
        variants.extend(
            [
                {
                    "variant_id": f"new_{i}",
                    "dimensions": {"hook_style": "statement"},
                    "performance": {"impressions": 5, "successes": 1},
                }
                for i in range(5)
            ]
        )

        # Act - No exploration
        no_exploration = select_top_variants_with_exploration(
            variants, top_k=5, min_impressions=100, exploration_ratio=0.0
        )

        # Act - Full exploration
        full_exploration = select_top_variants_with_exploration(
            variants, top_k=5, min_impressions=100, exploration_ratio=1.0
        )

        # Assert
        # With no exploration, should prefer experienced
        exp_count = sum(1 for v in no_exploration if "exp_" in v)
        assert exp_count >= 3  # Most should be experienced

        # With full exploration, should have mix
        new_count = sum(1 for v in full_exploration if "new_" in v)
        assert new_count >= 2  # Should have some new variants

    def test_select_variants_with_identical_performance(self):
        """Test that variants with identical performance still get randomized selection."""
        # Arrange
        np.random.seed(42)
        variants = [
            {
                "variant_id": f"identical_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 100, "successes": 50},  # All same
            }
            for i in range(10)
        ]

        # Act - Run multiple times
        selections = []
        for _ in range(10):
            selected = select_top_variants(variants, top_k=3)
            selections.append(selected[0])  # First selection

        # Assert - Should see different first selections due to randomness
        unique_first = set(selections)
        assert len(unique_first) > 1  # Should not always pick same variant

    def test_e3_predictions_with_missing_sample_content(self):
        """Test E3 predictions when sample_content is missing."""
        # Arrange
        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate.return_value = {
            "predicted_engagement_rate": 0.05
        }

        variants = [
            {
                "variant_id": "no_content",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                # No sample_content field
            },
            {
                "variant_id": "empty_content",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "",  # Empty content
            },
        ]

        # Act
        selected = select_top_variants_with_e3_predictions(
            variants, predictor=mock_predictor, top_k=2
        )

        # Assert
        assert len(selected) == 2
        # Predictor should not be called for missing/empty content
        assert mock_predictor.predict_engagement_rate.call_count <= 0

    def test_e3_predictions_with_nan_values(self):
        """Test E3 predictions returning NaN values."""
        # Arrange
        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate.return_value = {
            "predicted_engagement_rate": float("nan")
        }

        variants = [
            {
                "variant_id": "test_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "test content",
            }
        ]

        # Act - Should not crash
        selected = select_top_variants_with_e3_predictions(
            variants, predictor=mock_predictor, top_k=1
        )

        # Assert
        assert len(selected) == 1

    def test_e3_predictions_with_out_of_range_values(self):
        """Test E3 predictions returning values outside [0,1] range."""
        # Arrange
        mock_predictor = Mock()

        # Return invalid predictions
        predictions = [
            {"predicted_engagement_rate": 1.5},  # Too high
            {"predicted_engagement_rate": -0.1},  # Negative
        ]
        mock_predictor.predict_engagement_rate.side_effect = predictions

        variants = [
            {
                "variant_id": "high_prediction",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "content 1",
            },
            {
                "variant_id": "negative_prediction",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "content 2",
            },
        ]

        # Act - Should handle gracefully
        selected = select_top_variants_with_e3_predictions(
            variants, predictor=mock_predictor, top_k=2
        )

        # Assert
        assert len(selected) == 2

    def test_thompson_sampling_numerical_stability(self):
        """Test numerical stability with extreme values."""
        # Arrange
        variants = [
            {
                "variant_id": "huge_numbers",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 1000000, "successes": 999999},
            },
            {
                "variant_id": "tiny_numbers",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 1, "successes": 0},
            },
            {
                "variant_id": "zero_impressions",
                "dimensions": {"hook_style": "story"},
                "performance": {"impressions": 0, "successes": 0},
            },
        ]

        # Act - Should not overflow or underflow
        selected = select_top_variants(variants, top_k=3)

        # Assert
        assert len(selected) == 3
        assert all(isinstance(v, str) for v in selected)

    def test_top_k_edge_cases(self):
        """Test edge cases for top_k parameter."""
        # Arrange
        variants = [
            {
                "variant_id": f"v_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 10, "successes": 5},
            }
            for i in range(5)
        ]

        # Test k=0
        selected = select_top_variants(variants, top_k=0)
        assert selected == []

        # Test k=1
        selected = select_top_variants(variants, top_k=1)
        assert len(selected) == 1

        # Test k > len(variants)
        selected = select_top_variants(variants, top_k=100)
        assert len(selected) == 5

    def test_exploration_ratio_boundary_conditions(self):
        """Test boundary conditions for exploration ratio."""
        # Arrange
        variants = [
            {
                "variant_id": f"v_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {
                    "impressions": 150 if i < 5 else 10,
                    "successes": 75 if i < 5 else 2,
                },
            }
            for i in range(10)
        ]

        # Test negative exploration ratio (should be treated as 0)
        selected = select_top_variants_with_exploration(
            variants, top_k=5, min_impressions=100, exploration_ratio=-0.5
        )
        assert len(selected) == 5

        # Test exploration ratio > 1 (should be treated as 1)
        selected = select_top_variants_with_exploration(
            variants, top_k=5, min_impressions=100, exploration_ratio=1.5
        )
        assert len(selected) == 5

    def test_cache_pollution_with_malformed_content(self):
        """Test that malformed content doesn't pollute the cache."""
        # Arrange
        mock_predictor = Mock()
        call_count = 0

        def side_effect(content):
            nonlocal call_count
            call_count += 1
            if "malformed" in content:
                raise ValueError("Malformed content")
            return {"predicted_engagement_rate": 0.05}

        mock_predictor.predict_engagement_rate.side_effect = side_effect

        variants = [
            {
                "variant_id": "good_variant",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "good content",
            },
            {
                "variant_id": "bad_variant",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "malformed content",
            },
        ]

        # Act - Run twice to test caching
        for _ in range(2):
            selected = select_top_variants_with_e3_predictions(
                variants, predictor=mock_predictor, top_k=2, use_cache=True
            )

        # Assert
        assert len(selected) == 2
        # Good content should be cached, bad content should not
        assert call_count >= 3  # Good content once, bad content twice
