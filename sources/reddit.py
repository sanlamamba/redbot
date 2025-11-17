"""
Module Name: reddit_stream
Description: This module defines the RedditStream class, which interacts with the Reddit API
to retrieve new job postings from specified subreddits based on defined keywords.
"""

import asyncpraw
from datetime import datetime, timedelta

from utils.logger import logger
from utils.config import get_config
from utils.constants import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    MULTI_SUBREDDIT_QUERY,
    KEYWORDS,
    POST_LIMIT,
)
from data.database import load_sent_posts, save_sent_post
from data.models.job import JobPosting
from core import get_job_processor


class RedditStream:
    """A class to interact with the Reddit API and get new submissions from specified subreddits."""

    def __init__(self):
        self.reddit = asyncpraw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        self.sent_posts = load_sent_posts()
        self.age_filter_hours = get_config("scraping.age_filter_hours", 24)
        self.job_processor = get_job_processor()

    async def get_submissions(self) -> list:
        """Get new submissions from the Reddit API based on keywords and subreddits.

        Returns:
            list: A list of processed JobPosting objects.
        """
        subreddit = await self.reddit.subreddit(MULTI_SUBREDDIT_QUERY)
        submissions = []
        now = datetime.utcnow()
        age_cutoff = now - timedelta(hours=self.age_filter_hours)

        async for submission in subreddit.new(limit=POST_LIMIT):
            # Check age filter (if enabled)
            if self.age_filter_hours > 0:
                post_age = datetime.utcfromtimestamp(submission.created_utc)
                if post_age < age_cutoff:
                    continue  # Skip old posts

            post_title = submission.title.lower()
            post_text = submission.selftext.lower()
            post_url = submission.url

            # Check keywords and exclusions
            if (
                any(
                    keyword in post_title or keyword in post_text
                    for keyword in KEYWORDS
                )
                and "for hire" not in post_title
            ):
                if post_url not in self.sent_posts:
                    # Convert to JobPosting and process
                    job = self._create_job_posting(submission)
                    processed_job = self.job_processor.process(job)
                    submissions.append(processed_job)

        logger.info(f"Found {len(submissions)} new posts in the subreddits.")
        return submissions

    def _create_job_posting(self, submission) -> JobPosting:
        """Convert Reddit submission to JobPosting.

        Args:
            submission: asyncpraw Submission object

        Returns:
            JobPosting instance
        """
        return JobPosting(
            url=submission.url,
            title=submission.title,
            description=submission.selftext,
            subreddit=submission.subreddit.display_name,
            author=submission.author.name if submission.author else "[deleted]",
            created_utc=int(submission.created_utc),
            discovered_at=datetime.utcnow().isoformat(),
            source="reddit",
            source_id=submission.id
        )

    def add_sent_post(self, url: str) -> None:
        """Add a sent post URL to the sent_posts set.

        Args:
            url (str): The URL of the sent post.
        """
        self.sent_posts.add(url)
        logger.debug(f"Added {url} to the list of sent posts.")
        save_sent_post(url)
