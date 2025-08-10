# Comment Monitoring Pipeline Deployment Guide (CRA-235)

## Overview

This guide covers the comprehensive Kubernetes deployment configurations for the Comment Monitoring Pipeline, implementing high-performance comment processing with optimized resource utilization, monitoring, and scaling capabilities.

## Architecture Components

### Core Components
- **Orchestrator Service**: Enhanced with comment monitoring capabilities
- **Database Migration Job**: Automated table creation and schema updates
- **Prometheus Monitoring**: Comprehensive metrics collection and alerting
- **HorizontalPodAutoscaler**: Dynamic scaling based on workload
- **Redis Cache**: Comment deduplication and performance optimization

### Performance Optimizations
- **Batch Processing**: Comments processed in configurable batches (5-25 comments/batch)
- **Deduplication**: N+1 query elimination with bulk database operations
- **Connection Pooling**: Optimized database and cache connections
- **Rate Limiting**: Configurable request rate limiting (50-200 req/min)
- **Exponential Backoff**: Resilient retry mechanisms

## Deployment Configurations

### 1. Orchestrator Service Updates

#### Enhanced Resource Configuration
```yaml
orchestrator:
  resources:
    requests:
      memory: "512Mi"    # Base: sufficient for comment processing
      cpu: "200m"
    limits:
      memory: "1Gi"      # Dev: allows burst processing
      cpu: "1000m"
  
  # Production settings
  resources:
    requests:
      memory: "768Mi"    # Production: increased for high volume
      cpu: "300m"
    limits:
      memory: "2Gi"      # Production: handles large comment batches
      cpu: "1500m"
```

#### Environment Variables
- `COMMENT_MONITORING_ENABLED`: Enable/disable comment monitoring
- `COMMENT_BATCH_SIZE`: Comments per processing batch (5-25)
- `COMMENT_DEDUP_CACHE_TTL`: Cache TTL for deduplication (1800-7200s)
- `COMMENT_PROCESSING_TIMEOUT`: Processing timeout (15-45s)
- `REDIS_URL`: Redis connection for caching

#### Health Checks
- **Readiness Probe**: HTTP GET `/health` every 5s
- **Liveness Probe**: HTTP GET `/health` every 30s with 5s timeout

### 2. Database Migration Job

The existing migration job automatically handles comment monitoring tables:

```yaml
# Runs migration 008_add_comment_monitoring_tables.py
apiVersion: batch/v1
kind: Job
metadata:
  name: migrations
  annotations:
    "helm.sh/hook": post-install,post-upgrade
```

#### Database Schema
- **comments table**: Stores raw comment data with optimized indexes
- **Indexes**: Optimized for post_id queries, author analysis, and time-range queries
- **Partial Index**: Hot data optimization for recent comments (7 days)

### 3. Monitoring and Observability

#### Prometheus Metrics
- `comment_processing_duration_seconds`: Processing latency histogram
- `comment_processing_queue_length`: Current queue backlog
- `comment_processing_errors_total`: Error rate tracking
- `comment_duplicates_detected_total`: Deduplication effectiveness
- `comment_db_query_duration_seconds`: Database performance

#### ServiceMonitor Configuration
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: orchestrator
spec:
  endpoints:
  - port: metrics
    interval: 30s
    scrapeTimeout: 10s
```

#### Alert Rules
- **CommentProcessingHighLatency**: 95th percentile > 10s
- **CommentProcessingErrors**: Error rate > 0.1/sec
- **CommentQueueBacklog**: Queue length > threshold (100-1000)
- **CommentDatabaseSlowQueries**: 95th percentile DB queries > 2s
- **Resource Utilization**: Memory/CPU approaching limits

### 4. Horizontal Pod Autoscaler

#### Standard Resource-Based Scaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 1-2     # Dev: 1, Prod: 2
  maxReplicas: 5-10    # Dev: 5, Prod: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70-75
  - type: Resource
    resource:
      name: memory
      target:
        averageUtilization: 80
```

#### Custom Metrics Scaling (Production)
```yaml
# Scale based on comment processing queue length
- type: Pods
  pods:
    metric:
      name: comment_processing_queue_length
    target:
      type: AverageValue
      averageValue: "50-75"
```

#### Scaling Behavior
- **Scale Up**: Fast response to comment bursts (15-60s stabilization)
- **Scale Down**: Conservative approach for stability (300-600s stabilization)

### 5. Security and Network Policies

#### RBAC Configuration
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: comment-monitoring-sa

apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: comment-monitoring-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
```

#### Network Policy
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  podSelector:
    matchLabels:
      app: orchestrator
  policyTypes:
  - Ingress
  - Egress
  # Allows communication with postgres, redis, rabbitmq, and DNS
```

## Environment-Specific Configurations

### Development Environment (`values-dev.yaml`)
```yaml
orchestrator:
  commentMonitoring:
    enabled: true
    batchSize: 5                    # Smaller batches for development
    dedupCacheTTL: 1800            # Shorter TTL for testing
    processingTimeout: 15           # Faster timeout for dev
    rateLimitPerMinute: 50         # Lower rate limit
    alerts:
      queueBacklogThreshold: 100   # Lower threshold for dev testing
  autoscaling:
    enabled: false                 # Manual scaling in dev
```

### Production Environment (`values-prod.yaml`)
```yaml
orchestrator:
  commentMonitoring:
    enabled: true
    batchSize: 25                  # Larger batches for efficiency
    dedupCacheTTL: 7200           # Longer TTL for production
    processingTimeout: 45          # More time for complex processing
    rateLimitPerMinute: 200       # Higher rate limit
    alerts:
      queueBacklogThreshold: 1000 # Higher threshold for production
    networkPolicy:
      enabled: true               # Enable security
    rbac:
      enabled: true              # Enable RBAC
  autoscaling:
    enabled: true
    minReplicas: 2               # HA configuration
    maxReplicas: 10              # Scale for high load
    customMetrics:
      enabled: true              # Queue-based scaling
```

## Deployment Steps

### 1. Prerequisites
```bash
# Ensure cluster connectivity
kubectl cluster-info

# Verify Helm chart
helm template threads-agent ./chart --values ./chart/values-dev.yaml --dry-run
```

### 2. Development Deployment
```bash
# Deploy with comment monitoring enabled
helm upgrade --install threads-agent ./chart \
  --values ./chart/values-dev.yaml \
  --set orchestrator.commentMonitoring.enabled=true \
  --set monitoring.prometheus.enabled=true \
  --set postgres.enabled=true \
  --set redis.enabled=true \
  --wait
```

### 3. Production Deployment
```bash
# Deploy production configuration
helm upgrade --install threads-agent ./chart \
  --values ./chart/values-prod.yaml \
  --timeout 10m \
  --wait
```

### 4. Validation
```bash
# Run comprehensive validation
./scripts/validate-comment-monitoring-deployment.sh
```

## Monitoring and Dashboards

### Grafana Dashboard
The comment monitoring Grafana dashboard provides:
- **Processing Overview**: Rate, errors, queue length, duplicates
- **Latency Metrics**: 50th, 95th, 99th percentile processing times
- **Throughput Analysis**: Attempts, successes, errors per second
- **Database Performance**: Query times, operations, errors
- **Resource Utilization**: CPU, memory usage
- **Celery Queue Metrics**: Task queue lengths and processing rates
- **Cache Performance**: Hit rates, miss rates
- **Error Breakdown**: Categorized error analysis

### Key Metrics to Monitor
1. **comment_processing_duration_seconds**: Keep 95th percentile < 10s
2. **comment_processing_queue_length**: Alert when > threshold
3. **comment_processing_errors_total**: Target < 1% error rate
4. **comment_duplicates_detected_total**: Monitor deduplication effectiveness
5. **comment_db_query_duration_seconds**: Keep DB queries < 2s

## Performance Tuning

### Batch Size Optimization
- **Small Batches (5-10)**: Lower latency, higher overhead
- **Large Batches (20-25)**: Higher throughput, potential latency spikes
- **Recommendation**: Start with 10, tune based on load patterns

### Cache Configuration
- **Development**: 1800s TTL (30 minutes)
- **Production**: 7200s TTL (2 hours)
- **Memory Impact**: Higher TTL = more memory usage

### Rate Limiting
- **Development**: 50 requests/minute
- **Production**: 200 requests/minute
- **Burst Handling**: Configure with processing capacity

### Resource Allocation
- **Memory**: Base 512Mi, production 768Mi-2Gi
- **CPU**: Base 200m, production 300m-1500m
- **Scaling**: Min 1-2 replicas, max 5-10 replicas

## Troubleshooting

### Common Issues

#### High Processing Latency
```bash
# Check queue backlog
kubectl exec -it deployment/orchestrator -- curl localhost:9090/metrics | grep comment_processing_queue_length

# Scale up manually if needed
kubectl scale deployment orchestrator --replicas=3
```

#### Database Connection Issues
```bash
# Check database connectivity
kubectl exec -it deployment/orchestrator -- python -c "
import os, psycopg2
conn = psycopg2.connect(os.environ['POSTGRES_DSN'])
print('DB connection successful')
"
```

#### Memory Issues
```bash
# Check memory usage
kubectl top pods -l app=orchestrator

# Check for memory leaks
kubectl exec -it deployment/orchestrator -- curl localhost:9090/metrics | grep container_memory
```

### Performance Debugging
```bash
# Enable debug logging
kubectl set env deployment/orchestrator LOG_LEVEL=DEBUG

# Check processing metrics
kubectl port-forward svc/orchestrator 9090:9090
curl http://localhost:9090/metrics | grep comment_processing
```

## Security Considerations

### Network Security
- Enable NetworkPolicy in production
- Restrict ingress to necessary services only
- Allow egress to database, cache, and message queue

### RBAC
- Dedicated ServiceAccount for comment monitoring
- Minimal required permissions
- Regular audit of permissions

### Data Privacy
- Comment data encryption at rest
- Secure database connections (TLS)
- PII scrubbing in logs

## Maintenance

### Regular Tasks
1. **Monitor Metrics**: Daily review of processing rates and errors
2. **Database Maintenance**: Weekly cleanup of old comments
3. **Performance Review**: Monthly analysis of resource usage
4. **Security Audit**: Quarterly review of permissions and policies

### Backup Strategy
- Database backups include comment monitoring tables
- Configuration backups via Git repository
- Metrics data retention per Prometheus configuration

## Integration Testing

### Test Scenarios
1. **Batch Processing**: Verify comment batching works correctly
2. **Deduplication**: Ensure duplicate comments are handled
3. **Error Handling**: Test retry mechanisms and error recovery
4. **Scaling**: Verify HPA triggers under load
5. **Database Integration**: Test transaction handling and rollback
6. **Cache Integration**: Verify Redis connectivity and performance

### Load Testing
```bash
# Example load test
for i in {1..100}; do
  curl -X POST http://orchestrator:8080/comments/process \
    -H "Content-Type: application/json" \
    -d '{"post_id": "test_'$i'", "comments": [...]}' &
done
wait
```

## Conclusion

The Comment Monitoring Pipeline deployment provides:
- **High Performance**: Optimized batch processing and caching
- **Scalability**: Dynamic scaling based on workload
- **Reliability**: Comprehensive monitoring and alerting
- **Security**: Network policies and RBAC
- **Maintainability**: Environment-specific configurations and validation tools

This implementation supports the CRA-235 requirements for production-grade comment monitoring with comprehensive Kubernetes integration.