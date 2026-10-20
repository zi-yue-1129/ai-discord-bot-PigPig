"""The song request channel: every message typed there is a song request.

The request is deleted right away so the channel only shows a pinned explanation
and the player. Chatting with the AI is not possible in that channel; the bot's
message handler asks :meth:`RequestChannel.handle` first and stops when it took
the message.
"""

from __future__ import annotations

from typing import Any

import discord

from addons.logging import get_logger

from .context import PlaybackContext

log = get_logger(server_id="Bot", source=__name__)

# How long the short replies to a request stay in the channel.
REPLY_SECONDS = 8
# Requests longer than this are not song names.
MAX_REQUEST_LENGTH = 300


class RequestChannel:
    """Manages each guild's song request channel.

    Args:
        cog: The ``YTMusic`` cog.
    """

    def __init__(self, cog: Any) -> None:
        self._cog = cog

    def _t(self, guild_id: int, *path: str, **kwargs: Any) -> str:
        lang_manager = self._cog.lang_manager or self._cog.bot.get_cog("LanguageManager")
        if lang_manager is None:
            return path[-1]
        return lang_manager.translate(str(guild_id), *path, **kwargs)

    def is_request_channel(self, channel: Any) -> bool:
        """Tells whether ``channel`` is its guild's request channel."""
        guild = getattr(channel, "guild", None)
        if guild is None:
            return False
        return self._cog.store.get_settings(guild.id).request_channel_id == getattr(channel, "id", None)

    def _header(self, guild_id: int) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎵 | {self._t(guild_id, 'system', 'music', 'request_channel', 'title')}",
            description=self._t(guild_id, "system", "music", "request_channel", "description"),
            color=discord.Color.blue(),
        )
        embed.set_footer(text=self._t(guild_id, "system", "music", "request_channel", "footer"))
        return embed

    async def _delete_header(self, guild: Any) -> None:
        settings = self._cog.store.get_settings(guild.id)
        channel = guild.get_channel(settings.request_channel_id) if settings.request_channel_id else None
        if channel is None or settings.request_message_id is None:
            return
        try:
            message = await channel.fetch_message(settings.request_message_id)
            await message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    async def enable(self, guild: Any, channel: Any) -> bool:
        """Makes ``channel`` the request channel and posts (and pins) its explanation.

        Returns:
            False when the bot cannot post or manage messages there.
        """
        permissions = channel.permissions_for(guild.me)
        if not (permissions.send_messages and permissions.manage_messages and permissions.read_message_history):
            return False
        await self._delete_header(guild)
        try:
            header = await channel.send(embed=self._header(guild.id))
        except (discord.Forbidden, discord.HTTPException):
            log.warning("Could not post the request channel header in guild %s", guild.id, exc_info=True)
            return False
        try:
            await header.pin()
        except (discord.Forbidden, discord.HTTPException):
            pass
        self._cog.store.update_settings(guild.id, request_channel_id=channel.id, request_message_id=header.id)
        return True

    async def disable(self, guild: Any) -> None:
        """Turns the request channel off and removes its explanation."""
        await self._delete_header(guild)
        self._cog.store.update_settings(guild.id, request_channel_id=None, request_message_id=None)

    async def _reply(self, channel: Any, text: str, *, error: bool = False) -> None:
        embed = discord.Embed(title=f"{'❌' if error else '✅'} | {text}",
                              color=discord.Color.red() if error else discord.Color.blue())
        try:
            await channel.send(embed=embed, delete_after=REPLY_SECONDS)
        except (discord.Forbidden, discord.HTTPException):
            pass

    async def handle(self, message: Any) -> bool:
        """Treats a message in the request channel as a song request.

        Args:
            message: A message from a person (bots are filtered out by the caller).

        Returns:
            True when the message was in the request channel (whatever happened to it),
            so nothing else should answer it.
        """
        if message.guild is None or not self.is_request_channel(message.channel):
            return False
        query = (message.content or "").strip()
        try:
            await message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass
        if not query or query.startswith(("/", "!")) or len(query) > MAX_REQUEST_LENGTH:
            return True

        guild_id = message.guild.id
        result = await self._cog.service.play(PlaybackContext.from_message(message), query)
        if not result.ok:
            text = self._t(guild_id, "system", "music", "ai_errors", result.reason, detail=result.detail)
            await self._reply(message.channel, text, error=True)
            return True
        data = result.data
        if data.get("kind") == "playlist":
            text = self._t(guild_id, "system", "music", "request_channel", "playlist_queued",
                           user=message.author.display_name, count=data.get("total", 0))
        elif data.get("started"):
            return True  # the player shows the song
        else:
            text = self._t(guild_id, "system", "music", "request_channel", "queued",
                           user=message.author.display_name, title=data.get("title", ""), position=data.get("position") or "?")
        await self._reply(message.channel, text)
        return True
