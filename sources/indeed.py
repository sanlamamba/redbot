"""Indeed Publisher API source stub.

Requires an approved Indeed Publisher account:
  https://ads.indeed.com/jobroll/xmlfeed

Configuration (config.yaml):
  platforms:
    indeed:
      enabled: true
      publisher_id: "YOUR_PUBLISHER_ID"   # from Indeed Publisher Portal
      keywords:
        - python developer
        - javascript developer
      locations:
        - Remote
      results_per_query: 25

Set enabled: false (default) until Publisher API access is approved.
"""
from __future__ import annotations

from typing import List
from datetime import datetime

import aiohttp

from utils.logger import logger
from utils.config import get_config
from data.models.job import JobPosting
from core import get_job_processor
from sources.base import BaseSource

_API_BASE = "https://api.indeed.com/ads/apisearch"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"}


class IndeedStream(BaseSource):
    """Pull job listings from the Indeed Publisher Job Search API.

    NOTE: This is a stub — the API call is implemented but requires a valid
    publisher_id obtained through Indeed's Publisher Programme approval process.
    The source returns an empty list and logs a reminder until credentials are
    configured.
    """

    name = "Indeed"

    def __init__(self):
        self.job_processor = get_job_processor()
        self.publisher_id: str = get_config("platforms.indeed.publisher_id", "")
        self.keywords: list = get_config("platforms.indeed.keywords", [])
        self.locations: list = get_config("platforms.indeed.locations", ["Remote"])
        self.limit: int = get_config("platforms.indeed.results_per_query", 25)

    async def get_submissions(self) -> List[JobPosting]:
        if not self.publisher_id:
            logger.warning(
                "Indeed: publisher_id not configured. "
                "Apply at https://ads.indeed.com/jobroll/xmlfeed and set "
                "platforms.indeed.publisher_id in config.yaml."
            )
            return []

        all_jobs: List[JobPosting] = []

        for keyword in self.keywords:
            for location in self.locations:
                try:
                    jobs = await self._fetch(keyword, location)
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"Indeed: error fetching '{keyword}' in '{location}': {e}")

        logger.info(f"Indeed: {len(all_jobs)} listings fetched")
        return all_jobs

    async def _fetch(self, keyword: str, location: str) -> List[JobPosting]:
        params = {
            "publisher": self.publisher_id,
            "q": keyword,
            "l": location,
            "format": "json",
            "v": "2",
            "limit": self.limit,
            "userip": "1.2.3.4",        # required by Indeed API
            "useragent": "JobBot/1.0",
        }

        async with aiohttp.ClientSession(headers=_HEADERS) as session:
            async with session.get(
                _API_BASE, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Indeed API: HTTP {resp.status} for '{keyword}'")
                    return []
                data = await resp.json()

        jobs = []
        for item in data.get("results", []):
            job = self._parse_item(item)
            if job:
                jobs.append(self.job_processor.process(job))

        return jobs

    def _parse_item(self, item: dict) -> JobPosting | None:
        title = (item.get("jobtitle") or "").strip()
        url = item.get("url", "")
        if not title or not url:
            return None

        description = item.get("snippet", "")
        company = item.get("company", "")
        location = item.get("formattedLocation", "")
        is_remote = "remote" in location.lower() or "remote" in title.lower()

        # Indeed uses epoch seconds in 'date' field (string: "Mon, 01 Jan 2024 00:00:00 GMT")
        try:
            from email.utils import parsedate_to_datetime
            created_utc = int(parsedate_to_datetime(item["date"]).timestamp())
        except Exception:
            created_utc = int(datetime.utcnow().timestamp())

        return JobPosting(
            url=url,
            title=title,
            description=description,
            subreddit="",
            author=company,
            created_utc=created_utc,
            discovered_at=datetime.utcnow().isoformat(),
            source="indeed",
            source_id=item.get("jobkey", ""),
            company_name=company,
            location=location,
            is_remote=is_remote,
        )

    async def health_check(self) -> bool:
        return bool(self.publisher_id)
