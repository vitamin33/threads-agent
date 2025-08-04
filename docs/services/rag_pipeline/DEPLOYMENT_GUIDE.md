# RAG Pipeline Deployment Guide

## Overview

Comprehensive deployment guide for the production-grade RAG Pipeline service. This guide covers Kubernetes deployment, performance optimization, monitoring setup, and operational best practices for MLOps environments.

## Prerequisites

### System Requirements

**Kubernetes Cluster**:
- Kubernetes 1.24+
- Minimum 3 nodes (for high availability)
- Node specifications:
  - CPU: 4+ cores per node
  - Memory: 16GB+ per node
  - Storage: SSD recommended for vector operations

**Dependencies**:
- Qdrant vector database cluster
- Redis cluster for caching
- Prometheus for metrics
- Grafana for dashboards
- Optional: Jaeger for distributed tracing

**External Services**:
- OpenAI API access (or compatible embedding service)
- Container registry access
- DNS resolution for service discovery

### Pre-deployment Checklist

```bash
# Verify cluster access
kubectl cluster-info

# Check available resources
kubectl top nodes

# Verify required namespaces
kubectl get namespaces | grep -E "(threads-agent|monitoring|qdrant|redis)"

# Check storage classes
kubectl get storageclass
```

## Container Image Preparation

### Building the Image

```bash
# Navigate to RAG pipeline directory
cd services/rag_pipeline

# Build optimized production image
docker build -f services/rag_pipeline/Dockerfile -t rag-pipeline:optimized .

# Tag for registry (replace with your registry)
docker tag rag-pipeline:optimized your-registry.com/rag-pipeline:v1.0.0

# Push to registry
docker push your-registry.com/rag-pipeline:v1.0.0
```

### Dockerfile Optimization

```dockerfile
FROM python:3.12-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set ownership and switch to non-root user
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "services.rag_pipeline.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Kubernetes Deployment

### 1. Namespace Setup

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: threads-agent
  labels:
    name: threads-agent
    monitoring: enabled
---
# Priority class for AI workloads
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
description: "High priority for AI/ML workloads"
```

```bash
kubectl apply -f namespace.yaml
```

### 2. Configuration and Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: rag-secrets
  namespace: threads-agent
type: Opaque
data:
  openai-api-key: <base64-encoded-api-key>
  database-url: <base64-encoded-db-url>
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-config
  namespace: threads-agent
data:
  # Performance settings
  RAG_BATCH_SIZE: "100"
  RAG_CACHE_TTL_SECONDS: "1800"
  RAG_TOP_K: "20"
  RAG_RERANK_TOP_K: "10"
  RAG_MIN_SCORE: "0.7"
  
  # Connection pools
  QDRANT_POOL_SIZE: "20"
  REDIS_POOL_SIZE: "15"
  MAX_CONCURRENT_BATCHES: "3"
  
  # Memory management
  RAG_MAX_MEMORY_MB: "2048"
  MMR_MAX_CANDIDATES: "50"
  
  # Logging
  LOG_LEVEL: "INFO"
  PYTHONUNBUFFERED: "1"
```

```bash
# Create secrets (replace with actual values)
kubectl create secret generic rag-secrets \
  --from-literal=openai-api-key="your-openai-key" \
  --from-literal=database-url="postgresql://user:pass@db:5432/dbname" \
  -n threads-agent

kubectl apply -f configmap.yaml
```

### 3. Main Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-pipeline
  namespace: threads-agent
  labels:
    app: rag-pipeline
    component: ai-retrieval
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 2
  selector:
    matchLabels:
      app: rag-pipeline
  template:
    metadata:
      labels:
        app: rag-pipeline
        component: ai-retrieval
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      priorityClassName: high-priority
      
      # Anti-affinity for high availability
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: [rag-pipeline]
              topologyKey: kubernetes.io/hostname
      
      # Init containers for dependency checks
      initContainers:
      - name: wait-for-qdrant
        image: busybox:1.35
        command: ['sh', '-c']
        args:
        - |
          echo "Waiting for Qdrant..."
          until nc -z qdrant-cluster 6333; do
            echo "Qdrant not ready, waiting..."
            sleep 2
          done
          echo "Qdrant is ready!"
        resources:
          requests:
            cpu: 10m
            memory: 16Mi
          limits:
            cpu: 50m
            memory: 32Mi
      
      - name: wait-for-redis
        image: busybox:1.35
        command: ['sh', '-c']
        args:
        - |
          echo "Waiting for Redis..."
          until nc -z redis-cluster 6379; do
            echo "Redis not ready, waiting..."
            sleep 2
          done
          echo "Redis is ready!"
        resources:
          requests:
            cpu: 10m
            memory: 16Mi
          limits:
            cpu: 50m
            memory: 32Mi
      
      containers:
      - name: rag-pipeline
        image: your-registry.com/rag-pipeline:v1.0.0
        imagePullPolicy: IfNotPresent
        
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        
        # Resource allocation optimized for AI workloads
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
            ephemeral-storage: 200Mi
          limits:
            cpu: 2000m
            memory: 3Gi
            ephemeral-storage: 1Gi
        
        # Environment variables
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: openai-api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: database-url
        - name: QDRANT_URL
          value: "http://qdrant-cluster:6333"
        - name: REDIS_URL
          value: "redis://redis-cluster:6379/1"
        
        # Configuration from ConfigMap
        envFrom:
        - configMapRef:
            name: rag-config
        
        # Health checks optimized for AI workloads
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 12  # Allow 60s for initialization
        
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 2
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 45
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        
        # Volume mounts for caching
        volumeMounts:
        - name: embedding-cache
          mountPath: /app/cache/embeddings
        - name: model-cache
          mountPath: /app/cache/models
        - name: tmp-storage
          mountPath: /tmp
      
      # Volumes for performance optimization
      volumes:
      - name: embedding-cache
        emptyDir:
          sizeLimit: 500Mi
          medium: Memory  # In-memory cache
      - name: model-cache
        emptyDir:
          sizeLimit: 200Mi
      - name: tmp-storage
        emptyDir:
          sizeLimit: 300Mi
      
      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      
      # DNS optimization
      dnsPolicy: ClusterFirst
      dnsConfig:
        options:
        - name: ndots
          value: "2"
        - name: timeout
          value: "1"
        - name: attempts
          value: "2"
      
      # Graceful shutdown
      terminationGracePeriodSeconds: 45
```

### 4. Service and Networking

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: rag-pipeline
  namespace: threads-agent
  labels:
    app: rag-pipeline
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  sessionAffinity: None
  ports:
  - name: http
    port: 8000
    targetPort: 8000
    protocol: TCP
  selector:
    app: rag-pipeline
---
# Optional: Ingress for external access
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rag-pipeline-ingress
  namespace: threads-agent
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
spec:
  rules:
  - host: rag-pipeline.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: rag-pipeline
            port:
              number: 8000
```

### 5. Auto-scaling Configuration

```yaml
# hpa.yaml - Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rag-pipeline-hpa
  namespace: threads-agent
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rag-pipeline
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  # Custom metrics (requires custom metrics API)
  - type: Pods
    pods:
      metric:
        name: rag_requests_per_second
      target:
        type: AverageValue
        averageValue: "20"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 120
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 120
---
# pdb.yaml - Pod Disruption Budget
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: rag-pipeline-pdb
  namespace: threads-agent
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: rag-pipeline
```

### 6. Security Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: rag-pipeline-netpol
  namespace: threads-agent
spec:
  podSelector:
    matchLabels:
      app: rag-pipeline
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow internal service communication
  - from:
    - namespaceSelector:
        matchLabels:
          name: threads-agent
    ports:
    - protocol: TCP
      port: 8000
  # Allow monitoring
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8000
  egress:
  # Allow Qdrant
  - to:
    - podSelector:
        matchLabels:
          app: qdrant
    ports:
    - protocol: TCP
      port: 6333
  # Allow Redis
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  # Allow external API calls (OpenAI)
  - to: []
    ports:
    - protocol: TCP
      port: 443
  # Allow DNS
  - to: []
    ports:
    - protocol: UDP
      port: 53
```

## Deployment Execution

### Step-by-Step Deployment

```bash
# 1. Create namespace and RBAC
kubectl apply -f namespace.yaml

# 2. Create secrets and config
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml

# 3. Deploy the application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# 4. Setup auto-scaling
kubectl apply -f hpa.yaml

# 5. Apply security policies
kubectl apply -f network-policy.yaml

# 6. Verify deployment
kubectl get pods -n threads-agent -l app=rag-pipeline
kubectl get svc -n threads-agent rag-pipeline
kubectl get hpa -n threads-agent rag-pipeline-hpa
```

### Verification Commands

```bash
# Check pod status
kubectl get pods -n threads-agent -l app=rag-pipeline -o wide

# Check resource usage
kubectl top pods -n threads-agent -l app=rag-pipeline

# Check logs
kubectl logs -n threads-agent -l app=rag-pipeline -f

# Test health endpoint
kubectl port-forward -n threads-agent svc/rag-pipeline 8000:8000
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics | grep rag_
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: rag-pipeline-metrics
  namespace: threads-agent
  labels:
    app: rag-pipeline
spec:
  selector:
    matchLabels:
      app: rag-pipeline
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
    honorLabels: true
    scrapeTimeout: 10s
  namespaceSelector:
    matchNames:
    - threads-agent
```

### Custom Alerts

```yaml
# prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: rag-pipeline-alerts
  namespace: threads-agent
spec:
  groups:
  - name: rag-pipeline.alerts
    rules:
    - alert: RAGHighLatency
      expr: histogram_quantile(0.95, sum(rate(rag_latency_seconds_bucket[5m])) by (le)) > 1.0
      for: 2m
      labels:
        severity: warning
        component: rag-pipeline
      annotations:
        summary: "RAG Pipeline high latency"
        description: "P95 latency is {{ $value }}s, exceeding 1s threshold"
    
    - alert: RAGHighErrorRate
      expr: sum(rate(rag_requests_total{status="error"}[5m])) / sum(rate(rag_requests_total[5m])) > 0.05
      for: 2m
      labels:
        severity: critical
        component: rag-pipeline
      annotations:
        summary: "RAG Pipeline high error rate"
        description: "Error rate is {{ $value | humanizePercentage }}"
    
    - alert: RAGPodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total{pod=~"rag-pipeline-.*"}[5m]) > 0
      for: 1m
      labels:
        severity: critical
        component: rag-pipeline
      annotations:
        summary: "RAG Pipeline pod restarting"
        description: "Pod {{ $labels.pod }} is crash looping"
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "RAG Pipeline Operations",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(rag_requests_total[5m])) by (operation)",
            "legendFormat": "{{ operation }}"
          }
        ]
      },
      {
        "title": "Latency Percentiles",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(rag_latency_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(rag_latency_seconds_bucket[5m])) by (le))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "Resource Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(container_cpu_usage_seconds_total{pod=~\"rag-pipeline-.*\"}[5m])) by (pod)",
            "legendFormat": "CPU - {{ pod }}"
          },
          {
            "expr": "sum(container_memory_working_set_bytes{pod=~\"rag-pipeline-.*\"}) by (pod) / 1024 / 1024 / 1024",
            "legendFormat": "Memory - {{ pod }}"
          }
        ]
      }
    ]
  }
}
```

## Performance Optimization

### Resource Tuning

```yaml
# Optimize based on workload patterns
resources:
  requests:
    # Start conservative for scheduling
    cpu: 500m
    memory: 1Gi
  limits:
    # Allow bursting for AI workloads
    cpu: 2000m      # Increase for CPU-intensive embedding operations
    memory: 3Gi     # Sufficient for large batch processing
```

### Environment Tuning

```yaml
env:
# Batch processing optimization
- name: RAG_BATCH_SIZE
  value: "100"        # Increase for higher throughput
- name: MAX_CONCURRENT_BATCHES
  value: "3"          # Limit concurrent API calls

# Memory management
- name: RAG_MAX_MEMORY_MB
  value: "2048"       # Leave headroom for system
- name: MMR_MAX_CANDIDATES
  value: "50"         # Prevent memory exhaustion

# Cache optimization
- name: RAG_CACHE_TTL_SECONDS
  value: "1800"       # 30 minutes default
- name: REDIS_POOL_SIZE
  value: "15"         # Increase for high concurrency

# Connection pools
- name: QDRANT_POOL_SIZE
  value: "20"         # Match expected concurrent requests
```

### JVM/Python Optimization

```yaml
env:
# Python optimization
- name: PYTHONUNBUFFERED
  value: "1"
- name: PYTHONHASHSEED
  value: "0"
- name: PYTHONASYNCIODEBUG
  value: "0"          # Disable in production

# Uvicorn optimization
- name: UVICORN_WORKERS
  value: "1"          # Single worker, async handles concurrency
- name: UVICORN_BACKLOG
  value: "2048"
```

## Scaling Strategies

### Horizontal Scaling

```yaml
# Production scaling configuration
spec:
  minReplicas: 3      # Minimum for high availability
  maxReplicas: 12     # Scale based on traffic patterns
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70    # Conservative for AI workloads
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75
  # Custom metrics based on queue depth
  - type: Pods
    pods:
      metric:
        name: rag_embedding_queue_size
      target:
        type: AverageValue
        averageValue: "30"
```

### Vertical Scaling (VPA)

```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: rag-pipeline-vpa
  namespace: threads-agent
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rag-pipeline
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: rag-pipeline
      minAllowed:
        cpu: 200m
        memory: 512Mi
      maxAllowed:
        cpu: 4000m
        memory: 6Gi
      controlledResources: ["cpu", "memory"]
```

## Troubleshooting

### Common Issues

#### 1. Pod Startup Issues

```bash
# Check pod events
kubectl describe pod -n threads-agent <pod-name>

# Check init container logs
kubectl logs -n threads-agent <pod-name> -c wait-for-qdrant
kubectl logs -n threads-agent <pod-name> -c wait-for-redis

# Check resource constraints
kubectl top pods -n threads-agent
kubectl describe nodes
```

#### 2. Performance Issues

```bash
# Check resource utilization
kubectl top pods -n threads-agent -l app=rag-pipeline

# Check HPA status
kubectl describe hpa -n threads-agent rag-pipeline-hpa

# Check application metrics
kubectl port-forward -n threads-agent svc/rag-pipeline 8000:8000
curl http://localhost:8000/metrics | grep -E "(rag_latency|rag_requests)"
```

#### 3. Connection Issues

```bash
# Test service connectivity
kubectl exec -it -n threads-agent deployment/rag-pipeline -- curl http://qdrant-cluster:6333/health
kubectl exec -it -n threads-agent deployment/rag-pipeline -- redis-cli -h redis-cluster ping

# Check network policies
kubectl describe networkpolicy -n threads-agent rag-pipeline-netpol
```

### Debug Commands

```bash
# Get detailed pod information
kubectl get pods -n threads-agent -l app=rag-pipeline -o yaml

# Check configuration
kubectl get cm -n threads-agent rag-config -o yaml
kubectl get secret -n threads-agent rag-secrets -o yaml

# Monitor real-time logs
kubectl logs -n threads-agent -l app=rag-pipeline -f --tail=100

# Execute debugging session
kubectl exec -it -n threads-agent deployment/rag-pipeline -- /bin/bash
```

## Maintenance and Updates

### Rolling Updates

```bash
# Update image
kubectl set image deployment/rag-pipeline \
  rag-pipeline=your-registry.com/rag-pipeline:v1.1.0 \
  -n threads-agent

# Monitor rollout
kubectl rollout status deployment/rag-pipeline -n threads-agent

# Rollback if needed
kubectl rollout undo deployment/rag-pipeline -n threads-agent
```

### Configuration Updates

```bash
# Update configuration
kubectl patch configmap rag-config -n threads-agent --patch='
data:
  RAG_BATCH_SIZE: "150"
  QDRANT_POOL_SIZE: "25"
'

# Restart deployment to pick up changes
kubectl rollout restart deployment/rag-pipeline -n threads-agent
```

### Backup and Recovery

```bash
# Backup configuration
kubectl get all,cm,secret -n threads-agent -o yaml > rag-pipeline-backup.yaml

# Restore from backup
kubectl apply -f rag-pipeline-backup.yaml
```

## Production Checklist

### Pre-deployment

- [ ] Container images built and pushed to registry
- [ ] Secrets created with proper values
- [ ] Dependencies (Qdrant, Redis) deployed and healthy
- [ ] Monitoring stack (Prometheus, Grafana) configured
- [ ] Network policies reviewed and applied
- [ ] Resource quotas configured
- [ ] Backup strategy in place

### Post-deployment

- [ ] All pods running and healthy
- [ ] Health checks passing
- [ ] Metrics being collected
- [ ] Alerts configured and tested
- [ ] Performance benchmarks met
- [ ] Security scans passed
- [ ] Documentation updated
- [ ] Team trained on operations

### Ongoing Operations

- [ ] Regular security updates
- [ ] Performance monitoring and optimization
- [ ] Capacity planning based on growth
- [ ] Disaster recovery testing
- [ ] Cost optimization reviews
- [ ] Configuration drift monitoring

---

## Summary

This deployment guide provides comprehensive instructions for deploying the RAG Pipeline service in production Kubernetes environments. The configuration emphasizes:

- **High Availability**: Multi-pod deployment with anti-affinity
- **Performance**: Optimized resource allocation and connection pooling
- **Scalability**: Auto-scaling based on CPU, memory, and custom metrics
- **Observability**: Comprehensive monitoring and alerting
- **Security**: Network policies and security contexts
- **Reliability**: Health checks, graceful shutdown, and circuit breakers

For additional support and advanced configurations, refer to the main technical documentation and API reference guides.