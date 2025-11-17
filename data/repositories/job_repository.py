"""Job repository for job posting data access."""
from datetime import datetime, timedelta
from typing import Optional, List

from ..models.job import JobPosting
from .base_repository import BaseRepository


class JobRepository(BaseRepository):
    """Repository for job posting data access."""

    def save(self, job: JobPosting) -> Optional[int]:
        """Save job posting to database.

        Args:
            job: JobPosting instance

        Returns:
            Job ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                data = job.to_dict()
                data.pop('id', None)  # Remove ID (auto-increment)

                columns = ', '.join(data.keys())
                placeholders = ', '.join('?' * len(data))

                cursor.execute(
                    f"INSERT OR IGNORE INTO job_postings ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )

                return cursor.lastrowid if cursor.rowcount > 0 else None
        except Exception as e:
            print(f"Error saving job: {e}")
            return None

    def get_by_url(self, url: str) -> Optional[JobPosting]:
        """Get job posting by URL."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM job_postings WHERE url = ?", (url,))
                row = cursor.fetchone()
                return JobPosting.from_dict(dict(row)) if row else None
        except Exception as e:
            print(f"Error getting job by URL: {e}")
            return None

    def get_recent(self, hours: int = 24, limit: int = 100) -> List[JobPosting]:
        """Get recent job postings."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cutoff = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())

                cursor.execute(
                    """
                    SELECT * FROM job_postings
                    WHERE created_utc >= ? AND archived = 0
                    ORDER BY created_utc DESC
                    LIMIT ?
                    """,
                    (cutoff, limit)
                )

                return [JobPosting.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting recent jobs: {e}")
            return []

    def mark_duplicate(self, job_url: str, original_job_id: int) -> bool:
        """Mark job as duplicate of another job."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE job_postings SET duplicate_of = ? WHERE url = ?",
                    (original_job_id, job_url)
                )
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error marking duplicate: {e}")
            return False

    def find_similar(self, job: JobPosting, days: int = 7) -> List[JobPosting]:
        """Find similar jobs posted in recent days."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cutoff = int((datetime.utcnow() - timedelta(days=days)).timestamp())

                cursor.execute(
                    """
                    SELECT * FROM job_postings
                    WHERE created_utc >= ?
                    AND url != ?
                    AND (company_name = ? OR title LIKE ?)
                    AND archived = 0
                    ORDER BY created_utc DESC
                    LIMIT 10
                    """,
                    (cutoff, job.url, job.company_name, f"%{job.title[:30]}%")
                )

                return [JobPosting.from_dict(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error finding similar jobs: {e}")
            return []

    def archive_old(self, days: int = 90) -> int:
        """Archive jobs older than specified days."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cutoff = int((datetime.utcnow() - timedelta(days=days)).timestamp())
                timestamp = datetime.utcnow().isoformat()

                cursor.execute(
                    """
                    UPDATE job_postings
                    SET archived = 1, archived_at = ?
                    WHERE created_utc < ? AND archived = 0
                    """,
                    (timestamp, cutoff)
                )
                return cursor.rowcount
        except Exception as e:
            print(f"Error archiving old jobs: {e}")
            return 0
