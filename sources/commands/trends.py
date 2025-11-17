"""!trends command - Show job market trends over last 30 days."""

from statistics import median
import discord
from data.database import get_database
from parsers import ExperienceParser


async def handle_trends(message: discord.Message, trend_type: str, experience_parser: ExperienceParser) -> None:
    """Show trends over last 30 days."""
    if not trend_type:
        await message.channel.send("❌ Please specify trend type: `!trends salary`, `!trends keywords`, or `!trends subreddits`")
        return

    trend_type = trend_type.lower().strip()
    db = get_database()
    jobs = db.jobs.get_recent(hours=24*30, limit=10000)

    if not jobs:
        await message.channel.send("📈 No data available for the last 30 days.")
        return

    if trend_type == "salary":
        await _show_salary_trends(message, jobs, experience_parser)
    elif trend_type in ["keywords", "keyword"]:
        await _show_keyword_trends(message, jobs)
    elif trend_type in ["subreddits", "subreddit"]:
        await _show_subreddit_trends(message, jobs)
    else:
        await message.channel.send(f"❌ Unknown trend type: `{trend_type}`. Use: `salary`, `keywords`, or `subreddits`")


async def _show_salary_trends(message: discord.Message, jobs: list, experience_parser: ExperienceParser) -> None:
    """Show salary trends by experience level."""
    by_level = {}
    for job in jobs:
        if not (job.salary_min and job.experience_level):
            continue
        level = job.experience_level.split(",")[0].strip().lower()
        if level not in by_level:
            by_level[level] = []
        by_level[level].append(job.salary_min)

    if not by_level:
        await message.channel.send("📈 Not enough salary data to show trends.")
        return

    embed = discord.Embed(
        title="📈 Salary Trends (Last 30 Days)",
        description="Average and median salaries by experience level",
        color=discord.Color.gold()
    )

    for level in ["junior", "mid", "senior", "lead"]:
        if level not in by_level:
            continue
        salaries = by_level[level]
        avg = sum(salaries) // len(salaries)
        med = int(median(salaries))
        icon = experience_parser.get_icon(level) or ""
        embed.add_field(
            name=f"{icon} {level.title()} ({len(salaries)} jobs)",
            value=f"Avg: ${avg:,}/yr\nMedian: ${med:,}/yr",
            inline=True
        )

    await message.channel.send(embed=embed)


async def _show_keyword_trends(message: discord.Message, jobs: list) -> None:
    """Show most trending keywords."""
    keyword_counts = {}
    for job in jobs:
        if job.matched_keywords:
            for kw in job.matched_keywords:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

    if not keyword_counts:
        await message.channel.send("📈 No keyword data available.")
        return

    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    embed = discord.Embed(
        title="📈 Top Keywords (Last 30 Days)",
        description="Most in-demand skills and technologies",
        color=discord.Color.purple()
    )

    keywords_str = "\n".join([
        f"{i+1}. **{kw}** - {count} jobs ({count*100//len(jobs):.0f}%)"
        for i, (kw, count) in enumerate(top_keywords)
    ])
    embed.add_field(name=f"Top 10 (from {len(jobs)} jobs)", value=keywords_str, inline=False)

    await message.channel.send(embed=embed)


async def _show_subreddit_trends(message: discord.Message, jobs: list) -> None:
    """Show most active subreddits."""
    subreddit_counts = {}
    for job in jobs:
        subreddit_counts[job.subreddit] = subreddit_counts.get(job.subreddit, 0) + 1

    top_subreddits = sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    embed = discord.Embed(
        title="📈 Top Subreddits (Last 30 Days)",
        description="Most active job posting subreddits",
        color=discord.Color.orange()
    )

    subreddits_str = "\n".join([
        f"{i+1}. **r/{sub}** - {count} jobs ({count*100//len(jobs):.0f}%)"
        for i, (sub, count) in enumerate(top_subreddits)
    ])
    embed.add_field(name=f"Top 10 (from {len(jobs)} total)", value=subreddits_str, inline=False)

    await message.channel.send(embed=embed)
