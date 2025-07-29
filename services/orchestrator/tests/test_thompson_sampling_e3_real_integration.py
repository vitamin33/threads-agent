import pytest
import numpy as np
from pathlib import Path
import sys

# Add viral_engine to path for import
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from services.viral_engine.engagement_predictor import EngagementPredictor
from services.orchestrator.thompson_sampling import select_top_variants_with_e3_predictions


class TestThompsonSamplingRealE3Integration:
    """Test Thompson Sampling with real EngagementPredictor integration."""
    
    def test_integration_with_real_engagement_predictor(self):
        """Test that we can use the real EngagementPredictor with Thompson Sampling."""
        # Arrange
        predictor = EngagementPredictor()  # Real instance
        
        # Create variants with different content quality
        variants = [
            {
                "variant_id": "strong_hook",
                "dimensions": {"hook_style": "question", "emotion": "curiosity"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "Did you know that 90% of people don't realize this simple trick? Here's what happened when I tried it..."
            },
            {
                "variant_id": "weak_hook",
                "dimensions": {"hook_style": "statement", "emotion": "neutral"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "This is a post about something."
            },
            {
                "variant_id": "medium_hook",
                "dimensions": {"hook_style": "story", "emotion": "excitement"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "I discovered something interesting today that changed my perspective on productivity."
            }
        ]
        
        # Act
        selected = select_top_variants_with_e3_predictions(
            variants,
            predictor=predictor,
            top_k=2
        )
        
        # Assert
        assert len(selected) == 2
        assert all(isinstance(id, str) for id in selected)
        
        # Also verify we can get predictions
        for variant in variants:
            prediction = predictor.predict_engagement_rate(variant["sample_content"])
            assert "predicted_engagement_rate" in prediction
            assert 0 <= prediction["predicted_engagement_rate"] <= 1
    
    def test_performance_with_mixed_history_and_e3(self):
        """Test variants with mixed observed data and E3 predictions."""
        # Arrange
        predictor = EngagementPredictor()
        
        variants = [
            {
                "variant_id": "experienced_good",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 500, "successes": 50},  # 10% observed
                "sample_content": "What's your biggest challenge with productivity?"
            },
            {
                "variant_id": "experienced_bad", 
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 500, "successes": 10},  # 2% observed
                "sample_content": "Productivity is important."
            },
            {
                "variant_id": "new_high_quality",
                "dimensions": {"hook_style": "story"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "I used to struggle with focus until I discovered this one weird trick that tripled my output. Here's exactly what I did..."
            }
        ]
        
        # Act - Run multiple times to check selection patterns
        selections = []
        np.random.seed(42)
        
        for _ in range(50):
            selected = select_top_variants_with_e3_predictions(
                variants,
                predictor=predictor,
                top_k=1
            )
            selections.append(selected[0])
        
        # Assert
        # Count selections
        selection_counts = {
            variant["variant_id"]: selections.count(variant["variant_id"])
            for variant in variants
        }
        
        # With real E3, new high-quality content should get some selections
        # despite having no history
        assert selection_counts["new_high_quality"] > 0
        
        # Experienced good should still be selected most often
        assert selection_counts["experienced_good"] > selection_counts["experienced_bad"]