"""Slash command definitions for Discord bot."""

import discord
from discord import app_commands
from typing import Optional, Literal

from utils.logger import logger
from .commands import CommandHandler


class SlashCommands:
    """Container for all slash command definitions."""

    def __init__(self, bot, command_handler: CommandHandler):
        """Initialize slash commands.

        Args:
            bot: Discord bot instance
            command_handler: Command handler instance
        """
        self.bot = bot
        self.handler = command_handler

    def register_commands(self, tree: app_commands.CommandTree):
        """Register all slash commands with the command tree.

        Args:
            tree: Discord command tree
        """

        @tree.command(name="help", description="Show all available commands")
        async def help_command(interaction: discord.Interaction):
            """Show help message."""
            await interaction.response.defer(ephemeral=True)

            # Create a fake message object for the handler
            class FakeMessage:
                def __init__(self, interaction):
                    self.channel = interaction.channel
                    self.author = interaction.user
                    self.guild = interaction.guild

            fake_msg = FakeMessage(interaction)
            await self.handler.handle_help(fake_msg)

            await interaction.followup.send("✓ Help sent to channel", ephemeral=True)

        @tree.command(name="stats", description="Show today's job statistics")
        async def stats_command(interaction: discord.Interaction):
            """Show statistics."""
            await interaction.response.defer()

            class FakeMessage:
                def __init__(self, interaction):
                    self.channel = interaction.channel
                    self.author = interaction.user
                    self.guild = interaction.guild

            fake_msg = FakeMessage(interaction)
            await self.handler.handle_stats(fake_msg)

            await interaction.followup.send("✓ Stats displayed above", ephemeral=True)

        @tree.command(name="search", description="Search recent jobs by keyword")
        @app_commands.describe(keyword="The keyword to search for (e.g., python, javascript)")
        async def search_command(interaction: discord.Interaction, keyword: str):
            """Search jobs by keyword."""
            await interaction.response.defer()

            class FakeMessage:
                def __init__(self, interaction):
                    self.channel = interaction.channel
                    self.author = interaction.user
                    self.guild = interaction.guild

            fake_msg = FakeMessage(interaction)
            await self.handler.handle_search(fake_msg, keyword)

            await interaction.followup.send(f"✓ Search results for '{keyword}' displayed above", ephemeral=True)

        @tree.command(name="trends", description="Show trends over last 30 days")
        @app_commands.describe(
            trend_type="Type of trend to display"
        )
        async def trends_command(
            interaction: discord.Interaction,
            trend_type: Literal["salary", "keywords", "subreddits"]
        ):
            """Show trends."""
            await interaction.response.defer()

            class FakeMessage:
                def __init__(self, interaction):
                    self.channel = interaction.channel
                    self.author = interaction.user
                    self.guild = interaction.guild

            fake_msg = FakeMessage(interaction)
            await self.handler.handle_trends(fake_msg, trend_type)

            await interaction.followup.send(f"✓ {trend_type.title()} trends displayed above", ephemeral=True)

        @tree.command(name="export", description="Export last 100 jobs to CSV file")
        async def export_command(interaction: discord.Interaction):
            """Export jobs to CSV."""
            await interaction.response.defer()

            class FakeMessage:
                def __init__(self, interaction):
                    self.channel = interaction.channel
                    self.author = interaction.user
                    self.guild = interaction.guild

            fake_msg = FakeMessage(interaction)
            await self.handler.handle_export(fake_msg)

            await interaction.followup.send("✓ Export sent above", ephemeral=True)

        @tree.command(name="setchannel", description="🔧 [Admin] Set job posting channel")
        @app_commands.describe(
            channel="Channel to post jobs to (leave empty to use current channel)"
        )
        @app_commands.checks.has_permissions(manage_channels=True)
        async def setchannel_command(
            interaction: discord.Interaction,
            channel: Optional[discord.TextChannel] = None
        ):
            """Set job posting channel."""
            await interaction.response.defer(ephemeral=True)

            # Determine channel ID
            if channel:
                channel_arg = str(channel.id)
            else:
                channel_arg = ""  # Will use current channel in handler

            class FakeMessage:
                def __init__(self, interaction, ch):
                    self.channel = interaction.channel
                    self.author = interaction.user
                    self.guild = interaction.guild
                    self.channel_mentions = [ch] if ch else []

            fake_msg = FakeMessage(interaction, channel)
            await self.handler.handle_setchannel(self.bot, fake_msg, channel_arg)

            await interaction.followup.send(
                "✓ Channel configuration updated (see above for details)",
                ephemeral=True
            )

        @tree.command(name="getchannel", description="Show current job posting channel")
        async def getchannel_command(interaction: discord.Interaction):
            """Get current job posting channel."""
            await interaction.response.defer()

            class FakeMessage:
                def __init__(self, interaction):
                    self.channel = interaction.channel
                    self.author = interaction.user
                    self.guild = interaction.guild

            fake_msg = FakeMessage(interaction)
            await self.handler.handle_getchannel(self.bot, fake_msg)

            await interaction.followup.send("✓ Channel info displayed above", ephemeral=True)

        logger.info("Slash commands registered successfully")
