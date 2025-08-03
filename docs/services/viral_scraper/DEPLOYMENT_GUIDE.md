# Viral Scraper Deployment Guide

## Overview

This guide covers deployment strategies for the Viral Content Scraper Service in various environments, from local development to production Kubernetes clusters.

## Prerequisites

### System Requirements
- **Python**: 3.12+
- **Memory**: 128MB minimum, 512MB recommended
- **CPU**: 100m minimum, 500m recommended
- **Disk**: 100MB for service, additional for logs
- **Network**: HTTP/HTTPS outbound access for content scraping

### Dependencies
- **Container Runtime**: Docker or containerd
- **Orchestrator**: Kubernetes 1.20+ (for production)
- **Load Balancer**: Ingress controller or external LB
- **Monitoring**: Prometheus/Grafana (recommended)

## Local Development

### Direct Python Execution

```bash
# Clone repository
git clone https://github.com/threads-agent-stack/threads-agent.git
cd threads-agent/services/viral_scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Test health endpoint
curl http://localhost:8080/health
```

### Docker Development

```bash
# Build image
docker build -t viral-scraper:dev .

# Run container
docker run -d \
  --name viral-scraper-dev \
  -p 8080:8080 \
  -e RATE_LIMIT_REQUESTS_PER_WINDOW=1 \
  -e RATE_LIMIT_WINDOW_SECONDS=60 \
  viral-scraper:dev

# View logs
docker logs -f viral-scraper-dev

# Stop and remove
docker stop viral-scraper-dev
docker rm viral-scraper-dev
```

### Docker Compose Development

Create `docker-compose.dev.yml`:
```yaml
version: '3.8'

services:
  viral-scraper:
    build: .
    ports:
      - "8080:8080"
    environment:
      - RATE_LIMIT_REQUESTS_PER_WINDOW=2
      - RATE_LIMIT_WINDOW_SECONDS=30
      - LOG_LEVEL=DEBUG
    volumes:
      - ./:/app
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8080
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Redis for distributed rate limiting
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

```bash
# Start development stack
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f viral-scraper

# Stop stack
docker-compose -f docker-compose.dev.yml down
```

## Production Deployment

### Container Image Build

#### Multi-stage Dockerfile (Optimized)

```dockerfile
# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy source code
COPY --chown=appuser:appuser . .

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
```

#### Build and Push

```bash
# Build for multiple architectures
docker buildx create --use --name multiarch-builder
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-registry/viral-scraper:v1.0.0 \
  -t your-registry/viral-scraper:latest \
  --push .

# Or single architecture
docker build -t your-registry/viral-scraper:v1.0.0 .
docker push your-registry/viral-scraper:v1.0.0
```

### Kubernetes Deployment

#### Basic Deployment

```yaml
# viral-scraper-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: viral-scraper
  namespace: threads-agent
  labels:
    app: viral-scraper
    component: content-discovery
    part-of: viral-learning-flywheel
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: viral-scraper
  template:
    metadata:
      labels:
        app: viral-scraper
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: viral-scraper
        image: your-registry/viral-scraper:v1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        env:
        - name: RATE_LIMIT_REQUESTS_PER_WINDOW
          value: "1"
        - name: RATE_LIMIT_WINDOW_SECONDS
          value: "60"
        - name: LOG_LEVEL
          value: "INFO"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: viral-scraper-secrets
              key: redis-url
              optional: true
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 2
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

#### Service Definition

```yaml
# viral-scraper-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: viral-scraper
  namespace: threads-agent
  labels:
    app: viral-scraper
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8080
    targetPort: http
    protocol: TCP
  selector:
    app: viral-scraper
---
apiVersion: v1
kind: Service
metadata:
  name: viral-scraper-headless
  namespace: threads-agent
  labels:
    app: viral-scraper
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - name: http
    port: 8080
    targetPort: http
  selector:
    app: viral-scraper
```

#### Configuration Management

```yaml
# viral-scraper-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: viral-scraper-config
  namespace: threads-agent
data:
  rate-limit-requests: "1"
  rate-limit-window: "60"
  log-level: "INFO"
  max-posts-default: "50"
  days-back-default: "7"
  min-performance-percentile: "99.0"
---
apiVersion: v1
kind: Secret
metadata:
  name: viral-scraper-secrets
  namespace: threads-agent
type: Opaque
data:
  redis-url: cmVkaXM6Ly9yZWRpcy1jbHVzdGVyOjYzNzk=  # base64: redis://redis-cluster:6379
  threads-api-key: ""  # Add if needed
```

#### Horizontal Pod Autoscaler

```yaml
# viral-scraper-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: viral-scraper-hpa
  namespace: threads-agent
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
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

#### Network Policies

```yaml
# viral-scraper-network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: viral-scraper-network-policy
  namespace: threads-agent
spec:
  podSelector:
    matchLabels:
      app: viral-scraper
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: threads-agent
    - podSelector:
        matchLabels:
          app: orchestrator
    - podSelector:
        matchLabels:
          app: viral-engine
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to: []  # Allow all outbound (for content scraping)
    ports:
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
  - to:
    - podSelector:
        matchLabels:
          app: redis-cluster
    ports:
    - protocol: TCP
      port: 6379
```

#### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace threads-agent

# Apply configurations
kubectl apply -f viral-scraper-configmap.yaml
kubectl apply -f viral-scraper-deployment.yaml
kubectl apply -f viral-scraper-service.yaml
kubectl apply -f viral-scraper-hpa.yaml
kubectl apply -f viral-scraper-network-policy.yaml

# Verify deployment
kubectl get pods -n threads-agent -l app=viral-scraper
kubectl get svc -n threads-agent viral-scraper

# Check logs
kubectl logs -n threads-agent deployment/viral-scraper -f

# Test service
kubectl port-forward -n threads-agent svc/viral-scraper 8080:8080
curl http://localhost:8080/health
```

### Helm Chart Deployment

#### Chart Structure

```
viral-scraper-chart/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    ├── secret.yaml
    ├── hpa.yaml
    ├── pdb.yaml
    ├── networkpolicy.yaml
    └── tests/
        └── test-connection.yaml
```

#### Chart.yaml

```yaml
apiVersion: v2
name: viral-scraper
description: Viral Content Scraper Service for Threads Agent
type: application
version: 1.0.0
appVersion: "v1.0.0"
keywords:
  - viral-content
  - scraper
  - threads
  - ai
home: https://github.com/threads-agent-stack/threads-agent
sources:
  - https://github.com/threads-agent-stack/threads-agent
maintainers:
  - name: Threads Agent Team
    email: team@threads-agent.io
```

#### values.yaml

```yaml
# Default values for viral-scraper
image:
  repository: your-registry/viral-scraper
  tag: v1.0.0
  pullPolicy: IfNotPresent

nameOverride: ""
fullnameOverride: ""

replicaCount: 3

service:
  type: ClusterIP
  port: 8080
  targetPort: 8080
  annotations: {}

ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts:
    - host: viral-scraper.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "500m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

podDisruptionBudget:
  enabled: true
  minAvailable: 1

config:
  rateLimitRequests: 1
  rateLimitWindow: 60
  logLevel: INFO
  maxPostsDefault: 50
  daysBackDefault: 7
  minPerformancePercentile: 99.0

redis:
  enabled: false
  url: ""  # redis://redis-cluster:6379

monitoring:
  enabled: true
  prometheus:
    scrape: true
    port: 8080
    path: /metrics

networkPolicy:
  enabled: false

securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

podSecurityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL

nodeSelector: {}
tolerations: []
affinity: {}
```

#### Deploy with Helm

```bash
# Add repository (if using Helm repository)
helm repo add threads-agent https://charts.threads-agent.io
helm repo update

# Install from local chart
helm install viral-scraper ./viral-scraper-chart \
  --namespace threads-agent \
  --create-namespace \
  --values values-prod.yaml

# Or install from repository
helm install viral-scraper threads-agent/viral-scraper \
  --namespace threads-agent \
  --create-namespace \
  --values values-prod.yaml

# Upgrade deployment
helm upgrade viral-scraper threads-agent/viral-scraper \
  --namespace threads-agent \
  --values values-prod.yaml

# Check status
helm status viral-scraper -n threads-agent

# Uninstall
helm uninstall viral-scraper -n threads-agent
```

## Cloud Provider Specific Deployments

### AWS EKS

#### Prerequisites

```bash
# Install AWS CLI and eksctl
aws configure
eksctl create cluster --name threads-agent --region us-west-2

# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=threads-agent
```

#### EKS-specific Configuration

```yaml
# values-eks.yaml
ingress:
  enabled: true
  className: alb
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
  hosts:
    - host: viral-scraper.threads-agent.io
      paths:
        - path: /
          pathType: Prefix

resources:
  requests:
    memory: "128Mi"
    cpu: "200m"
  limits:
    memory: "256Mi"
    cpu: "1000m"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
```

### Google GKE

#### Prerequisites

```bash
# Install gcloud CLI
gcloud auth login
gcloud config set project your-project-id

# Create GKE cluster
gcloud container clusters create threads-agent \
  --zone=us-central1-a \
  --machine-type=e2-standard-2 \
  --num-nodes=3 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10
```

#### GKE-specific Configuration

```yaml
# values-gke.yaml
ingress:
  enabled: true
  className: gce
  annotations:
    kubernetes.io/ingress.global-static-ip-name: viral-scraper-ip
    networking.gke.io/managed-certificates: viral-scraper-cert
  hosts:
    - host: viral-scraper.threads-agent.io
      paths:
        - path: /*
          pathType: ImplementationSpecific

nodeSelector:
  cloud.google.com/gke-nodepool: default-pool
```

### Azure AKS

#### Prerequisites

```bash
# Install Azure CLI
az login
az group create --name threads-agent --location eastus

# Create AKS cluster
az aks create \
  --resource-group threads-agent \
  --name threads-agent-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

#### AKS-specific Configuration

```yaml
# values-aks.yaml
ingress:
  enabled: true
  className: azure/application-gateway
  annotations:
    appgw.ingress.kubernetes.io/backend-path-prefix: "/"
  hosts:
    - host: viral-scraper.threads-agent.io
      paths:
        - path: /
          pathType: Prefix
```

## Environment-Specific Configurations

### Development Environment

```yaml
# values-dev.yaml
replicaCount: 1

config:
  rateLimitRequests: 5  # More permissive for testing
  rateLimitWindow: 30
  logLevel: DEBUG

resources:
  requests:
    memory: "32Mi"
    cpu: "50m"
  limits:
    memory: "64Mi"
    cpu: "200m"

autoscaling:
  enabled: false

ingress:
  enabled: true
  hosts:
    - host: viral-scraper-dev.local
```

### Staging Environment

```yaml
# values-staging.yaml
replicaCount: 2

config:
  rateLimitRequests: 2
  rateLimitWindow: 45
  logLevel: INFO

resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "500m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5

redis:
  enabled: true
  url: redis://redis-staging:6379
```

### Production Environment

```yaml
# values-prod.yaml
replicaCount: 3

config:
  rateLimitRequests: 1
  rateLimitWindow: 60
  logLevel: INFO

resources:
  requests:
    memory: "128Mi"
    cpu: "200m"
  limits:
    memory: "256Mi"
    cpu: "1000m"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 15

redis:
  enabled: true
  url: redis://redis-cluster:6379

monitoring:
  enabled: true

networkPolicy:
  enabled: true

podDisruptionBudget:
  enabled: true
  minAvailable: 2
```

## Monitoring and Observability

### Prometheus Integration

```yaml
# prometheus-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: viral-scraper
  namespace: threads-agent
  labels:
    app: viral-scraper
spec:
  selector:
    matchLabels:
      app: viral-scraper
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Viral Scraper Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(viral_scraper_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Rate Limit Hits",
        "type": "graph", 
        "targets": [
          {
            "expr": "rate(viral_scraper_rate_limits_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "viral_scraper_response_seconds"
          }
        ]
      }
    ]
  }
}
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy-viral-scraper.yml
name: Deploy Viral Scraper

on:
  push:
    branches: [main]
    paths: ['services/viral_scraper/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      working-directory: services/viral_scraper
      run: |
        pip install -r requirements.txt
        pip install pytest
    - name: Run tests
      working-directory: services/viral_scraper
      run: pytest tests/ -v

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: services/viral_scraper
        push: true
        tags: ${{ secrets.REGISTRY }}/viral-scraper:${{ github.sha }}
    
    - name: Deploy to Kubernetes
      uses: azure/k8s-deploy@v1
      with:
        manifests: |
          k8s/viral-scraper-deployment.yaml
          k8s/viral-scraper-service.yaml
        images: |
          ${{ secrets.REGISTRY }}/viral-scraper:${{ github.sha }}
        kubectl-version: 'latest'
```

## Troubleshooting

### Common Deployment Issues

#### Pod CrashLoopBackOff

```bash
# Check pod status
kubectl get pods -n threads-agent -l app=viral-scraper

# Check pod logs
kubectl logs -n threads-agent deployment/viral-scraper --previous

# Check pod events
kubectl describe pods -n threads-agent -l app=viral-scraper
```

#### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n threads-agent viral-scraper

# Test service connectivity
kubectl run test-pod --image=curlimages/curl -i --tty --rm -- /bin/sh
curl http://viral-scraper.threads-agent.svc.cluster.local:8080/health
```

#### High Memory Usage

```bash
# Check resource usage
kubectl top pods -n threads-agent -l app=viral-scraper

# Increase memory limits
kubectl patch deployment viral-scraper -n threads-agent -p '{"spec":{"template":{"spec":{"containers":[{"name":"viral-scraper","resources":{"limits":{"memory":"256Mi"}}}]}}}}'
```

### Performance Tuning

#### Optimize for High Traffic

```yaml
# High-traffic configuration
spec:
  replicas: 10
  resources:
    requests:
      memory: "256Mi"
      cpu: "500m"
    limits:
      memory: "512Mi"
      cpu: "2000m"
  env:
  - name: UVICORN_WORKERS
    value: "4"
  - name: UVICORN_WORKER_CLASS
    value: "uvicorn.workers.UvicornWorker"
```

#### Database Connection Pooling

```python
# For Redis rate limiting
REDIS_CONNECTION_POOL_SIZE = 20
REDIS_CONNECTION_POOL_TIMEOUT = 30
```

---

**Last Updated**: 2025-08-03
**Service**: Viral Content Scraper (CRA-280)
**Deployment Version**: v1.0.0