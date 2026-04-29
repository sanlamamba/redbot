"""CommandContext — unified context object for both text and slash commands."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

import discord


class InteractionChannelProxy:
    """Makes discord.Interaction.followup look like a sendable channel.

    Handlers call ctx.channel.send(embed=...) without knowing whether they
    were invoked via a text prefix command or a slash command.
    """

    def __init__(self, interaction: discord.Interaction):
        real = interaction.channel
        self._followup = interaction.followup
        self.id: int = real.id if real else 0
        self.name: str = getattr(real, "name", "")
        self.mention: str = getattr(real, "mention", "")
        self.guild: Optional[discord.Guild] = interaction.guild

    async def send(self, content=None, *, embed=None, embeds=None,
                   file=None, files=None, **kwargs) -> discord.WebhookMessage:
        kwargs.pop("ephemeral", None)
        return await self._followup.send(
            content=content, embed=embed, embeds=embeds,
            file=file, files=files, **kwargs
        )


@dataclass
class CommandContext:
    """Unified context passed to every command handler.

    Created from either a discord.Message (prefix command) or a
    discord.Interaction (slash command) via the class-method factories.
    """

    channel: Any  # discord.TextChannel | InteractionChannelProxy
    author: discord.Member | discord.User
    guild: Optional[discord.Guild]
    interaction: Optional[discord.Interaction] = None
    channel_mentions: list = field(default_factory=list)

    @property
    def has_manage_channels(self) -> bool:
        """True if the invoking user has Manage Channels permission."""
        return bool(getattr(getattr(self.author, "guild_permissions", None),
                            "manage_channels", False))

    @classmethod
    def from_message(cls, message: discord.Message) -> CommandContext:
        return cls(
            channel=message.channel,
            author=message.author,
            guild=message.guild,
            interaction=None,
            channel_mentions=message.channel_mentions,
        )

    @classmethod
    def from_interaction(
        cls,
        interaction: discord.Interaction,
        channel_mentions: list | None = None,
    ) -> CommandContext:
        return cls(
            channel=InteractionChannelProxy(interaction),
            author=interaction.user,
            guild=interaction.guild,
            interaction=interaction,
            channel_mentions=channel_mentions or [],
        )
