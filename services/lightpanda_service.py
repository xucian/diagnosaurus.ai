"""
Lightpanda.io web scraping service for extracting medical content
"""
from typing import Dict, Any, Optional
import httpx
from loguru import logger


class LightpandaService:
    """Lightpanda.io headless browser scraping service"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Lightpanda service

        Args:
            api_key: Lightpanda.io API key (optional if self-hosted)
        """
        self.api_key = api_key
        self.base_url = "https://api.lightpanda.io/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        logger.info("Lightpanda service initialized")

    async def scrape_url(
        self,
        url: str,
        extract_mode: str = "markdown",
    ) -> Dict[str, Any]:
        """
        Scrape a URL using Lightpanda.io

        Args:
            url: URL to scrape
            extract_mode: Extraction mode - "markdown", "text", or "html"

        Returns:
            Dict with scraped content and metadata
        """
        try:
            payload = {
                "url": url,
                "mode": extract_mode,
                "wait_for": "networkidle",  # Wait for page to fully load
                "timeout": 15000,  # 15 second timeout
                "extract": {
                    "title": True,
                    "meta_description": True,
                    "headings": True,
                    "main_content": True,
                },
            }

            response = await self.client.post(
                f"{self.base_url}/scrape",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()

            result = {
                "url": url,
                "title": data.get("title", ""),
                "content": data.get("content", ""),
                "meta_description": data.get("meta_description", ""),
                "headings": data.get("headings", []),
                "main_content": data.get("main_content", ""),
                "success": True,
            }

            logger.info(f"Successfully scraped: {url}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Lightpanda scraping failed for {url}: {e}")
            return {
                "url": url,
                "content": "",
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"Lightpanda unexpected error for {url}: {e}")
            return {
                "url": url,
                "content": "",
                "success": False,
                "error": str(e),
            }

    async def scrape_medical_content(
        self,
        url: str,
    ) -> Dict[str, Any]:
        """
        Scrape medical content with optimized extraction

        Args:
            url: Medical page URL

        Returns:
            Extracted medical content
        """
        # Use markdown mode for better structured content extraction
        result = await self.scrape_url(url, extract_mode="markdown")

        # Additional medical-specific processing
        if result.get("success"):
            content = result.get("content", "")

            # Clean up common medical site artifacts
            content = self._clean_medical_content(content)
            result["content"] = content

        return result

    def _clean_medical_content(self, content: str) -> str:
        """
        Clean medical content from common artifacts

        Args:
            content: Raw scraped content

        Returns:
            Cleaned content
        """
        # Remove common navigation/footer text
        noise_patterns = [
            "Cookie Policy",
            "Privacy Policy",
            "Terms of Service",
            "Subscribe to our newsletter",
            "Share on Facebook",
            "Share on Twitter",
        ]

        for pattern in noise_patterns:
            content = content.replace(pattern, "")

        return content.strip()

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
