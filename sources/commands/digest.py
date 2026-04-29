"""Digest mode command handler."""
import discord
from data.database import get_database
from sources.command_context import CommandContext


async def handle_setmode(ctx: CommandContext, mode: str) -> None:
    """Set instant or digest notification mode for this guild."""
    if mode not in ("instant", "digest"):
        await ctx.channel.send("❌ Valid modes: `instant` (post immediately) or `digest` (batched summary).")
        return

    guild_id = str(ctx.guild.id) if ctx.guild else ""
    db = get_database()
    db.settings.set("notification_mode", mode, guild_id=guild_id)

    if mode == "instant":
        await ctx.channel.send("✅ Notification mode set to **instant** — jobs will be posted as they arrive.")
    else:
        freq = db.settings.get_int("digest_frequency_hours", guild_id=guild_id) or 24
        await ctx.channel.send(
            f"✅ Notification mode set to **digest** — jobs will be batched and posted every "
            f"**{freq}h**. Use `/setdigestfreq` to adjust the interval."
        )


async def handle_setdigestfreq(ctx: CommandContext, hours: int) -> None:
    """Set how often the digest is posted (hours)."""
    if hours < 1 or hours > 168:
        await ctx.channel.send("❌ Frequency must be between 1 and 168 hours.")
        return

    guild_id = str(ctx.guild.id) if ctx.guild else ""
    db = get_database()
    db.settings.set("digest_frequency_hours", str(hours), guild_id=guild_id)
    await ctx.channel.send(f"✅ Digest will be posted every **{hours}h**.")
