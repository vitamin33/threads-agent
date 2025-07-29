import pytest
from typing import List, Dict, Any
import random
import numpy as np

from services.orchestrator.thompson_sampling import select_top_variants


class TestThompsonSampling:
    """Test Thompson Sampling variant selection for A/B testing."""
    
    def test_select_variants_cold_start_returns_10_variants(self):
        """Test that we get exactly 10 variants when all have no history."""
        # Arrange
        variants = [
            {
                "variant_id": f"v_{i}",
                "dimensions": {
                    "hook_style": "question",
                    "emotion": "curiosity", 
                    "length": "short",
                    "cta": "learn_more"
                },
                "performance": {
                    "impressions": 0,
                    "successes": 0
                }
            }
            for i in range(20)  # Create 20 variants with no history
        ]
        
        # Act
        selected = select_top_variants(variants, top_k=10)
        
        # Assert
        assert len(selected) == 10
        assert all(isinstance(v, str) for v in selected)  # Should return variant IDs
        assert len(set(selected)) == 10  # All should be unique
    
    def test_select_variants_with_performance_history_uses_thompson_sampling(self):
        """Test that variants with better performance are more likely to be selected."""
        # Arrange
        np.random.seed(42)  # For reproducible tests
        random.seed(42)
        
        # Create variants with different performance levels
        variants = [
            # High performing variant (60% success rate)
            {
                "variant_id": "high_performer",
                "dimensions": {"hook_style": "question", "emotion": "curiosity", "length": "short", "cta": "learn_more"},
                "performance": {"impressions": 1000, "successes": 600}
            },
            # Low performing variant (10% success rate)
            {
                "variant_id": "low_performer",
                "dimensions": {"hook_style": "statement", "emotion": "urgency", "length": "long", "cta": "follow_now"},
                "performance": {"impressions": 1000, "successes": 100}
            }
        ]
        
        # Add more variants with no history
        for i in range(18):
            variants.append({
                "variant_id": f"no_history_{i}",
                "dimensions": {"hook_style": "story", "emotion": "excitement", "length": "medium", "cta": "share_thoughts"},
                "performance": {"impressions": 0, "successes": 0}
            })
        
        # Act - Run selection multiple times to check probability
        selections = []
        for _ in range(100):
            selected = select_top_variants(variants, top_k=10)
            selections.extend(selected)
        
        # Assert
        high_performer_count = selections.count("high_performer")
        low_performer_count = selections.count("low_performer")
        
        # High performer should be selected more often than low performer
        assert high_performer_count > low_performer_count
        # High performer should be selected most of the time (>70% in top 10)
        assert high_performer_count > 70
    
    def test_select_variants_handles_zero_impressions_gracefully(self):
        """Test that variants with zero impressions are handled correctly."""
        # Arrange
        variants = [
            {
                "variant_id": "zero_impressions",
                "dimensions": {"hook_style": "question", "emotion": "curiosity", "length": "short", "cta": "learn_more"},
                "performance": {"impressions": 0, "successes": 0}
            },
            {
                "variant_id": "has_impressions",
                "dimensions": {"hook_style": "statement", "emotion": "urgency", "length": "long", "cta": "follow_now"},
                "performance": {"impressions": 100, "successes": 10}
            }
        ]
        
        # Act & Assert - Should not raise any errors
        selected = select_top_variants(variants, top_k=2)
        assert len(selected) == 2
        assert "zero_impressions" in selected
        assert "has_impressions" in selected
    
    def test_select_variants_with_minimum_impressions_filter(self):
        """Test that we can filter variants by minimum impressions threshold."""
        # Arrange
        variants = [
            {
                "variant_id": "experienced_good",
                "dimensions": {"hook_style": "question", "emotion": "curiosity", "length": "short", "cta": "learn_more"},
                "performance": {"impressions": 200, "successes": 100}  # 50% success
            },
            {
                "variant_id": "experienced_bad", 
                "dimensions": {"hook_style": "statement", "emotion": "urgency", "length": "long", "cta": "follow_now"},
                "performance": {"impressions": 150, "successes": 15}  # 10% success
            },
            {
                "variant_id": "new_variant",
                "dimensions": {"hook_style": "story", "emotion": "excitement", "length": "medium", "cta": "share_thoughts"},
                "performance": {"impressions": 50, "successes": 25}  # 50% but not enough data
            }
        ]
        
        # Act
        from services.orchestrator.thompson_sampling import select_top_variants_with_exploration
        selected = select_top_variants_with_exploration(
            variants, 
            top_k=2,
            min_impressions=100,
            exploration_ratio=0.5  # 50% exploration
        )
        
        # Assert
        assert len(selected) == 2
        # Should include at least one experienced variant
        experienced_variants = ["experienced_good", "experienced_bad"]
        assert any(v in selected for v in experienced_variants)