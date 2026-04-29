"""Greenhouse ATS adapter — uses the public Boards API (no auth required)."""
import re
from datetime import datetime
from typing import List, Optional

import aiohttp

from utils.logger import logger
from data.models.job import JobPosting

_BASE = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"}


class GreenhouseAdapter:
    """Fetch job listings via Greenhouse Boards API."""

    async def fetch_jobs(self, company: dict) -> List[JobPosting]:
        slug = company.get("slug") or company.get("name", "").lower().replace(" ", "-")
        url = _BASE.format(slug=slug) + "?content=true"
        name = company.get("name", slug)

        try:
            async with aiohttp.ClientSession(headers=_HEADERS) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        logger.warning(f"Greenhouse {name}: HTTP {resp.status}")
                        return []
                    data = await resp.json()
        except Exception as e:
            logger.error(f"Greenhouse {name}: fetch error: {e}")
            return []

        jobs = []
        for item in data.get("jobs", []):
            job = self._parse_item(item, name)
            if job:
                jobs.append(job)

        logger.debug(f"Greenhouse {name}: {len(jobs)} listings")
        return jobs

    def _parse_item(self, item: dict, company_name: str) -> Optional[JobPosting]:
        title = (item.get("title") or "").strip()
        job_url = item.get("absolute_url", "")
        if not title or not job_url:
            return None

        location = (item.get("location") or {}).get("name", "")
        is_remote = bool(re.search(r"\bremote\b", location, re.IGNORECASE))

        # Strip HTML from Greenhouse content field
        raw_content = item.get("content", "")
        description = re.sub(r"<[^>]+>", " ", raw_content).strip()[:2000] if raw_content else ""

        source_id = str(item.get("id", ""))
        updated_raw = item.get("updated_at", "")
        try:
            created_utc = int(datetime.fromisoformat(updated_raw.rstrip("Z")).timestamp())
        except Exception:
            created_utc = int(datetime.utcnow().timestamp())

        return JobPosting(
            url=job_url,
            title=title,
            description=description,
            subreddit=company_name.lower().replace(" ", "_"),
            author=company_name,
            created_utc=created_utc,
            discovered_at=datetime.utcnow().isoformat(),
            source="company",
            source_id=f"gh_{source_id}",
            company_name=company_name,
            location=location,
            is_remote=is_remote,
        )
