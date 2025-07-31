# Pattern Analyzer Service

A service for detecting and preventing pattern fatigue in AI-generated content.

## Features

- **Pattern Extraction**: Identifies patterns in generated content
- **Fatigue Detection**: Tracks pattern usage over 7-day rolling window
- **Freshness Scoring**: Provides scores for variant selection weighting
- **Database Integration**: Persistent storage with SQLAlchemy
- **High Performance**: <100ms latency for fatigue checking

## Components

### PatternFatigueDetector
Tracks pattern usage and detects fatigue (3+ uses in 7 days).

### PatternExtractor
Extracts reusable patterns from generated content.

### PatternUsage Model
Database model for tracking pattern usage history.

## Usage

```python
from services.pattern_analyzer.service import PatternAnalyzerService

# Initialize service (optionally with database session)
service = PatternAnalyzerService(db_session=session)

# Check pattern fatigue
result = service.check_pattern_fatigue(
    pattern="Check out this amazing {topic}!",
    persona_id="viral_tech_tips"
)

print(f"Is fatigued: {result['is_fatigued']}")
print(f"Freshness score: {result['freshness_score']}")
```

## Testing

Run all tests:
```bash
pytest services/pattern_analyzer/tests/ -v
```

Check coverage:
```bash
pytest services/pattern_analyzer/tests/ --cov=services.pattern_analyzer
```

## Performance

- Pattern fatigue checking: <100ms even with 1000+ patterns
- Efficient database queries with proper indexing
- In-memory fallback for testing