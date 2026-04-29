"""Static HTML adapter — BeautifulSoup fallback for non-ATS career pages."""
import hashlib
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from utils.logger import logger
from data.models.job import JobPosting

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"}

# CSS selectors checked in priority order to find job link elements
_JOB_SELECTORS = [
    "a[class*=job]",
    "a[class*=position]",
    "a[class*=opening]",
    "a[class*=career]",
    "a[class*=role]",
    "li[class*=job] a",
    "li[class*=position] a",
    "tr[class*=job] a",
    "[data-job-id] a",
    "[data-position] a",
]

# Heading tags that may contain job titles when no anchor is found
_HEADING_TAGS = ["h2", "h3", "h4"]

# Title must contain at least one of these terms (case-insensitive) to be considered a job
_JOB_TERMS = re.compile(
    r"\b(engineer|developer|designer|manager|analyst|scientist|architect|"
    r"devops|sre|product|sales|recruiter|coordinator|specialist|director|"
    r"consultant|intern|associate|lead|head of)\b",
    re.IGNORECASE,
)


class StaticAdapter:
    """Parse job listings from static (server-rendered) HTML career pages."""

    async def fetch_jobs(self, company: dict) -> List[JobPosting]:
        url = company.get("url", "")
        name = company.get("name", "Unknown")

        if not url:
            logger.warning(f"Static {name}: no URL configured")
            return []

        html = await self._fetch(url)
        if not html:
            return []

        jobs = self._parse_html(html, name, url)
        logger.debug(f"Static {name}: {len(jobs)} listings from {url}")
        return jobs

    async def _fetch(self, url: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession(headers=_HEADERS) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        logger.warning(f"Static fetch {url}: HTTP {resp.status}")
                        return None
                    return await resp.text()
        except Exception as e:
            logger.error(f"Static fetch {url}: {e}")
            return None

    def _parse_html(self, html: str, company_name: str, base_url: str) -> List[JobPosting]:
        soup = BeautifulSoup(html, "lxml")

        # Remove noise
        for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        jobs = []
        seen_titles: set[str] = set()

        # Try each selector in priority order
        anchors = []
        for selector in _JOB_SELECTORS:
            anchors = soup.select(selector)
            if anchors:
                break

        if anchors:
            for a in anchors:
                title = a.get_text(separator=" ", strip=True)
                href = a.get("href", "")
                job = self._make_job(title, href, base_url, company_name, seen_titles)
                if job:
                    jobs.append(job)
        else:
            # Fallback: scan headings for job-like titles
            for tag in soup.find_all(_HEADING_TAGS):
                text = tag.get_text(separator=" ", strip=True)
                # Look for an adjacent <a> inside or nearby
                a = tag.find("a") or tag.find_next_sibling("a")
                href = a.get("href", "") if a else ""
                job = self._make_job(text, href, base_url, company_name, seen_titles)
                if job:
                    jobs.append(job)

        return jobs

    def _make_job(
        self,
        title: str,
        href: str,
        base_url: str,
        company_name: str,
        seen: set,
    ) -> Optional[JobPosting]:
        title = " ".join(title.split())  # normalise whitespace
        if not title or len(title) < 5 or len(title) > 200:
            return None
        if not _JOB_TERMS.search(title):
            return None
        key = title.lower()
        if key in seen:
            return None
        seen.add(key)

        # Build absolute URL
        if href and not href.startswith("#"):
            job_url = urljoin(base_url, href)
        else:
            # No real URL — generate a stable synthetic one from company+title
            slug = hashlib.md5(f"{company_name}:{title}".encode()).hexdigest()[:12]
            job_url = f"{base_url}#{slug}"

        return JobPosting(
            url=job_url,
            title=title,
            description=f"Job posting from {company_name} career page",
            subreddit=company_name.lower().replace(" ", "_"),
            author=company_name,
            created_utc=int(datetime.utcnow().timestamp()),
            discovered_at=datetime.utcnow().isoformat(),
            source="company",
            source_id=hashlib.md5(f"{company_name}:{title}".encode()).hexdigest()[:12],
            company_name=company_name,
        )
