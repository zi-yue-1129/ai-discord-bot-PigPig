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
from cogs.music_lib.filters import FILTER_NAMES
from cogs.music_lib.service import ActionResult
from llm.music_context import format_seconds

_logger = get_logger(server_id="Bot", source="llm.tools.music_tools")

# Lyrics handed to the model at most (a whole song fits; the context stays small).
_MAX_LYRICS_CHARS = 4000
# Songs of one playlist listed to the model (the same as /playlist view shows).
_MAX_PLAYLIST_SONGS = 40

# Every music slash command ("command:<group> <name>") and player control ("button:<id>",
# "menu:<id>") must be in exactly one of the two tables below; tests/music_cog/test_ai_tool_coverage.py
# scans the real commands and fails for one that is in neither. This keeps the AI from being
# asked for something it has no tool for (it once answered "autoplay is on" by changing the loop mode).
MUSIC_ACTION_TOOLS = {
    "command:play": "play_music",
    "command:mode": "set_music_loop_mode",
    "command:shuffle": "set_music_shuffle",
    "command:volume": "set_music_volume",
    "command:queue_remove": "remove_song_from_queue",
    "command:queue_clear": "clear_music_queue",
    "command:filter": "set_music_effect",
    "command:music seek": "seek_music",
    "command:music forward": "seek_music",
    "command:music rewind": "seek_music",
    "command:music replay": "seek_music",
    "command:music previous": "play_previous_song",
    "command:music history": "get_music_history",
    "command:music lyrics": "get_current_song_lyrics",
    "command:queue move": "move_song_in_queue",
    "command:queue swap": "move_song_in_queue",
    "command:playlist add": "add_song_to_playlist",
    "command:playlist create": "create_music_playlist",
    "command:playlist list": "list_music_playlists",
    "command:playlist view": "view_music_playlist",
    "command:playlist remove": "remove_song_from_playlist",
    "command:playlist play": "play_saved_playlist",
    "command:playlist save_queue": "save_queue_as_playlist",
    "command:music_settings view": "get_music_settings",
    "button:previous": "play_previous_song",
    "button:toggle_playback": "pause_music",
    "button:skip": "skip_music",
    "button:stop": "stop_music",
    "button:toggle_shuffle": "set_music_shuffle",
    "button:toggle_autoplay": "set_music_autoplay",
    "button:seek_back": "seek_music",
    "button:seek_forward": "seek_music",
    "button:queue_play_next": "move_song_in_queue",
    "button:queue_remove": "remove_song_from_queue",
    "menu:play_mode": "set_music_loop_mode",
    "menu:audio_filter": "set_music_effect",
}

MUSIC_ACTIONS_NOT_FOR_AI = {
    "command:queue export": "Sends a text file to the user; there is nothing for the AI to do in chat.",
    "command:queue import": "Needs an uploaded text file, which the AI tools cannot receive.",
    "command:playlist export": "Sends a text file to the user; there is nothing for the AI to do in chat.",
    "command:playlist import": "Needs an uploaded text file, which the AI tools cannot receive.",
    "command:playlist delete": "Destroys saved data; kept behind an explicit command so a stray sentence cannot erase a playlist.",
    "command:playlist rename": "Changes saved data that others may refer to; kept behind an explicit command.",
    "command:playlist share": "Copies a playlist to another member; kept behind an explicit command.",
    "command:music_settings dj": "Server-wide setting that needs Manage Server; the tools do not check the speaker's permission.",
    "command:music_settings vote_ratio": "Server-wide setting that needs Manage Server; the tools do not check the speaker's permission.",
    "command:music_settings default_volume": "Server-wide setting that needs Manage Server; the tools do not check the speaker's permission.",
    "command:music_settings stay_247": "Server-wide setting that needs Manage Server; the tools do not check the speaker's permission.",
    "command:music_settings request_channel": "Server-wide setting that needs Manage Server; the tools do not check the speaker's permission.",
    "command:music_settings stage_announce": "Server-wide setting that needs Manage Server; the tools do not check the speaker's permission.",
    "button:toggle_lyrics": "Only shows or hides the lyrics field of the player panel; it does nothing in chat.",
    "button:show_queue": "Only shows or hides the queue field of the player panel; it does nothing in chat.",
    "menu:queue_song": "First step of the queue menu (pick a song, then play it next or remove it); the AI names the song itself.",
}


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

    def _cog(self) -> Optional[Any]:
        """Returns the music cog, if loaded."""
        bot = getattr(self.runtime, "bot", None)
        return bot.get_cog("YTMusic") if bot is not None else None

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
        async def play_music(query: str, play_next: bool = False) -> str:
            """Plays music in the voice channel of the user who asked.

            Call this when the user asks to play, queue or put on a song, an artist
            or a YouTube link. The bot joins the requester's voice channel by itself,
            so do not refuse and do not try to work out where anyone is: always call
            this tool. If the user is not in a voice channel, the tool tells them so
            in the channel.

            Requests play in the order they were made. Set play_next to true only when
            the user explicitly asks to cut in or to play the song next (插播).

            Args:
                query: A YouTube or SoundCloud link, a Spotify track link, or search
                    keywords such as a song title and artist. Pass links through
                    unchanged.
                play_next: Cut in so the song plays right after the current one.

            Returns:
                What was queued, or an error explaining why it could not be played.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.play(ctx, query, play_next=play_next)
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
        async def set_music_autoplay(enabled: bool) -> str:
            """Turns autoplay on or off: when the queue runs out the bot keeps playing songs it recommends.

            This is not the loop mode. Use set_music_loop_mode to repeat the queue or one song, and
            this tool when the user asks for automatic recommendations or autoplay.

            Args:
                enabled: True to let the bot queue recommended songs, False to stop when the queue ends.

            Returns:
                A confirmation, or an error explaining why it could not change.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.set_autoplay(ctx, enabled)
            return f"Autoplay is now {'on' if enabled else 'off'}." if result.ok else await _failure(ctx, result)

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

        @tool
        async def seek_music(seconds: float, relative: bool = False) -> str:
            """Jumps to a point of the song that is playing, or fast-forwards / rewinds it.

            Args:
                seconds: With relative=false, the time to jump to in seconds from the start
                    (e.g. 90 for 1:30; 0 starts the song over). With relative=true, how far
                    to jump: positive fast-forwards, negative rewinds (e.g. -10).
                relative: Whether seconds is counted from the current position.

            Returns:
                The new position, or an error (nothing playing, a live stream, past the end).
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.seek(ctx, seconds, relative=relative)
            if not result.ok:
                return await _failure(ctx, result)
            return (f"Now at {format_seconds(result.data['position'])} of {_quoted(result.data.get('title'))} "
                    f"({format_seconds(result.data['duration'])}).")

        async def set_music_effect(effect: str) -> str:
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.set_filter(ctx, effect)
            if not result.ok:
                return await _failure(ctx, result)
            return "The audio effect is off." if effect == "off" else f"The audio effect is now {effect}."

        # The effect list comes from filters.py, so the docstring is built rather than written out.
        set_music_effect.__doc__ = (
            "Applies an audio effect to the music (it stays on for the next songs).\n\n"
            "Args:\n"
            f"    effect: One of {', '.join(FILTER_NAMES)}. \"off\" removes the effect; \"karaoke\" "
            "removes the vocals; \"speed_up\" and \"slow_down\" keep the pitch.\n\n"
            "Returns:\n"
            "    A confirmation, or an error if the effect does not exist."
        )
        set_music_effect = tool(set_music_effect)

        @tool
        async def play_previous_song() -> str:
            """Goes back to the song that played before the current one (with none, starts the current song over).

            Returns:
                What plays now, or an error explaining why not.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.previous(ctx)
            if not result.ok:
                return await _failure(ctx, result)
            if result.data.get("replayed"):
                return f"There was no earlier song, so {_quoted(result.data.get('title'))} started over."
            return f"Went back to {_quoted(result.data.get('title'))}; the song that was playing comes after it."

        @tool
        async def move_song_in_queue(position: int, to: int) -> str:
            """Moves an upcoming song to another place in the queue.

            The queue and its positions are listed in the music player section of the context.

            Args:
                position: The song's current position (1 is the next song).
                to: The position to move it to (1 makes it play next).

            Returns:
                A confirmation, or an error if a position does not exist.
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await service.move(ctx, position, to)
            if not result.ok:
                return await _failure(ctx, result)
            return f"Moved '{result.data.get('title')}' to position {to}."

        @tool
        async def get_current_song_lyrics() -> str:
            """Looks up the lyrics of the song that is playing.

            Only call this when the user asks about the lyrics (what they say, what they
            mean, a translation); never to find out what is playing.

            Returns:
                The lyrics, or an error when nothing plays or no lyrics were found.
            """
            cog = self._cog()
            service, ctx, error = resolve()
            if error:
                return error
            song = cog.state_manager.get_state(ctx.guild.id).current_song
            if not song:
                return "Error: Nothing is playing."
            lyrics = await cog.current_lyrics(ctx.guild.id)
            if lyrics is None:
                return f"No lyrics were found for '{song.get('title')}'."
            text = lyrics.plain[:_MAX_LYRICS_CHARS]
            return f"Lyrics of '{lyrics.track or song.get('title')}' by {lyrics.artist or song.get('author')}:\n{text}"

        @tool
        async def play_saved_playlist(name: str, shuffle: bool = False) -> str:
            """Plays one of the user's saved playlists (or the server's) by name.

            Call this when the user asks to play "my playlist X" or a server playlist.

            Args:
                name: The playlist's name (case does not matter).
                shuffle: Shuffle its songs.

            Returns:
                How many songs were queued, or an error (no such playlist, user not in voice).
            """
            service, ctx, error = resolve()
            if error:
                return error
            result = await self._cog().playlists.play(ctx, name, shuffle=shuffle)
            if not result.ok:
                return await _failure(ctx, result)
            return f"Queued the playlist '{result.data.get('name')}' ({result.data.get('total')} songs){_in_channel(result.data)}."

        @tool
        async def add_song_to_playlist(playlist: str, query: str = "", server_playlist: bool = False) -> str:
            """Saves a song into one of the user's playlists (created if it does not exist).

            Args:
                playlist: The playlist's name.
                query: The song to add (title, artist or link). Leave empty to add the song
                    that is playing now.
                server_playlist: Save to the server's shared playlist instead of the user's own.

            Returns:
                What was added, or an error.
            """
            service, ctx, error = resolve()
            if error:
                return error
            playlists = self._cog().playlists
            scope = "server" if server_playlist else "personal"
            found = await playlists.resolve(ctx, query)
            if not found.ok:
                return await _failure(ctx, found)
            result = await playlists.add_tracks(ctx, playlist, scope, found.data["tracks"], create=True)
            if not result.ok:
                return await _failure(ctx, result)
            titles = ", ".join(f"'{track.get('title')}'" for track in found.data["tracks"][:3])
            if not result.data.get("added"):
                return f"{titles} was already in the playlist '{playlist}'."
            return f"Added {result.data['added']} song(s) ({titles}) to the playlist '{playlist}'."

        @tool
        async def create_music_playlist(name: str, server_playlist: bool = False) -> str:
            """Creates an empty playlist for the user (or for the whole server).

            Args:
                name: The new playlist's name.
                server_playlist: Create it as a shared server playlist. Only server managers
                    and DJs may change those.

            Returns:
                A confirmation, or an error (the name exists, no permission, ...).
            """
            service, ctx, error = resolve()
            if error:
                return error
            scope = "server" if server_playlist else "personal"
            result = await self._cog().playlists.create(ctx, name, scope)
            if not result.ok:
                return await _failure(ctx, result)
            return f"Created the {scope} playlist '{result.data.get('name', name)}'."

        @tool
        async def list_music_playlists() -> str:
            """Lists the user's own playlists and the server's playlists with their sizes.

            Returns:
                The playlist names and how many songs each holds.
            """
            service, ctx, error = resolve()
            if error:
                return error
            names = await self._cog().playlists.names(ctx)
            sections = []
            for scope, title in (("personal", "Your playlists"), ("server", "Server playlists")):
                if names.get(scope):
                    items = ", ".join(f"{playlist.name} ({playlist.track_count} songs)" for playlist in names[scope])
                    sections.append(f"{title}: {items}")
            return "\n".join(sections) or "There are no playlists yet."

        @tool
        async def view_music_playlist(name: str) -> str:
            """Shows the songs of a playlist with their numbers.

            Use the numbers with remove_song_from_playlist. The user's own playlist of that
            name is looked up first, then the server's.

            Args:
                name: The playlist's name (case does not matter).

            Returns:
                The numbered songs, or an error when there is no such playlist.
            """
            service, ctx, error = resolve()
            if error:
                return error
            found = await self._cog().playlists.find(ctx, name)
            if not found.ok:
                return await _failure(ctx, found)
            playlist = found.data["playlist"]
            lines = [f"{index}. {track['title']}" for index, track in enumerate(playlist.tracks[:_MAX_PLAYLIST_SONGS], 1)]
            if playlist.track_count > _MAX_PLAYLIST_SONGS:
                lines.append(f"...and {playlist.track_count - _MAX_PLAYLIST_SONGS} more.")
            body = "\n".join(lines) or "It has no songs yet."
            return f"Playlist '{playlist.name}' ({found.data.get('scope')}, {playlist.track_count} songs):\n{body}"

        @tool
        async def remove_song_from_playlist(playlist: str, position: int, server_playlist: bool = False) -> str:
            """Removes one song from a playlist.

            Call view_music_playlist first when the user did not say the song's number.

            Args:
                playlist: The playlist's name.
                position: The song's number in the playlist (1 is the first).
                server_playlist: The playlist is the shared server one.

            Returns:
                What was removed, or an error.
            """
            service, ctx, error = resolve()
            if error:
                return error
            scope = "server" if server_playlist else "personal"
            result = await self._cog().playlists.remove_track(ctx, playlist, position, scope)
            if not result.ok:
                return await _failure(ctx, result)
            return f"Removed '{result.data.get('title')}' (number {position}) from the playlist '{playlist}'."

        @tool
        async def save_queue_as_playlist(name: str, server_playlist: bool = False) -> str:
            """Saves the song that is playing and the queue as a playlist (created if missing).

            Args:
                name: The playlist's name.
                server_playlist: Save it as a shared server playlist.

            Returns:
                How many songs were saved, or an error (nothing is playing, no permission, ...).
            """
            service, ctx, error = resolve()
            if error:
                return error
            scope = "server" if server_playlist else "personal"
            result = await self._cog().playlists.save_queue(ctx, name, scope)
            if not result.ok:
                return await _failure(ctx, result)
            skipped = result.data.get("skipped")
            note = f" ({skipped} already in it)" if skipped else ""
            return f"Saved {result.data.get('added')} song(s) into the playlist '{name}'{note}."

        @tool
        async def get_music_history() -> str:
            """Lists the songs that were played in this voice session, oldest first.

            Call this when the user asks what was played before, what the last songs were,
            or to go back to one of them.

            Returns:
                The numbered songs, or a note that nothing was played yet.
            """
            service, ctx, error = resolve()
            if error:
                return error
            songs = service.history(ctx.guild.id)
            if not songs:
                return "Nothing has been played yet in this session."
            lines = [f"{index}. {song.get('title')} ({format_seconds(song.get('duration') or 0)})"
                     for index, song in enumerate(songs, 1)]
            return "Played in this session:\n" + "\n".join(lines)

        @tool
        async def get_music_settings() -> str:
            """Reads the server's music settings (it cannot change them).

            Covers the DJ role, the share of listeners needed to vote a song away, the default
            volume, 24/7 mode, the song request channel and the stage topic.

            Returns:
                One line per setting.
            """
            service, ctx, error = resolve()
            if error:
                return error
            settings = self._cog().store.get_settings(ctx.guild.id)
            not_set = "not set"
            stay = "on" if settings.stay_247 else "off"
            if settings.stay_247 and settings.stay_channel_id:
                stay += f" (<#{settings.stay_channel_id}>)"
            return "\n".join([
                f"DJ role: {f'<@&{settings.dj_role_id}>' if settings.dj_role_id else not_set}",
                f"Share of listeners needed to skip: {round(settings.vote_ratio * 100)}%",
                f"Default volume: {settings.default_volume}%",
                f"24/7 mode: {stay}",
                f"Song request channel: {f'<#{settings.request_channel_id}>' if settings.request_channel_id else not_set}",
                f"Stage topic follows the song: {'on' if settings.stage_announce else 'off'}",
            ])

        # All music tools run in the info agent: its tool results are handed to the reply
        # agent, whereas the reply agent calls the model once and never sees tool results
        # (and its tool calls are cut off after 10 seconds, too short for a download).
        action_tools = (
            play_music, skip_music, pause_music, resume_music,
            stop_music, set_music_loop_mode, set_music_shuffle, set_music_autoplay,
            set_music_volume, remove_song_from_queue, clear_music_queue,
            seek_music, set_music_effect, play_previous_song, move_song_in_queue,
            get_current_song_lyrics, play_saved_playlist, add_song_to_playlist,
            create_music_playlist, list_music_playlists, view_music_playlist,
            remove_song_from_playlist, save_queue_as_playlist, get_music_history, get_music_settings,
        )

        # The music group comes after the core tools and can be limited to some channels.
        for music_tool in action_tools:
            music_tool.metadata = {**(music_tool.metadata or {}), "tool_group": "music"}
        return list(action_tools)
