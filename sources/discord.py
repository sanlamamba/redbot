"""
Module Name: discord_bot
Description: This module defines the DiscordBot class, which interacts with the Discord API
to send new Reddit submissions to a specified Discord channel.
"""

import asyncio
import discord
from discord import app_commands

from utils.constants import CHECK_FREQUENCY_SECONDS
from utils.logger import logger
from data.database import get_database
from data.models.job import JobPosting
from core.dedup import DeduplicationService
from parsers import SalaryParser, ExperienceParser, SentimentAnalyzer
from .reddit import RedditStream
from .command_context import CommandContext
from .commands import CommandHandler
from .slash_commands import SlashCommands
from .embed_builder import EmbedBuilder


class DiscordBot(discord.Client):
    """A class to interact with the Discord API
    and send new Reddit submissions to a Discord channel.
    """

    def __init__(self, reddit_stream: RedditStream, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reddit_stream = reddit_stream
        self.salary_parser = SalaryParser()
        self.experience_parser = ExperienceParser()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.embed_builder = EmbedBuilder(
            self.salary_parser, self.experience_parser, self.sentiment_analyzer
        )
        self.command_prefix = "!"
        self.command_handler = CommandHandler(self.salary_parser, self.experience_parser)
        self.job_sources = [reddit_stream]  # Will be updated by main.py
        self.job_channel_id = None  # Will be loaded from database on ready
        self.dedup = DeduplicationService(get_database())

        # Set up slash commands
        self.tree = app_commands.CommandTree(self)
        self.slash_commands = SlashCommands(self, self.command_handler)
        self.slash_commands.register_commands(self.tree)

    async def bulk_delete(self) -> None:
        """Bulk delete old messages from the bot in the Discord channel."""
        if not self.job_channel_id:
            logger.warning("No job channel configured, skipping bulk delete")
            return

        channel = self.get_channel(self.job_channel_id)
        if channel:
            try:
                deleted = await channel.purge(
                    limit=100, check=lambda m: m.author == self.user
                )
                logger.info(f"Bulk deleted {len(deleted)} old messages from the bot.")
            except Exception as e:
                logger.error(f"Error in bulk delete: {e}")

    async def send_to_discord(self, job: JobPosting) -> None:
        """Send a job posting to the Discord channel with enhanced information.

        Args:
            job: JobPosting object with parsed data
        """
        if self.dedup.is_duplicate(job):
            logger.debug(f"Skipping duplicate job: {job.url}")
            return

        if not self.job_channel_id:
            logger.warning("No job channel configured, skipping job posting")
            return

        channel = self.get_channel(self.job_channel_id)
        if channel is None:
            logger.error(f"Failed to get Discord channel with ID: {self.job_channel_id}")
            return

        embed = self.embed_builder.build_job_embed(job)

        try:
            # Save full job posting to database
            db = get_database()
            job_id = db.jobs.save(job)
            if job_id:
                logger.debug(f"Saved job to database: ID {job_id}")

            # Send to Discord
            await channel.send(embed=embed)
            logger.info(f"Sent job: {job.title[:50]}...")
            self.dedup.mark_seen(job)
        except Exception as e:
            logger.error(f"Error sending message to Discord: {e}")

    async def on_message(self, message: discord.Message) -> None:
        """Event handler for processing commands."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Check if message starts with command prefix
        if not message.content.startswith(self.command_prefix):
            return

        # Parse command and arguments
        parts = message.content[len(self.command_prefix):].strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        ctx = CommandContext.from_message(message)

        # Route commands to handler
        try:
            if command == "help":
                await self.command_handler.handle_help(ctx)
            elif command == "stats":
                await self.command_handler.handle_stats(ctx)
            elif command == "search":
                await self.command_handler.handle_search(ctx, args)
            elif command == "trends":
                await self.command_handler.handle_trends(ctx, args)
            elif command == "export":
                await self.command_handler.handle_export(ctx)
            elif command == "setchannel":
                await self.command_handler.handle_setchannel(self, ctx, args)
            elif command == "getchannel":
                await self.command_handler.handle_getchannel(self, ctx)
            else:
                await message.channel.send(f"Unknown command: `{command}`. Type `!help` for available commands.")
        except Exception as e:
            logger.error(f"Error processing command '{command}': {e}")
            await message.channel.send(f"❌ Error processing command: {str(e)}")

    async def on_ready(self) -> None:
        """Event handler for when the bot is ready."""
        logger.info("="*70)
        logger.info(f"Bot connected as: {self.user.name} (ID: {self.user.id})")
        logger.info("="*70)

        # Show server information
        guild_count = len(self.guilds)
        if guild_count == 0:
            logger.warning("Bot is not in any servers yet!")
            logger.warning("Invite the bot to a server to get started.")
        else:
            logger.info(f"Active in {guild_count} server(s):")
            for i, guild in enumerate(self.guilds, 1):
                member_count = guild.member_count
                text_channels = len(guild.text_channels)
                logger.info(
                    f"  {i}. {guild.name} | "
                    f"Members: {member_count} | "
                    f"Channels: {text_channels} | "
                    f"ID: {guild.id}"
                )

        logger.info("-"*70)

        # Load job channel from database (per-guild where possible)
        db = get_database()
        # Use the first guild's channel config as the active one; multi-guild
        # routing will be handled by Phase 4.3 RoutingEngine.
        primary_guild_id = str(self.guilds[0].id) if self.guilds else ""
        self.job_channel_id = (
            db.settings.get_int("job_channel_id", guild_id=primary_guild_id)
            or db.settings.get_int("job_channel_id", guild_id="")  # fall back to global
        )

        if self.job_channel_id:
            channel = self.get_channel(self.job_channel_id)
            if channel:
                logger.info(f"✓ Job channel: #{channel.name} (ID: {self.job_channel_id})")
            else:
                logger.warning(f"⚠ Configured channel ID {self.job_channel_id} not found or inaccessible")
                logger.warning("  Use !setchannel to reconfigure")
        else:
            logger.warning("⚠ No job channel configured")
            logger.warning("  Use !setchannel #channel-name to set one")

        source_names = [s.name for s in self.job_sources]
        logger.info(f"Job sources enabled: {', '.join(source_names)}")

        # Sync slash commands
        logger.info("-"*70)
        logger.info("Syncing slash commands...")
        try:
            synced = await self.tree.sync()
            logger.info(f"✓ Synced {len(synced)} slash command(s)")
            logger.info("  Commands available as /help, /stats, /search, etc.")
        except Exception as e:
            logger.error(f"⚠ Failed to sync slash commands: {e}")
            logger.warning("  Text commands (!help) will still work")

        logger.info("="*70)
        logger.info("Bot ready! Monitoring for jobs...")
        logger.info("="*70)

        await asyncio.gather(self.bulk_delete(), self.start_scraping_jobs())

    async def start_scraping_jobs(self) -> None:
        """Start the job scraping process from all sources."""
        logger.info(f"Starting job scraping from {len(self.job_sources)} sources...")

        while not self.is_closed():
            try:
                all_jobs = []

                # Scrape from all sources
                for source in self.job_sources:
                    try:
                        jobs = await source.get_submissions()
                        all_jobs.extend(jobs)
                        logger.info(f"{source.name}: Found {len(jobs)} new jobs")
                    except Exception as e:
                        logger.error(f"Error scraping {source.name}: {e}")

                # Send all jobs to Discord
                logger.info(f"Total: {len(all_jobs)} jobs from all sources")
                for job in all_jobs:
                    await self.send_to_discord(job)
                    await asyncio.sleep(0.5)  # Avoid rate limits

            except Exception as e:
                logger.error(f"Error in scraping loop: {e}")

            await asyncio.sleep(CHECK_FREQUENCY_SECONDS)
