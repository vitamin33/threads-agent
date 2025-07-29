"""Test business value extraction functionality."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from services.achievement_collector.services.ai_analyzer import AIAnalyzer


class TestBusinessValueExtraction:
    """Test AI-powered business value extraction from PR descriptions."""

    @pytest.mark.asyncio
    async def test_extract_simple_dollar_amount(self):
        """Test extraction of a simple dollar amount from text."""
        # Arrange
        analyzer = AIAnalyzer()
        pr_description = "This optimization reduces cloud costs by $15,000 per year"
        
        # Act
        result = await analyzer.extract_business_value(pr_description)
        
        # Assert
        assert result is not None
        assert result["total_value"] == 15000
        assert result["currency"] == "USD"
        assert result["period"] == "yearly"
        assert result["type"] == "cost_savings"

    @pytest.mark.asyncio
    async def test_extract_time_saved_converts_to_dollars(self):
        """Test extraction of time saved and conversion to dollar value."""
        # Arrange
        analyzer = AIAnalyzer()
        pr_description = "This automation saves 200 developer hours annually"
        
        # Act
        result = await analyzer.extract_business_value(pr_description)
        
        # Assert
        assert result is not None
        assert result["total_value"] == 20000  # 200 hours * $100/hour
        assert result["currency"] == "USD"
        assert result["period"] == "yearly"
        assert result["type"] == "time_savings"
        assert result["breakdown"]["time_saved_hours"] == 200
        assert result["breakdown"]["hourly_rate"] == 100

    @pytest.mark.asyncio
    async def test_returns_none_when_no_business_value_found(self):
        """Test that None is returned when no business value is detected."""
        # Arrange
        analyzer = AIAnalyzer()
        pr_description = "Fixed typo in README"
        
        # Act
        result = await analyzer.extract_business_value(pr_description)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_business_value_with_ai(self):
        """Test business value extraction using GPT-4 API."""
        # Arrange
        analyzer = AIAnalyzer()
        analyzer.client = AsyncMock()
        
        # Mock GPT-4 response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "total_value": 50000,
            "currency": "USD",
            "period": "yearly",
            "type": "performance_improvement",
            "confidence": 0.85,
            "breakdown": {
                "infrastructure_savings": 30000,
                "productivity_gain": 20000
            },
            "extraction_method": "gpt-4",
            "raw_text": "50% reduction in query time, saving $50k annually"
        })
        analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        pr_description = "Optimized database queries reducing response time by 50%, estimated to save $50k annually in infrastructure costs"
        
        # Act
        result = await analyzer.extract_business_value(pr_description)
        
        # Assert
        assert result is not None
        assert result["total_value"] == 50000
        assert result["currency"] == "USD"
        assert result["type"] == "performance_improvement"
        assert result["confidence"] == 0.85
        assert analyzer.client.chat.completions.create.called

    @pytest.mark.asyncio
    async def test_falls_back_to_offline_on_api_error(self):
        """Test that extraction falls back to offline mode on API errors."""
        # Arrange
        analyzer = AIAnalyzer()
        analyzer.client = AsyncMock()
        analyzer.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        pr_description = "This optimization reduces cloud costs by $15,000 per year"
        
        # Act
        result = await analyzer.extract_business_value(pr_description)
        
        # Assert - should still work using offline extraction
        assert result is not None
        assert result["total_value"] == 15000
        assert result["type"] == "cost_savings"

    @pytest.mark.asyncio
    async def test_integration_with_achievement_model(self):
        """Test that business value can be extracted and stored in Achievement model."""
        # Arrange
        from services.achievement_collector.db.models import Achievement
        
        analyzer = AIAnalyzer()
        achievement = Achievement(
            title="Optimize database queries",
            description="Reduced query time by 50% saving $15,000 per year in infrastructure costs",
            category="performance",
            business_value=None  # Initially empty - String field
        )
        
        # Act
        business_value_data = await analyzer.extract_business_value(achievement.description)
        if business_value_data:
            # Store as JSON string in the business_value field
            achievement.business_value = json.dumps(business_value_data)
            # Also extract specific metrics for dedicated fields
            achievement.time_saved_hours = business_value_data.get("breakdown", {}).get("time_saved_hours", 0)
            if business_value_data.get("type") == "performance_improvement":
                achievement.performance_improvement_pct = 50.0  # From the description
        
        # Assert
        assert achievement.business_value is not None
        stored_value = json.loads(achievement.business_value)
        assert stored_value["total_value"] == 15000
        assert stored_value["type"] == "cost_savings"

    @pytest.mark.asyncio 
    async def test_extract_performance_improvement_value(self):
        """Test extraction of performance improvement business value."""
        # Arrange
        analyzer = AIAnalyzer()
        pr_description = "Optimized query performance by 75%, reducing response time from 4s to 1s"
        
        # Act
        result = await analyzer.extract_business_value(pr_description)
        
        # Assert
        assert result is not None
        # Should calculate some value based on performance improvement
        assert result["type"] == "performance_improvement"
        assert "75%" in str(result.get("raw_text", ""))


class TestBusinessValueUpdater:
    """Test updating existing achievements with business values."""
    
    @pytest.mark.asyncio
    async def test_update_achievement_with_business_value(self):
        """Test updating an achievement with extracted business value."""
        # Arrange
        from services.achievement_collector.db.models import Achievement
        
        analyzer = AIAnalyzer()
        achievement = Achievement(
            id=1,
            title="Database optimization",
            description="Improved query performance by 80%, saving $25,000 annually",
            category="performance",
            business_value=None,
            time_saved_hours=0,
            performance_improvement_pct=0
        )
        
        # Act
        updated = await analyzer.update_achievement_business_value(achievement)
        
        # Assert
        assert updated is True
        assert achievement.business_value is not None
        assert achievement.performance_improvement_pct == 80.0
        
        # Verify the stored JSON
        business_data = json.loads(achievement.business_value)
        assert business_data["total_value"] == 25000
        assert business_data["type"] == "cost_savings"

    @pytest.mark.asyncio
    async def test_batch_update_achievements(self):
        """Test batch updating multiple achievements with business values."""
        # Arrange
        from services.achievement_collector.db.models import Achievement
        
        analyzer = AIAnalyzer()
        achievements = [
            Achievement(
                id=1,
                title="API optimization",
                description="Reduced API response time by 60%",
                business_value=None
            ),
            Achievement(
                id=2,
                title="Bug fix",
                description="Fixed critical bug preventing user logins",
                business_value=None
            ),
            Achievement(
                id=3,
                title="Automation",
                description="Automated deployment process, saving 10 hours per week",
                business_value=None
            )
        ]
        
        # Act
        results = await analyzer.batch_update_business_values(achievements)
        
        # Assert
        assert results["updated"] == 3
        assert results["failed"] == 0
        assert achievements[0].business_value is not None
        assert achievements[2].business_value is not None
        
        # Check time savings calculation
        time_savings_data = json.loads(achievements[2].business_value)
        assert time_savings_data["type"] == "time_savings"
        # 10 hours/week * 52 weeks * $100/hour
        assert time_savings_data["total_value"] == 52000