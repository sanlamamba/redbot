"""Unified deduplication service — single source of truth for seen jobs."""

from __future__ import annotations
from typing import TYPE_CHECKING

from utils.logger import logger

if TYPE_CHECKING:
    from data.database import Database
    from data.models.job import JobPosting


class DeduplicationService:
    """In-memory URL + content-hash cache backed by the job_postings table.

    URL dedup catches exact-URL repeats (same post scraped twice).
    Content-hash dedup catches the same job appearing across different sources
    (Reddit, HackerNews, and a company career page all listing the same role).

    All sources check is_duplicate() BEFORE processing a job.
    send_to_discord() calls mark_seen() AFTER a successful send so the
    cache stays consistent with what's actually been posted.
    """

    def __init__(self, db: "Database"):
        self._db = db
        self._url_cache: set[str] = set()
        self._hash_cache: set[str] = set()
        self._load_from_db()
        logger.info(
            f"DeduplicationService: {len(self._url_cache)} URLs, "
            f"{len(self._hash_cache)} content hashes"
        )

    def _load_from_db(self) -> None:
        """Seed both in-memory caches from job_postings at startup."""
        try:
            with self._db.jobs.get_connection() as conn:
                cursor = conn.execute("SELECT url, content_hash FROM job_postings")
                for url, content_hash in cursor.fetchall():
                    self._url_cache.add(url)
                    if content_hash:
                        self._hash_cache.add(content_hash)
        except Exception as e:
            logger.error(f"DeduplicationService: failed to load caches: {e}")

    def is_duplicate(self, job: "JobPosting") -> bool:
        """Return True if this job has already been seen (by URL or content hash)."""
        if job.url in self._url_cache:
            return True
        if job.content_hash and job.content_hash in self._hash_cache:
            logger.debug(f"Content-hash duplicate: {job.title!r} ({job.source})")
            return True
        return False

    def mark_seen(self, job: "JobPosting") -> None:
        """Add job to both in-memory caches (DB persistence happens via save())."""
        self._url_cache.add(job.url)
        if job.content_hash:
            self._hash_cache.add(job.content_hash)

    def cache_size(self) -> int:
        return len(self._url_cache)
