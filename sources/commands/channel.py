"""Channel management commands."""

import discord
from typing import TYPE_CHECKING

from utils.logger import logger
from data.database import get_database

if TYPE_CHECKING:
    from sources.discord import DiscordBot


async def handle_setchannel(bot: "DiscordBot", message: discord.Message, args: str = "") -> None:
    """Set the channel where job postings will be sent.

    Usage: !setchannel [#channel or channel_id]
    If no argument provided, sets current channel as job channel.

    Args:
        bot: Discord bot instance
        message: Discord message that triggered the command
        args: Optional channel mention or ID
    """
    # Check if user has manage channels permission
    if not message.author.guild_permissions.manage_channels:
        await message.channel.send(
            "❌ You need **Manage Channels** permission to use this command."
        )
        return

    db = get_database()
    channel_id = None

    # Parse channel from arguments
    if args.strip():
        # Check if it's a channel mention
        if message.channel_mentions:
            channel_id = message.channel_mentions[0].id
        else:
            # Try to parse as channel ID
            try:
                channel_id = int(args.strip().replace("#", ""))
            except ValueError:
                await message.channel.send(
                    "❌ Invalid channel. Use `!setchannel #channel` or `!setchannel channel_id`"
                )
                return
    else:
        # Use current channel
        channel_id = message.channel.id

    # Verify channel exists and bot can access it
    channel = bot.get_channel(channel_id)
    if not channel:
        await message.channel.send(
            f"❌ Could not find channel with ID `{channel_id}`. Make sure the bot has access to it."
        )
        return

    # Check bot permissions in the channel
    if isinstance(channel, discord.TextChannel):
        permissions = channel.permissions_for(channel.guild.me)
        if not permissions.send_messages or not permissions.embed_links:
            await message.channel.send(
                f"❌ Bot doesn't have permission to send messages in {channel.mention}.\n"
                f"Required permissions: **Send Messages**, **Embed Links**"
            )
            return

    # Save channel to database
    success = db.settings.set(
        "job_channel_id",
        str(channel_id),
        updated_by=str(message.author)
    )

    if success:
        # Update bot's cached channel ID
        bot.job_channel_id = channel_id

        embed = discord.Embed(
            title="✅ Job Channel Updated",
            description=f"Job postings will now be sent to {channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Channel ID", value=f"`{channel_id}`", inline=True)
        embed.add_field(name="Set by", value=message.author.mention, inline=True)

        await message.channel.send(embed=embed)
        logger.info(f"Job channel set to {channel_id} by {message.author}")
    else:
        await message.channel.send("❌ Failed to save channel setting. Check logs for details.")


async def handle_getchannel(bot: "DiscordBot", message: discord.Message) -> None:
    """Show the current job posting channel.

    Usage: !getchannel

    Args:
        bot: Discord bot instance
        message: Discord message that triggered the command
    """
    db = get_database()
    channel_id = db.settings.get_int("job_channel_id")

    if not channel_id:
        embed = discord.Embed(
            title="📢 Job Channel Status",
            description="No job channel configured yet.\n\nUse `!setchannel #channel` to set one.",
            color=discord.Color.orange()
        )
        await message.channel.send(embed=embed)
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

        # Show if bot has proper permissions
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

    await message.channel.send(embed=embed)
