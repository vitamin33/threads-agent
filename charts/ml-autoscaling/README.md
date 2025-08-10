# ML Autoscaling Helm Chart

## MLOPS-008 Implementation

This Helm chart deploys ML Infrastructure Auto-scaling with KEDA for the threads-agent platform.

## Features

- **KEDA-based autoscaling** for ML workloads
- **Predictive scaling** based on historical patterns
- **GPU-aware scaling** with cost optimization
- **Multi-trigger scaling** (queue depth, latency, GPU utilization)
- **Scale-to-zero** capability for GPU workloads
- **Business hours awareness**
- **Grafana dashboards** for monitoring

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Prometheus (for metrics)
- RabbitMQ (for Celery worker scaling)

## Installation

### Add Helm repository

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
```

### Install the chart

```bash
# Install with default values
helm install ml-autoscaling ./charts/ml-autoscaling

# Install with custom values
helm install ml-autoscaling ./charts/ml-autoscaling \
  --set services.vllmService.enabled=true \
  --set services.vllmService.minReplicas=0 \
  --set services.vllmService.maxReplicas=4
```

## Configuration

Key configuration options:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `enabled` | Enable ML autoscaling | `true` |
| `keda.enabled` | Install KEDA operator | `true` |
| `predictiveScaling.enabled` | Enable predictive scaling | `true` |
| `services.celeryWorker.enabled` | Enable Celery worker scaling | `true` |
| `services.vllmService.enabled` | Enable vLLM GPU scaling | `true` |
| `services.orchestrator.enabled` | Enable orchestrator scaling | `true` |

### Service-specific configuration

#### Celery Worker
```yaml
services:
  celeryWorker:
    enabled: true
    minReplicas: 2
    maxReplicas: 20
    triggers:
      rabbitmq:
        queueLength: 5  # Scale when queue > 5 messages
      latency:
        targetValue: 10  # Scale when latency > 10s
```

#### vLLM GPU Service
```yaml
services:
  vllmService:
    enabled: true
    minReplicas: 0  # Scale to zero when idle
    maxReplicas: 4
    preferSpotInstances: true
    triggers:
      requestRate:
        targetValue: 10  # RPS
      gpuUtilization:
        targetValue: 80  # Percentage
```

## Monitoring

The chart includes Grafana dashboards:

1. **ML Autoscaling Overview** - Overall scaling metrics
2. **ML Predictive Scaling** - Forecast accuracy and patterns
3. **ML Cost Optimization** - Cost tracking and optimization

Access dashboards:
```bash
kubectl port-forward svc/grafana 3000:3000
# Open http://localhost:3000
```

## Cost Optimization

Enable cost optimization features:

```yaml
businessRules:
  costOptimization:
    enabled: true
    maxHourlyCost: 100  # $100/hour max
    preferSpotInstances: true
    spotDiscountPercentage: 70  # 30% discount
```

## Predictive Scaling

Configure predictive scaling:

```yaml
predictiveScaling:
  enabled: true
  lookbackHours: 168  # 1 week of history
  forecastMinutes: 30
  confidenceThreshold: 0.7
  enableProactiveScaling: true
  scaleAheadMinutes: 15
```

## Troubleshooting

### Check KEDA operator status
```bash
kubectl get pods -n keda
kubectl logs -n keda deployment/keda-operator
```

### Check ScaledObject status
```bash
kubectl get scaledobjects
kubectl describe scaledobject <name>
```

### View scaling events
```bash
kubectl get events --sort-by='.lastTimestamp' | grep ScaledObject
```

## Uninstallation

```bash
helm uninstall ml-autoscaling
```

## Development

### Run tests
```bash
cd services/ml_autoscaling
pytest tests/
```

### Validate Helm chart
```bash
helm lint charts/ml-autoscaling
helm template ml-autoscaling charts/ml-autoscaling
```

## License

Apache 2.0

## Support

For issues and questions, please open an issue in the threads-agent repository.