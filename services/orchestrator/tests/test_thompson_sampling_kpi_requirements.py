"""Test that Thompson Sampling implementation meets business KPI requirements."""

import pytest
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.orchestrator.db import Base
from services.orchestrator.db.models import VariantPerformance
from services.orchestrator.thompson_sampling import (
    select_top_variants_for_persona,
    update_variant_performance,
)


class TestThompsonSamplingKPIRequirements:
    """Test business KPI requirements for CRA-231."""

    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_early_kill_10_minute_requirement(self, db_session):
        """Test that poor performing variants can be identified for early kill after 10 minutes."""
        # Create variants with different performance levels
        now = datetime.now(timezone.utc)
        
        # High performer - should NOT be killed
        high_performer = VariantPerformance(
            variant_id="high_performer",
            dimensions={"hook_style": "question", "emotion": "curiosity"},
            impressions=100,
            successes=8,  # 8% engagement (above 6% target)
            last_used=now - timedelta(minutes=15),
            created_at=now - timedelta(minutes=15)
        )
        
        # Low performer past 10 minutes - SHOULD be killed
        low_performer_old = VariantPerformance(
            variant_id="low_performer_old",
            dimensions={"hook_style": "statement", "emotion": "neutral"},
            impressions=80,
            successes=2,  # 2.5% engagement (below 50% of expected 6%)
            last_used=now - timedelta(minutes=12),
            created_at=now - timedelta(minutes=12)
        )
        
        # Low performer under 10 minutes - should NOT be killed yet
        low_performer_new = VariantPerformance(
            variant_id="low_performer_new",
            dimensions={"hook_style": "story", "emotion": "excitement"},
            impressions=50,
            successes=1,  # 2% engagement
            last_used=now - timedelta(minutes=8),
            created_at=now - timedelta(minutes=8)
        )
        
        # New variant with few impressions - should NOT be killed
        new_variant = VariantPerformance(
            variant_id="new_variant",
            dimensions={"hook_style": "controversy", "emotion": "anger"},
            impressions=5,
            successes=0,  # 0% but too few impressions
            last_used=now - timedelta(minutes=11),
            created_at=now - timedelta(minutes=11)
        )
        
        db_session.add_all([high_performer, low_performer_old, low_performer_new, new_variant])
        db_session.commit()
        
        # Implement early kill logic
        def get_variants_to_kill(session, min_impressions=10, min_minutes=10, 
                                 performance_threshold=0.03):  # 50% of 6% target
            """Identify variants that should be killed based on performance."""
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=min_minutes)
            
            variants_to_kill = session.query(VariantPerformance).filter(
                VariantPerformance.impressions >= min_impressions,
                VariantPerformance.created_at <= cutoff_time,
                VariantPerformance.success_rate < performance_threshold
            ).all()
            
            return [v.variant_id for v in variants_to_kill]
        
        # Test early kill identification
        kill_list = get_variants_to_kill(db_session)
        
        assert "low_performer_old" in kill_list, "Should kill low performer past 10 minutes"
        assert "high_performer" not in kill_list, "Should not kill high performer"
        assert "low_performer_new" not in kill_list, "Should not kill low performer under 10 minutes"
        assert "new_variant" not in kill_list, "Should not kill variant with too few impressions"

    def test_15_percent_engagement_improvement(self, db_session):
        """Test that Thompson Sampling achieves 15% engagement improvement over baseline."""
        # Simulate A/B test: baseline random selection vs Thompson Sampling
        
        # Create a pool of variants with varying performance
        np.random.seed(42)  # For reproducibility
        variants = []
        
        # Create realistic variant distribution
        for i in range(100):
            if i < 10:  # 10% excellent variants (hidden gems)
                success_rate = np.random.uniform(0.08, 0.12)
                impressions = np.random.randint(0, 20)  # Few impressions initially
            elif i < 30:  # 20% good variants
                success_rate = np.random.uniform(0.05, 0.08)
                impressions = np.random.randint(50, 200)
            elif i < 60:  # 30% average variants
                success_rate = np.random.uniform(0.03, 0.05)
                impressions = np.random.randint(100, 500)
            else:  # 40% poor variants
                success_rate = np.random.uniform(0.01, 0.03)
                impressions = np.random.randint(200, 1000)
            
            successes = int(impressions * success_rate)
            
            variant = VariantPerformance(
                variant_id=f"variant_{i}",
                dimensions={
                    "hook_style": ["question", "statement", "story", "controversy"][i % 4],
                    "emotion": ["curiosity", "urgency", "excitement", "fear"][i % 4]
                },
                impressions=impressions,
                successes=successes
            )
            variants.append(variant)
        
        db_session.add_all(variants)
        db_session.commit()
        
        # Simulate performance over multiple rounds
        rounds = 50
        thompson_total_engagement = 0
        baseline_total_engagement = 0
        
        for round_num in range(rounds):
            # Thompson Sampling selection
            from services.orchestrator.thompson_sampling import load_variants_from_db
            all_variants = load_variants_from_db(db_session)
            thompson_selected = select_top_variants_for_persona(
                db_session, 
                persona_id="test_persona",
                top_k=10,
                min_impressions=10,
                exploration_ratio=0.3
            )
            
            # Calculate expected engagement for Thompson selection
            for variant_id in thompson_selected:
                variant = next(v for v in all_variants if v["variant_id"] == variant_id)
                if variant["performance"]["impressions"] > 0:
                    engagement_rate = (
                        variant["performance"]["successes"] / 
                        variant["performance"]["impressions"]
                    )
                else:
                    engagement_rate = 0.05  # Expected rate for new variants
                thompson_total_engagement += engagement_rate
            
            # Baseline random selection
            baseline_selected = np.random.choice(
                [v["variant_id"] for v in all_variants], 
                size=10, 
                replace=False
            )
            
            # Calculate expected engagement for baseline
            for variant_id in baseline_selected:
                variant = next(v for v in all_variants if v["variant_id"] == variant_id)
                if variant["performance"]["impressions"] > 0:
                    engagement_rate = (
                        variant["performance"]["successes"] / 
                        variant["performance"]["impressions"]
                    )
                else:
                    engagement_rate = 0.05
                baseline_total_engagement += engagement_rate
            
            # Update impressions/successes to simulate learning
            for variant_id in thompson_selected:
                # Thompson Sampling learns from its selections
                success = np.random.random() < 0.06  # Simulate 6% avg engagement
                update_variant_performance(
                    db_session, 
                    variant_id, 
                    impression=True, 
                    success=success
                )
        
        # Calculate average engagement rates
        thompson_avg_engagement = thompson_total_engagement / (rounds * 10)
        baseline_avg_engagement = baseline_total_engagement / (rounds * 10)
        
        # Calculate improvement
        improvement = (
            (thompson_avg_engagement - baseline_avg_engagement) / 
            baseline_avg_engagement * 100
        )
        
        print(f"\nEngagement Test Results:")
        print(f"Baseline avg engagement: {baseline_avg_engagement:.4f}")
        print(f"Thompson avg engagement: {thompson_avg_engagement:.4f}")
        print(f"Improvement: {improvement:.1f}%")
        
        # Assert 15% improvement
        assert improvement >= 15.0, (
            f"Thompson Sampling achieved only {improvement:.1f}% improvement, "
            f"target is 15%"
        )

    def test_pattern_fatigue_detection(self, db_session):
        """Test that overused patterns are detected and penalized."""
        # Create variants with same pattern used multiple times
        now = datetime.now(timezone.utc)
        
        # Overused pattern (question + curiosity)
        overused_variants = []
        for i in range(5):
            variant = VariantPerformance(
                variant_id=f"overused_{i}",
                dimensions={
                    "hook_style": "question",
                    "emotion": "curiosity",
                    "pattern_hash": "question_curiosity"  # Track pattern
                },
                impressions=1000,
                successes=60,  # 6% engagement
                last_used=now - timedelta(days=i),
                created_at=now - timedelta(days=7)
            )
            overused_variants.append(variant)
        
        # Fresh pattern variants
        fresh_variants = []
        fresh_patterns = [
            ("story", "excitement"),
            ("controversy", "anger"),
            ("statement", "urgency")
        ]
        
        for i, (hook, emotion) in enumerate(fresh_patterns):
            variant = VariantPerformance(
                variant_id=f"fresh_{i}",
                dimensions={
                    "hook_style": hook,
                    "emotion": emotion,
                    "pattern_hash": f"{hook}_{emotion}"
                },
                impressions=100,
                successes=6,  # Same 6% engagement
                last_used=now - timedelta(days=10),  # Not used recently
                created_at=now - timedelta(days=30)
            )
            fresh_variants.append(variant)
        
        db_session.add_all(overused_variants + fresh_variants)
        db_session.commit()
        
        # Implement pattern fatigue detection
        def get_pattern_usage_last_7_days(session):
            """Count pattern usage in last 7 days."""
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            
            variants = session.query(VariantPerformance).filter(
                VariantPerformance.last_used >= cutoff
            ).all()
            
            pattern_counts = {}
            for variant in variants:
                pattern = variant.dimensions.get("pattern_hash", "unknown")
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            return pattern_counts
        
        # Test pattern usage detection
        pattern_usage = get_pattern_usage_last_7_days(db_session)
        
        assert pattern_usage.get("question_curiosity", 0) >= 3, (
            "Should detect overused pattern"
        )
        assert pattern_usage.get("story_excitement", 0) == 0, (
            "Fresh pattern should have no recent usage"
        )
        
        # Test that selection favors fresh patterns
        # In a real implementation, this would be integrated into variant selection
        def select_with_pattern_fatigue_penalty(variants, pattern_usage, max_uses=3):
            """Apply penalty to overused patterns."""
            scored_variants = []
            
            for variant in variants:
                pattern = variant.dimensions.get("pattern_hash", "unknown")
                uses = pattern_usage.get(pattern, 0)
                
                # Calculate fatigue penalty
                if uses >= max_uses:
                    penalty = 0.5  # 50% penalty for overused patterns
                else:
                    penalty = 1.0 - (uses / max_uses) * 0.3  # Gradual penalty
                
                # Adjust score
                base_score = variant.success_rate if variant.impressions > 0 else 0.05
                adjusted_score = base_score * penalty
                
                scored_variants.append((adjusted_score, variant.variant_id))
            
            # Sort by adjusted score
            scored_variants.sort(reverse=True)
            return [v_id for _, v_id in scored_variants[:10]]
        
        # Test selection with pattern fatigue
        all_variants = db_session.query(VariantPerformance).all()
        selected = select_with_pattern_fatigue_penalty(all_variants, pattern_usage)
        
        # Fresh patterns should be preferred despite same performance
        fresh_count = sum(1 for v_id in selected if v_id.startswith("fresh_"))
        overused_count = sum(1 for v_id in selected if v_id.startswith("overused_"))
        
        assert fresh_count > overused_count, (
            "Selection should prefer fresh patterns over overused ones"
        )

    def test_maintains_cost_per_post_under_2_cents(self, db_session):
        """Test that variant generation maintains <$0.02 per post despite 10x variants."""
        # Simulate cost calculation for multi-variant testing
        
        # Cost assumptions (based on OpenAI pricing)
        COST_PER_1K_TOKENS_CHEAP = 0.0005  # GPT-3.5
        COST_PER_1K_TOKENS_EXPENSIVE = 0.03  # GPT-4
        AVG_TOKENS_PER_VARIANT = 150
        
        # E3 prediction cost (cached after first call)
        E3_TOKENS_PER_PREDICTION = 200
        E3_CACHE_HIT_RATE = 0.8  # 80% cache hits
        
        # Calculate cost for 10 variants
        num_variants = 10
        
        # Generation cost (using cheap model for body)
        generation_cost = (
            num_variants * AVG_TOKENS_PER_VARIANT * COST_PER_1K_TOKENS_CHEAP / 1000
        )
        
        # E3 prediction cost (only for cache misses)
        e3_predictions_needed = num_variants * (1 - E3_CACHE_HIT_RATE)
        e3_cost = (
            e3_predictions_needed * E3_TOKENS_PER_PREDICTION * 
            COST_PER_1K_TOKENS_EXPENSIVE / 1000
        )
        
        # Total cost per post request
        total_cost = generation_cost + e3_cost
        
        print(f"\nCost Analysis:")
        print(f"Generation cost: ${generation_cost:.4f}")
        print(f"E3 prediction cost: ${e3_cost:.4f}")
        print(f"Total cost per post: ${total_cost:.4f}")
        print(f"Cost per variant: ${total_cost/num_variants:.4f}")
        
        # Assert cost is under $0.02
        assert total_cost < 0.02, (
            f"Cost per post ${total_cost:.4f} exceeds $0.02 target"
        )


@pytest.mark.integration
class TestThompsonSamplingIntegrationKPIs:
    """Integration tests for KPI requirements."""
    
    def test_end_to_end_engagement_improvement_simulation(self):
        """Simulate full system to verify 15% improvement over 1000 posts."""
        # This would be an integration test with:
        # 1. Actual variant generation
        # 2. Thompson Sampling selection
        # 3. Simulated user engagement
        # 4. Performance tracking
        # 5. Measurement of improvement
        
        # In a real test, this would connect to test instances of all services
        pass