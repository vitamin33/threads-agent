# Shared Models Migration Guide

This guide helps services migrate to the new shared models for achievement and article data structures.

## Overview

The shared models ensure consistency between `achievement_collector` and `tech_doc_generator` services, enabling seamless integration and reducing data transformation overhead.

## Location

All shared models are in: `services/common/models/`

## Migration Steps

### 1. For achievement_collector Service

Replace local models with shared ones:

```python
# OLD (services/achievement_collector/api/schemas.py)
from .schemas import Achievement, AchievementCreate

# NEW
from services.common.models import (
    Achievement,
    AchievementCreate,
    AchievementUpdate,
    AchievementFilter,
    AchievementCategory,
    AchievementMetrics
)
```

### 2. For tech_doc_generator Service

Update article models:

```python
# OLD (services/tech_doc_generator/app/models/article.py)
from .models.article import ArticleType, Platform, ArticleContent

# NEW
from services.common.models import (
    ArticleType,
    Platform,
    ArticleContent,
    ArticleMetadata,
    InsightScore,
    ContentRequest,
    ContentResponse
)
```

### 3. Database Model Alignment

Ensure database models match shared model fields:

```python
# services/achievement_collector/db/models.py
class Achievement(Base):
    __tablename__ = "achievements"
    
    # Ensure all fields from shared Achievement model exist
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # Use AchievementCategory values
    impact_score = Column(Float, nullable=False)
    complexity_score = Column(Float, default=50.0)
    business_value = Column(Text, nullable=False)
    
    # JSON fields for complex data
    technical_details = Column(JSON)
    metrics = Column(JSON)  # Store AchievementMetrics as JSON
    tags = Column(JSON, default=list)
    
    # ... rest of fields
```

## Model Features

### 1. AchievementCategory Enum

Standardized categories across services:

```python
class AchievementCategory(str, Enum):
    FEATURE = "feature"
    AI_ML = "ai_ml"
    DEVOPS = "devops"
    # ... etc
```

### 2. AchievementMetrics

Structured metrics with validation:

```python
metrics = AchievementMetrics(
    time_saved_hours=40,
    cost_saved_dollars=50000,
    performance_improvement_percent=150,
    custom={"api_latency_ms": 50}
)
```

### 3. Achievement Model

- Auto-calculates `duration_hours` from timestamps
- Normalizes tags to lowercase
- Validates all numeric ranges

### 4. ArticleContent Model

- Validates minimum content length
- Supports platform-specific formatting
- Includes structured sections for complex articles

### 5. ContentRequest/Response

Standardized API contracts for content generation:

```python
# Request
request = ContentRequest(
    achievement_ids=[1, 2, 3],
    article_types=[ArticleType.CASE_STUDY],
    platforms=[Platform.LINKEDIN],
    target_company="notion"
)

# Response
response = ContentResponse(
    request_id="req_123",
    status="success",
    articles=[...],
    average_quality_score=8.5
)
```

## Validation Benefits

1. **Type Safety**: Pydantic models ensure type correctness
2. **Value Constraints**: Automatic validation of scores, percentages, etc.
3. **Required Fields**: Clear distinction between required and optional
4. **Auto-computation**: Duration calculation, tag normalization

## Testing

Run shared model tests:

```bash
cd services/common
pytest tests/test_achievement_models.py -v
pytest tests/test_article_models.py -v
pytest tests/test_model_integration.py -v
```

## Best Practices

1. **Import from common**: Always import from `services.common.models`
2. **Use enums**: Use `AchievementCategory` and `ArticleType` enums
3. **Validate early**: Create model instances as soon as data enters the system
4. **JSON storage**: Use model's `.dict()` method for JSON serialization

## Example Integration

```python
# Achievement Collector
from services.common.models import Achievement, AchievementCreate

@router.post("/achievements/", response_model=Achievement)
async def create_achievement(data: AchievementCreate):
    # Pydantic validates input automatically
    achievement = Achievement(
        id=generate_id(),
        **data.dict(),
        created_at=datetime.now()
    )
    return achievement

# Tech Doc Generator
from services.common.models import ContentRequest, ArticleContent

@router.post("/generate", response_model=List[ArticleContent])
async def generate_content(request: ContentRequest):
    articles = []
    for achievement_id in request.achievement_ids:
        # Generate content using shared models
        article = ArticleContent(
            article_type=request.article_types[0],
            platform=request.platforms[0],
            title="...",
            content="..."
        )
        articles.append(article)
    return articles
```

## Backwards Compatibility

To maintain compatibility during migration:

1. Create aliases for old model names
2. Add deprecation warnings
3. Support both old and new field names temporarily

```python
# Temporary compatibility layer
Achievement = SharedAchievement  # Alias to shared model

# Add deprecation warning
import warnings
warnings.warn(
    "Local Achievement model is deprecated. Use services.common.models.Achievement",
    DeprecationWarning
)
```

## Future Enhancements

1. **Model versioning**: Track model version for migrations
2. **Serialization helpers**: Custom JSON encoders/decoders
3. **Model registry**: Central registry of all shared models
4. **Validation middleware**: Auto-validate requests/responses