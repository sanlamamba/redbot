"""Channel management commands."""

import discord
from typing import TYPE_CHECKING

from utils.logger import logger
from data.database import get_database
from sources.command_context import CommandContext

if TYPE_CHECKING:
    from sources.discord import DiscordBot


async def handle_setchannel(bot: "DiscordBot", ctx: CommandContext, args: str = "") -> None:
    """Set the channel where job postings will be sent.

    Usage: !setchannel [#channel or channel_id]
    If no argument provided, sets current channel as job channel.
    """
    if not ctx.has_manage_channels:
        await ctx.channel.send(
            "❌ You need **Manage Channels** permission to use this command."
        )
        return

    db = get_database()
    channel_id = None

    if args.strip():
        if ctx.channel_mentions:
            channel_id = ctx.channel_mentions[0].id
        else:
            try:
                channel_id = int(args.strip().replace("#", ""))
            except ValueError:
                await ctx.channel.send(
                    "❌ Invalid channel. Use `!setchannel #channel` or `!setchannel channel_id`"
                )
                return
    else:
        channel_id = ctx.channel.id

    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.channel.send(
            f"❌ Could not find channel with ID `{channel_id}`. Make sure the bot has access to it."
        )
        return

    if isinstance(channel, discord.TextChannel):
        permissions = channel.permissions_for(channel.guild.me)
        if not permissions.send_messages or not permissions.embed_links:
            await ctx.channel.send(
                f"❌ Bot doesn't have permission to send messages in {channel.mention}.\n"
                f"Required permissions: **Send Messages**, **Embed Links**"
            )
            return

    guild_id = str(ctx.guild.id) if ctx.guild else ""
    success = db.settings.set(
        "job_channel_id",
        str(channel_id),
        updated_by=str(ctx.author),
        guild_id=guild_id,
    )

    if success:
        bot.job_channel_id = channel_id

        embed = discord.Embed(
            title="✅ Job Channel Updated",
            description=f"Job postings will now be sent to {channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Channel ID", value=f"`{channel_id}`", inline=True)
        embed.add_field(name="Set by", value=ctx.author.mention, inline=True)

        await ctx.channel.send(embed=embed)
        logger.info(f"Job channel set to {channel_id} by {ctx.author}")
    else:
        await ctx.channel.send("❌ Failed to save channel setting. Check logs for details.")


async def handle_getchannel(bot: "DiscordBot", ctx: CommandContext) -> None:
    """Show the current job posting channel.

    Usage: !getchannel
    """
    db = get_database()
    guild_id = str(ctx.guild.id) if ctx.guild else ""
    channel_id = (
        db.settings.get_int("job_channel_id", guild_id=guild_id)
        or db.settings.get_int("job_channel_id", guild_id="")
    )

    if not channel_id:
        embed = discord.Embed(
            title="📢 Job Channel Status",
            description="No job channel configured yet.\n\nUse `!setchannel #channel` to set one.",
            color=discord.Color.orange()
        )
        await ctx.channel.send(embed=embed)
        return

    channel = bot.get_channel(channel_id)

    if channel:
        embed = discord.Embed(
            title="📢 Current Job Channel",
            description=f"Job postings are being sent to {channel.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Channel ID", value=f"`{channel_id}`", inline=True)
        embed.add_field(name="Channel Name", value=f"#{channel.name}", inline=True)

        if isinstance(channel, discord.TextChannel):
            permissions = channel.permissions_for(channel.guild.me)
            status = "✅" if permissions.send_messages and permissions.embed_links else "⚠️"
            embed.add_field(
                name="Bot Access",
                value=f"{status} {'Ready' if status == '✅' else 'Missing Permissions'}",
                inline=True
            )
    else:
        embed = discord.Embed(
            title="⚠️ Job Channel Not Found",
            description=f"Channel ID `{channel_id}` is configured but not accessible.\n\n"
                        f"The channel may have been deleted or the bot lost access.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Fix",
            value="Use `!setchannel #channel` to set a new channel",
            inline=False
        )

    await ctx.channel.send(embed=embed)
