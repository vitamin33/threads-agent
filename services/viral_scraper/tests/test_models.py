# services/viral_scraper/tests/test_models.py
"""
TDD Test: ViralPost data model with content, metrics, and metadata

This test will fail because the ViralPost model doesn't exist yet.
Following TDD principles: Red -> Green -> Refactor
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


def test_viral_post_model_creation():
    """Test that ViralPost model can be created with required fields"""
    # This will fail because ViralPost doesn't exist yet
    from services.viral_scraper.models import ViralPost

    post_data = {
        "content": "This is a viral post about AI!",
        "account_id": "test_account_123",
        "post_url": "https://threads.net/test/post/123",
        "timestamp": datetime.now(),
        "likes": 1000,
        "comments": 50,
        "shares": 200,
        "engagement_rate": 0.15,
        "performance_percentile": 99.5,
    }

    post = ViralPost(**post_data)

    assert post.content == "This is a viral post about AI!"
    assert post.account_id == "test_account_123"
    assert post.likes == 1000
    assert post.performance_percentile == 99.5


def test_viral_post_is_top_1_percent():
    """Test that ViralPost can identify if it's in top 1% performance tier"""
    from services.viral_scraper.models import ViralPost

    # Top 1% post (>99th percentile)
    top_post = ViralPost(
        content="Viral content",
        account_id="test",
        post_url="https://test.com",
        timestamp=datetime.now(),
        likes=5000,
        comments=200,
        shares=1000,
        engagement_rate=0.25,
        performance_percentile=99.5,
    )

    assert top_post.is_top_1_percent() is True

    # Regular post (not top 1%)
    regular_post = ViralPost(
        content="Regular content",
        account_id="test",
        post_url="https://test.com",
        timestamp=datetime.now(),
        likes=100,
        comments=5,
        shares=10,
        engagement_rate=0.05,
        performance_percentile=50.0,
    )

    assert regular_post.is_top_1_percent() is False


def test_viral_post_validation():
    """Test that ViralPost validates required fields"""
    from services.viral_scraper.models import ViralPost

    # Missing required fields should raise ValidationError
    with pytest.raises(ValidationError):
        ViralPost()

    # Negative engagement metrics should be invalid
    with pytest.raises(ValidationError):
        ViralPost(
            content="Test",
            account_id="test",
            post_url="https://test.com",
            timestamp=datetime.now(),
            likes=-100,  # Invalid negative value
            comments=5,
            shares=10,
            engagement_rate=0.05,
            performance_percentile=50.0,
        )
