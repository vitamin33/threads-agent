from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, Text, Boolean
from datetime import datetime
from typing import Optional, AsyncGenerator
import structlog

from .config import get_settings

logger = structlog.get_logger()

Base = declarative_base()

class Article(Base):
    """Database model for articles"""
    __tablename__ = "articles"
    
    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    analysis_data = Column(JSON, nullable=True)
    insight_score = Column(Float, nullable=True)
    status = Column(String(50), default="draft")
    article_type = Column(String(50), nullable=False)
    target_platforms = Column(JSON, nullable=False)
    published_urls = Column(JSON, default=dict)
    performance_metrics = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexing for performance
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

class DatabaseManager:
    """Optimized database connection manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Initialize database connection with optimized settings"""
        if self.engine is None:
            # Convert PostgreSQL URL to async version
            database_url = self.settings.database_url
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            
            # Create engine with connection pooling optimization
            self.engine = create_async_engine(
                database_url,
                # Connection pool settings for high performance
                poolclass=QueuePool,
                pool_size=20,              # Number of connections to maintain
                max_overflow=30,           # Additional connections when pool is full
                pool_pre_ping=True,        # Verify connections before use
                pool_recycle=3600,         # Recycle connections every hour
                
                # Query optimization settings
                echo=False,                # Disable SQL logging in production
                future=True,               # Use SQLAlchemy 2.0 style
                
                # Connection timeout settings
                connect_args={
                    "command_timeout": 30,
                    "server_settings": {
                        "application_name": "tech_doc_generator",
                        "jit": "off",              # Disable JIT for faster simple queries
                        "statement_timeout": "30s", # Prevent long-running queries
                    }
                }
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("Database initialized with connection pooling")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with proper cleanup"""
        if not self.session_factory:
            await self.initialize()
            
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error("Database session error", error=str(e))
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

# Global database manager
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get or create database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

# Database operations with optimized queries
class ArticleRepository:
    """Repository for optimized article database operations"""
    
    def __init__(self):
        self.db = get_database_manager()
    
    async def create_article(self, article_data: dict) -> Article:
        """Create new article with optimized insert"""
        async with self.db.get_session() as session:
            article = Article(**article_data)
            session.add(article)
            await session.commit()
            await session.refresh(article)
            return article
    
    async def get_article_by_id(self, article_id: str) -> Optional[Article]:
        """Get article by ID with optimized query"""
        async with self.db.get_session() as session:
            from sqlalchemy import select
            
            stmt = select(Article).where(Article.id == article_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def update_article_status(self, article_id: str, status: str) -> bool:
        """Update article status with minimal query"""
        async with self.db.get_session() as session:
            from sqlalchemy import update
            
            stmt = update(Article).where(Article.id == article_id).values(
                status=status,
                updated_at=datetime.utcnow()
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    
    async def get_recent_articles(self, limit: int = 10) -> list[Article]:
        """Get recent articles with pagination"""
        async with self.db.get_session() as session:
            from sqlalchemy import select, desc
            
            stmt = (
                select(Article)
                .order_by(desc(Article.created_at))
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_articles_by_status(self, status: str, limit: int = 50) -> list[Article]:
        """Get articles by status with optimized query"""
        async with self.db.get_session() as session:
            from sqlalchemy import select
            
            stmt = (
                select(Article)
                .where(Article.status == status)
                .order_by(Article.created_at)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def update_performance_metrics(
        self, 
        article_id: str, 
        metrics: dict
    ) -> bool:
        """Update performance metrics efficiently"""
        async with self.db.get_session() as session:
            from sqlalchemy import update
            
            stmt = update(Article).where(Article.id == article_id).values(
                performance_metrics=metrics,
                updated_at=datetime.utcnow()
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    
    async def get_article_statistics(self) -> dict:
        """Get article statistics with aggregated queries"""
        async with self.db.get_session() as session:
            from sqlalchemy import select, func
            
            # Count by status
            status_stmt = (
                select(Article.status, func.count(Article.id))
                .group_by(Article.status)
            )
            status_result = await session.execute(status_stmt)
            status_counts = dict(status_result.all())
            
            # Average insight score
            avg_score_stmt = select(func.avg(Article.insight_score))
            avg_result = await session.execute(avg_score_stmt)
            avg_score = avg_result.scalar() or 0.0
            
            # Total articles
            total_stmt = select(func.count(Article.id))
            total_result = await session.execute(total_stmt)
            total_count = total_result.scalar() or 0
            
            return {
                "total_articles": total_count,
                "status_counts": status_counts,
                "average_insight_score": round(avg_score, 2)
            }

# Initialize database on startup
async def init_database():
    """Initialize database connection on startup"""
    db_manager = get_database_manager()
    await db_manager.initialize()
    logger.info("Database initialization completed")

# Cleanup on shutdown
async def close_database():
    """Close database connections on shutdown"""
    db_manager = get_database_manager()
    await db_manager.close()
    logger.info("Database cleanup completed")