# CRA-297 CI/CD Pipeline Deployment Guide

## 🚀 Quick Start

```bash
# Deploy everything with one command
just deploy-cicd-pipeline

# Or manually:
kubectl apply -f chart/templates/cicd-pipeline.yaml
kubectl apply -f chart/templates/redis-cluster.yaml
kubectl apply -f chart/templates/cicd-monitoring.yaml
```

## 📋 Prerequisites

- Kubernetes cluster (k3d) running
- MLflow server deployed
- Prometheus & Grafana deployed
- GitHub repository with Actions enabled
- Required secrets configured

## 🔧 Step-by-Step Deployment

### 1. Prepare Environment

```bash
# Verify k3d cluster
k3d cluster list
kubectl cluster-info

# Check existing services
kubectl get svc -A | grep -E "(mlflow|prometheus|grafana)"

# Create namespace (if needed)
kubectl create namespace cicd-pipeline
```

### 2. Configure Secrets

```bash
# Create Kubernetes secrets
kubectl create secret generic cicd-secrets \
  --from-literal=MLFLOW_TRACKING_URI=http://mlflow.mlflow.svc.cluster.local:5000 \
  --from-literal=PROMETHEUS_URL=http://prometheus.monitoring.svc.cluster.local:9090 \
  --from-literal=OPENAI_API_KEY=your-key \
  -n default

# Configure GitHub secrets
gh secret set MLFLOW_TRACKING_URI --body "http://mlflow.mlflow.svc.cluster.local:5000"
gh secret set PROMETHEUS_URL --body "http://prometheus.monitoring.svc.cluster.local:9090"
gh secret set SLACK_WEBHOOK --body "your-webhook-url"
gh secret set PAGERDUTY_TOKEN --body "your-token"
gh secret set OPENAI_API_KEY --body "your-key"
```

### 3. Deploy CI/CD Components

```bash
# Deploy main CI/CD pipeline
kubectl apply -f chart/templates/cicd-pipeline.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=cicd-pipeline --timeout=300s

# Verify deployment
kubectl get pods -l app=cicd-pipeline
kubectl logs -l app=cicd-pipeline --tail=50
```

### 4. Deploy Redis Cache Cluster

```bash
# Deploy Redis for caching
kubectl apply -f chart/templates/redis-cluster.yaml

# Wait for Redis
kubectl wait --for=condition=ready pod -l app=redis-cluster --timeout=300s

# Test Redis connection
kubectl exec -it redis-cluster-0 -- redis-cli ping
```

### 5. Configure Monitoring

```bash
# Deploy monitoring configuration
kubectl apply -f chart/templates/cicd-monitoring.yaml

# Update Prometheus config
kubectl rollout restart deployment/prometheus -n monitoring

# Import Grafana dashboards
kubectl exec -it deployment/grafana -n monitoring -- \
  curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @/dashboards/cicd-pipeline.json
```

### 6. Enable GitHub Workflows

```bash
# List available workflows
gh workflow list

# Enable CI/CD workflows
gh workflow enable prompt-template-pr.yml
gh workflow enable gradual-rollout.yml
gh workflow enable performance-monitoring.yml
gh workflow enable emergency-rollback.yml

# Verify workflows are enabled
gh workflow list --all
```

## 🔍 Verification Steps

### 1. Test Component Health

```bash
# Check pod status
kubectl get pods -l app=cicd-pipeline -o wide

# Test PromptTestRunner
kubectl exec -it deployment/cicd-pipeline -- python -c "
from services.common.prompt_test_runner import PromptTestRunner
runner = PromptTestRunner()
print('PromptTestRunner: OK')
"

# Test RegressionDetector
kubectl exec -it deployment/cicd-pipeline -- python -c "
from services.common.performance_regression_detector import PerformanceRegressionDetector
detector = PerformanceRegressionDetector()
print('PerformanceRegressionDetector: OK')
"
```

### 2. Test Integration Points

```bash
# Test MLflow connection
kubectl exec -it deployment/cicd-pipeline -- python -c "
from services.common.mlflow_model_registry_config import get_mlflow_client
client = get_mlflow_client()
print(f'MLflow connection: OK')
print(f'Registered models: {len(client.search_registered_models())}')
"

# Test Prometheus connection
kubectl exec -it deployment/cicd-pipeline -- curl -s \
  http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up | jq '.status'
```

### 3. Run Smoke Tests

```bash
# Trigger test workflow
gh workflow run prompt-template-pr.yml \
  -f prompt_name="test-prompt"

# Monitor workflow
gh run list --workflow=prompt-template-pr.yml
gh run view $(gh run list --workflow=prompt-template-pr.yml --limit 1 --json databaseId -q '.[0].databaseId')
```

## 🔧 Configuration Options

### Environment Variables

```yaml
# chart/values-cicd.yaml
cicdPipeline:
  env:
    - name: MLFLOW_TRACKING_URI
      value: "http://mlflow.mlflow.svc.cluster.local:5000"
    - name: PROMETHEUS_URL
      value: "http://prometheus.monitoring.svc.cluster.local:9090"
    - name: ROLLBACK_TIMEOUT
      value: "30"
    - name: HEALTH_CHECK_INTERVAL
      value: "30"
    - name: MAX_CONCURRENT_ROLLOUTS
      value: "3"
    - name: REGRESSION_CONFIDENCE_LEVEL
      value: "0.95"
```

### Resource Allocation

```yaml
# Adjust based on cluster capacity
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"

# HPA settings
autoscaling:
  enabled: true
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
```

## 📊 Post-Deployment Setup

### 1. Configure Prometheus Alerts

```yaml
# Add to Prometheus rules
groups:
  - name: cicd_pipeline_alerts
    rules:
      - alert: RollbackSLABreach
        expr: cicd_pipeline_rollback_duration_seconds > 30
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Rollback exceeded 30s SLA"
          
      - alert: HighRegressionRate
        expr: rate(cicd_pipeline_regression_detected_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High regression detection rate"
```

### 2. Setup Grafana Dashboards

```bash
# Import dashboards
for dashboard in cicd-overview model-performance rollout-progress; do
  kubectl cp dashboards/${dashboard}.json \
    grafana-pod:/tmp/${dashboard}.json -n monitoring
  
  kubectl exec -it deployment/grafana -n monitoring -- \
    curl -X POST http://localhost:3000/api/dashboards/import \
    -H "Content-Type: application/json" \
    -d @/tmp/${dashboard}.json
done
```

### 3. Configure Slack Notifications

```bash
# Test Slack webhook
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-type: application/json' \
  -d '{"text":"CI/CD Pipeline deployed successfully!"}'
```

## 🔍 Troubleshooting

### Common Issues

1. **Pods not starting**
```bash
# Check pod events
kubectl describe pod -l app=cicd-pipeline

# Check logs
kubectl logs -l app=cicd-pipeline --previous

# Common fixes:
# - Verify secrets exist
# - Check resource limits
# - Verify image pull permissions
```

2. **MLflow connection issues**
```bash
# Test connectivity
kubectl exec -it deployment/cicd-pipeline -- \
  curl -v http://mlflow.mlflow.svc.cluster.local:5000/health

# Check MLflow service
kubectl get svc -n mlflow
kubectl logs -n mlflow deployment/mlflow
```

3. **GitHub workflow failures**
```bash
# Check workflow permissions
gh auth status
gh repo view --json permissions

# Re-run with debug
gh workflow run prompt-template-pr.yml \
  --ref main \
  -f debug_enabled=true
```

## 🔄 Rollback Deployment

If deployment fails:

```bash
# Rollback Kubernetes deployment
kubectl rollout undo deployment/cicd-pipeline

# Or delete and reapply
kubectl delete -f chart/templates/cicd-pipeline.yaml
kubectl apply -f chart/templates/cicd-pipeline-stable.yaml

# Disable workflows if needed
gh workflow disable prompt-template-pr.yml
gh workflow disable gradual-rollout.yml
```

## 📈 Performance Tuning

### Optimize for Speed

```bash
# Increase replicas for high load
kubectl scale deployment/cicd-pipeline --replicas=5

# Enable in-memory caching
kubectl set env deployment/cicd-pipeline \
  ENABLE_MEMORY_CACHE=true \
  CACHE_SIZE_MB=512
```

### Optimize for Cost

```bash
# Reduce resource requests
kubectl patch deployment/cicd-pipeline --patch '
spec:
  template:
    spec:
      containers:
      - name: cicd-pipeline
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
'

# Enable spot instances
kubectl label nodes node1 node-type=spot
kubectl patch deployment/cicd-pipeline --patch '
spec:
  template:
    spec:
      nodeSelector:
        node-type: spot
'
```

## 🎯 Next Steps

1. **Run test deployments** to verify everything works
2. **Set up monitoring alerts** in Grafana
3. **Configure backup procedures** for rollback history
4. **Train team** on emergency procedures
5. **Document runbooks** for common scenarios

---

**Support**: Contact MLOps team via Slack #mlops-support
**Documentation**: See [CRA-297_CICD_PIPELINE_README.md](./CRA-297_CICD_PIPELINE_README.md)
**Version**: 1.0.0