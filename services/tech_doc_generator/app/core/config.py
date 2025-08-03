from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Configuration settings for the tech doc generator service"""

    # Service settings
    environment: str = "development"
    service_name: str = "tech_doc_generator"

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://user:pass@localhost:5432/threads_agent"
    )

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "test")
    openai_model: str = os.getenv("TECH_DOC_MODEL", "gpt-4o")

    # Celery/Redis
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # Platform API keys
    devto_api_key: Optional[str] = os.getenv("DEVTO_API_KEY")
    linkedin_access_token: Optional[str] = os.getenv("LINKEDIN_ACCESS_TOKEN")
    twitter_bearer_token: Optional[str] = os.getenv("TWITTER_BEARER_TOKEN")
    twitter_api_key: Optional[str] = os.getenv("TWITTER_API_KEY")
    twitter_api_secret: Optional[str] = os.getenv("TWITTER_API_SECRET")
    twitter_access_token: Optional[str] = os.getenv("TWITTER_ACCESS_TOKEN")
    twitter_access_token_secret: Optional[str] = os.getenv(
        "TWITTER_ACCESS_TOKEN_SECRET"
    )

    # Threads (Meta) settings
    threads_access_token: Optional[str] = os.getenv("THREADS_ACCESS_TOKEN")
    threads_user_id: Optional[str] = os.getenv("THREADS_USER_ID")
    threads_username: Optional[str] = os.getenv("THREADS_USERNAME")

    # Code analysis settings
    repo_path: str = os.getenv("REPO_PATH", "/app")
    analysis_depth: str = os.getenv("ANALYSIS_DEPTH", "medium")  # shallow, medium, deep

    # Content generation settings
    max_article_length: int = int(os.getenv("MAX_ARTICLE_LENGTH", "5000"))
    min_insight_score: float = float(os.getenv("MIN_INSIGHT_SCORE", "7.0"))
    supported_platforms: List[str] = [
        "devto",
        "linkedin",
        "twitter",
        "threads",
        "github",
        "medium",
    ]

    # Scheduling settings
    default_publish_delay_hours: int = int(
        os.getenv("DEFAULT_PUBLISH_DELAY_HOURS", "2")
    )
    max_daily_articles: int = int(os.getenv("MAX_DAILY_ARTICLES", "3"))

    class Config:
        env_file = ".env"


_settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
