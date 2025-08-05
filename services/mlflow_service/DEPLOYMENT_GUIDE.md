# MLflow Production Deployment Guide

## Overview

This guide covers the optimized MLflow deployment for the threads-agent project with enterprise-grade features including high availability, security, monitoring, and backup strategies.

## Key Improvements Implemented

### 1. **Security Enhancements**
- **RBAC**: ServiceAccount with minimal required permissions
- **NetworkPolicy**: Strict ingress/egress rules limiting traffic
- **SecurityContext**: Non-root user, read-only filesystem, dropped capabilities
- **Secret Management**: Auto-generated credentials stored in Kubernetes secrets

### 2. **High Availability**
- **Multi-replica deployment**: 2+ replicas with pod anti-affinity
- **HorizontalPodAutoscaler**: Auto-scales 2-10 replicas based on CPU/memory
- **PodDisruptionBudget**: Ensures minimum availability during updates
- **Rolling updates**: Zero-downtime deployments

### 3. **Resource Optimization**
- **Right-sized resources**: Reduced from 500m/1Gi to 250m/512Mi (requests)
- **Efficient limits**: Prevents resource hogging while allowing bursts
- **PostgreSQL indexes**: Optimized query performance
- **Startup probe**: Prevents premature readiness during initialization

### 4. **Monitoring & Observability**
- **Prometheus metrics**: ServiceMonitor for automatic scraping
- **Grafana dashboards**: Pre-configured MLflow dashboard
- **Alert rules**: Critical alerts for downtime, errors, performance
- **Jaeger tracing**: Distributed tracing with 10% sampling

### 5. **Backup & Recovery**
- **Automated backups**: Daily PostgreSQL backups with compression
- **S3 storage**: Backups stored in MinIO with encryption
- **Retention policy**: Keep last 7 backups
- **Restore procedures**: One-command restore with validation

## Deployment Instructions

### Prerequisites

1. k3d cluster running with monitoring stack
2. Helm 3.x installed
3. kubectl configured

### Step 1: Add Helm Dependencies

```bash
cd services/mlflow/helm
helm dependency update
```

### Step 2: Create Namespace

```bash
kubectl create namespace mlflow
```

### Step 3: Deploy MLflow

```bash
# Development deployment
helm install mlflow . -n mlflow \
  --set ingress.hosts[0].host=mlflow.local \
  --set postgresql.auth.password=secure-password \
  --set minio.auth.rootPassword=secure-minio-password

# Production deployment with all features
helm install mlflow . -n mlflow \
  --set ingress.hosts[0].host=mlflow.yourdomain.com \
  --set ingress.tls[0].secretName=mlflow-tls \
  --set ingress.tls[0].hosts={mlflow.yourdomain.com} \
  --set auth.enabled=true \
  --set networkPolicy.enabled=true \
  --set backup.enabled=true
```

### Step 4: Verify Deployment

```bash
# Check pods
kubectl get pods -n mlflow

# Check HPA
kubectl get hpa -n mlflow

# Check services
kubectl get svc -n mlflow

# Check ingress
kubectl get ingress -n mlflow
```

### Step 5: Access MLflow

```bash
# For local development
kubectl port-forward -n mlflow svc/mlflow 5000:5000

# Access at http://localhost:5000
```

## Configuration Examples

### Enable Authentication

```yaml
auth:
  enabled: true
  username: admin
  password: "secure-password"  # Or leave empty for auto-generation
```

### Configure External PostgreSQL

```yaml
postgresql:
  enabled: false

backendStore:
  uri: "postgresql://user:pass@external-postgres:5432/mlflow"
```

### Configure External S3

```yaml
minio:
  enabled: false

artifactStore:
  uri: "s3://your-bucket/mlflow"

env:
  - name: AWS_ACCESS_KEY_ID
    value: "your-key"
  - name: AWS_SECRET_ACCESS_KEY
    value: "your-secret"
```

### Adjust Resource Limits for Heavy Workloads

```yaml
resources:
  requests:
    cpu: 1000m
    memory: 2Gi
  limits:
    cpu: 4000m
    memory: 8Gi

autoscaling:
  targetCPUUtilizationPercentage: 50
  maxReplicas: 20
```

## Backup & Restore Operations

### Manual Backup

```bash
# Trigger immediate backup
kubectl create job --from=cronjob/mlflow-backup mlflow-manual-backup -n mlflow
```

### List Backups

```bash
# Check backup PVC
kubectl exec -n mlflow deployment/mlflow -c mlflow -- ls -la /backup/

# Check S3 backups
kubectl exec -n mlflow deployment/mlflow-minio -c minio -- mc ls minio/mlflow-backups/postgres-backups/
```

### Restore from Backup

```bash
# Enable restore in values
helm upgrade mlflow . -n mlflow \
  --set restore.enabled=true \
  --set restore.backupFile="mlflow_backup_20240125_020000.sql.gz" \
  --set restore.fromS3=true
```

## Monitoring

### Access Grafana Dashboard

1. Port-forward Grafana: `kubectl port-forward -n monitoring svc/grafana 3000:3000`
2. Login to Grafana
3. Navigate to Dashboards → MLflow Dashboard

### Key Metrics to Monitor

- **Request rate**: Track API usage patterns
- **P95 latency**: Ensure performance SLAs
- **Memory usage**: Prevent OOM kills
- **Token usage**: Monitor LLM costs
- **Error rate**: Catch issues early

### Alerts

Critical alerts configured:
- MLflow service down (5+ minutes)
- High error rate (>5%)
- High latency (P95 > 1s)
- Database connection failures
- Backup failures

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod -n mlflow mlflow-xxxx

# Check logs
kubectl logs -n mlflow mlflow-xxxx --all-containers
```

### Database Connection Issues

```bash
# Test connection
kubectl exec -n mlflow deployment/mlflow -c mlflow -- pg_isready -h mlflow-postgresql

# Check secret
kubectl get secret -n mlflow mlflow-secret -o yaml
```

### Backup Failures

```bash
# Check CronJob status
kubectl describe cronjob -n mlflow mlflow-backup

# Check last job logs
kubectl logs -n mlflow job/mlflow-backup-xxxxx
```

## Performance Tuning

### Database Optimization

The deployment includes automatic index creation for common queries:
- Experiment name lookups
- Run queries by experiment
- Metric/parameter queries by run

### Caching

Consider adding Redis for caching if experiencing high read loads:

```yaml
# Add to values.yaml
redis:
  enabled: true
  
env:
  - name: MLFLOW_REDIS_URL
    value: "redis://mlflow-redis:6379"
```

### Connection Pooling

Adjust Gunicorn workers based on workload:

```yaml
mlflow:
  workers: 8  # Increase for more concurrent requests
  threads: 4  # Increase for I/O bound operations
```

## Security Best Practices

1. **Always enable NetworkPolicy in production**
2. **Use strong auto-generated passwords**
3. **Enable TLS for ingress**
4. **Regularly rotate credentials**
5. **Review and update RBAC permissions**
6. **Enable audit logging**

## Cost Optimization

1. **Adjust autoscaling thresholds based on usage patterns**
2. **Use spot instances for worker nodes**
3. **Configure appropriate backup retention**
4. **Monitor and optimize storage usage**
5. **Use sampling for distributed tracing**

## Integration with threads-agent

The MLflow deployment integrates seamlessly with the threads-agent stack:

1. **Metrics**: Exposed on `/metrics` for Prometheus scraping
2. **Tracing**: Sends traces to Jaeger in monitoring namespace
3. **Logs**: Structured logging compatible with existing log aggregation
4. **Network**: Allows traffic from orchestrator and persona-runtime services

Example integration code:

```python
import mlflow
from opentelemetry import trace

# Configure MLflow
mlflow.set_tracking_uri("http://mlflow.mlflow.svc.cluster.local:5000")
mlflow.set_experiment("llm-experiments")

# Track LLM calls
with mlflow.start_run():
    mlflow.log_param("model", "gpt-4")
    mlflow.log_param("temperature", 0.7)
    
    # Your LLM call here
    
    mlflow.log_metric("tokens_used", 150)
    mlflow.log_metric("latency_ms", 1200)
```

## Maintenance

### Regular Tasks

1. **Weekly**: Review metrics and alerts
2. **Monthly**: Analyze resource usage and adjust limits
3. **Quarterly**: Review and test backup restoration
4. **Annually**: Security audit and dependency updates

### Upgrades

```bash
# Update Chart dependencies
helm dependency update

# Upgrade deployment
helm upgrade mlflow . -n mlflow --reuse-values

# Rollback if needed
helm rollback mlflow -n mlflow
```

## Support

For issues or questions:
1. Check pod logs and events
2. Review Grafana dashboards
3. Check AlertManager for firing alerts
4. Consult MLflow documentation
5. Review threads-agent project documentation