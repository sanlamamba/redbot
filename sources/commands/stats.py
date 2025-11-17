"""!stats command - Show today's job statistics."""

from datetime import datetime
import discord
from data.database import get_database
from parsers import ExperienceParser


async def handle_stats(message: discord.Message, experience_parser: ExperienceParser) -> None:
    """Show today's job statistics."""
    db = get_database()
    jobs = db.jobs.get_recent(hours=24, limit=1000)

    if not jobs:
        await message.channel.send("📊 No jobs found in the last 24 hours.")
        return

    # Calculate statistics
    total_jobs = len(jobs)
    salaries = [j.salary_min for j in jobs if j.salary_min]
    avg_salary = sum(salaries) // len(salaries) if salaries else 0

    # Top subreddit
    subreddit_counts = {}
    for j in jobs:
        subreddit_counts[j.subreddit] = subreddit_counts.get(j.subreddit, 0) + 1
    top_subreddit = max(subreddit_counts.items(), key=lambda x: x[1]) if subreddit_counts else ("N/A", 0)

    # Top keywords
    keyword_counts = {}
    for j in jobs:
        if j.matched_keywords:
            for kw in j.matched_keywords:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Remote jobs
    remote_count = sum(1 for j in jobs if j.is_remote)
    remote_pct = (remote_count / total_jobs * 100) if total_jobs > 0 else 0

    # Create embed
    embed = discord.Embed(
        title="📊 Today's Job Statistics (Last 24 Hours)",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )

    embed.add_field(name="Total Jobs", value=f"{total_jobs}", inline=True)
    embed.add_field(
        name="Avg Salary",
        value=f"${avg_salary:,}/year" if avg_salary > 0 else "N/A",
        inline=True
    )
    embed.add_field(name="Remote Jobs", value=f"{remote_count} ({remote_pct:.1f}%)", inline=True)
    embed.add_field(
        name="Top Subreddit",
        value=f"r/{top_subreddit[0]} ({top_subreddit[1]} jobs)",
        inline=False
    )

    if top_keywords:
        keywords_str = "\n".join([f"{i+1}. {kw} ({count} jobs)" for i, (kw, count) in enumerate(top_keywords)])
        embed.add_field(name="Top Keywords", value=keywords_str, inline=False)

    await message.channel.send(embed=embed)
