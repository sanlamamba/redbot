"""Company career page monitoring — dispatches to per-company ATS adapters."""
import asyncio
from typing import List

from utils.logger import logger
from utils.config import get_config
from data.models.job import JobPosting
from core import get_job_processor
from sources.base import BaseSource
from sources.adapters import GreenhouseAdapter, LeverAdapter, StaticAdapter, PlaywrightAdapter


_ADAPTERS = {
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
    "static": StaticAdapter,
    "playwright": PlaywrightAdapter,
}


class CompanyMonitor(BaseSource):
    """Monitor specific company career pages for new job postings."""

    name = "CompanyMonitor"

    def __init__(self):
        self.job_processor = get_job_processor()
        self.companies: list = get_config("platforms.company_monitor.companies", [])
        # Cache adapter instances to avoid repeated instantiation
        self._adapters: dict = {}

    def _get_adapter(self, ats_type: str):
        if ats_type not in self._adapters:
            cls = _ADAPTERS.get(ats_type)
            if cls is None:
                logger.warning(f"Unknown ats_type '{ats_type}', falling back to static")
                cls = StaticAdapter
            self._adapters[ats_type] = cls()
        return self._adapters[ats_type]

    async def get_submissions(self) -> List[JobPosting]:
        if not self.companies:
            logger.debug("No companies configured for monitoring")
            return []

        all_jobs: List[JobPosting] = []

        for company in self.companies:
            name = company.get("name", "Unknown")
            ats_type = company.get("ats_type", "static")
            adapter = self._get_adapter(ats_type)

            try:
                raw_jobs = await adapter.fetch_jobs(company)
                for job in raw_jobs:
                    all_jobs.append(self.job_processor.process(job))
                if raw_jobs:
                    logger.info(f"{name} ({ats_type}): {len(raw_jobs)} listings")
            except Exception as e:
                logger.error(f"Error checking {name}: {e}")

            await asyncio.sleep(2)  # rate-limit between companies

        if all_jobs:
            logger.info(f"CompanyMonitor: {len(all_jobs)} total new jobs")

        return all_jobs
