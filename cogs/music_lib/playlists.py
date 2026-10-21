"""Saved playlists: personal ones (follow the user to every server) and server ones.

Like ``MusicService``, every operation needs only a :class:`PlaybackContext` and
returns an ``ActionResult``, so the ``/playlist`` commands and the AI tools share it.
Who may change a server playlist: server managers and, when one is set, the DJ role.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from addons.logging import get_logger

from .context import PlaybackContext
from .music_store import SCOPE_GUILD, SCOPE_USER, Playlist, PlaylistError, track_from_song
from .service import ActionResult, classify_query

log = get_logger(server_id="Bot", source=__name__)

# What a command's ``scope`` choice means.
PERSONAL = "personal"
SERVER = "server"


def _fail(reason: str, detail: str = "") -> ActionResult:
    return ActionResult(ok=False, reason=reason, detail=detail or reason)


class PlaylistService:
    """Playlist operations on behalf of one user.

    Args:
        cog: The ``YTMusic`` cog (its ``store``, ``service`` and ``youtube``).
    """

    def __init__(self, cog: Any) -> None:
        self._cog = cog

    @property
    def store(self) -> Any:
        return self._cog.store

    @staticmethod
    def owner(ctx: PlaybackContext, scope: str) -> tuple:
        """Returns the database ``(scope, owner_id)`` for a command's scope choice."""
        if scope == SERVER:
            return SCOPE_GUILD, ctx.guild.id
        return SCOPE_USER, ctx.user.id

    def may_edit(self, ctx: PlaybackContext, scope: str) -> bool:
        """Tells whether ``ctx.user`` may change playlists of ``scope``."""
        if scope != SERVER:
            return True
        permissions = getattr(ctx.user, "guild_permissions", None)
        if permissions is not None and (getattr(permissions, "manage_guild", False) or getattr(permissions, "administrator", False)):
            return True
        dj_role_id = self.store.get_settings(ctx.guild.id).dj_role_id
        return dj_role_id is not None and any(getattr(role, "id", None) == dj_role_id for role in getattr(ctx.user, "roles", None) or ())

    async def _run(self, func, *args) -> Any:
        """Runs a store call in a thread so the bot's loop never waits on the disk."""
        return await asyncio.to_thread(func, *args)

    def _edit_denied(self, ctx: PlaybackContext, scope: str) -> Optional[ActionResult]:
        if self.may_edit(ctx, scope):
            return None
        return _fail("playlist_no_permission", "Only server managers and DJs may change server playlists.")

    @staticmethod
    def _error(error: PlaylistError) -> ActionResult:
        return _fail(f"playlist_{error.reason}")

    # ------------------------------------------------------------------ reading
    async def names(self, ctx: PlaybackContext) -> Dict[str, List[Playlist]]:
        """Returns ``{"personal": [...], "server": [...]}`` (without tracks)."""
        personal = await self._run(self.store.list_playlists, *self.owner(ctx, PERSONAL))
        server = await self._run(self.store.list_playlists, *self.owner(ctx, SERVER))
        return {PERSONAL: personal, SERVER: server}

    async def get(self, ctx: PlaybackContext, name: str, scope: str) -> ActionResult:
        """Returns a playlist with its songs in ``data["playlist"]``."""
        playlist = await self._run(self.store.get_playlist, *self.owner(ctx, scope), name)
        if playlist is None:
            return _fail("playlist_not_found")
        return ActionResult(ok=True, data={"playlist": playlist})

    async def find(self, ctx: PlaybackContext, name: str) -> ActionResult:
        """Finds a playlist by name, the user's own first, then the server's."""
        for scope in (PERSONAL, SERVER):
            result = await self.get(ctx, name, scope)
            if result.ok:
                result.data["scope"] = scope
                return result
        return _fail("playlist_not_found")

    # ------------------------------------------------------------------ changes
    async def create(self, ctx: PlaybackContext, name: str, scope: str) -> ActionResult:
        denied = self._edit_denied(ctx, scope)
        if denied:
            return denied
        try:
            playlist = await self._run(self.store.create_playlist, *self.owner(ctx, scope), name)
        except PlaylistError as error:
            return self._error(error)
        return ActionResult(ok=True, data={"name": playlist.name})

    async def delete(self, ctx: PlaybackContext, name: str, scope: str) -> ActionResult:
        denied = self._edit_denied(ctx, scope)
        if denied:
            return denied
        try:
            playlist = await self._run(self.store.delete_playlist, *self.owner(ctx, scope), name)
        except PlaylistError as error:
            return self._error(error)
        return ActionResult(ok=True, data={"name": playlist.name, "count": playlist.track_count})

    async def rename(self, ctx: PlaybackContext, name: str, new_name: str, scope: str) -> ActionResult:
        denied = self._edit_denied(ctx, scope)
        if denied:
            return denied
        try:
            playlist = await self._run(self.store.rename_playlist, *self.owner(ctx, scope), name, new_name)
        except PlaylistError as error:
            return self._error(error)
        return ActionResult(ok=True, data={"name": playlist.name})

    async def add_tracks(self, ctx: PlaybackContext, name: str, scope: str, tracks: List[Dict[str, Any]],
                         *, create: bool = False) -> ActionResult:
        """Adds songs to a playlist (creating it first when ``create`` and it is missing).

        Returns:
            The outcome; ``data`` holds ``added``, ``skipped`` (already there or no room) and ``name``.
        """
        denied = self._edit_denied(ctx, scope)
        if denied:
            return denied
        owner = self.owner(ctx, scope)
        tracks = [track_from_song(track) for track in tracks if classify_query(str(track.get("url") or "")) == "video"]
        if not tracks:
            return _fail("nothing_to_import")
        try:
            if create and await self._run(self.store.get_playlist, *owner, name) is None:
                await self._run(self.store.create_playlist, *owner, name)
            added = await self._run(self.store.add_tracks, *owner, name, tracks)
        except PlaylistError as error:
            return self._error(error)
        return ActionResult(ok=True, data={"added": added, "skipped": len(tracks) - added, "name": name.strip()})

    async def remove_track(self, ctx: PlaybackContext, name: str, position: int, scope: str) -> ActionResult:
        denied = self._edit_denied(ctx, scope)
        if denied:
            return denied
        try:
            track = await self._run(self.store.remove_track, *self.owner(ctx, scope), name, position)
        except PlaylistError as error:
            return self._error(error)
        return ActionResult(ok=True, data={"title": track["title"], "position": position})

    async def share(self, ctx: PlaybackContext, name: str, recipient: Any) -> ActionResult:
        """Gives ``recipient`` a copy of one of the user's personal playlists.

        A name the recipient already uses gets a number: "Chill (2)".
        """
        source = await self._run(self.store.get_playlist, *self.owner(ctx, PERSONAL), name)
        if source is None:
            return _fail("playlist_not_found")
        if getattr(recipient, "bot", False) or recipient.id == ctx.user.id:
            return _fail("playlist_invalid_recipient")
        existing = {playlist.name.lower() for playlist in await self._run(self.store.list_playlists, SCOPE_USER, recipient.id)}
        copy_name = source.name
        number = 2
        while copy_name.lower() in existing:
            copy_name = f"{source.name} ({number})"
            number += 1
        try:
            copy = await self._run(self.store.copy_playlist, source, SCOPE_USER, recipient.id, copy_name)
        except PlaylistError as error:
            return self._error(error)
        return ActionResult(ok=True, data={"name": copy.name, "count": copy.track_count})

    # ---------------------------------------------------------------- resolving
    async def resolve(self, ctx: PlaybackContext, query: Optional[str]) -> ActionResult:
        """Turns what a user typed into songs to save.

        Args:
            ctx: The playback context.
            query: Nothing (the song that is playing), a video or playlist link, a
                Spotify track link or search words (the first result).

        Returns:
            The outcome; ``data["tracks"]`` holds the songs.
        """
        cog = self._cog
        if not query or not query.strip():
            song = cog.state_manager.get_state(ctx.guild.id).current_song
            if not song:
                return _fail("nothing_playing")
            return ActionResult(ok=True, data={"tracks": [song]})
        query, problem = await cog.service.resolve_query(query.strip())
        if problem:
            return problem
        kind = classify_query(query)
        if kind == "playlist":
            tracks, error = await cog.youtube.list_playlist(query, limit=self.store.max_tracks)
            if error or not tracks:
                return _fail("lookup_failed", str(error or "The playlist is empty."))
            return ActionResult(ok=True, data={"tracks": tracks})
        if kind == "video":
            info, error = await cog.youtube.get_video_info_without_download(query, ctx)
            if error or not info:
                return _fail("lookup_failed", str(error))
            return ActionResult(ok=True, data={"tracks": [info]})
        results = await cog.youtube.search_videos(query, max_results=5)
        time_limit = getattr(cog.youtube, "time_limit", 0)
        playable = [r for r in results if not time_limit or not r.get("duration") or r["duration"] <= time_limit]
        if not playable:
            return _fail("no_results", f"No results found for {query!r}.")
        return ActionResult(ok=True, data={"tracks": [playable[0]]})

    async def save_queue(self, ctx: PlaybackContext, name: str, scope: str) -> ActionResult:
        """Saves the current song and the queue into a playlist (created when missing)."""
        tracks = self._cog.service.upcoming_tracks(ctx.guild.id)
        if not tracks:
            return _fail("nothing_playing")
        return await self.add_tracks(ctx, name, scope, tracks, create=True)

    async def play(self, ctx: PlaybackContext, name: str, scope: Optional[str] = None, *, shuffle: bool = False) -> ActionResult:
        """Queues a saved playlist (``scope`` ``None`` looks in the user's own, then the server's)."""
        found = await (self.get(ctx, name, scope) if scope else self.find(ctx, name))
        if not found.ok:
            return found
        playlist: Playlist = found.data["playlist"]
        if not playlist.tracks:
            return _fail("playlist_empty")
        result = await self._cog.service.play_tracks(ctx, playlist.tracks, shuffle=shuffle)
        if result.ok:
            result.data["name"] = playlist.name
        return result
