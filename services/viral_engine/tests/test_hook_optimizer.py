# services/viral_engine/tests/test_hook_optimizer.py
from __future__ import annotations

from unittest.mock import patch

import pytest

from services.viral_engine.hook_optimizer import ViralHookEngine


@pytest.fixture
def hook_engine():
    """Create ViralHookEngine instance for testing"""
    return ViralHookEngine()


@pytest.fixture
def sample_base_content():
    """Sample content for testing"""
    return "AI will transform the workplace"


class TestViralHookEngine:
    """Test suite for ViralHookEngine"""

    def test_initialization(self, hook_engine):
        """Test engine initializes correctly"""
        assert isinstance(hook_engine, ViralHookEngine)
        assert len(hook_engine.patterns) > 0
        assert "controversy" in hook_engine.patterns
        assert "curiosity_gap" in hook_engine.patterns

    def test_pattern_loading(self, hook_engine):
        """Test patterns are loaded correctly"""
        patterns = hook_engine.get_available_patterns()

        # Should have all 6 categories
        expected_categories = [
            "controversy",
            "curiosity_gap",
            "social_proof",
            "pattern_interrupt",
            "emotion_triggers",
            "story_hooks",
        ]

        for category in expected_categories:
            assert category in patterns
            assert patterns[category] > 0  # Should have patterns

    def test_get_pattern_categories(self, hook_engine):
        """Test getting pattern categories"""
        categories = hook_engine.get_pattern_categories()
        assert len(categories) == 6
        assert "controversy" in categories
        assert "curiosity_gap" in categories

    def test_time_context_detection(self, hook_engine):
        """Test time context detection"""
        with patch("services.viral_engine.hook_optimizer.datetime") as mock_datetime:
            # Test morning
            mock_datetime.now.return_value.hour = 9
            time_context = hook_engine._get_current_time_context()
            assert time_context == "morning"

            # Test lunch
            mock_datetime.now.return_value.hour = 12
            time_context = hook_engine._get_current_time_context()
            assert time_context == "lunch"

            # Test evening
            mock_datetime.now.return_value.hour = 19
            time_context = hook_engine._get_current_time_context()
            assert time_context == "evening"

    @pytest.mark.asyncio
    async def test_hook_optimization(self, hook_engine, sample_base_content):
        """Test basic hook optimization"""
        result = await hook_engine.optimize_hook(
            persona_id="ai-jesus", base_content=sample_base_content
        )

        # Verify result structure
        assert "original_hook" in result
        assert "optimized_hooks" in result
        assert "selected_pattern" in result
        assert "expected_engagement_rate" in result
        assert "optimization_reason" in result

        # Verify content
        assert result["original_hook"] == sample_base_content
        assert len(result["optimized_hooks"]) == 1
        assert result["expected_engagement_rate"] > 0

        optimized_hook = result["optimized_hooks"][0]
        assert "content" in optimized_hook
        assert "pattern" in optimized_hook
        assert "score" in optimized_hook

    @pytest.mark.asyncio
    async def test_variant_generation(self, hook_engine, sample_base_content):
        """Test generating multiple variants"""
        variants = await hook_engine.generate_variants(
            persona_id="ai-elon", base_content=sample_base_content, variant_count=3
        )

        assert len(variants) <= 3  # Should generate up to 3 variants

        for variant in variants:
            assert "variant_id" in variant
            assert "content" in variant
            assert "pattern" in variant
            assert "pattern_category" in variant
            assert "expected_er" in variant
            assert variant["original_content"] == sample_base_content

    @pytest.mark.asyncio
    async def test_persona_preferences(self, hook_engine, sample_base_content):
        """Test persona-specific preferences"""
        # ai-jesus should avoid controversy
        result_jesus = await hook_engine.optimize_hook(
            persona_id="ai-jesus", base_content=sample_base_content
        )

        # ai-elon should prefer bold patterns
        await hook_engine.optimize_hook(
            persona_id="ai-elon", base_content=sample_base_content
        )

        # Results should be different for different personas
        jesus_pattern = result_jesus["optimized_hooks"][0]["pattern_category"]

        # ai-jesus should not get controversy patterns
        assert jesus_pattern != "controversy"

    def test_template_filling(self, hook_engine):
        """Test pattern template filling"""
        sample_pattern = {
            "template": "Unpopular opinion: {statement}",
            "variables": ["statement"],
        }

        result = hook_engine._fill_pattern_template(
            pattern=sample_pattern, base_content="AI is overhyped", persona_id="ai-elon"
        )

        assert "Unpopular opinion: AI is overhyped" == result
        assert "{statement}" not in result

    @pytest.mark.asyncio
    async def test_caching(self, hook_engine, sample_base_content):
        """Test result caching"""
        # First call
        result1 = await hook_engine.optimize_hook(
            persona_id="ai-jesus", base_content=sample_base_content
        )

        # Second call with same parameters should use cache
        result2 = await hook_engine.optimize_hook(
            persona_id="ai-jesus", base_content=sample_base_content
        )

        # Results should be identical (from cache)
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_performance_analytics(self, hook_engine):
        """Test pattern performance analytics"""
        analytics = await hook_engine.get_pattern_performance(
            persona_id="ai-jesus", time_period_days=7
        )

        assert "persona_id" in analytics
        assert "top_performing_categories" in analytics
        assert "recommendation" in analytics
        assert analytics["persona_id"] == "ai-jesus"
        assert len(analytics["top_performing_categories"]) == 3

    def test_pattern_selection_with_time(self, hook_engine):
        """Test pattern selection considers time context"""
        # Morning patterns
        morning_patterns = hook_engine._select_optimal_patterns(
            persona_id="ai-jesus", posting_time="morning", variant_count=2
        )

        # Evening patterns
        evening_patterns = hook_engine._select_optimal_patterns(
            persona_id="ai-jesus", posting_time="evening", variant_count=2
        )

        assert len(morning_patterns) <= 2
        assert len(evening_patterns) <= 2

        # Should have selected patterns
        for category, pattern in morning_patterns:
            assert category in hook_engine.patterns
            assert "id" in pattern

    @pytest.mark.asyncio
    async def test_error_handling(self, hook_engine):
        """Test error handling for edge cases"""
        # Test with empty content
        result = await hook_engine.optimize_hook(
            persona_id="unknown-persona", base_content=""
        )

        # Should still return a result
        assert "original_hook" in result
        assert "optimized_hooks" in result


# Performance benchmarks
class TestPerformance:
    """Performance tests for ViralHookEngine"""

    @pytest.mark.asyncio
    async def test_optimization_speed(self, hook_engine, sample_base_content):
        """Test optimization completes within performance requirements (<100ms)"""
        import time

        start_time = time.time()
        await hook_engine.optimize_hook(
            persona_id="ai-jesus", base_content=sample_base_content
        )
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        # Should complete within 100ms requirement
        assert (
            duration_ms < 100
        ), f"Optimization took {duration_ms:.2f}ms, should be <100ms"

    @pytest.mark.asyncio
    async def test_variant_generation_speed(self, hook_engine, sample_base_content):
        """Test variant generation speed"""
        import time

        start_time = time.time()
        variants = await hook_engine.generate_variants(
            persona_id="ai-jesus", base_content=sample_base_content, variant_count=5
        )
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        # Should complete efficiently
        assert duration_ms < 200, f"Variant generation took {duration_ms:.2f}ms"
        assert len(variants) > 0
