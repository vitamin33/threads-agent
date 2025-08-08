# 🏗️ Threads-Agent Technical Architecture Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Database Architecture](#database-architecture)
3. [Service Communication](#service-communication)
4. [Data Flow Patterns](#data-flow-patterns)
5. [Dashboard Implementation](#dashboard-implementation)
6. [Infrastructure Details](#infrastructure-details)
7. [Monitoring & Observability](#monitoring--observability)
8. [Security Architecture](#security-architecture)

## System Overview

The Threads-Agent is a sophisticated AI-powered content generation and achievement tracking platform built on microservices architecture, deployed on Kubernetes (k3d).

### Core Architecture Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Streamlit  │  │   Grafana   │  │  Prometheus │            │
│  │  Dashboard  │  │  Dashboard  │  │   Metrics   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                          API Gateway Layer                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Orchestrator Service (FastAPI)              │   │
│  │  - REST API endpoints                                    │   │
│  │  - Service coordination                                  │   │
│  │  - Request routing                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                       Business Logic Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ Achievement │  │   Persona   │  │   Prompt    │           │
│  │  Collector  │  │   Runtime   │  │ Engineering │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Celery    │  │    Viral    │  │    Tech     │           │
│  │   Worker    │  │   Engine    │  │     Doc     │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                         Data Storage Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ PostgreSQL  │  │   Qdrant    │  │    Redis    │           │
│  │  (Primary)  │  │  (Vectors)  │  │   (Cache)   │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  RabbitMQ   │  │    MinIO    │  │  InfluxDB   │           │
│  │  (Queues)   │  │  (Objects)  │  │  (Metrics)  │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

## Database Architecture

### PostgreSQL Structure

The system uses PostgreSQL as the primary relational database with multiple schemas:

#### 1. Orchestrator Schema (`public`)

```sql
-- Core content tracking
CREATE TABLE posts (
    id BIGSERIAL PRIMARY KEY,
    persona_id VARCHAR(50) NOT NULL,
    hook TEXT NOT NULL,
    body TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    engagement_rate FLOAT DEFAULT 0.0,
    original_input TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Indexes for performance
    INDEX idx_posts_persona (persona_id),
    INDEX idx_posts_ts (ts DESC),
    INDEX idx_posts_engagement (engagement_rate DESC)
);

-- Task queue management
CREATE TABLE tasks (
    id BIGSERIAL PRIMARY KEY,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Status transitions
    CONSTRAINT chk_status CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    INDEX idx_tasks_status (status, created_at)
);

-- A/B testing framework
CREATE TABLE variant_performance (
    id SERIAL PRIMARY KEY,
    variant_id VARCHAR(100) UNIQUE NOT NULL,
    dimensions JSONB NOT NULL,
    impressions INTEGER DEFAULT 0,
    successes INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_level FLOAT DEFAULT 0.0,
    
    -- Statistical tracking
    mean_performance FLOAT,
    variance FLOAT,
    
    INDEX idx_variant_performance (variant_id),
    INDEX idx_variant_last_used (last_used DESC)
);
```

#### 2. Achievement Collector Schema

```sql
-- Main achievement tracking
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category achievement_category NOT NULL,
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_hours FLOAT GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (completed_at - started_at)) / 3600
    ) STORED,
    
    -- Impact metrics
    impact_score FLOAT DEFAULT 0.0 CHECK (impact_score >= 0 AND impact_score <= 100),
    complexity_score FLOAT DEFAULT 0.0,
    business_value JSONB DEFAULT '{}',
    time_saved_hours FLOAT DEFAULT 0.0,
    performance_improvement_pct FLOAT DEFAULT 0.0,
    
    -- Source tracking
    source_type source_type_enum NOT NULL,
    source_id VARCHAR(255),
    source_url VARCHAR(500),
    
    -- Portfolio management
    portfolio_ready BOOLEAN DEFAULT FALSE,
    portfolio_section VARCHAR(100),
    display_priority INTEGER DEFAULT 50,
    
    -- Publishing
    linkedin_post_id VARCHAR(255),
    linkedin_published_at TIMESTAMP,
    
    -- Metadata
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_achievements_category (category),
    INDEX idx_achievements_impact (impact_score DESC),
    INDEX idx_achievements_portfolio (portfolio_ready, display_priority),
    INDEX idx_achievements_source (source_type, source_id)
);

-- Trigger for updated_at
CREATE TRIGGER update_achievements_updated_at
    BEFORE UPDATE ON achievements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 3. Emotion Analysis Schema

```sql
-- Emotion trajectory analysis
CREATE TABLE emotion_trajectories (
    id BIGSERIAL PRIMARY KEY,
    post_id VARCHAR(100) NOT NULL,
    persona_id VARCHAR(50) NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    
    -- Trajectory metadata
    segment_count INTEGER NOT NULL,
    trajectory_type VARCHAR(20) CHECK (trajectory_type IN ('rising', 'falling', 'stable', 'volatile')),
    
    -- Emotion scores (0-1 scale)
    joy_avg FLOAT DEFAULT 0.0,
    anger_avg FLOAT DEFAULT 0.0,
    fear_avg FLOAT DEFAULT 0.0,
    sadness_avg FLOAT DEFAULT 0.0,
    surprise_avg FLOAT DEFAULT 0.0,
    disgust_avg FLOAT DEFAULT 0.0,
    anticipation_avg FLOAT DEFAULT 0.0,
    trust_avg FLOAT DEFAULT 0.0,
    
    -- Sentiment analysis
    sentiment_positive FLOAT DEFAULT 0.0,
    sentiment_negative FLOAT DEFAULT 0.0,
    sentiment_neutral FLOAT DEFAULT 0.0,
    sentiment_compound FLOAT DEFAULT 0.0,
    
    -- Performance
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_emotion_post (post_id),
    INDEX idx_emotion_persona (persona_id),
    INDEX idx_emotion_created (created_at DESC)
);
```

### Qdrant Vector Database

Used for semantic similarity and deduplication:

```python
# Collection structure
collections = {
    "posts_{persona_id}": {
        "vectors": {
            "size": 1536,  # OpenAI embedding dimension
            "distance": "Cosine"
        },
        "payload_schema": {
            "hook": "text",
            "body": "text",
            "timestamp": "datetime",
            "engagement_rate": "float"
        }
    },
    "achievements": {
        "vectors": {
            "size": 1536,
            "distance": "Cosine"
        },
        "payload_schema": {
            "title": "text",
            "description": "text",
            "impact_score": "float",
            "category": "keyword"
        }
    }
}
```

### Redis Cache Structure

```python
# Cache key patterns
cache_keys = {
    # Session management
    "session:{session_id}": "user session data",
    
    # API response caching
    "api:achievements:{page}:{per_page}": "paginated achievements",
    "api:metrics:summary": "system metrics summary",
    
    # Task results
    "task:result:{task_id}": "background task result",
    
    # Rate limiting
    "ratelimit:{api_key}:{endpoint}": "rate limit counter",
    
    # Feature flags
    "feature:{feature_name}": "feature toggle state"
}
```

## Service Communication

### REST API Endpoints

#### Orchestrator Service (Port 8080)

```python
# Core endpoints
POST   /task                    # Queue new task
GET    /metrics                 # Prometheus metrics
GET    /metrics/summary         # Business metrics summary
POST   /content/generate        # Generate content
GET    /content/posts           # List posts
PUT    /content/posts/{id}      # Update post
POST   /search/trends           # Search trends
GET    /health                  # Health check
```

#### Achievement Collector (Port 8090)

```python
# Achievement management
GET    /achievements/           # List achievements (paginated)
POST   /achievements/           # Create achievement
GET    /achievements/{id}       # Get specific achievement
PUT    /achievements/{id}       # Update achievement
DELETE /achievements/{id}       # Delete achievement

# Portfolio management
GET    /portfolio/ready         # Get portfolio-ready items
POST   /portfolio/export        # Export portfolio
GET    /portfolio/stats         # Portfolio statistics

# Analytics
GET    /analytics/impact        # Impact analysis
GET    /analytics/timeline      # Achievement timeline
POST   /analytics/roi           # ROI calculation
```

#### Prompt Engineering (Port 8085)

```python
# Template management
GET    /api/v1/templates        # List templates
POST   /api/v1/templates        # Create template
GET    /api/v1/templates/{id}   # Get template
PUT    /api/v1/templates/{id}   # Update template

# A/B testing
GET    /api/v1/experiments      # List experiments
POST   /api/v1/experiments      # Create experiment
GET    /api/v1/experiments/{id} # Get experiment results

# Chain execution
POST   /api/v1/chains/execute   # Execute prompt chain
GET    /api/v1/chains/status    # Chain execution status
```

### Message Queue Patterns

#### RabbitMQ Exchanges and Queues

```python
# Exchange configuration
exchanges = {
    "tasks": {
        "type": "direct",
        "durable": True,
        "queues": {
            "content.generation": "content generation tasks",
            "achievement.analysis": "achievement processing",
            "emotion.analysis": "emotion trajectory analysis"
        }
    },
    "events": {
        "type": "fanout",
        "durable": True,
        "queues": {
            "notifications": "system notifications",
            "analytics": "analytics events",
            "monitoring": "monitoring events"
        }
    }
}

# Message format
message_format = {
    "id": "uuid",
    "type": "task_type",
    "payload": {},
    "metadata": {
        "created_at": "timestamp",
        "priority": "high|medium|low",
        "retry_count": 0
    }
}
```

### Service Discovery

Kubernetes internal DNS resolution:

```yaml
# Service naming pattern
{service-name}.{namespace}.svc.cluster.local

# Examples
orchestrator.default.svc.cluster.local:8080
postgres-0.default.svc.cluster.local:5432
redis.default.svc.cluster.local:6379
```

## Data Flow Patterns

### 1. Content Generation Flow

```
User Request → Dashboard → Orchestrator → Task Queue → Celery Worker
                                ↓
                         Persona Runtime → OpenAI API
                                ↓
                         Emotion Analysis → Database
                                ↓
                         Vector Storage → Qdrant
                                ↓
                         Response → Dashboard
```

### 2. Achievement Collection Flow

```
GitHub PR Merge → Webhook → Achievement Collector
                              ↓
                         Code Analysis
                              ↓
                         Impact Calculation
                              ↓
                         Database Storage
                              ↓
                    Portfolio Generation → Dashboard
```

### 3. A/B Testing Flow

```
Template Request → Prompt Engineering Service
                           ↓
                    Variant Selection
                           ↓
                    Execution & Tracking
                           ↓
                    Statistical Analysis
                           ↓
                    Performance Update → Database
```

## Dashboard Implementation

### Streamlit Architecture

```python
# Main application structure
dashboard/
├── app.py                    # Main entry point
├── pages/                    # Multi-page app
│   ├── 1_📊_Overview.py      # System overview
│   ├── 2_🏆_Achievements.py  # Achievement tracking
│   ├── 3_📝_Content_Pipeline.py
│   ├── 4_💼_LinkedIn_Analytics.py
│   ├── 5_📄_Content_Drafts.py
│   ├── 6_🧪_AB_Testing.py
│   └── 7_🧪_Prompt_Engineering.py
├── services/                 # Service integrations
│   ├── api_client.py        # Unified API client
│   ├── k8s_monitor.py       # Kubernetes monitoring
│   └── realtime_client.py   # WebSocket client
└── utils/                   # Utilities
    └── theme_config.py      # UI theming
```

### API Client Implementation

```python
class ThreadsAgentAPI:
    def __init__(self):
        # Service discovery
        self.orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8080")
        self.achievement_url = os.getenv("ACHIEVEMENT_API_URL", "http://localhost:8090")
        
        # Connection pooling
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self.limits = httpx.Limits(max_keepalive_connections=10)
    
    @st.cache_data(ttl=60)  # Streamlit caching
    def get_achievements(self, days=7):
        # Cached API call with retry logic
        pass
```

### Real-time Updates

```python
# SSE (Server-Sent Events) implementation
async def stream_updates():
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', f"{api_url}/events") as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    yield json.loads(line[6:])

# WebSocket alternative
async def websocket_updates():
    async with websockets.connect(f"ws://{api_url}/ws") as websocket:
        async for message in websocket:
            yield json.loads(message)
```

## Infrastructure Details

### Kubernetes Deployment

#### Resource Definitions

```yaml
# Deployment example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      containers:
      - name: orchestrator
        image: orchestrator:local
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: connection-string
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```

#### Service Mesh

```yaml
# Service definition
apiVersion: v1
kind: Service
metadata:
  name: orchestrator
spec:
  selector:
    app: orchestrator
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

### Helm Chart Structure

```
chart/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── templates/
│   ├── orchestrator-deployment.yaml
│   ├── orchestrator-service.yaml
│   ├── achievement-deployment.yaml
│   ├── postgres-statefulset.yaml
│   ├── redis-deployment.yaml
│   └── _helpers.tpl
```

## Monitoring & Observability

### Prometheus Metrics

```python
# Custom metrics
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_latency = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Business metrics
active_users = Gauge(
    'active_users_total',
    'Total active users'
)

content_generated = Counter(
    'content_generated_total',
    'Total content pieces generated',
    ['persona', 'type']
)

achievement_impact = Histogram(
    'achievement_impact_score',
    'Achievement impact score distribution',
    buckets=[0, 10, 25, 50, 75, 90, 100]
)
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "Threads Agent Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[5m])"
        }]
      },
      {
        "title": "Achievement Impact",
        "targets": [{
          "expr": "histogram_quantile(0.95, achievement_impact_score)"
        }]
      },
      {
        "title": "Content Generation Rate",
        "targets": [{
          "expr": "rate(content_generated_total[1h])"
        }]
      }
    ]
  }
}
```

### Distributed Tracing

```python
# Jaeger integration
from opentracing import tracer

def traced_endpoint():
    with tracer.start_span('process_request') as span:
        span.set_tag('endpoint', '/api/achievements')
        
        with tracer.start_span('database_query', child_of=span):
            # Database operation
            pass
        
        with tracer.start_span('cache_lookup', child_of=span):
            # Cache operation
            pass
```

## Security Architecture

### Authentication & Authorization

```python
# JWT token validation
from jose import jwt

def verify_token(token: str):
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    return payload

# API key management
def validate_api_key(api_key: str):
    # Check against database
    # Implement rate limiting
    # Log access
    pass
```

### Network Security

```yaml
# Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: orchestrator-netpol
spec:
  podSelector:
    matchLabels:
      app: orchestrator
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: dashboard
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### Secret Management

```yaml
# Kubernetes Secrets
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  database-url: <base64-encoded>
  openai-api-key: <base64-encoded>
  jwt-secret: <base64-encoded>
```

## Performance Optimization

### Database Optimization

```sql
-- Query optimization examples
-- Efficient achievement retrieval
CREATE INDEX CONCURRENTLY idx_achievements_composite 
ON achievements(portfolio_ready, impact_score DESC, created_at DESC)
WHERE portfolio_ready = true;

-- Materialized view for dashboard
CREATE MATERIALIZED VIEW dashboard_metrics AS
SELECT 
    COUNT(*) as total_achievements,
    AVG(impact_score) as avg_impact,
    SUM(time_saved_hours) as total_time_saved,
    COUNT(DISTINCT category) as categories_covered
FROM achievements
WHERE created_at > NOW() - INTERVAL '30 days';

-- Refresh strategy
CREATE OR REPLACE FUNCTION refresh_dashboard_metrics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_metrics;
END;
$$ LANGUAGE plpgsql;
```

### Caching Strategy

```python
# Multi-level caching
class CacheManager:
    def __init__(self):
        self.local_cache = {}  # In-memory
        self.redis_client = redis.Redis()
    
    async def get(self, key: str):
        # L1: Local cache
        if key in self.local_cache:
            return self.local_cache[key]
        
        # L2: Redis cache
        value = await self.redis_client.get(key)
        if value:
            self.local_cache[key] = value
            return value
        
        # L3: Database
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        # Update all cache levels
        self.local_cache[key] = value
        await self.redis_client.setex(key, ttl, value)
```

## Conclusion

The Threads-Agent architecture represents a sophisticated, production-ready system combining:

1. **Microservices**: Clean separation of concerns
2. **Event-driven**: Asynchronous processing with queues
3. **Observability**: Comprehensive monitoring and tracing
4. **Scalability**: Kubernetes-native with horizontal scaling
5. **Security**: Defense-in-depth approach
6. **Performance**: Multi-level caching and optimization

This architecture supports high-performance content generation, comprehensive achievement tracking, and real-time analytics while maintaining reliability and scalability.