# MLflow Quick Start Guide

## 🚀 5-Minute Setup

### 1. Deploy MLflow (One-time setup)

```bash
# Deploy to cluster
cd services/mlflow
make deploy-helm

# Access UI
kubectl port-forward -n mlflow svc/mlflow 8085:5000
open http://localhost:8085
```

### 2. Track Your First LLM Call

```python
# In any service that uses OpenAI
from services.common.mlflow_openai_wrapper import chat_with_tracking

# Replace your existing call
response = chat_with_tracking(
    model="gpt-4o",
    prompt="Generate a viral tweet about AI",
    persona_id="viral_creator"
)
```

That's it! Your LLM call is now tracked in MLflow.

## 📊 View Your Data

### In MLflow UI

1. Go to http://localhost:8085
2. Click on experiment (e.g., `viral_creator_2025-01-31`)
3. View runs with metrics:
   - Token usage
   - Latency
   - Cost estimation

### Quick Queries

```python
# Get today's token usage
import mlflow
from datetime import datetime

mlflow.set_tracking_uri("http://localhost:8085")
today = datetime.now().strftime("%Y-%m-%d")
experiment = mlflow.get_experiment_by_name(f"viral_creator_{today}")

if experiment:
    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    total_tokens = runs['metrics.total_tokens'].sum()
    print(f"Total tokens today: {total_tokens}")
```

## 💰 Cost Tracking

```python
# Calculate costs for a persona
def calculate_persona_cost(persona_id: str, date: str):
    experiment_name = f"{persona_id}_{date}"
    experiment = mlflow.get_experiment_by_name(experiment_name)
    
    if not experiment:
        return 0
    
    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    
    # GPT-4o pricing
    input_cost = runs['metrics.prompt_tokens'].sum() / 1000 * 0.005
    output_cost = runs['metrics.completion_tokens'].sum() / 1000 * 0.015
    
    return input_cost + output_cost

# Example
cost = calculate_persona_cost("viral_creator", "2025-01-31")
print(f"Cost: ${cost:.2f}")
```

## 🔍 Common Queries

### Find High-Latency Calls

```python
# Find slow API calls
slow_runs = runs[runs['metrics.latency_ms'] > 1000]
print(f"Slow calls: {len(slow_runs)}")
```

### Compare Models

```python
# Compare token efficiency
gpt4_runs = runs[runs['params.model'] == 'gpt-4o']
gpt35_runs = runs[runs['params.model'] == 'gpt-3.5-turbo']

print(f"GPT-4o avg tokens: {gpt4_runs['metrics.total_tokens'].mean()}")
print(f"GPT-3.5 avg tokens: {gpt35_runs['metrics.total_tokens'].mean()}")
```

### Daily Summary

```python
# Get daily summary for all personas
from collections import defaultdict

summaries = defaultdict(lambda: {'calls': 0, 'tokens': 0, 'cost': 0})

for persona in ['viral_creator', 'tech_expert', 'comedian']:
    exp_name = f"{persona}_{today}"
    exp = mlflow.get_experiment_by_name(exp_name)
    
    if exp:
        runs = mlflow.search_runs(experiment_ids=[exp.experiment_id])
        summaries[persona]['calls'] = len(runs)
        summaries[persona]['tokens'] = runs['metrics.total_tokens'].sum()
        summaries[persona]['cost'] = calculate_persona_cost(persona, today)

# Print summary
for persona, data in summaries.items():
    print(f"{persona}: {data['calls']} calls, {data['tokens']} tokens, ${data['cost']:.2f}")
```

## 🛠️ Troubleshooting

### MLflow Not Reachable

```bash
# Check if MLflow is running
kubectl -n mlflow get pods

# If not running, deploy it
cd services/mlflow && make deploy-helm
```

### Missing Tracking Data

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test tracking
from services.common.mlflow_tracking import MLflowExperimentTracker
tracker = MLflowExperimentTracker()
# Check console for error messages
```

### Reset MLflow Data

```bash
# Delete and recreate (WARNING: Deletes all data)
kubectl -n mlflow delete pvc mlflow-pvc
kubectl -n mlflow delete pod -l app.kubernetes.io/name=mlflow
```

## 📈 Best Practices

1. **Always specify persona_id** - Makes filtering easier
2. **Use descriptive persona names** - `viral_creator` not `bot1`
3. **Monitor daily** - Check token usage and costs
4. **Set up alerts** - For high token usage or costs

## 🔗 More Resources

- [Full Documentation](./MLFLOW_EXPERIMENT_TRACKING.md)
- [Epic Overview](./E4.5_MLOPS_FOUNDATION_EPIC.md)
- [Deployment Guide](../../services/mlflow/DEPLOYMENT_GUIDE.md)