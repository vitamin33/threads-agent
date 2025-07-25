# Achievement Collector Service

A microservice for automatically collecting, tracking, and analyzing professional achievements from the Threads-Agent Stack project.

## Overview

The Achievement Collector service monitors development activities, captures metrics, and generates portfolio-ready documentation of professional accomplishments.

## Features

- **Automated Achievement Tracking**: Monitors Git commits, PRs, CI runs, and production metrics
- **Real-time Analysis**: AI-powered insights on impact and value
- **Portfolio Generation**: Markdown, PDF, and web formats
- **Metrics Collection**: Business impact, technical complexity, time savings

## Architecture

- FastAPI-based REST API
- PostgreSQL for achievement storage
- Redis for caching and real-time updates
- Celery for background processing
- Integration with GitHub webhooks

## API Endpoints

- `POST /achievements` - Create new achievement
- `GET /achievements` - List achievements with filtering
- `GET /achievements/{id}` - Get specific achievement
- `PUT /achievements/{id}` - Update achievement
- `DELETE /achievements/{id}` - Delete achievement
- `POST /achievements/analyze` - Analyze impact of achievement
- `GET /achievements/portfolio` - Generate portfolio document
- `POST /webhooks/github` - GitHub webhook endpoint

## Database Schema

See `db/models.py` for complete schema definition.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload

# Run tests
pytest
```

## Deployment

The service is deployed as part of the Threads-Agent Stack Kubernetes cluster.