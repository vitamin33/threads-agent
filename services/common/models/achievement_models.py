"""
Shared Achievement Models

These models ensure consistency between achievement_collector and tech_doc_generator services.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class AchievementCategory(str, Enum):
    """Standard achievement categories"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    PERFORMANCE = "performance"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENTATION = "documentation"
    AUTOMATION = "automation"
    RESEARCH = "research"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    AI_ML = "ai_ml"
    DATA_ENGINEERING = "data_engineering"
    DEVOPS = "devops"
    TESTING = "testing"
    REFACTORING = "refactoring"
    OPTIMIZATION = "optimization"


class AchievementMetrics(BaseModel):
    """Standardized metrics for achievements"""
    time_saved_hours: Optional[float] = Field(None, ge=0)
    cost_saved_dollars: Optional[float] = Field(None, ge=0)
    performance_improvement_percent: Optional[float] = Field(None, ge=-100, le=1000)
    error_reduction_percent: Optional[float] = Field(None, ge=0, le=100)
    coverage_increase_percent: Optional[float] = Field(None, ge=0, le=100)
    users_impacted: Optional[int] = Field(None, ge=0)
    revenue_impact_dollars: Optional[float] = Field(None, ge=0)
    
    # Custom metrics as key-value pairs
    custom: Dict[str, float] = Field(default_factory=dict)


class Achievement(BaseModel):
    """Complete achievement model"""
    id: int
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20)
    category: AchievementCategory
    impact_score: float = Field(..., ge=0, le=100)
    complexity_score: float = Field(50.0, ge=0, le=100)
    business_value: str = Field(..., min_length=10)
    
    # Technical details
    technical_details: Optional[Dict[str, Any]] = None
    technologies_used: List[str] = Field(default_factory=list)
    
    # Metrics
    metrics: Optional[AchievementMetrics] = None
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    portfolio_ready: bool = False
    source_type: Optional[str] = None  # "github_pr", "manual", "linear", etc.
    source_id: Optional[str] = None  # PR number, ticket ID, etc.
    
    # Timestamps
    started_at: datetime
    completed_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    duration_hours: Optional[float] = None
    
    # Integration metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('duration_hours', always=True)
    def calculate_duration(cls, v, values):
        """Auto-calculate duration if not provided"""
        if v is None and 'started_at' in values and 'completed_at' in values:
            delta = values['completed_at'] - values['started_at']
            return delta.total_seconds() / 3600
        return v
    
    @validator('tags')
    def normalize_tags(cls, v):
        """Normalize tags to lowercase"""
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AchievementCreate(BaseModel):
    """Model for creating new achievements"""
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20)
    category: AchievementCategory
    impact_score: float = Field(..., ge=0, le=100)
    complexity_score: float = Field(50.0, ge=0, le=100)
    business_value: str = Field(..., min_length=10)
    
    technical_details: Optional[Dict[str, Any]] = None
    technologies_used: List[str] = Field(default_factory=list)
    metrics: Optional[AchievementMetrics] = None
    
    tags: List[str] = Field(default_factory=list)
    portfolio_ready: bool = True
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    
    started_at: datetime
    completed_at: datetime
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AchievementUpdate(BaseModel):
    """Model for updating achievements"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20)
    category: Optional[AchievementCategory] = None
    impact_score: Optional[float] = Field(None, ge=0, le=100)
    complexity_score: Optional[float] = Field(None, ge=0, le=100)
    business_value: Optional[str] = Field(None, min_length=10)
    
    technical_details: Optional[Dict[str, Any]] = None
    technologies_used: Optional[List[str]] = None
    metrics: Optional[AchievementMetrics] = None
    
    tags: Optional[List[str]] = None
    portfolio_ready: Optional[bool] = None
    
    metadata: Optional[Dict[str, Any]] = None


class AchievementSummary(BaseModel):
    """Lightweight achievement summary for listings"""
    id: int
    title: str
    category: AchievementCategory
    impact_score: float
    business_value: str
    tags: List[str]
    completed_at: datetime
    portfolio_ready: bool
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AchievementFilter(BaseModel):
    """Filter criteria for achievement queries"""
    categories: Optional[List[AchievementCategory]] = None
    min_impact_score: Optional[float] = Field(None, ge=0, le=100)
    max_impact_score: Optional[float] = Field(None, ge=0, le=100)
    min_complexity_score: Optional[float] = Field(None, ge=0, le=100)
    portfolio_ready_only: bool = False
    
    tags: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    source_type: Optional[str] = None
    
    # Text search
    search_query: Optional[str] = None
    
    # Company-specific filtering
    company_keywords: Optional[List[str]] = None
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    
    # Sorting
    sort_by: str = Field("completed_at", pattern="^(completed_at|created_at|impact_score|complexity_score)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Ensure end_date is after start_date"""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v