"""Channel routing slash command handlers."""
import discord

from data.database import get_database
from data.repositories.routing_repository import RoutingRule
from sources.command_context import CommandContext

_VALID_RULE_TYPES = ("keyword", "subreddit", "source", "experience", "remote")


async def handle_addroute(
    ctx: CommandContext,
    channel: discord.TextChannel,
    rule_type: str,
    rule_value: str,
    priority: int = 0,
) -> None:
    """Add a channel routing rule."""
    rule_type = rule_type.lower()
    if rule_type not in _VALID_RULE_TYPES:
        await ctx.channel.send(
            f"❌ Invalid rule type `{rule_type}`. "
            f"Valid types: {', '.join(f'`{t}`' for t in _VALID_RULE_TYPES)}"
        )
        return

    guild_id = str(ctx.guild.id) if ctx.guild else ""
    db = get_database()
    rule = RoutingRule(
        guild_id=guild_id,
        channel_id=str(channel.id),
        rule_type=rule_type,
        rule_value=rule_value.lower(),
        priority=priority,
    )
    rule_id = db.routes.add_rule(rule)
    if rule_id:
        await ctx.channel.send(
            f"✅ Route added (ID `{rule_id}`): jobs matching "
            f"`{rule_type}={rule_value}` → {channel.mention}"
        )
    else:
        await ctx.channel.send("❌ Failed to add route.")


async def handle_listroutes(ctx: CommandContext) -> None:
    """List all routing rules for this guild."""
    guild_id = str(ctx.guild.id) if ctx.guild else ""
    db = get_database()
    rules = db.routes.get_rules(guild_id)

    if not rules:
        await ctx.channel.send("📭 No routing rules configured. Use `/addroute` to add one.")
        return

    embed = discord.Embed(
        title="📡 Channel Routing Rules",
        color=discord.Color.blurple(),
        description=f"{len(rules)} rule{'s' if len(rules) != 1 else ''}",
    )
    for rule in rules:
        embed.add_field(
            name=f"ID {rule.id} | priority {rule.priority}",
            value=f"`{rule.rule_type}={rule.rule_value}` → <#{rule.channel_id}>",
            inline=False,
        )
    await ctx.channel.send(embed=embed)


async def handle_removeroute(ctx: CommandContext, rule_id: int) -> None:
    """Remove a routing rule by ID."""
    guild_id = str(ctx.guild.id) if ctx.guild else ""
    db = get_database()
    removed = db.routes.remove_rule(rule_id, guild_id)
    if removed:
        await ctx.channel.send(f"🗑️ Removed routing rule `{rule_id}`.")
    else:
        await ctx.channel.send(f"❌ No rule with ID `{rule_id}` found in this server.")
