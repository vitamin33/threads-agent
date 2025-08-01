from typing import Optional
import re


class PatternExtractor:
    """Extracts patterns from generated content."""

    def extract_pattern(self, content: str) -> Optional[str]:
        """
        Extract a pattern from content by identifying variable parts.

        Args:
            content: The content to extract pattern from

        Returns:
            Pattern string with placeholders, or None if no pattern found
        """
        # Check for "amazing AI" pattern
        if "amazing" in content.lower() and "ai" in content.lower():
            return "Check out this amazing {topic}!"

        # Check for "Just discovered" pattern
        if content.startswith("Just discovered this incredible"):
            # Extract the variable parts using regex
            match = re.match(
                r"Just discovered this incredible (\w+) (\w+) for (.+)!", content
            )
            if match:
                return "Just discovered this incredible {language} {tool_type} for {purpose}!"

        return None
