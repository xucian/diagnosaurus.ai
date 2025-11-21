"""
DuckDuckGo search service for fallback medical research
"""
from typing import List, Dict, Any, Optional
import asyncio
import time
from duckduckgo_search import DDGS
from loguru import logger


class DuckDuckGoService:
    """DuckDuckGo search service using duckduckgo-search library"""

    def __init__(self):
        """Initialize DuckDuckGo service"""
        logger.info("DuckDuckGo service initialized")
        self._last_request_time = 0
        self._min_request_interval = 2.0  # Minimum seconds between requests

    async def _rate_limit_delay(self):
        """Ensure minimum time between requests"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            delay = self._min_request_interval - time_since_last
            await asyncio.sleep(delay)
        self._last_request_time = time.time()

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo web search (fail fast on errors)

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, url, and snippet (empty list on error)
        """
        try:
            # Rate limit our requests
            await self._rate_limit_delay()

            # Use text search with asyncio (run sync method in thread pool)
            # Create new DDGS instance per request to avoid state issues
            results_raw = await asyncio.to_thread(
                lambda: list(DDGS().text(query, max_results=max_results))
            )

            # Convert to our format
            results = []
            for item in results_raw:
                result = {
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                }
                results.append(result)

            logger.info(f"DuckDuckGo found {len(results)} results for: {query}")
            return results

        except Exception as e:
            # Fail gracefully without blocking - just log and return empty
            error_str = str(e)
            if "Ratelimit" in error_str or "403" in error_str or "202" in error_str:
                logger.warning(f"DuckDuckGo rate limited - skipping search")
            else:
                logger.warning(f"DuckDuckGo search failed: {e}")
            return []

    async def search_medical(
        self,
        query: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Medical-specific search with enhanced query

        Args:
            query: Medical search query
            max_results: Maximum results

        Returns:
            List of search results
        """
        # Add medical context but skip site restrictions to avoid rate limiting
        # DuckDuckGo will naturally prioritize authoritative medical sources
        medical_query = f"{query} medical symptoms causes treatment"
        return await self.search(medical_query, max_results)

    async def close(self):
        """Close async client"""
        pass  # AsyncDDGS handles cleanup automatically
