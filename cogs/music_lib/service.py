"""Interaction-free music operations shared by slash commands, buttons and AI tools.

Slash commands answer through an interaction and buttons through a component
interaction, but an AI tool has neither. Everything that actually changes the
player (queueing, pausing, skipping, ...) therefore lives here and only needs a
:class:`PlaybackContext`; each front end only formats the result.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import discord

from addons.logging import get_logger
from addons.settings import MusicAISettings, StreamingSettings, music_config

from .context import PlaybackContext, user_shares_voice_channel
from .sources import classify_url, extract_youtube_id, fetch_spotify_search_query
from .queue_manager import PlayMode

log = get_logger(source=__name__, server_id="system")

# Every ``reason`` a failed ActionResult can carry; each needs a translation in
# translations/<locale>/system/music/ai_errors.json.
FAILURE_REASONS = (
    "user_not_in_voice",
    "not_in_bot_channel",
    "voice_connect_failed",
    "lookup_failed",
    "queue_full",
    "no_results",
    "nothing_playing",
    "already_paused",
    "not_paused",
    "invalid_mode",
    "invalid_volume",
    "invalid_position",
    "playback_not_started",
    "already_playing",
    "not_in_queue",
)

# How long the bot stays in the channel after a request that could not be served.
FAILED_PLAY_DISCONNECT_SECONDS = 60
_SEARCH_CANDIDATES = 3
# Songs queued immediately from a playlist; the rest wait in the playlist buffer.
_PLAYLIST_INITIAL_SLOTS = 5


@dataclass
class ActionResult:
    """Outcome of a music operation.

    Attributes:
        ok: Whether the operation succeeded.
        reason: Machine-readable outcome (``"ok"`` or the failure cause).
        detail: Human-readable explanation.
        data: Extra structured data about the result.
    """

    ok: bool
    reason: str = "ok"
    detail: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


def classify_query(query: str) -> str:
    """Classify a play request.

    Args:
        query: What the user typed after ``/play`` (or asked the AI to play).

    Returns:
        ``"playlist"`` for a YouTube playlist link or SoundCloud set, ``"video"`` for any
        other allowed YouTube or SoundCloud link, ``"spotify"`` for a Spotify track link,
        ``"spotify_unsupported"`` for other Spotify links, otherwise ``"search"``.
    """
    sources = music_config.sources
    return classify_url(query, allowed_hosts=sources.allowed_hosts, spotify_enabled=sources.spotify)


def _channel_name(channel: Any) -> str:
    """Returns a voice channel's name for use in messages."""
    return str(getattr(channel, "name", None) or "the voice channel")


def _current_title(cog: Any, guild_id: int) -> Optional[str]:
    """Returns the title of the song that is playing, if any."""
    song = cog.state_manager.get_state(guild_id).current_song
    return song["title"] if song else None


def _fail(reason: str, detail: str) -> ActionResult:
    """Builds a failed result."""
    return ActionResult(ok=False, reason=reason, detail=detail)


class MusicService:
    """Music operations that need no Discord interaction.

    Args:
        cog: The ``YTMusic`` cog providing the queue, state and player internals.
        settings: AI-related music settings.
        streaming: First-song streaming settings.
    """

    def __init__(self, cog: Any, settings: MusicAISettings, streaming: Optional[StreamingSettings] = None) -> None:
        self._cog = cog
        self.settings = settings
        self.streaming = streaming if streaming is not None else StreamingSettings()

    # ------------------------------------------------------------------ helpers
    def _refresh_buttons(self, guild_id: int) -> Optional[Any]:
        """Returns the guild's control view, if one is showing."""
        return self._cog.ui_manager.get_current_view(guild_id)

    def _check_control(self, ctx: PlaybackContext, *, require_connection: bool = True) -> Optional[ActionResult]:
        """Checks that ``ctx.user`` may control the player.

        Args:
            ctx: The playback context.
            require_connection: Whether a missing voice connection is a failure
                (``True``) or means there is nothing to protect (``False``).

        Returns:
            A failed result when control is not allowed, otherwise ``None``.
        """
        voice_client = ctx.guild.voice_client
        if voice_client is None:
            if require_connection:
                return _fail("nothing_playing", "The bot is not connected to a voice channel.")
            return None
        if not user_shares_voice_channel(ctx.user, voice_client):
            return _fail(
                "not_in_bot_channel",
                f"Nothing was changed: the requester is not in the voice channel '{_channel_name(voice_client.channel)}' "
                "where the bot is playing.",
            )
        return None

    async def _ensure_voice(self, ctx: PlaybackContext) -> Optional[ActionResult]:
        """Joins the user's voice channel when needed and checks they share it.

        Returns:
            A failed result when the user cannot be served, otherwise ``None``.
        """
        voice_state = getattr(ctx.user, "voice", None)
        if voice_state is None or voice_state.channel is None:
            return _fail("user_not_in_voice", "Nothing was played: the requester is not in a voice channel.")

        voice_client = ctx.guild.voice_client
        if voice_client is None:
            try:
                await voice_state.channel.connect()
            except (discord.ClientException, discord.HTTPException, asyncio.TimeoutError):
                log.error("Failed to join voice channel in guild %s", ctx.guild.id, exc_info=True)
                return _fail("voice_connect_failed", "The bot could not join the voice channel.")
            return None

        if voice_client.channel == voice_state.channel:
            return None

        busy = voice_client.is_playing() or voice_client.is_paused() or not self._cog.queue_manager.is_queue_empty(ctx.guild.id)
        if busy:
            return _fail(
                "not_in_bot_channel",
                f"Nothing was played: the bot is already playing in the voice channel "
                f"'{_channel_name(voice_client.channel)}' and the requester is not in it.",
            )
        try:
            await voice_client.move_to(voice_state.channel)
        except (discord.ClientException, discord.HTTPException, asyncio.TimeoutError):
            log.error("Failed to move to the requester's channel in guild %s", ctx.guild.id, exc_info=True)
            return _fail("voice_connect_failed", "The bot could not move to the requester's voice channel.")
        return None

    async def _keep_connected(self, ctx: PlaybackContext) -> None:
        """Cancels the queue-end idle disconnect: a request is being served right now.

        A paused player keeps its own idle timer.
        """
        voice_client = ctx.guild.voice_client
        if voice_client is not None and not voice_client.is_paused():
            await self._cog._cancel_disconnect_timer(ctx.guild.id)

    async def enqueue_video(
        self, ctx: PlaybackContext, url: str, play_next: bool = False
    ) -> Tuple[Optional[dict], Optional[ActionResult]]:
        """Resolves one video URL and queues it as a request (``play_next`` cuts in).

        Returns:
            ``(video_info, None)`` on success, otherwise ``(None, failure)``.
        """
        cog = self._cog
        guild_id = ctx.guild.id
        await self._keep_connected(ctx)
        _, folder = cog._get_guild_folder(guild_id)
        voice_client = ctx.guild.voice_client
        nothing_playing = not (voice_client.is_playing() or voice_client.is_paused())
        if cog.queue_manager.get_queue(guild_id).qsize() == 0:
            video_info = None
            error = None
            if self.streaming.enabled and nothing_playing:
                # Start from the stream URL: the download continues in the background while it plays.
                video_info, error = await cog.youtube.resolve_stream(url, ctx)
            if video_info is None and error is None:
                video_info, error = await cog.youtube.download_audio(url, folder, ctx)
        else:
            video_info, error = await cog.youtube.get_video_info_without_download(url, ctx)
        if error:
            return None, _fail("lookup_failed", str(error))

        video_info["added_by"] = ctx.user.id
        if not await cog.queue_manager.enqueue_request(guild_id, video_info, play_next=play_next):
            return None, _fail("queue_full", "The queue is full.")
        return video_info, None

    async def enqueue_playlist(self, ctx: PlaybackContext, url: str) -> Tuple[Optional[List[dict]], int, Optional[ActionResult]]:
        """Resolves a playlist, queues the first songs and buffers the rest.

        Returns:
            ``(added_songs, total, None)`` on success, otherwise ``(None, 0, failure)``.
        """
        cog = self._cog
        guild_id = ctx.guild.id
        await self._keep_connected(ctx)
        _, folder = cog._get_guild_folder(guild_id)
        video_infos, error = await cog.youtube.download_playlist(url, folder, ctx)
        if error or not video_infos:
            return None, 0, _fail("lookup_failed", str(error or "The playlist is empty."))
        if cog.queue_manager.is_shuffle_enabled(guild_id):
            video_infos = cog.queue_manager.shuffled(video_infos)

        queue_size = cog.queue_manager.get_queue(guild_id).qsize()
        slots = max(0, min(_PLAYLIST_INITIAL_SLOTS - queue_size, len(video_infos)))
        added = video_infos[:slots]
        for info in added:
            info["added_by"] = ctx.user.id
            await cog.queue_manager.add_to_queue(guild_id, info)
        remaining = video_infos[slots:]
        for info in remaining:
            info["added_by"] = ctx.user.id
        if remaining:
            cog.queue_manager.extend_playlist(guild_id, remaining)
        return added, len(video_infos), None

    # --------------------------------------------------------------------- play
    async def play(self, ctx: PlaybackContext, query: str, play_next: bool = False) -> ActionResult:
        """Queues a song, playlist or search result and starts playback if idle.

        Args:
            ctx: The playback context (the user must be in a voice channel).
            query: A YouTube URL, a playlist URL or search keywords.
            play_next: Cut in: play a single song right after the current one instead of
                after the earlier requests.

        Returns:
            The outcome; on success ``data`` holds the queued song(s).
        """
        problem = await self._ensure_voice(ctx)
        if problem:
            return problem
        await self._keep_connected(ctx)

        result = await self._queue_and_start(ctx, query, play_next)
        if not result.ok:
            await self._leave_soon_if_idle(ctx)
        return result

    async def _leave_soon_if_idle(self, ctx: PlaybackContext) -> None:
        """Starts a short idle timer when a request failed and left the bot with nothing to do."""
        voice_client = ctx.guild.voice_client
        queue_manager = self._cog.queue_manager
        if (voice_client is not None and voice_client.is_connected() and self._cog._is_idle(voice_client)
                and queue_manager.is_queue_empty(ctx.guild.id)):
            await self._cog._start_disconnect_timer(ctx.guild.id, FAILED_PLAY_DISCONNECT_SECONDS)

    async def resolve_query(self, query: str) -> Tuple[str, Optional[ActionResult]]:
        """Turns a Spotify link into search text; every other query is returned unchanged.

        Args:
            query: What the user typed or asked the AI to play.

        Returns:
            ``(query, None)``, or ``("", failure)`` when a Spotify link cannot be used.
        """
        kind = classify_query(query)
        if kind == "spotify_unsupported":
            return "", _fail("lookup_failed", "Only Spotify track links are supported, not albums or playlists.")
        if kind != "spotify":
            return query, None
        found = await fetch_spotify_search_query(query.strip(), timeout=music_config.sources.spotify_timeout_seconds)
        if found is None:
            return "", _fail("lookup_failed", "Could not read that Spotify link.")
        return found, None

    async def _queue_and_start(self, ctx: PlaybackContext, query: str, play_next: bool = False) -> ActionResult:
        """Queues what ``query`` names and starts playback when nothing is playing."""
        query, problem = await self.resolve_query(query)
        if problem:
            return problem
        kind = classify_query(query)
        data: Dict[str, Any]
        info: Dict[str, Any] = {}
        if kind == "playlist":
            added, total, failure = await self.enqueue_playlist(ctx, query.strip())
            if failure:
                return failure
            data = {"kind": "playlist", "added": len(added or []), "total": total,
                    "buffered": total - len(added or []),
                    "titles": [info["title"] for info in added or []]}
        else:
            queued, failure = await self._queue_video_or_search(ctx, query, kind, play_next)
            if failure or queued is None:
                return failure or _fail("lookup_failed", "Nothing could be queued.")
            info = queued
            data = {"kind": "video", "title": info["title"], "url": info.get("url"),
                    "duration": info.get("duration", 0)}

        voice_client = ctx.guild.voice_client
        if voice_client is None:
            # The idle timer (or a disconnect) removed the bot while the song was being prepared.
            self._cog.queue_manager.clear_queue(ctx.guild.id)
            return _fail("voice_connect_failed", "The bot left the voice channel while the song was being prepared.")
        data["channel"] = _channel_name(voice_client.channel)
        if voice_client.is_playing() or voice_client.is_paused():
            self._cog.prefetcher.schedule(ctx)
            data["started"] = False
            data["current"] = _current_title(self._cog, ctx.guild.id)
            if data["kind"] == "video":
                data["position"] = self._queue_position(ctx.guild.id, info.get("video_id"))
            return ActionResult(ok=True, detail="Queued behind the current song.", data=data)

        await self._cog.play_next(ctx)
        started = await self._wait_until_playing(voice_client)
        if not started and self.settings.start_confirm_timeout_seconds > 0:
            return _fail("playback_not_started", "The song was queued but playback did not start.")
        data["started"] = started
        return ActionResult(ok=True, detail="Playing." if started else "Queued.", data=data)

    def _playing_video_id(self, ctx: PlaybackContext) -> Optional[str]:
        """Returns the video ID of the song that is playing (or paused) right now, if any."""
        voice_client = ctx.guild.voice_client
        if voice_client is None or not (voice_client.is_playing() or voice_client.is_paused()):
            return None
        song = self._cog.state_manager.get_state(ctx.guild.id).current_song
        return song.get("video_id") if song else None

    @staticmethod
    def _already_playing(title: Optional[str]) -> ActionResult:
        """Builds the refusal for a request for the song that is playing."""
        name = f"'{title}'" if title else "That song"
        return _fail("already_playing", f"{name} is already playing, so it was not queued again.")

    def _queue_position(self, guild_id: int, video_id: Optional[str]) -> Optional[int]:
        """Returns the one-based queue position of ``video_id``, if it is queued."""
        snapshot = self._cog.queue_manager.get_queue_snapshot(guild_id)
        return next((index for index, song in enumerate(snapshot, 1) if song.get("video_id") == video_id), None)

    async def _wait_until_playing(self, voice_client: Any) -> bool:
        """Waits up to the configured time for the player to report that it plays.

        Returns:
            Whether the voice client is playing (or paused) when the wait ends.
        """
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.settings.start_confirm_timeout_seconds
        while True:
            if voice_client.is_playing() or voice_client.is_paused():
                return True
            if loop.time() >= deadline:
                return False
            await asyncio.sleep(0.1)

    async def _queue_video_or_search(
        self, ctx: PlaybackContext, query: str, kind: str, play_next: bool = False
    ) -> Tuple[Optional[dict], Optional[ActionResult]]:
        """Queues a single video URL, or the first search result that can be queued."""
        playing_id = self._playing_video_id(ctx)
        if kind == "video":
            if playing_id is not None and extract_youtube_id(query) == playing_id:
                return None, self._already_playing(_current_title(self._cog, ctx.guild.id))
            return await self.enqueue_video(ctx, query.strip(), play_next)

        results = await self._cog.youtube.search_videos(query, max_results=5)
        if not results:
            return None, _fail("no_results", f"No results found for {query!r}.")
        # A search often ranks the song that is playing first; queueing it would play it twice.
        if playing_id is not None:
            others = [r for r in results if r.get("video_id") != playing_id]
            if not others:
                return None, self._already_playing(_current_title(self._cog, ctx.guild.id))
            results = others
        # The search already reports each duration (0 means unknown, e.g. a live stream), so
        # videos over the limit are dropped here instead of costing a yt-dlp probe each.
        time_limit = self._cog.youtube.time_limit
        playable = [r for r in results if not r.get("duration") or r["duration"] <= time_limit]
        if not playable:
            return None, _fail(
                "no_results",
                f"Every result for {query!r} is longer than the {time_limit // 60} minutes limit.",
            )
        failure: Optional[ActionResult] = None
        for candidate in playable[:_SEARCH_CANDIDATES]:
            info, failure = await self.enqueue_video(ctx, candidate["url"], play_next)
            if info is not None:
                return info, None
            if failure is not None and failure.reason == "queue_full":
                break
        return None, failure

    # ----------------------------------------------------------------- controls
    async def skip(self, ctx: PlaybackContext, *, refresh_buttons: bool = True) -> ActionResult:
        """Skips the current song.

        Args:
            ctx: The playback context.
            refresh_buttons: Whether to refresh the player buttons afterwards.
        """
        denied = self._check_control(ctx)
        if denied:
            return denied
        voice_client = ctx.guild.voice_client
        if not (voice_client.is_playing() or voice_client.is_paused()):
            return _fail("nothing_playing", "Nothing is playing.")

        guild_id = ctx.guild.id
        state = self._cog.state_manager.get_state(guild_id)
        skipped = state.current_song["title"] if state.current_song else None
        queued = self.queue_titles(guild_id)
        upcoming = queued[0] if queued else None
        view = self._refresh_buttons(guild_id)
        if view:
            view.stop_progress_updater()
        self._cog.mark_user_stop(guild_id)
        self._cog.state_manager.update_state(guild_id, force_next=True)
        self._record_quick_skip(guild_id, state)
        voice_client.stop()
        if view and refresh_buttons:
            await view.update_button_state()
        if state.autoplay:
            asyncio.create_task(self._cog._trigger_autoplay(ctx, guild_id))
        more_coming = self._cog.queue_manager.has_playlist_songs(guild_id) or state.autoplay
        return ActionResult(ok=True, detail="Skipped.", data={"skipped": skipped, "next": upcoming, "more_coming": more_coming})

    def _record_quick_skip(self, guild_id: int, state: Any) -> None:
        """Counts a skipped recommendation against its author when it was skipped right away."""
        song = state.current_song
        if not song or song.get("added_by") != self._cog.bot.user.id or not song.get("author"):
            return
        played = self._cog._clock() - state.song_started_at
        if played <= music_config.autoplay.skip_penalty_window_seconds:
            self._cog.taste_for(guild_id).record_skip(song["author"])

    async def pause(self, ctx: PlaybackContext, *, refresh_buttons: bool = True) -> ActionResult:
        """Pauses playback and starts the idle-disconnect timer."""
        denied = self._check_control(ctx)
        if denied:
            return denied
        voice_client = ctx.guild.voice_client
        if voice_client.is_paused():
            return _fail("already_paused", "Playback is already paused.")
        if not voice_client.is_playing():
            return _fail("nothing_playing", "Nothing is playing.")

        voice_client.pause()
        self._cog.state_manager.update_state(ctx.guild.id, auto_paused=False)
        await self._cog._start_disconnect_timer(ctx.guild.id)
        view = self._refresh_buttons(ctx.guild.id)
        if view and refresh_buttons:
            await view.update_button_state()
        return ActionResult(ok=True, detail="Paused.", data={"title": _current_title(self._cog, ctx.guild.id)})

    async def resume(self, ctx: PlaybackContext, *, refresh_buttons: bool = True) -> ActionResult:
        """Resumes paused playback."""
        denied = self._check_control(ctx)
        if denied:
            return denied
        voice_client = ctx.guild.voice_client
        if not voice_client.is_paused():
            if voice_client.is_playing():
                return _fail("not_paused", "Playback is not paused.")
            return _fail("nothing_playing", "Nothing is playing.")

        voice_client.resume()
        self._cog.state_manager.update_state(ctx.guild.id, auto_paused=False)
        await self._cog._cancel_disconnect_timer(ctx.guild.id)
        view = self._refresh_buttons(ctx.guild.id)
        if view and refresh_buttons:
            await view.update_button_state()
        return ActionResult(ok=True, detail="Resumed.", data={"title": _current_title(self._cog, ctx.guild.id)})

    async def stop(self, ctx: PlaybackContext) -> ActionResult:
        """Stops playback, clears the queue and leaves the voice channel."""
        denied = self._check_control(ctx)
        if denied:
            return denied
        guild_id = ctx.guild.id
        cleared = len(self.queue_titles(guild_id))
        await self._cog._cancel_disconnect_timer(guild_id)
        await self._cog._cleanup_voice_session(guild_id)
        return ActionResult(ok=True, detail="Stopped and disconnected.", data={"cleared": cleared})

    async def set_mode(self, ctx: PlaybackContext, mode: str) -> ActionResult:
        """Sets the loop mode (``no_loop``, ``loop_queue`` or ``loop_single``)."""
        denied = self._check_control(ctx, require_connection=False)
        if denied:
            return denied
        try:
            play_mode = PlayMode(mode)
        except ValueError:
            valid = ", ".join(item.value for item in PlayMode)
            return _fail("invalid_mode", f"Unknown mode {mode!r}; use one of: {valid}.")
        self._cog.queue_manager.set_play_mode(ctx.guild.id, play_mode)
        view = self._refresh_buttons(ctx.guild.id)
        if view:
            await view.update_button_state()
        return ActionResult(ok=True, detail=f"Mode set to {play_mode.value}.", data={"mode": play_mode.value})

    async def set_shuffle(self, ctx: PlaybackContext, enabled: bool) -> ActionResult:
        """Turns shuffle on or off."""
        denied = self._check_control(ctx, require_connection=False)
        if denied:
            return denied
        queue_manager = self._cog.queue_manager
        if queue_manager.is_shuffle_enabled(ctx.guild.id) != enabled:
            queue_manager.toggle_shuffle(ctx.guild.id)
        view = self._refresh_buttons(ctx.guild.id)
        if view:
            await view.update_button_state()
        return ActionResult(ok=True, detail=f"Shuffle {'on' if enabled else 'off'}.", data={"shuffle": enabled})

    async def set_volume(self, ctx: PlaybackContext, percent: int) -> ActionResult:
        """Sets the playback volume of the guild.

        Args:
            ctx: The playback context.
            percent: Volume from 0 to 100.
        """
        denied = self._check_control(ctx, require_connection=False)
        if denied:
            return denied
        if not 0 <= percent <= 100:
            return _fail("invalid_volume", "Volume must be between 0 and 100.")
        volume = percent / 100
        self._cog.state_manager.update_state(ctx.guild.id, volume=volume)
        source = getattr(ctx.guild.voice_client, "source", None)
        if source is not None and hasattr(source, "volume"):
            source.volume = volume
        return ActionResult(ok=True, detail=f"Volume set to {percent}%.", data={"volume": percent})

    async def _discard_files(self, guild_id: int, songs: List[Dict[str, Any]]) -> None:
        """Deletes the downloaded files of songs that left the queue.

        The file of the song that is playing right now is never touched.
        """
        playing = self._cog.state_manager.get_state(guild_id).current_song
        playing_path = playing.get("file_path") if playing else None
        for song in songs:
            path = song.get("file_path")
            if path and path != playing_path:
                await self._cog.audio_manager.delete_file(guild_id, path)

    async def remove_from_queue(self, ctx: PlaybackContext, position: int) -> ActionResult:
        """Removes one song from the queue.

        Args:
            ctx: The playback context.
            position: One-based position in the queue (1 is the next song).
        """
        denied = self._check_control(ctx, require_connection=False)
        if denied:
            return denied
        guild_id = ctx.guild.id
        removed = self._cog.queue_manager.remove_at(guild_id, position - 1) if position >= 1 else None
        if removed is None:
            size = len(self._cog.queue_manager.get_queue_snapshot(guild_id))
            return _fail("invalid_position", f"Position must be between 1 and {size}.")
        await self._cog.prefetcher.cancel_song(guild_id, removed.get("video_id"))
        await self._discard_files(guild_id, [removed])
        return ActionResult(ok=True, detail="Removed.", data={"title": removed["title"], "position": position})

    def _queued_index(self, guild_id: int, video_id: str) -> Optional[int]:
        """Returns the zero-based queue position of ``video_id``, if it is still queued."""
        snapshot = self._cog.queue_manager.get_queue_snapshot(guild_id)
        return next((index for index, song in enumerate(snapshot) if song.get("video_id") == video_id), None)

    async def play_queued_next(self, ctx: PlaybackContext, video_id: str) -> ActionResult:
        """Moves a queued song to the front so it plays right after the current one.

        Args:
            ctx: The playback context (the user must share the bot's voice channel).
            video_id: The song, as listed in the player's menu.

        Returns:
            The outcome; on success ``data`` holds the song's title.
        """
        denied = self._check_control(ctx, require_connection=False)
        if denied:
            return denied
        guild_id = ctx.guild.id
        index = self._queued_index(guild_id, video_id)
        song = self._cog.queue_manager.move_to_front(guild_id, index) if index is not None else None
        if song is None:
            return _fail("not_in_queue", "That song is no longer in the queue.")
        self._cog.prefetcher.schedule(ctx)
        return ActionResult(ok=True, detail="It plays next.", data={"title": song["title"]})

    async def remove_queued(self, ctx: PlaybackContext, video_id: str) -> ActionResult:
        """Removes a queued song chosen by its video ID (positions shift as songs play).

        Args:
            ctx: The playback context (the user must share the bot's voice channel).
            video_id: The song, as listed in the player's menu.

        Returns:
            The outcome; on success ``data`` holds the song's title.
        """
        denied = self._check_control(ctx, require_connection=False)
        if denied:
            return denied
        index = self._queued_index(ctx.guild.id, video_id)
        if index is None:
            return _fail("not_in_queue", "That song is no longer in the queue.")
        return await self.remove_from_queue(ctx, index + 1)

    async def clear_queue(self, ctx: PlaybackContext) -> ActionResult:
        """Empties the queue (and the buffered playlist) without touching the current song."""
        denied = self._check_control(ctx, require_connection=False)
        if denied:
            return denied
        guild_id = ctx.guild.id
        queue_manager = self._cog.queue_manager
        removed = queue_manager.get_queue_snapshot(guild_id)
        queue_manager.clear_queue(guild_id)
        queue_manager.set_playlist(guild_id, [])
        await self._cog.prefetcher.cancel(guild_id, keep_current=True)
        await self._discard_files(guild_id, removed)
        return ActionResult(ok=True, detail="Queue cleared.", data={"removed": len(removed)})

    # ------------------------------------------------------------------- queries
    def queue_titles(self, guild_id: int) -> List[str]:
        """Returns the titles waiting in the queue, in play order."""
        return [song["title"] for song in self._cog.queue_manager.get_queue_snapshot(guild_id)]

    @staticmethod
    def _describe(song: Dict[str, Any]) -> Dict[str, Any]:
        """Reduces a song entry to the fields worth showing."""
        return {
            "title": song.get("title"),
            "author": song.get("author"),
            "duration": song.get("duration", 0),
            "url": song.get("url"),
        }

    def status(self, guild_id: int) -> Dict[str, Any]:
        """Describes the player of a guild.

        Returns:
            A dict with ``state`` (``idle``/``playing``/``paused``),
            ``current``, ``queue``, ``mode``, ``shuffle``, ``autoplay`` and ``volume``.
        """
        cog = self._cog
        voice_client = cog.get_voice_client(guild_id)
        state = cog.state_manager.get_state(guild_id)
        if voice_client is None or not voice_client.is_connected():
            # Being connected is an implementation detail (play_music joins the
            # requester's channel itself); for everyone else it simply means idle.
            player_state = "idle"
        elif voice_client.is_paused():
            player_state = "paused"
        elif voice_client.is_playing():
            player_state = "playing"
        else:
            player_state = "idle"
        return {
            "state": player_state,
            "current": self._describe(state.current_song) if state.current_song else None,
            "queue": [self._describe(song) for song in cog.queue_manager.get_queue_snapshot(guild_id)],
            "mode": cog.queue_manager.get_play_mode(guild_id).value,
            "shuffle": cog.queue_manager.is_shuffle_enabled(guild_id),
            "autoplay": state.autoplay,
            "volume": round(state.volume * 100),
        }
