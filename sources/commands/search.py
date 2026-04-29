"""!search command - Search recent jobs by keyword."""

from data.database import get_database
from parsers import SalaryParser
from sources.command_context import CommandContext
from sources.embed_builder import EmbedBuilder, SearchPaginationView


async def handle_search(ctx: CommandContext, keyword: str, salary_parser: SalaryParser) -> None:
    """Search recent jobs by keyword."""
    if not keyword:
        await ctx.channel.send("❌ Please provide a keyword to search. Usage: `!search python`")
        return

    keyword = keyword.lower().strip()
    db = get_database()
    jobs = db.jobs.get_recent(hours=24 * 7, limit=1000)

    matching_jobs = [
        j for j in jobs
        if keyword in j.title.lower()
        or keyword in (j.description or "").lower()
        or (j.matched_keywords and keyword in [k.lower() for k in j.matched_keywords])
    ]

    if not matching_jobs:
        await ctx.channel.send(f"🔍 No jobs found matching keyword: `{keyword}`")
        return

    # Lazy-build a minimal EmbedBuilder (salary parser already available)
    from parsers import ExperienceParser, SentimentAnalyzer
    builder = EmbedBuilder(salary_parser, ExperienceParser(), SentimentAnalyzer())

    view = SearchPaginationView(matching_jobs, keyword, builder)
    await ctx.channel.send(embed=view.current_embed(), view=view)
