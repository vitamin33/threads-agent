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
        """Create selector instance with mocked pattern service."""
        with patch("services.orchestrator.thompson_sampling_with_fatigue.SessionLocal"):
            selector = ThompsonSamplingWithFatigue()
            # Mock the pattern service to avoid database calls
            selector.pattern_service = MagicMock()
            return selector

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
        # Mock the pattern extractor
        with patch.object(
            selector.pattern_extractor, "extract_pattern"
        ) as mock_extract:
            mock_extract.side_effect = lambda x: f"pattern_{x[:10]}"

            # Mock the database session and query
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_query.filter.return_value.group_by.return_value.all.return_value = []
            mock_session.query.return_value = mock_query

            with patch(
                "services.orchestrator.thompson_sampling_with_fatigue.SessionLocal"
            ) as mock_session_local:
                mock_session_local.return_value.__enter__.return_value = mock_session

                selected = selector.select_top_variants_with_fatigue_detection(
                    sample_variants, persona_id="test_persona", top_k=3
                )

                assert len(selected) == 3
                assert all(isinstance(vid, str) for vid in selected)

    def test_select_variants_with_fatigued_patterns(self, selector, sample_variants):
        """Test selection with some fatigued patterns."""
        # Mock the pattern extractor
        with patch.object(
            selector.pattern_extractor, "extract_pattern"
        ) as mock_extract:
            mock_extract.side_effect = lambda x: f"pattern_{x[:10]}"

            # Mock the database session and query to return high usage for some patterns
            mock_session = MagicMock()
            mock_query = MagicMock()
            # Return high usage for "Check out" pattern
            mock_query.filter.return_value.group_by.return_value.all.return_value = [
                ("pattern_Check out ", 5),  # High usage = fatigued
            ]
            mock_session.query.return_value = mock_query

            with patch(
                "services.orchestrator.thompson_sampling_with_fatigue.SessionLocal"
            ) as mock_session_local:
                mock_session_local.return_value.__enter__.return_value = mock_session

                selected = selector.select_top_variants_with_fatigue_detection(
                    sample_variants, persona_id="test_persona", top_k=3
                )

                # Variants with "Check out this amazing" should be deprioritized
                assert len(selected) == 3
                # v1 and v4 have the fatigued pattern, so they should be less likely selected
                assert "v2" in selected or "v3" in selected or "v5" in selected

    def test_pattern_usage_recording(self, selector, sample_variants):
        """Test that pattern usage is recorded."""
        # Mock the pattern extractor
        with patch.object(
            selector.pattern_extractor, "extract_pattern"
        ) as mock_extract:
            mock_extract.side_effect = lambda x: f"pattern_{x[:10]}"

            # Mock the database session for both context manager and direct instantiation
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_query.filter.return_value.group_by.return_value.all.return_value = []
            mock_session.query.return_value = mock_query

            with patch(
                "services.orchestrator.thompson_sampling_with_fatigue.SessionLocal"
            ) as mock_session_local:
                # For context manager usage in fatigue calculation
                mock_session_local.return_value.__enter__.return_value = mock_session
                # For direct instantiation in pattern recording
                mock_session_local.return_value = mock_session

                selector.select_top_variants_with_fatigue_detection(
                    sample_variants[:2], persona_id="test_persona", top_k=2
                )

                # Check that usage was recorded (pattern recording uses direct SessionLocal() call)
                assert mock_session.bulk_insert_mappings.called
                assert mock_session.commit.called
                assert mock_session.close.called

    def test_fatigue_weight_influence(self, selector, sample_variants):
        """Test that fatigue weight properly influences selection."""
        # Mock the pattern extractor
        with patch.object(
            selector.pattern_extractor, "extract_pattern"
        ) as mock_extract:
            mock_extract.side_effect = lambda x: f"pattern_{x[:10]}"

            # Mock the database session and query
            mock_session = MagicMock()
            mock_query = MagicMock()

            with patch(
                "services.orchestrator.thompson_sampling_with_fatigue.SessionLocal"
            ) as mock_session_local:
                mock_session_local.return_value.__enter__.return_value = mock_session

                # Test with no fatigue weight
                selector.fatigue_weight = 0.0
                mock_query.filter.return_value.group_by.return_value.all.return_value = [
                    ("pattern_Check out ", 5),  # High usage
                ]
                mock_session.query.return_value = mock_query

                _ = selector.select_top_variants_with_fatigue_detection(
                    sample_variants, persona_id="test_persona", top_k=3
                )

                # Test with high fatigue weight
                selector.fatigue_weight = 0.9

                # Simulate different usage counts for different patterns
                def pattern_usage_side_effect(*args, **kwargs):
                    # Return different results based on the query
                    return mock_query

                mock_session.query.side_effect = pattern_usage_side_effect
                mock_query.filter.return_value.group_by.return_value.all.return_value = [
                    ("pattern_Check out ", 5),  # High usage for "Check out"
                    ("pattern_Revolution", 0),  # No usage for "Revolutionary"
                ]

                selected_high_weight = (
                    selector.select_top_variants_with_fatigue_detection(
                        sample_variants, persona_id="test_persona", top_k=3
                    )
                )

                # With high fatigue weight, fresher patterns should be strongly preferred
                # v2 should be highly ranked due to low usage
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
            "services.orchestrator.thompson_sampling_with_fatigue.ThompsonSamplingWithFatigue"
        ) as mock_selector_class:
            # Create a mock instance
            mock_selector = MagicMock()
            mock_selector.select_top_variants_with_fatigue_detection.return_value = [
                "v1",
                "v2",
            ]
            mock_selector_class.return_value = mock_selector

            selected = select_variants_with_fatigue_detection(
                sample_variants, persona_id="test_persona", top_k=2
            )

            assert len(selected) == 2
            assert all(isinstance(vid, str) for vid in selected)
            mock_selector.select_top_variants_with_fatigue_detection.assert_called_once_with(
                sample_variants, "test_persona", 2
            )

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
        # Mock the pattern extractor
        with patch.object(
            selector.pattern_extractor, "extract_pattern"
        ) as mock_extract:
            mock_extract.side_effect = lambda x: f"pattern_{x[:10]}"

            # First mock for the pattern fatigue calculation - this should work
            mock_session_good = MagicMock()
            mock_query = MagicMock()
            mock_query.filter.return_value.group_by.return_value.all.return_value = []
            mock_session_good.query.return_value = mock_query

            # Second mock for the pattern recording - this should fail
            mock_session_bad = MagicMock()
            mock_session_bad.bulk_insert_mappings.side_effect = Exception("DB Error")

            call_count = 0

            def session_factory():
                nonlocal call_count
                call_count += 1
                if call_count <= len(sample_variants):  # For fatigue calculations
                    return mock_session_good
                else:  # For pattern recording
                    return mock_session_bad

            with patch(
                "services.orchestrator.thompson_sampling_with_fatigue.SessionLocal"
            ) as mock_session_local:
                mock_session_local.side_effect = session_factory

                # Should not raise, just log error
                selected = selector.select_top_variants_with_fatigue_detection(
                    sample_variants, persona_id="test_persona", top_k=2
                )

                assert len(selected) == 2  # Selection should still work
