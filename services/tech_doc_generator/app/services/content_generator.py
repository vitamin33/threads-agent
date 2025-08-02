import openai
from typing import Dict, List, Any, Optional
import json
import structlog
from datetime import datetime
import hashlib

from ..models.article import ArticleContent, ArticleType, CodeAnalysis, Platform
from ..core.config import get_settings
from ..core.cache import get_cache_manager
from ..core.resilience import resilient_api_call

logger = structlog.get_logger()

class ContentGenerator:
    """Generates varied, engaging content from code analysis"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.cache = get_cache_manager()
        
        # Content style templates for different audiences
        self.content_styles = {
            "technical_deep_dive": {
                "tone": "expert",
                "humor_level": "minimal",
                "examples": "detailed",
                "target": "senior engineers, architects"
            },
            "problem_solving_story": {
                "tone": "conversational",
                "humor_level": "moderate",
                "examples": "practical",
                "target": "team leads, managers"
            },
            "learning_journey": {
                "tone": "educational",
                "humor_level": "light",
                "examples": "step-by-step",
                "target": "mid-level engineers"
            },
            "war_stories": {
                "tone": "humorous",
                "humor_level": "high",
                "examples": "relatable",
                "target": "all levels"
            },
            "architecture_showcase": {
                "tone": "professional",
                "humor_level": "subtle",
                "examples": "visual",
                "target": "CTOs, principal engineers"
            }
        }
    
    async def _cached_openai_call(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        operation: str = "general"
    ) -> str:
        """Make cached OpenAI API call to reduce costs and latency"""
        if model is None:
            model = self.settings.openai_model
            
        # Generate cache key from messages content
        messages_str = json.dumps(messages, sort_keys=True)
        cache_key_data = {
            "messages_hash": hashlib.md5(messages_str.encode()).hexdigest(),
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Try to get cached response
        cached_response = await self.cache.get_cached_result("openai_response", **cache_key_data)
        if cached_response:
            logger.info("Using cached OpenAI response", operation=operation)
            return cached_response
        
        # Make resilient API call
        async def _make_openai_call():
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        try:
            result = await resilient_api_call(
                _make_openai_call,
                service_name="openai"
            )
            
            # Cache the response
            await self.cache.cache_result("openai_response", result, **cache_key_data)
            
            logger.info("OpenAI API call completed", operation=operation, model=model, tokens=max_tokens)
            return result
            
        except Exception as e:
            logger.error("OpenAI API call failed", operation=operation, error=str(e))
            raise
    
    async def generate_article(
        self,
        analysis: CodeAnalysis,
        article_type: ArticleType,
        target_platform: Platform,
        style_preference: Optional[str] = None
    ) -> ArticleContent:
        """Generate article content based on code analysis"""
        
        logger.info("Generating article", 
                   article_type=article_type, 
                   platform=target_platform,
                   style=style_preference)
        
        # Select content style
        style = style_preference or self._select_optimal_style(article_type, target_platform)
        
        # Generate multiple angles and select best
        angles = await self._generate_content_angles(analysis, article_type, style)
        best_angle = await self._select_best_angle(angles, target_platform)
        
        # Generate full content
        content = await self._generate_full_content(analysis, best_angle, style, target_platform)
        
        return content
    
    async def _generate_content_angles(
        self, 
        analysis: CodeAnalysis, 
        article_type: ArticleType,
        style: str
    ) -> List[Dict[str, Any]]:
        """Generate multiple content angles for the same code"""
        
        style_config = self.content_styles[style]
        
        system_prompt = f"""You are a senior technical writer who creates engaging content for {style_config['target']}.
        Your writing style is {style_config['tone']} with {style_config['humor_level']} humor.
        You specialize in turning real code into compelling stories that showcase technical expertise.
        
        Generate 3 different angles for an article about this code analysis:
        - Patterns found: {analysis.patterns}
        - Complexity: {analysis.complexity_score}
        - Dependencies: {analysis.dependencies}
        - Interesting functions: {len(analysis.interesting_functions)}
        - Recent changes: {len(analysis.recent_changes)}
        
        For each angle, provide:
        1. Hook (attention-grabbing opening)
        2. Core narrative (main story)
        3. Technical insights (what readers will learn)
        4. Relatable moments (human elements)
        5. Call to action (what readers should do)"""
        
        user_prompt = f"""Create 3 varied content angles for a {article_type.value} article.
        
        Style requirements:
        - Tone: {style_config['tone']}
        - Humor level: {style_config['humor_level']}
        - Examples: {style_config['examples']}
        - Target audience: {style_config['target']}
        
        Make each angle unique and engaging. Include real situations that hiring managers would find impressive.
        
        Code Analysis Data:
        {json.dumps({
            'patterns': analysis.patterns,
            'complexity_score': analysis.complexity_score,
            'test_coverage': analysis.test_coverage,
            'dependencies': analysis.dependencies[:10],  # Limit for context
            'interesting_functions': analysis.interesting_functions[:5],
            'recent_changes': analysis.recent_changes[:3],
            'metrics': analysis.metrics
        }, indent=2)}"""
        
        # Use cached OpenAI call
        angles_text = await self._cached_openai_call(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=2000,
            operation="generate_content_angles"
        )
        return self._parse_content_angles(angles_text)
    
    def _parse_content_angles(self, angles_text: str) -> List[Dict[str, Any]]:
        """Parse the generated angles into structured data"""
        # This is simplified - would use more sophisticated parsing
        angles = []
        
        # Split by angle markers (Angle 1, Angle 2, etc.)
        sections = angles_text.split("Angle ")
        
        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            angle = {
                "id": i,
                "hook": self._extract_section(section, "Hook:"),
                "narrative": self._extract_section(section, "Core narrative:"),
                "insights": self._extract_section(section, "Technical insights:"),
                "relatable": self._extract_section(section, "Relatable moments:"),
                "cta": self._extract_section(section, "Call to action:"),
                "full_text": section
            }
            angles.append(angle)
        
        return angles
    
    def _extract_section(self, text: str, marker: str) -> str:
        """Extract a section from text based on marker"""
        lines = text.split('\n')
        capturing = False
        content = []
        
        for line in lines:
            if marker.lower() in line.lower():
                capturing = True
                # Get content after the marker
                after_marker = line.split(marker, 1)[-1].strip()
                if after_marker:
                    content.append(after_marker)
                continue
            
            if capturing:
                # Stop at next marker or empty line
                if any(m in line.lower() for m in ["hook:", "narrative:", "insights:", "relatable:", "call to action:"]):
                    break
                if line.strip():
                    content.append(line.strip())
                elif content:  # Stop at empty line if we have content
                    break
        
        return ' '.join(content)
    
    async def _select_best_angle(self, angles: List[Dict[str, Any]], platform: Platform) -> Dict[str, Any]:
        """Select the best angle based on platform and engagement potential"""
        
        # Score each angle
        scored_angles = []
        for angle in angles:
            score = await self._score_angle(angle, platform)
            scored_angles.append((angle, score))
        
        # Return highest scoring angle
        best_angle = max(scored_angles, key=lambda x: x[1])[0]
        logger.info("Selected best angle", angle_id=best_angle["id"], score=max(scored_angles, key=lambda x: x[1])[1])
        
        return best_angle
    
    async def _score_angle(self, angle: Dict[str, Any], platform: Platform) -> float:
        """Score an angle for engagement potential"""
        
        scoring_prompt = f"""Score this content angle for {platform.value} on a scale of 1-10.
        
        Consider:
        - Hook strength (will it grab attention?)
        - Technical value (will experts find it valuable?)
        - Relatability (will readers connect with it?)
        - Platform fit (does it suit {platform.value}?)
        - Uniqueness (is it different from typical content?)
        
        Angle:
        Hook: {angle['hook']}
        Narrative: {angle['narrative']}
        Insights: {angle['insights']}
        
        Respond with just a number from 1-10."""
        
        try:
            score_text = await self._cached_openai_call(
                messages=[{"role": "user", "content": scoring_prompt}],
                model="gpt-3.5-turbo",  # Use faster model for scoring
                temperature=0.3,
                max_tokens=10,
                operation="score_angle"
            )
            
            return float(score_text.strip())
        except:
            return 5.0  # Default score if parsing fails
    
    async def _generate_full_content(
        self,
        analysis: CodeAnalysis,
        angle: Dict[str, Any],
        style: str,
        platform: Platform
    ) -> ArticleContent:
        """Generate full article content based on selected angle"""
        
        style_config = self.content_styles[style]
        
        # Generate title variations
        titles = await self._generate_titles(angle, platform)
        best_title = titles[0]  # Select first for now
        
        # Generate main content
        content_text = await self._generate_main_content(analysis, angle, style_config, platform)
        
        # Extract code examples
        code_examples = self._extract_code_examples(analysis)
        
        # Generate insights
        insights = await self._generate_key_insights(analysis, angle)
        
        # Generate tags
        tags = self._generate_tags(analysis, platform)
        
        # Estimate read time
        read_time = self._estimate_read_time(content_text)
        
        return ArticleContent(
            title=best_title,
            subtitle=angle['hook'],
            content=content_text,
            tags=tags,
            estimated_read_time=read_time,
            code_examples=code_examples,
            insights=insights,
            platform_specific=self._generate_platform_specific_content(platform, content_text)
        )
    
    async def _generate_titles(self, angle: Dict[str, Any], platform: Platform) -> List[str]:
        """Generate multiple title options"""
        
        prompt = f"""Generate 5 compelling titles for a {platform.value} article based on this angle:
        
        Hook: {angle['hook']}
        Narrative: {angle['narrative']}
        
        Make titles:
        - Specific and actionable
        - Appealing to hiring managers
        - Technical but accessible
        - Platform-appropriate for {platform.value}
        
        Examples of good titles:
        - "How I Built a PR Achievement Analyzer That Saved Our Team 20 Hours/Week"
        - "The Kubernetes Architecture Decision That Made Our Microservices Actually Scale"
        - "From Chaos to Clarity: My Journey Building Production-Ready AI Pipelines"
        
        Return 5 titles, one per line."""
        
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=500
        )
        
        titles = [line.strip() for line in response.choices[0].message.content.split('\n') if line.strip()]
        return titles[:5]
    
    async def _generate_main_content(
        self,
        analysis: CodeAnalysis,
        angle: Dict[str, Any],
        style_config: Dict[str, str],
        platform: Platform
    ) -> str:
        """Generate the main article content"""
        
        system_prompt = f"""You are writing for {style_config['target']} with a {style_config['tone']} tone.
        Include {style_config['humor_level']} humor and {style_config['examples']} examples.
        
        Write content that demonstrates:
        1. Technical expertise and problem-solving ability
        2. Leadership and architectural thinking
        3. Real-world impact and business value
        4. Modern best practices and tool knowledge
        
        Make it engaging with:
        - Personal anecdotes and "war stories"
        - Specific metrics and outcomes
        - Relatable developer struggles
        - Clear technical explanations
        - Actionable takeaways"""
        
        # Create detailed content prompt with real code data
        interesting_functions = analysis.interesting_functions[:3]
        recent_changes = analysis.recent_changes[:2]
        
        user_prompt = f"""Write a detailed article following this structure:
        
        **Opening Hook:**
        {angle['hook']}
        
        **Main Narrative:**
        {angle['narrative']}
        
        **Technical Deep Dive:**
        Based on this real code analysis:
        - Architecture patterns: {analysis.patterns}
        - Code complexity: {analysis.complexity_score}/10
        - Test coverage: {analysis.test_coverage}%
        - Key dependencies: {', '.join(analysis.dependencies[:5])}
        
        **Interesting Implementation Details:**
        {json.dumps(interesting_functions, indent=2)}
        
        **Recent Evolution:**
        {json.dumps(recent_changes, indent=2)}
        
        **Key Insights to Highlight:**
        {angle['insights']}
        
        **Relatable Moments:**
        {angle['relatable']}
        
        **Call to Action:**
        {angle['cta']}
        
        Write 1500-2500 words. Include:
        - Specific code examples and explanations
        - Personal stories about challenges faced
        - Metrics showing real impact
        - Technical decisions and trade-offs
        - Lessons learned and best practices
        
        Make it valuable for both technical readers and hiring managers.
        Show depth of knowledge while keeping it accessible."""
        
        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    def _extract_code_examples(self, analysis: CodeAnalysis) -> List[Dict[str, str]]:
        """Extract and format code examples from analysis"""
        examples = []
        
        for func in analysis.interesting_functions[:3]:
            example = {
                "title": f"Function: {func['name']}",
                "language": "python",
                "code": f"# {func['file']}:{func['line']}\n" + 
                       f"def {func['name']}({', '.join(func['args'])}):\n" +
                       f"    \"\"\"{func.get('docstring', 'Implementation details...')}\"\"\"\n" +
                       f"    # Complexity score: {func['complexity']}\n" +
                       f"    pass  # Actual implementation here",
                "explanation": f"This {'async ' if func.get('is_async') else ''}function in {func['file']} demonstrates "
                             f"{'asynchronous programming patterns' if func.get('is_async') else 'clean code structure'} "
                             f"with a complexity score of {func['complexity']}."
            }
            examples.append(example)
        
        return examples
    
    async def _generate_key_insights(self, analysis: CodeAnalysis, angle: Dict[str, Any]) -> List[str]:
        """Generate key insights that would impress hiring managers"""
        
        prompt = f"""Based on this code analysis and article angle, generate 5-7 key insights that would impress hiring managers:
        
        Code Analysis:
        - Patterns: {analysis.patterns}
        - Complexity: {analysis.complexity_score}
        - Coverage: {analysis.test_coverage}%
        - Dependencies: {analysis.dependencies[:5]}
        
        Article Focus:
        {angle['insights']}
        
        Generate insights that show:
        1. Technical depth and modern practices
        2. System thinking and architecture skills
        3. Performance and scalability awareness
        4. Testing and quality focus
        5. Business impact understanding
        
        Format as bullet points focusing on what the candidate learned/achieved."""
        
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=800
        )
        
        insights_text = response.choices[0].message.content
        insights = [line.strip('- ').strip() for line in insights_text.split('\n') if line.strip().startswith('-')]
        
        return insights[:7]
    
    def _generate_tags(self, analysis: CodeAnalysis, platform: Platform) -> List[str]:
        """Generate relevant tags based on analysis and platform"""
        tags = []
        
        # Add pattern-based tags
        pattern_tags = {
            'microservices': ['microservices', 'architecture', 'distributed'],
            'kubernetes': ['kubernetes', 'k8s', 'devops', 'containerization'],
            'async_programming': ['async', 'python', 'performance'],
            'rest_api': ['api', 'fastapi', 'backend'],
            'testing': ['testing', 'pytest', 'quality'],
            'observability': ['monitoring', 'prometheus', 'observability']
        }
        
        for pattern in analysis.patterns:
            if pattern in pattern_tags:
                tags.extend(pattern_tags[pattern])
        
        # Add dependency-based tags
        dep_tags = {
            'fastapi': ['fastapi', 'python', 'api'],
            'kubernetes': ['kubernetes', 'k8s'],
            'prometheus': ['monitoring', 'metrics'],
            'celery': ['async', 'background-jobs'],
            'openai': ['ai', 'llm', 'gpt']
        }
        
        for dep in analysis.dependencies:
            dep_lower = dep.lower()
            for key, dep_tag_list in dep_tags.items():
                if key in dep_lower:
                    tags.extend(dep_tag_list)
        
        # Add platform-specific tags
        platform_tags = {
            Platform.DEVTO: ['python', 'tutorial', 'beginners'],
            Platform.LINKEDIN: ['leadership', 'engineering', 'career'],
            Platform.TWITTER: ['tech', 'coding', 'tips']
        }
        
        tags.extend(platform_tags.get(platform, []))
        
        # Remove duplicates and limit
        unique_tags = list(set(tags))
        return unique_tags[:8]
    
    def _estimate_read_time(self, content: str) -> int:
        """Estimate reading time in minutes"""
        words = len(content.split())
        # Average reading speed: 200-250 words per minute
        return max(1, round(words / 225))
    
    def _generate_platform_specific_content(self, platform: Platform, content: str) -> Dict[Platform, Dict[str, Any]]:
        """Generate platform-specific content variations"""
        platform_content = {}
        
        if platform == Platform.DEVTO:
            platform_content[platform] = {
                "canonical_url": None,
                "series": None,
                "cover_image": None
            }
        elif platform == Platform.LINKEDIN:
            platform_content[platform] = {
                "post_type": "article",
                "include_pdf": False
            }
        elif platform == Platform.TWITTER:
            platform_content[platform] = {
                "thread_count": self._estimate_thread_length(content),
                "include_images": True
            }
        
        return platform_content
    
    def _estimate_thread_length(self, content: str) -> int:
        """Estimate how many tweets needed for thread"""
        words = len(content.split())
        # Rough estimate: ~25 words per tweet accounting for formatting
        return max(1, round(words / 25))
    
    def _select_optimal_style(self, article_type: ArticleType, platform: Platform) -> str:
        """Select optimal content style based on article type and platform"""
        
        style_matrix = {
            (ArticleType.ARCHITECTURE, Platform.DEVTO): "technical_deep_dive",
            (ArticleType.ARCHITECTURE, Platform.LINKEDIN): "architecture_showcase",
            (ArticleType.TUTORIAL, Platform.DEVTO): "learning_journey",
            (ArticleType.TUTORIAL, Platform.LINKEDIN): "problem_solving_story",
            (ArticleType.PERFORMANCE, Platform.DEVTO): "technical_deep_dive",
            (ArticleType.PERFORMANCE, Platform.TWITTER): "war_stories",
            (ArticleType.PROBLEM_SOLUTION, Platform.LINKEDIN): "problem_solving_story",
            (ArticleType.PROBLEM_SOLUTION, Platform.TWITTER): "war_stories",
        }
        
        return style_matrix.get((article_type, platform), "technical_deep_dive")
    
    async def generate_content_variations(
        self,
        base_content: ArticleContent,
        target_platforms: List[Platform]
    ) -> Dict[Platform, ArticleContent]:
        """Generate variations of content optimized for different platforms"""
        
        variations = {}
        
        for platform in target_platforms:
            if platform == base_content.platform_specific:
                variations[platform] = base_content
                continue
            
            # Generate platform-specific variation
            variation = await self._adapt_content_for_platform(base_content, platform)
            variations[platform] = variation
        
        return variations
    
    async def _adapt_content_for_platform(
        self,
        base_content: ArticleContent,
        target_platform: Platform
    ) -> ArticleContent:
        """Adapt content for a specific platform"""
        
        # This would generate platform-specific versions
        # For now, return adapted version with platform-specific formatting
        
        adapted_content = ArticleContent(
            title=base_content.title,
            subtitle=base_content.subtitle,
            content=base_content.content,
            tags=self._adapt_tags_for_platform(base_content.tags, target_platform),
            estimated_read_time=base_content.estimated_read_time,
            code_examples=base_content.code_examples,
            insights=base_content.insights,
            platform_specific=self._generate_platform_specific_content(target_platform, base_content.content)
        )
        
        return adapted_content
    
    def _adapt_tags_for_platform(self, tags: List[str], platform: Platform) -> List[str]:
        """Adapt tags for specific platform requirements"""
        
        platform_limits = {
            Platform.DEVTO: 4,
            Platform.LINKEDIN: 10,
            Platform.TWITTER: 3
        }
        
        limit = platform_limits.get(platform, 8)
        return tags[:limit]