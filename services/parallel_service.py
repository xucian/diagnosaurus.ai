"""
Parallel.ai MCP integration for medical research and clinic discovery
"""
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger
from config import settings
from models.schemas import ClinicResult


class ParallelService:
    """Parallel.ai research and search service"""

    def __init__(self):
        """Initialize Parallel.ai MCP client"""
        self.api_key = settings.parallel_ai_api_key
        self.base_url = "https://api.parallel.ai/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        logger.info("Parallel.ai service initialized")

    async def search_medical(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search medical information using Parallel.ai

        Args:
            query: Search query (e.g., "symptoms of iron deficiency anemia")
            sources: Specific sources to search (e.g., ["pubmed", "mayo_clinic"])
            max_results: Maximum number of results

        Returns:
            List of search results with content and citations
        """
        try:
            payload = {
                "query": query,
                "sources": sources or ["medical", "pubmed", "nih", "mayo_clinic"],
                "max_results": max_results,
                "include_citations": True,
            }

            response = await self.client.post(
                f"{self.base_url}/search/medical",
                json=payload,
            )
            response.raise_for_status()

            results = response.json().get("results", [])
            logger.info(f"Found {len(results)} medical search results for: {query}")
            return results

        except httpx.HTTPError as e:
            logger.error(f"Parallel.ai medical search failed: {e}")
            return []

    async def find_clinics(
        self,
        location: Dict[str, float],
        specialty: Optional[str] = None,
        min_rating: float = 3.5,
        max_distance_km: float = 25,
    ) -> List[ClinicResult]:
        """
        Find nearby clinics using Parallel.ai

        Args:
            location: {"lat": float, "lon": float}
            specialty: Medical specialty filter
            min_rating: Minimum Google rating
            max_distance_km: Maximum distance in kilometers

        Returns:
            List of ClinicResult objects
        """
        try:
            payload = {
                "location": location,
                "query": f"{specialty or 'medical'} clinic",
                "radius_km": max_distance_km,
                "min_rating": min_rating,
                "limit": settings.max_clinics,
                "include_reviews": True,
            }

            response = await self.client.post(
                f"{self.base_url}/search/places",
                json=payload,
            )
            response.raise_for_status()

            places = response.json().get("places", [])
            clinics = []

            for place in places:
                try:
                    clinic = ClinicResult(
                        name=place.get("name"),
                        doctor_name=self._extract_doctor_name(place),
                        specialty=specialty or "General Medicine",
                        rating=place.get("rating", 0.0),
                        review_count=place.get("review_count", 0),
                        phone=place.get("phone", "N/A"),
                        address=place.get("address", ""),
                        distance_km=place.get("distance_km", 0.0),
                        accepts_new_patients=place.get("accepts_new_patients", True),
                        website=place.get("website"),
                        next_available=place.get("next_available"),
                    )
                    clinics.append(clinic)
                except Exception as e:
                    logger.warning(f"Failed to parse clinic data: {e}")
                    continue

            logger.info(f"Found {len(clinics)} clinics near location")
            return clinics[:settings.max_clinics]

        except httpx.HTTPError as e:
            logger.error(f"Parallel.ai clinic search failed: {e}")
            return []

    async def research_condition(
        self,
        condition_name: str,
        symptom_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deep research on a specific medical condition

        Args:
            condition_name: Name of condition to research
            symptom_context: Patient symptoms for context

        Returns:
            Structured research data
        """
        try:
            query = f"{condition_name}"
            if symptom_context:
                query += f" symptoms: {symptom_context[:200]}"

            # Search medical literature
            results = await self.search_medical(
                query=query,
                sources=["pubmed", "nih", "medical_textbooks"],
                max_results=5,
            )

            # Structure research findings
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

            logger.info(f"Completed research on condition: {condition_name}")
            return research

        except Exception as e:
            logger.error(f"Condition research failed: {e}")
            return {"condition": condition_name, "error": str(e)}

    def _extract_doctor_name(self, place: Dict[str, Any]) -> str:
        """Extract doctor name from place data"""
        # Try various fields where doctor name might be stored
        return (
            place.get("doctor_name") or
            place.get("provider_name") or
            place.get("name", "").split("-")[0].strip() or
            "Dr. Smith"  # Fallback
        )

    def _extract_overview(self, results: List[Dict[str, Any]]) -> str:
        """Extract condition overview from search results"""
        for result in results:
            if "overview" in result.get("content", "").lower():
                return result.get("content", "")[:500]
        return results[0].get("content", "")[:500] if results else ""

    def _extract_symptoms(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract symptom list from search results"""
        symptoms = []
        for result in results:
            content = result.get("content", "")
            if "symptom" in content.lower():
                # Simple extraction - could be enhanced with NLP
                lines = content.split(".")
                symptoms.extend([l.strip() for l in lines if "symptom" in l.lower()])
        return symptoms[:10]  # Top 10 symptoms

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
                return content[:300]
        return ""

    def _extract_treatment(self, results: List[Dict[str, Any]]) -> str:
        """Extract treatment information"""
        for result in results:
            content = result.get("content", "")
            if "treatment" in content.lower():
                return content[:300]
        return ""

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
parallel_service = ParallelService()


def get_research_service():
    """
    Factory function to get the appropriate research service based on configuration

    Returns:
        ParallelService or FallbackResearchService based on USE_FALLBACK_RESEARCH setting
    """
    if settings.use_fallback_research:
        from .fallback_research_service import FallbackResearchService
        browser = settings.fallback_browser
        logger.info(f"Using fallback research service (DuckDuckGo + {browser.capitalize()})")
        return FallbackResearchService(
            lightpanda_api_key=settings.lightpanda_api_key,
            browser=browser
        )
    else:
        logger.info("Using Parallel.ai research service")
        return parallel_service
