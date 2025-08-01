# Viral Engine Documentation

## Overview

The Viral Engine is the core content generation and optimization system for the Threads Agent platform. It uses advanced algorithms and machine learning to create engaging content while maintaining diversity and quality.

## Components

### 1. [Pattern Fatigue Detection Engine](./PATTERN_FATIGUE_DETECTION_ENGINE.md)
- **Purpose**: Prevents content pattern overuse and maintains freshness
- **Key Features**:
  - 7-day rolling window pattern tracking
  - Persona-specific fatigue detection
  - Real-time freshness scoring
  - Thompson Sampling integration
- **Added in**: CRA-233

### 2. Thompson Sampling Algorithm
- **Purpose**: Optimizes content variant selection using multi-armed bandit approach
- **Key Features**:
  - Exploration vs exploitation balance
  - Performance-based selection
  - Real-time adaptation

### 3. Content Generation Pipeline
- **Purpose**: Orchestrates the end-to-end content creation process
- **Key Features**:
  - Multi-stage generation
  - Quality guardrails
  - Performance tracking

## Quick Start

### Basic Usage

```python
from services.orchestrator import ViralEngine

# Initialize engine
engine = ViralEngine()

# Generate content with pattern fatigue awareness
result = engine.generate_content(
    persona_id="tech_enthusiast_123",
    topic="AI advancements",
    enable_fatigue_detection=True
)
```

### Configuration

```yaml
viral_engine:
  pattern_fatigue:
    enabled: true
    threshold: 3
    window_days: 7
  thompson_sampling:
    exploration_rate: 0.1
    batch_size: 10
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  Orchestrator   │────▶│  Viral Engine    │────▶│ Content Output  │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Pattern Analyzer   │
                    │  - Fatigue Detection│
                    │  - Freshness Scores │
                    └─────────────────────┘
```

## Performance Metrics

- Content generation: <500ms average
- Pattern analysis: <100ms per batch
- Fatigue detection: <50ms query time
- Overall throughput: 1000+ requests/minute

## Related Documentation

- [System Architecture](../README.md)
- [API Documentation](../api/README.md)
- [Performance Guide](../performance/README.md)