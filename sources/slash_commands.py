"""Slash command definitions for Discord bot."""

import discord
from discord import app_commands
from typing import Optional, Literal

from utils.logger import logger
from .command_context import CommandContext
from .commands import CommandHandler
from .commands.preferences import (
    handle_preferences_view,
    handle_preferences_set,
    handle_savedsearch_add,
    handle_savedsearch_list,
    handle_savedsearch_remove,
)
from .commands.routing import handle_addroute, handle_listroutes, handle_removeroute
from .commands.digest import handle_setmode, handle_setdigestfreq


class SlashCommands:
    """Container for all slash command definitions."""

    def __init__(self, bot, command_handler: CommandHandler):
        self.bot = bot
        self.handler = command_handler

    def register_commands(self, tree: app_commands.CommandTree):
        """Register all slash commands with the command tree."""

        @tree.command(name="help", description="Show all available commands")
        async def help_command(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await self.handler.handle_help(ctx)

        @tree.command(name="stats", description="Show today's job statistics")
        async def stats_command(interaction: discord.Interaction):
            await interaction.response.defer()
            ctx = CommandContext.from_interaction(interaction)
            await self.handler.handle_stats(ctx)

        @tree.command(name="search", description="Search recent jobs by keyword")
        @app_commands.describe(keyword="The keyword to search for (e.g., python, javascript)")
        async def search_command(interaction: discord.Interaction, keyword: str):
            await interaction.response.defer()
            ctx = CommandContext.from_interaction(interaction)
            await self.handler.handle_search(ctx, keyword)

        @tree.command(name="trends", description="Show trends over last 30 days")
        @app_commands.describe(trend_type="Type of trend to display")
        async def trends_command(
            interaction: discord.Interaction,
            trend_type: Literal["salary", "keywords", "subreddits"]
        ):
            await interaction.response.defer()
            ctx = CommandContext.from_interaction(interaction)
            await self.handler.handle_trends(ctx, trend_type)

        @tree.command(name="export", description="Export last 100 jobs to CSV file")
        async def export_command(interaction: discord.Interaction):
            await interaction.response.defer()
            ctx = CommandContext.from_interaction(interaction)
            await self.handler.handle_export(ctx)

        @tree.command(name="setchannel", description="🔧 [Admin] Set job posting channel")
        @app_commands.describe(
            channel="Channel to post jobs to (leave empty to use current channel)"
        )
        @app_commands.checks.has_permissions(manage_channels=True)
        async def setchannel_command(
            interaction: discord.Interaction,
            channel: Optional[discord.TextChannel] = None
        ):
            await interaction.response.defer(ephemeral=True)
            mentions = [channel] if channel else []
            ctx = CommandContext.from_interaction(interaction, channel_mentions=mentions)
            channel_arg = str(channel.id) if channel else ""
            await self.handler.handle_setchannel(self.bot, ctx, channel_arg)

        @tree.command(name="getchannel", description="Show current job posting channel")
        async def getchannel_command(interaction: discord.Interaction):
            await interaction.response.defer()
            ctx = CommandContext.from_interaction(interaction)
            await self.handler.handle_getchannel(self.bot, ctx)

        # --- Preferences ---
        prefs_group = app_commands.Group(
            name="preferences", description="Manage your job alert preferences"
        )

        @prefs_group.command(name="view", description="View your current preferences")
        async def prefs_view(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_preferences_view(ctx)

        @prefs_group.command(name="set", description="Set a preference value")
        @app_commands.describe(
            key="Preference name (min_salary, remote_only, experience, keywords)",
            value="Value to set",
        )
        async def prefs_set(interaction: discord.Interaction, key: str, value: str):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_preferences_set(ctx, key, value)

        tree.add_command(prefs_group)

        # --- Saved searches ---
        search_group = app_commands.Group(
            name="savedsearch", description="Manage saved job search alerts"
        )

        @search_group.command(name="add", description="Add a saved search alert")
        @app_commands.describe(
            name="A short name for this search",
            keywords="Comma-separated keywords (e.g. python,django)",
            min_salary="Minimum annual salary",
            experience="Comma-separated levels (junior,mid,senior,lead)",
            remote_only="Only match remote jobs",
        )
        async def ss_add(
            interaction: discord.Interaction,
            name: str,
            keywords: str = "",
            min_salary: int = 0,
            experience: str = "",
            remote_only: bool = False,
        ):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_savedsearch_add(ctx, name, keywords, min_salary, experience, remote_only)

        @search_group.command(name="list", description="List your saved searches")
        async def ss_list(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_savedsearch_list(ctx)

        @search_group.command(name="remove", description="Remove a saved search")
        @app_commands.describe(name="Name of the saved search to remove")
        async def ss_remove(interaction: discord.Interaction, name: str):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_savedsearch_remove(ctx, name)

        tree.add_command(search_group)

        # --- Routing ---
        @tree.command(name="addroute", description="[Admin] Route jobs matching a rule to a channel")
        @app_commands.describe(
            channel="Target channel",
            rule_type="Match type: keyword, subreddit, source, experience, remote",
            rule_value="Value to match (e.g. 'python' for keyword, 'senior' for experience)",
            priority="Higher priority rules are evaluated first (default 0)",
        )
        @app_commands.checks.has_permissions(manage_channels=True)
        async def addroute_command(
            interaction: discord.Interaction,
            channel: discord.TextChannel,
            rule_type: str,
            rule_value: str = "",
            priority: int = 0,
        ):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_addroute(ctx, channel, rule_type, rule_value, priority)

        @tree.command(name="listroutes", description="List channel routing rules for this server")
        async def listroutes_command(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_listroutes(ctx)

        @tree.command(name="removeroute", description="[Admin] Remove a routing rule by ID")
        @app_commands.describe(rule_id="ID of the rule to remove (from /listroutes)")
        @app_commands.checks.has_permissions(manage_channels=True)
        async def removeroute_command(interaction: discord.Interaction, rule_id: int):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_removeroute(ctx, rule_id)

        # --- Notification mode ---
        @tree.command(name="setmode", description="[Admin] Set notification mode: instant or digest")
        @app_commands.describe(mode="instant = post immediately, digest = batch summary on a schedule")
        @app_commands.checks.has_permissions(manage_channels=True)
        async def setmode_command(
            interaction: discord.Interaction,
            mode: Literal["instant", "digest"],
        ):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_setmode(ctx, mode)

        @tree.command(name="setdigestfreq", description="[Admin] Set digest posting frequency in hours")
        @app_commands.describe(hours="Hours between digest posts (1–168)")
        @app_commands.checks.has_permissions(manage_channels=True)
        async def setdigestfreq_command(interaction: discord.Interaction, hours: int):
            await interaction.response.defer(ephemeral=True)
            ctx = CommandContext.from_interaction(interaction)
            await handle_setdigestfreq(ctx, hours)

        logger.info("Slash commands registered successfully")
