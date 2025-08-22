# Apple Silicon Local LM Evaluation Suite

Professional evaluation framework for 7-9B instruct models on Apple Silicon M4 Max with pairwise LLM-as-judge, bootstrap confidence intervals, and Elo ranking.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key for judging
export OPENAI_API_KEY="your-key-here"

# Run preparation
python -m evalsuite.cli prepare

# Test with smoke test (2 prompts per task, one model)
python -m evalsuite.cli run --stack mps --models opt-2.7b --tasks linkedin
```

## Commands

### Prepare Environment
```bash
python -m evalsuite.cli prepare
```
Validates environment, downloads models, prints dataset and config hashes.

### Run Evaluation
```bash
python -m evalsuite.cli run --stack {mlx|mps|llamacpp} --models all --tasks all
```
Generates outputs for each model and prompt with fixed sampling parameters.

### Judge Outputs
```bash
python -m evalsuite.cli judge --models all --tasks all --seeds 3
```
Runs pairwise comparisons using LLM-as-judge with deterministic formatting.

### Calculate Rankings
```bash
python -m evalsuite.cli rank
```
Computes Elo rankings with bootstrap 95% confidence intervals.

### Measure Performance
```bash
python -m evalsuite.cli perf --stack {mlx|mps|llamacpp}
```
Measures p50/p95 latency, tokens/sec, peak RSS with consistent sampling.

### Cost Analysis
```bash
python -m evalsuite.cli cost
```
Produces cost sensitivity table with local kWh vs cloud baseline.

### Generate Report
```bash
python -m evalsuite.cli report
```
Builds comprehensive Markdown report with all results.

## Full Pipeline
```bash
# Run complete evaluation suite
./scripts/repro.sh
```

## Configuration

Edit `evalsuite/configs/experiment.yml` for:
- Model selection and licensing
- Sampling parameters
- Local power costs
- Cloud pricing baselines
- MLflow configuration

## Apple Silicon Optimization

- **MPS Stack**: PyTorch with Metal Performance Shaders
- **MLX Stack**: Apple's native ML framework (install mlx-lm)
- **Llama.cpp**: Quantized GGUF models for memory efficiency

## Results

All results logged to MLflow with comprehensive metrics and artifacts:
- Model rankings with confidence intervals
- Performance benchmarks across stacks
- Cost analysis and sensitivity tables
- Complete reproducibility data