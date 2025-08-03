# Tech Documentation Generator Service

## Overview
AI-powered service that analyzes codebases to generate technical documentation, blog posts, and social media content. Part of the threads-agent microservices architecture.

## Key Features

### 1. Code Analysis
- AST-based code understanding
- Pattern recognition and architectural insights
- Performance metrics extraction
- Git history analysis

### 2. Content Generation
- Technical documentation
- API documentation
- Architecture explanations
- Performance optimization stories
- Best practices articles

### 3. Quality Scoring
- Engagement prediction (0-100)
- Technical depth rating
- Readability analysis
- Trend alignment

### 4. Multi-Platform Publishing
- Dev.to integration
- LinkedIn posts
- Threads/Twitter content
- GitHub documentation

## Quick Start

```bash
# Install dependencies
cd services/tech_doc_generator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.sample .env
# Edit .env with your API keys

# Run tests
python -m pytest tests/

# Run service
uvicorn app.main:app --reload
```

## API Endpoints

- `POST /analyze` - Analyze repository or PR
- `POST /generate` - Generate article from analysis
- `POST /publish` - Publish to platforms
- `GET /insights/{id}` - Get analysis results

## Architecture

Integrates with:
- **Orchestrator**: Task scheduling
- **Celery Worker**: Async processing
- **Viral Engine**: Content optimization
- **Achievement Collector**: Impact tracking

## Configuration

Required environment variables:
- `OPENAI_API_KEY` - For content generation
- `GITHUB_TOKEN` - For repo analysis
- Platform-specific tokens (optional)

## Testing

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/
```