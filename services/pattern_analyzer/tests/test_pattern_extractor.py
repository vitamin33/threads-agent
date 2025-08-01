from services.pattern_analyzer.pattern_extractor import PatternExtractor


class TestPatternExtractor:
    """Test the PatternExtractor class."""

    def test_extract_simple_pattern_from_content(self) -> None:
        """Test extracting a simple pattern with placeholders from content."""
        # Arrange
        extractor = PatternExtractor()
        content = "Check out this amazing new AI tool!"

        # Act
        pattern = extractor.extract_pattern(content)

        # Assert
        assert pattern is not None
        assert "{" in pattern  # Should contain placeholders
        assert "}" in pattern

    def test_extract_pattern_identifies_variable_parts(self) -> None:
        """Test that the extractor correctly identifies variable parts in similar content."""
        # Arrange
        extractor = PatternExtractor()

        # Two similar posts with different topics
        content1 = "Just discovered this incredible Python library for data analysis!"
        content2 = (
            "Just discovered this incredible JavaScript framework for web development!"
        )

        # Act
        pattern1 = extractor.extract_pattern(content1)
        pattern2 = extractor.extract_pattern(content2)

        # Assert
        # Both should extract to the same pattern
        assert pattern1 == pattern2
        assert (
            pattern1
            == "Just discovered this incredible {language} {tool_type} for {purpose}!"
        )
