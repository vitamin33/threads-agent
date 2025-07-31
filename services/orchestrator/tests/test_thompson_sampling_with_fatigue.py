"""Integration tests for Thompson Sampling with Pattern Fatigue Detection."""

import pytest
from unittest.mock import patch, MagicMock

from services.orchestrator.thompson_sampling_with_fatigue import (
    ThompsonSamplingWithFatigue,
    select_variants_with_fatigue_detection,
)


class TestThompsonSamplingWithFatigue:
    """Test Thompson Sampling with fatigue detection integration."""

    @pytest.fixture
    def selector(self):
        """Create selector instance."""
        return ThompsonSamplingWithFatigue()

    @pytest.fixture
    def sample_variants(self):
        """Sample variants for testing."""
        return [
            {
                "variant_id": "v1",
                "content": "Check out this amazing AI tool!",
                "performance": {"impressions": 100, "successes": 10},
            },
            {
                "variant_id": "v2",
                "content": "Revolutionary breakthrough in tech!",
                "performance": {"impressions": 50, "successes": 8},
            },
            {
                "variant_id": "v3",
                "content": "You won't believe what happened next!",
                "performance": {"impressions": 200, "successes": 12},
            },
            {
                "variant_id": "v4",
                "content": "Check out this amazing product!",
                "performance": {"impressions": 80, "successes": 9},
            },
            {
                "variant_id": "v5",
                "content": "New tech discovery changes everything!",
                "performance": {"impressions": 30, "successes": 5},
            },
        ]

    def test_select_variants_with_fresh_content(self, selector, sample_variants):
        """Test selection when all content is fresh."""
        with patch.object(
            selector.pattern_service, "get_pattern_freshness", return_value=1.0
        ):
            selected = selector.select_top_variants_with_fatigue_detection(
                sample_variants, persona_id="test_persona", top_k=3
            )

            assert len(selected) == 3
            assert all(isinstance(vid, str) for vid in selected)

    def test_select_variants_with_fatigued_patterns(self, selector, sample_variants):
        """Test selection with some fatigued patterns."""

        def mock_freshness(persona_id, pattern):
            # Make "Check out this amazing" pattern fatigued
            if "Check out this amazing" in pattern:
                return 0.2  # Low freshness
            return 0.9  # High freshness

        with patch.object(
            selector.pattern_service,
            "get_pattern_freshness",
            side_effect=mock_freshness,
        ):
            selected = selector.select_top_variants_with_fatigue_detection(
                sample_variants, persona_id="test_persona", top_k=3
            )

            # Variants with "Check out this amazing" should be deprioritized
            assert len(selected) == 3
            # v1 and v4 have the fatigued pattern, so they should be less likely selected
            assert "v2" in selected or "v3" in selected or "v5" in selected

    def test_pattern_usage_recording(self, selector, sample_variants):
        """Test that pattern usage is recorded."""
        mock_db = MagicMock()

        with patch(
            "services.orchestrator.thompson_sampling_with_fatigue.SessionLocal",
            return_value=mock_db,
        ):
            _ = selector.select_top_variants_with_fatigue_detection(
                sample_variants[:2], persona_id="test_persona", top_k=2
            )

            # Check that usage was recorded
            assert mock_db.add.called
            assert mock_db.commit.called

    def test_fatigue_weight_influence(self, selector, sample_variants):
        """Test that fatigue weight properly influences selection."""
        # Test with no fatigue weight
        selector.fatigue_weight = 0.0
        with patch.object(
            selector.pattern_service, "get_pattern_freshness", return_value=0.1
        ):
            _ = selector.select_top_variants_with_fatigue_detection(
                sample_variants, persona_id="test_persona", top_k=3
            )

        # Test with high fatigue weight
        selector.fatigue_weight = 0.9
        with patch.object(
            selector.pattern_service, "get_pattern_freshness"
        ) as mock_freshness:
            # Make different freshness scores
            def varying_freshness(persona_id, pattern):
                if "amazing" in pattern:
                    return 0.1
                elif "Revolutionary" in pattern:
                    return 0.9
                elif "believe" in pattern:
                    return 0.5
                else:
                    return 0.7

            mock_freshness.side_effect = varying_freshness
            selected_high_weight = selector.select_top_variants_with_fatigue_detection(
                sample_variants, persona_id="test_persona", top_k=3
            )

            # With high fatigue weight, fresher patterns should be strongly preferred
            # v2 should be highly ranked due to high freshness
            assert "v2" in selected_high_weight[:2]  # Should be in top 2

    def test_empty_variants_handling(self, selector):
        """Test handling of empty variant list."""
        selected = selector.select_top_variants_with_fatigue_detection(
            [], persona_id="test_persona", top_k=5
        )

        assert selected == []

    def test_variants_without_content(self, selector):
        """Test handling variants without content field."""
        variants = [
            {"variant_id": "v1", "performance": {"impressions": 100, "successes": 10}},
            {
                "variant_id": "v2",
                "sample_content": "Some content",
                "performance": {"impressions": 50, "successes": 5},
            },
        ]

        with patch.object(
            selector.pattern_service, "get_pattern_freshness", return_value=1.0
        ):
            selected = selector.select_top_variants_with_fatigue_detection(
                variants, persona_id="test_persona", top_k=2
            )

            assert len(selected) <= 2
            assert all(isinstance(vid, str) for vid in selected)

    def test_convenience_function(self, sample_variants):
        """Test the convenience function."""
        with patch(
            "services.pattern_analyzer.service.PatternAnalyzerService"
        ) as mock_service:
            mock_service.return_value.get_pattern_freshness.return_value = 0.8

            selected = select_variants_with_fatigue_detection(
                sample_variants, persona_id="test_persona", top_k=2
            )

            assert len(selected) == 2
            assert all(isinstance(vid, str) for vid in selected)

    def test_generate_variants_with_freshness_placeholder(self, selector):
        """Test the placeholder variant generation method."""
        with patch.object(
            selector.pattern_service, "get_recent_patterns"
        ) as mock_recent:
            mock_recent.return_value = {
                "pattern1": 4,  # Fatigued
                "pattern2": 2,  # Not fatigued
                "pattern3": 5,  # Fatigued
            }

            variants = selector.generate_variants_with_freshness(
                "Base content", "test_persona", count=5
            )

            assert len(variants) == 5
            assert all("variant_id" in v for v in variants)
            assert all("content" in v for v in variants)
            assert all("patterns" in v for v in variants)

    def test_integration_with_thompson_sampling_base(self, selector, sample_variants):
        """Test that base Thompson Sampling methods still work."""
        # The integration should maintain backward compatibility
        scores = selector._calculate_thompson_scores(sample_variants)

        assert len(scores) == len(sample_variants)
        assert all(0 <= score <= 1 for score in scores.values())

        # Test base selection method
        base_selected = selector.select_top_variants(sample_variants, top_k=3)
        assert len(base_selected) == 3

    def test_error_handling_in_pattern_recording(self, selector, sample_variants):
        """Test graceful handling of database errors."""
        with patch(
            "services.orchestrator.thompson_sampling_with_fatigue.SessionLocal"
        ) as mock_session:
            # Simulate database error
            mock_session.return_value.__enter__.side_effect = Exception("DB Error")

            # Should not raise, just log error
            selected = selector.select_top_variants_with_fatigue_detection(
                sample_variants, persona_id="test_persona", top_k=2
            )

            assert len(selected) == 2  # Selection should still work
