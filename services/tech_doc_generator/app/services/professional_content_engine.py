"""
Professional Content Engine for AI Job Search

Adapts the viral_engine components for professional content generation
focused on attracting AI job opportunities. Uses proven viral patterns
but adjusted for professional, authority-building tone.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
import structlog
from pydantic import BaseModel, Field

from ..core.config import get_settings
from .achievement_content_generator import ContentType, Platform

logger = structlog.get_logger()


class ProfessionalContentRequest(BaseModel):
    """Request for professional content generation"""
    achievement_id: int
    content_type: ContentType = ContentType.CASE_STUDY
    target_company: Optional[str] = None
    platform: Platform = Platform.LINKEDIN
    tone: str = "professional"  # professional, thought-leader, technical
    include_hook: bool = True
    include_metrics: bool = True


class ProfessionalContentResult(BaseModel):
    """Result from professional content generation"""
    title: str
    content: str
    hook: Optional[str] = None
    engagement_score: float = Field(..., ge=0, le=100)
    quality_score: float = Field(..., ge=0, le=100)
    platform_optimized: Platform
    recommended_hashtags: List[str] = Field(default_factory=list)
    best_posting_time: Optional[str] = None
    seo_keywords: List[str] = Field(default_factory=list)


class ProfessionalContentEngine:
    """
    Professional content engine that leverages viral_engine components
    for AI job search content generation.
    
    Key adaptations:
    - Uses authority-building hooks instead of controversial ones
    - Focuses on technical credibility and business impact
    - Optimizes for recruiter and hiring manager engagement
    - Maintains professional tone while using proven viral patterns
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.viral_engine_url = self.settings.viral_engine_url or "http://viral-engine:8000"
        self.client = None
        
        # Professional hook patterns (adapted from viral patterns)
        self.professional_patterns = {
            "technical_authority": [
                "Here's how I reduced costs by {metric}% using {technology}...",
                "Most teams struggle with {problem}. Here's my solution:",
                "3 mistakes I made implementing {technology} (and how to avoid them):",
                "After {timeframe} of {task}, here's what I learned:",
            ],
            "business_impact": [
                "This {implementation} saved us ${amount} annually:",
                "How {technology} improved our {metric} by {percentage}%:",
                "The ROI story behind our {project}:",
                "Turning {problem} into {solution}: A case study",
            ],
            "thought_leadership": [
                "Unpopular opinion: {controversial_take}",
                "The future of {field} isn't what you think:",
                "Why {common_practice} is holding your team back:",
                "What I wish I knew before becoming a {role}:",
            ],
            "problem_solving": [
                "Debugging {system} for 3 days taught me this:",
                "How to {solve_problem} without {common_solution}:",
                "The {tool} feature that saved our {metric}:",
                "When {standard_approach} fails, try this:",
            ]
        }
        
        # Company-specific adjustments
        self.company_patterns = {
            "anthropic": {
                "focus": "ai_safety, responsible_ai, llm_ethics",
                "tone": "thoughtful, research-oriented",
                "avoid": ["hype", "unrealistic_claims"]
            },
            "notion": {
                "focus": "productivity, collaboration, user_experience",
                "tone": "user-centric, efficiency-focused", 
                "avoid": ["complexity", "technical_jargon"]
            },
            "stripe": {
                "focus": "developer_experience, api_design, fintech",
                "tone": "developer-friendly, precise",
                "avoid": ["vague_benefits", "non_technical"]
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    async def generate_professional_content(
        self, 
        request: ProfessionalContentRequest,
        achievement_data: Dict[str, Any]
    ) -> ProfessionalContentResult:
        """
        Generate professional content optimized for AI job search.
        
        Flow:
        1. Analyze achievement for key metrics and technical details
        2. Generate professional hook using adapted viral patterns
        3. Create content optimized for target platform/company
        4. Validate quality and engagement potential
        5. Add SEO and platform-specific optimizations
        """
        logger.info("generating_professional_content", 
                   achievement_id=request.achievement_id,
                   platform=request.platform.value,
                   company=request.target_company)
        
        try:
            # Step 1: Extract key elements from achievement
            content_elements = self._extract_content_elements(achievement_data)
            
            # Step 2: Generate professional hook
            hook = None
            if request.include_hook:
                hook = await self._generate_professional_hook(
                    content_elements, 
                    request.target_company,
                    request.tone
                )
            
            # Step 3: Generate main content
            content = await self._generate_main_content(
                content_elements,
                request.content_type,
                request.platform,
                hook
            )
            
            # Step 4: Get engagement prediction
            engagement_score = await self._predict_engagement(content, request.platform)
            
            # Step 5: Validate quality
            quality_score = await self._validate_quality(content, request.platform)
            
            # Step 6: Generate optimizations
            optimizations = await self._generate_optimizations(
                content,
                request.platform,
                request.target_company
            )
            
            result = ProfessionalContentResult(
                title=content_elements["title"],
                content=content,
                hook=hook,
                engagement_score=engagement_score,
                quality_score=quality_score,
                platform_optimized=request.platform,
                recommended_hashtags=optimizations["hashtags"],
                best_posting_time=optimizations["posting_time"],
                seo_keywords=optimizations["keywords"]
            )
            
            logger.info("professional_content_generated", 
                       achievement_id=request.achievement_id,
                       engagement_score=engagement_score,
                       quality_score=quality_score)
            
            return result
            
        except Exception as e:
            logger.error("professional_content_generation_failed",
                        achievement_id=request.achievement_id,
                        error=str(e))
            raise
    
    def _extract_content_elements(self, achievement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key elements from achievement for content generation"""
        return {
            "title": achievement_data.get("title", ""),
            "description": achievement_data.get("description", ""),
            "business_value": achievement_data.get("business_value", ""),
            "technical_details": achievement_data.get("technical_details", {}),
            "metrics": achievement_data.get("metrics", {}),
            "impact_score": achievement_data.get("impact_score", 0),
            "skills": achievement_data.get("skills_demonstrated", []),
            "category": achievement_data.get("category", ""),
            "tags": achievement_data.get("tags", [])
        }
    
    async def _generate_professional_hook(
        self, 
        elements: Dict[str, Any], 
        target_company: Optional[str],
        tone: str
    ) -> str:
        """Generate professional hook using adapted viral patterns"""
        
        # Select appropriate pattern category based on achievement
        category = self._select_hook_category(elements, target_company, tone)
        patterns = self.professional_patterns.get(category, self.professional_patterns["technical_authority"])
        
        # Use viral engine for hook optimization (if available)
        if self.client:
            try:
                viral_request = {
                    "persona_id": "professional-ai-engineer",
                    "base_content": elements["title"],
                    "topic_category": elements["category"],
                    "target_audience": "ai_recruiters_hiring_managers",
                    "posting_time": "morning"  # Professional posting time
                }
                
                response = await self.client.post(
                    f"{self.viral_engine_url}/optimize-hook",
                    json=viral_request
                )
                
                if response.status_code == 200:
                    viral_result = response.json()
                    # Adapt viral hook for professional tone
                    return self._adapt_hook_for_professional(viral_result.get("optimized_hook", ""))
                    
            except Exception as e:
                logger.warning("viral_engine_unavailable", error=str(e))
        
        # Fallback: Use professional patterns directly
        import random
        pattern = random.choice(patterns)
        return self._fill_pattern_template(pattern, elements)
    
    def _select_hook_category(
        self, 
        elements: Dict[str, Any], 
        target_company: Optional[str],
        tone: str
    ) -> str:
        """Select appropriate hook category based on content and target"""
        
        # Business impact achievements -> business_impact hooks
        if elements.get("business_value") and any(
            metric in elements["business_value"].lower() 
            for metric in ["$", "%", "cost", "saving", "revenue"]
        ):
            return "business_impact"
        
        # Technical achievements -> technical_authority
        if elements.get("category") in ["optimization", "infrastructure", "security"]:
            return "technical_authority"
        
        # Problem-solving achievements -> problem_solving
        if any(word in elements["title"].lower() for word in ["fix", "debug", "solve", "issue"]):
            return "problem_solving"
        
        # High-impact achievements -> thought_leadership
        if elements.get("impact_score", 0) > 85:
            return "thought_leadership"
        
        return "technical_authority"  # Default
    
    def _adapt_hook_for_professional(self, viral_hook: str) -> str:
        """Adapt viral hook for professional tone"""
        # Remove overly casual/controversial elements
        professional_replacements = {
            "This will blow your mind": "Here's what I discovered",
            "You won't believe": "The results surprised me",
            "INSANE": "Remarkable",
            "🔥": "",  # Remove emojis for professional tone
            "🚀": "",
            "💯": ""
        }
        
        adapted = viral_hook
        for casual, professional in professional_replacements.items():
            adapted = adapted.replace(casual, professional)
        
        return adapted
    
    def _fill_pattern_template(self, pattern: str, elements: Dict[str, Any]) -> str:
        """Fill pattern template with achievement data"""
        replacements = {
            "{metric}": str(elements.get("impact_score", "significant")),
            "{technology}": ", ".join(elements.get("skills", ["advanced techniques"])[:2]),
            "{problem}": elements.get("category", "system challenges"),
            "{timeframe}": "months",
            "{task}": elements.get("title", "this project").lower(),
            "{percentage}": str(elements.get("impact_score", 25)),
            "{amount}": elements.get("business_value", "significant value")
        }
        
        filled = pattern
        for placeholder, value in replacements.items():
            filled = filled.replace(placeholder, str(value))
        
        return filled
    
    async def _generate_main_content(
        self,
        elements: Dict[str, Any],
        content_type: ContentType,
        platform: Platform,
        hook: Optional[str]
    ) -> str:
        """Generate main content body"""
        
        # Structure based on content type
        if content_type == ContentType.CASE_STUDY:
            content = self._generate_case_study(elements, hook)
        elif content_type == ContentType.TECHNICAL_BLOG:
            content = self._generate_technical_blog(elements, hook)
        elif content_type == ContentType.LINKEDIN_POST:
            content = self._generate_linkedin_post(elements, hook)
        else:
            content = self._generate_default_content(elements, hook)
        
        # Platform-specific optimizations
        return self._optimize_for_platform(content, platform)
    
    def _generate_case_study(self, elements: Dict[str, Any], hook: Optional[str]) -> str:
        """Generate case study format content"""
        sections = []
        
        if hook:
            sections.append(hook)
        
        sections.extend([
            f"## The Challenge\n{elements['description']}",
            f"## The Solution\n{elements['title']}",
            f"## The Impact\n{elements['business_value']}",
            f"## Technical Implementation\n{self._format_technical_details(elements['technical_details'])}",
            f"## Results & Metrics\n{self._format_metrics(elements['metrics'])}",
            f"## Key Learnings\n{self._generate_learnings(elements)}"
        ])
        
        return "\n\n".join(sections)
    
    def _generate_technical_blog(self, elements: Dict[str, Any], hook: Optional[str]) -> str:
        """Generate technical blog format"""
        sections = []
        
        if hook:
            sections.append(hook)
        
        sections.extend([
            f"# {elements['title']}",
            f"## Overview\n{elements['description']}",
            f"## Technical Deep Dive\n{self._format_technical_details(elements['technical_details'])}",
            f"## Performance Impact\n{self._format_metrics(elements['metrics'])}",
            f"## Best Practices\n{self._generate_best_practices(elements)}",
            f"## Conclusion\n{elements['business_value']}"
        ])
        
        return "\n\n".join(sections)
    
    def _generate_linkedin_post(self, elements: Dict[str, Any], hook: Optional[str]) -> str:
        """Generate LinkedIn post format (shorter, more engaging)"""
        parts = []
        
        if hook:
            parts.append(hook)
        
        parts.extend([
            f"📊 Results: {elements['business_value']}",
            f"🔧 Tech Stack: {', '.join(elements['skills'][:3])}",
            f"💡 Key insight: {self._generate_key_insight(elements)}",
            "",
            "#AI #MachineLearning #Engineering #TechLeadership"
        ])
        
        return "\n\n".join(parts)
    
    def _generate_default_content(self, elements: Dict[str, Any], hook: Optional[str]) -> str:
        """Generate default content format"""
        parts = []
        
        if hook:
            parts.append(hook)
        
        parts.extend([
            elements['title'],
            elements['description'],
            f"Impact: {elements['business_value']}",
            f"Technologies: {', '.join(elements['skills'])}"
        ])
        
        return "\n\n".join(parts)
    
    def _optimize_for_platform(self, content: str, platform: Platform) -> str:
        """Apply platform-specific optimizations"""
        if platform == Platform.LINKEDIN:
            # LinkedIn prefers shorter paragraphs and emojis
            content = content.replace("\n\n", "\n\n🔹 ")
        elif platform == Platform.MEDIUM:
            # Medium likes longer-form content with subheadings
            content = content.replace("##", "###")
        elif platform == Platform.DEVTO:
            # Dev.to prefers technical focus
            content = f"```yaml\ndev.to: true\npublished: true\ntags: [ai, engineering, tutorial]\n```\n\n{content}"
        
        return content
    
    async def _predict_engagement(self, content: str, platform: Platform) -> float:
        """Predict engagement using viral engine"""
        if not self.client:
            return 75.0  # Default score
        
        try:
            response = await self.client.post(
                f"{self.viral_engine_url}/predict-engagement",
                json={"content": content}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("predicted_engagement_rate", 75.0) * 100
        except Exception as e:
            logger.warning("engagement_prediction_failed", error=str(e))
        
        return 75.0  # Fallback
    
    async def _validate_quality(self, content: str, platform: Platform) -> float:
        """Validate content quality using viral engine quality gate"""
        if not self.client:
            return 80.0  # Default score
        
        try:
            response = await self.client.post(
                f"{self.viral_engine_url}/quality-gate",
                json={"content": content}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("quality_score", 80.0) * 100
        except Exception as e:
            logger.warning("quality_validation_failed", error=str(e))
        
        return 80.0  # Fallback
    
    async def _generate_optimizations(
        self, 
        content: str, 
        platform: Platform,
        target_company: Optional[str]
    ) -> Dict[str, Any]:
        """Generate platform and company-specific optimizations"""
        
        # Base hashtags for AI/ML content
        hashtags = ["#AI", "#MachineLearning", "#Engineering", "#TechLeadership"]
        
        # Platform-specific hashtags
        if platform == Platform.LINKEDIN:
            hashtags.extend(["#LinkedIn", "#CareerGrowth", "#Innovation"])
        elif platform == Platform.DEVTO:
            hashtags.extend(["#DevCommunity", "#Programming", "#Tutorial"])
        elif platform == Platform.MEDIUM:
            hashtags.extend(["#Technology", "#DataScience", "#SoftwareDevelopment"])
        
        # Company-specific hashtags
        if target_company:
            company_hashtags = {
                "anthropic": ["#AIEthics", "#ResponsibleAI", "#LLM"],
                "notion": ["#Productivity", "#Collaboration", "#UserExperience"],
                "stripe": ["#Fintech", "#DeveloperTools", "#API"]
            }
            hashtags.extend(company_hashtags.get(target_company.lower(), []))
        
        # Best posting times (professional audience)
        posting_times = {
            Platform.LINKEDIN: "Tuesday 10 AM",
            Platform.MEDIUM: "Sunday 7 PM", 
            Platform.DEVTO: "Wednesday 2 PM"
        }
        
        # SEO keywords
        keywords = [
            "artificial intelligence", "machine learning", "software engineering",
            "technical leadership", "system optimization", "data science"
        ]
        
        return {
            "hashtags": hashtags[:10],  # Limit to 10
            "posting_time": posting_times.get(platform, "Tuesday 10 AM"),
            "keywords": keywords
        }
    
    def _format_technical_details(self, details: Dict[str, Any]) -> str:
        """Format technical details for content"""
        if not details:
            return "Technical implementation details available upon request."
        
        formatted = []
        for key, value in details.items():
            formatted.append(f"• **{key.replace('_', ' ').title()}**: {value}")
        
        return "\n".join(formatted)
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for content"""
        if not metrics:
            return "Measurable improvements achieved across key performance indicators."
        
        formatted = []
        for key, value in metrics.items():
            formatted.append(f"• **{key.replace('_', ' ').title()}**: {value}")
        
        return "\n".join(formatted)
    
    def _generate_learnings(self, elements: Dict[str, Any]) -> str:
        """Generate key learnings section"""
        learnings = [
            f"Understanding {elements['category']} challenges in production environments",
            f"Implementing {', '.join(elements['skills'][:2])} for maximum impact",
            "The importance of measuring business value alongside technical metrics"
        ]
        
        return "\n".join(f"• {learning}" for learning in learnings)
    
    def _generate_best_practices(self, elements: Dict[str, Any]) -> str:
        """Generate best practices section"""
        practices = [
            "Start with clear success metrics and business objectives",
            f"Leverage {elements['skills'][0] if elements['skills'] else 'proven technologies'} for reliability",
            "Document learnings for team knowledge sharing",
            "Monitor performance continuously post-implementation"
        ]
        
        return "\n".join(f"1. {practice}" for practice in practices)
    
    def _generate_key_insight(self, elements: Dict[str, Any]) -> str:
        """Generate key insight for social media"""
        if elements.get("impact_score", 0) > 85:
            return f"High-impact {elements['category']} work requires both technical depth and business alignment."
        else:
            return f"Successful {elements['category']} projects balance innovation with practical delivery."


# Singleton instance
_professional_engine = None

def get_professional_content_engine() -> ProfessionalContentEngine:
    """Get singleton professional content engine"""
    global _professional_engine
    if _professional_engine is None:
        _professional_engine = ProfessionalContentEngine()
    return _professional_engine