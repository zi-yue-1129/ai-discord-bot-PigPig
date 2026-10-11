# MIT License
#
# Copyright (c) 2024 starpig1129
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Music tools for LLM integration.

LangChain tools that let the model play, pause, skip and inspect music on
behalf of the user who wrote the message. They are thin wrappers around
``MusicService``: permission rules (the user must sit in the bot's voice
channel) and queue behaviour are the same as for the slash commands.
"""

from typing import Any, Optional

import discord

from langchain_core.tools import tool

from addons.logging import get_logger
from cogs.music_lib.context import PlaybackContext
from addons.settings import music_config
from cogs.music_lib.service import ActionResult
from llm.music_context import format_seconds

_logger = get_logger(server_id="Bot", source="llm.tools.music_tools")


def _in_channel(data: dict) -> str:
    """Returns " in the voice channel 'X'" when the channel is known."""
    channel = data.get("channel")
    return f" in the voice channel '{channel}'" if channel else ""


def _format_queued(result: ActionResult) -> str:
    """Describes exactly what a successful ``play`` did."""
    data = result.data
    if data.get("kind") == "playlist" and not data.get("added"):
        return (
            f"Added {data.get('total')} songs from the playlist{_in_channel(data)}; "
            "they play after the current queue."
        )
    if data.get("kind") == "playlist":
        titles = ", ".join(data.get("titles", [])[:5])
        return (
            f"Queued {data.get('added')} of {data.get('total')} songs from the playlist"
            f"{_in_channel(data)} (the rest load as the queue plays): {titles}."
        )
    title = f"'{data.get('title')}' ({format_seconds(data.get('duration'))})"
    if data.get("started"):
        return f"Now playing {title}{_in_channel(data)}."
    position = f" at position {data['position']}" if data.get("position") else ""
    after = f"; it plays after '{data['current']}'" if data.get("current") else ""
    return f"Queued {title}{position}{_in_channel(data)}{after}."


def _quoted(title: Optional[str]) -> str:
    """Returns ``'title'`` or a neutral phrase when the title is unknown."""
    return f"'{title}'" if title else "the current song"


class MusicTools:
    """Container for the music tools bound to one request.

    Attributes:
        runtime: The orchestrator request holding the bot and the user's message.
    """

    def __init__(self, runtime: Any) -> None:
        """Initializes MusicTools with runtime context.

        Args:
            runtime: The orchestrator request (bot, message, logger).
        """
        self.runtime = runtime

    def _resolve(self) -> "tuple[Optional[Any], Optional[PlaybackContext], Optional[str]]":
        """Finds the music service and the playback context for this request.

        Returns:
            ``(service, context, None)`` on success, otherwise ``(None, None, error)``.
        """
        runtime = self.runtime
        bot = getattr(runtime, "bot", None)
        message = getattr(runtime, "message", None)
        if bot is None or message is None:
            return None, None, "Error: Bot or message is not available."
        if getattr(message, "guild", None) is None:
            return None, None, "Error: Music can only be controlled inside a server."
        cog = bot.get_cog("YTMusic")
        if cog is None:
            return None, None, "Error: The music module is not loaded."
        return cog.service, PlaybackContext.from_message(message), None

    def get_tools(self) -> list:
        """Returns the LangChain tools bound to this request.

        Returns:
            Action tools (message agent) and a status tool (info agent).
        """
        resolve = self._resolve
        logger = getattr(self.runtime, "logger", None) or _logger

        async def _failure(ctx: PlaybackContext, result: ActionResult) -> str:
            """Reports a failed action to the channel and returns the error text.

            The reply agent never sees tool results, so without the channel
            message the user would only hear the model's optimistic answer.
            """
            logger.info("Music tool refused: %s (%s)", result.reason, result.detail)
            if music_config.ai.announce_failures and ctx.channel is not None:
                await _announce(ctx, result)
            return f"Error: {result.detail}"

        async def _announce(ctx: PlaybackContext, result: ActionResult) -> None:
            """Posts a public failure message in the channel the user wrote in."""
            lang_manager = self.runtime.bot.get_cog("LanguageManager")
            text = result.detail
            if lang_manager is not None:
                text = lang_manager.translate(
                    str(ctx.guild.id), "system", "music", "ai_errors", result.reason, detail=result.detail
                )
            embed = discord.Embed(title=f"❌ | {text}", color=discord.Color.red())
            try:
                await ctx.channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                logger.warning("Could not announce a music failure in the channel", exc_info=True)

        @tool
        async def play_music(query: str) -> str:
            """Plays music in the voice channel of the user who asked.

            Call this when the user asks to play, queue or put on a song, an artist
            or a YouTube link. The bot joins the requester's voice channel by itself,
            so do not refuse and do not try to work out where anyone is: always call
            this tool. If the user is not in a voice channel, the tool tells them so
            in the channel.

            Args:
                query: A YouTube video or playlist URL, or search keywords such as
                    a song title and artist.

            Returns:
                What was queued, or an error explaining why it could not be played.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.play(ctx, query)
            return _format_queued(result) if result.ok else await _failure(ctx, result)

        @tool
        async def skip_music() -> str:
            """Skips the song that is currently playing.

            Returns:
                A confirmation, or an error if nothing is playing or the user is
                not in the bot's voice channel.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.skip(ctx)
            if not result.ok:
                return await _failure(ctx, result)
            skipped = _quoted(result.data.get("skipped"))
            upcoming = result.data.get("next")
            if upcoming:
                return f"Skipped {skipped}. Up next: '{upcoming}'."
            if result.data.get("more_coming"):
                return f"Skipped {skipped}. More songs will load from the playlist or autoplay."
            return f"Skipped {skipped}. The queue is now empty."

        @tool
        async def pause_music() -> str:
            """Pauses the music that is currently playing.

            Returns:
                A confirmation, or an error explaining why it could not pause.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.pause(ctx)
            if not result.ok:
                return await _failure(ctx, result)
            return f"Paused {_quoted(result.data.get('title'))}."

        @tool
        async def resume_music() -> str:
            """Resumes music that was paused.

            Returns:
                A confirmation, or an error if the music is not paused.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.resume(ctx)
            if not result.ok:
                return await _failure(ctx, result)
            return f"Resumed {_quoted(result.data.get('title'))}."

        @tool
        async def stop_music() -> str:
            """Stops the music, clears the queue and leaves the voice channel.

            Only call this when the user clearly wants the music to end; use
            pause_music to merely pause.

            Returns:
                A confirmation, or an error explaining why it could not stop.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.stop(ctx)
            if not result.ok:
                return await _failure(ctx, result)
            cleared = result.data.get("cleared", 0)
            if not cleared:
                return "Stopped the music and left the voice channel."
            noun = "song" if cleared == 1 else "songs"
            return f"Stopped the music, dropped {cleared} queued {noun} and left the voice channel."

        @tool
        async def set_music_loop_mode(mode: str) -> str:
            """Sets how the music loops.

            Args:
                mode: One of "no_loop" (play the queue once), "loop_queue"
                    (repeat the whole queue) or "loop_single" (repeat the current song).

            Returns:
                A confirmation, or an error if the mode is not valid.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.set_mode(ctx, mode)
            return f"Loop mode is now {mode}." if result.ok else await _failure(ctx, result)

        @tool
        async def set_music_shuffle(enabled: bool) -> str:
            """Turns shuffle on or off for the music queue.

            Args:
                enabled: True to shuffle the queue, False to play it in order.

            Returns:
                A confirmation, or an error explaining why it could not change.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.set_shuffle(ctx, enabled)
            return f"Shuffle is now {'on' if enabled else 'off'}." if result.ok else await _failure(ctx, result)

        @tool
        async def set_music_volume(percent: int) -> str:
            """Sets the music volume.

            Args:
                percent: Volume from 0 (silent) to 100 (full volume).

            Returns:
                A confirmation, or an error if the value is out of range.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.set_volume(ctx, percent)
            return f"Volume is now {percent}%." if result.ok else await _failure(ctx, result)

        @tool
        async def remove_song_from_queue(position: int) -> str:
            """Removes one upcoming song from the queue.

            The queue and its positions are listed in the music player section of the context.

            Args:
                position: Position in the queue, starting at 1 for the next song.

            Returns:
                The removed song, or an error if the position does not exist.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.remove_from_queue(ctx, position)
            if not result.ok:
                return await _failure(ctx, result)
            return f"Removed '{result.data.get('title')}' from position {position}."

        @tool
        async def clear_music_queue() -> str:
            """Removes every upcoming song from the queue; the current song keeps playing.

            Returns:
                How many songs were removed, or an error explaining why not.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.clear_queue(ctx)
            if not result.ok:
                return await _failure(ctx, result)
            return f"Cleared the queue ({result.data.get('removed')} songs removed)."

        # All music tools run in the info agent: its tool results are handed to the reply
        # agent, whereas the reply agent calls the model once and never sees tool results
        # (and its tool calls are cut off after 10 seconds, too short for a download).
        action_tools = (
            play_music, skip_music, pause_music, resume_music,
            stop_music, set_music_loop_mode, set_music_shuffle,
            set_music_volume, remove_song_from_queue, clear_music_queue,
        )

        return list(action_tools)
