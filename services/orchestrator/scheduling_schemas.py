"""
Pydantic schemas for Scheduling Management API (Phase 1 of Epic 14)

These schemas define the API contract for content management and scheduling.
They are implemented following TDD methodology - tests were written first.
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import pytz


# Enums for validation
class ContentStatus(str, Enum):
    """Content lifecycle status."""
    DRAFT = "draft"
    READY = "ready"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class PlatformType(str, Enum):
    """Supported social media platforms."""
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    DEVTO = "devto"
    MEDIUM = "medium"


class ContentType(str, Enum):
    """Types of content that can be created."""
    BLOG_POST = "blog_post"
    SOCIAL_POST = "social_post"
    ARTICLE = "article"
    NEWSLETTER = "newsletter"
    VIDEO_SCRIPT = "video_script"


# Content Item Schemas
class ContentItemCreate(BaseModel):
    """Schema for creating new content items."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: str = Field(..., min_length=1, max_length=500, description="Content title")
    content: str = Field(..., min_length=1, description="Main content body")
    content_type: ContentType = Field(..., description="Type of content")
    author_id: str = Field(..., min_length=1, description="ID of content author")
    status: ContentStatus = Field(default=ContentStatus.DRAFT, description="Content status")
    slug: Optional[str] = Field(None, max_length=200, description="URL-friendly slug")
    content_metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional metadata as JSON"
    )

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v) > 500:
            raise ValueError('Title must be 500 characters or less')
        return v.strip()


class ContentItemUpdate(BaseModel):
    """Schema for updating existing content items."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    content_type: Optional[ContentType] = None
    status: Optional[ContentStatus] = None
    slug: Optional[str] = Field(None, max_length=200)
    content_metadata: Optional[Dict[str, Any]] = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Title cannot be empty')
            if len(v) > 500:
                raise ValueError('Title must be 500 characters or less')
            return v.strip()
        return v


class ContentItemResponse(BaseModel):
    """Schema for content item responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    content: str
    content_type: ContentType
    author_id: str
    status: ContentStatus
    slug: Optional[str] = None
    content_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


# Content Schedule Schemas
class ContentScheduleCreate(BaseModel):
    """Schema for creating content schedules."""
    
    content_item_id: int = Field(..., description="ID of content to schedule")
    platform: PlatformType = Field(..., description="Target platform")
    scheduled_time: datetime = Field(..., description="When to publish")
    timezone_name: str = Field(default="UTC", description="Timezone for scheduling")
    status: str = Field(default="scheduled", description="Schedule status")
    platform_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Platform-specific configuration"
    )

    @field_validator('scheduled_time')
    @classmethod
    def validate_future_time(cls, v: datetime) -> datetime:
        # Ensure timezone awareness
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError('Scheduled time must be in the future')
        
        return v

    @field_validator('timezone_name')
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            pytz.timezone(v)
        except pytz.UnknownTimeZoneError:
            raise ValueError(f'Invalid timezone: {v}')
        return v


class ContentScheduleUpdate(BaseModel):
    """Schema for updating content schedules."""
    
    scheduled_time: Optional[datetime] = None
    timezone_name: Optional[str] = None
    status: Optional[str] = None
    platform_config: Optional[Dict[str, Any]] = None

    @field_validator('scheduled_time')
    @classmethod
    def validate_future_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            # Ensure timezone awareness
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            if v <= now:
                raise ValueError('Scheduled time must be in the future')
        
        return v

    @field_validator('timezone_name')
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                pytz.timezone(v)
            except pytz.UnknownTimeZoneError:
                raise ValueError(f'Invalid timezone: {v}')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_statuses = ["scheduled", "published", "failed", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f'Invalid status: {v}. Must be one of {valid_statuses}')
        return v


class ContentScheduleResponse(BaseModel):
    """Schema for content schedule responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    content_item_id: int
    platform: PlatformType
    scheduled_time: datetime
    timezone_name: str
    status: str
    retry_count: int = 0
    max_retries: int = 3
    next_retry_time: Optional[datetime] = None
    platform_config: Optional[Dict[str, Any]] = None
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Response Schemas
class ContentStatusResponse(BaseModel):
    """Schema for content publishing status."""
    
    content_id: int
    status: ContentStatus
    schedules: List[ContentScheduleResponse]
    publishing_progress: Dict[str, int] = Field(
        description="Progress across platforms",
        example={
            "total_platforms": 3,
            "published_platforms": 1,
            "failed_platforms": 0,
            "scheduled_platforms": 2
        }
    )
    last_updated: datetime


class PaginatedContentResponse(BaseModel):
    """Schema for paginated content responses."""
    
    items: List[ContentItemResponse]
    total: int
    page: int
    size: int
    pages: int


class UpcomingSchedulesResponse(BaseModel):
    """Schema for upcoming schedules response."""
    
    schedules: List[ContentScheduleResponse]
    total: int
    next_24_hours: int = Field(description="Schedules in next 24 hours")
    next_week: int = Field(description="Schedules in next week")


class CalendarViewResponse(BaseModel):
    """Schema for calendar view of schedules."""
    
    schedules: List[ContentScheduleResponse]
    date_range: Dict[str, str] = Field(
        description="Date range for the calendar view",
        example={"start": "2025-01-01", "end": "2025-01-31"}
    )
    grouped_by_date: Dict[str, List[ContentScheduleResponse]] = Field(
        description="Schedules grouped by date"
    )


# Filter and Query Schemas
class ContentListFilters(BaseModel):
    """Schema for content list filtering parameters."""
    
    status: Optional[ContentStatus] = None
    author_id: Optional[str] = None
    content_type: Optional[ContentType] = None
    search: Optional[str] = Field(None, description="Search in title and content")
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class ScheduleListFilters(BaseModel):
    """Schema for schedule list filtering parameters."""
    
    platform: Optional[PlatformType] = None
    status: Optional[str] = None
    scheduled_after: Optional[datetime] = None
    scheduled_before: Optional[datetime] = None
    content_item_id: Optional[int] = None


# Error Response Schemas
class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    
    detail: str
    error_code: Optional[str] = None
    field_errors: Optional[Dict[str, List[str]]] = None


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""
    
    detail: str = "Validation error"
    errors: List[Dict[str, Any]] = Field(description="List of validation errors")