"""Unified deduplication service — single source of truth for seen jobs."""

from __future__ import annotations
from typing import TYPE_CHECKING

from utils.logger import logger

if TYPE_CHECKING:
    from data.database import Database
    from data.models.job import JobPosting


class DeduplicationService:
    """In-memory URL cache backed by the job_postings table.

    All sources check is_duplicate() BEFORE processing a job.
    send_to_discord() calls mark_seen() AFTER a successful send so the
    cache stays consistent with what's actually been posted.
    """

    def __init__(self, db: "Database"):
        self._db = db
        self._url_cache: set[str] = self._load_from_db()
        logger.info(f"DeduplicationService loaded {len(self._url_cache)} known URLs")

    def _load_from_db(self) -> set[str]:
        """Seed the in-memory cache from job_postings at startup."""
        try:
            with self._db.jobs.get_connection() as conn:
                cursor = conn.execute("SELECT url FROM job_postings")
                return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"DeduplicationService: failed to load URL cache: {e}")
            return set()

    def is_duplicate(self, job: "JobPosting") -> bool:
        """Return True if this job URL has already been seen."""
        return job.url in self._url_cache

    def mark_seen(self, job: "JobPosting") -> None:
        """Add job URL to the in-memory cache (DB persistence happens via save())."""
        self._url_cache.add(job.url)

    def cache_size(self) -> int:
        return len(self._url_cache)
