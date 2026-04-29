"""!search command - Search recent jobs by keyword."""

from data.database import get_database
from parsers import SalaryParser
from sources.command_context import CommandContext
from sources.embed_builder import EmbedBuilder, SearchPaginationView
from core.ml_ranker import get_ranker, load_profile_from_db


async def handle_search(ctx: CommandContext, keyword: str, salary_parser: SalaryParser) -> None:
    """Search recent jobs by keyword, reranked by the user's ML profile."""
    if not keyword:
        await ctx.channel.send("❌ Please provide a keyword to search. Usage: `!search python`")
        return

    keyword = keyword.lower().strip()
    db = get_database()
    jobs = db.jobs.get_recent(hours=24 * 7, limit=1000)
    user_id = str(ctx.author.id)

    # Filter dismissed jobs for this user
    dismissed = db.users.get_dismissed_urls(user_id)

    matching_jobs = [
        j for j in jobs
        if j.url not in dismissed
        and (
            keyword in j.title.lower()
            or keyword in (j.description or "").lower()
            or (j.matched_keywords and keyword in [k.lower() for k in j.matched_keywords])
        )
    ]

    if not matching_jobs:
        await ctx.channel.send(f"🔍 No jobs found matching keyword: `{keyword}`")
        return

    # Rerank by ML relevance score if user has enough interaction history
    ranker = get_ranker()
    if not ranker.has_profile(user_id):
        load_profile_from_db(ranker, user_id, db)

    if ranker.has_profile(user_id):
        matching_jobs.sort(key=lambda j: ranker.score(user_id, j), reverse=True)

    from parsers import ExperienceParser, SentimentAnalyzer
    builder = EmbedBuilder(salary_parser, ExperienceParser(), SentimentAnalyzer())

    view = SearchPaginationView(matching_jobs, keyword, builder)
    await ctx.channel.send(embed=view.current_embed(), view=view)
