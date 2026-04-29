"""Slash command definitions for Discord bot."""

import discord
from discord import app_commands
from typing import Optional, Literal

from utils.logger import logger
from .command_context import CommandContext
from .commands import CommandHandler


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

        logger.info("Slash commands registered successfully")
