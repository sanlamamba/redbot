"""
Module Name: discord_bot
Description: This module defines the DiscordBot class, which interacts with the Discord API
to send new Reddit submissions to a specified Discord channel.
"""

import asyncio
from datetime import datetime
import discord
from utils.constants import DISCORD_CHANNEL_ID, CHECK_FREQUENCY_SECONDS
from utils.database import save_sent_post
from utils.bprint import bprint as bp
from utils.database import purge_sent_posts
from .reddit import RedditStream


class DiscordBot(discord.Client):
    """A class to interact with the Discord API
    and send new Reddit submissions to a Discord channel.
    """

    def __init__(self, reddit_stream: RedditStream, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reddit_stream = reddit_stream

    async def bulk_delete(self) -> None:
        """Bulk delete old messages from the bot in the Discord channel."""
        channel = self.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            try:
                deleted = await channel.purge(
                    limit=100, check=lambda m: m.author == self.user
                )
                bp.info(f"Bulk deleted {len(deleted)} old messages from the bot.")
            except Exception as e:
                bp.error(f"Error in bulk delete: {e}")

    async def send_to_discord(self, submission) -> None:
        """Send a Reddit submission to the Discord channel.

        Args:
            submission (asyncpraw.models.Submission): A Reddit submission object.
        """
        channel = self.get_channel(DISCORD_CHANNEL_ID)
        if channel is None:
            bp.error(f"Failed to get Discord channel with ID: {DISCORD_CHANNEL_ID}")
            return

        description = (
            submission.selftext[:200] + "..."
            if submission.selftext
            else "No description provided"
        )
        embed = discord.Embed(
            title=submission.title[:256],
            url=submission.url,
            description=description,
            color=discord.Color.blue(),
            timestamp=datetime.utcfromtimestamp(submission.created_utc),
        )
        embed.set_author(name=submission.author.name)
        embed.add_field(
            name="Subreddit", value=submission.subreddit.display_name, inline=True
        )
        embed.set_footer(text="Posted at")

        try:
            await channel.send(embed=embed)
            bp.info(f"Sent post: {submission.title}")
            save_sent_post(submission.url)
            self.reddit_stream.sent_posts.add(submission.url)
        except Exception as e:
            bp.error(f"Error sending message to Discord: {e}")

    async def on_ready(self) -> None:
        """Event handler for when the bot is ready."""
        bp.info(f"Logged in as {self.user.name}")
        await asyncio.gather(self.bulk_delete(), self.start_scraping_jobs())
        await purge_sent_posts()

    async def start_scraping_jobs(self) -> None:
        """Start the Reddit job scraping process."""
        bp.info("Starting the Reddit job scraping process...")
        while not self.is_closed():
            try:
                submissions = await self.reddit_stream.get_submissions()
                bp.info(f"Scraping completed. Found {len(submissions)} matching posts.")
                for submission in submissions:
                    await self.send_to_discord(submission)
            except Exception as e:
                bp.error(f"Error checking Reddit: {e}")
            await asyncio.sleep(CHECK_FREQUENCY_SECONDS)
