"""Playwright adapter for JS-rendered career pages.

Activated by setting ats_type: playwright in a company's config block.
Falls back to StaticAdapter automatically if Playwright is not installed
or no browsers are available — no hard dependency.

Install (optional):
    pip install playwright
    playwright install chromium
"""
from __future__ import annotations

from typing import List

from utils.logger import logger
from data.models.job import JobPosting
from .static import StaticAdapter


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


class PlaywrightAdapter:
    """Fetch JS-rendered career pages using a headless Chromium browser.

    Falls back to StaticAdapter if Playwright is unavailable so operators
    don't need to install it unless they have JS-heavy target sites.
    """

    def __init__(self):
        self._fallback = StaticAdapter()
        self._available = _playwright_available()
        if not self._available:
            logger.warning(
                "Playwright not installed — JS-rendered adapter will fall back to static HTML. "
                "Install with: pip install playwright && playwright install chromium"
            )

    async def fetch_jobs(self, company: dict) -> List[JobPosting]:
        if not self._available:
            return await self._fallback.fetch_jobs(company)

        url = company.get("url", "")
        name = company.get("name", "Unknown")
        if not url:
            logger.warning(f"Playwright {name}: no URL configured")
            return []

        try:
            html = await self._render(url)
        except Exception as e:
            logger.error(f"Playwright {name}: render failed ({e}), falling back to static")
            return await self._fallback.fetch_jobs(company)

        if not html:
            return await self._fallback.fetch_jobs(company)

        # Reuse StaticAdapter's BS4 parsing on the rendered HTML
        jobs = self._fallback._parse_html(html, name, url)
        logger.debug(f"Playwright {name}: {len(jobs)} listings from {url}")
        return jobs

    async def _render(self, url: str) -> str:
        """Launch a headless Chromium instance, navigate to URL, return rendered HTML."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    user_agent="Mozilla/5.0 (compatible; JobBot/1.0)"
                )
                await page.goto(url, timeout=30_000, wait_until="networkidle")
                # Wait a moment for any lazy-loaded job cards
                await page.wait_for_timeout(2000)
                html = await page.content()
            finally:
                await browser.close()

        return html
