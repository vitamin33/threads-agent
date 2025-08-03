# Viral Pattern Engine

AI-powered viral content pattern extraction service that analyzes social media posts to identify viral patterns and predict engagement potential.

## Features

### Core Pattern Detection
- **Hook Patterns**: Discovery, statistical, transformation stories, curiosity gaps, urgency
- **Emotion Patterns**: Excitement, amazement, surprise detection
- **Structure Patterns**: Content length, thread indicators, reading time analysis
- **Engagement Correlation**: Pattern strength scoring and engagement prediction

### API Endpoints

#### `POST /extract-patterns`
Extract viral patterns from a single post.

**Request Body:**
```json
{
  "content": "Just discovered this incredible Python library that automates 90% of my data analysis!",
  "account_id": "user123",
  "post_url": "https://threads.net/post1",
  "timestamp": "2025-01-01T12:00:00Z",
  "likes": 1500,
  "comments": 300,
  "shares": 150,
  "engagement_rate": 0.85,
  "performance_percentile": 95.0
}
```

**Response:**
```json
{
  "hook_patterns": [
    {
      "type": "discovery",
      "template": "Just discovered this incredible {tool} that {benefit}!",
      "confidence": 0.8
    }
  ],
  "emotion_patterns": [
    {
      "type": "excitement",
      "intensity": 0.8,
      "confidence": 0.7
    }
  ],
  "structure_patterns": [
    {
      "length_category": "medium",
      "has_thread_indicator": false,
      "sentence_count": 1,
      "reading_time_seconds": 60,
      "word_count": 15
    }
  ],
  "engagement_score": 0.85,
  "pattern_strength": 0.9
}
```

#### `POST /analyze-batch`
Analyze multiple posts in batch with summary statistics.

#### `GET /pattern-types`
Get available pattern types that can be detected.

#### `GET /health`
Health check endpoint.

## Pattern Types

### Hook Patterns
1. **Discovery**: "Just discovered this incredible..."
2. **Statistical**: "Increased productivity by 300%..."
3. **Transformation Story**: "3 months ago... today..."
4. **Curiosity Gap**: "The secret that experts don't want you to know..."
5. **Urgency**: "🚨 BREAKING: ..."

### Emotion Patterns
- **Excitement**: High-energy positive emotions
- **Amazement**: Wonder and surprise indicators
- **Surprise**: Unexpected revelation patterns

### Structure Patterns
- **Length Categories**: Short (<20 words), Medium (20-100), Long (>100)
- **Thread Indicators**: Detection of multi-part content markers
- **Readability**: Sentence count and estimated reading time

## Development

### Setup
```bash
cd services/viral_pattern_engine
pip install -r requirements.txt
```

### Running Tests
```bash
pytest -v
```

### Running the Service
```bash
uvicorn main:app --reload --port 8000
```

### Docker
```bash
docker build -t viral-pattern-engine .
docker run -p 8000:8000 viral-pattern-engine
```

## Integration

The service integrates with:
- **viral_scraper**: Consumes ViralPost models
- **orchestrator**: Provides pattern analysis for content generation
- **PostgreSQL**: For pattern storage and analytics

## Testing

- **18 test cases** covering all functionality
- **TDD approach** with comprehensive coverage
- **Error handling** and edge case validation
- **API integration** tests with FastAPI TestClient

## Architecture

```
viral_pattern_engine/
├── main.py                    # FastAPI service
├── pattern_extractor.py       # Core ML/NLP pattern extraction
├── tests/
│   ├── test_pattern_extractor.py    # Core logic tests
│   ├── test_advanced_patterns.py    # Advanced feature tests
│   ├── test_api.py                  # API endpoint tests
│   └── test_error_handling.py       # Error handling tests
├── requirements.txt
├── Dockerfile
└── README.md
```

## Performance

- **Pattern Strength Scoring**: 0.0-1.0 confidence scoring
- **Batch Processing**: Efficient multi-post analysis
- **Engagement Correlation**: Pattern effectiveness metrics
- **Real-time Analysis**: Sub-second response times

Built with Test-Driven Development (TDD) for the threads-agent ecosystem.