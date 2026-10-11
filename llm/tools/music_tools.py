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

from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from addons.logging import get_logger
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.service import ActionResult

_logger = get_logger(server_id="Bot", source="llm.tools.music_tools")

_MAX_QUEUE_LINES = 10


def _format_seconds(seconds: Any) -> str:
    """Formats a duration in seconds as ``MM:SS``."""
    try:
        minutes, secs = divmod(int(seconds), 60)
    except (TypeError, ValueError):
        return "??:??"
    return f"{minutes:02d}:{secs:02d}"


def _format_queued(result: ActionResult) -> str:
    """Describes what a successful ``play`` queued."""
    data = result.data
    if data.get("kind") == "playlist":
        titles = ", ".join(data.get("titles", [])[:5])
        return (
            f"Queued {data.get('added')} of {data.get('total')} songs from the playlist "
            f"(the rest load as the queue plays): {titles}."
        )
    return f"Queued '{data.get('title')}' ({_format_seconds(data.get('duration'))}). It plays right away if nothing else is playing."


def _format_status(status: Dict[str, Any]) -> str:
    """Renders the player status as plain text for the model."""
    lines = [f"Player state: {status['state']}"]
    current: Optional[Dict[str, Any]] = status["current"]
    if current:
        lines.append(f"Now playing: '{current['title']}' by {current['author']} ({_format_seconds(current['duration'])})")
    queue: List[Dict[str, Any]] = status["queue"]
    if queue:
        lines.append(f"Up next ({len(queue)} in queue):")
        for position, song in enumerate(queue[:_MAX_QUEUE_LINES], 1):
            lines.append(f"{position}. '{song['title']}' ({_format_seconds(song['duration'])})")
        if len(queue) > _MAX_QUEUE_LINES:
            lines.append(f"... and {len(queue) - _MAX_QUEUE_LINES} more")
    else:
        lines.append("The queue is empty.")
    lines.append(
        f"Loop mode: {status['mode']}; shuffle: {'on' if status['shuffle'] else 'off'}; "
        f"autoplay: {'on' if status['autoplay'] else 'off'}"
    )
    return "\n".join(lines)


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

        def _failure(result: ActionResult) -> str:
            logger.info("Music tool refused: %s (%s)", result.reason, result.detail)
            return f"Error: {result.detail}"

        @tool
        async def play_music(query: str) -> str:
            """Plays music in the voice channel of the user who asked.

            Call this when the user asks to play, queue or put on a song, an artist
            or a YouTube link. The user must already be in a voice channel; if the
            bot is not connected it joins that channel.

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
            return _format_queued(result) if result.ok else _failure(result)

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
                return _failure(result)
            skipped = result.data.get("skipped")
            return f"Skipped '{skipped}'." if skipped else "Skipped the current song."

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
            return "Paused the music." if result.ok else _failure(result)

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
            return "Resumed the music." if result.ok else _failure(result)

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
            return "Stopped the music and left the voice channel." if result.ok else _failure(result)

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
            return f"Loop mode is now {mode}." if result.ok else _failure(result)

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
            return f"Shuffle is now {'on' if enabled else 'off'}." if result.ok else _failure(result)

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
            return f"Volume is now {percent}%." if result.ok else _failure(result)

        @tool
        async def remove_song_from_queue(position: int) -> str:
            """Removes one upcoming song from the queue.

            Use get_music_status first to see the positions.

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
                return _failure(result)
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
                return _failure(result)
            return f"Cleared the queue ({result.data.get('removed')} songs removed)."

        @tool
        async def get_music_status() -> str:
            """Reports what the music player is doing right now.

            Use it to answer questions such as "what song is this?" or "what is
            next in the queue?".

            Returns:
                The player state, the current song, the upcoming queue and the
                loop/shuffle/autoplay settings.
            """
            service, ctx, error = resolve()
            if error:
                return error
            return _format_status(service.status(ctx.guild.id))

        action_tools = (
            play_music, skip_music, pause_music, resume_music,
            stop_music, set_music_loop_mode, set_music_shuffle,
            set_music_volume, remove_song_from_queue, clear_music_queue,
        )
        # Actions are executed by the message agent; status is read by the info agent.
        for action_tool in action_tools:
            action_tool.__dict__["target_agent_mode"] = "message"

        return [*action_tools, get_music_status]
