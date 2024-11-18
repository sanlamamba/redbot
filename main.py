#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Name: main.py
Description: A Discord bot that monitors Reddit for job postings and
             automatically forwards them to a specified Discord channel.
Features include:
- Multi-subreddit monitoring
- Keyword filtering
- Duplicate post detection
- Automatic message cleanup
- Persistent logging
Author: San Lamamba P.
Created: 2024
Dependencies: discord.py, asyncpraw, python-dotenv, loguru
Environment: Requires .env file with Reddit and Discord credentials
"""

import asyncio
import discord
from components.discord import DiscordBot
from components.reddit import RedditStream
from utils.constants import DISCORD_TOKEN


async def main() -> None:
    """Main function to start the Discord bot and Reddit stream."""
    reddit_stream = RedditStream()
    discord_bot = DiscordBot(
        reddit_stream,
        activity=discord.Game(name="Reddit Jobs"),
        intents=discord.Intents.default(),
    )
    await discord_bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
