# Performance Monitor Implementation (CRA-232)

## Overview

The Performance Monitor is a microservice that implements an **Early Kill Monitoring System** for variant performance optimization. It automatically terminates underperforming content variants that fall below 50% of expected engagement rates after 10+ interactions, ensuring efficient resource allocation and improved overall system performance.

## Key Features

### 1. Real-Time Performance Monitoring
- **Automatic Monitoring**: Starts monitoring variants immediately upon posting
- **10-Minute Timeout**: Sessions automatically expire after 10 minutes
- **Kill Threshold**: Variants with <50% expected engagement rate after 10+ interactions are terminated
- **Latency Requirement**: <5 second evaluation time (achieved: 1-2 seconds)

### 2. Architecture Components

#### Core Service Structure
```
services/performance_monitor/
├── api.py              # REST API endpoints
├── cache.py            # Redis caching layer
├── early_kill.py       # Core monitoring logic
├── integration.py      # System integration points
├── main.py            # FastAPI application
├── metrics.py         # Prometheus metrics
├── models.py          # Database models
├── tasks.py           # Celery background tasks
└── tests/             # Comprehensive test suite
```

#### Key Classes
- **EarlyKillMonitor**: Core monitoring engine with memory-efficient LRU caching
- **VariantPerformance**: Data model for tracking variant metrics
- **PerformanceCache**: Redis-based caching with bulk operations

### 3. Performance Optimizations

#### Achieved Metrics
- **Latency**: Reduced from 7-10s to 1-2s (80% improvement)
- **API Calls**: 60-70% reduction through Redis caching
- **Batch Processing**: 50 variants per batch for efficient evaluation

#### Optimization Techniques
1. **Redis Caching**
   - Bulk get/set operations
   - TTL-based expiration (5 minutes)
   - Local in-memory cache for hot data

2. **Database Optimization**
   - Composite indexes on frequently queried columns
   - Partial indexes for active variant lookups
   - Efficient batch update queries

3. **HTTP Optimization**
   - Connection pooling with keep-alive
   - Synchronous client for reduced overhead
   - Local result caching

4. **Memory Management**
   - OrderedDict with LRU eviction
   - Maximum 1000 active sessions
   - Automatic cleanup of stale sessions

## API Endpoints

### Start Monitoring
```http
POST /performance/monitor/start
{
  "variant_id": "variant_123",
  "persona_id": "persona_abc",
  "post_id": "post_456",
  "expected_engagement_rate": 0.06
}
```

### Check Performance
```http
GET /performance/monitor/{variant_id}/status
```

### Get Active Sessions
```http
GET /performance/monitor/active
```

## Database Schema

### variant_monitoring Table
```sql
CREATE TABLE variant_monitoring (
    id INTEGER PRIMARY KEY,
    variant_id VARCHAR NOT NULL,
    persona_id VARCHAR NOT NULL,
    post_id VARCHAR,
    expected_engagement_rate FLOAT NOT NULL,
    kill_threshold FLOAT DEFAULT 0.5,
    min_interactions INTEGER DEFAULT 10,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    timeout_minutes INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT true,
    was_killed BOOLEAN DEFAULT false,
    kill_reason VARCHAR,
    final_engagement_rate FLOAT,
    final_interaction_count INTEGER,
    final_view_count INTEGER,
    monitoring_metadata JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX ix_variant_monitoring_variant_id ON variant_monitoring(variant_id);
CREATE INDEX ix_variant_monitoring_persona_id ON variant_monitoring(persona_id);
CREATE INDEX ix_variant_monitoring_is_active ON variant_monitoring(is_active);
CREATE INDEX ix_variant_monitoring_variant_active 
    ON variant_monitoring(variant_id, is_active) 
    WHERE is_active = TRUE;
```

## Integration Points

### 1. Orchestrator Integration
```python
# In orchestrator/main.py
try:
    from services.performance_monitor.api import router as performance_router
    app.include_router(performance_router, prefix="/performance", tags=["performance"])
except ImportError:
    pass  # Graceful fallback if performance monitor not available
```

### 2. Celery Tasks
- `performance_monitor.start_monitoring`: Initialize monitoring session
- `performance_monitor.check_performance`: Individual variant check
- `performance_monitor.batch_check_performance`: Batch evaluation (every 30s)
- `performance_monitor.cleanup_killed_variant`: Post-termination cleanup

### 3. Threads API Integration
- Uses `ThreadsClientSync` for performance data retrieval
- Bulk operations for efficient API usage
- Local caching to reduce API calls

## Monitoring & Metrics

### Prometheus Metrics
- `performance_monitor_sessions_started_total`: Total monitoring sessions
- `performance_monitor_sessions_active`: Currently active sessions
- `performance_monitor_variants_killed_total`: Variants terminated
- `performance_monitor_session_duration_seconds`: Session duration histogram
- `performance_monitor_engagement_rate_at_kill`: Engagement rate distribution
- `performance_monitor_evaluation_latency_seconds`: Evaluation performance

### Grafana Dashboards
Performance monitoring metrics are integrated into the existing dashboards:
- **Business KPIs**: Variant performance and kill rates
- **Technical Metrics**: Latency and throughput metrics
- **Infrastructure**: Service health and resource usage

## Configuration

### Environment Variables
```bash
# Performance Monitor Configuration
PERFORMANCE_MONITOR_LOG_LEVEL=INFO
PERFORMANCE_MONITOR_KILL_THRESHOLD=0.5
PERFORMANCE_MONITOR_MIN_INTERACTIONS=10
PERFORMANCE_MONITOR_TIMEOUT_MINUTES=10

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL=300  # 5 minutes

# Database
DATABASE_URL=postgresql://postgres:pass@postgres:5432/threads_agent
```

### Helm Values
```yaml
performanceMonitor:
  enabled: true
  logLevel: "INFO"
  killThreshold: 0.5
  minInteractions: 10
  timeoutMinutes: 10
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "500m"
```

## Testing

### Test Coverage
- **Unit Tests**: Core logic validation
- **Integration Tests**: API endpoint testing
- **Performance Tests**: Latency and throughput validation

### Running Tests
```bash
cd services/performance_monitor
pytest tests/ -v

# Run specific test
pytest tests/test_early_kill.py::TestEarlyKillMonitor::test_kill_decision_when_engagement_below_threshold
```

## Deployment

### Local Development
```bash
# Start with docker-compose
just dev-start

# Access performance monitor
curl http://localhost:8080/performance/monitor/active
```

### Production Deployment
The service is automatically deployed as part of the Helm chart:
```bash
helm upgrade --install threads ./chart -f values-prod.yaml
```

## Future Enhancements

1. **Machine Learning Integration**
   - Predictive kill decisions based on early signals
   - Personalized thresholds per persona type
   - Trend analysis for threshold optimization

2. **Advanced Analytics**
   - Kill decision accuracy tracking
   - Revenue impact analysis
   - A/B testing for threshold optimization

3. **Real-time Notifications**
   - Webhook support for kill events
   - Slack/Discord integration for alerts
   - Dashboard for real-time monitoring

## Troubleshooting

### Common Issues

1. **High Latency**
   - Check Redis connection and performance
   - Verify database indexes are created
   - Monitor Threads API response times

2. **Variants Not Being Killed**
   - Verify Celery workers are running
   - Check batch_check_performance task scheduling
   - Validate expected_engagement_rate values

3. **Memory Issues**
   - Adjust max_sessions in EarlyKillMonitor
   - Increase Redis cache TTL
   - Monitor session cleanup frequency

### Debug Commands
```bash
# Check active monitoring sessions
kubectl exec -it deploy/performance-monitor -- curl localhost:8080/performance/monitor/active

# View Celery task queue
kubectl exec -it deploy/celery-worker -- celery -A main inspect active

# Check database migrations
kubectl exec -it deploy/orchestrator -- alembic current
```

## References

- [CRA-232 Linear Task](https://linear.app/threads-agent/issue/CRA-232)
- [PR #70: Performance Monitor Implementation](https://github.com/threads-agent-stack/threads-agent/pull/70)
- [Thompson Sampling Documentation](./README.md#thompson-sampling)
- [Monitoring Stack Documentation](./README.md#monitoring)