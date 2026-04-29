"""Preference and saved-search command handlers."""
import json
from datetime import datetime
from typing import List

import discord

from data.database import get_database
from data.models.user_preference import SavedSearch
from sources.command_context import CommandContext

_VALID_PREFS = {
    "min_salary": "Minimum salary filter (e.g. 80000)",
    "remote_only": "Only show remote jobs (true/false)",
    "experience": "Preferred levels, comma-separated (e.g. senior,lead)",
    "keywords": "Required keywords, comma-separated (e.g. python,django)",
}


async def handle_preferences_view(ctx: CommandContext) -> None:
    """Show the user's current preferences."""
    db = get_database()
    guild_id = str(ctx.guild.id) if ctx.guild else ""
    prefs = db.users.get_all_prefs(str(ctx.author.id), guild_id)

    embed = discord.Embed(
        title="⚙️ Your Preferences",
        color=discord.Color.blurple(),
    )

    if not prefs:
        embed.description = "No preferences set. Use `/preferences set` to configure."
    else:
        for key, value in prefs.items():
            embed.add_field(name=key, value=value, inline=True)

    await ctx.channel.send(embed=embed)


async def handle_preferences_set(ctx: CommandContext, key: str, value: str) -> None:
    """Set a user preference."""
    if key not in _VALID_PREFS:
        valid = "\n".join(f"• `{k}` — {v}" for k, v in _VALID_PREFS.items())
        await ctx.channel.send(f"❌ Unknown preference `{key}`.\n\nValid options:\n{valid}")
        return

    db = get_database()
    guild_id = str(ctx.guild.id) if ctx.guild else ""
    db.users.set_pref(str(ctx.author.id), guild_id, key, value)
    await ctx.channel.send(f"✅ Set `{key}` = `{value}`")


async def handle_savedsearch_add(
    ctx: CommandContext,
    name: str,
    keywords: str = "",
    min_salary: int = 0,
    experience: str = "",
    remote_only: bool = False,
) -> None:
    """Add a saved search."""
    db = get_database()
    user_id = str(ctx.author.id)
    guild_id = str(ctx.guild.id) if ctx.guild else ""

    existing = db.users.get_saved_searches(user_id, guild_id)
    if any(s.name.lower() == name.lower() for s in existing):
        await ctx.channel.send(
            f"❌ A saved search named `{name}` already exists. Remove it first with `/savedsearch remove`."
        )
        return

    if len(existing) >= 10:
        await ctx.channel.send("❌ You can have at most 10 saved searches.")
        return

    kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
    exp_list = [e.strip().lower() for e in experience.split(",") if e.strip()] if experience else []

    search = SavedSearch(
        user_id=user_id,
        guild_id=guild_id,
        name=name,
        keywords=kw_list,
        min_salary=min_salary or None,
        experience_levels=exp_list,
        remote_only=remote_only,
        created_at=datetime.utcnow().isoformat(),
    )
    db.users.add_saved_search(search)

    embed = discord.Embed(
        title=f"🔔 Saved Search: {name}",
        color=discord.Color.green(),
    )
    if kw_list:
        embed.add_field(name="Keywords", value=", ".join(kw_list), inline=True)
    if min_salary:
        embed.add_field(name="Min Salary", value=f"${min_salary:,}", inline=True)
    if exp_list:
        embed.add_field(name="Experience", value=", ".join(exp_list), inline=True)
    embed.add_field(name="Remote Only", value="Yes" if remote_only else "No", inline=True)
    embed.set_footer(text="You'll receive a DM when a matching job is posted.")
    await ctx.channel.send(embed=embed)


async def handle_savedsearch_list(ctx: CommandContext) -> None:
    """List the user's saved searches."""
    db = get_database()
    user_id = str(ctx.author.id)
    guild_id = str(ctx.guild.id) if ctx.guild else ""
    searches = db.users.get_saved_searches(user_id, guild_id)

    if not searches:
        await ctx.channel.send("📭 No saved searches. Use `/savedsearch add` to create one.")
        return

    embed = discord.Embed(
        title="🔔 Your Saved Searches",
        color=discord.Color.blurple(),
        description=f"{len(searches)} saved search{'es' if len(searches) != 1 else ''}",
    )
    for s in searches:
        parts = []
        if s.keywords:
            parts.append(f"keywords: {', '.join(s.keywords)}")
        if s.min_salary:
            parts.append(f"min ${s.min_salary:,}")
        if s.experience_levels:
            parts.append(f"level: {', '.join(s.experience_levels)}")
        if s.remote_only:
            parts.append("remote only")
        embed.add_field(name=s.name, value=", ".join(parts) or "no filters", inline=False)

    await ctx.channel.send(embed=embed)


async def handle_savedsearch_remove(ctx: CommandContext, name: str) -> None:
    """Remove a saved search by name."""
    db = get_database()
    user_id = str(ctx.author.id)
    guild_id = str(ctx.guild.id) if ctx.guild else ""
    removed = db.users.remove_saved_search(user_id, guild_id, name)
    if removed:
        await ctx.channel.send(f"🗑️ Removed saved search `{name}`.")
    else:
        await ctx.channel.send(f"❌ No saved search named `{name}` found.")
