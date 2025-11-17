"""Company career page monitoring - track job postings from specific companies."""
import asyncio
import aiohttp
import hashlib
from datetime import datetime
from typing import List, Optional, Dict
import re

from utils.logger import logger
from utils.config import get_config
from data.database import get_database
from data.models.job import JobPosting
from core import get_job_processor


class CompanyMonitor:
    """Monitor specific company career pages for new job postings."""

    def __init__(self):
        """Initialize company monitor."""
        self.job_processor = get_job_processor()
        self.db = get_database()
        self.page_hashes: Dict[str, str] = {}  # Track page content hashes
        self.companies = get_config("platforms.company_monitor.companies", [])

    def get_page_hash(self, content: str) -> str:
        """Generate hash of page content for change detection.

        Args:
            content: Page HTML content

        Returns:
            MD5 hash string
        """
        return hashlib.md5(content.encode()).hexdigest()

    async def fetch_career_page(self, url: str) -> Optional[str]:
        """Fetch company career page content.

        Args:
            url: Career page URL

        Returns:
            Page content or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"
                }
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")

        return None

    def extract_jobs_from_page(self, html: str, company_name: str, base_url: str) -> List[JobPosting]:
        """Extract job postings from HTML content.

        Simple extraction based on common patterns. Can be enhanced per company.

        Args:
            html: HTML content
            company_name: Company name
            base_url: Base URL for the career page

        Returns:
            List of JobPosting objects
        """
        jobs = []

        try:
            # Remove script and style tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)

            # Look for job titles (common patterns)
            patterns = [
                r'<h[23][^>]*>([^<]+(?:engineer|developer|designer|manager|analyst|scientist)[^<]*)</h[23]>',
                r'job-title["\'][^>]*>([^<]+)</[^>]+>',
                r'position["\'][^>]*>([^<]+)</[^>]+>',
            ]

            all_titles = set()
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                all_titles.update(matches)

            # Create JobPosting for each unique title
            for title in all_titles:
                title = re.sub(r'<[^>]+>', '', title).strip()
                if len(title) < 5 or len(title) > 200:
                    continue

                # Generate unique URL (hash-based since we don't have individual URLs)
                job_id = hashlib.md5(f"{company_name}:{title}".encode()).hexdigest()[:12]
                url = f"{base_url}#{job_id}"

                # Check if already exists
                existing = self.db.jobs.get_by_url(url)
                if existing:
                    continue

                # Create job posting
                job = JobPosting(
                    url=url,
                    title=title,
                    description=f"Job posting from {company_name} career page",
                    subreddit=company_name.lower().replace(" ", "_"),
                    author=company_name,
                    created_utc=int(datetime.utcnow().timestamp()),
                    discovered_at=datetime.utcnow().isoformat(),
                    source="company",
                    source_id=job_id,
                    company_name=company_name
                )

                jobs.append(job)

        except Exception as e:
            logger.error(f"Error extracting jobs from {company_name}: {e}")

        return jobs

    async def check_company(self, company: dict) -> List[JobPosting]:
        """Check a single company for new job postings.

        Args:
            company: Company config dict with 'name' and 'url'

        Returns:
            List of new JobPosting objects
        """
        name = company.get("name", "Unknown")
        url = company.get("url")

        if not url:
            logger.warning(f"No URL configured for {name}")
            return []

        logger.info(f"Checking {name} at {url}")

        # Fetch page
        html = await self.fetch_career_page(url)
        if not html:
            return []

        # Check if page changed
        page_hash = self.get_page_hash(html)
        if url in self.page_hashes and self.page_hashes[url] == page_hash:
            logger.debug(f"{name}: No changes detected")
            return []

        self.page_hashes[url] = page_hash

        # Extract jobs
        jobs = self.extract_jobs_from_page(html, name, url)

        if jobs:
            logger.info(f"{name}: Found {len(jobs)} new job postings")

            # Process through job processor
            processed_jobs = []
            for job in jobs:
                processed_job = self.job_processor.process(job)
                processed_jobs.append(processed_job)

            return processed_jobs

        return []

    async def get_submissions(self) -> List[JobPosting]:
        """Get new job postings from all monitored companies.

        Returns:
            List of JobPosting objects
        """
        if not self.companies:
            logger.debug("No companies configured for monitoring")
            return []

        all_jobs = []

        for company in self.companies:
            try:
                jobs = await self.check_company(company)
                all_jobs.extend(jobs)
                await asyncio.sleep(2)  # Rate limiting between companies
            except Exception as e:
                logger.error(f"Error checking {company.get('name', 'Unknown')}: {e}")

        if all_jobs:
            logger.info(f"Company monitor: Found {len(all_jobs)} total new jobs")

        return all_jobs
