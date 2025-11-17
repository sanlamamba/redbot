"""HackerNews job scraper - monitors 'Who is hiring?' threads."""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional

from utils.logger import logger
from utils.config import get_config
from data.database import get_database
from data.models.job import JobPosting
from core import get_job_processor


class HackerNewsStream:
    """Scrape job postings from HackerNews 'Who is hiring?' threads."""

    def __init__(self):
        """Initialize HackerNews stream."""
        self.api_base = "https://hacker-news.firebaseio.com/v0"
        self.job_processor = get_job_processor()
        self.db = get_database()
        self.processed_ids = set()  # Track processed comment IDs
        self.age_filter_hours = get_config("scraping.age_filter_hours", 24)

    async def find_latest_hiring_thread(self) -> Optional[int]:
        """Find the latest 'Who is hiring?' thread ID.

        Returns:
            Thread ID if found, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Search recent Ask HN posts
                url = "https://hn.algolia.com/api/v1/search"
                params = {
                    "query": "who is hiring",
                    "tags": "ask_hn",
                    "hitsPerPage": 5
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data.get("hits", [])

                        for hit in hits:
                            title = hit.get("title", "").lower()
                            # Look for current month's thread
                            if "who is hiring" in title and "hiring?" in title:
                                thread_id = hit.get("objectID")
                                logger.info(f"Found HN hiring thread: {hit.get('title')} (ID: {thread_id})")
                                return int(thread_id)

        except Exception as e:
            logger.error(f"Error finding HN hiring thread: {e}")

        return None

    async def fetch_item(self, item_id: int) -> Optional[dict]:
        """Fetch a single HN item (story or comment).

        Args:
            item_id: HackerNews item ID

        Returns:
            Item data dict or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/item/{item_id}.json"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Error fetching HN item {item_id}: {e}")

        return None

    async def fetch_comments(self, story_id: int) -> List[dict]:
        """Fetch all top-level comments from a story.

        Args:
            story_id: HackerNews story ID

        Returns:
            List of comment dicts
        """
        story = await self.fetch_item(story_id)
        if not story or "kids" not in story:
            return []

        # Fetch all comments (limited to avoid overload)
        comment_ids = story["kids"][:500]  # Limit to first 500 comments
        logger.info(f"Fetching {len(comment_ids)} comments from HN thread {story_id}")

        comments = []
        for comment_id in comment_ids:
            comment = await self.fetch_item(comment_id)
            if comment and not comment.get("deleted") and comment.get("text"):
                comments.append(comment)
            await asyncio.sleep(0.1)  # Rate limiting

        return comments

    def comment_to_job_posting(self, comment: dict) -> Optional[JobPosting]:
        """Convert HN comment to JobPosting object.

        Args:
            comment: HN comment dict

        Returns:
            JobPosting if valid, None otherwise
        """
        try:
            text = comment.get("text", "")
            if not text or len(text) < 50:  # Too short to be a job posting
                return None

            # Remove HTML tags
            import re
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            # Extract first line as title (usually company name or role)
            lines = text.split('.')
            title = lines[0][:200] if lines else "HN Job Posting"

            # Create URL to comment
            comment_id = comment.get("id")
            url = f"https://news.ycombinator.com/item?id={comment_id}"

            # Check if already processed
            existing = self.db.jobs.get_by_url(url)
            if existing:
                return None

            # Create JobPosting
            job = JobPosting(
                url=url,
                title=title,
                description=text[:1000],  # Limit description length
                subreddit="hackernews",  # Use as source identifier
                author=comment.get("by", "unknown"),
                created_utc=comment.get("time", int(datetime.utcnow().timestamp())),
                discovered_at=datetime.utcnow().isoformat(),
                source="hackernews",
                source_id=str(comment_id)
            )

            return job

        except Exception as e:
            logger.error(f"Error converting HN comment to job: {e}")
            return None

    async def get_submissions(self) -> List[JobPosting]:
        """Get new job postings from HackerNews.

        Returns:
            List of JobPosting objects
        """
        try:
            # Find latest hiring thread
            thread_id = await self.find_latest_hiring_thread()
            if not thread_id:
                logger.warning("No HN hiring thread found")
                return []

            # Fetch comments
            comments = await self.fetch_comments(thread_id)
            logger.info(f"Found {len(comments)} comments in HN thread")

            # Convert to JobPosting objects
            jobs = []
            for comment in comments:
                # Skip if already processed
                comment_id = comment.get("id")
                if comment_id in self.processed_ids:
                    continue

                job = self.comment_to_job_posting(comment)
                if job:
                    # Process through job processor (salary, experience, etc.)
                    processed_job = self.job_processor.process(job)
                    jobs.append(processed_job)
                    self.processed_ids.add(comment_id)

            logger.info(f"Processed {len(jobs)} new HN job postings")
            return jobs

        except Exception as e:
            logger.error(f"Error getting HN submissions: {e}")
            return []
