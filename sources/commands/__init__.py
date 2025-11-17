"""Command handlers for Discord bot - modular command routing."""

import discord
from parsers import SalaryParser, ExperienceParser
from .stats import handle_stats
from .search import handle_search
from .trends import handle_trends
from .export import handle_export


class CommandHandler:
    """Routes commands to appropriate handlers."""

    def __init__(self, salary_parser: SalaryParser, experience_parser: ExperienceParser):
        self.salary_parser = salary_parser
        self.experience_parser = experience_parser

    async def handle_help(self, message: discord.Message) -> None:
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
        await message.channel.send(embed=embed)

    async def handle_stats(self, message: discord.Message) -> None:
        await handle_stats(message, self.experience_parser)

    async def handle_search(self, message: discord.Message, keyword: str) -> None:
        await handle_search(message, keyword, self.salary_parser)

    async def handle_trends(self, message: discord.Message, trend_type: str) -> None:
        await handle_trends(message, trend_type, self.experience_parser)

    async def handle_export(self, message: discord.Message) -> None:
        await handle_export(message)
