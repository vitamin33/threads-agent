"""
Shared Article and Content Models

These models ensure consistency for content generation across services.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class ArticleType(str, Enum):
    """Types of articles that can be generated"""
    TUTORIAL = "tutorial"
    CASE_STUDY = "case_study"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    ARCHITECTURE_OVERVIEW = "architecture_overview"
    BEST_PRACTICES = "best_practices"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    LESSONS_LEARNED = "lessons_learned"
    QUICK_TIP = "quick_tip"
    SECURITY_ANALYSIS = "security_analysis"
    POST_MORTEM = "post_mortem"
    FEATURE_ANNOUNCEMENT = "feature_announcement"
    TECHNICAL_DEBT = "technical_debt"
    MIGRATION_GUIDE = "migration_guide"
    TOOL_COMPARISON = "tool_comparison"
    DEEP_DIVE = "deep_dive"


class Platform(str, Enum):
    """Supported publishing platforms"""
    LINKEDIN = "linkedin"
    DEVTO = "devto"
    MEDIUM = "medium"
    GITHUB = "github"
    HASHNODE = "hashnode"
    HACKERNOON = "hackernoon"
    REDDIT = "reddit"
    TWITTER = "twitter"
    PERSONAL_BLOG = "personal_blog"


class InsightScore(BaseModel):
    """Quality scoring for generated content"""
    overall_score: float = Field(..., ge=0, le=10)
    technical_depth: float = Field(..., ge=0, le=10)
    business_value: float = Field(..., ge=0, le=10)
    clarity: float = Field(..., ge=0, le=10)
    originality: float = Field(..., ge=0, le=10)
    
    # Platform-specific scores
    platform_relevance: float = Field(..., ge=0, le=10)
    engagement_potential: float = Field(..., ge=0, le=10)
    
    # Detailed feedback
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    
    @validator('overall_score')
    def validate_overall_score(cls, v, values):
        """Ensure overall score is reasonable given components"""
        if values:
            components = [
                values.get('technical_depth', 0),
                values.get('business_value', 0),
                values.get('clarity', 0),
                values.get('originality', 0)
            ]
            avg = sum(components) / len(components)
            if abs(v - avg) > 3:  # Allow some variance but not extreme
                return avg
        return v


class ArticleMetadata(BaseModel):
    """Metadata for generated articles"""
    # Source information
    source_type: str = "achievement"  # "achievement", "codebase", "analysis"
    source_id: Optional[str] = None
    achievement_id: Optional[int] = None
    
    # Generation details
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_time_seconds: Optional[float] = None
    model_used: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    
    # Content attributes
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    code_snippets_count: Optional[int] = None
    
    # SEO and discoverability
    keywords: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    
    # Publishing information
    published: bool = False
    published_at: Optional[datetime] = None
    published_url: Optional[str] = None
    
    # Engagement metrics (updated post-publishing)
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    
    # Custom metadata
    custom: Dict[str, Any] = Field(default_factory=dict)


class ArticleContent(BaseModel):
    """Complete article content model"""
    # Article identifiers
    article_type: ArticleType
    platform: Platform
    
    # Content
    title: str = Field(..., min_length=10, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    content: str = Field(..., min_length=100)
    
    # Structured sections (optional, for complex articles)
    sections: Optional[List[Dict[str, str]]] = None
    
    # Platform-specific formatting
    formatted_content: Optional[Dict[str, str]] = None  # {"markdown": "...", "html": "..."}
    
    # Media and code
    code_snippets: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[Dict[str, str]] = Field(default_factory=list)  # [{"url": "...", "alt": "..."}]
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: ArticleMetadata = Field(default_factory=ArticleMetadata)
    
    @validator('tags')
    def normalize_tags(cls, v):
        """Normalize tags"""
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    @validator('content')
    def validate_content_quality(cls, v):
        """Basic content quality checks"""
        if len(v.split()) < 50:
            raise ValueError("Content too short - minimum 50 words required")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContentRequest(BaseModel):
    """Request model for content generation"""
    # Source specification
    achievement_ids: Optional[List[int]] = None
    codebase_paths: Optional[List[str]] = None
    analysis_id: Optional[str] = None
    
    # Content preferences
    article_types: List[ArticleType]
    platforms: List[Platform]
    
    # Generation options
    auto_publish: bool = False
    quality_threshold: float = Field(7.0, ge=0, le=10)
    max_articles: Optional[int] = Field(None, ge=1, le=20)
    
    # Targeting
    target_company: Optional[str] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = Field("professional", pattern="^(professional|casual|technical|business)$")
    
    # Additional context
    context: Optional[Dict[str, Any]] = None


class ContentResponse(BaseModel):
    """Response model for content generation"""
    request_id: str
    status: str = Field(..., pattern="^(success|partial|failed)$")
    
    # Generated content
    articles: List[ArticleContent]
    total_generated: int
    
    # Quality metrics
    average_quality_score: float
    highest_quality_article_id: Optional[str] = None
    
    # Generation stats
    generation_time_seconds: float
    total_tokens_used: int
    estimated_cost_usd: float
    
    # Publishing status (if auto_publish was true)
    published_count: int = 0
    publishing_errors: List[Dict[str, str]] = Field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }