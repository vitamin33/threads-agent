# API Schemas

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AchievementBase(BaseModel):
    """Base achievement schema"""
    
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str = Field(..., pattern="^(feature|optimization|bugfix|infrastructure|documentation|testing|security|performance|architecture)$")
    
    started_at: datetime
    completed_at: datetime
    duration_hours: float = Field(..., ge=0)
    
    source_type: str = Field(..., pattern="^(git|github|ci|manual|api)$")
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    
    tags: List[str] = []
    skills_demonstrated: List[str] = []


class AchievementCreate(AchievementBase):
    """Schema for creating achievement"""
    
    evidence: Optional[Dict[str, Any]] = {}
    metrics_before: Optional[Dict[str, Any]] = {}
    metrics_after: Optional[Dict[str, Any]] = {}


class AchievementUpdate(BaseModel):
    """Schema for updating achievement"""
    
    title: Optional[str] = None
    description: Optional[str] = None
    
    impact_score: Optional[float] = Field(None, ge=0, le=100)
    complexity_score: Optional[float] = Field(None, ge=0, le=100)
    business_value: Optional[Decimal] = Field(None, ge=0)
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
    business_value: Decimal = Decimal("0.00")
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
    business_value: Decimal
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
    total_value_generated: Decimal
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