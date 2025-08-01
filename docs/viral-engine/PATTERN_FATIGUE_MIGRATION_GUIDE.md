# Pattern Fatigue Detection - Migration Guide

## Overview

This guide helps developers integrate the Pattern Fatigue Detection Engine into existing content generation workflows.

## Migration Steps

### 1. Database Migration

Run the Alembic migration to create the necessary tables:

```bash
# From the orchestrator service directory
cd services/orchestrator
alembic upgrade head
```

This creates the `pattern_usage` table with all required indexes.

### 2. Update Thompson Sampling Integration

Replace the standard Thompson Sampling with the fatigue-aware version:

```python
# Before
from services.orchestrator.thompson_sampling import ThompsonSampling
sampler = ThompsonSampling()

# After
from services.orchestrator.thompson_sampling_with_fatigue import ThompsonSamplingWithFatigue
sampler = ThompsonSamplingWithFatigue()
```

### 3. Configure Pattern Analysis

Add pattern analyzer service to your Docker Compose:

```yaml
pattern-analyzer:
  build:
    context: ./services/pattern_analyzer
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - PATTERN_FATIGUE_THRESHOLD=3
    - PATTERN_FATIGUE_WINDOW_DAYS=7
  depends_on:
    - postgres
```

### 4. Update Helm Charts

Add the pattern analyzer to your Kubernetes deployment:

```yaml
# chart/templates/pattern-analyzer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pattern-analyzer
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: pattern-analyzer
        image: pattern-analyzer:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: url
```

## Code Integration Examples

### Basic Integration

```python
# Minimal changes required
from services.viral_engine import ViralEngine

engine = ViralEngine(enable_pattern_fatigue=True)
content = engine.generate(persona_id, topic)
```

### Advanced Integration

```python
from services.pattern_analyzer import PatternFatigueDetector
from services.orchestrator.thompson_sampling_with_fatigue import ThompsonSamplingWithFatigue

class EnhancedContentGenerator:
    def __init__(self):
        self.fatigue_detector = PatternFatigueDetector()
        self.sampler = ThompsonSamplingWithFatigue()
    
    def generate_with_diversity(self, persona_id, topic, variants):
        # Check current pattern usage
        pattern_stats = self.fatigue_detector.get_pattern_stats(persona_id)
        
        # Select variants with fatigue awareness
        selected = self.sampler.select(
            variants=variants,
            persona_id=persona_id,
            n_select=5
        )
        
        return selected
```

### Custom Pattern Extraction

```python
from services.pattern_analyzer import PatternExtractor

class CustomPatternExtractor(PatternExtractor):
    def extract_pattern(self, content):
        # Custom extraction logic
        pattern = super().extract_pattern(content)
        
        # Additional processing
        pattern = self.normalize_pattern(pattern)
        pattern = self.add_semantic_tags(pattern)
        
        return pattern
```

## Configuration Options

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost/threads

# Optional (with defaults)
PATTERN_FATIGUE_THRESHOLD=3
PATTERN_FATIGUE_WINDOW_DAYS=7
PATTERN_CACHE_TTL=300
PATTERN_BATCH_SIZE=100
PATTERN_ANALYSIS_ENABLED=true
```

### Runtime Configuration

```python
# Configure at runtime
from services.pattern_analyzer import configure_fatigue_detection

configure_fatigue_detection(
    threshold=5,  # More lenient
    window_days=14,  # Longer window
    cache_ttl=600  # Longer cache
)
```

## Testing Your Integration

### Unit Tests

```python
import pytest
from services.pattern_analyzer import PatternFatigueDetector

def test_pattern_fatigue_integration():
    detector = PatternFatigueDetector()
    
    # Test pattern is not initially fatigued
    assert not detector.is_pattern_fatigued(
        "Test pattern {var}",
        "test_persona"
    )
    
    # Record usage
    for _ in range(3):
        detector.record_pattern_usage(
            "Test pattern {var}",
            "test_persona"
        )
    
    # Test pattern is now fatigued
    assert detector.is_pattern_fatigued(
        "Test pattern {var}",
        "test_persona"
    )
```

### Integration Tests

```python
@pytest.mark.integration
async def test_full_generation_with_fatigue():
    engine = ViralEngine(enable_pattern_fatigue=True)
    
    # Generate content multiple times
    results = []
    for _ in range(10):
        content = await engine.generate(
            persona_id="test_persona",
            topic="AI"
        )
        results.append(content)
    
    # Verify pattern diversity
    patterns = [extract_pattern(r.content) for r in results]
    unique_patterns = len(set(patterns))
    
    assert unique_patterns >= 5  # Should use diverse patterns
```

## Rollback Plan

If issues arise, you can disable pattern fatigue detection without code changes:

```bash
# Disable via environment variable
PATTERN_ANALYSIS_ENABLED=false

# Or disable at runtime
sampler = ThompsonSamplingWithFatigue(enable_fatigue_detection=False)
```

## Common Issues and Solutions

### Issue: High Database Load

**Solution**: Adjust batch sizes and caching:
```python
configure_fatigue_detection(
    batch_size=50,  # Smaller batches
    cache_ttl=900   # Longer cache
)
```

### Issue: Patterns Not Being Detected

**Solution**: Check pattern extraction:
```python
# Debug pattern extraction
extractor = PatternExtractor()
pattern = extractor.extract_pattern(content)
print(f"Extracted pattern: {pattern}")
```

### Issue: Too Aggressive Fatigue Detection

**Solution**: Adjust thresholds:
```python
configure_fatigue_detection(
    threshold=5,     # Allow more uses
    window_days=3    # Shorter window
)
```

## Performance Considerations

1. **Database Indexes**: Ensure all migrations ran successfully
2. **Connection Pooling**: Use connection pooling for high traffic
3. **Caching**: Redis caching recommended for >1000 req/min
4. **Batch Processing**: Process patterns in batches for efficiency

## Monitoring

Add these metrics to your monitoring:

```python
# Prometheus metrics
pattern_diversity_score{persona_id="..."}
pattern_fatigue_rate{persona_id="..."}
pattern_extraction_latency_seconds
fatigue_check_latency_seconds
```

## Support

For issues or questions:
1. Check logs in `/var/log/pattern-analyzer/`
2. Review database query performance
3. Verify environment variables
4. Check integration test results