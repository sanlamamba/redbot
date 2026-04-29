"""Lever ATS adapter — uses the public Lever postings API (no auth required)."""
import re
from datetime import datetime, timezone
from typing import List, Optional

import aiohttp

from utils.logger import logger
from data.models.job import JobPosting

_BASE = "https://api.lever.co/v0/postings/{slug}?mode=json"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"}


class LeverAdapter:
    """Fetch job listings via Lever public postings API."""

    async def fetch_jobs(self, company: dict) -> List[JobPosting]:
        slug = company.get("slug") or company.get("name", "").lower().replace(" ", "-")
        url = _BASE.format(slug=slug)
        name = company.get("name", slug)

        try:
            async with aiohttp.ClientSession(headers=_HEADERS) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        logger.warning(f"Lever {name}: HTTP {resp.status}")
                        return []
                    data = await resp.json()
        except Exception as e:
            logger.error(f"Lever {name}: fetch error: {e}")
            return []

        if not isinstance(data, list):
            logger.warning(f"Lever {name}: unexpected response shape")
            return []

        jobs = []
        for item in data:
            job = self._parse_item(item, name)
            if job:
                jobs.append(job)

        logger.debug(f"Lever {name}: {len(jobs)} listings")
        return jobs

    def _parse_item(self, item: dict, company_name: str) -> Optional[JobPosting]:
        title = (item.get("text") or "").strip()
        job_url = item.get("hostedUrl", "")
        if not title or not job_url:
            return None

        categories = item.get("categories") or {}
        location = categories.get("location", "")
        commitment = categories.get("commitment", "")
        is_remote = bool(re.search(r"\bremote\b", f"{location} {commitment}", re.IGNORECASE))

        description = (item.get("descriptionPlain") or item.get("description") or "").strip()[:2000]
        if not description:
            description = f"Job posting from {company_name}"

        source_id = str(item.get("id", ""))
        created_ms = item.get("createdAt", 0)
        created_utc = int(created_ms / 1000) if created_ms else int(datetime.utcnow().timestamp())

        return JobPosting(
            url=job_url,
            title=title,
            description=description,
            subreddit=company_name.lower().replace(" ", "_"),
            author=company_name,
            created_utc=created_utc,
            discovered_at=datetime.utcnow().isoformat(),
            source="company",
            source_id=f"lv_{source_id}",
            company_name=company_name,
            location=location,
            is_remote=is_remote,
        )
