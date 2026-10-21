"""SQLite persistence for per-guild music settings and saved playlists.

Settings are read on almost every control (who is a DJ, whether to stay 24/7), so
they are cached in memory and only written through on change. Playlists are read
on demand: they are only touched by the ``/playlist`` commands.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from addons.logging import get_logger

log = get_logger(server_id="Bot", source=__name__)

# ``scope`` of a playlist: owned by one user (usable everywhere) or by one guild.
SCOPE_USER = "user"
SCOPE_GUILD = "guild"
SCOPES = (SCOPE_USER, SCOPE_GUILD)

# Track fields kept for a saved song; enough to queue it again without a lookup.
TRACK_FIELDS = ("video_id", "url", "title", "author", "duration")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    dj_role_id INTEGER,
    vote_ratio REAL NOT NULL DEFAULT 0.5,
    stay_247 INTEGER NOT NULL DEFAULT 0,
    stay_channel_id INTEGER,
    default_volume INTEGER NOT NULL DEFAULT 100,
    request_channel_id INTEGER,
    request_message_id INTEGER,
    stage_announce INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    name TEXT NOT NULL COLLATE NOCASE,
    created_at REAL NOT NULL,
    UNIQUE (scope, owner_id, name)
);
CREATE TABLE IF NOT EXISTS playlist_tracks (
    playlist_id INTEGER NOT NULL REFERENCES playlists (id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    video_id TEXT,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    duration INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (playlist_id, position)
);
"""


@dataclass(frozen=True)
class GuildMusicSettings:
    """Music settings of one guild.

    Attributes:
        dj_role_id: Members with this role control the player freely; ``None`` means
            everyone in the bot's voice channel may (no DJ system).
        vote_ratio: Share of the listeners whose votes skip a song (when a DJ role is set).
        stay_247: Stay in the voice channel when the queue ends or the channel empties.
        stay_channel_id: The voice channel to stay in (and rejoin after a restart).
        default_volume: Volume (0-100) every new session starts at.
        request_channel_id: Text channel where every message is a song request.
        request_message_id: The pinned instructions message in that channel.
        stage_announce: Set a stage channel's topic to the song that plays.
    """

    dj_role_id: Optional[int] = None
    vote_ratio: float = 0.5
    stay_247: bool = False
    stay_channel_id: Optional[int] = None
    default_volume: int = 100
    request_channel_id: Optional[int] = None
    request_message_id: Optional[int] = None
    stage_announce: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Returns the settings as a plain dict (IDs as strings, for JSON clients)."""
        data = asdict(self)
        for key in ("dj_role_id", "stay_channel_id", "request_channel_id", "request_message_id"):
            if data[key] is not None:
                data[key] = str(data[key])
        return data


_SETTING_NAMES = tuple(f.name for f in fields(GuildMusicSettings))
_BOOL_SETTINGS = ("stay_247", "stage_announce")


@dataclass
class Playlist:
    """A saved playlist.

    Attributes:
        id: Database ID.
        scope: ``"user"`` or ``"guild"``.
        owner_id: The owning user or guild.
        name: Its name (unique per owner, case-insensitive).
        tracks: The songs, in play order (only filled by ``get_playlist``).
        track_count: Number of songs.
    """

    id: int
    scope: str
    owner_id: int
    name: str
    tracks: List[Dict[str, Any]] = field(default_factory=list)
    track_count: int = 0


class PlaylistError(Exception):
    """A playlist operation that cannot be done; ``reason`` is a translation key."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def track_from_song(song: Dict[str, Any]) -> Dict[str, Any]:
    """Keeps the fields of a queue entry that a saved playlist stores.

    Args:
        song: A queue entry or search result.

    Returns:
        A track dict with ``TRACK_FIELDS`` (duration as an int).
    """
    track = {name: song.get(name) for name in TRACK_FIELDS}
    try:
        track["duration"] = int(float(track["duration"] or 0))
    except (TypeError, ValueError):
        track["duration"] = 0
    track["title"] = str(track["title"] or track["url"] or "")
    return track


class MusicStore:
    """Guild music settings and saved playlists in one SQLite file.

    A database problem while reading settings is logged and the defaults are used, so
    playback never breaks because of it.

    Attributes:
        path: The database file.
        max_playlists: Playlists one owner may keep.
        max_tracks: Songs one playlist may hold.
    """

    def __init__(self, path: Union[str, Path], *, max_playlists: int = 25, max_tracks: int = 200) -> None:
        self.path = Path(path)
        self.max_playlists = max_playlists
        self.max_tracks = max_tracks
        self._lock = threading.RLock()
        self._ready = False
        self._settings: Dict[int, GuildMusicSettings] = {}

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        """Yields a connection (folder and tables created the first time) that commits and closes."""
        with self._lock:
            if not self._ready:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path, timeout=10)
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("PRAGMA foreign_keys = ON")
                if not self._ready:
                    connection.executescript(_SCHEMA)
                    self._ready = True
                with connection:
                    yield connection
            finally:
                connection.close()

    # ---------------------------------------------------------------- settings
    def get_settings(self, guild_id: int) -> GuildMusicSettings:
        """Returns a guild's settings (defaults when none were saved).

        Args:
            guild_id: The guild.
        """
        cached = self._settings.get(guild_id)
        if cached is not None:
            return cached
        settings = GuildMusicSettings()
        try:
            with self._session() as connection:
                row = connection.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)).fetchone()
            if row is not None:
                values = {name: row[name] for name in _SETTING_NAMES}
                for name in _BOOL_SETTINGS:
                    values[name] = bool(values[name])
                settings = GuildMusicSettings(**values)
        except sqlite3.Error:
            log.error("Could not read the music settings of guild %s", guild_id, exc_info=True)
        self._settings[guild_id] = settings
        return settings

    def update_settings(self, guild_id: int, **changes: Any) -> GuildMusicSettings:
        """Changes some of a guild's settings and saves them.

        Args:
            guild_id: The guild.
            **changes: Setting names and their new values.

        Returns:
            The updated settings.

        Raises:
            ValueError: For an unknown setting name.
        """
        unknown = set(changes) - set(_SETTING_NAMES)
        if unknown:
            raise ValueError(f"Unknown music settings: {', '.join(sorted(unknown))}")
        settings = replace(self.get_settings(guild_id), **changes)
        values = [getattr(settings, name) for name in _SETTING_NAMES]
        values = [int(value) if isinstance(value, bool) else value for value in values]
        columns = ", ".join(_SETTING_NAMES)
        placeholders = ", ".join("?" for _ in _SETTING_NAMES)
        with self._session() as connection:
            connection.execute(
                f"INSERT OR REPLACE INTO guild_settings (guild_id, {columns}) VALUES (?, {placeholders})",
                (guild_id, *values),
            )
        self._settings[guild_id] = settings
        return settings

    def guilds_staying(self) -> Dict[int, int]:
        """Returns ``{guild_id: voice_channel_id}`` for every guild with 24/7 on."""
        try:
            with self._session() as connection:
                rows = connection.execute(
                    "SELECT guild_id, stay_channel_id FROM guild_settings WHERE stay_247 = 1 AND stay_channel_id IS NOT NULL"
                ).fetchall()
        except sqlite3.Error:
            log.error("Could not read the 24/7 guilds", exc_info=True)
            return {}
        return {row["guild_id"]: row["stay_channel_id"] for row in rows}

    # --------------------------------------------------------------- playlists
    def list_playlists(self, scope: str, owner_id: int) -> List[Playlist]:
        """Lists an owner's playlists (without their tracks), by name."""
        with self._session() as connection:
            rows = connection.execute(
                "SELECT p.id, p.scope, p.owner_id, p.name, COUNT(t.position) AS track_count "
                "FROM playlists p LEFT JOIN playlist_tracks t ON t.playlist_id = p.id "
                "WHERE p.scope = ? AND p.owner_id = ? GROUP BY p.id ORDER BY p.name",
                (scope, owner_id),
            ).fetchall()
        return [Playlist(id=row["id"], scope=row["scope"], owner_id=row["owner_id"], name=row["name"],
                         track_count=row["track_count"]) for row in rows]

    def get_playlist(self, scope: str, owner_id: int, name: str) -> Optional[Playlist]:
        """Returns an owner's playlist with its tracks, or ``None`` (name is case-insensitive)."""
        with self._session() as connection:
            row = connection.execute(
                "SELECT id, scope, owner_id, name FROM playlists WHERE scope = ? AND owner_id = ? AND name = ?",
                (scope, owner_id, name.strip()),
            ).fetchone()
            if row is None:
                return None
            tracks = connection.execute(
                f"SELECT {', '.join(TRACK_FIELDS)} FROM playlist_tracks WHERE playlist_id = ? ORDER BY position",
                (row["id"],),
            ).fetchall()
        track_list = [dict(track) for track in tracks]
        return Playlist(id=row["id"], scope=row["scope"], owner_id=row["owner_id"], name=row["name"],
                        tracks=track_list, track_count=len(track_list))

    def _require(self, scope: str, owner_id: int, name: str) -> Playlist:
        """Like ``get_playlist`` but raises ``PlaylistError("not_found")``."""
        playlist = self.get_playlist(scope, owner_id, name)
        if playlist is None:
            raise PlaylistError("not_found")
        return playlist

    def create_playlist(self, scope: str, owner_id: int, name: str) -> Playlist:
        """Creates an empty playlist.

        Raises:
            PlaylistError: ``invalid_name``, ``too_many`` or ``exists``.
        """
        name = name.strip()
        if not name or len(name) > 50:
            raise PlaylistError("invalid_name")
        if len(self.list_playlists(scope, owner_id)) >= self.max_playlists:
            raise PlaylistError("too_many")
        try:
            with self._session() as connection:
                cursor = connection.execute(
                    "INSERT INTO playlists (scope, owner_id, name, created_at) VALUES (?, ?, ?, ?)",
                    (scope, owner_id, name, time.time()),
                )
                playlist_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise PlaylistError("exists") from None
        return Playlist(id=playlist_id, scope=scope, owner_id=owner_id, name=name)

    def delete_playlist(self, scope: str, owner_id: int, name: str) -> Playlist:
        """Deletes a playlist and returns it (with its tracks)."""
        playlist = self._require(scope, owner_id, name)
        with self._session() as connection:
            connection.execute("DELETE FROM playlists WHERE id = ?", (playlist.id,))
        return playlist

    def rename_playlist(self, scope: str, owner_id: int, name: str, new_name: str) -> Playlist:
        """Renames a playlist.

        Raises:
            PlaylistError: ``not_found``, ``invalid_name`` or ``exists``.
        """
        playlist = self._require(scope, owner_id, name)
        new_name = new_name.strip()
        if not new_name or len(new_name) > 50:
            raise PlaylistError("invalid_name")
        try:
            with self._session() as connection:
                connection.execute("UPDATE playlists SET name = ? WHERE id = ?", (new_name, playlist.id))
        except sqlite3.IntegrityError:
            raise PlaylistError("exists") from None
        playlist.name = new_name
        return playlist

    def add_tracks(self, scope: str, owner_id: int, name: str, tracks: List[Dict[str, Any]]) -> int:
        """Appends songs to a playlist, skipping songs it already holds.

        Returns:
            How many songs were added (the playlist size limit may cut the list).

        Raises:
            PlaylistError: ``not_found`` or ``full`` when nothing fits.
        """
        playlist = self._require(scope, owner_id, name)
        known = {track.get("video_id") or track.get("url") for track in playlist.tracks}
        room = self.max_tracks - playlist.track_count
        fresh: List[Dict[str, Any]] = []
        for song in tracks:
            track = track_from_song(song)
            key = track.get("video_id") or track.get("url")
            if not track["url"] or key in known:
                continue
            known.add(key)
            fresh.append(track)
        if fresh and room <= 0:
            raise PlaylistError("full")
        fresh = fresh[:room]
        with self._session() as connection:
            connection.executemany(
                f"INSERT INTO playlist_tracks (playlist_id, position, {', '.join(TRACK_FIELDS)}) "
                f"VALUES (?, ?, {', '.join('?' for _ in TRACK_FIELDS)})",
                [(playlist.id, playlist.track_count + offset, *(track[name] for name in TRACK_FIELDS))
                 for offset, track in enumerate(fresh)],
            )
        return len(fresh)

    def remove_track(self, scope: str, owner_id: int, name: str, position: int) -> Dict[str, Any]:
        """Removes the song at a one-based position and closes the gap.

        Raises:
            PlaylistError: ``not_found`` or ``invalid_position``.
        """
        playlist = self._require(scope, owner_id, name)
        if not 1 <= position <= playlist.track_count:
            raise PlaylistError("invalid_position")
        removed = playlist.tracks[position - 1]
        remaining = playlist.tracks[:position - 1] + playlist.tracks[position:]
        self._replace_tracks(playlist.id, remaining)
        return removed

    def _replace_tracks(self, playlist_id: int, tracks: List[Dict[str, Any]]) -> None:
        """Rewrites a playlist's songs in the given order."""
        with self._session() as connection:
            connection.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
            connection.executemany(
                f"INSERT INTO playlist_tracks (playlist_id, position, {', '.join(TRACK_FIELDS)}) "
                f"VALUES (?, ?, {', '.join('?' for _ in TRACK_FIELDS)})",
                [(playlist_id, index, *(track[name] for name in TRACK_FIELDS)) for index, track in enumerate(tracks)],
            )

    def copy_playlist(self, source: Playlist, scope: str, owner_id: int, name: Optional[str] = None) -> Playlist:
        """Copies a playlist (with its songs) to another owner.

        Args:
            source: The playlist to copy, with its tracks.
            scope: The new owner's scope.
            owner_id: The new owner.
            name: The copy's name; defaults to the source's name.

        Raises:
            PlaylistError: ``too_many``, ``exists`` or ``invalid_name``.
        """
        copy = self.create_playlist(scope, owner_id, name or source.name)
        self._replace_tracks(copy.id, [track_from_song(track) for track in source.tracks[:self.max_tracks]])
        copy.tracks = list(source.tracks[:self.max_tracks])
        copy.track_count = len(copy.tracks)
        return copy
