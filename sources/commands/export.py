"""!export command - Export recent jobs to CSV file."""

import csv
import io
from datetime import datetime
import discord
from data.database import get_database
from utils.logger import logger


async def handle_export(message: discord.Message) -> None:
    """Export recent jobs to CSV file."""
    db = get_database()
    jobs = db.jobs.get_recent(hours=24*30, limit=100)

    if not jobs:
        await message.channel.send("❌ No jobs to export.")
        return

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Title", "URL", "Subreddit", "Author", "Posted Date",
        "Salary Min", "Salary Max", "Currency", "Experience Level",
        "Company", "Location", "Remote", "Skills"
    ])

    # Write jobs
    for job in jobs:
        posted_date = datetime.utcfromtimestamp(job.created_utc).strftime("%Y-%m-%d %H:%M")
        skills = ", ".join(job.matched_keywords) if job.matched_keywords else ""

        writer.writerow([
            job.title,
            job.url,
            job.subreddit,
            job.author,
            posted_date,
            job.salary_min or "",
            job.salary_max or "",
            job.salary_currency or "USD",
            job.experience_level or "",
            job.company_name or "",
            job.location or "",
            "Yes" if job.is_remote else "No",
            skills
        ])

    # Send file
    output.seek(0)
    file = discord.File(io.BytesIO(output.getvalue().encode()), filename="jobs_export.csv")
    await message.channel.send(f"📤 Exported {len(jobs)} jobs to CSV:", file=file)
    logger.info(f"Exported {len(jobs)} jobs to CSV")
