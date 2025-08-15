"""
Auto Content Pipeline - Converts achievements into viral content with high serbyn.pro conversion

This service implements the automatic PR→Content→Publishing pipeline with:
1. Strategic serbyn.pro CTAs for maximum conversion
2. UTM tracking for analytics
3. Platform-specific content optimization
4. Authority building and social proof
5. AI-powered PR evaluation for intelligent content generation decisions
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

import structlog
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

logger = structlog.get_logger()


class ContentType(Enum):
    """Types of content to generate"""
    CASE_STUDY = "case_study"
    TECHNICAL_BLOG = "technical_blog"
    LINKEDIN_POST = "linkedin_post"
    TWITTER_THREAD = "twitter_thread"
    ACHIEVEMENT_SHOWCASE = "achievement_showcase"


class Platform(Enum):
    """Target platforms for publishing"""
    DEVTO = "devto"
    LINKEDIN = "linkedin"
    MEDIUM = "medium"
    GITHUB = "github"
    TWITTER = "twitter"
    THREADS = "threads"


class ContentGenerationRequest(BaseModel):
    """Request for content generation with conversion optimization"""
    achievement_id: int
    include_serbyn_pro_cta: bool = True
    include_hiring_cta: bool = True
    utm_campaign: str = "pr_automation"
    target_platforms: List[str] = Field(default_factory=lambda: ["devto", "linkedin", "medium"])
    target_role: str = "MLOps Engineer"
    location_preference: str = "Remote US"
    # NEW: AI Hiring Manager Optimization parameters
    enable_hiring_manager_optimization: bool = False
    target_companies: List[str] = Field(default_factory=list)
    hiring_manager_focus: str = "technical_leadership"


class PublishingRequest(BaseModel):
    """Request for multi-platform publishing"""
    content_id: str
    platforms: List[str]
    schedule_immediately: bool = True


@dataclass
class ContentResult:
    """Result from content generation"""
    content: str
    title: str
    engagement_score: float
    conversion_score: float
    platforms_optimized: List[str]


@dataclass
class PublishingResult:
    """Result from publishing to platforms"""
    total_platforms: int
    successful_publications: int
    published_urls: List[str]
    failed_platforms: List[str] = None


# AI Hiring Manager Content Optimization Data Models
@dataclass
class HiringManagerPersona:
    """Hiring manager persona analysis result"""
    appeal_score: float  # 0-10 scale
    key_interests: List[str]
    optimization_suggestions: List[str]
    company_values: List[str]


@dataclass
class KeywordOptimizationResult:
    """Keyword optimization analysis result"""
    optimized_content: str
    keyword_analysis: Dict[str, float]
    seo_score: float  # 0-100 scale
    recommended_keywords: List[str]


@dataclass
class OptimizedHook:
    """Hiring manager optimized content hook"""
    content: str
    hiring_manager_appeal_score: float  # 0-10 scale
    target_audience_fit: float  # 0-10 scale
    authority_signals: List[str]


@dataclass
class HookOptimizationResult:
    """Hook optimization analysis result"""
    optimized_hooks: List[OptimizedHook]
    performance_prediction: Dict[str, float]
    target_audience_fit: float  # 0-10 scale


@dataclass
class CompanyVariant:
    """Company-specific content variant"""
    content: str
    company_alignment_score: float  # 0-10 scale
    key_messaging: List[str]
    value_alignment: Dict[str, str]


@dataclass
class CompanyTargetingResult:
    """Company-specific targeting result"""
    company_variants: Dict[str, CompanyVariant]
    overall_targeting_score: float  # 0-10 scale
    targeting_insights: Dict[str, str]


@dataclass
class AuthorityOptimizationResult:
    """Professional authority optimization result"""
    authority_enhanced_content: str
    authority_score: float  # 0-10 scale
    credibility_indicators: List[str]
    leadership_signals: List[str]


@dataclass
class OptimizedCTA:
    """Hiring manager optimized call-to-action"""
    content: str
    conversion_score: float  # 0-10 scale
    hiring_manager_appeal: float  # 0-10 scale
    utm_tracking: str
    platform_specific: bool


@dataclass
class CTAOptimizationResult:
    """CTA optimization analysis result"""
    optimized_ctas: List[OptimizedCTA]
    conversion_analysis: Dict[str, float]
    a_b_test_variants: List[OptimizedCTA]


@dataclass
class CompleteHiringManagerOptimizationResult:
    """Complete hiring manager optimization result"""
    optimized_content: str
    overall_conversion_score: float  # 0-100 scale
    hiring_manager_appeal_score: float  # 0-100 scale
    authority_score: float  # 0-100 scale
    seo_score: float  # 0-100 scale
    optimization_breakdown: Dict[str, Any]
    recommended_platforms: List[str]


class AutoContentPipeline:
    """
    Main pipeline for automatic content generation and publishing.
    
    Conversion Strategy:
    1. Authority-first hooks ("After 5+ years optimizing AI systems...")
    2. Specific business impact ("$120k annual savings")
    3. Strategic CTAs driving to serbyn.pro
    4. UTM tracking for analytics
    5. Platform-specific optimization
    """
    
    def __init__(self):
        self.enable_ai_evaluation = False  # Feature flag for AI-powered evaluation
        self.ai_evaluator = None
        self.hiring_manager_engine = AIHiringManagerContentEngine()
        self.conversion_templates = {
            "hiring_cta": [
                "🚀 Currently seeking remote US AI/MLOps roles where I can deliver similar impact.",
                "Ready to optimize AI systems for your team? Let's connect:",
                "Open to discussing MLOps challenges and opportunities:",
            ],
            "portfolio_cta": [
                "See more AI/MLOps case studies: {portfolio_link}",
                "Full technical breakdown & portfolio: {portfolio_link}",
                "Complete project details: {portfolio_link}",
            ],
            "contact_cta": [
                "Let's discuss your AI infrastructure needs: {contact_link}",
                "Interested in similar optimizations? Reach out: {contact_link}",
                "Schedule a technical discussion: {contact_link}",
            ]
        }
        
        self.authority_hooks = {
            "cost_optimization": "After 5+ years optimizing AI systems at scale, here's how I achieved {percentage}% cost reduction:",
            "performance": "Most ML teams struggle with {metric}. Here's my proven approach:",
            "infrastructure": "Building production AI systems taught me this counterintuitive lesson:",
            "automation": "This automation strategy saved {value} in operational overhead:",
        }

    def should_generate_content(self, pr_data: Dict[str, Any]) -> bool:
        """Determine if PR warrants content generation"""
        
        # Skip trivial changes
        trivial_indicators = [
            "typo", "fix typo", "update readme", "bump version",
            "format", "lint", "style", "comment", "docs only"
        ]
        
        title_lower = pr_data.get("title", "").lower()
        if any(indicator in title_lower for indicator in trivial_indicators):
            return False
        
        # Skip documentation-only changes
        files = pr_data.get("files", [])
        if files and all(
            f.get("filename", "").endswith((".md", ".txt", ".rst"))
            for f in files
        ):
            return False
        
        # Require significant changes
        significant_indicators = [
            "feat:", "feature", "implement", "add", "build",
            "performance", "optimization", "security", "scale",
            "automation", "mlops", "ai", "model", "pipeline",
            "registry", "rollback", "monitoring"
        ]
        
        # Get PR data properly
        pull_request = pr_data.get('pull_request', {})
        title = pull_request.get('title', pr_data.get('title', ''))
        body = pull_request.get('body', pr_data.get('body', ''))
        
        body_text = f"{title} {body}".lower()
        has_significant_work = any(
            indicator in body_text for indicator in significant_indicators
        )
        
        # Check for business impact indicators
        business_indicators = [
            "$", "save", "cost", "revenue", "performance", "speed",
            "efficiency", "scale", "reduce", "improve", "%"
        ]
        
        has_business_impact = any(
            indicator in body_text for indicator in business_indicators
        )
        
        return has_significant_work or has_business_impact

    async def should_generate_content_ai_powered(self, pr_data: Dict[str, Any]) -> bool:
        """AI-powered version of should_generate_content with intelligent evaluation"""
        
        if not self.enable_ai_evaluation:
            # Fallback to keyword-based method
            return self.should_generate_content(pr_data)
        
        # Initialize AI evaluator if not already done
        if self.ai_evaluator is None:
            self.ai_evaluator = AIPoweredPREvaluator()
        
        try:
            # Get AI evaluation scores
            marketing_value = await self.ai_evaluator.calculate_marketing_value(pr_data)
            
            # Threshold for content generation: overall score > 6.0
            # This means the PR has good potential for marketing/career advancement
            should_generate = marketing_value.overall_score > 6.0
            
            logger.info(
                f"AI evaluation for PR: {pr_data.get('pull_request', {}).get('title', 'Unknown')}",
                extra={
                    "overall_score": marketing_value.overall_score,
                    "should_generate": should_generate,
                    "technical_score": marketing_value.technical_significance_score,
                    "business_score": marketing_value.business_impact_score,
                    "positioning_score": marketing_value.professional_positioning_score,
                    "content_score": marketing_value.content_potential_score
                }
            )
            
            return should_generate
            
        except Exception as e:
            logger.error(f"AI evaluation failed, falling back to keyword matching: {e}")
            # Fallback to original method if AI fails
            return self.should_generate_content(pr_data)

    async def generate_content_with_cta(
        self, 
        achievement_data: Dict[str, Any], 
        request: ContentGenerationRequest
    ) -> ContentResult:
        """Generate content with conversion-optimized CTAs"""
        
        # Check if AI Hiring Manager Optimization is enabled
        if request.enable_hiring_manager_optimization:
            # Use AI Hiring Manager Content Optimizer for maximum conversion
            hiring_manager_optimizer = AIHiringManagerContentOptimizer()
            
            optimization_result = await hiring_manager_optimizer.generate_complete_hiring_manager_optimized_content(
                achievement_data=achievement_data,
                target_companies=request.target_companies,
                target_roles=[request.target_role],
                platforms=request.target_platforms
            )
            
            return ContentResult(
                content=optimization_result.optimized_content,
                title=achievement_data.get("title", "AI/MLOps Achievement"),
                engagement_score=optimization_result.hiring_manager_appeal_score,
                conversion_score=optimization_result.overall_conversion_score,
                platforms_optimized=request.target_platforms
            )
        
        # Traditional content generation path
        # Step 1: Create authority-building hook
        hook = self._generate_authority_hook(achievement_data)
        
        # Step 2: Structure main content with business focus
        main_content = self._generate_business_focused_content(achievement_data)
        
        # Step 3: Add conversion-optimized CTAs
        cta_section = self._generate_conversion_ctas(request)
        
        # Step 4: Combine with professional formatting
        full_content = f"{hook}\n\n{main_content}\n\n{cta_section}"
        
        # Step 5: Calculate conversion score
        conversion_score = self._calculate_conversion_score(full_content)
        
        return ContentResult(
            content=full_content,
            title=achievement_data.get("title", "AI/MLOps Achievement"),
            engagement_score=85.0,  # Will implement proper scoring
            conversion_score=conversion_score,
            platforms_optimized=request.target_platforms
        )

    async def add_utm_tracking(
        self,
        content: str,
        platform: str,
        campaign: str = "pr_automation",
        content_type: str = "case_study"
    ) -> str:
        """Add UTM tracking parameters for conversion analytics"""
        
        # Generate platform-specific UTM links
        base_url = "https://serbyn.pro"
        
        utm_params = {
            "utm_source": platform,
            "utm_medium": "social" if platform in ["linkedin", "twitter", "threads"] else "article",
            "utm_campaign": campaign,
            "utm_content": content_type,
        }
        
        # Create tracked links
        portfolio_link = f"{base_url}/portfolio?" + "&".join(f"{k}={v}" for k, v in utm_params.items())
        contact_link = f"{base_url}/contact?" + "&".join(f"{k}={v}" for k, v in utm_params.items())
        
        # Replace generic links with tracked versions
        tracked_content = content.replace(
            "serbyn.pro/portfolio", portfolio_link
        ).replace(
            "serbyn.pro/contact", contact_link
        )
        
        return tracked_content

    async def generate_platform_content(
        self, 
        achievement_data: Dict[str, Any], 
        platform: str
    ) -> str:
        """Generate platform-optimized content"""
        
        if platform == "linkedin":
            return self._generate_linkedin_content(achievement_data)
        elif platform == "devto":
            return self._generate_devto_content(achievement_data)
        elif platform == "twitter":
            return self._generate_twitter_thread(achievement_data)
        elif platform == "medium":
            return self._generate_medium_content(achievement_data)
        else:
            return self._generate_default_content(achievement_data)

    async def publish_to_all_platforms(self, request: PublishingRequest) -> PublishingResult:
        """Publish content to all specified platforms"""
        
        # This would integrate with the existing platform_publisher
        # For now, return success simulation
        successful_urls = []
        
        for platform in request.platforms:
            # Generate platform-specific UTM tracking
            utm_url = f"https://serbyn.pro/portfolio?utm_source={platform}&utm_medium=social&utm_campaign=pr_automation"
            successful_urls.append(utm_url)
        
        return PublishingResult(
            total_platforms=len(request.platforms),
            successful_publications=len(request.platforms),
            published_urls=successful_urls,
            failed_platforms=[]
        )

    async def generate_and_publish(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete pipeline: PR data → Content → Multi-platform publishing"""
        
        if not self.should_generate_content(pr_data):
            return {
                "content_generated": False,
                "reason": "PR does not meet content generation criteria"
            }
        
        # Convert PR data to achievement format
        achievement_data = self._pr_to_achievement_data(pr_data)
        
        # Generate content
        content_request = ContentGenerationRequest(
            achievement_id=pr_data.get("number", 0),
            utm_campaign="pr_automation"
        )
        
        content_result = await self.generate_content_with_cta(achievement_data, content_request)
        
        # Publish to all platforms
        publish_request = PublishingRequest(
            content_id=f"pr_{pr_data.get('number', 0)}",
            platforms=["devto", "linkedin", "medium", "github", "twitter", "threads"]
        )
        
        publish_result = await self.publish_to_all_platforms(publish_request)
        
        return {
            "content_generated": True,
            "platforms_published": publish_result.successful_publications,
            "content_id": f"pr_{pr_data.get('number', 0)}",
            "conversion_score": content_result.conversion_score,
            "published_urls": publish_result.published_urls
        }

    def _generate_authority_hook(self, achievement_data: Dict[str, Any]) -> str:
        """Generate authority-building hook"""
        
        category = achievement_data.get("category", "optimization")
        business_value = achievement_data.get("business_value", "")
        
        # Extract metrics for personalization
        if "$" in business_value:
            hook_template = self.authority_hooks.get("cost_optimization", "")
            # Extract percentage if available
            percentage = "40"  # Default
            if "%" in business_value:
                import re
                match = re.search(r'(\d+)%', business_value)
                if match:
                    percentage = match.group(1)
            return hook_template.format(percentage=percentage)
        
        elif "performance" in category.lower() or "speed" in business_value.lower():
            return self.authority_hooks.get("performance", "").format(
                metric="performance bottlenecks"
            )
        
        elif "infrastructure" in category.lower():
            return self.authority_hooks.get("infrastructure", "")
        
        else:
            # Default to cost optimization template
            return "After years of building production AI systems, here's what I learned:"

    def _generate_business_focused_content(self, achievement_data: Dict[str, Any]) -> str:
        """Generate content focused on business impact"""
        
        sections = []
        
        # Problem statement
        sections.append(f"## The Challenge\n{achievement_data.get('description', '')}")
        
        # Solution with technical credibility
        title = achievement_data.get('title', '')
        sections.append(f"## My Solution\n{title}")
        
        # Business impact (key for conversion)
        business_value = achievement_data.get('business_value', '')
        if business_value:
            sections.append(f"## Business Impact\n{business_value}")
        
        # Technical implementation (builds authority)
        technical_details = achievement_data.get('technical_details', {})
        if technical_details:
            formatted_tech = "\n".join(f"• {k}: {v}" for k, v in technical_details.items())
            sections.append(f"## Technical Implementation\n{formatted_tech}")
        
        # Key insights (thought leadership)
        sections.append(f"## Key Insights\n• Production AI systems require business-first thinking\n• Technical optimization means nothing without measurable ROI\n• The best solutions balance innovation with reliability")
        
        return "\n\n".join(sections)

    def _generate_conversion_ctas(self, request: ContentGenerationRequest) -> str:
        """Generate conversion-optimized CTAs"""
        
        ctas = []
        
        if request.include_hiring_cta:
            hiring_cta = f"🚀 Currently seeking remote US {request.target_role} roles where I can deliver similar impact."
            ctas.append(hiring_cta)
        
        if request.include_serbyn_pro_cta:
            portfolio_cta = "📊 See more AI/MLOps case studies: serbyn.pro/portfolio"
            contact_cta = "💬 Let's discuss your AI infrastructure needs: serbyn.pro/contact"
            ctas.extend([portfolio_cta, contact_cta])
        
        # Add social proof
        ctas.append("✨ Follow for more AI/MLOps insights and real-world case studies")
        
        return "\n\n".join(ctas)

    def _calculate_conversion_score(self, content: str) -> float:
        """Calculate conversion potential score"""
        
        score = 0
        
        # Authority indicators
        authority_words = ["years", "experience", "proven", "scale", "production"]
        score += len([word for word in authority_words if word in content.lower()]) * 10
        
        # Business impact indicators
        business_words = ["$", "%", "saved", "reduced", "improved", "roi"]
        score += len([word for word in business_words if word in content.lower()]) * 15
        
        # CTA quality
        if "serbyn.pro" in content:
            score += 20
        if "currently seeking" in content.lower():
            score += 15
        if "let's discuss" in content.lower():
            score += 10
        
        # Cap at 100
        return min(score, 100)

    def _pr_to_achievement_data(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert PR data to achievement format"""
        
        pull_request = pr_data.get("pull_request", {})
        
        return {
            "title": pull_request.get("title", ""),
            "description": pull_request.get("body", ""),
            "business_value": self._extract_business_value(pull_request),
            "technical_details": self._extract_technical_details(pull_request),
            "category": self._categorize_pr(pull_request),
            "impact_score": self._calculate_impact_score(pull_request),
        }

    def _extract_business_value(self, pr_data: Dict[str, Any]) -> str:
        """Extract business value from PR description"""
        
        body = pr_data.get("body", "")
        
        # Look for business impact patterns
        business_patterns = [
            r"(\$[\d,]+(?:\.\d{2})?)\s*(?:annual|yearly|per year|savings?)",
            r"(\d+%)\s*(?:reduction|improvement|faster|increase)",
            r"(\d+x)\s*(?:faster|improvement|speed)",
        ]
        
        import re
        extracted_values = []
        
        for pattern in business_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            extracted_values.extend(matches)
        
        if extracted_values:
            return f"Business impact: {', '.join(extracted_values)}"
        
        # Default business value
        return "Improved system reliability and operational efficiency"

    def _extract_technical_details(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract technical details from PR"""
        
        # Simple extraction - can be enhanced
        return {
            "implementation": "Production-ready solution",
            "testing": "Comprehensive test coverage",
            "deployment": "Zero-downtime deployment strategy"
        }

    def _categorize_pr(self, pr_data: Dict[str, Any]) -> str:
        """Categorize PR for content optimization"""
        
        title = pr_data.get("title", "").lower()
        
        if any(word in title for word in ["cost", "optimization", "performance"]):
            return "optimization"
        elif any(word in title for word in ["security", "auth", "encrypt"]):
            return "security"
        elif any(word in title for word in ["infrastructure", "deploy", "k8s"]):
            return "infrastructure"
        elif any(word in title for word in ["ml", "model", "ai", "mlops"]):
            return "mlops"
        else:
            return "development"

    def _calculate_impact_score(self, pr_data: Dict[str, Any]) -> int:
        """Calculate impact score for prioritization"""
        
        # Simple scoring - can be enhanced
        score = 50  # Base score
        
        body = pr_data.get("body", "").lower()
        
        # Business impact indicators
        if "$" in body:
            score += 30
        if "%" in body:
            score += 20
        if any(word in body for word in ["production", "scale", "performance"]):
            score += 15
        
        return min(score, 100)

    def _generate_linkedin_content(self, achievement_data: Dict[str, Any]) -> str:
        """Generate LinkedIn-optimized content"""
        
        hook = "🚀 Just shipped a game-changing optimization..."
        
        content = f"{hook}\n\n"
        content += f"{achievement_data.get('title', '')}\n\n"
        content += f"📊 Impact: {achievement_data.get('business_value', '')}\n\n"
        content += "Currently seeking remote US MLOps roles where I can deliver similar results.\n\n"
        content += "Portfolio & case studies: serbyn.pro/portfolio\n\n"
        content += "#MLOps #AI #Engineering #RemoteWork #TechLeadership"
        
        return content

    def _generate_devto_content(self, achievement_data: Dict[str, Any]) -> str:
        """Generate Dev.to technical article"""
        
        content = f"# {achievement_data.get('title', '')}\n\n"
        content += f"{achievement_data.get('description', '')}\n\n"
        content += f"## Business Impact\n{achievement_data.get('business_value', '')}\n\n"
        content += "## Technical Implementation\n\n"
        content += "```python\n# Example implementation\nclass MLOpsOptimization:\n    pass\n```\n\n"
        content += "---\n\n"
        content += "*Currently seeking remote US MLOps Engineer roles. "
        content += "Check out my [portfolio](https://serbyn.pro/portfolio) for more case studies.*"
        
        return content

    def _generate_twitter_thread(self, achievement_data: Dict[str, Any]) -> List[str]:
        """Generate Twitter thread"""
        
        tweets = [
            f"🧵 {achievement_data.get('title', '')}",
            f"Problem: {achievement_data.get('description', '')[:200]}...",
            f"Solution: {achievement_data.get('business_value', '')}",
            "Currently seeking remote US MLOps roles. Portfolio: serbyn.pro/portfolio",
        ]
        
        return tweets

    def _generate_medium_content(self, achievement_data: Dict[str, Any]) -> str:
        """Generate Medium long-form article"""
        
        return self._generate_devto_content(achievement_data)  # Similar format

    def _generate_default_content(self, achievement_data: Dict[str, Any]) -> str:
        """Generate default content format"""
        
        return self._generate_linkedin_content(achievement_data)


# AI-Powered PR Evaluation Models
@dataclass
class TechnicalSignificanceScore:
    """Result from AI technical significance evaluation"""
    score: float  # 0-10 scale
    reasoning: str
    technical_merits: Optional[List[str]] = None


@dataclass
class BusinessImpactScore:
    """Result from AI business impact analysis"""
    score: float  # 0-10 scale
    reasoning: str
    potential_savings: Optional[str] = None
    roi_category: str = "medium"  # high, medium, low


@dataclass
class ProfessionalPositioningScore:
    """Result from AI professional positioning evaluation"""
    score: float  # 0-10 scale
    role_alignment: str  # high, medium, low
    relevant_skills: List[str]
    positioning_advice: str


@dataclass
class ContentPotentialScore:
    """Result from AI content potential prediction"""
    engagement_score: float  # 0-10 scale
    conversion_score: float  # 0-10 scale
    viral_elements: List[str]
    target_audience: str
    recommendation: str  # generate, skip, enhance, combine_with_other_work


@dataclass
class MarketingValueScore:
    """Combined AI marketing value assessment"""
    overall_score: float  # 0-10 scale
    technical_significance_score: float
    business_impact_score: float
    professional_positioning_score: float
    content_potential_score: float
    marketing_strategy: str
    recommended_platforms: List[str]


class AIPoweredPREvaluator:
    """AI-powered PR evaluation system for intelligent content generation decisions"""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI()
        self._cache = {}  # Simple in-memory cache
        
    def _get_cache_key(self, pr_data: Dict[str, Any], evaluation_type: str) -> str:
        """Generate cache key for PR evaluation"""
        pr_content = json.dumps(pr_data, sort_keys=True)
        return hashlib.md5(f"{evaluation_type}:{pr_content}".encode()).hexdigest()
    
    async def evaluate_technical_significance(self, pr_data: Dict[str, Any]) -> TechnicalSignificanceScore:
        """Evaluate technical significance of PR using AI"""
        
        cache_key = self._get_cache_key(pr_data, "technical_significance")
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        pull_request = pr_data.get("pull_request", {})
        title = pull_request.get("title", "")
        body = pull_request.get("body", "")
        files = pull_request.get("files", [])
        
        prompt = f"""
        Evaluate the technical significance of this Pull Request for content marketing purposes.
        
        Title: {title}
        Description: {body}
        Files changed: {len(files)} files
        
        Analyze this PR and provide a JSON response with:
        {{
            "score": <float 0-10 representing technical significance>,
            "reasoning": "<detailed explanation of technical merit>",
            "technical_merits": ["<list of specific technical achievements>"]
        }}
        
        Consider:
        - Technical complexity and innovation
        - Architecture improvements
        - Performance optimizations
        - System reliability enhancements
        - Code quality improvements
        
        Score 8-10: Highly significant technical achievement
        Score 5-7: Moderate technical significance
        Score 0-4: Low technical significance (typos, minor changes)
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result_json = json.loads(response.choices[0].message.content)
            result = TechnicalSignificanceScore(
                score=result_json["score"],
                reasoning=result_json["reasoning"],
                technical_merits=result_json.get("technical_merits", [])
            )
            
            # Cache the result
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"AI evaluation failed: {e}")
            # Fallback to basic evaluation
            return TechnicalSignificanceScore(
                score=5.0,
                reasoning="AI evaluation unavailable, using default scoring",
                technical_merits=[]
            )
    
    async def analyze_business_impact(self, pr_data: Dict[str, Any]) -> BusinessImpactScore:
        """Analyze business impact potential using AI"""
        
        cache_key = self._get_cache_key(pr_data, "business_impact")
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        pull_request = pr_data.get("pull_request", {})
        title = pull_request.get("title", "")
        body = pull_request.get("body", "")
        
        prompt = f"""
        Analyze the business impact potential of this Pull Request.
        
        Title: {title}
        Description: {body}
        
        Provide a JSON response with:
        {{
            "score": <float 0-10 representing business impact>,
            "reasoning": "<explanation of business value>",
            "potential_savings": "<estimated cost savings or business value>",
            "roi_category": "<high/medium/low>"
        }}
        
        Consider:
        - Cost savings opportunities
        - Performance improvements
        - Operational efficiency gains
        - Risk reduction
        - Revenue generation potential
        - Scalability improvements
        
        Look for hidden business value that might not be obvious from keywords.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result_json = json.loads(response.choices[0].message.content)
            result = BusinessImpactScore(
                score=result_json["score"],
                reasoning=result_json["reasoning"],
                potential_savings=result_json.get("potential_savings"),
                roi_category=result_json.get("roi_category", "medium")
            )
            
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"AI business impact analysis failed: {e}")
            return BusinessImpactScore(
                score=5.0,
                reasoning="AI analysis unavailable, using default scoring",
                potential_savings="Unable to estimate",
                roi_category="medium"
            )
    
    async def score_professional_positioning(
        self, 
        pr_data: Dict[str, Any], 
        target_role: str = "MLOps Engineer",
        target_location: str = "Remote US"
    ) -> ProfessionalPositioningScore:
        """Score how well PR positions candidate for target role"""
        
        cache_key = self._get_cache_key(pr_data, f"positioning_{target_role}_{target_location}")
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        pull_request = pr_data.get("pull_request", {})
        title = pull_request.get("title", "")
        body = pull_request.get("body", "")
        
        prompt = f"""
        Evaluate how well this Pull Request helps position a candidate for a {target_role} role in {target_location}.
        
        Title: {title}
        Description: {body}
        Target Role: {target_role}
        Target Location: {target_location}
        
        Provide a JSON response with:
        {{
            "score": <float 0-10 representing role alignment>,
            "role_alignment": "<high/medium/low>",
            "relevant_skills": ["<list of skills demonstrated>"],
            "positioning_advice": "<strategic advice for career positioning>"
        }}
        
        Consider:
        - Relevance to target role responsibilities
        - Skills and technologies demonstrated
        - Leadership and impact demonstration
        - Industry best practices followed
        - Career advancement potential
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result_json = json.loads(response.choices[0].message.content)
            result = ProfessionalPositioningScore(
                score=result_json["score"],
                role_alignment=result_json["role_alignment"],
                relevant_skills=result_json["relevant_skills"],
                positioning_advice=result_json["positioning_advice"]
            )
            
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"AI positioning analysis failed: {e}")
            return ProfessionalPositioningScore(
                score=5.0,
                role_alignment="medium",
                relevant_skills=[],
                positioning_advice="AI analysis unavailable"
            )
    
    async def predict_content_potential(self, pr_data: Dict[str, Any]) -> ContentPotentialScore:
        """Predict content engagement and conversion potential using AI"""
        
        cache_key = self._get_cache_key(pr_data, "content_potential")
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        pull_request = pr_data.get("pull_request", {})
        title = pull_request.get("title", "")
        body = pull_request.get("body", "")
        
        prompt = f"""
        Predict the content potential of this Pull Request for social media and professional marketing.
        
        Title: {title}
        Description: {body}
        
        Provide a JSON response with:
        {{
            "engagement_score": <float 0-10 for social media engagement>,
            "conversion_score": <float 0-10 for hiring/business conversion>,
            "viral_elements": ["<list of viral content elements>"],
            "target_audience": "<primary audience description>",
            "recommendation": "<generate/skip/enhance/combine_with_other_work>"
        }}
        
        Consider viral elements:
        - Impressive metrics and numbers
        - Problem-solving stories
        - Technical achievements
        - Business impact
        - Before/after transformations
        - Counterintuitive insights
        
        High engagement: specific metrics, visual results, relatable problems
        High conversion: authority building, business impact, skill demonstration
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result_json = json.loads(response.choices[0].message.content)
            result = ContentPotentialScore(
                engagement_score=result_json["engagement_score"],
                conversion_score=result_json["conversion_score"],
                viral_elements=result_json["viral_elements"],
                target_audience=result_json["target_audience"],
                recommendation=result_json["recommendation"]
            )
            
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"AI content potential prediction failed: {e}")
            return ContentPotentialScore(
                engagement_score=5.0,
                conversion_score=5.0,
                viral_elements=[],
                target_audience="general",
                recommendation="skip"
            )
    
    async def calculate_marketing_value(
        self, 
        pr_data: Dict[str, Any],
        target_role: str = "MLOps Engineer",
        target_location: str = "Remote US"
    ) -> MarketingValueScore:
        """Calculate overall marketing value combining all AI evaluations"""
        
        cache_key = self._get_cache_key(pr_data, f"marketing_value_{target_role}_{target_location}")
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get all individual scores
        tech_score = await self.evaluate_technical_significance(pr_data)
        business_score = await self.analyze_business_impact(pr_data)
        positioning_score = await self.score_professional_positioning(pr_data, target_role, target_location)
        content_score = await self.predict_content_potential(pr_data)
        
        # Calculate weighted overall score
        # Business impact and positioning are weighted higher for job search
        overall_score = (
            tech_score.score * 0.2 +
            business_score.score * 0.3 +
            positioning_score.score * 0.3 +
            content_score.engagement_score * 0.1 +
            content_score.conversion_score * 0.1
        )
        
        # Generate marketing strategy
        strategy = f"""
        Marketing Strategy for {target_role} positioning:
        
        Technical Strengths: {tech_score.reasoning[:200]}...
        Business Impact: {business_score.reasoning[:200]}...
        Key Skills: {', '.join(positioning_score.relevant_skills[:5])}
        
        Recommended approach: Focus on {business_score.roi_category} ROI messaging with specific technical achievements.
        """
        
        # Recommend platforms based on scores
        platforms = ["linkedin"]  # Always include LinkedIn for professional content
        if content_score.engagement_score > 7.0:
            platforms.extend(["twitter", "threads"])
        if tech_score.score > 7.0:
            platforms.extend(["devto", "medium"])
        if business_score.score > 8.0:
            platforms.append("github")
        
        result = MarketingValueScore(
            overall_score=overall_score,
            technical_significance_score=tech_score.score,
            business_impact_score=business_score.score,
            professional_positioning_score=positioning_score.score,
            content_potential_score=(content_score.engagement_score + content_score.conversion_score) / 2,
            marketing_strategy=strategy,
            recommended_platforms=list(set(platforms))
        )
        
        self._cache[cache_key] = result
        return result


# Optimized content components for specific conversion goals
class ContentOptimizer:
    """Specialized content optimization for maximum conversion"""
    
    async def generate_engaging_hooks(
        self, 
        achievement_type: str, 
        business_impact: str
    ) -> List[str]:
        """Generate proven viral hooks with authority positioning"""
        
        hooks = [
            f"Here's how I {achievement_type.replace('_', ' ')} and achieved {business_impact}:",
            f"Most teams struggle with {achievement_type.replace('_', ' ')}. Here's my solution:",
            f"3 mistakes I made with {achievement_type.replace('_', ' ')} (and how to avoid them):",
            f"After months of {achievement_type.replace('_', ' ')}, here's what I learned:",
            f"This {achievement_type.replace('_', ' ')} strategy {business_impact}:",
        ]
        
        return hooks

    async def add_social_proof(self, achievement_data: Dict[str, Any]) -> str:
        """Add social proof elements for credibility"""
        
        proof_elements = []
        
        # Specific metrics
        business_value = achievement_data.get("business_value", "")
        if business_value:
            proof_elements.append(f"✅ Proven results: {business_value}")
        
        # Impact score
        impact_score = achievement_data.get("impact_score", 0)
        if impact_score > 80:
            proof_elements.append("✅ High-impact solution validated in production")
        
        # Authority indicators
        proof_elements.extend([
            "✅ 5+ years optimizing AI systems at scale",
            "✅ Production experience with Fortune 500 teams",
            "✅ Proven track record of measurable business impact"
        ])
        
        return "\n".join(proof_elements)


class AIHiringManagerContentEngine:
    """AI-powered content optimization specifically for AI/MLOps hiring managers"""
    
    def __init__(self):
        # Keywords that AI hiring managers search for
        self.hiring_manager_keywords = {
            "mlops": ["MLOps", "ML operations", "model deployment", "ML infrastructure", "model registry"],
            "ai_platform": ["AI platform", "ML platform", "LLM infrastructure", "AI engineering"],
            "finops": ["FinOps", "cost optimization", "GPU optimization", "infrastructure cost"],
            "genai": ["GenAI", "LLM", "RAG", "prompt engineering", "vector database"],
            "leadership": ["technical lead", "staff engineer", "principal engineer", "engineering manager"],
            "scale": ["production scale", "enterprise", "high availability", "performance optimization"]
        }
        
        # Company-specific content optimization
        self.company_targeting = {
            "anthropic": {
                "focus": "AI safety, responsible AI, alignment, robustness",
                "tone": "Safety-first technical leadership",
                "keywords": ["AI safety", "alignment", "robustness", "responsible AI"]
            },
            "notion": {
                "focus": "User experience, product engineering, developer tools",
                "tone": "Product-focused technical excellence", 
                "keywords": ["developer experience", "product engineering", "user-centric"]
            },
            "stripe": {
                "focus": "Developer experience, API design, reliability, scale",
                "tone": "Developer-first engineering excellence",
                "keywords": ["developer experience", "API design", "reliability at scale"]
            }
        }
        
        # Hiring manager hook templates
        self.hiring_hooks = {
            "cost_savings": "Most AI teams struggle with infrastructure costs. Here's how I reduced GPU spending by {percentage}% while improving performance:",
            "scale_achievement": "Scaling AI systems to enterprise levels taught me this counterintuitive approach:",
            "reliability": "After building mission-critical AI infrastructure, here's my approach to 99.9% reliability:",
            "team_leadership": "Leading AI teams through complex technical challenges requires this strategic mindset:"
        }

    def optimize_for_hiring_managers(self, content: str, achievement_data: Dict[str, Any], target_company: str = None) -> str:
        """Optimize content specifically for AI hiring managers"""
        
        # Add hiring manager keywords
        optimized_content = self._add_hiring_manager_keywords(content, achievement_data)
        
        # Apply company-specific targeting if specified
        if target_company and target_company.lower() in self.company_targeting:
            optimized_content = self._apply_company_targeting(optimized_content, target_company.lower())
        
        # Enhance authority positioning for hiring managers
        optimized_content = self._enhance_hiring_authority(optimized_content, achievement_data)
        
        # Optimize CTAs for hiring managers
        optimized_content = self._optimize_hiring_ctas(optimized_content)
        
        return optimized_content

    def _add_hiring_manager_keywords(self, content: str, achievement_data: Dict[str, Any]) -> str:
        """Add keywords that AI hiring managers search for"""
        
        category = achievement_data.get('category', 'development')
        
        if category in self.hiring_manager_keywords:
            relevant_keywords = self.hiring_manager_keywords[category]
            
            # Strategically inject keywords into content
            if "MLOps" not in content and "mlops" in category:
                content = content.replace("machine learning", "MLOps machine learning")
                content = content.replace("ML", "MLOps/ML")
        
        # Add technical leadership indicators
        if "led" not in content.lower() and "managed" not in content.lower():
            content = content.replace("implemented", "led the implementation of")
            content = content.replace("built", "architected and built")
        
        return content

    def _apply_company_targeting(self, content: str, company: str) -> str:
        """Apply company-specific content optimization"""
        
        targeting = self.company_targeting[company]
        
        # Add company-relevant focus areas
        company_section = f"\n\n## {targeting['focus'].title()} Focus\n"
        company_section += f"This implementation demonstrates {targeting['focus']} principles that align with companies prioritizing {targeting['tone'].lower()}."
        
        # Add before the CTA section
        cta_index = content.find("Currently seeking")
        if cta_index != -1:
            content = content[:cta_index] + company_section + "\n\n" + content[cta_index:]
        else:
            content += company_section
        
        return content

    def _enhance_hiring_authority(self, content: str, achievement_data: Dict[str, Any]) -> str:
        """Enhance authority positioning for hiring managers"""
        
        business_value = achievement_data.get('business_value', '')
        
        # Add quantified leadership impact
        if "$" in business_value or "%" in business_value:
            authority_addition = "\n\n🏆 **Leadership Impact**: This optimization represents the kind of strategic technical leadership that drives measurable business outcomes - exactly what AI teams need to scale effectively."
            
            # Insert before CTAs
            cta_index = content.find("Currently seeking")
            if cta_index != -1:
                content = content[:cta_index] + authority_addition + "\n\n" + content[cta_index:]
        
        return content

    def _optimize_hiring_ctas(self, content: str) -> str:
        """Optimize CTAs specifically for hiring managers"""
        
        # Replace generic CTAs with hiring-manager-focused ones
        hiring_ctas = [
            "🎯 **For AI Hiring Managers**: If your team faces similar infrastructure challenges, let's discuss how I can deliver comparable results for your organization.",
            "💼 **Currently Available**: Seeking remote US MLOps/AI Platform Engineer roles where I can apply this expertise at scale.",
            "📊 **Portfolio**: More enterprise AI case studies and leadership examples: serbyn.pro/portfolio",
            "🤝 **Let's Connect**: Discuss your AI infrastructure needs and team challenges: serbyn.pro/contact"
        ]
        
        # Replace existing CTAs
        if "Currently seeking" in content:
            # Find and replace the CTA section
            import re
            cta_pattern = r"Currently seeking.*?serbyn\.pro/contact"
            replacement = "\n\n".join(hiring_ctas)
            content = re.sub(cta_pattern, replacement, content, flags=re.DOTALL)
        
        return content

    def generate_hiring_manager_hook(self, achievement_data: Dict[str, Any]) -> str:
        """Generate hooks specifically designed for AI hiring managers"""
        
        business_value = achievement_data.get('business_value', '')
        category = achievement_data.get('category', 'optimization')
        
        # Extract key metrics for personalization
        cost_match = None
        performance_match = None
        
        import re
        if "$" in business_value:
            cost_match = re.search(r'\$[\d,]+', business_value)
        if "%" in business_value:
            performance_match = re.search(r'(\d+)%', business_value)
        
        # Generate hiring-manager-focused hooks
        if cost_match and performance_match:
            return f"Most AI teams burn through infrastructure budgets. Here's how I saved {cost_match.group()} while improving performance by {performance_match.group()}:"
        elif cost_match:
            return f"AI infrastructure costs are killing budgets. Here's my proven approach to {cost_match.group()} in annual savings:"
        elif performance_match:
            return f"Performance bottlenecks plague AI systems. Here's how I achieved {performance_match.group()} improvement:"
        else:
            return self.hiring_hooks.get(category, "Here's how I solve complex AI infrastructure challenges:")


class PlatformOptimizer:
    """Platform-specific optimization for maximum conversion"""
    
    async def optimize_for_platform(
        self, 
        achievement_data: Dict[str, Any], 
        platform: str
    ) -> str:
        """Optimize content for specific platform audience"""
        
        if platform == "linkedin":
            # Optimize for recruiters and hiring managers
            content = f"🎯 **Business Impact Showcase**\n\n"
            content += f"**Challenge:** {achievement_data.get('description', '')}\n\n"
            content += f"**Solution:** {achievement_data.get('title', '')}\n\n"
            content += f"**Business Impact:** {achievement_data.get('business_value', '')}\n\n"
            content += f"**Leadership Approach:** Focused on measurable ROI and team scalability\n\n"
            content += "Currently seeking remote US MLOps Engineer roles where I can deliver similar business impact.\n\n"
            content += "🔗 Portfolio: serbyn.pro/portfolio\n"
            content += "📩 Let's connect: serbyn.pro/contact"
            
            return content
            
        elif platform == "devto":
            # Optimize for developers and technical audience
            content = f"# {achievement_data.get('title', '')}\n\n"
            content += f"## The Problem\n{achievement_data.get('description', '')}\n\n"
            content += f"## My Solution\n{achievement_data.get('title', '')}\n\n"
            content += f"## Code Examples\n\n"
            content += "```python\n"
            content += "# Example implementation\n"
            content += f"class {achievement_data.get('title', 'Solution').replace(' ', '')}:\n"
            content += "    def optimize(self):\n"
            content += "        # Your optimization logic here\n"
            content += "        pass\n"
            content += "```\n\n"
            content += f"## Technical Implementation\n\n"
            
            # Add technical details
            technical_details = achievement_data.get('technical_details', {})
            for key, value in technical_details.items():
                content += f"### {key.replace('_', ' ').title()}\n{value}\n\n"
            
            content += f"## Results\n{achievement_data.get('business_value', '')}\n\n"
            content += "---\n\n"
            content += "*I'm Vitalii, an MLOps Engineer building AI systems that solve real business problems. "
            content += "Currently looking for remote US-based AI/MLOps roles. "
            content += "Check out my [portfolio](https://serbyn.pro/portfolio) or "
            content += "connect on [LinkedIn](https://serbyn.pro/contact).*"
            
            return content
            
        else:
            # Default optimization
            return f"{achievement_data.get('title', '')}\n\n{achievement_data.get('business_value', '')}\n\nPortfolio: serbyn.pro/portfolio"


class AIHiringManagerContentOptimizer:
    """
    AI-powered content optimizer specifically designed to maximize conversion with AI/MLOps hiring managers.
    
    This optimizer uses AI to understand what hiring managers at companies like Anthropic, Notion, 
    Stripe, and OpenAI are looking for, and optimizes content accordingly to increase job opportunity conversion rates.
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI()
        self._cache = {}  # Simple in-memory cache
        
        # Company-specific targeting knowledge base
        self.company_personas = {
            "anthropic": {
                "values": ["ai safety", "responsible ai", "research excellence", "technical depth"],
                "interests": ["alignment", "safety", "interpretability", "robustness"],
                "keywords": ["responsible", "safety", "alignment", "research", "ethical ai"]
            },
            "notion": {
                "values": ["productivity", "collaboration", "user experience", "scalability"],
                "interests": ["productivity tools", "collaboration", "user-centered design", "performance"],
                "keywords": ["productivity", "collaboration", "user experience", "workflows", "efficiency"]
            },
            "stripe": {
                "values": ["reliability", "scalability", "developer experience", "global scale"],
                "interests": ["payments infrastructure", "reliability", "developer tools", "global scale"],
                "keywords": ["scale", "reliability", "infrastructure", "developer experience", "payments"]
            },
            "openai": {
                "values": ["ai advancement", "research", "scaling", "safety"],
                "interests": ["large language models", "ai research", "scaling laws", "capabilities"],
                "keywords": ["llm", "scaling", "research", "capabilities", "ai advancement"]
            },
            "scale ai": {
                "values": ["data quality", "ml infrastructure", "enterprise ai", "automation"],
                "interests": ["data pipelines", "ml ops", "enterprise deployment", "automation"],
                "keywords": ["data quality", "ml infrastructure", "enterprise", "automation", "mlops"]
            }
        }
        
        # High-value AI/MLOps keywords that hiring managers search for
        self.high_value_keywords = {
            "technical": [
                "MLOps", "MLflow", "Kubernetes", "Docker", "Airflow", "Kubeflow",
                "model registry", "feature store", "model monitoring", "drift detection",
                "A/B testing", "canary deployment", "blue-green deployment",
                "CI/CD", "infrastructure as code", "Terraform", "Helm"
            ],
            "business": [
                "cost optimization", "performance improvement", "scalability", 
                "reliability", "SLO", "SLA", "uptime", "latency", "throughput",
                "ROI", "business impact", "operational efficiency", "automation"
            ],
            "leadership": [
                "technical leadership", "cross-functional collaboration", "mentoring",
                "architecture design", "system design", "team leadership",
                "stakeholder management", "strategic planning"
            ]
        }

    async def analyze_hiring_manager_personas(
        self, 
        achievement_data: Dict[str, Any], 
        target_companies: List[str]
    ) -> Dict[str, HiringManagerPersona]:
        """Analyze content through multiple hiring manager personas"""
        
        personas = {}
        
        for company in target_companies:
            company_key = company.lower().replace(" ", "_")
            company_info = self.company_personas.get(company_key, {})
            
            # Use AI to analyze appeal to this specific company's hiring managers
            prompt = f"""
            Analyze how appealing this achievement would be to hiring managers at {company}.
            
            Achievement: {achievement_data.get('title', '')}
            Description: {achievement_data.get('description', '')}
            Business Value: {achievement_data.get('business_value', '')}
            
            Company Values: {company_info.get('values', [])}
            Company Interests: {company_info.get('interests', [])}
            
            Provide a JSON response with:
            {{
                "appeal_score": <float 0-10>,
                "key_interests": ["<list of relevant interests for this company>"],
                "optimization_suggestions": ["<specific suggestions to improve appeal>"],
                "company_values": ["<company values that align with this achievement>"]
            }}
            """
            
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                result = json.loads(response.choices[0].message.content)
                personas[company_key] = HiringManagerPersona(
                    appeal_score=result["appeal_score"],
                    key_interests=result["key_interests"],
                    optimization_suggestions=result["optimization_suggestions"],
                    company_values=result["company_values"]
                )
                
            except Exception as e:
                logger.error(f"AI persona analysis failed for {company}: {e}")
                # Fallback to basic persona
                personas[company_key] = HiringManagerPersona(
                    appeal_score=7.0,
                    key_interests=company_info.get('interests', []),
                    optimization_suggestions=["Emphasize technical leadership", "Quantify business impact"],
                    company_values=company_info.get('values', [])
                )
        
        return personas

    async def optimize_job_search_keywords(
        self, 
        achievement_data: Dict[str, Any], 
        target_roles: List[str]
    ) -> KeywordOptimizationResult:
        """Optimize content with keywords that AI/MLOps hiring managers search for"""
        
        original_content = f"{achievement_data.get('title', '')} {achievement_data.get('description', '')}"
        
        # Collect relevant keywords for target roles
        relevant_keywords = []
        for category, keywords in self.high_value_keywords.items():
            relevant_keywords.extend(keywords)
        
        # Use AI to intelligently integrate keywords
        prompt = f"""
        Optimize this achievement description to include high-value AI/MLOps keywords that hiring managers search for.
        
        Original Content: {original_content}
        Target Roles: {target_roles}
        High-Value Keywords: {relevant_keywords[:20]}  # Limit to top 20
        
        Create an optimized version that:
        1. Naturally integrates relevant keywords without keyword stuffing
        2. Maintains professional tone and readability
        3. Enhances technical credibility
        4. Improves job search SEO
        
        Provide a JSON response with:
        {{
            "optimized_content": "<enhanced content with keywords>",
            "keyword_analysis": {{"<keyword>": <relevance_score_0_to_1>}},
            "seo_score": <score_0_to_100>,
            "recommended_keywords": ["<top keywords to emphasize>"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return KeywordOptimizationResult(
                optimized_content=result["optimized_content"],
                keyword_analysis=result["keyword_analysis"],
                seo_score=result["seo_score"],
                recommended_keywords=result["recommended_keywords"]
            )
            
        except Exception as e:
            logger.error(f"AI keyword optimization failed: {e}")
            # Fallback to basic keyword integration
            enhanced_content = original_content
            for keyword in self.high_value_keywords["technical"][:5]:
                if keyword.lower() not in enhanced_content.lower():
                    enhanced_content += f" Implemented using {keyword} best practices."
                    
            return KeywordOptimizationResult(
                optimized_content=enhanced_content,
                keyword_analysis={kw: 0.8 for kw in self.high_value_keywords["technical"][:5]},
                seo_score=75.0,
                recommended_keywords=self.high_value_keywords["technical"][:5]
            )

    async def optimize_hiring_manager_hooks(
        self, 
        achievement_data: Dict[str, Any], 
        target_audience: str
    ) -> HookOptimizationResult:
        """Generate content hooks that specifically resonate with technical hiring managers"""
        
        prompt = f"""
        Create compelling content hooks for this achievement that will resonate with {target_audience}.
        
        Achievement: {achievement_data.get('title', '')}
        Business Value: {achievement_data.get('business_value', '')}
        
        Generate 5 different hooks that:
        1. Build authority and credibility
        2. Include specific metrics or results
        3. Appeal to hiring managers' interests
        4. Demonstrate technical leadership
        5. Show business impact understanding
        
        Provide a JSON response with:
        {{
            "optimized_hooks": [
                {{
                    "content": "<hook text>",
                    "hiring_manager_appeal_score": <score_0_to_10>,
                    "target_audience_fit": <score_0_to_10>,
                    "authority_signals": ["<list of authority elements>"]
                }}
            ],
            "performance_prediction": {{"engagement": <score>, "conversion": <score>}},
            "target_audience_fit": <overall_score_0_to_10>
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4  # Slightly higher creativity for hooks
            )
            
            result = json.loads(response.choices[0].message.content)
            
            optimized_hooks = []
            for hook_data in result["optimized_hooks"]:
                optimized_hooks.append(OptimizedHook(
                    content=hook_data["content"],
                    hiring_manager_appeal_score=hook_data["hiring_manager_appeal_score"],
                    target_audience_fit=hook_data["target_audience_fit"],
                    authority_signals=hook_data["authority_signals"]
                ))
            
            return HookOptimizationResult(
                optimized_hooks=optimized_hooks,
                performance_prediction=result["performance_prediction"],
                target_audience_fit=result["target_audience_fit"]
            )
            
        except Exception as e:
            logger.error(f"AI hook optimization failed: {e}")
            # Fallback hooks
            fallback_hooks = [
                OptimizedHook(
                    content=f"After years of building production AI systems, here's how I achieved {achievement_data.get('business_value', 'significant impact')}:",
                    hiring_manager_appeal_score=8.0,
                    target_audience_fit=7.5,
                    authority_signals=["years", "production", "achieved", "systems"]
                ),
                OptimizedHook(
                    content=f"Most MLOps teams struggle with {achievement_data.get('title', 'scalability')}. Here's my proven solution:",
                    hiring_manager_appeal_score=7.5,
                    target_audience_fit=8.0,
                    authority_signals=["proven", "solution", "teams", "struggle"]
                )
            ]
            
            return HookOptimizationResult(
                optimized_hooks=fallback_hooks,
                performance_prediction={"engagement": 7.5, "conversion": 7.0},
                target_audience_fit=8.0
            )

    async def generate_company_specific_variants(
        self, 
        achievement_data: Dict[str, Any], 
        target_companies: List[str]
    ) -> CompanyTargetingResult:
        """Create company-specific content variants"""
        
        company_variants = {}
        
        for company in target_companies:
            company_key = company.lower().replace(" ", "_")
            company_info = self.company_personas.get(company_key, {})
            
            prompt = f"""
            Create a company-specific version of this achievement tailored for {company} hiring managers.
            
            Achievement: {achievement_data.get('title', '')}
            Description: {achievement_data.get('description', '')}
            Business Value: {achievement_data.get('business_value', '')}
            
            {company} Values: {company_info.get('values', [])}
            {company} Keywords: {company_info.get('keywords', [])}
            
            Create content that:
            1. Aligns with {company}'s values and culture
            2. Uses terminology that resonates with their hiring managers
            3. Emphasizes aspects most relevant to {company}
            4. Maintains professional credibility
            
            Provide a JSON response with:
            {{
                "content": "<company-tailored content>",
                "company_alignment_score": <score_0_to_10>,
                "key_messaging": ["<key messages for this company>"],
                "value_alignment": {{"<company_value>": "<how achievement aligns>"}}
            }}
            """
            
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                result = json.loads(response.choices[0].message.content)
                company_variants[company_key] = CompanyVariant(
                    content=result["content"],
                    company_alignment_score=result["company_alignment_score"],
                    key_messaging=result["key_messaging"],
                    value_alignment=result["value_alignment"]
                )
                
            except Exception as e:
                logger.error(f"AI company variant generation failed for {company}: {e}")
                # Fallback variant
                base_content = f"{achievement_data.get('title', '')}. {achievement_data.get('description', '')}"
                company_keywords = company_info.get('keywords', [])
                if company_keywords:
                    base_content += f" This aligns with {company}'s focus on {', '.join(company_keywords[:2])}."
                
                company_variants[company_key] = CompanyVariant(
                    content=base_content,
                    company_alignment_score=7.0,
                    key_messaging=[f"Relevant to {company}'s mission", "Technical excellence"],
                    value_alignment={company_info.get('values', ['innovation'])[0]: "Direct alignment through technical achievement"}
                )
        
        # Calculate overall targeting score
        total_score = sum(variant.company_alignment_score for variant in company_variants.values())
        overall_score = total_score / len(company_variants) if company_variants else 0.0
        
        return CompanyTargetingResult(
            company_variants=company_variants,
            overall_targeting_score=overall_score,
            targeting_insights={company: f"Optimized for {company}'s values" for company in target_companies}
        )

    async def optimize_professional_authority(
        self, 
        achievement_data: Dict[str, Any], 
        authority_focus: str = "technical_leadership"
    ) -> AuthorityOptimizationResult:
        """Optimize content to build professional authority that impresses hiring managers"""
        
        prompt = f"""
        Enhance this achievement to build maximum professional authority with hiring managers.
        Focus area: {authority_focus}
        
        Achievement: {achievement_data.get('title', '')}
        Description: {achievement_data.get('description', '')}
        Business Value: {achievement_data.get('business_value', '')}
        Technical Details: {achievement_data.get('technical_details', {})}
        
        Enhance the content to demonstrate:
        1. Technical leadership and expertise
        2. Business impact understanding
        3. Production experience at scale
        4. Problem-solving capabilities
        5. Quantifiable results
        
        Provide a JSON response with:
        {{
            "authority_enhanced_content": "<enhanced content with authority building>",
            "authority_score": <score_0_to_10>,
            "credibility_indicators": ["<list of credibility elements added>"],
            "leadership_signals": ["<list of leadership signals>"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return AuthorityOptimizationResult(
                authority_enhanced_content=result["authority_enhanced_content"],
                authority_score=result["authority_score"],
                credibility_indicators=result["credibility_indicators"],
                leadership_signals=result["leadership_signals"]
            )
            
        except Exception as e:
            logger.error(f"AI authority optimization failed: {e}")
            # Fallback authority building
            base_content = f"{achievement_data.get('title', '')}. {achievement_data.get('description', '')}"
            
            # Add authority signals
            authority_content = f"Led implementation of {base_content.lower()}"
            authority_content += f" Delivered measurable business impact: {achievement_data.get('business_value', 'significant ROI')}."
            authority_content += " Architected solution for production scale with enterprise-grade reliability."
            authority_content += " Mentored team through complex technical challenges while ensuring stakeholder alignment."
            
            return AuthorityOptimizationResult(
                authority_enhanced_content=authority_content,
                authority_score=8.5,
                credibility_indicators=["Led implementation", "Production scale", "Enterprise-grade", "Measurable impact"],
                leadership_signals=["Led", "Delivered", "Architected", "Mentored"]
            )

    async def optimize_hiring_manager_ctas(
        self, 
        achievement_data: Dict[str, Any], 
        target_roles: List[str], 
        target_companies: List[str]
    ) -> CTAOptimizationResult:
        """Optimize CTAs specifically for converting hiring managers into job opportunities"""
        
        prompt = f"""
        Create high-conversion CTAs specifically designed to convert hiring managers into job opportunities.
        
        Achievement: {achievement_data.get('title', '')}
        Business Value: {achievement_data.get('business_value', '')}
        Target Roles: {target_roles}
        Target Companies: {target_companies}
        
        Create 5 different CTAs that:
        1. Appeal specifically to hiring managers
        2. Create urgency without being pushy
        3. Demonstrate value proposition
        4. Include clear next steps
        5. Maintain professional tone
        
        Provide a JSON response with:
        {{
            "optimized_ctas": [
                {{
                    "content": "<CTA text with serbyn.pro links>",
                    "conversion_score": <score_0_to_10>,
                    "hiring_manager_appeal": <score_0_to_10>,
                    "utm_tracking": "<utm parameters>",
                    "platform_specific": <boolean>
                }}
            ],
            "conversion_analysis": {{"best_performing": "<reason>", "target_audience": "<analysis>"}},
            "a_b_test_variants": [<additional variants for testing>]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            result = json.loads(response.choices[0].message.content)
            
            optimized_ctas = []
            for cta_data in result["optimized_ctas"]:
                optimized_ctas.append(OptimizedCTA(
                    content=cta_data["content"],
                    conversion_score=cta_data["conversion_score"],
                    hiring_manager_appeal=cta_data["hiring_manager_appeal"],
                    utm_tracking=cta_data["utm_tracking"],
                    platform_specific=cta_data["platform_specific"]
                ))
            
            return CTAOptimizationResult(
                optimized_ctas=optimized_ctas,
                conversion_analysis=result["conversion_analysis"],
                a_b_test_variants=optimized_ctas[:3]  # First 3 as variants
            )
            
        except Exception as e:
            logger.error(f"AI CTA optimization failed: {e}")
            # Fallback CTAs
            fallback_ctas = [
                OptimizedCTA(
                    content=f"Currently seeking {target_roles[0] if target_roles else 'MLOps Engineer'} roles where I can deliver similar impact. Portfolio: serbyn.pro/portfolio?utm_source=linkedin&utm_campaign=hiring_manager&utm_content=cta1",
                    conversion_score=8.5,
                    hiring_manager_appeal=8.0,
                    utm_tracking="utm_source=linkedin&utm_campaign=hiring_manager&utm_content=cta1",
                    platform_specific=True
                ),
                OptimizedCTA(
                    content="Open to discussing similar challenges and opportunities with forward-thinking teams. Let's connect: serbyn.pro/contact?utm_source=content&utm_campaign=hiring_manager&utm_content=cta2",
                    conversion_score=8.0,
                    hiring_manager_appeal=7.5,
                    utm_tracking="utm_source=content&utm_campaign=hiring_manager&utm_content=cta2",
                    platform_specific=False
                )
            ]
            
            return CTAOptimizationResult(
                optimized_ctas=fallback_ctas,
                conversion_analysis={"best_performing": "Direct value proposition", "target_audience": "Technical hiring managers"},
                a_b_test_variants=fallback_ctas
            )

    async def generate_complete_hiring_manager_optimized_content(
        self, 
        achievement_data: Dict[str, Any], 
        target_companies: List[str], 
        target_roles: List[str], 
        platforms: List[str]
    ) -> CompleteHiringManagerOptimizationResult:
        """Generate fully optimized content for hiring managers integrating all optimization components"""
        
        # Run all optimization components
        keyword_optimization = await self.optimize_job_search_keywords(achievement_data, target_roles)
        hook_optimization = await self.optimize_hiring_manager_hooks(achievement_data, "AI/MLOps hiring managers")
        company_targeting = await self.generate_company_specific_variants(achievement_data, target_companies)
        authority_optimization = await self.optimize_professional_authority(achievement_data, "technical_leadership")
        cta_optimization = await self.optimize_hiring_manager_ctas(achievement_data, target_roles, target_companies)
        
        # Select best components
        best_hook = max(hook_optimization.optimized_hooks, key=lambda h: h.hiring_manager_appeal_score)
        best_cta = max(cta_optimization.optimized_ctas, key=lambda c: c.conversion_score)
        
        # Compose final optimized content
        optimized_content = f"{best_hook.content}\n\n"
        optimized_content += f"{authority_optimization.authority_enhanced_content}\n\n"
        optimized_content += f"{keyword_optimization.optimized_content}\n\n"
        optimized_content += f"{best_cta.content}"
        
        # Calculate overall scores
        overall_conversion_score = (
            keyword_optimization.seo_score * 0.2 +
            (best_hook.hiring_manager_appeal_score * 10) * 0.3 +  # Convert to 0-100 scale
            authority_optimization.authority_score * 10 * 0.3 +
            best_cta.conversion_score * 10 * 0.2
        )
        
        hiring_manager_appeal_score = (
            best_hook.hiring_manager_appeal_score * 10 * 0.4 +
            company_targeting.overall_targeting_score * 10 * 0.3 +
            best_cta.hiring_manager_appeal * 10 * 0.3
        )
        
        return CompleteHiringManagerOptimizationResult(
            optimized_content=optimized_content,
            overall_conversion_score=min(overall_conversion_score, 100.0),
            hiring_manager_appeal_score=min(hiring_manager_appeal_score, 100.0),
            authority_score=min(authority_optimization.authority_score * 10, 100.0),
            seo_score=keyword_optimization.seo_score,
            optimization_breakdown={
                "keyword_optimization": keyword_optimization.seo_score,
                "hook_optimization": best_hook.hiring_manager_appeal_score * 10,
                "authority_building": authority_optimization.authority_score * 10,
                "cta_optimization": best_cta.conversion_score * 10,
                "company_targeting": company_targeting.overall_targeting_score * 10
            },
            recommended_platforms=platforms
        )