# 🚀 Achievement Collector Deployment Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring & Observability](#monitoring--observability)
- [Backup & Recovery](#backup--recovery)
- [Scaling Guidelines](#scaling-guidelines)
- [Security Checklist](#security-checklist)

## Prerequisites

### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB for application + database growth
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows (WSL2)

### Software Dependencies
```bash
# Required
python >= 3.8
postgresql >= 12 or sqlite3
redis >= 6.0 (for caching)
git
github-cli (gh)

# Optional but recommended
docker >= 20.10
kubernetes >= 1.21
helm >= 3.0
nginx (for reverse proxy)
```

## Local Development

### 1. Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/achievement-collector
cd services/achievement_collector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Configure environment
cp .env.example .env
# Edit .env with your values

# Initialize database
python -m alembic upgrade head

# Run development server
uvicorn main:app --reload --port 8000
```

### 2. Environment Configuration

Create `.env` file:
```bash
# Core Settings
APP_ENV=development
APP_NAME=achievement-collector
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/achievements
# Or for SQLite:
USE_SQLITE=true
SQLITE_PATH=./achievements.db

# APIs
OPENAI_API_KEY=sk-your-key-here
GITHUB_TOKEN=ghp_your-token-here

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
WEBHOOK_SECRET=your-webhook-secret

# Features
MOCK_MODE=false
AUTO_ANALYZE_PRS=true
STORY_GENERATION_ENABLED=true
```

### 3. Database Setup

#### PostgreSQL
```bash
# Create database
createdb achievements

# Run migrations
alembic upgrade head

# Create initial user (optional)
python scripts/create_admin.py
```

#### SQLite (for development)
```bash
# Migrations auto-create SQLite file
alembic upgrade head
```

## Docker Deployment

### 1. Single Container

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gh \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
# Build image
docker build -t achievement-collector:latest .

# Run container
docker run -d \
  --name achievement-collector \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/achievements \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -v $(pwd)/data:/app/data \
  achievement-collector:latest
```

### 2. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/achievements
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: achievements
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

Run stack:
```bash
docker-compose up -d
docker-compose logs -f app
```

## Kubernetes Deployment

### 1. Helm Chart

```yaml
# helm/values.yaml
replicaCount: 2

image:
  repository: your-registry/achievement-collector
  tag: latest
  pullPolicy: Always

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: achievements.your-domain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: achievements-tls
      hosts:
        - achievements.your-domain.com

resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

postgresql:
  enabled: true
  auth:
    postgresPassword: changeme
    database: achievements

redis:
  enabled: true
  auth:
    enabled: false

env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: achievement-secrets
        key: openai-api-key
  - name: GITHUB_TOKEN
    valueFrom:
      secretKeyRef:
        name: achievement-secrets
        key: github-token
```

Deploy:
```bash
# Create namespace
kubectl create namespace achievements

# Create secrets
kubectl create secret generic achievement-secrets \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=github-token=$GITHUB_TOKEN \
  -n achievements

# Install chart
helm install achievement-collector ./helm \
  -n achievements \
  -f helm/values.yaml

# Check status
kubectl get pods -n achievements
kubectl logs -f deployment/achievement-collector -n achievements
```

### 2. Raw Kubernetes Manifests

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: achievement-collector
  namespace: achievements
spec:
  replicas: 3
  selector:
    matchLabels:
      app: achievement-collector
  template:
    metadata:
      labels:
        app: achievement-collector
    spec:
      containers:
      - name: app
        image: your-registry/achievement-collector:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connection-string
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: achievement-collector
  namespace: achievements
spec:
  selector:
    app: achievement-collector
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

## Production Configuration

### 1. Environment Variables

```bash
# Production .env
APP_ENV=production
LOG_LEVEL=INFO
WORKERS=4  # Number of uvicorn workers

# Database (use connection pooling)
DATABASE_URL=postgresql://user:pass@db-cluster:5432/achievements?pool_size=20&max_overflow=40
DATABASE_POOL_RECYCLE=3600

# Redis Cluster
REDIS_URL=redis://redis-cluster:6379/0
REDIS_MAX_CONNECTIONS=50

# API Keys (from secret manager)
OPENAI_API_KEY=${OPENAI_API_KEY}
GITHUB_TOKEN=${GITHUB_TOKEN}

# Security
SECRET_KEY=${SECRET_KEY}  # From secret manager
ALLOWED_HOSTS=achievements.your-domain.com
CORS_ORIGINS=https://your-frontend.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Features
AUTO_ANALYZE_PRS=true
STORY_GENERATION_ENABLED=true
WEBHOOK_VALIDATION=true
```

### 2. Gunicorn Configuration

```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
timeout = 60
graceful_timeout = 30
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'achievement-collector'

# Server mechanics
daemon = False
pidfile = '/tmp/achievement-collector.pid'
user = 'appuser'
group = 'appuser'
tmp_upload_dir = None

# SSL (if not using reverse proxy)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'
```

Run with Gunicorn:
```bash
gunicorn main:app -c gunicorn.conf.py
```

### 3. Nginx Configuration

```nginx
# nginx.conf
upstream achievement_backend {
    least_conn;
    server app1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server app2:8000 weight=1 max_fails=3 fail_timeout=30s;
    server app3:8000 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name achievements.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name achievements.your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://achievement_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://achievement_backend/health;
    }

    # Static files (if any)
    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## Monitoring & Observability

### 1. Prometheus Metrics

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'achievement-collector'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
```

### 2. Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Achievement Collector",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Achievement Creation Rate",
        "targets": [
          {
            "expr": "rate(achievements_created_total[1h])"
          }
        ]
      },
      {
        "title": "API Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

### 3. Logging Configuration

```python
# logging_config.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if os.getenv("APP_ENV") == "production" else "default"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "root": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "handlers": ["console", "file"]
    }
}
```

### 4. Application Monitoring

```python
# monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_latency = Histogram('http_request_duration_seconds', 'HTTP request latency')
active_connections = Gauge('active_connections', 'Active connections')
achievements_created = Counter('achievements_created_total', 'Total achievements created', ['source'])

# Middleware
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    # Track active connections
    active_connections.inc()
    
    try:
        response = await call_next(request)
        
        # Record metrics
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        request_latency.observe(time.time() - start_time)
        
        return response
    finally:
        active_connections.dec()
```

## Backup & Recovery

### 1. Database Backup

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL backup
pg_dump $DATABASE_URL > $BACKUP_DIR/achievements_$DATE.sql

# Compress
gzip $BACKUP_DIR/achievements_$DATE.sql

# Upload to S3
aws s3 cp $BACKUP_DIR/achievements_$DATE.sql.gz s3://your-backup-bucket/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### 2. Automated Backup CronJob

```yaml
# backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: achievement-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:14
            command: ["/scripts/backup.sh"]
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: connection-string
            volumeMounts:
            - name: backup-script
              mountPath: /scripts
          volumes:
          - name: backup-script
            configMap:
              name: backup-script
              defaultMode: 0755
          restartPolicy: OnFailure
```

### 3. Recovery Procedure

```bash
# 1. Stop application
kubectl scale deployment achievement-collector --replicas=0

# 2. Restore database
gunzip < achievements_20250128_020000.sql.gz | psql $DATABASE_URL

# 3. Verify restoration
psql $DATABASE_URL -c "SELECT COUNT(*) FROM achievements;"

# 4. Restart application
kubectl scale deployment achievement-collector --replicas=3
```

## Scaling Guidelines

### Horizontal Scaling

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: achievement-collector-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: achievement-collector
  minReplicas: 2
  maxReplicas: 20
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
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

### Database Scaling

```yaml
# PostgreSQL with read replicas
production:
  postgresql:
    architecture: replication
    primary:
      resources:
        requests:
          memory: "2Gi"
          cpu: "1000m"
    readReplicas:
      replicaCount: 2
      resources:
        requests:
          memory: "1Gi"
          cpu: "500m"
```

### Caching Strategy

```python
# caching.py
from functools import lru_cache
import redis
import json

redis_client = redis.from_url(os.getenv("REDIS_URL"))

class CacheManager:
    @staticmethod
    def cache_achievement(achievement_id: int, data: dict, ttl: int = 3600):
        """Cache achievement data for 1 hour"""
        key = f"achievement:{achievement_id}"
        redis_client.setex(key, ttl, json.dumps(data))
    
    @staticmethod
    def get_cached_achievement(achievement_id: int):
        """Get cached achievement"""
        key = f"achievement:{achievement_id}"
        data = redis_client.get(key)
        return json.loads(data) if data else None
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def get_analysis_cache(pr_number: int):
        """In-memory cache for analysis results"""
        return f"analysis:{pr_number}"
```

## Security Checklist

### 1. API Security
- [ ] Enable HTTPS only
- [ ] Implement rate limiting
- [ ] Use API key authentication
- [ ] Validate webhook signatures
- [ ] Enable CORS properly
- [ ] SQL injection prevention
- [ ] XSS protection

### 2. Secret Management
```bash
# Use secret management service
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name achievement-collector/prod \
  --secret-string file://secrets.json

# Kubernetes Secrets
kubectl create secret generic api-keys \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=github-token=$GITHUB_TOKEN
```

### 3. Network Security
```yaml
# Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: achievement-collector-netpol
spec:
  podSelector:
    matchLabels:
      app: achievement-collector
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  # Allow external API calls
  - to: []
    ports:
    - protocol: TCP
      port: 443
```

### 4. Compliance
- [ ] GDPR compliance for user data
- [ ] SOC2 audit logging
- [ ] PCI DSS if handling payments
- [ ] Regular security scans
- [ ] Dependency vulnerability checks

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
```bash
# Check connectivity
pg_isready -h localhost -p 5432
# Check credentials
psql $DATABASE_URL -c "SELECT 1;"
```

2. **Memory Issues**
```bash
# Increase worker memory
WORKERS=2  # Reduce workers
# Or increase container limits
```

3. **Slow API Responses**
```bash
# Enable query logging
LOG_LEVEL=DEBUG
# Check slow queries
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

### Health Checks

```python
# health.py
@app.get("/health")
async def health_check():
    checks = {
        "status": "healthy",
        "database": check_database(),
        "redis": check_redis(),
        "github_api": check_github_api(),
        "timestamp": datetime.utcnow()
    }
    
    if not all([checks["database"], checks["redis"]]):
        raise HTTPException(status_code=503, detail=checks)
    
    return checks

@app.get("/ready")
async def readiness_check():
    # Check if app is ready to serve traffic
    return {"ready": True}
```

## Support & Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Review metrics and logs
2. **Monthly**: Update dependencies
3. **Quarterly**: Security audit
4. **Yearly**: Major version upgrades

### Support Channels
- GitHub Issues: [Link]
- Slack: #achievement-collector
- Email: support@example.com

---

*Last updated: January 2025*