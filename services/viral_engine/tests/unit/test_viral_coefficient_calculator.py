# services/viral_engine/tests/unit/test_viral_coefficient_calculator.py
from __future__ import annotations

import pytest

from services.viral_engine.viral_coefficient_calculator import (
    ViralCoefficientCalculator,
)


@pytest.fixture
def calculator():
    """Create ViralCoefficientCalculator instance for testing"""
    return ViralCoefficientCalculator()


class TestViralCoefficientCalculator:
    """Test suite for ViralCoefficientCalculator"""

    def test_initialization(self, calculator):
        """Test calculator initializes correctly"""
        assert isinstance(calculator, ViralCoefficientCalculator)

    def test_calculate_viral_coefficient_basic_case(self, calculator):
        """Test basic viral coefficient calculation: (Shares + Comments) / Views * 100"""
        # Given: 10 shares, 20 comments, 1000 views
        # Expected: (10 + 20) / 1000 * 100 = 3.0
        result = calculator.calculate_viral_coefficient(
            shares=10, comments=20, views=1000
        )
        assert result == 3.0

    def test_calculate_viral_coefficient_zero_engagement(self, calculator):
        """Test viral coefficient with zero engagement"""
        # Given: 0 shares, 0 comments, 1000 views
        # Expected: (0 + 0) / 1000 * 100 = 0.0
        result = calculator.calculate_viral_coefficient(
            shares=0, comments=0, views=1000
        )
        assert result == 0.0

    def test_calculate_viral_coefficient_high_engagement(self, calculator):
        """Test viral coefficient with high engagement"""
        # Given: 50 shares, 100 comments, 1000 views
        # Expected: (50 + 100) / 1000 * 100 = 15.0
        result = calculator.calculate_viral_coefficient(
            shares=50, comments=100, views=1000
        )
        assert result == 15.0

    def test_calculate_viral_coefficient_zero_views_raises_exception(self, calculator):
        """Test that zero views raises ValueError"""
        with pytest.raises(ValueError, match="Views cannot be zero"):
            calculator.calculate_viral_coefficient(shares=10, comments=20, views=0)

    def test_calculate_viral_coefficient_negative_shares_raises_exception(
        self, calculator
    ):
        """Test that negative shares raises ValueError"""
        with pytest.raises(ValueError, match="Shares cannot be negative"):
            calculator.calculate_viral_coefficient(shares=-1, comments=20, views=1000)

    def test_calculate_viral_coefficient_negative_comments_raises_exception(
        self, calculator
    ):
        """Test that negative comments raises ValueError"""
        with pytest.raises(ValueError, match="Comments cannot be negative"):
            calculator.calculate_viral_coefficient(shares=10, comments=-1, views=1000)

    def test_calculate_viral_coefficient_negative_views_raises_exception(
        self, calculator
    ):
        """Test that negative views raises ValueError"""
        with pytest.raises(ValueError, match="Views cannot be negative"):
            calculator.calculate_viral_coefficient(shares=10, comments=20, views=-1)

    def test_calculate_viral_coefficient_accepts_floats(self, calculator):
        """Test that calculator accepts float inputs"""
        result = calculator.calculate_viral_coefficient(
            shares=10.5, comments=20.5, views=1000.0
        )
        assert result == 3.1

    def test_calculate_viral_coefficient_decimal_precision(self, calculator):
        """Test decimal precision handling"""
        # Given: 1 share, 2 comments, 333 views
        # Expected: (1 + 2) / 333 * 100 = 0.900900... ≈ 0.9009
        result = calculator.calculate_viral_coefficient(shares=1, comments=2, views=333)
        assert abs(result - 0.9009009009009009) < 0.0001

    def test_calculate_viral_coefficient_returns_float(self, calculator):
        """Test that result is always a float"""
        result = calculator.calculate_viral_coefficient(shares=1, comments=1, views=100)
        assert isinstance(result, float)
        assert result == 2.0

    def test_calculate_viral_coefficient_large_numbers(self, calculator):
        """Test with large numbers"""
        result = calculator.calculate_viral_coefficient(
            shares=10000, comments=20000, views=1000000
        )
        assert result == 3.0

    def test_calculate_viral_coefficient_small_numbers(self, calculator):
        """Test with small numbers"""
        result = calculator.calculate_viral_coefficient(shares=1, comments=1, views=10)
        assert result == 20.0

    def test_batch_calculate_viral_coefficients(self, calculator):
        """Test batch processing of viral coefficients"""
        metrics_data = [
            {"shares": 10, "comments": 20, "views": 1000},
            {"shares": 5, "comments": 15, "views": 500},
            {"shares": 0, "comments": 10, "views": 100},
        ]

        results = calculator.batch_calculate_viral_coefficients(metrics_data)

        assert len(results) == 3
        assert results[0] == 3.0  # (10 + 20) / 1000 * 100
        assert results[1] == 4.0  # (5 + 15) / 500 * 100
        assert results[2] == 10.0  # (0 + 10) / 100 * 100

    def test_batch_calculate_with_invalid_data_skips_invalid(self, calculator):
        """Test batch processing skips invalid entries"""
        metrics_data = [
            {"shares": 10, "comments": 20, "views": 1000},  # Valid
            {"shares": 5, "comments": 15, "views": 0},  # Invalid - zero views
            {"shares": 0, "comments": 10, "views": 100},  # Valid
        ]

        results = calculator.batch_calculate_viral_coefficients(
            metrics_data, skip_invalid=True
        )

        assert len(results) == 2  # Only valid entries
        assert results[0] == 3.0
        assert results[1] == 10.0

    def test_batch_calculate_with_invalid_data_raises_exception(self, calculator):
        """Test batch processing raises exception on invalid data when skip_invalid=False"""
        metrics_data = [
            {"shares": 10, "comments": 20, "views": 1000},  # Valid
            {"shares": 5, "comments": 15, "views": 0},  # Invalid - zero views
        ]

        with pytest.raises(ValueError, match="Views cannot be zero"):
            calculator.batch_calculate_viral_coefficients(
                metrics_data, skip_invalid=False
            )

    def test_calculate_with_metadata_tracking(self, calculator):
        """Test calculation with metadata for MLOps tracking"""
        result = calculator.calculate_viral_coefficient_with_metadata(
            shares=10,
            comments=20,
            views=1000,
            post_id="post_123",
            timestamp="2024-01-01T12:00:00Z",
        )

        assert "viral_coefficient" in result
        assert "metadata" in result
        assert result["viral_coefficient"] == 3.0
        assert result["metadata"]["post_id"] == "post_123"
        assert result["metadata"]["timestamp"] == "2024-01-01T12:00:00Z"
        assert result["metadata"]["shares"] == 10
        assert result["metadata"]["comments"] == 20
        assert result["metadata"]["views"] == 1000

    def test_get_calculation_stats(self, calculator):
        """Test calculation statistics tracking"""
        # Perform some calculations
        calculator.calculate_viral_coefficient(shares=10, comments=20, views=1000)
        calculator.calculate_viral_coefficient(shares=5, comments=15, views=500)

        stats = calculator.get_calculation_stats()

        assert "total_calculations" in stats
        assert "average_viral_coefficient" in stats
        assert "min_viral_coefficient" in stats
        assert "max_viral_coefficient" in stats
        assert stats["total_calculations"] == 2
        assert stats["average_viral_coefficient"] == 3.5  # (3.0 + 4.0) / 2
        assert stats["min_viral_coefficient"] == 3.0
        assert stats["max_viral_coefficient"] == 4.0

    def test_reset_calculation_stats(self, calculator):
        """Test resetting calculation statistics"""
        # Perform calculation
        calculator.calculate_viral_coefficient(shares=10, comments=20, views=1000)

        # Reset stats
        calculator.reset_calculation_stats()

        stats = calculator.get_calculation_stats()
        assert stats["total_calculations"] == 0
        assert stats["average_viral_coefficient"] == 0.0
        assert stats["min_viral_coefficient"] is None
        assert stats["max_viral_coefficient"] is None
