"""Playback context shared by slash commands, buttons and background playback.

Playback code only ever needs three facts about whoever started it: the guild,
the text channel to post player messages in, and the requesting user. A
``discord.Interaction`` expires after 15 minutes and does not exist at all when
playback is started from a chat message, so internal playback APIs take this
small value object instead of an interaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class PlaybackContext:
    """Where playback was requested and by whom.

    Attributes:
        guild: The guild whose voice client plays the music.
        channel: Text channel for player messages; ``None`` if unknown.
        user: The member that requested the playback.
    """

    guild: Any
    channel: Optional[Any]
    user: Any

    @classmethod
    def from_interaction(cls, interaction: Any) -> "PlaybackContext":
        """Builds a context from a Discord interaction.

        Args:
            interaction: A ``discord.Interaction`` (or compatible object).

        Returns:
            The equivalent playback context.

        Raises:
            ValueError: If the interaction did not happen inside a guild.
        """
        if interaction.guild is None:
            raise ValueError("Music playback requires a guild interaction")
        return cls(
            guild=interaction.guild,
            channel=interaction.channel,
            user=interaction.user,
        )

    @classmethod
    def from_message(cls, message: Any) -> "PlaybackContext":
        """Builds a context from a chat message (the author is the requester).

        Args:
            message: A ``discord.Message`` (or compatible object).

        Returns:
            The equivalent playback context.

        Raises:
            ValueError: If the message was not sent inside a guild.
        """
        if message.guild is None:
            raise ValueError("Music playback requires a guild message")
        return cls(guild=message.guild, channel=message.channel, user=message.author)

    @classmethod
    def coerce(cls, source: Any) -> "PlaybackContext":
        """Returns ``source`` if it is already a context, else converts an interaction.

        Args:
            source: A ``PlaybackContext`` or a ``discord.Interaction``.

        Returns:
            A playback context.
        """
        if isinstance(source, cls):
            return source
        return cls.from_interaction(source)


def user_shares_voice_channel(user: Any, voice_client: Optional[Any]) -> bool:
    """Tells whether ``user`` sits in the voice channel the bot is playing in.

    Args:
        user: The guild member that wants to control playback.
        voice_client: The guild's voice client, or ``None`` when not connected.

    Returns:
        ``True`` only when the bot is connected and ``user`` is in that channel.
    """
    if voice_client is None:
        return False
    voice_state = getattr(user, "voice", None)
    if voice_state is None or voice_state.channel is None:
        return False
    return voice_state.channel == voice_client.channel
