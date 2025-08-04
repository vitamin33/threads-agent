# Tech Doc Generator - API Reference

## Base URL
```
http://tech-doc-generator:8000
```

## Authentication
Optional API key authentication via header:
```
X-API-Key: your-api-key
```

## Endpoints

### Achievement Article Generation

#### Generate Single Article
```http
POST /achievement-articles/generate
```

**Request Body:**
```json
{
  "achievement_id": 25,
  "article_type": "case_study",
  "target_company": "anthropic",
  "platform": "linkedin",
  "include_code_samples": true,
  "seo_optimize": true
}
```

**Response:**
```json
{
  "article": {
    "id": "art_123",
    "title": "How I Reduced Infrastructure Costs by 40% with Kubernetes Auto-scaling",
    "content": "...",
    "platform": "linkedin",
    "metadata": {
      "keywords": ["kubernetes", "cost-optimization", "auto-scaling"],
      "reading_time": 5,
      "target_audience": "DevOps Engineers"
    },
    "achievement_id": 25,
    "created_at": "2025-02-04T10:00:00Z"
  }
}
```

#### Batch Generate Articles
```http
POST /achievement-articles/batch-generate
```

**Request Body:**
```json
{
  "achievement_ids": [25, 26, 27],
  "article_types": ["blog_post", "case_study"],
  "platforms": ["medium", "devto"],
  "generation_options": {
    "include_visuals": true,
    "tone": "professional",
    "length": "medium"
  }
}
```

**Response:**
```json
{
  "articles": [
    {
      "achievement_id": 25,
      "generated_articles": [
        {
          "type": "blog_post",
          "platform": "medium",
          "title": "...",
          "url": null
        }
      ]
    }
  ],
  "summary": {
    "total_generated": 6,
    "platforms": {
      "medium": 3,
      "devto": 3
    }
  }
}
```

### Content Opportunities

#### Get Content Opportunities
```http
GET /achievement-articles/opportunities
```

**Query Parameters:**
- `min_impact_score` (float): Minimum impact score filter
- `categories` (array): Filter by categories
- `days` (int): Recent achievements within X days

**Response:**
```json
{
  "opportunities": {
    "total_achievements": 15,
    "content_ready": 12,
    "high_impact": 8,
    "by_category": {
      "feature": 6,
      "optimization": 3,
      "infrastructure": 3
    },
    "potential_articles": 45,
    "recommended_focus": ["ai_ml", "infrastructure"]
  }
}
```

### Company Portfolio

#### Generate Company Portfolio
```http
POST /achievement-articles/company-portfolio
```

**Request Body:**
```json
{
  "company_name": "anthropic",
  "max_articles": 10,
  "article_types": ["case_study", "technical_deep_dive"],
  "focus_areas": ["ai_safety", "llm_optimization"],
  "portfolio_options": {
    "include_metrics": true,
    "highlight_impact": true,
    "technical_depth": "high"
  }
}
```

**Response:**
```json
{
  "portfolio": {
    "company": "anthropic",
    "articles": [
      {
        "title": "Building Safer AI Systems: A Case Study",
        "type": "case_study",
        "relevance_score": 0.95,
        "key_points": ["..."],
        "achievement_id": 26
      }
    ],
    "portfolio_url": "/portfolios/anthropic_2025_02_04",
    "total_articles": 8
  }
}
```

### Content Analytics

#### Get Generation Statistics
```http
GET /achievement-articles/stats
```

**Response:**
```json
{
  "statistics": {
    "total_generated": 156,
    "last_7_days": 23,
    "by_platform": {
      "linkedin": 45,
      "medium": 38,
      "devto": 32,
      "personal_blog": 41
    },
    "by_type": {
      "case_study": 67,
      "blog_post": 54,
      "technical_tutorial": 35
    },
    "average_generation_time": 2.3,
    "quality_scores": {
      "average": 0.88,
      "high_quality": 134
    }
  }
}
```

### Publishing Integration

#### Publish to Platform
```http
POST /achievement-articles/publish
```

**Request Body:**
```json
{
  "article_id": "art_123",
  "platform": "linkedin",
  "publish_options": {
    "schedule": "2025-02-05T09:00:00Z",
    "hashtags": ["#DevOps", "#Kubernetes", "#CostOptimization"],
    "notify_connections": true
  }
}
```

**Response:**
```json
{
  "status": "scheduled",
  "platform": "linkedin",
  "scheduled_time": "2025-02-05T09:00:00Z",
  "article_id": "art_123",
  "platform_post_id": null
}
```

### Health & Status

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "achievement_collector": "connected",
    "database": "connected",
    "cache": "connected"
  },
  "version": "1.0.0"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "detail": "achievement_id must be a positive integer",
  "code": "INVALID_ACHIEVEMENT_ID"
}
```

### 404 Not Found
```json
{
  "error": "Achievement not found",
  "detail": "No achievement with ID 999",
  "code": "ACHIEVEMENT_NOT_FOUND"
}
```

### 429 Rate Limited
```json
{
  "error": "Rate limit exceeded",
  "detail": "Maximum 100 requests per hour",
  "retry_after": 3600
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred",
  "request_id": "req_abc123"
}
```

## Rate Limits

- **Standard**: 100 requests/hour
- **Batch operations**: 20 requests/hour
- **Portfolio generation**: 10 requests/hour

## Best Practices

1. **Use Batch Endpoints**: For multiple articles, always use batch endpoints
2. **Cache Responses**: Achievement data can be cached for up to 1 hour
3. **Handle Retries**: Implement exponential backoff for failed requests
4. **Monitor Rate Limits**: Check `X-RateLimit-*` headers in responses

## SDK Examples

### Python
```python
from tech_doc_generator import Client

client = Client(base_url="http://tech-doc-generator:8000")

# Generate article
article = await client.generate_article(
    achievement_id=25,
    article_type="case_study",
    platform="linkedin"
)

# Batch generate
articles = await client.batch_generate(
    achievement_ids=[25, 26, 27],
    platforms=["medium", "devto"]
)
```

### cURL
```bash
# Generate single article
curl -X POST http://tech-doc-generator:8000/achievement-articles/generate \
  -H "Content-Type: application/json" \
  -d '{
    "achievement_id": 25,
    "article_type": "case_study",
    "platform": "linkedin"
  }'

# Get opportunities
curl http://tech-doc-generator:8000/achievement-articles/opportunities?min_impact_score=85
```

## Webhook Events

Configure webhooks to receive notifications:

- `article.generated` - Article successfully generated
- `article.published` - Article published to platform
- `portfolio.created` - Company portfolio created
- `generation.failed` - Article generation failed

---

**Version**: 1.0.0  
**Last Updated**: 2025-02-04