"""Embed construction for job postings and search results."""
from datetime import datetime
from typing import List, Optional

import discord

from data.models.job import JobPosting
from parsers.salary import SalaryParser, SalaryInfo
from parsers.experience import ExperienceParser
from parsers.sentiment import SentimentAnalyzer

_PER_PAGE = 5


class EmbedBuilder:
    """Build Discord embeds from JobPosting data."""

    def __init__(
        self,
        salary_parser: SalaryParser,
        experience_parser: ExperienceParser,
        sentiment_analyzer: SentimentAnalyzer,
    ):
        self._salary = salary_parser
        self._exp = experience_parser
        self._sentiment = sentiment_analyzer

    # ------------------------------------------------------------------
    # Job posting embed
    # ------------------------------------------------------------------

    def build_job_embed(self, job: JobPosting) -> discord.Embed:
        color = self._embed_color(job)

        title = job.title[:200]
        if job.experience_level:
            icon = self._exp.get_icon(job.experience_level.split(",")[0].strip())
            if icon:
                title = f"{icon} {title}"

        description = (
            job.description[:300] + "..."
            if job.description and len(job.description) > 300
            else job.description or "No description provided"
        )

        if job.red_flags:
            warnings = self._sentiment.format_warnings(
                {"red_flags": job.red_flags, "warnings": []}
            )
            if warnings:
                description = f"⚠️ **{warnings}**\n\n{description}"

        embed = discord.Embed(
            title=title,
            url=job.url,
            description=description,
            color=color,
            timestamp=datetime.utcfromtimestamp(job.created_utc),
        )

        if job.author:
            embed.set_author(name=job.author)
        if job.subreddit:
            embed.add_field(name="Subreddit", value=f"r/{job.subreddit}", inline=True)

        embed.add_field(name="🕒 Posted", value=self._posted_field(job.created_utc), inline=True)

        salary_str = self._format_salary(job)
        if salary_str:
            embed.add_field(name="💰 Salary", value=salary_str, inline=True)

        if job.experience_level:
            levels = job.experience_level.split(", ")
            formatted = self._exp.format_levels(levels) or job.experience_level
            embed.add_field(name="📊 Level", value=formatted, inline=True)

        if job.location or job.is_remote:
            location_str = job.location or ""
            if job.is_remote:
                location_str = "🌍 Remote" + (f" ({location_str})" if location_str else "")
            if location_str:
                embed.add_field(name="📍 Location", value=location_str, inline=True)

        if job.matched_keywords:
            skills_str = ", ".join(job.matched_keywords[:8])
            if len(job.matched_keywords) > 8:
                skills_str += f" +{len(job.matched_keywords) - 8} more"
            embed.add_field(name="🛠️ Skills", value=skills_str, inline=False)

        if job.company_name:
            embed.add_field(name="🏢 Company", value=job.company_name, inline=True)

        embed.set_footer(text=f"Source: {job.source} | Posted at")
        return embed

    # ------------------------------------------------------------------
    # Search results embed
    # ------------------------------------------------------------------

    def build_search_embed(
        self, jobs: List[JobPosting], keyword: str, page: int, total: int
    ) -> discord.Embed:
        total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)
        start = page * _PER_PAGE
        page_jobs = jobs[start : start + _PER_PAGE]

        embed = discord.Embed(
            title=f"🔍 Search Results: '{keyword}'",
            description=f"Found {total} job{'s' if total != 1 else ''}.",
            color=discord.Color.blue(),
        )

        for i, job in enumerate(page_jobs, start=start + 1):
            salary_str = self._format_salary(job)
            suffix = f" | {salary_str}" if salary_str else ""
            value = f"[{job.title[:80]}]({job.url})\nr/{job.subreddit}{suffix}"
            embed.add_field(name=f"{i}.", value=value, inline=False)

        embed.set_footer(text=f"Page {page + 1}/{total_pages}")
        return embed

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _embed_color(self, job: JobPosting) -> discord.Color:
        score = job.priority_score or 0
        if score >= 80:
            return discord.Color.gold()      # top 20%
        if score >= 50:
            return discord.Color.blue()      # top 50%
        if score >= 30:
            return discord.Color.orange()    # some concerns
        return discord.Color.dark_gray()     # bottom 20% / suspicious

    def _format_salary(self, job: JobPosting) -> Optional[str]:
        if not job.salary_min and not job.salary_max:
            return None
        info = SalaryInfo(
            min=job.salary_min,
            max=job.salary_max,
            currency=job.salary_currency or "USD",
            period=job.salary_period or "yearly",
        )
        return self._salary.format_salary(info)

    @staticmethod
    def _posted_field(created_utc: int) -> str:
        posted = datetime.utcfromtimestamp(created_utc)
        diff = datetime.utcnow() - posted
        if diff.days > 0:
            relative = f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds >= 3600:
            h = diff.seconds // 3600
            relative = f"{h} hour{'s' if h != 1 else ''} ago"
        elif diff.seconds >= 60:
            m = diff.seconds // 60
            relative = f"{m} minute{'s' if m != 1 else ''} ago"
        else:
            relative = "just now"
        absolute = posted.strftime("%Y-%m-%d %H:%M UTC")
        return f"{relative}\n({absolute})"


class SearchPaginationView(discord.ui.View):
    """Paginated view for search results."""

    def __init__(
        self,
        jobs: List[JobPosting],
        keyword: str,
        embed_builder: EmbedBuilder,
        page: int = 0,
    ):
        super().__init__(timeout=120)
        self._jobs = jobs
        self._keyword = keyword
        self._builder = embed_builder
        self._page = page
        self._total_pages = max(1, (len(jobs) + _PER_PAGE - 1) // _PER_PAGE)
        self._refresh_buttons()

    def _refresh_buttons(self) -> None:
        self.prev_button.disabled = self._page == 0
        self.next_button.disabled = self._page >= self._total_pages - 1

    def current_embed(self) -> discord.Embed:
        return self._builder.build_search_embed(
            self._jobs, self._keyword, self._page, len(self._jobs)
        )

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._page = max(0, self._page - 1)
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._page = min(self._total_pages - 1, self._page + 1)
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)
