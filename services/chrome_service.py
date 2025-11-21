"""
Chrome browser scraping service using Playwright
Provides better website compatibility than headless solutions
"""
from typing import Dict, Any, Optional
from loguru import logger

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install chrome")


class ChromeService:
    """Chrome browser scraping service using Playwright"""

    def __init__(self):
        """Initialize Chrome service"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for Chrome scraping. "
                "Install with: pip install playwright && playwright install chrome"
            )

        self.browser: Optional[Browser] = None
        self.playwright = None
        logger.info("Chrome scraping service initialized")

    async def _ensure_browser(self):
        """Ensure browser is launched"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                ]
            )
            logger.info("Chrome browser launched")

    async def scrape_url(
        self,
        url: str,
        extract_mode: str = "markdown",
        wait_for: str = "networkidle",
        timeout: int = 15000,
    ) -> Dict[str, Any]:
        """
        Scrape a URL using Chrome browser

        Args:
            url: URL to scrape
            extract_mode: Extraction mode - "markdown", "text", or "html"
            wait_for: Wait condition - "networkidle", "load", or "domcontentloaded"
            timeout: Timeout in milliseconds

        Returns:
            Dict with scraped content and metadata
        """
        try:
            await self._ensure_browser()

            page: Page = await self.browser.new_page()

            try:
                # Navigate to URL
                await page.goto(url, wait_until=wait_for, timeout=timeout)

                # Extract metadata
                title = await page.title()

                # Extract main content based on mode
                if extract_mode == "html":
                    content = await page.content()
                elif extract_mode == "text":
                    content = await page.inner_text("body")
                else:  # markdown mode - extract structured content
                    content = await self._extract_markdown(page)

                # Extract meta description
                meta_desc = await page.evaluate(
                    "() => document.querySelector('meta[name=\"description\"]')?.content || ''"
                )

                # Extract headings
                headings = await page.evaluate("""
                    () => {
                        const headings = [];
                        document.querySelectorAll('h1, h2, h3').forEach(h => {
                            headings.push(h.innerText);
                        });
                        return headings;
                    }
                """)

                result = {
                    "url": url,
                    "title": title,
                    "content": content,
                    "meta_description": meta_desc,
                    "headings": headings[:10],  # Limit to top 10
                    "success": True,
                }

                logger.info(f"Successfully scraped with Chrome: {url}")
                return result

            finally:
                await page.close()

        except Exception as e:
            logger.error(f"Chrome scraping failed for {url}: {e}")
            return {
                "url": url,
                "content": "",
                "success": False,
                "error": str(e),
            }

    async def _extract_markdown(self, page: Page) -> str:
        """
        Extract content in markdown-like format

        Args:
            page: Playwright page object

        Returns:
            Markdown-formatted content
        """
        try:
            # Extract main content areas (article, main, or body)
            content = await page.evaluate("""
                () => {
                    // Try to find main content area
                    const mainContent =
                        document.querySelector('article') ||
                        document.querySelector('main') ||
                        document.querySelector('[role="main"]') ||
                        document.querySelector('.content') ||
                        document.querySelector('.article') ||
                        document.body;

                    if (!mainContent) return '';

                    let markdown = '';

                    // Extract headings and paragraphs
                    const elements = mainContent.querySelectorAll('h1, h2, h3, h4, p, ul, ol');

                    elements.forEach(el => {
                        const tag = el.tagName.toLowerCase();
                        const text = el.innerText.trim();

                        if (!text) return;

                        if (tag === 'h1') {
                            markdown += '# ' + text + '\\n\\n';
                        } else if (tag === 'h2') {
                            markdown += '## ' + text + '\\n\\n';
                        } else if (tag === 'h3') {
                            markdown += '### ' + text + '\\n\\n';
                        } else if (tag === 'h4') {
                            markdown += '#### ' + text + '\\n\\n';
                        } else if (tag === 'p') {
                            markdown += text + '\\n\\n';
                        } else if (tag === 'ul' || tag === 'ol') {
                            const items = el.querySelectorAll('li');
                            items.forEach(li => {
                                markdown += '- ' + li.innerText.trim() + '\\n';
                            });
                            markdown += '\\n';
                        }
                    });

                    return markdown;
                }
            """)

            return content

        except Exception as e:
            logger.warning(f"Markdown extraction failed, falling back to text: {e}")
            return await page.inner_text("body")

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
        # Use markdown mode for better structured content
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
            "Terms and Conditions",
            "Subscribe to our newsletter",
            "Sign up for our newsletter",
            "Share on Facebook",
            "Share on Twitter",
            "Share on LinkedIn",
            "Follow us on",
            "Download our app",
        ]

        for pattern in noise_patterns:
            content = content.replace(pattern, "")

        return content.strip()

    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            logger.info("Chrome browser closed")

        if self.playwright:
            await self.playwright.stop()
            logger.info("Playwright stopped")
