"""
DuckDuckGo search service for fallback medical research
"""
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger


class DuckDuckGoService:
    """DuckDuckGo search service using their instant answer API"""

    def __init__(self):
        """Initialize DuckDuckGo service"""
        self.base_url = "https://api.duckduckgo.com/"
        self.client = httpx.AsyncClient(timeout=10.0)
        logger.info("DuckDuckGo service initialized")

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo instant answer API

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, url, and snippet
        """
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            }

            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()
            results = []

            # Extract related topics (most useful for medical queries)
            related_topics = data.get("RelatedTopics", [])

            for item in related_topics[:max_results]:
                # Skip topic headers
                if "Topics" in item:
                    continue

                if "FirstURL" in item and "Text" in item:
                    result = {
                        "title": item.get("Text", "").split(" - ")[0],
                        "url": item.get("FirstURL", ""),
                        "snippet": item.get("Text", ""),
                    }
                    results.append(result)

            # If we didn't get enough from related topics, try abstract
            if len(results) < 3 and data.get("AbstractURL"):
                results.insert(0, {
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("Abstract", ""),
                })

            logger.info(f"DuckDuckGo found {len(results)} results for: {query}")
            return results

        except httpx.HTTPError as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
        except Exception as e:
            logger.error(f"DuckDuckGo unexpected error: {e}")
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
        # Enhance query for medical results
        medical_query = f"{query} site:mayoclinic.org OR site:nih.gov OR site:medlineplus.gov"
        return await self.search(medical_query, max_results)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
