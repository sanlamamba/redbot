"""Persistent action buttons attached to every job posting embed."""
import discord

from data.database import get_database
from utils.logger import logger


class JobActionsView(discord.ui.View):
    """Save / Applied / Dismiss buttons for a job posting.

    timeout=None makes the view persistent across bot restarts (Discord
    continues to route button interactions to the bot).  The view is
    registered in on_ready() so it survives restarts.
    """

    # Custom IDs are stable — changing them breaks in-flight interactions
    CUSTOM_ID_SAVE = "job:save"
    CUSTOM_ID_APPLY = "job:apply"
    CUSTOM_ID_DISMISS = "job:dismiss"

    def __init__(self, job_url: str = ""):
        super().__init__(timeout=None)
        # Store the job URL as instance state so button handlers can look it up.
        # For persisted views Discord re-creates the view from custom_id; the
        # URL is embedded in the button custom_id as a suffix.
        self._job_url = job_url

    # ------------------------------------------------------------------
    # Factory — called when attaching to a new embed
    # ------------------------------------------------------------------

    @classmethod
    def for_job(cls, job_url: str) -> "JobActionsView":
        view = cls(job_url=job_url)
        # Re-assign custom IDs to embed the URL so the handler can retrieve it
        # even after a bot restart (Discord passes back the full custom_id).
        # We truncate to 100 chars (Discord limit).
        suffix = f":{job_url}"[:95]
        view.save_button.custom_id = cls.CUSTOM_ID_SAVE + suffix
        view.apply_button.custom_id = cls.CUSTOM_ID_APPLY + suffix
        view.dismiss_button.custom_id = cls.CUSTOM_ID_DISMISS + suffix
        return view

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------

    @discord.ui.button(
        label="💾 Save",
        style=discord.ButtonStyle.secondary,
        custom_id=CUSTOM_ID_SAVE,
    )
    async def save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "saved", "💾 Job saved to your list!")

    @discord.ui.button(
        label="✅ Applied",
        style=discord.ButtonStyle.success,
        custom_id=CUSTOM_ID_APPLY,
    )
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "applied", "✅ Marked as applied!")

    @discord.ui.button(
        label="🙈 Dismiss",
        style=discord.ButtonStyle.danger,
        custom_id=CUSTOM_ID_DISMISS,
    )
    async def dismiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "dismissed", "🙈 Job dismissed — won't appear in your searches.")

    # ------------------------------------------------------------------

    async def _handle(
        self, interaction: discord.Interaction, action: str, message: str
    ) -> None:
        user_id = str(interaction.user.id)
        # Recover URL from custom_id suffix (format: "job:<action>:<url>")
        parts = interaction.data.get("custom_id", "").split(":", 2)
        job_url = parts[2] if len(parts) == 3 else self._job_url

        try:
            db = get_database()
            db.users.record_interaction(user_id, job_url, action)
        except Exception as e:
            logger.error(f"JobActionsView: error recording {action} for {user_id}: {e}")

        await interaction.response.send_message(message, ephemeral=True)
