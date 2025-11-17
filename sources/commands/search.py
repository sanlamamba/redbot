"""!search command - Search recent jobs by keyword."""

import discord
from data.database import get_database
from parsers import SalaryParser


async def handle_search(message: discord.Message, keyword: str, salary_parser: SalaryParser) -> None:
    """Search recent jobs by keyword."""
    if not keyword:
        await message.channel.send("❌ Please provide a keyword to search. Usage: `!search python`")
        return

    keyword = keyword.lower().strip()
    db = get_database()
    jobs = db.jobs.get_recent(hours=24*7, limit=1000)

    # Filter by keyword
    matching_jobs = [
        j for j in jobs
        if keyword in j.title.lower() or
           keyword in (j.description or "").lower() or
           (j.matched_keywords and keyword in [k.lower() for k in j.matched_keywords])
    ]

    if not matching_jobs:
        await message.channel.send(f"🔍 No jobs found matching keyword: `{keyword}`")
        return

    # Show first 5 results
    embed = discord.Embed(
        title=f"🔍 Search Results: '{keyword}'",
        description=f"Found {len(matching_jobs)} jobs. Showing top 5:",
        color=discord.Color.blue()
    )

    for i, job in enumerate(matching_jobs[:5]):
        salary_str = ""
        if job.salary_min or job.salary_max:
            salary_info = type('obj', (object,), {
                'min': job.salary_min,
                'max': job.salary_max,
                'currency': job.salary_currency or 'USD',
                'period': job.salary_period or 'yearly'
            })()
            salary_str = f" | {salary_parser.format_salary(salary_info)}"

        value = f"[{job.title[:80]}]({job.url})\nr/{job.subreddit}{salary_str}"
        embed.add_field(name=f"{i+1}.", value=value, inline=False)

    if len(matching_jobs) > 5:
        embed.set_footer(text=f"+ {len(matching_jobs) - 5} more jobs matching '{keyword}'")

    await message.channel.send(embed=embed)
