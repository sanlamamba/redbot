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
            title="📚 RedBot Commands",
            description="Prefix commands (`!`) work everywhere. Slash commands (`/`) require Discord to sync.",
            color=discord.Color.blue(),
        )

        embed.add_field(name="── Job Discovery ──", value="​", inline=False)
        embed.add_field(name="!search / /search `<keyword>`",
                        value="Search recent jobs (reranked by your personal ML profile)", inline=False)
        embed.add_field(name="!stats / /stats",
                        value="Today's stats: total jobs, avg salary, top skills", inline=False)
        embed.add_field(name="!trends / /trends `salary|keywords|subreddits`",
                        value="30-day trends", inline=False)
        embed.add_field(name="!export / /export",
                        value="Download last 100 jobs as a CSV file", inline=False)

        embed.add_field(name="── Alerts & Preferences ──", value="​", inline=False)
        embed.add_field(name="/savedsearch add `name` `[keywords]` `[min_salary]` `[experience]` `[remote_only]`",
                        value="Create a saved search — you'll be DM'd when a match is posted", inline=False)
        embed.add_field(name="/savedsearch list / remove `name`",
                        value="View or delete your saved searches", inline=False)
        embed.add_field(name="/preferences set `key` `value`",
                        value="Keys: `min_salary`, `remote_only`, `experience`, `keywords`", inline=False)
        embed.add_field(name="/preferences view",
                        value="Show your current preferences", inline=False)

        embed.add_field(name="── Admin ──", value="​", inline=False)
        embed.add_field(name="!setchannel / /setchannel `[#channel]`",
                        value="🔧 Set job posting channel (defaults to current)", inline=False)
        embed.add_field(name="/addroute `#channel` `rule_type` `rule_value`",
                        value="🔧 Route matching jobs to a specific channel (types: keyword, subreddit, source, experience, remote)",
                        inline=False)
        embed.add_field(name="/listroutes / /removeroute `id`",
                        value="🔧 View or delete routing rules", inline=False)
        embed.add_field(name="/setmode `instant|digest`",
                        value="🔧 Instant = post immediately; digest = batch on a schedule", inline=False)
        embed.add_field(name="/setdigestfreq `hours`",
                        value="🔧 How often the digest is posted (1–168 h)", inline=False)
        embed.add_field(name="!getchannel / /getchannel",
                        value="Show current job posting channel", inline=False)

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
