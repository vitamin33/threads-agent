from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
import structlog

from .routers import articles, manual_publish
from .core.config import get_settings
from .core.database import init_database, close_database
from .core.cache import get_cache_manager
from .core.middleware import MetricsMiddleware, HealthCheckMiddleware

logger = structlog.get_logger()

# Prometheus metrics for comprehensive monitoring
REQUEST_COUNT = Counter('tech_doc_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('tech_doc_request_duration_seconds', 'Request latency', ['endpoint'])
ARTICLES_GENERATED = Counter('articles_generated_total', 'Articles generated', ['type', 'platform'])
INSIGHT_SCORE = Histogram('insight_score_distribution', 'Distribution of insight scores')

# Code analysis metrics
CODE_ANALYSIS_DURATION = Histogram('code_analysis_duration_seconds', 'Code analysis processing time', ['analysis_type'])
FILES_PROCESSED = Counter('files_processed_total', 'Total files processed', ['file_type'])
MEMORY_USAGE = Histogram('memory_usage_bytes', 'Memory usage during operations', ['operation'])

# OpenAI API metrics
OPENAI_API_CALLS = Counter('openai_api_calls_total', 'OpenAI API calls', ['model', 'operation'])
OPENAI_API_FAILURES = Counter('openai_api_failures_total', 'OpenAI API failures', ['model', 'error_type'])
OPENAI_TOKEN_USAGE = Counter('openai_tokens_used_total', 'Total OpenAI tokens used', ['model', 'type'])
OPENAI_API_LATENCY = Histogram('openai_api_duration_seconds', 'OpenAI API response time', ['model'])

# Cache metrics
CACHE_REQUESTS = Counter('cache_requests_total', 'Total cache requests', ['operation'])
CACHE_HITS = Counter('cache_hits_total', 'Cache hits', ['operation'])
CACHE_MISSES = Counter('cache_misses_total', 'Cache misses', ['operation'])
CACHE_OPERATION_DURATION = Histogram('cache_operation_duration_seconds', 'Cache operation time', ['operation'])

# Database metrics
DB_CONNECTIONS = Histogram('db_connections_active', 'Active database connections')
DB_QUERY_DURATION = Histogram('db_query_duration_seconds', 'Database query duration', ['operation'])
DB_OPERATIONS = Counter('db_operations_total', 'Database operations', ['operation', 'status'])

# Publishing metrics
PUBLISHING_ATTEMPTS = Counter('publishing_attempts_total', 'Publishing attempts', ['platform'])
PUBLISHING_SUCCESS = Counter('publishing_success_total', 'Successful publications', ['platform'])
PUBLISHING_FAILURES = Counter('publishing_failures_total', 'Failed publications', ['platform', 'error_type'])
PUBLISHING_DURATION = Histogram('publishing_duration_seconds', 'Publishing operation time', ['platform'])

# Business metrics
ARTICLE_QUALITY_SCORE = Histogram('article_quality_score', 'Article quality assessment', ['article_type'])
CONTENT_LENGTH = Histogram('content_length_words', 'Article content length in words', ['article_type'])
PROCESSING_PIPELINE_DURATION = Histogram('processing_pipeline_duration_seconds', 'End-to-end processing time', ['pipeline_stage'])

app = FastAPI(
    title="Tech Documentation Generator",
    description="AI-powered codebase analysis and article generation service",
    version="1.0.0"
)

# Performance monitoring middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(HealthCheckMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(manual_publish.router, prefix="/api", tags=["manual-publishing"])

@app.get("/")
async def root():
    return {"service": "tech_doc_generator", "status": "active", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {"status": "healthy", "service": "tech_doc_generator"}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    logger.info("Tech Doc Generator starting", 
                environment=settings.environment,
                service="tech_doc_generator")
    
    # Initialize database connections
    await init_database()
    
    # Initialize cache manager
    cache_manager = get_cache_manager()
    await cache_manager.get_redis_client()
    
    logger.info("All services initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Tech Doc Generator shutting down", service="tech_doc_generator")
    
    # Close database connections
    await close_database()
    
    # Close cache connections
    cache_manager = get_cache_manager()
    await cache_manager.close()
    
    logger.info("All services shut down successfully")