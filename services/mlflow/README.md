# MLflow Service for Threads-Agent

This service provides MLflow experiment tracking for all LLM calls in the threads-agent project.

## Features

- **Automatic LLM Call Tracking**: Tracks prompts, responses, tokens, and latency
- **Experiment Organization**: Groups experiments by persona and date
- **PostgreSQL Backend**: Stores experiment metadata
- **MinIO/S3 Storage**: Stores artifacts and large objects
- **Kubernetes Ready**: Helm chart for easy deployment

## Deployment

### Prerequisites

- Kubernetes cluster (k3d for local development)
- Helm 3.x installed
- kubectl configured

### Install with Helm

```bash
# Add bitnami repo for dependencies
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install MLflow
cd services/mlflow
helm dependency update ./helm
helm install mlflow ./helm -n threads-agent

# Check deployment
kubectl get pods -n threads-agent
kubectl get svc -n threads-agent
```

### Access MLflow UI

```bash
# Port forward for local access
kubectl port-forward svc/mlflow 5000:5000 -n threads-agent

# Open browser
open http://localhost:5000
```

Or use the configured ingress at `http://mlflow.local` (requires /etc/hosts entry).

## Integration

### 1. Direct Tracking

```python
from services.common.mlflow_tracking import MLflowExperimentTracker

tracker = MLflowExperimentTracker()
tracker.track_llm_call(
    persona_id="viral_creator",
    model="gpt-4o",
    prompt="Create viral content",
    response="Response text...",
    prompt_tokens=10,
    completion_tokens=20,
    latency_ms=150
)
```

### 2. Enhanced Wrapper

```python
from services.common.mlflow_openai_wrapper import chat_with_tracking

response = chat_with_tracking(
    model="gpt-4o",
    prompt="Your prompt",
    persona_id="persona_name"
)
```

### 3. Decorator for Async Functions

```python
from services.common.mlflow_tracking import track_llm_call

@track_llm_call(persona_id="assistant")
async def generate_content(prompt: str):
    # Your OpenAI API call here
    return response
```

## Configuration

### Environment Variables

- `MLFLOW_TRACKING_URI`: MLflow server URL (default: http://localhost:5000)
- `MLFLOW_BACKEND_STORE_URI`: Database connection string
- `MLFLOW_DEFAULT_ARTIFACT_ROOT`: S3/MinIO bucket for artifacts
- `AWS_ACCESS_KEY_ID`: MinIO access key
- `AWS_SECRET_ACCESS_KEY`: MinIO secret key

### Helm Values

Key configuration options in `helm/values.yaml`:

```yaml
service:
  type: LoadBalancer  # or ClusterIP for internal only
  port: 5000

postgresql:
  enabled: true
  postgresqlDatabase: mlflow

minio:
  enabled: true
  defaultBuckets: mlflow-artifacts
```

## Monitoring

### Tracked Metrics

- `prompt_tokens`: Number of tokens in the prompt
- `completion_tokens`: Number of tokens in the response
- `total_tokens`: Sum of prompt and completion tokens
- `latency_ms`: Response time in milliseconds

### Experiment Organization

Experiments are organized by:
- **Persona**: The AI persona making the call
- **Date**: YYYY-MM-DD format
- Example: `viral_creator_2024-01-31`

## Testing

```bash
# Run unit tests
pytest services/common/tests/test_mlflow_*.py -v

# Run integration tests
pytest services/mlflow/tests/ -v
```

## Troubleshooting

### MLflow Server Unavailable

The tracking client handles server unavailability gracefully:
- Logs warnings but doesn't crash
- Continues normal operation
- Tracking resumes when server is back

### View Logs

```bash
kubectl logs -f deployment/mlflow -n threads-agent
```

### Check Health

```bash
curl http://localhost:5000/health
```

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   LLM Calls     │────▶│   MLflow     │────▶│ PostgreSQL  │
│ (OpenAI, etc.)  │     │   Tracker    │     │  (Metadata) │
└─────────────────┘     └──────────────┘     └─────────────┘
                               │
                               ▼
                        ┌─────────────┐
                        │    MinIO    │
                        │ (Artifacts) │
                        └─────────────┘
```

## Next Steps

1. **Dashboard Integration**: Connect to Grafana for visualization
2. **Alerts**: Set up alerts for token usage and costs
3. **Model Registry**: Integrate with MLflow model registry
4. **A/B Testing**: Use experiments for prompt optimization