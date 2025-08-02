"""
Tests for ContentGenerator - Following TDD principles

This module tests the AI-powered content generation functionality that creates
engaging technical articles from code analysis.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.content_generator import ContentGenerator
from app.models.article import (
    ArticleContent, ArticleType, CodeAnalysis, Platform, 
    ArticleRequest, SourceType
)


class TestContentGenerator:
    """Test suite for ContentGenerator following TDD methodology"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = MagicMock()
        settings.openai_api_key = "test-key"
        settings.openai_model = "gpt-4"
        return settings
    
    @pytest.fixture
    def sample_code_analysis(self):
        """Sample code analysis for testing"""
        return CodeAnalysis(
            patterns=["microservices", "async_programming", "testing"],
            complexity_score=4.2,
            test_coverage=85.5,
            dependencies=["fastapi", "pytest", "celery", "openai"],
            metrics={
                "lines_of_code": {"total": 5000, "python": 4500},
                "file_counts": {".py": 42, ".yaml": 8}
            },
            interesting_functions=[
                {
                    "name": "process_article_request",
                    "file": "app/services/content_generator.py",
                    "line": 53,
                    "complexity": 6,
                    "docstring": "Generate article content based on code analysis",
                    "args": ["self", "analysis", "article_type", "target_platform"],
                    "is_async": True
                },
                {
                    "name": "parse_content_angles",
                    "file": "app/services/content_generator.py", 
                    "line": 142,
                    "complexity": 3,
                    "docstring": "Parse the generated angles into structured data",
                    "args": ["self", "angles_text"],
                    "is_async": False
                }
            ],
            recent_changes=[
                {
                    "hash": "abc123ef",
                    "message": "feat: add content generation API",
                    "author": "Developer",
                    "date": "2024-01-15T10:30:00",
                    "files_changed": 3
                }
            ]
        )
    
    def test_content_generator_initialization_with_settings(self, mock_settings):
        """
        Test: ContentGenerator should initialize with settings and OpenAI client
        Expected: Should create instance with proper configuration
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI') as mock_openai:
                generator = ContentGenerator()
                
                assert generator.settings == mock_settings
                mock_openai.assert_called_once_with(api_key="test-key")
                assert len(generator.content_styles) == 5
                assert "technical_deep_dive" in generator.content_styles

    def test_content_styles_configuration_completeness(self, mock_settings):
        """
        Test: ContentGenerator should have complete content style configurations
        Expected: All styles should have required fields
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                required_fields = ["tone", "humor_level", "examples", "target"]
                
                for style_name, style_config in generator.content_styles.items():
                    for field in required_fields:
                        assert field in style_config, f"Style {style_name} missing {field}"
                    
                    assert isinstance(style_config["tone"], str)
                    assert isinstance(style_config["target"], str)

    @pytest.mark.asyncio
    async def test_generate_article_basic_flow_calls_required_methods(self, mock_settings, sample_code_analysis):
        """
        Test: generate_article should call all required methods in correct order
        Expected: Should return ArticleContent with proper data flow
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                # Mock all the private methods
                mock_angles = [
                    {
                        "id": 1,
                        "hook": "Ever wondered how microservices actually scale?",
                        "narrative": "A journey through real production challenges",
                        "insights": "Key patterns for distributed systems",
                        "relatable": "The 3 AM production incident story",
                        "cta": "Try implementing these patterns"
                    }
                ]
                
                expected_content = ArticleContent(
                    title="How I Built Microservices That Actually Scale",
                    subtitle="Ever wondered how microservices actually scale?",
                    content="Full article content here...",
                    tags=["microservices", "python", "architecture"],
                    estimated_read_time=8,
                    code_examples=[{
                        "title": "Function: process_article_request",
                        "language": "python",
                        "code": "# Example code",
                        "explanation": "This async function demonstrates..."
                    }],
                    insights=["Insight 1", "Insight 2"]
                )
                
                with patch.object(generator, '_select_optimal_style', return_value="technical_deep_dive"):
                    with patch.object(generator, '_generate_content_angles', return_value=mock_angles):
                        with patch.object(generator, '_select_best_angle', return_value=mock_angles[0]):
                            with patch.object(generator, '_generate_full_content', return_value=expected_content):
                                
                                result = await generator.generate_article(
                                    analysis=sample_code_analysis,
                                    article_type=ArticleType.ARCHITECTURE,
                                    target_platform=Platform.DEVTO
                                )
                                
                                assert isinstance(result, ArticleContent)
                                assert result.title == expected_content.title
                                assert result.subtitle == expected_content.subtitle
                                assert len(result.tags) > 0

    @pytest.mark.asyncio
    async def test_generate_content_angles_creates_structured_angles(self, mock_settings, sample_code_analysis):
        """
        Test: _generate_content_angles should create multiple content angles
        Expected: Should return list of structured angle dictionaries
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = """
            Angle 1:
            Hook: This is a compelling opening
            Core narrative: The main story unfolds
            Technical insights: Key learning points
            Relatable moments: Human connection
            Call to action: What to do next
            
            Angle 2:
            Hook: Another attention grabber
            Core narrative: Different story approach
            Technical insights: Alternative insights
            Relatable moments: Different struggles
            Call to action: Alternative action
            """
            mock_client.chat.completions.create.return_value = mock_response
            
            with patch('app.services.content_generator.openai.AsyncOpenAI', return_value=mock_client):
                generator = ContentGenerator()
                
                angles = await generator._generate_content_angles(
                    analysis=sample_code_analysis,
                    article_type=ArticleType.ARCHITECTURE,
                    style="technical_deep_dive"
                )
                
                assert isinstance(angles, list)
                assert len(angles) >= 2
                
                for angle in angles:
                    assert "id" in angle
                    assert "hook" in angle
                    assert "narrative" in angle
                    assert "insights" in angle
                    assert "relatable" in angle
                    assert "cta" in angle
                    assert isinstance(angle["id"], int)

    def test_parse_content_angles_extracts_sections_correctly(self, mock_settings):
        """
        Test: _parse_content_angles should extract sections from text
        Expected: Should return structured angle data
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                angles_text = """
                Angle 1:
                Hook: Amazing technical story
                Core narrative: How we solved the problem
                Technical insights: What we learned
                Relatable moments: The struggle was real
                Call to action: Try this approach
                
                Angle 2:
                Hook: Different compelling opening
                Core narrative: Alternative approach
                Technical insights: Different lessons
                Relatable moments: Another challenge
                Call to action: Consider this method
                """
                
                angles = generator._parse_content_angles(angles_text)
                
                assert len(angles) == 2
                assert angles[0]["id"] == 1
                assert angles[1]["id"] == 2
                assert "Amazing technical story" in angles[0]["hook"]
                assert "Different compelling opening" in angles[1]["hook"]

    def test_extract_section_finds_content_after_marker(self, mock_settings):
        """
        Test: _extract_section should find content after specific marker
        Expected: Should return clean content string
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                text = """
                Some intro text
                Hook: This is the hook content
                that continues on next line
                Core narrative: This is different content
                """
                
                hook_content = generator._extract_section(text, "Hook:")
                assert "This is the hook content that continues on next line" in hook_content
                assert "Core narrative" not in hook_content

    @pytest.mark.asyncio
    async def test_select_best_angle_scores_and_returns_highest(self, mock_settings):
        """
        Test: _select_best_angle should score angles and return best one
        Expected: Should return angle with highest score
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                angles = [
                    {"id": 1, "hook": "Good hook", "narrative": "Good story", "insights": "Good insights"},
                    {"id": 2, "hook": "Better hook", "narrative": "Better story", "insights": "Better insights"},
                    {"id": 3, "hook": "OK hook", "narrative": "OK story", "insights": "OK insights"}
                ]
                
                # Mock scoring to return predictable scores
                with patch.object(generator, '_score_angle', side_effect=[7.5, 8.5, 6.0]):
                    best_angle = await generator._select_best_angle(angles, Platform.DEVTO)
                    
                    assert best_angle["id"] == 2  # Second angle had highest score (8.5)

    @pytest.mark.asyncio
    async def test_score_angle_returns_numeric_score(self, mock_settings):
        """
        Test: _score_angle should return numeric score between 1-10
        Expected: Should return float in valid range
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "8.5"
            mock_client.chat.completions.create.return_value = mock_response
            
            with patch('app.services.content_generator.openai.AsyncOpenAI', return_value=mock_client):
                generator = ContentGenerator()
                
                angle = {
                    "hook": "Compelling hook",
                    "narrative": "Great story",
                    "insights": "Valuable insights"
                }
                
                score = await generator._score_angle(angle, Platform.DEVTO)
                
                assert isinstance(score, float)
                assert 1.0 <= score <= 10.0

    @pytest.mark.asyncio
    async def test_score_angle_handles_api_errors_gracefully(self, mock_settings):
        """
        Test: _score_angle should handle API errors and return default score
        Expected: Should return 5.0 when API call fails
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            with patch('app.services.content_generator.openai.AsyncOpenAI', return_value=mock_client):
                generator = ContentGenerator()
                
                angle = {"hook": "Test", "narrative": "Test", "insights": "Test"}
                score = await generator._score_angle(angle, Platform.DEVTO)
                
                assert score == 5.0

    def test_extract_code_examples_processes_function_data(self, mock_settings, sample_code_analysis):
        """
        Test: _extract_code_examples should process function data into examples
        Expected: Should return formatted code examples with explanations
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                examples = generator._extract_code_examples(sample_code_analysis)
                
                assert isinstance(examples, list)
                assert len(examples) <= 3  # Limited to first 3 functions
                
                for example in examples:
                    assert "title" in example
                    assert "language" in example
                    assert "code" in example
                    assert "explanation" in example
                    assert example["language"] == "python"

    def test_generate_tags_creates_relevant_tags(self, mock_settings, sample_code_analysis):
        """
        Test: _generate_tags should create relevant tags from analysis
        Expected: Should return list of relevant tags for platform
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                tags = generator._generate_tags(sample_code_analysis, Platform.DEVTO)
                
                assert isinstance(tags, list)
                assert len(tags) > 0  # Should have at least some tags
                
                # Check for any relevant tags from patterns or dependencies
                expected_tags = ["microservices", "async", "testing", "fastapi", "python", 
                                "architecture", "distributed", "pytest", "api", "tutorial", "beginners"]
                assert any(tag in expected_tags for tag in tags), f"No expected tags found in {tags}"

    def test_estimate_read_time_calculates_correctly(self, mock_settings):
        """
        Test: _estimate_read_time should calculate reading time from word count
        Expected: Should return reasonable time in minutes
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                # ~450 words should be ~2 minutes (450/225)
                content = " ".join(["word"] * 450)
                read_time = generator._estimate_read_time(content)
                
                assert isinstance(read_time, int)
                assert read_time >= 1  # At least 1 minute
                assert read_time == 2  # Should be 2 minutes for 450 words

    def test_select_optimal_style_chooses_appropriate_style(self, mock_settings):
        """
        Test: _select_optimal_style should select style based on article type and platform
        Expected: Should return appropriate style from predefined matrix
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                # Test specific combinations
                style1 = generator._select_optimal_style(ArticleType.ARCHITECTURE, Platform.DEVTO)
                assert style1 == "technical_deep_dive"
                
                style2 = generator._select_optimal_style(ArticleType.ARCHITECTURE, Platform.LINKEDIN)
                assert style2 == "architecture_showcase"
                
                style3 = generator._select_optimal_style(ArticleType.TUTORIAL, Platform.DEVTO)
                assert style3 == "learning_journey"
                
                # Test fallback for unknown combination
                style4 = generator._select_optimal_style(ArticleType.DEEP_DIVE, Platform.GITHUB)
                assert style4 == "technical_deep_dive"  # Default fallback

    def test_adapt_tags_for_platform_respects_limits(self, mock_settings):
        """
        Test: _adapt_tags_for_platform should respect platform tag limits
        Expected: Should return appropriate number of tags for each platform
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                many_tags = ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"]
                
                devto_tags = generator._adapt_tags_for_platform(many_tags, Platform.DEVTO)
                assert len(devto_tags) <= 4
                
                linkedin_tags = generator._adapt_tags_for_platform(many_tags, Platform.LINKEDIN)
                assert len(linkedin_tags) <= 10
                
                twitter_tags = generator._adapt_tags_for_platform(many_tags, Platform.TWITTER)
                assert len(twitter_tags) <= 3

    def test_estimate_thread_length_calculates_tweet_count(self, mock_settings):
        """
        Test: _estimate_thread_length should calculate number of tweets needed
        Expected: Should return reasonable tweet count based on content length
        """
        with patch('app.services.content_generator.get_settings', return_value=mock_settings):
            with patch('app.services.content_generator.openai.AsyncOpenAI'):
                generator = ContentGenerator()
                
                # ~100 words should be ~4 tweets (100/25)
                content = " ".join(["word"] * 100)
                thread_length = generator._estimate_thread_length(content)
                
                assert isinstance(thread_length, int)
                assert thread_length >= 1
                assert thread_length == 4