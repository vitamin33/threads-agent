# API Schemas

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AchievementBase(BaseModel):
    """Base achievement schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str = Field(
        ...,
        pattern="^(feature|optimization|bugfix|infrastructure|documentation|testing|security|performance|architecture|content|business|milestone|project|development|refactoring)$",
    )

    started_at: datetime
    completed_at: datetime
    duration_hours: float = Field(..., ge=0)

    source_type: str = Field(
        ...,
        pattern="^(git|github|github_pr|ci|manual|api|threads|prometheus|webhook|linear)$",
    )
    source_id: Optional[str] = None
    source_url: Optional[str] = None

    tags: List[str] = []
    skills_demonstrated: List[str] = []


class AchievementCreate(BaseModel):
    """Schema for creating achievement"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str = Field(
        ...,
        pattern="^(feature|optimization|bugfix|infrastructure|documentation|testing|security|performance|architecture|content|business|milestone|project|development|refactoring)$",
    )

    started_at: datetime
    completed_at: datetime
    # duration_hours is calculated automatically from dates

    source_type: str = Field(
        ...,
        pattern="^(git|github|github_pr|ci|manual|api|threads|prometheus|webhook|linear)$",
    )
    source_id: Optional[str] = None
    source_url: Optional[str] = None

    tags: List[str] = []
    skills_demonstrated: List[str] = []

    evidence: Optional[Dict[str, Any]] = {}
    metrics_before: Optional[Dict[str, Any]] = {}
    metrics_after: Optional[Dict[str, Any]] = {}

    # Optional fields that can be set
    impact_score: Optional[float] = Field(None, ge=0, le=100)
    complexity_score: Optional[float] = Field(None, ge=0, le=100)
    business_value: Optional[str] = None
    time_saved_hours: Optional[float] = Field(None, ge=0)
    portfolio_ready: Optional[bool] = False


class AchievementUpdate(BaseModel):
    """Schema for updating achievement"""

    title: Optional[str] = None
    description: Optional[str] = None

    impact_score: Optional[float] = Field(None, ge=0, le=100)
    complexity_score: Optional[float] = Field(None, ge=0, le=100)
    business_value: Optional[str] = None
    time_saved_hours: Optional[float] = Field(None, ge=0)
    performance_improvement_pct: Optional[float] = Field(None, ge=0)

    evidence: Optional[Dict[str, Any]] = None
    metrics_before: Optional[Dict[str, Any]] = None
    metrics_after: Optional[Dict[str, Any]] = None

    tags: Optional[List[str]] = None
    skills_demonstrated: Optional[List[str]] = None

    ai_summary: Optional[str] = None
    ai_impact_analysis: Optional[str] = None
    ai_technical_analysis: Optional[str] = None

    portfolio_ready: Optional[bool] = None
    portfolio_section: Optional[str] = None
    display_priority: Optional[int] = Field(None, ge=0, le=100)


class Achievement(AchievementBase):
    """Complete achievement schema"""

    id: int

    impact_score: float = 0.0
    complexity_score: float = 0.0
    business_value: Optional[str] = None
    time_saved_hours: float = 0.0
    performance_improvement_pct: float = 0.0

    evidence: Dict[str, Any] = {}
    metrics_before: Dict[str, Any] = {}
    metrics_after: Dict[str, Any] = {}

    ai_summary: Optional[str] = None
    ai_impact_analysis: Optional[str] = None
    ai_technical_analysis: Optional[str] = None

    portfolio_ready: bool = False
    portfolio_section: Optional[str] = None
    display_priority: int = 50

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AchievementList(BaseModel):
    """List of achievements with pagination"""

    items: List[Achievement]
    total: int
    page: int
    per_page: int
    pages: int


class AnalysisRequest(BaseModel):
    """Request for achievement analysis"""

    achievement_id: int
    analyze_impact: bool = True
    analyze_technical: bool = True
    generate_summary: bool = True


class AnalysisResponse(BaseModel):
    """Analysis results"""

    achievement_id: int
    impact_score: float
    complexity_score: float
    business_value: Optional[str]
    time_saved_hours: float

    summary: str
    impact_analysis: str
    technical_analysis: str

    recommendations: List[str]


class PortfolioRequest(BaseModel):
    """Request for portfolio generation"""

    format: str = Field("markdown", pattern="^(markdown|pdf|html|json)$")
    include_categories: Optional[List[str]] = None
    min_impact_score: float = Field(0, ge=0, le=100)
    portfolio_ready_only: bool = True
    max_achievements: Optional[int] = Field(None, ge=1)


class PortfolioResponse(BaseModel):
    """Portfolio generation response"""

    version: str
    format: str
    total_achievements: int
    total_impact_score: float
    total_value_generated: Optional[str]
    total_time_saved: float

    content_preview: str
    download_url: Optional[str] = None
    storage_url: Optional[str] = None


class GitHubWebhookPayload(BaseModel):
    """GitHub webhook payload"""

    action: str
    repository: Dict[str, Any]
    sender: Dict[str, Any]

    # Optional fields based on event type
    pull_request: Optional[Dict[str, Any]] = None
    workflow_run: Optional[Dict[str, Any]] = None
    issue: Optional[Dict[str, Any]] = None


class WebhookResponse(BaseModel):
    """Webhook processing response"""

    status: str
    message: str
    achievement_created: bool = False
    achievement_id: Optional[int] = None


class PRAchievementCreate(BaseModel):
    """Schema for creating PR-based achievement"""

    pr_number: int
    title: str
    description: Optional[str] = None
    merge_timestamp: datetime
    author: str
    reviewers: List[str] = []

    code_analysis: Dict[str, Any] = {}
    impact_analysis: Dict[str, Any] = {}
    stories: Dict[str, Any] = {}

    ci_metrics: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}
    quality_metrics: Dict[str, Any] = {}

    posting_metadata: Dict[str, Any] = {}


class PRAchievement(PRAchievementCreate):
    """Complete PR achievement schema"""

    id: int
    achievement_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PRCodeChangeCreate(BaseModel):
    """Schema for PR code changes"""

    file_path: str
    language: Optional[str] = None
    change_type: Optional[str] = None

    lines_added: int = 0
    lines_deleted: int = 0
    complexity_before: Optional[float] = None
    complexity_after: Optional[float] = None

    key_changes: List[str] = []
    patterns_used: List[str] = []


class PRKPIImpactCreate(BaseModel):
    """Schema for KPI impacts"""

    kpi_name: str
    kpi_category: str

    value_before: Optional[float] = None
    value_after: Optional[float] = None
    improvement_percentage: Optional[float] = None
    improvement_absolute: Optional[float] = None

    measurement_method: Optional[str] = None
    confidence_score: Optional[float] = None


class ComprehensiveAnalysisResult(BaseModel):
    """Result from comprehensive PR analysis"""

    metadata: Dict[str, Any]
    code_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    business_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    team_metrics: Dict[str, Any]
    architectural_metrics: Dict[str, Any]
    security_metrics: Dict[str, Any]
    innovation_metrics: Dict[str, Any]
    learning_metrics: Dict[str, Any]
    impact_predictions: Dict[str, Any]
    composite_scores: Dict[str, Any]
    ai_insights: Dict[str, Any]


class StoryGenerationRequest(BaseModel):
    """Request for story generation"""

    analysis: ComprehensiveAnalysisResult
    pr_data: Dict[str, Any]
    personas: List[str] = ["technical", "business", "leadership"]


class StoryGenerationResponse(BaseModel):
    """Generated stories response"""

    stories: Dict[str, Dict[str, Any]]
    personas: Dict[str, Dict[str, Any]]
    generation_time: float


class MultiPlatformContentRequest(BaseModel):
    """Request for multi-platform content preparation"""

    achievement_id: int
    platforms: List[str] = ["linkedin", "twitter", "devto", "github", "portfolio"]


class MultiPlatformContentResponse(BaseModel):
    """Prepared content for multiple platforms"""

    achievement_id: int
    platforms: Dict[str, Dict[str, Any]]
    preparation_time: float
