"""
Fallback research service using DuckDuckGo + Lightpanda.io/Chrome
This provides a free alternative to Parallel.ai for medical research
"""
from typing import List, Dict, Any, Optional
import asyncio
from loguru import logger
from .duckduckgo_service import DuckDuckGoService
from .lightpanda_service import LightpandaService
from .chrome_service import ChromeService


class FallbackResearchService:
    """
    Fallback medical research service
    Uses DuckDuckGo for search + Lightpanda.io/Chrome for content scraping
    """

    def __init__(
        self,
        lightpanda_api_key: Optional[str] = None,
        browser: str = "lightpanda"
    ):
        """
        Initialize fallback research service

        Args:
            lightpanda_api_key: Optional Lightpanda.io API key
            browser: Browser to use for scraping - "lightpanda" or "chrome"
        """
        self.ddg = DuckDuckGoService()
        self.browser_type = browser.lower()

        # Initialize appropriate scraper based on browser selection
        if self.browser_type == "chrome":
            self.scraper = ChromeService()
            logger.info("Fallback research service initialized (DuckDuckGo + Chrome)")
        else:
            self.scraper = LightpandaService(api_key=lightpanda_api_key)
            logger.info("Fallback research service initialized (DuckDuckGo + Lightpanda)")

    async def search_medical(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search medical information using DuckDuckGo + scraping

        Args:
            query: Search query
            sources: Ignored (kept for API compatibility with ParallelService)
            max_results: Maximum number of results

        Returns:
            List of search results with scraped content
        """
        try:
            # Step 1: Get search results from DuckDuckGo
            logger.info(f"Searching DuckDuckGo for: {query}")
            search_results = await self.ddg.search_medical(query, max_results=max_results)

            if not search_results:
                logger.warning(f"No DuckDuckGo results for: {query}")
                return []

            # Step 2: Scrape first 3 results in parallel
            urls_to_scrape = [r["url"] for r in search_results[:3] if r.get("url")]

            logger.info(f"Scraping {len(urls_to_scrape)} URLs in parallel with {self.browser_type}")
            scrape_tasks = [
                self.scraper.scrape_medical_content(url)
                for url in urls_to_scrape
            ]

            scraped_contents = await asyncio.gather(*scrape_tasks, return_exceptions=True)

            # Step 3: Merge search results with scraped content
            enriched_results = []

            for i, result in enumerate(search_results):
                enriched = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", ""),
                    "content": result.get("snippet", ""),  # Default to snippet
                    "citation": result.get("url", ""),
                }

                # If this URL was scraped, use the full content
                if i < len(scraped_contents):
                    scraped = scraped_contents[i]
                    if not isinstance(scraped, Exception) and scraped.get("success"):
                        enriched["content"] = scraped.get("content", result.get("snippet", ""))
                        enriched["title"] = scraped.get("title") or result.get("title", "")

                enriched_results.append(enriched)

            logger.info(f"Fallback search returned {len(enriched_results)} enriched results")
            return enriched_results

        except Exception as e:
            logger.error(f"Fallback medical search failed: {e}")
            return []

    async def research_condition(
        self,
        condition_name: str,
        symptom_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deep research on a medical condition using fallback sources

        Args:
            condition_name: Name of condition to research
            symptom_context: Patient symptoms for context

        Returns:
            Structured research data (compatible with ParallelService format)
        """
        try:
            query = f"{condition_name} symptoms causes treatment diagnosis"
            if symptom_context:
                query += f" {symptom_context[:100]}"

            # Search and scrape
            results = await self.search_medical(query, max_results=5)

            if not results:
                logger.warning(f"No results for condition: {condition_name}")
                return {
                    "condition": condition_name,
                    "error": "No results found",
                }

            # Structure research findings (basic extraction)
            research = {
                "condition": condition_name,
                "overview": self._extract_overview(results),
                "symptoms": self._extract_symptoms(results),
                "causes": self._extract_causes(results),
                "risk_factors": self._extract_risk_factors(results),
                "diagnosis": self._extract_diagnosis(results),
                "treatment": self._extract_treatment(results),
                "sources": [r.get("citation") for r in results if r.get("citation")],
            }

            logger.info(f"Completed fallback research on: {condition_name}")
            return research

        except Exception as e:
            logger.error(f"Fallback condition research failed: {e}")
            return {"condition": condition_name, "error": str(e)}

    def _extract_overview(self, results: List[Dict[str, Any]]) -> str:
        """Extract condition overview from search results"""
        for result in results:
            content = result.get("content", "")
            if content and len(content) > 100:
                return content[:500]
        return results[0].get("content", "")[:500] if results else ""

    def _extract_symptoms(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract symptom list from search results"""
        symptoms = []
        for result in results:
            content = result.get("content", "")
            if "symptom" in content.lower():
                # Simple extraction - split by periods
                lines = content.split(".")
                symptoms.extend([l.strip() for l in lines if "symptom" in l.lower()])
        return symptoms[:10]

    def _extract_causes(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract causes from search results"""
        causes = []
        for result in results:
            content = result.get("content", "")
            if "cause" in content.lower():
                lines = content.split(".")
                causes.extend([l.strip() for l in lines if "cause" in l.lower()])
        return causes[:5]

    def _extract_risk_factors(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract risk factors from search results"""
        factors = []
        for result in results:
            content = result.get("content", "")
            if "risk factor" in content.lower():
                lines = content.split(".")
                factors.extend([l.strip() for l in lines if "risk" in l.lower()])
        return factors[:5]

    def _extract_diagnosis(self, results: List[Dict[str, Any]]) -> str:
        """Extract diagnosis information"""
        for result in results:
            content = result.get("content", "")
            if "diagnos" in content.lower():
                # Find the sentence containing "diagnosis"
                sentences = content.split(".")
                for sentence in sentences:
                    if "diagnos" in sentence.lower():
                        return sentence.strip()[:300]
        return ""

    def _extract_treatment(self, results: List[Dict[str, Any]]) -> str:
        """Extract treatment information"""
        for result in results:
            content = result.get("content", "")
            if "treatment" in content.lower():
                # Find the sentence containing "treatment"
                sentences = content.split(".")
                for sentence in sentences:
                    if "treatment" in sentence.lower():
                        return sentence.strip()[:300]
        return ""

    async def find_clinics(
        self,
        location: Dict[str, float],
        specialty: Optional[str] = None,
        min_rating: float = 3.5,
        max_distance_km: float = 25,
    ) -> List[Any]:
        """
        Clinic search not supported in fallback mode
        Returns empty list (requires Parallel.ai integration)

        Args:
            location: {"lat": float, "lon": float}
            specialty: Medical specialty filter (ignored)
            min_rating: Minimum rating (ignored)
            max_distance_km: Maximum distance (ignored)

        Returns:
            Empty list (clinic search requires Parallel.ai)
        """
        logger.warning(
            "Clinic search not available in fallback mode. "
            "Set USE_FALLBACK_RESEARCH=false to enable clinic discovery via Parallel.ai"
        )
        return []

    async def close(self):
        """Close all HTTP clients"""
        await self.ddg.close()
        await self.scraper.close()
