#!/usr/bin/env python3
"""
Reddit Job Scraper Bot

A Discord bot that monitors Reddit for job postings and automatically forwards
them to a specified Discord channel with intelligent parsing and analysis.

Features:
- Multi-subreddit monitoring with keyword filtering
- Salary detection and normalization
- Experience level classification
- Sentiment analysis and red flag detection
- Tech stack extraction
- Duplicate post detection
- Rich Discord embeds with parsed data

Author: San Lamamba P.
Created: 2024
"""

import asyncio
import discord

from sources import RedditStream, DiscordBot, HackerNewsStream, CompanyMonitor
from utils.constants import DISCORD_TOKEN
from utils.logger import logger
from utils.config import get_config


async def main() -> None:
    """Main entry point - initialize and start the bot."""
    logger.info("Starting Multi-Source Job Scraper Bot...")

    try:
        # Configure Discord intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for reading message content and commands
        intents.messages = True  # Required for message events

        # Initialize job sources
        reddit_stream = RedditStream()
        sources = [reddit_stream]

        # Add HackerNews if enabled
        if get_config("platforms.hackernews.enabled", False):
            hn_stream = HackerNewsStream()
            sources.append(hn_stream)
            logger.info("HackerNews source enabled")

        # Add company monitor if enabled
        if get_config("platforms.company_monitor.enabled", False):
            company_monitor = CompanyMonitor()
            sources.append(company_monitor)
            logger.info("Company monitoring enabled")

        discord_bot = DiscordBot(
            reddit_stream,  # Keep for backward compatibility
            activity=discord.Game(name="Scouting Jobs 🔍"),
            intents=intents,
        )

        # Store all sources on bot for access
        discord_bot.job_sources = sources

        logger.info(f"Bot initialized with {len(sources)} job sources")
        await discord_bot.start(DISCORD_TOKEN)

    except Exception as e:
        logger.error(f"Fatal error starting bot: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
