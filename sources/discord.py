"""
Module Name: discord_bot
Description: This module defines the DiscordBot class, which interacts with the Discord API
to send new Reddit submissions to a specified Discord channel.
"""

import asyncio
from datetime import datetime
import discord
from discord import app_commands

from utils.constants import CHECK_FREQUENCY_SECONDS
from utils.logger import logger
from data.database import save_sent_post, get_database
from data.models.job import JobPosting
from parsers import SalaryParser, ExperienceParser, SentimentAnalyzer
from .reddit import RedditStream
from .commands import CommandHandler
from .slash_commands import SlashCommands


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
        self.command_prefix = "!"
        self.command_handler = CommandHandler(self.salary_parser, self.experience_parser)
        self.job_sources = [reddit_stream]  # Will be updated by main.py
        self.job_channel_id = None  # Will be loaded from database on ready

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
        if not self.job_channel_id:
            logger.warning("No job channel configured, skipping job posting")
            return

        channel = self.get_channel(self.job_channel_id)
        if channel is None:
            logger.error(f"Failed to get Discord channel with ID: {self.job_channel_id}")
            return

        # Determine embed color based on red flags and score
        if job.red_flags and len(job.red_flags) >= 3:
            color = discord.Color.red()  # Suspicious
        elif job.red_flags:
            color = discord.Color.orange()  # Some concerns
        elif job.salary_min and job.salary_min > 100000:
            color = discord.Color.gold()  # High salary
        else:
            color = discord.Color.blue()  # Normal

        # Create title with experience level icon
        title = job.title[:200]
        if job.experience_level:
            icon = self.experience_parser.get_icon(job.experience_level.split(",")[0].strip())
            title = f"{icon} {title}" if icon else title

        # Create description
        description = (
            job.description[:300] + "..."
            if job.description and len(job.description) > 300
            else job.description or "No description provided"
        )

        # Add red flag warning to description
        if job.red_flags:
            warnings = self.sentiment_analyzer.format_warnings(
                {"red_flags": job.red_flags, "warnings": []}
            )
            if warnings:
                description = f"⚠️ **{warnings}**\n\n{description}"

        # Create embed
        embed = discord.Embed(
            title=title,
            url=job.url,
            description=description,
            color=color,
            timestamp=datetime.utcfromtimestamp(job.created_utc),
        )

        # Add author and subreddit
        if job.author:
            embed.set_author(name=job.author)
        if job.subreddit:
            embed.add_field(name="Subreddit", value=f"r/{job.subreddit}", inline=True)

        # Add posted time with relative and absolute timestamps
        posted_time = datetime.utcfromtimestamp(job.created_utc)
        now = datetime.utcnow()
        time_diff = now - posted_time

        # Calculate relative time
        if time_diff.days > 0:
            if time_diff.days == 1:
                relative = "1 day ago"
            else:
                relative = f"{time_diff.days} days ago"
        elif time_diff.seconds >= 3600:
            hours = time_diff.seconds // 3600
            relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif time_diff.seconds >= 60:
            minutes = time_diff.seconds // 60
            relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            relative = "just now"

        # Format absolute time
        absolute = posted_time.strftime("%Y-%m-%d %H:%M UTC")
        posted_str = f"{relative}\n({absolute})"
        embed.add_field(name="🕒 Posted", value=posted_str, inline=True)

        # Add salary if detected
        if job.salary_min or job.salary_max:
            salary_info = type('obj', (object,), {
                'min': job.salary_min,
                'max': job.salary_max,
                'currency': job.salary_currency or 'USD',
                'period': job.salary_period or 'yearly'
            })()
            salary_str = self.salary_parser.format_salary(salary_info)
            embed.add_field(name="💰 Salary", value=salary_str, inline=True)

        # Add experience level if detected
        if job.experience_level:
            levels = job.experience_level.split(", ")
            formatted = self.experience_parser.format_levels(levels)
            embed.add_field(name="📊 Level", value=formatted or job.experience_level, inline=True)

        # Add location/remote status
        if job.location or job.is_remote:
            location_str = job.location or ""
            if job.is_remote:
                location_str = "🌍 Remote" + (f" ({location_str})" if location_str else "")
            if location_str:
                embed.add_field(name="📍 Location", value=location_str, inline=True)

        # Add top skills if detected
        if job.matched_keywords and len(job.matched_keywords) > 0:
            skills_str = ", ".join(job.matched_keywords[:8])  # Top 8 skills
            if len(job.matched_keywords) > 8:
                skills_str += f" +{len(job.matched_keywords) - 8} more"
            embed.add_field(name="🛠️ Skills", value=skills_str, inline=False)

        # Add company name if detected
        if job.company_name:
            embed.add_field(name="🏢 Company", value=job.company_name, inline=True)

        # Add footer with source
        embed.set_footer(text=f"Source: {job.source} | Posted at")

        try:
            # Save full job posting to database
            db = get_database()
            job_id = db.jobs.save(job)
            if job_id:
                logger.debug(f"Saved job to database: ID {job_id}")

            # Send to Discord
            await channel.send(embed=embed)
            logger.info(f"Sent job: {job.title[:50]}...")

            # Update legacy sent_posts tracking
            save_sent_post(job.url)
            self.reddit_stream.sent_posts.add(job.url)
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

        # Route commands to handler
        try:
            if command == "help":
                await self.command_handler.handle_help(message)
            elif command == "stats":
                await self.command_handler.handle_stats(message)
            elif command == "search":
                await self.command_handler.handle_search(message, args)
            elif command == "trends":
                await self.command_handler.handle_trends(message, args)
            elif command == "export":
                await self.command_handler.handle_export(message)
            elif command == "setchannel":
                await self.command_handler.handle_setchannel(self, message, args)
            elif command == "getchannel":
                await self.command_handler.handle_getchannel(self, message)
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

        # Load job channel from database
        db = get_database()
        self.job_channel_id = db.settings.get_int("job_channel_id")

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

        # Show enabled job sources
        source_names = [s.__class__.__name__.replace("Stream", "").replace("Monitor", "")
                       for s in self.job_sources]
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
                        source_name = source.__class__.__name__.replace("Stream", "")
                        logger.info(f"{source_name}: Found {len(jobs)} new jobs")
                    except Exception as e:
                        logger.error(f"Error scraping {source.__class__.__name__}: {e}")

                # Send all jobs to Discord
                logger.info(f"Total: {len(all_jobs)} jobs from all sources")
                for job in all_jobs:
                    await self.send_to_discord(job)
                    await asyncio.sleep(0.5)  # Avoid rate limits

            except Exception as e:
                logger.error(f"Error in scraping loop: {e}")

            await asyncio.sleep(CHECK_FREQUENCY_SECONDS)
