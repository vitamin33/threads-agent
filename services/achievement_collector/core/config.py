# Application Configuration

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Achievement Collector"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = (
        "postgresql://postgres:pass@localhost:5432/achievement_collector"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # GitHub Integration
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_TOKEN: str = ""

    # OpenAI (for analysis)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Portfolio Generation
    PORTFOLIO_OUTPUT_DIR: str = "/tmp/portfolios"

    # Monitoring
    PROMETHEUS_PORT: int = 9090

    # Background Tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()
