from services.pattern_analyzer.service import PatternAnalyzerService


class TestPatternAnalyzerService:
    """Test the PatternAnalyzerService API."""

    def test_check_pattern_fatigue_returns_status_and_score(self) -> None:
        """Test that the service API returns both fatigue status and freshness score."""
        # Arrange
        service = PatternAnalyzerService()
        pattern = "Check out this amazing {topic}!"
        persona_id = "test_persona"

        # Act
        result = service.check_pattern_fatigue(pattern, persona_id)

        # Assert
        assert "is_fatigued" in result
        assert "freshness_score" in result
        assert "pattern" in result
        assert result["is_fatigued"] is False  # New pattern should not be fatigued
        assert result["freshness_score"] == 1.0  # New pattern should have max freshness
        assert result["pattern"] == pattern
