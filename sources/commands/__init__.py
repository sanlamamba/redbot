"""Command handlers for Discord bot - modular command routing."""

import discord
from parsers import SalaryParser, ExperienceParser
from sources.command_context import CommandContext
from .stats import handle_stats
from .search import handle_search
from .trends import handle_trends
from .export import handle_export
from .channel import handle_setchannel, handle_getchannel


class CommandHandler:
    """Routes commands to appropriate handlers."""

    def __init__(self, salary_parser: SalaryParser, experience_parser: ExperienceParser):
        self.salary_parser = salary_parser
        self.experience_parser = experience_parser

    async def handle_help(self, ctx: CommandContext) -> None:
        """Show available commands."""
        embed = discord.Embed(
            title="📚 Available Commands",
            description="Here are the commands you can use:",
            color=discord.Color.blue()
        )

        embed.add_field(name="!help", value="Show this help message", inline=False)
        embed.add_field(
            name="!stats",
            value="Show today's job statistics (total jobs, avg salary, top keywords)",
            inline=False
        )
        embed.add_field(
            name="!search <keyword>",
            value="Search recent jobs by keyword (e.g., `!search python`)",
            inline=False
        )
        embed.add_field(
            name="!trends <type>",
            value="Show trends over last 30 days\nTypes: `salary`, `keywords`, `subreddits`",
            inline=False
        )
        embed.add_field(name="!export", value="Export last 100 jobs to CSV file", inline=False)
        embed.add_field(
            name="!setchannel [#channel]",
            value="🔧 **[Admin]** Set job posting channel (defaults to current channel)",
            inline=False
        )
        embed.add_field(
            name="!getchannel",
            value="Show current job posting channel",
            inline=False
        )

        await ctx.channel.send(embed=embed)

    async def handle_stats(self, ctx: CommandContext) -> None:
        await handle_stats(ctx, self.experience_parser)

    async def handle_search(self, ctx: CommandContext, keyword: str) -> None:
        await handle_search(ctx, keyword, self.salary_parser)

    async def handle_trends(self, ctx: CommandContext, trend_type: str) -> None:
        await handle_trends(ctx, trend_type, self.experience_parser)

    async def handle_export(self, ctx: CommandContext) -> None:
        await handle_export(ctx)

    async def handle_setchannel(self, bot, ctx: CommandContext, args: str) -> None:
        await handle_setchannel(bot, ctx, args)

    async def handle_getchannel(self, bot, ctx: CommandContext) -> None:
        await handle_getchannel(bot, ctx)
