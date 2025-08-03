import redis.asyncio as redis
import json
import hashlib
from typing import Optional, Any, Dict, List
import structlog
from datetime import timedelta

from .config import get_settings

logger = structlog.get_logger()

class CacheManager:
    """Redis-based caching for expensive operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = None
        
        # Cache TTL settings (in seconds)
        self.cache_ttl = {
            "code_analysis": 3600 * 24,      # 24 hours
            "openai_response": 3600 * 24 * 7, # 7 days  
            "complexity_score": 3600 * 12,   # 12 hours
            "function_analysis": 3600 * 6,   # 6 hours
            "pattern_detection": 3600 * 24,  # 24 hours
            "article_content": 3600 * 24 * 3 # 3 days
        }
    
    async def get_redis_client(self):
        """Get or create Redis client with connection pooling"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    self.settings.celery_broker_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20,  # Connection pool
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error("Failed to connect to Redis", error=str(e))
                self.redis_client = None
        return self.redis_client
    
    def _generate_cache_key(self, operation: str, **kwargs) -> str:
        """Generate consistent cache key for operation with parameters"""
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_data = f"{operation}:{sorted_kwargs}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"tech_doc:{operation}:{key_hash}"
    
    async def get_cached_result(self, operation: str, **kwargs) -> Optional[Any]:
        """Get cached result for operation"""
        client = await self.get_redis_client()
        if not client:
            return None
            
        try:
            cache_key = self._generate_cache_key(operation, **kwargs)
            cached_data = await client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                logger.debug("Cache hit", operation=operation, key=cache_key[:20])
                return result
            
            logger.debug("Cache miss", operation=operation, key=cache_key[:20])
            return None
        except Exception as e:
            logger.warning("Cache get error", operation=operation, error=str(e))
            return None
    
    async def cache_result(self, operation: str, result: Any, **kwargs) -> bool:
        """Cache result for operation"""
        client = await self.get_redis_client()
        if not client:
            return False
            
        try:
            cache_key = self._generate_cache_key(operation, **kwargs)
            ttl = self.cache_ttl.get(operation, 3600)  # Default 1 hour
            
            # Serialize result
            cached_data = json.dumps(result, default=str)
            
            # Store with TTL
            await client.setex(cache_key, ttl, cached_data)
            
            logger.debug("Cached result", operation=operation, key=cache_key[:20], ttl=ttl)
            return True
        except Exception as e:
            logger.warning("Cache set error", operation=operation, error=str(e))
            return False
    
    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        client = await self.get_redis_client()
        if not client:
            return 0
            
        try:
            keys = await client.keys(f"tech_doc:{pattern}:*")
            if keys:
                deleted = await client.delete(*keys)
                logger.info("Cache invalidated", pattern=pattern, deleted=deleted)
                return deleted
            return 0
        except Exception as e:
            logger.warning("Cache invalidation error", pattern=pattern, error=str(e))
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        client = await self.get_redis_client()
        if not client:
            return {"error": "Redis not available"}
            
        try:
            info = await client.info("memory")
            stats = {
                "used_memory": info.get("used_memory_human", "0"),
                "used_memory_peak": info.get("used_memory_peak_human", "0"),
                "connected_clients": info.get("connected_clients", 0),
                "cache_hit_rate": "tracking_not_implemented"  # Would need custom tracking
            }
            
            # Get key counts by prefix
            key_patterns = ["code_analysis", "openai_response", "complexity_score"]
            for pattern in key_patterns:
                keys = await client.keys(f"tech_doc:{pattern}:*")
                stats[f"{pattern}_keys"] = len(keys)
            
            return stats
        except Exception as e:
            logger.warning("Cache stats error", error=str(e))
            return {"error": str(e)}
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get or create cache manager singleton"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

# Decorator for automatic caching
def cached_operation(operation: str, ttl_override: Optional[int] = None):
    """Decorator to automatically cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key from function args
            cache_kwargs = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            
            # Try to get cached result
            cached_result = await cache.get_cached_result(operation, **cache_kwargs)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            # Cache the result
            if ttl_override:
                original_ttl = cache.cache_ttl.get(operation, 3600)
                cache.cache_ttl[operation] = ttl_override
                await cache.cache_result(operation, result, **cache_kwargs)
                cache.cache_ttl[operation] = original_ttl
            else:
                await cache.cache_result(operation, result, **cache_kwargs)
            
            return result
        return wrapper
    return decorator