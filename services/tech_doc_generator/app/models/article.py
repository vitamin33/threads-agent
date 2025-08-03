from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ArticleType(str, Enum):
    ARCHITECTURE = "architecture"
    TUTORIAL = "tutorial"
    PERFORMANCE = "performance"
    BEST_PRACTICES = "best_practices"
    PROBLEM_SOLUTION = "problem_solution"
    DEEP_DIVE = "deep_dive"

class Platform(str, Enum):
    DEVTO = "devto"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    THREADS = "threads"
    GITHUB = "github"
    MEDIUM = "medium"

class ArticleStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

class SourceType(str, Enum):
    REPOSITORY = "repository"
    FILE = "file"
    COMMIT = "commit"
    PR = "pr"
    DIRECTORY = "directory"

class InsightScore(BaseModel):
    """Quality prediction for article insights"""
    technical_depth: float = Field(..., ge=0, le=10, description="Technical complexity and depth")
    uniqueness: float = Field(..., ge=0, le=10, description="How unique/novel the insights are")
    readability: float = Field(..., ge=0, le=10, description="How accessible the content is")
    engagement_potential: float = Field(..., ge=0, le=10, description="Predicted engagement")
    trend_alignment: float = Field(..., ge=0, le=10, description="Alignment with current trends")
    overall_score: float = Field(..., ge=0, le=10, description="Overall insight quality score")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")

class CodeAnalysis(BaseModel):
    """Results from code analysis"""
    patterns: List[str] = Field(default_factory=list, description="Architectural patterns found")
    complexity_score: float = Field(0, description="Code complexity score")
    test_coverage: float = Field(0, description="Test coverage percentage")
    dependencies: List[str] = Field(default_factory=list, description="Key dependencies")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    interesting_functions: List[Dict[str, Any]] = Field(default_factory=list)
    recent_changes: List[Dict[str, Any]] = Field(default_factory=list)

class ArticleRequest(BaseModel):
    """Request to generate an article"""
    source_type: SourceType
    source_path: str = Field(..., description="Path to analyze (file, directory, commit hash)")
    angles: List[ArticleType] = Field(default=[ArticleType.ARCHITECTURE], description="Article types to generate")
    target_platforms: List[Platform] = Field(default=[Platform.DEVTO], description="Platforms to publish to")
    title_hint: Optional[str] = Field(None, description="Suggested title or topic focus")
    custom_instructions: Optional[str] = Field(None, description="Custom generation instructions")
    auto_publish: bool = Field(False, description="Whether to auto-publish after generation")

class ArticleContent(BaseModel):
    """Generated article content"""
    title: str
    subtitle: Optional[str] = None
    content: str
    tags: List[str] = Field(default_factory=list)
    estimated_read_time: int = Field(0, description="Estimated read time in minutes")
    code_examples: List[Dict[str, str]] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list, description="Key insights extracted")
    platform_specific: Dict[Platform, Dict[str, Any]] = Field(default_factory=dict)

class Article(BaseModel):
    """Complete article model"""
    id: str
    request: ArticleRequest
    analysis: Optional[CodeAnalysis] = None
    content: Optional[ArticleContent] = None
    insight_score: Optional[InsightScore] = None
    status: ArticleStatus = ArticleStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_urls: Dict[Platform, str] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

class PublishRequest(BaseModel):
    """Request to publish an article"""
    article_id: str
    platforms: List[Platform]
    schedule_time: Optional[datetime] = None
    custom_content: Optional[Dict[Platform, str]] = None

class PredictionRequest(BaseModel):
    """Request to predict article quality"""
    title: str
    content: str
    target_platform: Platform
    tags: List[str] = Field(default_factory=list)