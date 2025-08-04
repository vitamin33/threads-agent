# Tech Documentation Generator Integration

This document describes the integration endpoints added to the achievement_collector service specifically for the tech_doc_generator service.

## Overview

The integration provides optimized endpoints for content generation workflows, reducing API calls and improving performance through batch operations and targeted queries.

## New Endpoints

### 1. Batch Get Achievements
**POST** `/tech-doc-integration/batch-get`

Fetch multiple achievements in a single request.

```json
// Request
{
  "achievement_ids": [1, 2, 3, 4, 5]
}

// Response
[
  {
    "id": 1,
    "title": "Implemented AI-Powered Pipeline",
    "impact_score": 92.5,
    // ... full achievement data
  },
  // ... more achievements
]
```

### 2. Recent Highlights
**POST** `/tech-doc-integration/recent-highlights`

Get recent high-impact achievements for weekly content generation.

Parameters:
- `days` (int, default: 7): Number of days to look back
- `min_impact_score` (float, default: 75.0): Minimum impact threshold
- `limit` (int, default: 10): Maximum results

```bash
curl -X POST "http://localhost:8090/tech-doc-integration/recent-highlights?days=7&min_impact_score=80&limit=5"
```

### 3. Company-Targeted Achievements
**POST** `/tech-doc-integration/company-targeted`

Get achievements relevant for specific companies with intelligent keyword matching.

Parameters:
- `company_name` (string, required): Target company name
- `categories` (array, optional): Category filter
- `limit` (int, default: 20): Maximum results

Supported companies with custom keywords:
- **notion**: productivity, collaboration, documentation, knowledge, workflow
- **jasper**: ai, content, generation, nlp, automation, gpt, llm
- **anthropic**: ai, safety, alignment, llm, ethical, research, claude
- **stripe**: payment, fintech, api, billing, subscription, finance
- **databricks**: data, spark, ml, pipeline, lakehouse, analytics
- **scale**: ml, data, annotation, training, dataset, labeling
- **huggingface**: nlp, transformer, model, dataset, ml, ai
- **openai**: gpt, ai, llm, api, generation, assistant
- **cohere**: nlp, embedding, search, retrieval, rag, ai
- **runway**: ml, video, generation, creative, ai, media

### 4. Advanced Filter
**POST** `/tech-doc-integration/filter`

Complex filtering with multiple criteria.

```json
// Request
{
  "categories": ["automation", "ai"],
  "min_impact_score": 80,
  "portfolio_ready_only": true,
  "days_back": 30,
  "tags": ["ml", "optimization"],
  "company_keywords": ["scalability", "performance"]
}
```

### 5. Content-Ready Summaries
**GET** `/tech-doc-integration/content-ready`

Lightweight endpoint for scanning content opportunities.

Parameters:
- `limit` (int, default: 100): Maximum results

Returns summary objects with minimal data for fast listing.

### 6. Sync Status Update
**POST** `/tech-doc-integration/sync-status`

Mark achievements as processed by tech_doc_generator.

Parameters:
- `achievement_id` (int, required): Achievement ID
- `content_generated` (bool, default: true): Generation status
- `platforms` (array): Platforms where content was published

### 7. Content Opportunities Stats
**GET** `/tech-doc-integration/stats/content-opportunities`

Analytics on untapped content generation potential.

```json
// Response
{
  "total_content_ready": 145,
  "high_impact_opportunities": 42,
  "recent_achievements": 23,
  "unprocessed_achievements": 89,
  "by_category": {
    "automation": 35,
    "feature": 28,
    "performance": 22,
    // ...
  },
  "content_generation_rate": "38.6%"
}
```

## Integration Benefits

1. **Performance**: Batch operations reduce API calls by up to 90%
2. **Targeting**: Company-specific filtering improves content relevance
3. **Analytics**: Track content generation coverage and opportunities
4. **Optimization**: Purpose-built queries for content workflows

## Usage Example

```python
from services.tech_doc_generator.app.clients.achievement_client import AchievementClient

async def generate_weekly_content():
    client = AchievementClient()
    
    async with client:
        # Get recent highlights
        highlights = await client.get_recent_highlights(
            days=7, 
            min_impact_score=80
        )
        
        # Generate content for each
        for achievement in highlights:
            articles = await generate_articles(achievement)
            
        # Mark as processed
        for achievement in highlights:
            await client.update_sync_status(
                achievement.id,
                content_generated=True,
                platforms=["linkedin", "devto"]
            )
```

## Deployment

The integration endpoints are automatically included when the achievement_collector service is deployed. No additional configuration is required.

## Monitoring

Track integration usage through Prometheus metrics:
- `tech_doc_integration_requests_total`
- `tech_doc_integration_batch_size`
- `tech_doc_integration_response_time`

## Future Enhancements

1. **Webhook Support**: Real-time notifications for new high-impact achievements
2. **Content Templates**: Store preferred article templates per achievement category
3. **AI Recommendations**: ML-based content opportunity scoring
4. **Publishing Status**: Track which achievements have been published where