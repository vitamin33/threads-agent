# services/viral_engine/viral_coefficient_calculator.py
from __future__ import annotations
from typing import List, Dict, Any, Optional


class ViralCoefficientCalculator:
    """Calculator for viral coefficient metrics using the formula: (Shares + Comments) / Views * 100"""

    def calculate_viral_coefficient(
        self, shares: float, comments: float, views: float
    ) -> float:
        """
        Calculate viral coefficient: (Shares + Comments) / Views * 100

        Args:
            shares: Number of shares (must be >= 0)
            comments: Number of comments (must be >= 0)
            views: Number of views (must be > 0)

        Returns:
            float: Viral coefficient as percentage

        Raises:
            ValueError: If any input is invalid
        """
        # Validate inputs
        if views <= 0:
            if views == 0:
                raise ValueError("Views cannot be zero")
            else:
                raise ValueError("Views cannot be negative")

        if shares < 0:
            raise ValueError("Shares cannot be negative")

        if comments < 0:
            raise ValueError("Comments cannot be negative")

        # Calculate viral coefficient
        viral_coefficient = (shares + comments) / views * 100

        # Track calculation for statistics
        self._calculation_history.append(viral_coefficient)

        return viral_coefficient

    def __init__(self) -> None:
        """Initialize calculator with tracking capabilities"""
        self._calculation_history: List[float] = []

    def batch_calculate_viral_coefficients(
        self, metrics_data: List[Dict[str, float]], skip_invalid: bool = False
    ) -> List[float]:
        """
        Calculate viral coefficients for batch of metrics data

        Args:
            metrics_data: List of dicts with 'shares', 'comments', 'views' keys
            skip_invalid: If True, skip invalid entries; if False, raise exception

        Returns:
            List[float]: List of viral coefficients

        Raises:
            ValueError: If any entry is invalid and skip_invalid=False
        """
        results = []

        for data in metrics_data:
            try:
                result = self.calculate_viral_coefficient(
                    shares=data["shares"],
                    comments=data["comments"],
                    views=data["views"],
                )
                results.append(result)
            except ValueError:
                if not skip_invalid:
                    raise
                # Skip this entry and continue
                continue

        return results

    def calculate_viral_coefficient_with_metadata(
        self,
        shares: float,
        comments: float,
        views: float,
        post_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate viral coefficient with metadata tracking for MLOps

        Args:
            shares: Number of shares
            comments: Number of comments
            views: Number of views
            post_id: Optional post identifier
            timestamp: Optional timestamp

        Returns:
            Dict containing viral_coefficient and metadata
        """
        viral_coefficient = self.calculate_viral_coefficient(shares, comments, views)

        return {
            "viral_coefficient": viral_coefficient,
            "metadata": {
                "post_id": post_id,
                "timestamp": timestamp,
                "shares": shares,
                "comments": comments,
                "views": views,
            },
        }

    def get_calculation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about calculations performed

        Returns:
            Dict with calculation statistics
        """
        if not self._calculation_history:
            return {
                "total_calculations": 0,
                "average_viral_coefficient": 0.0,
                "min_viral_coefficient": None,
                "max_viral_coefficient": None,
            }

        return {
            "total_calculations": len(self._calculation_history),
            "average_viral_coefficient": sum(self._calculation_history)
            / len(self._calculation_history),
            "min_viral_coefficient": min(self._calculation_history),
            "max_viral_coefficient": max(self._calculation_history),
        }

    def reset_calculation_stats(self) -> None:
        """
        Reset calculation statistics
        """
        self._calculation_history.clear()
