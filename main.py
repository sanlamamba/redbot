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

import argparse
import asyncio
import discord

from sources import RedditStream, DiscordBot, HackerNewsStream, CompanyMonitor, IndeedStream
from utils.constants import DISCORD_TOKEN
from utils.logger import logger
from utils.config import get_config


async def _run_web(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Run the FastAPI dashboard inside the same event loop."""
    import uvicorn
    from web.app import app as web_app

    config = uvicorn.Config(web_app, host=host, port=port, loop="asyncio", log_level="warning")
    server = uvicorn.Server(config)
    logger.info(f"Web dashboard starting on http://{host}:{port}")
    await server.serve()


async def main(web: bool = False, web_port: int = 8080) -> None:
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

        # Add Indeed if enabled (requires Publisher API approval)
        if get_config("platforms.indeed.enabled", False):
            indeed_stream = IndeedStream()
            sources.append(indeed_stream)
            logger.info("Indeed source enabled")

        discord_bot = DiscordBot(
            reddit_stream,  # Keep for backward compatibility
            activity=discord.Game(name="Scouting Jobs 🔍"),
            intents=intents,
        )

        # Store all sources on bot for access
        discord_bot.job_sources = sources

        logger.info(f"Bot initialized with {len(sources)} job sources")

        if web:
            await asyncio.gather(
                discord_bot.start(DISCORD_TOKEN),
                _run_web(port=web_port),
            )
        else:
            await discord_bot.start(DISCORD_TOKEN)

    except Exception as e:
        logger.error(f"Fatal error starting bot: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RedBot — Discord job scraper")
    parser.add_argument("--web", action="store_true", help="Also start the web dashboard")
    parser.add_argument("--web-port", type=int, default=8080, help="Web dashboard port (default 8080)")
    args = parser.parse_args()
    asyncio.run(main(web=args.web, web_port=args.web_port))
