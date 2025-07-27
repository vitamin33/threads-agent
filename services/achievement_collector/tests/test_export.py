"""
Tests for Phase 3.2 Multi-format Export features.
"""

import json
import os
from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from services.achievement_collector.db.models import Achievement
from services.achievement_collector.export.formats.csv_export import CSVExporter
from services.achievement_collector.export.formats.json_export import JSONExporter
from services.achievement_collector.export.linkedin.integration import (
    LinkedInIntegration,
    LinkedInPost,
)
from services.achievement_collector.export.pdf.portfolio_generator import (
    PortfolioGenerator,
)
from services.achievement_collector.export.pdf.resume_generator import ResumeGenerator
from services.achievement_collector.export.web.portfolio_site import (
    WebPortfolioGenerator,
)
from services.achievement_collector.main import app


@pytest.fixture
def export_achievements():
    """Generate achievements for export testing."""
    achievements = []
    for i in range(5):
        achievements.append(
            Achievement(
                title=f"Export Test Achievement {i+1}",
                description=f"Description for export test {i+1}",
                category="feature" if i % 2 == 0 else "optimization",
                impact_score=70 + i * 5,
                complexity_score=60 + i * 3,
                skills_demonstrated=["Python", "FastAPI", "PostgreSQL"],
                tags=["Docker", "Kubernetes"],
                business_value="Improved system performance by 25%",
                duration_hours=40,
                completed_at=datetime.utcnow() - timedelta(days=30 * (5 - i)),
                started_at=datetime.utcnow() - timedelta(days=30 * (5 - i) + 7),
                portfolio_ready=True,
                source_type="manual",
                source_id=f"export_test_{i}",
            )
        )
    return achievements


class TestJSONExporter:
    """Test JSON export functionality."""
    
    @pytest.mark.asyncio
    async def test_json_export_basic(self, db_session, export_achievements):
        """Test basic JSON export."""
        exporter = JSONExporter()
        
        # Add achievements to session
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        # Export
        result = await exporter.export(db_session)
        
        assert "export_metadata" in result
        assert "achievements" in result
        assert result["export_metadata"]["total_achievements"] == 5
        assert len(result["achievements"]) == 5
        
    @pytest.mark.asyncio
    async def test_json_export_with_analytics(self, db_session, export_achievements):
        """Test JSON export with analytics."""
        exporter = JSONExporter()
        
        # Add achievements to session
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        # Export with analytics
        result = await exporter.export(db_session, include_analytics=True)
        
        assert "analytics" in result
        assert "summary" in result["analytics"]
        assert "top_skills" in result["analytics"]
        assert result["analytics"]["summary"]["total_achievements"] == 5
        
    def test_json_export_to_file(self, tmp_path):
        """Test JSON export to file."""
        exporter = JSONExporter()
        
        data = {"test": "data", "achievements": []}
        filename = str(tmp_path / "test_export.json")
        
        result_path = exporter.export_to_file(data, filename, pretty=True)
        
        assert os.path.exists(result_path)
        with open(result_path, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == data


class TestCSVExporter:
    """Test CSV export functionality."""
    
    @pytest.mark.asyncio
    async def test_csv_export_detailed(self, db_session, export_achievements):
        """Test detailed CSV export."""
        exporter = CSVExporter()
        
        # Add achievements to session
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        # Export
        result = await exporter.export(db_session, format_type="detailed")
        
        assert isinstance(result, str)
        assert "title,description,category" in result
        assert "Export Test Achievement 1" in result
        
    @pytest.mark.asyncio
    async def test_csv_export_summary(self, db_session, export_achievements):
        """Test summary CSV export."""
        exporter = CSVExporter()
        
        # Add achievements to session
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        # Export summary
        result = await exporter.export(db_session, format_type="summary")
        
        assert isinstance(result, str)
        assert "category,achievement_count" in result
        assert "TOTAL" in result
        
    def test_csv_export_to_file(self, tmp_path):
        """Test CSV export to file."""
        exporter = CSVExporter()
        
        csv_data = "header1,header2\nvalue1,value2"
        filename = str(tmp_path / "test_export.csv")
        
        result_path = exporter.export_to_file(csv_data, filename)
        
        assert os.path.exists(result_path)
        with open(result_path, 'r') as f:
            content = f.read()
        assert content == csv_data


class TestResumeGenerator:
    """Test resume PDF generation."""
    
    @pytest.mark.asyncio
    async def test_resume_generation(self, db_session, export_achievements, tmp_path):
        """Test resume PDF generation."""
        generator = ResumeGenerator()
        
        # Add achievements to session
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        # Mock AI analyzer
        with patch.object(generator.ai_analyzer, 'generate_professional_summary') as mock_summary:
            mock_summary.return_value = "Professional summary text"
            
            # Generate resume
            filename = str(tmp_path / "test_resume.pdf")
            result = await generator.export(
                db_session,
                user_info={"name": "Test User", "email": "test@example.com"},
                filename=filename
            )
            
            assert os.path.exists(result)
            assert result == filename
            
    def test_create_header(self):
        """Test resume header creation."""
        generator = ResumeGenerator()
        
        user_info = {
            "name": "John Doe",
            "email": "john@example.com",
            "location": "San Francisco"
        }
        
        header = generator._create_header(user_info)
        
        assert len(header) > 0
        assert any("John Doe" in str(item) for item in header)
        
    def test_create_skills_section(self, export_achievements):
        """Test skills section creation."""
        generator = ResumeGenerator()
        
        skills = generator._create_skills_section(export_achievements)
        
        assert len(skills) > 0
        assert any("Python" in str(item) for item in skills)


class TestPortfolioGenerator:
    """Test portfolio PDF generation."""
    
    @pytest.mark.asyncio
    async def test_portfolio_generation(self, db_session, export_achievements, tmp_path):
        """Test portfolio PDF generation."""
        generator = PortfolioGenerator()
        
        # Add achievements to session
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        # Generate portfolio
        filename = str(tmp_path / "test_portfolio.pdf")
        result = await generator.export(
            db_session,
            user_info={"name": "Test User"},
            filename=filename,
            include_charts=False  # Skip charts for testing
        )
        
        assert os.path.exists(result)
        assert result == filename
        
    def test_create_cover_page(self, export_achievements):
        """Test portfolio cover page creation."""
        generator = PortfolioGenerator()
        
        user_info = {"name": "Test User"}
        cover = generator._create_cover_page(user_info, export_achievements)
        
        assert len(cover) > 0
        assert any("PROFESSIONAL PORTFOLIO" in str(item) for item in cover)
        
    def test_create_executive_summary(self, export_achievements):
        """Test executive summary creation."""
        generator = PortfolioGenerator()
        
        summary = generator._create_executive_summary(export_achievements)
        
        assert len(summary) > 0
        assert any("EXECUTIVE SUMMARY" in str(item) for item in summary)


class TestLinkedInIntegration:
    """Test LinkedIn integration functionality."""
    
    @pytest.mark.asyncio
    async def test_achievement_post_generation(self, db_session, export_achievements):
        """Test LinkedIn achievement post generation."""
        integration = LinkedInIntegration()
        
        # Add achievements to session
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        # Mock AI analyzer
        with patch.object(integration.ai_analyzer, 'generate_linkedin_content') as mock_content:
            mock_content.return_value = "Excited to share this achievement!"
            
            # Generate posts
            posts = await integration.export(db_session, post_type="achievement")
            
            assert len(posts) > 0
            assert all(isinstance(post, LinkedInPost) for post in posts)
            assert all(post.post_type == "achievement" for post in posts)
            
    @pytest.mark.asyncio
    async def test_milestone_post_generation(self, db_session, export_achievements):
        """Test LinkedIn milestone post generation."""
        integration = LinkedInIntegration()
        
        # Add 10+ achievements for milestone
        for i in range(10):
            achievement = Achievement(
                title=f"Milestone Achievement {i+1}",
                description=f"Milestone achievement {i+1} description",
                impact_score=80,
                category="feature",
                skills_demonstrated=["Python"],
                started_at=datetime.utcnow() - timedelta(days=7),
                completed_at=datetime.utcnow(),
                duration_hours=40,
                source_type="manual",
                source_id=f"milestone_{i}"
            )
            db_session.add(achievement)
        db_session.commit()
        
        # Generate milestone post
        posts = await integration.export(db_session, post_type="milestone")
        
        assert len(posts) == 1
        assert posts[0].post_type == "milestone"
        assert "Celebrating a Career Milestone" in posts[0].content
        
    def test_generate_hashtags(self, export_achievements):
        """Test hashtag generation."""
        integration = LinkedInIntegration()
        
        hashtags = integration._generate_hashtags(export_achievements[0])
        
        assert len(hashtags) > 0
        assert len(hashtags) <= 10
        assert "Tech" in hashtags
        
    def test_profile_suggestions(self, export_achievements):
        """Test LinkedIn profile suggestions."""
        integration = LinkedInIntegration()
        
        suggestions = integration.format_for_profile_update(export_achievements)
        
        assert "headline" in suggestions
        assert "about" in suggestions
        assert "featured" in suggestions
        assert "Software Engineer" in suggestions["headline"]


class TestWebPortfolioGenerator:
    """Test web portfolio generation."""
    
    @pytest.mark.asyncio
    async def test_web_portfolio_generation(self, db_session, export_achievements, tmp_path):
        """Test web portfolio generation."""
        generator = WebPortfolioGenerator()
        
        # Add achievements to session
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        # Generate portfolio
        output_dir = str(tmp_path / "portfolio")
        result = await generator.export(
            db_session,
            user_info={"name": "Test User", "title": "Software Developer"},
            output_dir=output_dir,
            theme="modern"
        )
        
        assert os.path.exists(result)
        assert os.path.exists(os.path.join(result, "index.html"))
        assert os.path.exists(os.path.join(result, "css", "style.css"))
        assert os.path.exists(os.path.join(result, "js", "portfolio.js"))
        
    def test_prepare_portfolio_data(self, export_achievements):
        """Test portfolio data preparation."""
        generator = WebPortfolioGenerator()
        
        user_info = {"name": "Test User"}
        data = generator._prepare_portfolio_data(export_achievements, user_info)
        
        assert "user" in data
        assert "stats" in data
        assert "achievements" in data
        assert data["stats"]["total_achievements"] == 5
        
    def test_generate_timeline_data(self, export_achievements):
        """Test timeline data generation."""
        generator = WebPortfolioGenerator()
        
        timeline = generator._generate_timeline_data(export_achievements)
        
        assert len(timeline) == 5
        assert all("date" in item for item in timeline)
        assert all("title" in item for item in timeline)
        
    def test_generate_skills_data(self, export_achievements):
        """Test skills data generation."""
        generator = WebPortfolioGenerator()
        
        skills_data = generator._generate_skills_data(export_achievements)
        
        assert "counts" in skills_data
        assert "radar" in skills_data
        assert skills_data["total"] > 0
        assert "Python" in skills_data["counts"]


class TestExportAPI:
    """Test export API endpoints."""
    
    @pytest.fixture
    def client(self, db_session):
        """Create test client with database override."""
        def override():
            yield db_session
        
        from services.achievement_collector.db.config import get_db
        app.dependency_overrides[get_db] = override
        
        with TestClient(app) as test_client:
            yield test_client
        
        app.dependency_overrides.clear()
    
    def test_export_json_endpoint(self, client, db_session, export_achievements):
        """Test JSON export endpoint."""
        # Add achievements
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        response = client.post("/export/json", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert "export_metadata" in data
        assert "achievements" in data
        
    def test_export_csv_endpoint(self, client, db_session, export_achievements):
        """Test CSV export endpoint."""
        # Add achievements
        for achievement in export_achievements:
            db_session.add(achievement)
        db_session.commit()
        
        response = client.post("/export/csv", json={})
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
    def test_export_formats_endpoint(self, client):
        """Test export formats endpoint."""
        response = client.get("/export/formats")
        
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert "json" in data["formats"]
        assert "csv" in data["formats"]
        assert "pdf" in data["formats"]
        assert "linkedin" in data["formats"]
        assert "web" in data["formats"]