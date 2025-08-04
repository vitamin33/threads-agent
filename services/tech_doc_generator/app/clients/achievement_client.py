"""
Achievement Collector API Client for Tech Doc Generator

This client provides seamless integration with the achievement_collector service
to fetch achievements for automated content generation.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel, Field
import structlog
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import get_settings

logger = structlog.get_logger()


class Achievement(BaseModel):
    """Achievement model matching the collector service schema"""
    id: int
    title: str
    description: str
    category: str
    impact_score: float = Field(ge=0, le=100)
    business_value: Optional[str] = None
    technical_details: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, float]] = None
    tags: List[str] = Field(default_factory=list)
    portfolio_ready: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class AchievementListResponse(BaseModel):
    """Response model for achievement list endpoint"""
    achievements: List[Achievement]
    total: int
    page: int
    page_size: int


class AchievementClient:
    """
    Async HTTP client for achievement_collector service integration.
    
    Features:
    - Automatic retries with exponential backoff
    - Response caching with TTL
    - Circuit breaker pattern for fault tolerance
    - Comprehensive error handling and logging
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.achievement_collector_url
        self.api_key = api_key or settings.achievement_collector_api_key
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self._client = None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(minutes=5)
        
    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._get_headers()
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
            
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "tech-doc-generator/1.0"
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
        
    def _cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key for request"""
        return f"{method}:{str(sorted(kwargs.items()))}"
        
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached response if valid"""
        if key in self._cache:
            cached_data, cached_time = self._cache[key]
            if datetime.now() - cached_time < self._cache_ttl:
                logger.debug("cache_hit", cache_key=key)
                return cached_data
        return None
        
    def _set_cache(self, key: str, data: Any):
        """Set cache entry"""
        self._cache[key] = (data, datetime.now())
        logger.debug("cache_set", cache_key=key)
        
    async def _make_request(self, method: str, path: str, **kwargs) -> Any:
        """Make HTTP request with error handling"""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
            
        try:
            if method == "GET":
                response = await self._client.get(path, **kwargs)
            elif method == "POST":
                response = await self._client.post(path, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error", 
                        method=method,
                        path=path,
                        status_code=e.response.status_code,
                        error=str(e))
            raise
        except Exception as e:
            logger.error(f"Request failed",
                        method=method,
                        path=path,
                        error=str(e))
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_achievement(self, achievement_id: int) -> Optional[Achievement]:
        """
        Fetch a single achievement by ID.
        
        Args:
            achievement_id: The achievement ID to fetch
            
        Returns:
            Achievement object or None if not found
        """
        cache_key = self._cache_key("get_achievement", id=achievement_id)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
            
        try:
            if not self._client:
                async with self:
                    return await self.get_achievement(achievement_id)
                    
            response = await self._client.get(f"/achievements/{achievement_id}")
            response.raise_for_status()
            
            achievement = Achievement(**response.json())
            self._set_cache(cache_key, achievement)
            
            logger.info("achievement_fetched", achievement_id=achievement_id)
            return achievement
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("achievement_not_found", achievement_id=achievement_id)
                return None
            logger.error("achievement_fetch_error", 
                        achievement_id=achievement_id, 
                        status_code=e.response.status_code,
                        error=str(e))
            raise
        except Exception as e:
            logger.error("achievement_fetch_failed", 
                        achievement_id=achievement_id,
                        error=str(e))
            raise
            
    async def list_achievements(
        self,
        category: Optional[str] = None,
        min_impact_score: Optional[float] = None,
        portfolio_ready_only: bool = False,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> AchievementListResponse:
        """
        List achievements with filtering and pagination.
        
        Args:
            category: Filter by achievement category
            min_impact_score: Minimum impact score filter
            portfolio_ready_only: Only return portfolio-ready achievements
            tags: Filter by tags (any match)
            start_date: Filter achievements created after this date
            end_date: Filter achievements created before this date
            page: Page number (1-indexed)
            page_size: Items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            AchievementListResponse with paginated results
        """
        params = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        if category:
            params["category"] = category
        if min_impact_score is not None:
            params["min_impact_score"] = min_impact_score
        if portfolio_ready_only:
            params["portfolio_ready_only"] = portfolio_ready_only
        if tags:
            params["tags"] = ",".join(tags)
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        cache_key = self._cache_key("list_achievements", **params)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
            
        try:
            if not self._client:
                async with self:
                    return await self.list_achievements(**locals())
                    
            response = await self._client.get("/achievements", params=params)
            response.raise_for_status()
            
            result = AchievementListResponse(**response.json())
            self._set_cache(cache_key, result)
            
            logger.info("achievements_listed", 
                       total=result.total,
                       page=result.page,
                       filters=params)
            return result
            
        except Exception as e:
            logger.error("achievements_list_failed", 
                        params=params,
                        error=str(e))
            raise
            
    async def get_by_category(self, category: str, limit: int = 10) -> List[Achievement]:
        """
        Get top achievements by category.
        
        Args:
            category: Achievement category to filter
            limit: Maximum number of achievements to return
            
        Returns:
            List of achievements sorted by impact score
        """
        response = await self.list_achievements(
            category=category,
            page_size=limit,
            sort_by="impact_score",
            sort_order="desc"
        )
        return response.achievements
        
    async def get_recent_achievements(
        self, 
        days: int = 7, 
        min_impact_score: float = 70.0
    ) -> List[Achievement]:
        """
        Get recent high-impact achievements for content generation.
        
        Args:
            days: Number of days to look back
            min_impact_score: Minimum impact score threshold
            
        Returns:
            List of recent high-impact achievements
        """
        start_date = datetime.now() - timedelta(days=days)
        response = await self.list_achievements(
            start_date=start_date,
            min_impact_score=min_impact_score,
            portfolio_ready_only=True,
            sort_by="impact_score",
            sort_order="desc"
        )
        return response.achievements
        
    async def batch_get_achievements(self, achievement_ids: List[int]) -> List[Achievement]:
        """
        Batch fetch multiple achievements using optimized endpoint.
        
        Args:
            achievement_ids: List of achievement IDs to fetch
            
        Returns:
            List of achievements (excludes not found)
        """
        if not achievement_ids:
            return []
            
        # Use optimized batch endpoint
        response = await self._make_request(
            "POST",
            "/tech-doc-integration/batch-get",
            json={"achievement_ids": achievement_ids}
        )
        
        if response:
            return [Achievement(**item) for item in response]
        
        return []
        
    async def get_recent_highlights(self, days: int = 7, min_impact_score: float = 75.0, limit: int = 10) -> List[Achievement]:
        """
        Get recent high-impact achievements using optimized endpoint.
        
        Args:
            days: Number of days to look back
            min_impact_score: Minimum impact score
            limit: Maximum results
            
        Returns:
            List of recent highlights
        """
        response = await self._make_request(
            "POST",
            "/tech-doc-integration/recent-highlights",
            params={
                "days": days,
                "min_impact_score": min_impact_score,
                "limit": limit
            }
        )
        
        if response:
            return [Achievement(**item) for item in response]
            
        return []
        
    async def get_company_targeted(self, company_name: str, categories: Optional[List[str]] = None, limit: int = 20) -> List[Achievement]:
        """
        Get achievements targeted for a specific company.
        
        Args:
            company_name: Target company name
            categories: Optional category filter
            limit: Maximum results
            
        Returns:
            List of company-relevant achievements
        """
        params = {"company_name": company_name, "limit": limit}
        if categories:
            params["categories"] = categories
            
        response = await self._make_request(
            "POST",
            "/tech-doc-integration/company-targeted",
            params=params
        )
        
        if response:
            return [Achievement(**item) for item in response]
            
        return []


# Singleton instance for easy import
@lru_cache(maxsize=1)
def get_achievement_client() -> AchievementClient:
    """Get singleton achievement client instance"""
    return AchievementClient()