"""Persistent action buttons attached to every job posting embed.

Custom ID format: "job:<action>:<db_id>" where db_id is the integer
primary key from job_postings.  This stays well under Discord's 100-char
custom_id limit (max ~30 chars) and survives URL changes or truncation.
"""
import discord

from data.database import get_database
from utils.logger import logger

# Prefix shared across all job action buttons — used by the persistent view
# registration in on_ready() to route interactions to this class.
_PREFIX = "job:"


def _custom_id(action: str, job_db_id: int) -> str:
    return f"job:{action}:{job_db_id}"


class JobActionsView(discord.ui.View):
    """Save / Applied / Dismiss buttons for a job posting.

    timeout=None makes the view persistent across bot restarts.
    The view is re-registered in on_ready() so Discord can route
    button interactions even after a restart.
    """

    def __init__(self, job_db_id: int = 0):
        super().__init__(timeout=None)
        self._job_db_id = job_db_id

    # ------------------------------------------------------------------
    # Factory — called when attaching to a new embed
    # ------------------------------------------------------------------

    @classmethod
    def for_job(cls, job_db_id: int) -> "JobActionsView":
        """Create a view wired to a specific job's DB row."""
        view = cls(job_db_id=job_db_id)
        view.save_button.custom_id = _custom_id("save", job_db_id)
        view.apply_button.custom_id = _custom_id("apply", job_db_id)
        view.dismiss_button.custom_id = _custom_id("dismiss", job_db_id)
        return view

    # ------------------------------------------------------------------
    # Buttons (default custom_ids used by the persistent registration)
    # ------------------------------------------------------------------

    @discord.ui.button(
        label="💾 Save",
        style=discord.ButtonStyle.secondary,
        custom_id="job:save:0",
    )
    async def save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "saved", "💾 Job saved to your list!")

    @discord.ui.button(
        label="✅ Applied",
        style=discord.ButtonStyle.success,
        custom_id="job:apply:0",
    )
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "applied", "✅ Marked as applied!")

    @discord.ui.button(
        label="🙈 Dismiss",
        style=discord.ButtonStyle.danger,
        custom_id="job:dismiss:0",
    )
    async def dismiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "dismissed", "🙈 Dismissed — won't appear in your searches.")

    # ------------------------------------------------------------------

    async def _handle(self, interaction: discord.Interaction, action: str, message: str) -> None:
        user_id = str(interaction.user.id)

        # Parse DB ID from custom_id: "job:<action>:<db_id>"
        raw_id = interaction.data.get("custom_id", "").rsplit(":", 1)[-1]
        try:
            db_id = int(raw_id)
        except ValueError:
            db_id = self._job_db_id

        try:
            db = get_database()
            # Resolve the canonical URL from the DB so interactions are
            # always recorded against a full, uncorrupted URL.
            job = db.jobs.get_by_id(db_id) if db_id else None
            job_url = job.url if job else f"job_id:{db_id}"
            db.users.record_interaction(user_id, job_url, action)
        except Exception as e:
            logger.error(f"JobActionsView: error recording {action} for {user_id}: {e}")

        await interaction.response.send_message(message, ephemeral=True)
