"""
SearXNG Search Wrapper for Threads-Agent
Provides intelligent search capabilities for trend detection and competitive analysis
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import requests

logger = logging.getLogger(__name__)

# Default SearXNG instance URL
SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://localhost:8888")
SEARCH_TIMEOUT = int(os.environ.get("SEARCH_TIMEOUT", "10"))

# Search result caching
_search_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = timedelta(hours=1)  # Cache search results for 1 hour


class SearchResult:
    """Structured search result"""

    def __init__(
        self, title: str, url: str, content: str, engine: str, score: float = 0.0
    ):
        self.title = title
        self.url = url
        self.content = content
        self.engine = engine
        self.score = score
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "engine": self.engine,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
        }


class SearXNGWrapper:
    """Wrapper for SearXNG search operations"""

    def __init__(self, base_url: str = SEARXNG_URL):
        self.base_url = base_url.rstrip("/")
        self.search_endpoint = f"{self.base_url}/search"

    def _cache_key(self, query: str, **params) -> str:
        """Generate cache key for search query"""
        key_data = f"{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached data is still valid"""
        if "timestamp" not in cached_data:
            return False
        cached_time = datetime.fromisoformat(cached_data["timestamp"])
        return datetime.utcnow() - cached_time < CACHE_TTL

    def search(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        engines: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Perform synchronous search

        Args:
            query: Search query
            categories: List of categories (general, images, videos, news)
            engines: Specific engines to use (duckduckgo, google, qwant, etc)
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        # Check cache first
        cache_key = self._cache_key(
            query, categories=categories, engines=engines, limit=limit
        )
        if cache_key in _search_cache and self._is_cache_valid(
            _search_cache[cache_key]
        ):
            logger.info(f"Cache hit for query: {query}")
            return self._parse_results(_search_cache[cache_key]["results"])

        params = {"q": query, "format": "json", "safesearch": "0", "language": "en"}

        if categories:
            params["categories"] = ",".join(categories)

        if engines:
            params["engines"] = ",".join(engines)

        try:
            response = requests.get(
                self.search_endpoint, params=params, timeout=SEARCH_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            results = self._parse_results(data.get("results", [])[:limit])

            # Cache results
            _search_cache[cache_key] = {
                "results": data.get("results", [])[:limit],
                "timestamp": datetime.utcnow().isoformat(),
            }

            return results

        except Exception as e:
            logger.error(f"Search error for query '{query}': {str(e)}")
            return []

    async def search_async(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        engines: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """Asynchronous version of search"""
        # Check cache first
        cache_key = self._cache_key(
            query, categories=categories, engines=engines, limit=limit
        )
        if cache_key in _search_cache and self._is_cache_valid(
            _search_cache[cache_key]
        ):
            logger.info(f"Cache hit for query: {query}")
            return self._parse_results(_search_cache[cache_key]["results"])

        params = {"q": query, "format": "json", "safesearch": "0", "language": "en"}

        if categories:
            params["categories"] = ",".join(categories)

        if engines:
            params["engines"] = ",".join(engines)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.search_endpoint,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=SEARCH_TIMEOUT),
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    results = self._parse_results(data.get("results", [])[:limit])

                    # Cache results
                    _search_cache[cache_key] = {
                        "results": data.get("results", [])[:limit],
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    return results

        except Exception as e:
            logger.error(f"Async search error for query '{query}': {str(e)}")
            return []

    def _parse_results(self, raw_results: List[Dict[str, Any]]) -> List[SearchResult]:
        """Parse raw search results into SearchResult objects"""
        results = []
        for item in raw_results:
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                engine=item.get("engine", "unknown"),
                score=item.get("score", 0.0),
            )
            results.append(result)
        return results


class TrendDetector:
    """Detect trends using search data"""

    def __init__(self, searxng: SearXNGWrapper):
        self.searxng = searxng

    def find_trending_topics(
        self, base_query: str, timeframe: str = "week"
    ) -> List[Dict[str, Any]]:
        """
        Find trending topics related to base query

        Args:
            base_query: Base topic to find trends for (e.g., "AI", "threads")
            timeframe: Time period (day, week, month)

        Returns:
            List of trending topics with scores
        """
        # Search modifiers for trend detection
        trend_modifiers = [
            "trending",
            "viral",
            "popular",
            "hot",
            "2025",  # Current year
            f"this {timeframe}",
        ]

        all_results = []
        for modifier in trend_modifiers:
            query = f"{base_query} {modifier}"
            results = self.searxng.search(
                query, categories=["general", "news"], limit=20
            )
            all_results.extend(results)

        # Analyze and score trends
        trend_scores = {}
        for result in all_results:
            # Extract potential trend keywords from titles
            words = result.title.lower().split()
            for word in words:
                if len(word) > 3 and word not in base_query.lower():
                    trend_scores[word] = trend_scores.get(word, 0) + 1

        # Sort by frequency
        trends = [
            {"topic": topic, "score": score}
            for topic, score in sorted(
                trend_scores.items(), key=lambda x: x[1], reverse=True
            )
        ][:10]

        return trends


class CompetitiveAnalyzer:
    """Analyze competitor content and strategies"""

    def __init__(self, searxng: SearXNGWrapper):
        self.searxng = searxng

    def analyze_viral_content(
        self, topic: str, platform: str = "threads"
    ) -> List[Dict[str, Any]]:
        """
        Find and analyze viral content patterns

        Args:
            topic: Topic to analyze
            platform: Social platform to focus on

        Returns:
            List of viral content patterns
        """
        # Search for viral content
        viral_queries = [
            f"{topic} viral {platform}",
            f"{topic} high engagement",
            f"{topic} trending posts",
            f"best {topic} content {platform}",
        ]

        patterns = []
        for query in viral_queries:
            results = self.searxng.search(query, limit=15)

            for result in results:
                # Extract patterns from successful content
                pattern = {
                    "title": result.title,
                    "url": result.url,
                    "summary": result.content[:200],
                    "source": result.engine,
                    "keywords": self._extract_keywords(result.content),
                }
                patterns.append(pattern)

        return patterns

    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Simple keyword extraction"""
        # Remove common words
        stopwords = {
            "the",
            "is",
            "at",
            "which",
            "on",
            "and",
            "a",
            "an",
            "to",
            "in",
            "for",
            "of",
            "with",
        }
        words = text.lower().split()
        word_freq = {}

        for word in words:
            if len(word) > 3 and word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Return top keywords
        return [
            word
            for word, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[
                :top_n
            ]
        ]


# Global instances for easy access
_searxng = SearXNGWrapper()
_trend_detector = TrendDetector(_searxng)
_competitive_analyzer = CompetitiveAnalyzer(_searxng)


# Convenience functions
def search(query: str, **kwargs) -> List[SearchResult]:
    """Quick search function"""
    return _searxng.search(query, **kwargs)


def find_trends(topic: str, timeframe: str = "week") -> List[Dict[str, Any]]:
    """Find trending topics"""
    return _trend_detector.find_trending_topics(topic, timeframe)


def analyze_viral(topic: str, platform: str = "threads") -> List[Dict[str, Any]]:
    """Analyze viral content patterns"""
    return _competitive_analyzer.analyze_viral_content(topic, platform)


# Async versions
async def search_async(query: str, **kwargs) -> List[SearchResult]:
    """Async quick search"""
    return await _searxng.search_async(query, **kwargs)


if __name__ == "__main__":
    # Example usage
    results = search("AI trends 2025")
    for r in results[:3]:
        print(f"Title: {r.title}")
        print(f"URL: {r.url}")
        print(f"Content: {r.content[:100]}...")
        print("---")
