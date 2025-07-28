"""Multi-platform publisher infrastructure for achievements."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

from ..core.logging import setup_logging

logger = setup_logging(__name__)


class PlatformPublisher(ABC):
    """Abstract base class for platform publishers."""

    @abstractmethod
    async def prepare_content(self, achievement: Dict) -> Dict:
        """Prepare platform-specific content from achievement data."""
        pass

    @abstractmethod
    async def validate_content(self, content: Dict) -> bool:
        """Validate content meets platform requirements."""
        pass

    @abstractmethod
    async def publish(self, content: Dict) -> Dict:
        """Publish content to platform."""
        pass

    @abstractmethod
    async def get_analytics(self, post_id: str) -> Dict:
        """Get post analytics from platform."""
        pass


class LinkedInPublisher(PlatformPublisher):
    """LinkedIn publisher for professional achievements."""

    def __init__(self):
        self.api_key = None  # Will be configured later
        self.person_urn = None

    async def prepare_content(self, achievement: Dict) -> Dict:
        """Prepare LinkedIn-optimized content."""

        # Select best story for LinkedIn (professional audience)
        best_story = self._select_professional_story(achievement.get("stories", {}))

        content = {
            "text": self._format_linkedin_post(achievement, best_story),
            "media": self._prepare_media(achievement),
            "hashtags": self._generate_hashtags(achievement),
            "visibility": "PUBLIC",
            "metadata": {
                "achievement_id": achievement.get("id"),
                "story_type": best_story.get("type") if best_story else None,
                "target_audience": "professional",
            },
        }

        return content

    def _format_linkedin_post(self, achievement: Dict, story: Dict) -> str:
        """Format achievement as LinkedIn post."""

        # LinkedIn post structure
        sections = []

        # Hook - attention grabber
        if story and story.get("summary"):
            sections.append(f"🚀 {story['summary']}")
        else:
            sections.append(f"🚀 {achievement['metadata']['title']}")

        # Context
        sections.append("")
        if story and story.get("full_story"):
            # Take first 2-3 sentences
            sentences = story["full_story"].split(". ")[:3]
            sections.append(". ".join(sentences) + ".")

        # Key metrics (bullet points)
        sections.append("")
        sections.append("Key achievements:")

        metrics = self._extract_key_metrics(achievement)
        for metric in metrics[:5]:  # Limit to 5 metrics
            sections.append(f"• {metric}")

        # Skills demonstrated
        sections.append("")
        skills = achievement.get("code_metrics", {}).get("languages", {})
        if skills:
            sections.append(f"Technologies: {', '.join(list(skills.keys())[:5])}")

        # Call to action
        sections.append("")
        sections.append(
            "What performance improvements have you achieved recently? Share below! 💬"
        )

        return "\n".join(sections)

    def _extract_key_metrics(self, achievement: Dict) -> List[str]:
        """Extract key metrics for LinkedIn post."""
        metrics = []

        # Performance metrics
        perf = achievement.get("performance_metrics", {})
        if perf.get("latency_changes", {}).get("reported"):
            lat = perf["latency_changes"]["reported"]
            metrics.append(f"{lat['improvement_percentage']:.0f}% latency reduction")

        # Business metrics
        biz = achievement.get("business_metrics", {})
        if biz.get("financial_impact", {}).get("cost_savings"):
            savings = biz["financial_impact"]["cost_savings"]
            metrics.append(f"${savings:,.0f} annual cost savings")

        # Code metrics
        code = achievement.get("code_metrics", {})
        if code.get("total_lines_added", 0) > 100:
            metrics.append(f"{code['files_changed']} files optimized")

        # Team metrics
        team = achievement.get("team_metrics", {})
        if team.get("collaboration", {}).get("reviewers_count", 0) > 2:
            metrics.append(
                f"Collaborated with {team['collaboration']['reviewers_count']} team members"
            )

        # Quality metrics
        quality = achievement.get("quality_metrics", {})
        if quality.get("test_coverage", {}).get("delta", 0) > 5:
            metrics.append(
                f"{quality['test_coverage']['delta']:.0f}% test coverage increase"
            )

        return metrics

    def _generate_hashtags(self, achievement: Dict) -> List[str]:
        """Generate relevant hashtags."""
        hashtags = ["#SoftwareEngineering", "#TechLeadership"]

        # Add language-specific tags
        languages = achievement.get("code_metrics", {}).get("languages", {})
        for lang in list(languages.keys())[:3]:
            hashtags.append(f"#{lang}")

        # Add topic-specific tags
        if achievement.get("performance_metrics"):
            hashtags.append("#PerformanceOptimization")

        if achievement.get("business_metrics", {}).get("financial_impact"):
            hashtags.append("#BusinessImpact")

        if achievement.get("architectural_metrics"):
            hashtags.append("#SoftwareArchitecture")

        return hashtags[:10]  # LinkedIn recommends max 10 hashtags

    async def validate_content(self, content: Dict) -> bool:
        """Validate LinkedIn content requirements."""
        text = content.get("text", "")

        # LinkedIn limits
        if len(text) > 3000:
            logger.warning(f"LinkedIn post too long: {len(text)} chars")
            return False

        if len(content.get("hashtags", [])) > 10:
            logger.warning("Too many hashtags for LinkedIn")
            return False

        return True

    async def publish(self, content: Dict) -> Dict:
        """Mock publish to LinkedIn."""
        # In production, would use LinkedIn API
        logger.info("Mock publishing to LinkedIn")

        return {
            "success": True,
            "post_id": f"linkedin_mock_{datetime.now().timestamp()}",
            "url": "https://linkedin.com/posts/mock-post",
            "published_at": datetime.now().isoformat(),
        }

    async def get_analytics(self, post_id: str) -> Dict:
        """Mock get LinkedIn analytics."""
        return {
            "views": 1250,
            "likes": 89,
            "comments": 12,
            "shares": 5,
            "engagement_rate": 0.085,
        }

    def _select_professional_story(self, stories: Dict) -> Optional[Dict]:
        """Select best story for professional audience."""
        priority_order = [
            "business",
            "leadership",
            "architecture",
            "performance",
            "feature",
        ]

        for story_type in priority_order:
            if story_type in stories:
                return stories[story_type]

        return None

    def _prepare_media(self, achievement: Dict) -> List[Dict]:
        """Prepare media attachments."""
        media = []

        evidence = achievement.get("evidence", {})

        # Performance graphs
        if evidence.get("performance_graphs"):
            media.append(
                {
                    "type": "image",
                    "url": evidence["performance_graphs"][0],
                    "title": "Performance Improvements",
                }
            )

        # Architecture diagrams
        if evidence.get("architecture_diagrams"):
            media.append(
                {
                    "type": "image",
                    "url": evidence["architecture_diagrams"][0],
                    "title": "System Architecture",
                }
            )

        return media[:4]  # LinkedIn allows max 4 images


class TwitterPublisher(PlatformPublisher):
    """Twitter/X publisher for achievements."""

    async def prepare_content(self, achievement: Dict) -> Dict:
        """Prepare Twitter thread from achievement."""

        thread = self._create_thread(achievement)

        return {
            "thread": thread,
            "media": self._prepare_media_for_twitter(achievement),
            "hashtags": self._generate_twitter_hashtags(achievement),
            "metadata": {
                "achievement_id": achievement.get("id"),
                "thread_length": len(thread),
            },
        }

    def _create_thread(self, achievement: Dict) -> List[str]:
        """Create Twitter thread from achievement."""
        thread = []

        # Tweet 1: Hook
        story = self._get_most_impactful_story(achievement.get("stories", {}))
        if story:
            hook = f"🧵 {story['summary']}"
        else:
            hook = f"🧵 Just shipped: {achievement['metadata']['title']}"
        thread.append(self._fit_to_tweet(hook))

        # Tweet 2: Problem/Context
        context = "The challenge: " + self._extract_problem_statement(achievement)
        thread.append(self._fit_to_tweet(context))

        # Tweet 3-4: Solution & Metrics
        metrics = self._extract_top_metrics(achievement, limit=3)
        solution = "Results:\n" + "\n".join(f"→ {m}" for m in metrics)
        thread.append(self._fit_to_tweet(solution))

        # Tweet 5: Technical details (for tech audience)
        tech_details = self._extract_technical_highlights(achievement)
        if tech_details:
            tech_tweet = "Technical approach:\n" + "\n".join(
                f"• {d}" for d in tech_details[:3]
            )
            thread.append(self._fit_to_tweet(tech_tweet))

        # Final tweet: Takeaway
        takeaway = self._generate_takeaway(achievement)
        thread.append(self._fit_to_tweet(takeaway))

        return thread

    def _fit_to_tweet(self, text: str, max_length: int = 280) -> str:
        """Fit text to tweet length."""
        if len(text) <= max_length:
            return text

        # Smart truncation
        return text[: max_length - 3] + "..."

    def _generate_twitter_hashtags(self, achievement: Dict) -> List[str]:
        """Generate hashtags for Twitter."""
        # More trendy, shorter hashtags for Twitter
        hashtags = []

        if achievement.get("performance_metrics"):
            hashtags.append("#PerfMatters")

        languages = achievement.get("code_metrics", {}).get("languages", {})
        if "Python" in languages:
            hashtags.append("#Python")
        if "JavaScript" in languages:
            hashtags.append("#JavaScript")

        if achievement.get("innovation_metrics"):
            hashtags.append("#Innovation")

        hashtags.extend(["#CodeNewbie", "#100DaysOfCode", "#BuildInPublic"])

        return hashtags[:5]  # Fewer hashtags on Twitter

    async def validate_content(self, content: Dict) -> bool:
        """Validate Twitter content."""
        thread = content.get("thread", [])

        for tweet in thread:
            if len(tweet) > 280:
                logger.warning(f"Tweet too long: {len(tweet)} chars")
                return False

        if len(thread) > 10:
            logger.warning("Thread too long for Twitter")
            return False

        return True

    async def publish(self, content: Dict) -> Dict:
        """Mock publish to Twitter."""
        logger.info("Mock publishing to Twitter")

        return {
            "success": True,
            "thread_id": f"twitter_mock_{datetime.now().timestamp()}",
            "tweets": [
                {"id": f"tweet_{i}", "url": f"https://twitter.com/mock/status/{i}"}
                for i in range(len(content["thread"]))
            ],
            "published_at": datetime.now().isoformat(),
        }

    async def get_analytics(self, post_id: str) -> Dict:
        """Mock Twitter analytics."""
        return {
            "impressions": 5420,
            "likes": 234,
            "retweets": 45,
            "replies": 23,
            "engagement_rate": 0.056,
        }

    def _get_most_impactful_story(self, stories: Dict) -> Optional[Dict]:
        """Get story with highest impact for Twitter."""
        if not stories:
            return None

        # Twitter prefers performance and innovation stories
        priority = ["performance", "innovation", "feature", "business"]

        for story_type in priority:
            if story_type in stories:
                return stories[story_type]

        return list(stories.values())[0]

    def _extract_problem_statement(self, achievement: Dict) -> str:
        """Extract problem that was solved."""
        # Would use AI to extract from PR description
        return "Optimizing system performance for scale"

    def _extract_top_metrics(self, achievement: Dict, limit: int = 3) -> List[str]:
        """Extract top metrics for Twitter."""
        metrics = []

        # Performance improvements get priority on Twitter
        perf = achievement.get("performance_metrics", {})
        if perf.get("latency_changes", {}).get("reported"):
            lat = perf["latency_changes"]["reported"]
            metrics.append(
                f"{lat['improvement_percentage']:.0f}% faster response times"
            )

        # Code improvements
        code = achievement.get("code_metrics", {})
        if code.get("total_lines_deleted", 0) > code.get("total_lines_added", 0):
            reduction = code["total_lines_deleted"] - code["total_lines_added"]
            metrics.append(f"{reduction} lines of code removed")

        # Test coverage
        quality = achievement.get("quality_metrics", {})
        if quality.get("test_coverage", {}).get("after", 0) > 90:
            metrics.append(f"{quality['test_coverage']['after']:.0f}% test coverage")

        return metrics[:limit]

    def _extract_technical_highlights(self, achievement: Dict) -> List[str]:
        """Extract technical highlights for Twitter tech audience."""
        highlights = []

        # Architecture improvements
        arch = achievement.get("architectural_metrics", {})
        if arch.get("patterns_implemented", {}).get("design_patterns"):
            patterns = arch["patterns_implemented"]["design_patterns"]
            highlights.append(f"Implemented {', '.join(patterns[:2])}")

        # Technology used
        languages = list(
            achievement.get("code_metrics", {}).get("languages", {}).keys()
        )
        if languages:
            highlights.append(f"Built with {', '.join(languages[:3])}")

        return highlights

    def _generate_takeaway(self, achievement: Dict) -> str:
        """Generate takeaway message."""
        # Would use AI to generate insightful takeaway
        return "Key lesson: Performance optimization is about understanding your bottlenecks, not premature optimization. Measure first, optimize second. 📊"

    def _prepare_media_for_twitter(self, achievement: Dict) -> List[Dict]:
        """Prepare media for Twitter."""
        # Twitter allows 4 images per tweet
        return achievement.get("evidence", {}).get("screenshots", [])[:4]


class DevToPublisher(PlatformPublisher):
    """Dev.to publisher for technical articles."""

    async def prepare_content(self, achievement: Dict) -> Dict:
        """Prepare dev.to article from achievement."""

        article = {
            "title": self._generate_article_title(achievement),
            "body_markdown": self._generate_article_body(achievement),
            "tags": self._generate_dev_tags(achievement),
            "series": self._determine_series(achievement),
            "cover_image": self._select_cover_image(achievement),
            "metadata": {
                "achievement_id": achievement.get("id"),
                "reading_time": self._estimate_reading_time(achievement),
            },
        }

        return article

    def _generate_article_title(self, achievement: Dict) -> str:
        """Generate engaging technical article title."""
        # Would use AI to generate engaging title
        perf = achievement.get("performance_metrics", {})
        if perf.get("latency_changes", {}).get("reported"):
            improvement = perf["latency_changes"]["reported"]["improvement_percentage"]
            return f"How I Reduced API Latency by {improvement:.0f}% with These 3 Optimizations"

        return f"Lessons from {achievement['metadata']['title']}"

    def _generate_article_body(self, achievement: Dict) -> str:
        """Generate full technical article."""
        sections = []

        # Introduction
        sections.append("## The Challenge\n")
        sections.append(self._generate_problem_description(achievement))

        # Technical approach
        sections.append("\n## The Solution\n")
        sections.append(self._generate_technical_approach(achievement))

        # Code examples
        if achievement.get("code_analysis", {}).get("key_changes"):
            sections.append("\n## Code Deep Dive\n")
            sections.append(self._generate_code_examples(achievement))

        # Results
        sections.append("\n## Results\n")
        sections.append(self._generate_results_section(achievement))

        # Lessons learned
        sections.append("\n## Key Takeaways\n")
        sections.append(self._generate_lessons_learned(achievement))

        return "\n".join(sections)

    def _generate_dev_tags(self, achievement: Dict) -> List[str]:
        """Generate dev.to tags."""
        tags = []

        # Language tags
        languages = achievement.get("code_metrics", {}).get("languages", {})
        for lang in list(languages.keys())[:2]:
            tags.append(lang.lower())

        # Topic tags
        if achievement.get("performance_metrics"):
            tags.append("performance")

        if achievement.get("architectural_metrics"):
            tags.append("architecture")

        tags.append("programming")

        return tags[:4]  # Dev.to allows max 4 tags

    async def validate_content(self, content: Dict) -> bool:
        """Validate dev.to content."""
        # Dev.to has generous limits
        return True

    async def publish(self, content: Dict) -> Dict:
        """Mock publish to dev.to."""
        logger.info("Mock publishing to dev.to")

        return {
            "success": True,
            "article_id": f"devto_mock_{datetime.now().timestamp()}",
            "url": "https://dev.to/mock/article",
            "published_at": datetime.now().isoformat(),
        }

    async def get_analytics(self, post_id: str) -> Dict:
        """Mock dev.to analytics."""
        return {
            "views": 3420,
            "reactions": 234,
            "comments": 45,
            "reading_time": 8,
            "saves": 123,
        }

    def _determine_series(self, achievement: Dict) -> Optional[str]:
        """Determine if article belongs to a series."""
        # Could be "Performance Optimization Series", "Architecture Decisions", etc.
        return None

    def _select_cover_image(self, achievement: Dict) -> Optional[str]:
        """Select cover image for article."""
        evidence = achievement.get("evidence", {})

        # Prefer architecture diagrams for dev.to
        if evidence.get("architecture_diagrams"):
            return evidence["architecture_diagrams"][0]

        # Then performance graphs
        if evidence.get("performance_graphs"):
            return evidence["performance_graphs"][0]

        return None

    def _estimate_reading_time(self, achievement: Dict) -> int:
        """Estimate reading time in minutes."""
        # Rough estimate based on content
        return 5

    def _generate_problem_description(self, achievement: Dict) -> str:
        """Generate problem description for article."""
        return "Every developer faces performance challenges..."

    def _generate_technical_approach(self, achievement: Dict) -> str:
        """Generate technical approach section."""
        return (
            "After analyzing the bottlenecks, I implemented three key optimizations..."
        )

    def _generate_code_examples(self, achievement: Dict) -> str:
        """Generate code examples section."""
        return "```python\n# Before optimization\n...\n# After optimization\n...\n```"

    def _generate_results_section(self, achievement: Dict) -> str:
        """Generate results section with metrics."""
        return "The optimizations resulted in significant improvements across all metrics..."

    def _generate_lessons_learned(self, achievement: Dict) -> str:
        """Generate lessons learned section."""
        return "1. Always measure before optimizing\n2. ..."


class GitHubProfilePublisher(PlatformPublisher):
    """GitHub profile README publisher."""

    async def prepare_content(self, achievement: Dict) -> Dict:
        """Prepare GitHub profile update."""

        return {
            "readme_section": self._generate_readme_section(achievement),
            "gist": self._prepare_detailed_gist(achievement),
            "metadata": {
                "achievement_id": achievement.get("id"),
                "update_type": "recent_achievement",
            },
        }

    def _generate_readme_section(self, achievement: Dict) -> str:
        """Generate README section for achievement."""
        # This would update the "Recent Achievements" section

        metrics = self._extract_key_metrics_for_github(achievement)

        section = f"""
### 🏆 Recent Achievement: {achievement["metadata"]["title"]}

{achievement["metadata"]["description"][:200]}...

**Impact:**
{chr(10).join(f"- {metric}" for metric in metrics[:3])}

[View Details](gist_url_here) | [View PR](pr_url_here)
"""
        return section

    def _prepare_detailed_gist(self, achievement: Dict) -> Dict:
        """Prepare detailed gist with full achievement data."""

        return {
            "filename": f"achievement_{achievement['id']}.md",
            "content": self._generate_gist_content(achievement),
            "description": f"Achievement: {achievement['metadata']['title']}",
        }

    def _extract_key_metrics_for_github(self, achievement: Dict) -> List[str]:
        """Extract metrics suitable for GitHub profile."""
        metrics = []

        # Code metrics are most relevant for GitHub
        code = achievement.get("code_metrics", {})
        if code.get("files_changed"):
            metrics.append(f"Optimized {code['files_changed']} files")

        # Test coverage
        quality = achievement.get("quality_metrics", {})
        if quality.get("test_coverage", {}).get("after"):
            metrics.append(f"{quality['test_coverage']['after']:.0f}% test coverage")

        # Performance
        perf = achievement.get("performance_metrics", {})
        if perf.get("latency_changes", {}).get("reported"):
            improvement = perf["latency_changes"]["reported"]["improvement_percentage"]
            metrics.append(f"{improvement:.0f}% performance improvement")

        return metrics

    def _generate_gist_content(self, achievement: Dict) -> str:
        """Generate detailed gist content."""
        # Would include full metrics, code examples, learnings
        return f"# {achievement['metadata']['title']}\n\nDetailed achievement documentation..."

    async def validate_content(self, content: Dict) -> bool:
        """Validate GitHub content."""
        return True

    async def publish(self, content: Dict) -> Dict:
        """Mock publish to GitHub."""
        logger.info("Mock publishing to GitHub profile")

        return {
            "success": True,
            "gist_id": f"github_gist_mock_{datetime.now().timestamp()}",
            "profile_updated": True,
            "published_at": datetime.now().isoformat(),
        }

    async def get_analytics(self, post_id: str) -> Dict:
        """Mock GitHub analytics."""
        return {"gist_views": 234, "gist_clones": 12, "profile_views": 1420}


class PortfolioWebsitePublisher(PlatformPublisher):
    """Personal portfolio website publisher."""

    async def prepare_content(self, achievement: Dict) -> Dict:
        """Prepare portfolio entry."""

        return {
            "project": self._create_portfolio_project(achievement),
            "case_study": self._create_case_study(achievement),
            "metadata": {
                "achievement_id": achievement.get("id"),
                "category": self._determine_portfolio_category(achievement),
                "featured": self._should_feature(achievement),
            },
        }

    def _create_portfolio_project(self, achievement: Dict) -> Dict:
        """Create portfolio project entry."""

        return {
            "title": achievement["metadata"]["title"],
            "summary": self._generate_portfolio_summary(achievement),
            "technologies": list(
                achievement.get("code_metrics", {}).get("languages", {}).keys()
            ),
            "metrics": self._extract_portfolio_metrics(achievement),
            "images": achievement.get("evidence", {}).get("screenshots", []),
            "links": {
                "github": achievement.get("metadata", {}).get("pr_url"),
                "live": None,
                "case_study": f"/case-studies/{achievement['id']}",
            },
            "date": achievement.get("metadata", {}).get("merged_at"),
            "featured": self._should_feature(achievement),
        }

    def _create_case_study(self, achievement: Dict) -> Dict:
        """Create detailed case study."""

        return {
            "title": f"Case Study: {achievement['metadata']['title']}",
            "hero_image": self._select_hero_image(achievement),
            "sections": [
                {"type": "overview", "content": self._generate_overview(achievement)},
                {
                    "type": "challenge",
                    "content": self._generate_challenge_section(achievement),
                },
                {
                    "type": "solution",
                    "content": self._generate_solution_section(achievement),
                },
                {
                    "type": "results",
                    "content": self._generate_results_with_visuals(achievement),
                },
                {
                    "type": "technical_deep_dive",
                    "content": self._generate_technical_details(achievement),
                },
                {
                    "type": "lessons_learned",
                    "content": self._generate_portfolio_lessons(achievement),
                },
            ],
        }

    def _generate_portfolio_summary(self, achievement: Dict) -> str:
        """Generate portfolio-appropriate summary."""
        # Professional, outcome-focused summary
        return "Optimized critical system performance resulting in 75% latency reduction..."

    def _extract_portfolio_metrics(self, achievement: Dict) -> List[Dict]:
        """Extract metrics for portfolio display."""
        metrics = []

        # Format metrics for visual display
        perf = achievement.get("performance_metrics", {})
        if perf.get("latency_changes", {}).get("reported"):
            metrics.append(
                {
                    "label": "Performance Gain",
                    "value": f"{perf['latency_changes']['reported']['improvement_percentage']:.0f}%",
                    "icon": "rocket",
                }
            )

        biz = achievement.get("business_metrics", {})
        if biz.get("financial_impact", {}).get("cost_savings"):
            metrics.append(
                {
                    "label": "Cost Savings",
                    "value": f"${biz['financial_impact']['cost_savings']:,.0f}",
                    "icon": "dollar",
                }
            )

        return metrics

    def _should_feature(self, achievement: Dict) -> bool:
        """Determine if achievement should be featured."""
        # Feature high-impact achievements
        scores = achievement.get("composite_scores", {})
        return scores.get("overall_impact", 0) > 80

    def _determine_portfolio_category(self, achievement: Dict) -> str:
        """Determine portfolio category."""
        # Categories: Performance, Architecture, Features, Infrastructure

        if achievement.get("performance_metrics"):
            return "performance"
        elif achievement.get("architectural_metrics"):
            return "architecture"
        elif achievement.get("metadata", {}).get("is_feature"):
            return "features"
        else:
            return "infrastructure"

    def _select_hero_image(self, achievement: Dict) -> Optional[str]:
        """Select hero image for case study."""
        evidence = achievement.get("evidence", {})

        # Prefer architecture diagrams
        if evidence.get("architecture_diagrams"):
            return evidence["architecture_diagrams"][0]

        # Then screenshots
        if evidence.get("screenshots"):
            return evidence["screenshots"][0]

        return None

    def _generate_overview(self, achievement: Dict) -> str:
        """Generate case study overview."""
        return "This case study details the optimization of..."

    def _generate_challenge_section(self, achievement: Dict) -> str:
        """Generate challenge section."""
        return "The system was experiencing performance degradation..."

    def _generate_solution_section(self, achievement: Dict) -> str:
        """Generate solution section."""
        return "After thorough analysis, I implemented a multi-pronged approach..."

    def _generate_results_with_visuals(self, achievement: Dict) -> Dict:
        """Generate results section with visual elements."""
        return {
            "text": "The optimizations delivered significant improvements...",
            "graphs": achievement.get("evidence", {}).get("performance_graphs", []),
            "metrics_grid": self._extract_portfolio_metrics(achievement),
        }

    def _generate_technical_details(self, achievement: Dict) -> str:
        """Generate technical deep dive."""
        return "The technical implementation involved..."

    def _generate_portfolio_lessons(self, achievement: Dict) -> str:
        """Generate lessons learned for portfolio."""
        return "This project reinforced several key principles..."

    async def validate_content(self, content: Dict) -> bool:
        """Validate portfolio content."""
        return True

    async def publish(self, content: Dict) -> Dict:
        """Mock publish to portfolio."""
        logger.info("Mock publishing to portfolio website")

        return {
            "success": True,
            "project_id": f"portfolio_mock_{datetime.now().timestamp()}",
            "case_study_url": f"https://portfolio.com/case-studies/{content['metadata']['achievement_id']}",
            "published_at": datetime.now().isoformat(),
        }

    async def get_analytics(self, post_id: str) -> Dict:
        """Mock portfolio analytics."""
        return {
            "page_views": 543,
            "unique_visitors": 234,
            "avg_time_on_page": 145,  # seconds
            "conversion_rate": 0.034,  # Contact form submissions
        }


class MultiPlatformOrchestrator:
    """Orchestrate publishing across multiple platforms."""

    def __init__(self):
        self.publishers = {
            "linkedin": LinkedInPublisher(),
            "twitter": TwitterPublisher(),
            "devto": DevToPublisher(),
            "github": GitHubProfilePublisher(),
            "portfolio": PortfolioWebsitePublisher(),
        }

    async def prepare_all_content(self, achievement: Dict) -> Dict:
        """Prepare content for all platforms."""

        prepared_content = {}

        for platform, publisher in self.publishers.items():
            try:
                content = await publisher.prepare_content(achievement)
                if await publisher.validate_content(content):
                    prepared_content[platform] = content
                else:
                    logger.warning(f"Content validation failed for {platform}")
            except Exception as e:
                logger.error(f"Error preparing content for {platform}: {e}")

        return prepared_content

    async def publish_to_platforms(
        self, achievement: Dict, platforms: List[str] = None
    ) -> Dict:
        """Publish to specified platforms or all."""

        if platforms is None:
            platforms = list(self.publishers.keys())

        results = {}

        # Prepare content first
        prepared_content = await self.prepare_all_content(achievement)

        # Publish to each platform
        for platform in platforms:
            if platform in prepared_content:
                try:
                    result = await self.publishers[platform].publish(
                        prepared_content[platform]
                    )
                    results[platform] = result
                except Exception as e:
                    logger.error(f"Error publishing to {platform}: {e}")
                    results[platform] = {"success": False, "error": str(e)}

        return results

    async def get_cross_platform_analytics(self, achievement_id: int) -> Dict:
        """Get analytics from all platforms."""

        analytics = {}

        # Get posting metadata from database
        # For now, using mock data

        for platform, publisher in self.publishers.items():
            try:
                post_id = f"mock_{platform}_{achievement_id}"
                analytics[platform] = await publisher.get_analytics(post_id)
            except Exception as e:
                logger.error(f"Error getting analytics from {platform}: {e}")

        # Calculate aggregate metrics
        analytics["aggregate"] = {
            "total_reach": sum(
                p.get("views", 0) + p.get("impressions", 0) for p in analytics.values()
            ),
            "total_engagement": sum(
                p.get("likes", 0)
                + p.get("reactions", 0)
                + p.get("comments", 0)
                + p.get("shares", 0)
                + p.get("retweets", 0)
                for p in analytics.values()
            ),
            "avg_engagement_rate": sum(
                p.get("engagement_rate", 0) for p in analytics.values()
            )
            / len(analytics),
        }

        return analytics
