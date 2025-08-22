#!/usr/bin/env python3
"""
Judge Format Tests - Validate Judgment Parsing

Tests pairwise judge formatting, JSON parsing, and error handling.
"""

import pytest
import json
from evalsuite.judge.pairwise_judge import PairwiseJudge


def test_judgment_parsing_valid():
    """Test valid judgment parsing."""
    # Mock judge (no API calls)
    judge = PairwiseJudge("openai", "gpt-4o-mini")
    
    valid_judgment = '''
    {
        "winner": "A",
        "reasons": "Output A is clearer and more professional",
        "criteria_scores": {
            "clarity": 4,
            "relevance": 5,
            "tone": 4,
            "factuality": 5
        }
    }
    '''
    
    parsed = judge._parse_judgment(valid_judgment)
    
    assert parsed["winner"] == "A"
    assert "reasons" in parsed
    assert "criteria_scores" in parsed
    assert len(parsed["criteria_scores"]) == 4


def test_judgment_parsing_invalid():
    """Test invalid judgment handling."""
    judge = PairwiseJudge("openai", "gpt-4o-mini")
    
    invalid_judgment = "This is not valid JSON"
    
    parsed = judge._parse_judgment(invalid_judgment)
    
    # Should fail closed with tie
    assert parsed["winner"] == "tie"
    assert "criteria_scores" in parsed
    assert len(parsed["criteria_scores"]) == 4


def test_judgment_parsing_malformed():
    """Test malformed JSON handling."""
    judge = PairwiseJudge("openai", "gpt-4o-mini")
    
    malformed_judgment = '''
    {
        "winner": "invalid_value",
        "reasons": "Test"
    }
    '''
    
    parsed = judge._parse_judgment(malformed_judgment)
    
    # Should fail closed with tie for invalid winner
    assert parsed["winner"] == "tie"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])