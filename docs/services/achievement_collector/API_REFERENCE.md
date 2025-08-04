# 📚 Achievement Collector API Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
```http
Authorization: Bearer <your-api-token>
```

## Table of Contents
- [Achievements API](#achievements-api)
- [PR Analysis API](#pr-analysis-api)
- [Story Generation API](#story-generation-api)
- [Export API](#export-api)
- [Analytics API](#analytics-api)
- [Tech Doc Integration API](#tech-doc-integration-api)
- [Webhooks](#webhooks)
- [Error Responses](#error-responses)

## Achievements API

### Create Achievement

Create a new achievement manually.

```http
POST /achievements
Content-Type: application/json

{
  "title": "Optimized API Gateway Performance",
  "description": "Implemented Redis caching reducing latency by 40%",
  "category": "optimization",
  "started_at": "2025-01-25T10:00:00Z",
  "completed_at": "2025-01-28T15:30:00Z",
  "source_type": "manual",
  "tags": ["performance", "redis", "api"],
  "skills_demonstrated": ["Redis", "Performance Optimization", "Python"],
  "metrics_after": {
    "latency_ms": 120,
    "throughput_rps": 5000
  },
  "impact_score": 85,
  "business_value": "$15,000/month cost savings"
}
```

**Response:**
```json
{
  "id": 1,
  "title": "Optimized API Gateway Performance",
  "duration_hours": 77.5,
  "impact_score": 85,
  "portfolio_ready": true,
  "created_at": "2025-01-28T16:00:00Z"
}
```

### List Achievements

Get paginated list of achievements with filtering.

```http
GET /achievements?page=1&per_page=20&category=optimization&min_impact_score=70&portfolio_ready=true
```

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | int | Page number | 1 |
| `per_page` | int | Items per page (max 100) | 20 |
| `category` | string | Filter by category | - |
| `portfolio_ready` | bool | Only portfolio-ready items | - |
| `min_impact_score` | float | Minimum impact score (0-100) | - |
| `search` | string | Search in title/description | - |
| `sort_by` | string | Sort field: completed_at, impact_score, business_value | completed_at |
| `order` | string | Sort order: asc, desc | desc |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Optimized API Gateway Performance",
      "category": "optimization",
      "impact_score": 85,
      "completed_at": "2025-01-28T15:30:00Z",
      "tags": ["performance", "redis", "api"]
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### Get Achievement

Get specific achievement by ID.

```http
GET /achievements/{achievement_id}
```

**Response:**
```json
{
  "id": 1,
  "title": "Optimized API Gateway Performance",
  "description": "Implemented Redis caching reducing latency by 40%",
  "category": "optimization",
  "started_at": "2025-01-25T10:00:00Z",
  "completed_at": "2025-01-28T15:30:00Z",
  "duration_hours": 77.5,
  "impact_score": 85,
  "complexity_score": 72,
  "business_value": "$15,000/month cost savings",
  "time_saved_hours": 20,
  "source_type": "github_pr",
  "source_id": "PR-123",
  "source_url": "https://github.com/org/repo/pull/123",
  "tags": ["performance", "redis", "api"],
  "skills_demonstrated": ["Redis", "Performance Optimization", "Python"],
  "ai_summary": "Significant performance improvement through intelligent caching",
  "portfolio_ready": true,
  "metadata": {
    "pr_number": 123,
    "reviewers": ["tech_lead", "senior_dev"],
    "merge_time_hours": 72
  }
}
```

### Update Achievement

Update existing achievement.

```http
PUT /achievements/{achievement_id}
Content-Type: application/json

{
  "portfolio_ready": true,
  "display_priority": 90,
  "business_value": "$20,000/month cost savings"
}
```

### Delete Achievement

Delete an achievement.

```http
DELETE /achievements/{achievement_id}
```

**Response:**
```json
{
  "status": "deleted",
  "id": 1
}
```

### Get Achievement Statistics

Get aggregate statistics for achievements.

```http
GET /achievements/stats/summary
```

**Response:**
```json
{
  "total_achievements": 42,
  "total_value_generated": 250000.00,
  "total_time_saved_hours": 480.5,
  "average_impact_score": 72.3,
  "average_complexity_score": 68.9,
  "by_category": {
    "feature": 15,
    "optimization": 12,
    "bugfix": 8,
    "architecture": 7
  }
}
```

## PR Analysis API

### Create Achievement from PR

Analyze a PR and create an achievement.

```http
POST /achievements/pr/{pr_number}
Content-Type: application/json

{
  "pr_data": {
    "number": 123,
    "title": "Optimize API performance",
    "body": "Implements caching layer",
    "created_at": "2025-01-25T10:00:00Z",
    "merged_at": "2025-01-28T15:30:00Z",
    "html_url": "https://github.com/org/repo/pull/123",
    "user": {"login": "developer"},
    "labels": [{"name": "performance"}],
    "requested_reviewers": [{"login": "reviewer1"}]
  },
  "analysis": {
    "code_metrics": {
      "languages": {"Python": 150, "JavaScript": 50},
      "files_changed": 8,
      "total_lines_added": 200
    },
    "performance_metrics": {
      "latency_changes": {
        "reported": {
          "before": 200,
          "after": 120,
          "improvement_percentage": 40
        }
      }
    },
    "composite_scores": {
      "overall_impact": 85,
      "technical_excellence": 78
    }
  }
}
```

### Get PR Achievement

Get achievement by PR number.

```http
GET /achievements/pr/{pr_number}
```

### Get PR Achievement Details

Get detailed PR achievement data.

```http
GET /achievements/pr/{pr_number}/details
```

**Response:**
```json
{
  "id": 1,
  "achievement_id": 42,
  "pr_number": 123,
  "title": "Optimize API performance",
  "merge_timestamp": "2025-01-28T15:30:00Z",
  "code_analysis": {
    "languages": {"Python": 150},
    "complexity_reduction": 15
  },
  "impact_analysis": {
    "performance": {"latency_reduction": 40},
    "business": {"cost_savings": 15000}
  },
  "stories": {
    "technical": {
      "summary": "Implemented Redis caching",
      "key_points": ["Reduced latency", "Improved scalability"]
    }
  }
}
```

### Update PR Stories

Update PR achievement with generated stories.

```http
PUT /achievements/pr/{pr_number}/stories
Content-Type: application/json

{
  "technical": {
    "summary": "Advanced caching implementation",
    "full_story": "...",
    "key_points": ["Redis integration", "Cache invalidation strategy"]
  },
  "business": {
    "summary": "Significant cost reduction",
    "full_story": "...",
    "key_points": ["$15K monthly savings", "Improved user experience"]
  }
}
```

### List PR Achievements

List all PR-based achievements.

```http
GET /achievements/source/github_pr?page=1&per_page=20
```

## Story Generation API

### Generate Persona Stories

Generate stories for all personas from analysis data.

```http
POST /stories/generate
Content-Type: application/json

{
  "analysis": {
    "metadata": {...},
    "code_metrics": {...},
    "business_metrics": {...},
    "composite_scores": {...}
  },
  "personas": ["technical", "business", "leadership", "hr_manager"]
}
```

**Response:**
```json
{
  "technical": {
    "summary": "Implemented advanced caching strategy",
    "full_story": "Faced with increasing API latency...",
    "key_points": [
      "Reduced p99 latency by 40%",
      "Implemented cache-aside pattern",
      "Added intelligent invalidation"
    ],
    "technologies": ["Redis", "Python", "Docker"]
  },
  "business": {
    "summary": "Delivered $15K monthly cost savings",
    "full_story": "Identified opportunity to reduce infrastructure costs...",
    "key_points": [
      "$180K annual savings",
      "Improved user satisfaction",
      "Enabled 4x traffic growth"
    ]
  }
}
```

### Generate Specific Story Type

Generate story for specific persona.

```http
POST /stories/generate/{story_type}
Content-Type: application/json

{
  "pr_metadata": {...},
  "relevant_metrics": {...}
}
```

**Story Types:**
- `technical` - For technical interviews
- `business` - For business stakeholders
- `leadership` - For leadership roles
- `hr_manager` - For HR screening
- `tech_interviewer` - For technical deep dives
- `startup_ceo` - For startup environments
- `investor` - For investment discussions

## Export API

### Export to Portfolio

Generate portfolio-ready content.

```http
POST /export/portfolio
Content-Type: application/json

{
  "achievement_ids": [1, 2, 3],
  "format": "markdown",
  "include_metrics": true,
  "group_by": "category"
}
```

**Response:**
```json
{
  "content": "# Professional Achievements\n\n## Performance Optimization\n\n### Optimized API Gateway...",
  "format": "markdown",
  "word_count": 1250,
  "achievements_included": 3
}
```

### Export to Platform

Prepare content for specific platform.

```http
POST /export/platform/{platform}
Content-Type: application/json

{
  "achievement_id": 1,
  "include_hashtags": true,
  "tone": "professional"
}
```

**Platforms:**
- `linkedin` - LinkedIn post format
- `twitter` - Twitter thread format
- `devto` - Dev.to article format
- `github` - GitHub profile README

**Response:**
```json
{
  "platform": "linkedin",
  "content": {
    "post": "🚀 Just optimized our API gateway...",
    "hashtags": ["#Performance", "#Engineering", "#Innovation"],
    "media_suggestions": ["performance_graph.png"],
    "optimal_posting_time": "Tuesday 10 AM"
  }
}
```

### Bulk Export

Export multiple achievements.

```http
POST /export/bulk
Content-Type: application/json

{
  "filters": {
    "min_impact_score": 70,
    "categories": ["optimization", "feature"],
    "date_range": {
      "start": "2025-01-01",
      "end": "2025-12-31"
    }
  },
  "format": "json",
  "include_stories": true
}
```

## Analytics API

### Get Performance Metrics

Get performance analytics for achievements.

```http
GET /analytics/performance?period=monthly&year=2025
```

**Response:**
```json
{
  "period": "monthly",
  "year": 2025,
  "metrics": [
    {
      "month": "January",
      "total_achievements": 8,
      "avg_impact_score": 75.2,
      "total_value_generated": 45000,
      "top_categories": ["optimization", "feature"]
    }
  ],
  "trends": {
    "impact_score_trend": "increasing",
    "productivity_trend": "stable"
  }
}
```

### Get Skill Analytics

Analyze skill development over time.

```http
GET /analytics/skills
```

**Response:**
```json
{
  "top_skills": [
    {"skill": "Python", "count": 24, "avg_impact": 78},
    {"skill": "Performance Optimization", "count": 18, "avg_impact": 85},
    {"skill": "System Design", "count": 12, "avg_impact": 82}
  ],
  "skill_growth": [
    {"skill": "Kubernetes", "growth_rate": 150, "period": "6_months"}
  ],
  "skill_gaps": ["Machine Learning", "Security"]
}
```

### Get Career Progress

Track career progression metrics.

```http
GET /analytics/career-progress
```

**Response:**
```json
{
  "current_level": "Senior Engineer",
  "next_level": "Staff Engineer",
  "requirements_met": {
    "technical_depth": 85,
    "business_impact": 72,
    "leadership": 68,
    "innovation": 80
  },
  "recommendations": [
    "Focus on cross-team leadership initiatives",
    "Increase business metric visibility"
  ]
}
```

## Tech Doc Integration API

Optimized endpoints for tech_doc_generator service integration (AI Job Week 1 Epic).

### Batch Get Achievements

Fetch multiple achievements in a single request (90% API call reduction).

```http
POST /tech-doc-integration/batch-get
Content-Type: application/json

{
  "achievement_ids": [25, 26, 27]
}
```

**Response:**
```json
[
  {
    "id": 25,
    "title": "Implemented Kubernetes Auto-scaling",
    "category": "infrastructure",
    "impact_score": 95.0,
    "business_value": "$50K annual savings",
    "tags": ["kubernetes", "cost-optimization"],
    "portfolio_ready": true
  }
]
```

### Get Content-Ready Achievements

Get achievements ready for content generation.

```http
GET /tech-doc-integration/content-ready?limit=20
```

**Response:**
```json
[
  {
    "id": 26,
    "title": "AI Content Generation Pipeline",
    "category": "ai_ml",
    "impact_score": 92.0,
    "content_potential": "high",
    "suggested_formats": ["case_study", "technical_blog"]
  }
]
```

### Get Recent Highlights

Get recent high-impact achievements.

```http
POST /tech-doc-integration/recent-highlights?days=30&min_impact_score=85&limit=10
```

**Response:**
```json
[
  {
    "id": 27,
    "title": "Built Real-time Analytics Dashboard",
    "completed_at": "2025-01-28T15:30:00Z",
    "impact_score": 88.0,
    "highlight_reason": "recent_high_impact"
  }
]
```

### Get Company-Targeted Achievements

Get achievements relevant to specific companies.

```http
POST /tech-doc-integration/company-targeted?company_name=anthropic&limit=20
```

**Request Body (optional):**
```json
{
  "categories": ["ai_ml", "llm", "automation"]
}
```

**Response:**
```json
[
  {
    "id": 28,
    "title": "LLM Safety Framework Implementation",
    "category": "ai_ml",
    "relevance_score": 0.95,
    "matching_keywords": ["ai_safety", "llm", "responsible_ai"]
  }
]
```

### Content Opportunities Statistics

Get analytics on content generation opportunities.

```http
GET /tech-doc-integration/stats/content-opportunities
```

**Response:**
```json
{
  "total_content_ready": 15,
  "high_impact_opportunities": 12,
  "recent_achievements": 8,
  "by_category": {
    "feature": 6,
    "optimization": 3,
    "ai_ml": 4,
    "infrastructure": 2
  },
  "content_potential": {
    "total_articles": 45,
    "case_studies": 15,
    "technical_blogs": 20,
    "linkedin_posts": 10
  }
}
```

### Update Sync Status

Update content generation status for an achievement.

```http
POST /tech-doc-integration/sync-status?achievement_id=25&content_generated=true
```

**Query Parameters:**
- `platforms` (array): Platforms where content was published

**Response:**
```json
{
  "status": "updated",
  "achievement_id": 25,
  "content_generated": true,
  "platforms": ["linkedin", "medium"],
  "last_sync": "2025-02-04T10:00:00Z"
}
```

### Get Achievements by Category

Get achievements for a specific category.

```http
GET /tech-doc-integration/categories/ai_ml?limit=10
```

**Response:**
```json
[
  {
    "id": 29,
    "title": "Automated ML Model Deployment Pipeline",
    "category": "ai_ml",
    "impact_score": 87.0,
    "skills_demonstrated": ["MLOps", "Python", "Kubernetes"]
  }
]
```

### Company Keywords Reference

Supported companies and their matching keywords:

| Company | Keywords |
|---------|----------|
| notion | collaboration, productivity, workspace, real-time |
| anthropic | ai_safety, llm, responsible_ai, claude |
| jasper | content_generation, marketing_ai, copywriting |
| stripe | payments, fintech, api, developer_experience |
| databricks | data_engineering, spark, ml_platform |
| weights_biases | mlops, experiment_tracking, model_monitoring |
| cohere | nlp, embeddings, enterprise_ai |
| runway | creative_ai, video_generation, visual_ai |
| stability | stable_diffusion, open_source_ai, image_generation |
| hugging_face | transformers, model_hub, ml_community |

## Webhooks

### GitHub Webhook

Receive GitHub PR events.

```http
POST /webhooks/github
X-Hub-Signature-256: sha256=<signature>
Content-Type: application/json

{
  "action": "closed",
  "pull_request": {
    "merged": true,
    "number": 123,
    "title": "Optimize API performance",
    ...
  }
}
```

### Configure Webhook

Configure webhook settings.

```http
POST /webhooks/config
Content-Type: application/json

{
  "provider": "github",
  "events": ["pull_request.closed"],
  "url": "https://api.achievements.com/webhooks/github",
  "secret": "webhook-secret-key"
}
```

## Error Responses

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Achievement not found",
    "details": {
      "achievement_id": 999
    }
  },
  "request_id": "req_123456789"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `UNAUTHORIZED` | 401 | Missing or invalid auth token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Resource doesn't exist |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

### Rate Limiting

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## SDK Examples

### Python SDK

```python
from achievement_collector import AchievementClient

client = AchievementClient(
    api_key="your-api-key",
    base_url="http://localhost:8000/api/v1"
)

# Create achievement from PR
achievement = await client.achievements.create_from_pr(
    pr_number=123,
    analyze=True,
    generate_stories=True
)

# Search achievements
results = await client.achievements.search(
    category="optimization",
    min_impact_score=70,
    skills=["Python", "Redis"]
)

# Generate portfolio
portfolio = await client.export.to_portfolio(
    achievement_ids=[1, 2, 3],
    format="markdown"
)

# Get analytics
analytics = await client.analytics.get_performance(
    period="monthly",
    year=2025
)
```

### JavaScript/TypeScript SDK

```typescript
import { AchievementClient } from '@achievement-collector/sdk';

const client = new AchievementClient({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:8000/api/v1'
});

// Create achievement from PR
const achievement = await client.achievements.createFromPR({
  prNumber: 123,
  analyze: true,
  generateStories: true
});

// Search achievements
const results = await client.achievements.search({
  category: 'optimization',
  minImpactScore: 70,
  skills: ['Python', 'Redis']
});

// Generate portfolio
const portfolio = await client.export.toPortfolio({
  achievementIds: [1, 2, 3],
  format: 'markdown'
});
```

### cURL Examples

```bash
# Create achievement
curl -X POST http://localhost:8000/api/v1/achievements \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Optimized API Gateway",
    "category": "optimization",
    "impact_score": 85
  }'

# Get achievements
curl http://localhost:8000/api/v1/achievements?min_impact_score=70 \
  -H "Authorization: Bearer your-api-key"

# Generate stories
curl -X POST http://localhost:8000/api/v1/stories/generate \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"analysis": {...}}'
```

## API Versioning

The API uses URL versioning. Current version: `v1`

Future versions will maintain backward compatibility for at least 6 months after new version release.

## Support

- API Status: https://status.achievements.com
- Documentation: https://docs.achievements.com
- Support: api-support@achievements.com