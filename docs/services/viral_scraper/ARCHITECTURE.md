# Viral Scraper Architecture

## Executive Summary

The Viral Content Scraper Service implements a microservice architecture pattern within the Threads-Agent Stack, providing ethical content discovery capabilities for the E7 - Viral Learning Flywheel. This document details the architectural decisions, component relationships, and integration patterns.

## System Architecture

### High-Level Architecture

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                Threads-Agent Stack                      │
                    └─────────────────────────────────────────────────────────┘
                                              │
                                              ▼
    ┌─────────────────┐    ┌─────────────────────────────────┐    ┌─────────────────┐
    │                 │    │                                 │    │                 │
    │  Orchestrator   │◄──►│       Viral Scraper            │◄──►│  Viral Engine   │
    │  (Coordinator)  │    │     (Content Discovery)        │    │ (Pattern Learn) │
    │                 │    │                                 │    │                 │
    └─────────────────┘    └─────────────────────────────────┘    └─────────────────┘
                                              │
                                              ▼
                           ┌─────────────────────────────────┐
                           │                                 │
                           │      External Services          │
                           │   • Threads API                 │
                           │   • Content Sources             │
                           │                                 │
                           └─────────────────────────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Viral Scraper Service                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │                 │    │                 │    │                 │           │
│  │   FastAPI       │◄──►│   Rate Limiter  │◄──►│  ViralPost      │           │
│  │   Service       │    │   (Ethical)     │    │  Model          │           │
│  │                 │    │                 │    │                 │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│           │                       │                       │                   │
│           ▼                       ▼                       ▼                   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │                 │    │                 │    │                 │           │
│  │ HTTP Endpoints  │    │ Memory Store    │    │ Data Validation │           │
│  │ • /scrape/*     │    │ • Account Rate  │    │ • Type Safety   │           │
│  │ • /viral-posts  │    │ • Time Windows  │    │ • Performance   │           │
│  │ • /health       │    │                 │    │   Percentiles   │           │
│  │                 │    │                 │    │                 │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Design Patterns

### 1. Microservice Pattern

**Implementation**: Independent service with dedicated responsibility
- **Benefits**: Isolated deployment, technology choice flexibility, independent scaling
- **Trade-offs**: Network latency, distributed system complexity

```python
# Service boundary definition
class ViralScraperService:
    """
    Single Responsibility: Viral content discovery and extraction
    Dependencies: Minimal external dependencies
    Communication: HTTP/REST API
    """
    def __init__(self):
        self.rate_limiter = RateLimiter()  # Internal dependency
        self.app = FastAPI()              # Framework choice
```

### 2. Rate Limiting Pattern

**Implementation**: Per-account sliding window rate limiting
- **Pattern**: Token bucket with time-based windows
- **Justification**: Ethical scraping compliance, API protection

```python
class RateLimiter:
    """
    Pattern: Sliding Window Rate Limiting
    Scope: Per-account isolation
    Storage: In-memory (upgradeable to Redis)
    """
    def __init__(self, requests_per_window: int, window_seconds: int):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.requests: Dict[str, datetime] = {}  # Account -> Last request time
```

### 3. Data Transfer Object Pattern

**Implementation**: Pydantic models for type-safe data transfer
- **Benefits**: Validation, serialization, documentation generation
- **Usage**: API request/response models, internal data structures

```python
class ViralPost(BaseModel):
    """
    Pattern: Data Transfer Object
    Purpose: Type-safe content representation
    Validation: Built-in with Pydantic
    """
    content: str = Field(..., description="Post content text")
    engagement_rate: float = Field(..., ge=0.0, le=1.0)
    performance_percentile: float = Field(..., ge=0.0, le=100.0)
```

### 4. Dependency Injection Pattern

**Implementation**: Constructor-based dependency injection
- **Benefits**: Testability, flexibility, loose coupling

```python
# Dependency injection for testability
app = FastAPI()
rate_limiter = RateLimiter(requests_per_window=1, window_seconds=60)

@app.post("/scrape/account/{account_id}")
async def scrape_account(account_id: str, limiter: RateLimiter = Depends(lambda: rate_limiter)):
    if not limiter.check_rate_limit(account_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

## Component Details

### 1. FastAPI Service Layer

**Architecture Pattern**: Layered Architecture with separation of concerns

```python
# Presentation Layer
@app.post("/scrape/account/{account_id}")
async def scrape_account(account_id: str, request: Optional[ScrapeRequest] = None):
    """API endpoint handling HTTP requests"""
    pass

# Business Logic Layer  
def validate_scrape_request(request: ScrapeRequest) -> bool:
    """Business rule validation"""
    pass

# Data Access Layer
def store_viral_post(post: ViralPost) -> None:
    """Data persistence (future implementation)"""
    pass
```

**Responsibilities**:
- HTTP request/response handling
- Request validation and transformation
- Error handling and status code management
- OpenAPI documentation generation

**Design Decisions**:
- **FastAPI Choice**: Modern async framework with automatic documentation
- **Async/Await**: Non-blocking I/O for better concurrency
- **Pydantic Integration**: Automatic validation and serialization

### 2. Rate Limiting Component

**Architecture Pattern**: Strategy Pattern for rate limiting algorithms

```python
from abc import ABC, abstractmethod

class RateLimitStrategy(ABC):
    @abstractmethod
    def check_rate_limit(self, identifier: str) -> bool:
        pass

class SlidingWindowRateLimiter(RateLimitStrategy):
    """Current implementation: Simple sliding window"""
    def check_rate_limit(self, account_id: str) -> bool:
        # Implementation here
        pass

class TokenBucketRateLimiter(RateLimitStrategy):
    """Future implementation: Token bucket algorithm"""
    def check_rate_limit(self, account_id: str) -> bool:
        # More sophisticated rate limiting
        pass
```

**Current Implementation**:
- **Algorithm**: Simple sliding window per account
- **Storage**: In-memory dictionary (not horizontally scalable)
- **Granularity**: Per-account isolation

**Future Evolution**:
- **Distributed Storage**: Redis-based rate limiting for horizontal scaling
- **Algorithm Enhancement**: Token bucket or leaky bucket algorithms
- **Configuration**: Dynamic rate limit adjustment based on account behavior

### 3. Data Model Layer

**Architecture Pattern**: Domain-Driven Design with value objects

```python
class ViralPost(BaseModel):
    """
    Domain Entity: Represents viral content with business rules
    Value Object: Immutable content representation
    """
    
    # Core content attributes
    content: str
    account_id: str
    post_url: str
    timestamp: datetime
    
    # Engagement metrics (business logic embedded)
    likes: int = Field(ge=0)
    comments: int = Field(ge=0) 
    shares: int = Field(ge=0)
    engagement_rate: float = Field(ge=0.0, le=1.0)
    
    # Performance analysis (domain-specific calculation)
    performance_percentile: float = Field(ge=0.0, le=100.0)
    
    def is_top_1_percent(self) -> bool:
        """Business rule: Top 1% performance tier identification"""
        return self.performance_percentile > 99.0
```

**Design Principles**:
- **Immutability**: Value objects don't change after creation
- **Validation**: Built-in constraints ensure data integrity
- **Business Logic**: Domain methods encapsulate business rules
- **Type Safety**: Pydantic provides runtime type checking

## Integration Architecture

### 1. Service-to-Service Communication

**Pattern**: Synchronous HTTP communication with async clients

```python
# Integration with Viral Engine
class ViralEngineClient:
    def __init__(self, base_url: str):
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def submit_viral_patterns(self, posts: List[ViralPost]):
        """Send discovered patterns to viral engine"""
        payload = {"posts": [post.dict() for post in posts]}
        response = await self.client.post("/patterns/ingest", json=payload)
        return response.json()

# Integration with Orchestrator
class OrchestratorIntegration:
    async def notify_scraping_complete(self, task_id: str, results: dict):
        """Notify orchestrator of completed scraping task"""
        pass
```

**Communication Patterns**:
- **Request/Response**: Synchronous operations (health checks, data queries)
- **Fire-and-Forget**: Asynchronous notifications (pattern submission)
- **Circuit Breaker**: Fault tolerance for external service calls

### 2. Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │    │ Viral Scraper   │    │  Viral Engine   │
│                 │    │                 │    │                 │
│ 1. Schedule     │───▶│ 2. Rate Check   │    │                 │
│    Scraping     │    │                 │    │                 │
│                 │    │ 3. Content      │    │                 │
│                 │    │    Discovery    │    │                 │
│                 │    │                 │    │                 │
│                 │    │ 4. Pattern      │───▶│ 5. Pattern      │
│                 │    │    Extraction   │    │    Learning     │
│                 │◄───│                 │    │                 │
│ 6. Results      │    │                 │    │                 │
│    Notification │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Data Transformation Pipeline**:
1. **Raw Content Ingestion**: External API responses
2. **Content Normalization**: Standardized ViralPost format  
3. **Performance Analysis**: Percentile calculation and ranking
4. **Pattern Extraction**: Feature extraction for learning
5. **Results Aggregation**: Summary statistics and insights

### 3. Event-Driven Architecture (Future)

**Planned Evolution**: Transition to event-driven patterns for better scalability

```python
# Future event-driven architecture
class ViralContentEvents:
    """Event types for viral content discovery"""
    
    SCRAPING_STARTED = "viral.scraping.started"
    CONTENT_DISCOVERED = "viral.content.discovered"
    PATTERN_IDENTIFIED = "viral.pattern.identified"
    SCRAPING_COMPLETED = "viral.scraping.completed"

class EventPublisher:
    async def publish(self, event_type: str, payload: dict):
        """Publish events to message broker"""
        pass

# Event-driven scraping workflow
async def scrape_account_async(account_id: str):
    await event_publisher.publish(
        ViralContentEvents.SCRAPING_STARTED,
        {"account_id": account_id, "timestamp": datetime.now()}
    )
    # ... scraping logic ...
    await event_publisher.publish(
        ViralContentEvents.SCRAPING_COMPLETED,
        {"account_id": account_id, "posts_found": len(posts)}
    )
```

## Scalability Architecture

### 1. Horizontal Scaling Considerations

**Current Limitations**:
- In-memory rate limiting prevents horizontal scaling
- No shared state between service instances
- Rate limits are per-instance, not globally consistent

**Solutions**:
```python
# Redis-based distributed rate limiting
class DistributedRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_rate_limit(self, account_id: str) -> bool:
        """Distributed rate limiting with Redis"""
        key = f"rate_limit:{account_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, self.window_seconds)
        return current <= self.requests_per_window
```

### 2. Performance Scaling Patterns

**Load Balancing Strategy**:
```yaml
# Kubernetes service configuration
apiVersion: v1
kind: Service
metadata:
  name: viral-scraper
spec:
  selector:
    app: viral-scraper
  ports:
  - port: 8080
  sessionAffinity: None  # Stateless service
  type: ClusterIP
```

**Auto-scaling Configuration**:
```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: viral-scraper-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: viral-scraper
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 3. Database Architecture (Future)

**Planned Data Persistence Layer**:
```python
# Database abstraction layer
from abc import ABC, abstractmethod

class ViralPostRepository(ABC):
    @abstractmethod
    async def save_post(self, post: ViralPost) -> str:
        pass
    
    @abstractmethod
    async def find_by_account(self, account_id: str) -> List[ViralPost]:
        pass

class PostgreSQLRepository(ViralPostRepository):
    """PostgreSQL implementation for production"""
    async def save_post(self, post: ViralPost) -> str:
        # PostgreSQL-specific implementation
        pass

class InMemoryRepository(ViralPostRepository):
    """In-memory implementation for testing"""
    def __init__(self):
        self.posts = {}
```

## Security Architecture

### 1. Security Principles

**Defense in Depth**:
- API rate limiting (DoS protection)
- Input validation (injection prevention)
- Minimal privileges (container security)
- Network segmentation (Kubernetes policies)

**Implementation**:
```python
# Input sanitization and validation
class SecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # Rate limiting check
        if not await self.check_global_rate_limit(request.client.host):
            raise HTTPException(status_code=429, detail="Global rate limit exceeded")
        
        # Input validation
        if not self.validate_input_safety(request):
            raise HTTPException(status_code=400, detail="Invalid input detected")
        
        response = await call_next(request)
        return response
```

### 2. Container Security

**Security Context**:
```yaml
# Kubernetes security configuration
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
```

**Network Policies**:
```yaml
# Network isolation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: viral-scraper-network-policy
spec:
  podSelector:
    matchLabels:
      app: viral-scraper
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: orchestrator
  egress:
  - to: []  # Allow outbound for content scraping
```

## Monitoring and Observability Architecture

### 1. Metrics Architecture

**Prometheus Integration**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
scrape_requests_total = Counter(
    'viral_scraper_requests_total',
    'Total scraping requests',
    ['account_id', 'status']
)

response_time_seconds = Histogram(
    'viral_scraper_response_seconds',
    'Response time in seconds',
    ['endpoint']
)

rate_limit_violations = Counter(
    'viral_scraper_rate_limit_violations_total',
    'Rate limit violations',
    ['account_id']
)

# Technical metrics
active_connections = Gauge(
    'viral_scraper_active_connections',
    'Active HTTP connections'
)
```

### 2. Logging Architecture

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

async def scrape_account(account_id: str):
    logger.info(
        "scraping_started",
        account_id=account_id,
        timestamp=datetime.now().isoformat(),
        correlation_id=request_id
    )
    
    try:
        # Scraping logic
        logger.info(
            "scraping_completed",
            account_id=account_id,
            posts_found=len(posts),
            duration_ms=duration
        )
    except Exception as e:
        logger.error(
            "scraping_failed",
            account_id=account_id,
            error=str(e),
            error_type=type(e).__name__
        )
```

### 3. Distributed Tracing

**OpenTelemetry Integration**:
```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Automatic instrumentation
FastAPIInstrumentor.instrument_app(app)

# Manual tracing for business logic
tracer = trace.get_tracer(__name__)

async def scrape_account(account_id: str):
    with tracer.start_as_current_span("scrape_account") as span:
        span.set_attribute("account_id", account_id)
        # Scraping logic
        span.set_attribute("posts_found", len(posts))
```

## Technology Stack Decisions

### 1. Framework Choice: FastAPI

**Rationale**:
- **Performance**: ASGI-based async framework
- **Type Safety**: Native Pydantic integration
- **Documentation**: Automatic OpenAPI generation
- **Ecosystem**: Rich middleware and extension ecosystem

**Alternatives Considered**:
- Django REST Framework: Too heavyweight for microservice
- Flask: Lacks native async support and type safety
- Starlette: Lower level, more boilerplate required

### 2. Data Validation: Pydantic

**Rationale**:
- **Type Safety**: Runtime type checking
- **Validation**: Rich validation rules and custom validators
- **Serialization**: Automatic JSON serialization/deserialization
- **Documentation**: Self-documenting models

**Integration Benefits**:
```python
# Automatic API documentation from Pydantic models
class ViralPost(BaseModel):
    """Viral post data model with automatic validation"""
    content: str = Field(..., description="Post content text", min_length=1)
    likes: int = Field(..., ge=0, description="Number of likes")
    
    class Config:
        schema_extra = {
            "example": {
                "content": "Amazing AI breakthrough!",
                "likes": 1000
            }
        }
```

### 3. Deployment: Container-First

**Rationale**:
- **Consistency**: Same environment across dev/staging/production
- **Isolation**: Process and dependency isolation
- **Scalability**: Kubernetes-native deployment
- **Portability**: Cloud-agnostic deployment

**Container Optimization**:
```dockerfile
# Multi-stage build for smaller images
FROM python:3.12-slim as builder
# Build dependencies...

FROM python:3.12-slim as runtime
# Runtime setup...
COPY --from=builder /app /app
USER 1000  # Non-root user
```

## Future Architecture Evolution

### 1. Event-Driven Architecture Migration

**Current State**: Synchronous request/response
**Target State**: Event-driven microservices

```python
# Future event-driven architecture
class ViralScrapingWorkflow:
    """Event-driven workflow orchestration"""
    
    async def handle_scraping_request(self, event: ScrapingRequestEvent):
        # Validate rate limits
        # Queue scraping task
        # Publish scraping_started event
        pass
    
    async def handle_content_discovered(self, event: ContentDiscoveredEvent):
        # Process discovered content
        # Extract patterns
        # Publish pattern_identified event
        pass
```

### 2. ML Integration Architecture

**Planned Enhancement**: Machine learning for intelligent scraping

```python
# Future ML integration
class IntelligentScraper:
    """ML-enhanced content discovery"""
    
    def __init__(self, ml_model: ViralPredictionModel):
        self.model = ml_model
    
    async def predict_viral_potential(self, content: str) -> float:
        """Predict viral potential using ML model"""
        features = self.extract_features(content)
        return await self.model.predict(features)
    
    async def optimize_scraping_schedule(self, account_id: str) -> datetime:
        """ML-optimized scraping schedule"""
        historical_data = await self.get_account_history(account_id)
        return self.model.predict_optimal_time(historical_data)
```

### 3. Multi-Cloud Architecture

**Planned Enhancement**: Cloud-agnostic deployment

```yaml
# Future multi-cloud configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: viral-scraper-cloud-config
data:
  cloud_provider: "auto-detect"
  storage_backend: "cloud-native"
  rate_limit_store: "managed-redis"
  monitoring_backend: "cloud-native"
```

---

**Document Version**: v1.0.0
**Architecture Status**: Production-ready foundation
**Next Evolution**: Event-driven patterns and ML integration
**Scalability Target**: 1000+ requests/minute with <100ms latency