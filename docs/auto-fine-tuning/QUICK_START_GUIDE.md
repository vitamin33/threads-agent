# 🚀 Auto-Fine-Tuning Quick Start Guide

## How It Works

The pipeline automatically improves your models by:
1. **Collecting** high-engagement posts weekly (>6% engagement)
2. **Training** new models using OpenAI fine-tuning
3. **Testing** via A/B testing to ensure improvements
4. **Deploying** only if performance improves

## Setup Instructions

### 1. Configure Environment
```bash
export OPENAI_API_KEY=your-openai-api-key
export MLFLOW_TRACKING_URI=http://mlflow:5000  # Optional
```

### 2. Deploy to Kubernetes
```bash
# Create secrets
kubectl create secret generic openai-credentials \
  --from-literal=api-key=$OPENAI_API_KEY

# Deploy the pipeline
kubectl apply -f /tmp/fine_tuning_configmap.yaml
kubectl apply -f /tmp/fine_tuning_cronjob.yaml
```

### 3. Manual Testing (Optional)
```python
from services.common.fine_tuning_pipeline import FineTuningPipeline, PipelineConfig

# Configure
config = PipelineConfig(
    training_data_threshold=100,    # Min examples needed
    engagement_threshold=0.06,      # 6% engagement filter
    weekly_schedule="0 2 * * 0"     # Sunday 2 AM
)

# Run manually
pipeline = FineTuningPipeline(config=config)
result = await pipeline.run()
```

## Configuration Options

### Engagement Threshold
Controls which posts are used for training:
```python
engagement_threshold=0.06  # Only posts with 6%+ engagement
```

### Training Frequency
Cron schedule for automatic training:
```python
weekly_schedule="0 2 * * 0"  # Every Sunday at 2 AM
```

### A/B Testing
How long to test new models:
```python
a_b_test_duration_hours=168  # 1 week of testing
```

## Monitoring

### Check Pipeline Status
```bash
# View CronJob runs
kubectl get jobs | grep fine-tuning

# Check logs
kubectl logs -l job-name=fine-tuning-pipeline-xxxxx
```

### View Metrics
- **Grafana**: http://localhost:3000 (fine-tuning dashboard)
- **MLflow**: http://localhost:5000 (experiment tracking)

### Key Metrics to Watch
- `fine_tuning_training_examples_total` - Training data collected
- `fine_tuning_model_performance` - Model improvement %
- `fine_tuning_cost_per_training` - Training costs

## Customization

### Adjust Thresholds
Edit ConfigMap to change settings:
```bash
kubectl edit configmap fine-tuning-config
```

### Change Models
Update environment variables:
```bash
HOOK_MODEL=gpt-4o              # Hook generation
BODY_MODEL=gpt-3.5-turbo-0125  # Body generation
```

## Troubleshooting

### Not Enough Training Data
- Lower `training_data_threshold` (default: 100)
- Lower `engagement_threshold` (default: 0.06)
- Wait for more engagement data

### Pipeline Not Running
```bash
# Check CronJob
kubectl describe cronjob fine-tuning-pipeline

# Trigger manually
kubectl create job --from=cronjob/fine-tuning-pipeline manual-run
```

### Model Not Improving
- Check A/B test results in MLflow
- Verify training data quality
- Adjust `safety_threshold` for deployment

## Expected Results

After successful fine-tuning:
- **Engagement**: +10-20% improvement
- **Cost**: -20-30% per generation
- **Quality**: Better hooks and content
- **Automatic**: Continuous improvement weekly