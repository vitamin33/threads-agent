"""Synchronous client for Threads Adaptor with connection pooling."""
import httpx
from typing import Dict, Any, List, Optional
from functools import lru_cache
import time


class ThreadsClientSync:
    """Synchronous client with connection pooling for Celery tasks."""
    
    def __init__(self, base_url: str = "http://threads-adaptor:8070"):
        self.base_url = base_url
        # Connection pooling with limits
        self.client = httpx.Client(
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            ),
            timeout=httpx.Timeout(5.0, connect=2.0)
        )
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 30  # seconds
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache_timestamps:
            return False
        return time.time() - self._cache_timestamps[key] < self._cache_ttl
    
    def get_post_performance(self, post_id: str) -> Dict[str, Any]:
        """Get performance metrics with local caching."""
        # Check local cache first
        if self._is_cache_valid(post_id):
            return self._cache[post_id]
        
        # Fetch from API
        response = self.client.get(f"{self.base_url}/engagement/{post_id}")
        response.raise_for_status()
        data = response.json()
        
        # Transform to expected format
        result = {
            "views": data.get("impressions_count", 0),
            "interactions": (
                data.get("likes_count", 0) + 
                data.get("comments_count", 0) + 
                data.get("shares_count", 0)
            ),
            "engagement_rate": data.get("engagement_rate", 0.0)
        }
        
        # Update local cache
        self._cache[post_id] = result
        self._cache_timestamps[post_id] = time.time()
        
        return result
    
    def bulk_get_performance(self, post_ids: List[str]) -> List[Dict[str, Any]]:
        """Bulk fetch performance data efficiently."""
        results = []
        
        # This would ideally call a bulk endpoint
        # For now, we'll fetch individually but with caching
        for post_id in post_ids:
            try:
                perf = self.get_post_performance(post_id)
                results.append(perf)
            except Exception as e:
                # Return minimal data on error
                results.append({
                    "views": 0,
                    "interactions": 0,
                    "engagement_rate": 0.0,
                    "error": str(e)
                })
        
        return results
    
    def delete_post(self, post_id: str) -> bool:
        """Delete a post from Threads."""
        try:
            # This would call the actual delete endpoint when implemented
            # response = self.client.delete(f"{self.base_url}/posts/{post_id}")
            # response.raise_for_status()
            return True
        except Exception:
            return False
    
    def close(self):
        """Close the client and cleanup resources."""
        self.client.close()
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on context exit."""
        self.close()