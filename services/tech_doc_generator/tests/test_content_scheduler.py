"""
Tests for Content Scheduler

Tests the automated weekly content generation system that integrates
achievement_collector and viral_engine for AI job search content.
"""

import pytest
from datetime import datetime, timedelta, time
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.content_scheduler import (
    ContentScheduler,
    WeeklyContentPlan,
    ContentScheduleEntry,
    get_content_scheduler
)
from app.services.achievement_content_generator import Platform, ContentType
from app.services.professional_content_engine import ProfessionalContentResult


@pytest.fixture
def mock_achievement_data():
    """Sample achievement data for testing"""
    return [
        {
            "id": 1,
            "title": "Implemented Kubernetes Auto-scaling",
            "description": "Reduced infrastructure costs by 40%",
            "category": "infrastructure",
            "impact_score": 95.0,
            "business_value": "$50K annual savings",
            "skills_demonstrated": ["Kubernetes", "DevOps", "Cost Optimization"],
            "tags": ["kubernetes", "cost-optimization"],
            "portfolio_ready": True
        },
        {
            "id": 2,
            "title": "AI Content Generation Pipeline",
            "description": "Built automated content creation system",
            "category": "ai_ml",
            "impact_score": 92.0,
            "business_value": "15 hours/week time savings",
            "skills_demonstrated": ["Python", "OpenAI", "FastAPI"],
            "tags": ["ai", "automation"],
            "portfolio_ready": True
        },
        {
            "id": 3,
            "title": "Performance Monitoring Dashboard",
            "description": "Real-time system monitoring",
            "category": "monitoring",
            "impact_score": 88.0,
            "business_value": "99.9% uptime achieved",
            "skills_demonstrated": ["Prometheus", "Grafana", "Python"],
            "tags": ["monitoring", "dashboard"],
            "portfolio_ready": True
        }
    ]


@pytest.fixture
def mock_generated_content():
    """Sample generated content result"""
    return ProfessionalContentResult(
        title="How I Reduced Infrastructure Costs by 40% with Kubernetes Auto-scaling",
        content="## The Challenge\n\nOur infrastructure costs were spiraling...\n\n## The Solution\n\nImplemented Kubernetes auto-scaling...",
        hook="Here's how I reduced costs by 40% using Kubernetes...",
        engagement_score=85.5,
        quality_score=88.2,
        platform_optimized=Platform.LINKEDIN,
        recommended_hashtags=["#Kubernetes", "#DevOps", "#CostOptimization"],
        best_posting_time="Tuesday 10 AM",
        seo_keywords=["kubernetes", "auto-scaling", "infrastructure"]
    )


@pytest.mark.asyncio
class TestContentScheduler:
    """Test suite for ContentScheduler class"""
    
    def test_scheduler_initialization(self):
        """Test scheduler initializes with correct configuration"""
        scheduler = ContentScheduler()
        
        assert scheduler.achievement_client is not None
        assert scheduler.content_engine is not None
        assert len(scheduler.posting_schedule) == 3  # LinkedIn, Medium, Dev.to
        assert len(scheduler.content_rotation) == 3  # Monday, Wednesday, Friday
        assert len(scheduler.company_rotation) == 3  # 3-week rotation
    
    async def test_create_weekly_schedule(self, mock_achievement_data):
        """Test creating a weekly content schedule"""
        scheduler = ContentScheduler()
        
        # Mock the achievement client calls
        with patch.object(scheduler.achievement_client, '__aenter__', return_value=scheduler.achievement_client):
            with patch.object(scheduler.achievement_client, '__aexit__', return_value=None):
                with patch.object(scheduler.achievement_client, 'get_recent_highlights') as mock_recent:
                    with patch.object(scheduler.achievement_client, 'get_company_targeted') as mock_targeted:
                        
                        # Setup mocks to return achievement objects
                        from app.clients.achievement_client import Achievement
                        mock_achievements = [Achievement(**data) for data in mock_achievement_data]
                        
                        mock_recent.return_value = mock_achievements
                        mock_targeted.return_value = mock_achievements[:1]  # Return 1 per company
                        
                        # Create schedule
                        plan = await scheduler.create_weekly_schedule(
                            target_companies=["anthropic", "notion"]
                        )
                        
                        assert isinstance(plan, WeeklyContentPlan)
                        assert plan.target_posts == 3
                        assert len(plan.scheduled_entries) == 3
                        assert "anthropic" in plan.target_companies
                        assert "notion" in plan.target_companies
                        
                        # Check entries have correct structure
                        for entry in plan.scheduled_entries:
                            assert isinstance(entry, ContentScheduleEntry)
                            assert entry.achievement_id in [1, 2, 3]
                            assert entry.platform in [Platform.LINKEDIN, Platform.MEDIUM, Platform.DEVTO]
                            assert entry.content_type in [ContentType.CASE_STUDY, ContentType.TECHNICAL_BLOG, ContentType.LINKEDIN_POST]
                            assert entry.status == "scheduled"
    
    async def test_generate_scheduled_content(self, mock_achievement_data, mock_generated_content):
        """Test generating content for a scheduled entry"""
        scheduler = ContentScheduler()
        
        # Create a test entry
        entry = ContentScheduleEntry(
            id="20250811_monday_linkedin",
            achievement_id=1,
            content_type=ContentType.CASE_STUDY,
            platform=Platform.LINKEDIN,
            target_company="anthropic",
            scheduled_time=datetime.now() + timedelta(hours=1)
        )
        
        # Mock the dependencies
        with patch.object(scheduler.achievement_client, '__aenter__', return_value=scheduler.achievement_client):
            with patch.object(scheduler.achievement_client, '__aexit__', return_value=None):
                with patch.object(scheduler.achievement_client, 'get_achievement') as mock_get_achievement:
                    with patch.object(scheduler.content_engine, '__aenter__', return_value=scheduler.content_engine):
                        with patch.object(scheduler.content_engine, '__aexit__', return_value=None):
                            with patch.object(scheduler.content_engine, 'generate_professional_content') as mock_generate:
                                
                                from app.clients.achievement_client import Achievement
                                mock_get_achievement.return_value = Achievement(**mock_achievement_data[0])
                                mock_generate.return_value = mock_generated_content
                                
                                # Generate content
                                success = await scheduler.generate_scheduled_content(entry)
                                
                                assert success is True
                                assert entry.status == "generated"
                                assert entry.generated_content is not None
                                assert entry.generated_content.engagement_score == 85.5
                                assert entry.generated_content.quality_score == 88.2
    
    async def test_generate_content_quality_gate(self, mock_achievement_data):
        """Test content generation with quality gate (low scores)"""
        scheduler = ContentScheduler()
        
        entry = ContentScheduleEntry(
            id="test_entry",
            achievement_id=1,
            content_type=ContentType.CASE_STUDY,
            platform=Platform.LINKEDIN,
            scheduled_time=datetime.now()
        )
        
        # Mock low-quality content result
        low_quality_content = ProfessionalContentResult(
            title="Test Title",
            content="Test content",
            engagement_score=45.0,  # Below 60 threshold
            quality_score=55.0,     # Below 70 threshold
            platform_optimized=Platform.LINKEDIN,
            recommended_hashtags=[],
            seo_keywords=[]
        )
        
        with patch.object(scheduler.achievement_client, '__aenter__', return_value=scheduler.achievement_client):
            with patch.object(scheduler.achievement_client, '__aexit__', return_value=None):
                with patch.object(scheduler.achievement_client, 'get_achievement') as mock_get_achievement:
                    with patch.object(scheduler.content_engine, '__aenter__', return_value=scheduler.content_engine):
                        with patch.object(scheduler.content_engine, '__aexit__', return_value=None):
                            with patch.object(scheduler.content_engine, 'generate_professional_content') as mock_generate:
                                
                                from app.clients.achievement_client import Achievement
                                mock_get_achievement.return_value = Achievement(**mock_achievement_data[0])
                                mock_generate.return_value = low_quality_content
                                
                                success = await scheduler.generate_scheduled_content(entry)
                                
                                # Should still succeed but log warning about quality
                                assert success is True
                                assert entry.generated_content.engagement_score == 45.0
                                assert entry.generated_content.quality_score == 55.0
    
    async def test_process_weekly_schedule(self, mock_achievement_data, mock_generated_content):
        """Test processing a complete weekly schedule"""
        scheduler = ContentScheduler()
        
        # Create a test plan with entries
        plan = WeeklyContentPlan(
            week_start=datetime.now(),
            scheduled_entries=[
                ContentScheduleEntry(
                    id="entry_1",
                    achievement_id=1,
                    content_type=ContentType.CASE_STUDY,
                    platform=Platform.LINKEDIN,
                    scheduled_time=datetime.now() - timedelta(hours=1)  # Due now
                ),
                ContentScheduleEntry(
                    id="entry_2",
                    achievement_id=2,
                    content_type=ContentType.TECHNICAL_BLOG,
                    platform=Platform.MEDIUM,
                    scheduled_time=datetime.now() + timedelta(hours=2)  # Future
                )
            ]
        )
        
        plan_id = "test_plan"
        scheduler.active_schedules[plan_id] = plan
        
        # Mock content generation
        with patch.object(scheduler, 'generate_scheduled_content') as mock_generate:
            mock_generate.return_value = True
            
            results = await scheduler.process_weekly_schedule(plan_id)
            
            assert results["processed"] == 2
            assert results["successful"] == 1  # Only 1 due entry processed
            assert results["failed"] == 0
            assert len(results["entries"]) == 1  # Only due entry in results
    
    async def test_get_upcoming_content(self):
        """Test getting upcoming content entries"""
        scheduler = ContentScheduler()
        
        # Create test entries
        now = datetime.now()
        entries = [
            ContentScheduleEntry(
                id="upcoming_1",
                achievement_id=1,
                content_type=ContentType.CASE_STUDY,
                platform=Platform.LINKEDIN,
                scheduled_time=now + timedelta(hours=2)
            ),
            ContentScheduleEntry(
                id="upcoming_2", 
                achievement_id=2,
                content_type=ContentType.LINKEDIN_POST,
                platform=Platform.LINKEDIN,
                scheduled_time=now + timedelta(days=2)
            ),
            ContentScheduleEntry(
                id="too_far",
                achievement_id=3,
                content_type=ContentType.TECHNICAL_BLOG,
                platform=Platform.MEDIUM,
                scheduled_time=now + timedelta(days=10)  # Beyond 7-day window
            )
        ]
        
        plan = WeeklyContentPlan(week_start=now, scheduled_entries=entries)
        scheduler.active_schedules["test"] = plan
        
        upcoming = await scheduler.get_upcoming_content(days=7)
        
        assert len(upcoming) == 2  # Only entries within 7 days
        assert upcoming[0].scheduled_time < upcoming[1].scheduled_time  # Sorted by time
    
    async def test_content_performance_summary(self, mock_generated_content):
        """Test getting content performance analytics"""
        scheduler = ContentScheduler()
        
        # Create entries with generated content
        entries = [
            ContentScheduleEntry(
                id="perf_1",
                achievement_id=1,
                content_type=ContentType.CASE_STUDY,
                platform=Platform.LINKEDIN,
                target_company="anthropic",
                scheduled_time=datetime.now(),
                generated_content=mock_generated_content
            ),
            ContentScheduleEntry(
                id="perf_2",
                achievement_id=2,
                content_type=ContentType.TECHNICAL_BLOG,
                platform=Platform.MEDIUM,
                target_company="notion",
                scheduled_time=datetime.now(),
                generated_content=ProfessionalContentResult(
                    title="Test",
                    content="Test content",
                    engagement_score=75.0,
                    quality_score=80.0,
                    platform_optimized=Platform.MEDIUM,
                    recommended_hashtags=[],
                    seo_keywords=[]
                )
            )
        ]
        
        plan = WeeklyContentPlan(week_start=datetime.now(), scheduled_entries=entries)
        scheduler.active_schedules["test"] = plan
        
        summary = await scheduler.get_content_performance_summary()
        
        assert summary["total_generated"] == 2
        assert summary["avg_engagement_score"] == (85.5 + 75.0) / 2
        assert summary["avg_quality_score"] == (88.2 + 80.0) / 2
        assert "linkedin" in summary["platform_breakdown"]
        assert "medium" in summary["platform_breakdown"]
        assert "anthropic" in summary["company_performance"]
        assert "notion" in summary["company_performance"]
    
    def test_get_next_monday(self):
        """Test getting next Monday calculation"""
        scheduler = ContentScheduler()
        
        next_monday = scheduler._get_next_monday()
        
        assert next_monday.weekday() == 0  # Monday
        assert next_monday.time() == time(0, 0)
        assert next_monday.date() > datetime.now().date()
    
    def test_singleton_pattern(self):
        """Test that get_content_scheduler returns singleton"""
        scheduler1 = get_content_scheduler()
        scheduler2 = get_content_scheduler()
        
        assert scheduler1 is scheduler2


@pytest.mark.asyncio 
class TestContentSchedulerIntegration:
    """Integration tests with actual achievement data"""
    
    @pytest.mark.skip(reason="Requires running achievement_collector service")
    async def test_real_achievement_integration(self):
        """Test with real achievement_collector service"""
        scheduler = ContentScheduler()
        
        # This would test actual integration with running services
        plan = await scheduler.create_weekly_schedule(
            target_companies=["anthropic"]
        )
        
        assert len(plan.scheduled_entries) > 0
    
    @pytest.mark.skip(reason="Requires running viral_engine service")
    async def test_real_viral_engine_integration(self):
        """Test with real viral_engine service"""
        # This would test actual viral content optimization
        pass


class TestScheduleEntryValidation:
    """Test validation and edge cases for schedule entries"""
    
    def test_content_schedule_entry_validation(self):
        """Test ContentScheduleEntry validation"""
        entry = ContentScheduleEntry(
            id="test_entry",
            achievement_id=1,
            content_type=ContentType.CASE_STUDY,
            platform=Platform.LINKEDIN,
            scheduled_time=datetime.now()
        )
        
        assert entry.status == "scheduled"  # Default status
        assert entry.created_at is not None
        assert entry.generated_content is None  # Not generated yet
    
    def test_weekly_content_plan_defaults(self):
        """Test WeeklyContentPlan default values"""
        plan = WeeklyContentPlan(week_start=datetime.now())
        
        assert plan.target_posts == 3
        assert Platform.LINKEDIN in plan.platforms
        assert Platform.MEDIUM in plan.platforms  
        assert Platform.DEVTO in plan.platforms
        assert "anthropic" in plan.target_companies
        assert ContentType.CASE_STUDY in plan.content_types
        assert len(plan.scheduled_entries) == 0  # Empty initially


@pytest.mark.performance
class TestContentSchedulerPerformance:
    """Performance tests for scheduler operations"""
    
    @pytest.mark.asyncio
    async def test_batch_content_generation_performance(self, mock_achievement_data):
        """Test performance of generating multiple content pieces"""
        scheduler = ContentScheduler()
        
        # Create multiple entries
        entries = [
            ContentScheduleEntry(
                id=f"perf_entry_{i}",
                achievement_id=i + 1,
                content_type=ContentType.CASE_STUDY,
                platform=Platform.LINKEDIN,
                scheduled_time=datetime.now()
            )
            for i in range(5)
        ]
        
        # Mock content generation to be fast
        with patch.object(scheduler, 'generate_scheduled_content', return_value=True) as mock_generate:
            
            start_time = datetime.now()
            
            # Process all entries
            tasks = [scheduler.generate_scheduled_content(entry) for entry in entries]
            results = await asyncio.gather(*tasks)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            assert all(results)  # All succeeded
            assert duration < 5.0  # Should complete within 5 seconds
            assert mock_generate.call_count == 5