# Viral Scraper API Reference

## Base Information

- **Service**: Viral Content Scraper
- **Base URL**: `http://viral-scraper:8080`
- **Content-Type**: `application/json`
- **Version**: v1.0
- **OpenAPI**: Available at `/docs` (Swagger UI) and `/redoc`

## Authentication

Currently no authentication required. For production deployment, consider:
- API Keys for service-to-service communication
- Rate limiting based on client identification
- Integration with existing auth middleware

## Core Endpoints

### Health Check

```http
GET /health
```

**Description**: Service health validation endpoint

**Response**:
```json
{
  "status": "healthy",
  "service": "viral-scraper"
}
```

**Status Codes**:
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service degraded

---

### Trigger Account Scraping

```http
POST /scrape/account/{account_id}
```

**Description**: Initiates content scraping for a specific Threads account

**Path Parameters**:
- `account_id` (string, required): Target Threads account identifier

**Request Body** (optional):
```json
{
  "max_posts": 50,
  "days_back": 7,
  "min_performance_percentile": 99.0
}
```

**Request Schema**:
```python
class ScrapeRequest(BaseModel):
    max_posts: Optional[int] = 50
    days_back: Optional[int] = 7
    min_performance_percentile: Optional[float] = 99.0
```

**Success Response** (`200 OK`):
```json
{
  "task_id": "uuid-v4-string",
  "account_id": "target_account_id",
  "status": "queued",
  "max_posts": 50,
  "days_back": 7,
  "min_performance_percentile": 99.0
}
```

**Rate Limited Response** (`429 Too Many Requests`):
```json
{
  "detail": {
    "error": "Rate limit exceeded for this account",
    "retry_after": 45
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request parameters
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Service error

---

### Get Scraping Task Status

```http
GET /scrape/tasks/{task_id}/status
```

**Description**: Retrieve status of a previously submitted scraping task

**Path Parameters**:
- `task_id` (string, required): Task identifier from scrape request

**Response**:
```json
{
  "task_id": "uuid-v4-string",
  "status": "queued|processing|completed|failed"
}
```

**Status Values**:
- `queued`: Task submitted but not started
- `processing`: Currently scraping content
- `completed`: Successfully finished
- `failed`: Error occurred during processing

---

### Get Viral Posts

```http
GET /viral-posts
```

**Description**: Retrieve viral posts with optional filtering

**Query Parameters**:
- `account_id` (string, optional): Filter by specific account
- `limit` (integer, optional): Number of posts to return (default: 20, max: 100)
- `page` (integer, optional): Page number for pagination (default: 1)
- `min_engagement_rate` (float, optional): Minimum engagement rate filter (0.0-1.0)
- `top_1_percent_only` (boolean, optional): Only return top 1% posts (default: false)

**Example Requests**:
```bash
# Get all viral posts (paginated)
GET /viral-posts?limit=20&page=1

# Get top 1% posts only
GET /viral-posts?top_1_percent_only=true

# Filter by account and engagement rate
GET /viral-posts?account_id=viral_account&min_engagement_rate=0.15

# Combined filters
GET /viral-posts?account_id=tech_account&top_1_percent_only=true&limit=10
```

**Response**:
```json
{
  "posts": [
    {
      "content": "This is a viral post about AI trends!",
      "account_id": "tech_influencer_123",
      "post_url": "https://threads.net/tech_influencer_123/post/abc123",
      "timestamp": "2023-12-01T10:00:00Z",
      "likes": 5000,
      "comments": 200,
      "shares": 1000,
      "engagement_rate": 0.25,
      "performance_percentile": 99.5
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 20
}
```

**ViralPost Schema**:
```python
class ViralPost(BaseModel):
    content: str
    account_id: str
    post_url: str
    timestamp: datetime
    likes: int = Field(ge=0)
    comments: int = Field(ge=0)
    shares: int = Field(ge=0)
    engagement_rate: float = Field(ge=0.0, le=1.0)
    performance_percentile: float = Field(ge=0.0, le=100.0)
```

---

### Get Viral Posts by Account

```http
GET /viral-posts/{account_id}
```

**Description**: Retrieve all viral posts for a specific account

**Path Parameters**:
- `account_id` (string, required): Target account identifier

**Response**:
```json
{
  "account_id": "target_account",
  "posts": [
    {
      "content": "Account-specific viral content",
      "account_id": "target_account",
      "post_url": "https://threads.net/target_account/post/xyz789",
      "timestamp": "2023-12-01T15:30:00Z",
      "likes": 3000,
      "comments": 150,
      "shares": 500,
      "engagement_rate": 0.18,
      "performance_percentile": 97.2
    }
  ]
}
```

---

### Get Rate Limit Status

```http
GET /rate-limit/status/{account_id}
```

**Description**: Check rate limiting status for a specific account

**Path Parameters**:
- `account_id` (string, required): Account to check rate limit for

**Response**:
```json
{
  "account_id": "target_account",
  "requests_remaining": 0,
  "reset_time": "2023-12-01T10:01:00"
}
```

**Fields**:
- `requests_remaining`: Number of requests available in current window
- `reset_time`: ISO 8601 timestamp when rate limit resets

## Rate Limiting

### Current Configuration
- **Window**: 60 seconds
- **Requests per window**: 1 per account
- **Scope**: Per account (not global)

### Rate Limit Headers

When rate limited, responses include:
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": {
    "error": "Rate limit exceeded for this account",
    "retry_after": 45
  }
}
```

### Best Practices

1. **Check Rate Limit Status**: Use `/rate-limit/status/{account_id}` before scraping
2. **Handle 429 Responses**: Implement exponential backoff
3. **Respect retry_after**: Wait the specified seconds before retrying
4. **Distribute Requests**: Scrape different accounts to avoid limits

```python
import asyncio
import httpx

async def safe_scrape_account(client: httpx.AsyncClient, account_id: str):
    """Safely scrape with rate limit handling"""
    try:
        response = await client.post(f"/scrape/account/{account_id}")
        if response.status_code == 429:
            retry_after = response.json()["detail"]["retry_after"]
            print(f"Rate limited. Waiting {retry_after}s...")
            await asyncio.sleep(retry_after)
            return await client.post(f"/scrape/account/{account_id}")
        return response
    except Exception as e:
        print(f"Error scraping {account_id}: {e}")
        return None
```

## Error Handling

### Standard Error Format

All errors follow FastAPI's standard format:
```json
{
  "detail": "Error description"
}
```

Or structured errors:
```json
{
  "detail": {
    "error": "Descriptive error message",
    "code": "ERROR_CODE",
    "retry_after": 60
  }
}
```

### Common Error Scenarios

#### 400 Bad Request
```json
{
  "detail": [
    {
      "loc": ["body", "max_posts"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": 1}
    }
  ]
}
```

#### 404 Not Found
```json
{
  "detail": "Task not found"
}
```

#### 429 Too Many Requests
```json
{
  "detail": {
    "error": "Rate limit exceeded for this account",
    "retry_after": 45
  }
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## SDK Examples

### Python AsyncIO Client

```python
import httpx
import asyncio
from typing import List, Optional

class ViralScraperClient:
    def __init__(self, base_url: str = "http://viral-scraper:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def health_check(self) -> dict:
        """Check service health"""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def scrape_account(
        self, 
        account_id: str, 
        max_posts: int = 50,
        days_back: int = 7,
        min_performance_percentile: float = 99.0
    ) -> dict:
        """Trigger account scraping"""
        payload = {
            "max_posts": max_posts,
            "days_back": days_back,
            "min_performance_percentile": min_performance_percentile
        }
        
        response = await self.client.post(
            f"{self.base_url}/scrape/account/{account_id}",
            json=payload
        )
        
        if response.status_code == 429:
            error_detail = response.json()["detail"]
            raise RateLimitError(
                f"Rate limit exceeded. Retry after {error_detail['retry_after']}s"
            )
        
        response.raise_for_status()
        return response.json()
    
    async def get_viral_posts(
        self,
        account_id: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
        min_engagement_rate: Optional[float] = None,
        top_1_percent_only: bool = False
    ) -> List[dict]:
        """Get viral posts with filtering"""
        params = {
            "limit": limit,
            "page": page,
            "top_1_percent_only": top_1_percent_only
        }
        
        if account_id:
            params["account_id"] = account_id
        if min_engagement_rate:
            params["min_engagement_rate"] = min_engagement_rate
        
        response = await self.client.get(
            f"{self.base_url}/viral-posts",
            params=params
        )
        response.raise_for_status()
        return response.json()["posts"]
    
    async def get_rate_limit_status(self, account_id: str) -> dict:
        """Check rate limit status"""
        response = await self.client.get(
            f"{self.base_url}/rate-limit/status/{account_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass

# Usage example
async def main():
    client = ViralScraperClient()
    
    try:
        # Check service health
        health = await client.health_check()
        print(f"Service status: {health['status']}")
        
        # Scrape account with rate limit handling
        account_id = "viral_tech_account"
        
        # Check rate limit first
        rate_status = await client.get_rate_limit_status(account_id)
        if rate_status["requests_remaining"] > 0:
            # Trigger scraping
            task = await client.scrape_account(
                account_id=account_id,
                max_posts=100,
                min_performance_percentile=95.0
            )
            print(f"Scraping task: {task['task_id']}")
        else:
            print(f"Rate limited. Reset at: {rate_status['reset_time']}")
        
        # Get top viral posts
        top_posts = await client.get_viral_posts(
            top_1_percent_only=True,
            limit=10
        )
        print(f"Found {len(top_posts)} top viral posts")
        
    except RateLimitError as e:
        print(f"Rate limit error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

class ViralScraperClient {
    constructor(baseUrl = 'http://viral-scraper:8080') {
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    async scrapeAccount(accountId, options = {}) {
        const payload = {
            max_posts: options.maxPosts || 50,
            days_back: options.daysBack || 7,
            min_performance_percentile: options.minPerformancePercentile || 99.0
        };

        try {
            const response = await this.client.post(`/scrape/account/${accountId}`, payload);
            return response.data;
        } catch (error) {
            if (error.response?.status === 429) {
                const retryAfter = error.response.data.detail.retry_after;
                throw new RateLimitError(`Rate limit exceeded. Retry after ${retryAfter}s`);
            }
            throw error;
        }
    }

    async getViralPosts(options = {}) {
        const params = {
            limit: options.limit || 20,
            page: options.page || 1,
            top_1_percent_only: options.top1PercentOnly || false
        };

        if (options.accountId) params.account_id = options.accountId;
        if (options.minEngagementRate) params.min_engagement_rate = options.minEngagementRate;

        const response = await this.client.get('/viral-posts', { params });
        return response.data.posts;
    }

    async getRateLimitStatus(accountId) {
        const response = await this.client.get(`/rate-limit/status/${accountId}`);
        return response.data;
    }
}

class RateLimitError extends Error {
    constructor(message) {
        super(message);
        this.name = 'RateLimitError';
    }
}

// Usage example
async function main() {
    const client = new ViralScraperClient();

    try {
        // Get top viral posts
        const topPosts = await client.getViralPosts({
            top1PercentOnly: true,
            limit: 10
        });
        console.log(`Found ${topPosts.length} top viral posts`);

        // Scrape account with rate limit check
        const accountId = 'viral_tech_account';
        const rateStatus = await client.getRateLimitStatus(accountId);
        
        if (rateStatus.requests_remaining > 0) {
            const task = await client.scrapeAccount(accountId, {
                maxPosts: 100,
                minPerformancePercentile: 95.0
            });
            console.log(`Scraping task: ${task.task_id}`);
        } else {
            console.log(`Rate limited. Reset at: ${rateStatus.reset_time}`);
        }
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main().catch(console.error);
```

## OpenAPI Specification

The service automatically generates OpenAPI 3.0 specification:

- **Swagger UI**: `http://viral-scraper:8080/docs`
- **ReDoc**: `http://viral-scraper:8080/redoc`
- **JSON Schema**: `http://viral-scraper:8080/openapi.json`

## Performance Considerations

### Request Timing
- Health check: ~1ms
- Rate limit check: ~1ms
- Scrape request: ~10-50ms
- Viral posts query: ~10-100ms (depending on dataset size)

### Throughput Limits
- Concurrent requests: 100+ (per instance)
- Rate limiting: 1 request/minute per account
- Memory usage: ~10MB (will grow with account tracking)

### Optimization Recommendations
1. Use connection pooling for high-volume clients
2. Implement client-side caching for viral posts
3. Batch multiple account queries where possible
4. Monitor rate limit status to avoid 429 responses

---

**Last Updated**: 2025-08-03
**API Version**: v1.0
**Service**: Viral Content Scraper (CRA-280)