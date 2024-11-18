"""
Module Name: reddit_stream
Description: This module defines the RedditStream class, which interacts with the Reddit API
to retrieve new job postings from specified subreddits based on defined keywords.
"""

import asyncpraw
from utils.database import load_sent_posts, save_sent_post
from utils.bprint import bprint as bp
from utils.constants import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    MULTI_SUBREDDIT_QUERY,
    KEYWORDS,
    POST_LIMIT,
)


class RedditStream:
    """A class to interact with the Reddit API and get new submissions from specified subreddits."""

    def __init__(self):
        self.reddit = asyncpraw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        self.sent_posts = load_sent_posts()

    async def get_submissions(self) -> list:
        """Get new submissions from the Reddit API based on keywords and subreddits.

        Returns:
            list: A list of asyncpraw.models.Submission objects.
        """
        subreddit = await self.reddit.subreddit(MULTI_SUBREDDIT_QUERY)
        submissions = []

        async for submission in subreddit.new(limit=POST_LIMIT):
            post_title = submission.title.lower()
            post_text = submission.selftext.lower()
            post_url = submission.url

            if (
                any(
                    keyword in post_title or keyword in post_text
                    for keyword in KEYWORDS
                )
                and "for hire" not in post_title
            ):
                if post_url not in self.sent_posts:
                    submissions.append(submission)

        bp.info(f"Found {len(submissions)} new posts in the subreddits.")
        return submissions

    def add_sent_post(self, url: str) -> None:
        """Add a sent post URL to the sent_posts set.

        Args:
            url (str): The URL of the sent post.
        """
        self.sent_posts.add(url)
        bp.info(f"Added {url} to the list of sent posts.")
        save_sent_post(url)
