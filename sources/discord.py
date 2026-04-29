"""
Module Name: discord_bot
Description: This module defines the DiscordBot class, which interacts with the Discord API
to send new Reddit submissions to a specified Discord channel.
"""

import asyncio
import time
import discord
from discord import app_commands

from utils.constants import CHECK_FREQUENCY_SECONDS
from utils.logger import logger
from utils.rate_limiter import RateLimiter
from data.database import get_database
from data.models.job import JobPosting
from core.dedup import DeduplicationService
from core.routing import RoutingEngine
from parsers import SalaryParser, ExperienceParser, SentimentAnalyzer
from .reddit import RedditStream
from .command_context import CommandContext
from .commands import CommandHandler
from .slash_commands import SlashCommands
from .embed_builder import EmbedBuilder
from .views import JobActionsView


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
        self.routing = RoutingEngine()
        # Rate-limit DMs: max 5 per user per minute to avoid Discord limits
        self._dm_limiter = RateLimiter(max_calls=5, window_seconds=60)
        # Digest mode: per-guild pending job lists
        self._pending_digest: dict[str, list] = {}  # guild_id → [JobPosting, ...]

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
        """Send a job posting to the Discord channel with enhanced information."""
        if self.dedup.is_duplicate(job):
            logger.debug(f"Skipping duplicate job: {job.url}")
            return

        if not self.job_channel_id:
            logger.warning("No job channel configured, skipping job posting")
            return

        db = get_database()
        guild = self.guilds[0] if self.guilds else None
        guild_id = str(guild.id) if guild else ""

        # Check notification mode — digest mode buffers instead of sending immediately
        mode = db.settings.get("notification_mode", guild_id=guild_id) or "instant"
        if mode == "digest":
            self._pending_digest.setdefault(guild_id, []).append(job)
            self.dedup.mark_seen(job)  # prevent re-queuing on next scrape cycle
            logger.debug(f"Digest: queued '{job.title[:40]}' for guild {guild_id}")
            return

        await self._deliver_job(job, guild, guild_id, db)

    async def _deliver_job(self, job, guild, guild_id, db) -> None:
        """Immediately deliver a single job embed to all routed channels."""
        rules = db.routes.get_rules(guild_id) if guild_id else []
        target_ids = self.routing.resolve(job, rules, self.job_channel_id)
        embed = self.embed_builder.build_job_embed(job)

        try:
            job_db_id = db.jobs.save(job)
            if job_db_id:
                logger.debug(f"Saved job to database: ID {job_db_id}")
            else:
                # Job already existed — retrieve its ID for the action buttons
                job_db_id = db.jobs.get_id_by_url(job.url) or 0

            view = JobActionsView.for_job(job_db_id)
            sent = False
            for channel_id in target_ids:
                ch = self.get_channel(channel_id)
                if ch is None:
                    logger.warning(f"Channel {channel_id} not found, skipping")
                    continue
                await ch.send(embed=embed, view=view)
                sent = True

            if sent:
                logger.info(f"Sent job to {len(target_ids)} channel(s): {job.title[:50]}...")
                self.dedup.mark_seen(job)
                if guild:
                    await self._send_dm_alerts(job, guild)
            else:
                logger.warning(f"No reachable channels for job: {job.title[:50]}")
        except Exception as e:
            logger.error(f"Error sending message to Discord: {e}")

    async def _send_dm_alerts(self, job: JobPosting, guild: discord.Guild) -> None:
        """DM any guild member whose saved search matches the job."""
        db = get_database()
        searches = db.users.get_all_saved_searches_for_guild(str(guild.id))
        if not searches:
            return

        alerted: set[str] = set()
        for search in searches:
            if search.user_id in alerted:
                continue
            if not search.matches(job):
                continue
            if db.users.is_dm_disabled(search.user_id):
                continue
            if not self._dm_limiter.is_allowed(search.user_id):
                logger.debug(f"DM rate-limited for user {search.user_id}")
                continue

            try:
                member = guild.get_member(int(search.user_id))
                if member is None:
                    continue
                embed = self.embed_builder.build_job_embed(job)
                embed.set_footer(
                    text=f"Matched your saved search: {search.name} | Source: {job.source}"
                )
                await member.send(
                    content=f"🔔 New job matching **{search.name}**:", embed=embed
                )
                alerted.add(search.user_id)
                logger.debug(f"DM alert sent to {member} for search '{search.name}'")
            except discord.Forbidden:
                logger.debug(f"DM disabled for user {search.user_id}, marking")
                db.users.mark_dm_disabled(search.user_id)
            except Exception as e:
                logger.error(f"Error sending DM alert to {search.user_id}: {e}")

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """Handle persistent job action button interactions.

        discord.py's CommandTree and registered persistent views are dispatched
        via the internal ConnectionState before this event fires.  We use this
        hook to handle 'job:*' component interactions whose dynamic DB-ID suffix
        can't be matched by discord.py's exact custom_id persistence mechanism.
        """
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = (interaction.data or {}).get("custom_id", "")
        if not custom_id.startswith("job:"):
            return

        parts = custom_id.split(":", 2)
        if len(parts) != 3:
            return
        _, action, _ = parts

        _ACTIONS = {
            "save":    ("saved",     "💾 Job saved to your list!"),
            "apply":   ("applied",   "✅ Marked as applied!"),
            "dismiss": ("dismissed", "🙈 Dismissed — won't appear in your searches."),
        }
        if action not in _ACTIONS:
            return

        db_action, message_text = _ACTIONS[action]
        view = JobActionsView()
        await view._handle(interaction, db_action, message_text)

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

        # No add_view() needed for job buttons — they're handled in on_interaction
        # below via custom_id prefix matching, which discord.py's exact-match
        # persistent view registration can't do for dynamic IDs.

        logger.info("="*70)
        logger.info("Bot ready! Monitoring for jobs...")
        logger.info("="*70)

        await asyncio.gather(
            self.bulk_delete(),
            self.start_scraping_jobs(),
            self._digest_loop(),
        )

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

    async def _digest_loop(self) -> None:
        """Background task: flush pending digest jobs on a per-guild schedule."""
        _CHECK_INTERVAL = 300  # poll every 5 min; actual flush honours configured frequency

        while not self.is_closed():
            await asyncio.sleep(_CHECK_INTERVAL)
            db = get_database()

            for guild in self.guilds:
                guild_id = str(guild.id)
                mode = db.settings.get("notification_mode", guild_id=guild_id) or "instant"
                if mode != "digest":
                    continue

                pending = self._pending_digest.get(guild_id, [])
                if not pending:
                    continue

                freq_hours = db.settings.get_int("digest_frequency_hours", guild_id=guild_id) or 24
                last_ts = db.settings.get_int("digest_last_sent", guild_id=guild_id) or 0
                if time.time() - last_ts < freq_hours * 3600:
                    continue

                # Flush
                jobs_to_send = pending[:]
                self._pending_digest[guild_id] = []
                db.settings.set("digest_last_sent", str(int(time.time())), guild_id=guild_id)

                await self._post_digest(jobs_to_send, guild, guild_id, db)

    async def _post_digest(self, jobs, guild, guild_id, db) -> None:
        """Post a digest summary embed followed by individual job embeds."""
        if not self.job_channel_id:
            return

        # Sort by priority score descending, cap at 20 per digest
        jobs.sort(key=lambda j: j.priority_score or 0, reverse=True)
        jobs = jobs[:20]

        # Summary embed
        rules = db.routes.get_rules(guild_id)
        target_ids = self.routing.resolve(jobs[0], rules, self.job_channel_id) if jobs else [self.job_channel_id]
        ch = self.get_channel(target_ids[0])
        if ch is None:
            return

        summary = discord.Embed(
            title=f"📋 Job Digest — {len(jobs)} new job{'s' if len(jobs) != 1 else ''}",
            description="\n".join(f"• [{j.title[:60]}]({j.url})" for j in jobs[:10])
            + (f"\n…and {len(jobs) - 10} more" if len(jobs) > 10 else ""),
            color=discord.Color.dark_blue(),
        )
        await ch.send(embed=summary)

        # Individual embeds
        for job in jobs:
            await self._deliver_job(job, guild, guild_id, db)
            await asyncio.sleep(0.5)

        logger.info(f"Posted digest of {len(jobs)} jobs for guild {guild_id}")
