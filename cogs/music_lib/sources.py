"""Playback sources beyond YouTube: link classification, Spotify lookup and SoundCloud helpers."""

from __future__ import annotations

import asyncio
import html
import re
import urllib.request
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from addons.logging import get_logger

log = get_logger(server_id="Bot", source=__name__)

_YOUTUBE_HOSTS = ("youtube.com", "youtu.be")
_SOUNDCLOUD_HOST = "soundcloud.com"
_SOUNDCLOUD_SHORT_HOST = "on.soundcloud.com"
# Second path segments of a SoundCloud profile that are pages, not a track.
_SOUNDCLOUD_PROFILE_PAGES = frozenset(
    {"likes", "tracks", "albums", "reposts", "popular-tracks", "following", "followers", "comments", "spotlight"}
)
_SPOTIFY_HOST = "open.spotify.com"
_SPOTIFY_ID = re.compile(r"^[A-Za-z0-9]{22}$")
_SPOTIFY_UNSUPPORTED = frozenset({"album", "playlist", "artist", "show", "episode"})
_SPOTIFY_PAGE_LIMIT_BYTES = 2_000_000
_META = r'<meta property="{prop}" content="([^"]*)"'


def _host_matches(host: str, name: str) -> bool:
    """Whether ``host`` is ``name`` or a real subdomain of it (not a look-alike)."""
    return host == name or host.endswith(f".{name}")


def _spotify_track_id(path: str) -> Tuple[Optional[str], Optional[str]]:
    """Returns ``(kind, id)`` of a Spotify path such as ``/intl-ja/track/<id>``."""
    segments = [segment for segment in path.split("/") if segment]
    if segments and segments[0].startswith("intl-"):
        segments = segments[1:]
    if len(segments) < 2:
        return None, None
    return segments[0], segments[1]


def classify_url(query: str, *, allowed_hosts: Tuple[str, ...], spotify_enabled: bool) -> str:
    """Classifies a play request.

    Only hosts in ``allowed_hosts`` (and Spotify track links) are ever treated as links;
    any other URL is just text for a keyword search, so the bot never opens arbitrary
    addresses.

    Args:
        query: What the user typed after ``/play`` (or asked the AI to play).
        allowed_hosts: Hosts yt-dlp may open (subdomains included).
        spotify_enabled: Whether Spotify track links are recognized.

    Returns:
        ``"playlist"``, ``"video"``, ``"spotify"`` (a track to look up), ``"spotify_unsupported"``
        (an album, playlist or other Spotify page) or ``"search"``.
    """
    text = query.strip()
    if not text or " " in text:
        return "search"
    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.hostname or "").lower()

    if host == _SPOTIFY_HOST:
        if not spotify_enabled:
            return "search"
        kind, item_id = _spotify_track_id(parsed.path)
        if kind == "track" and item_id and _SPOTIFY_ID.match(item_id):
            return "spotify"
        return "spotify_unsupported" if kind in _SPOTIFY_UNSUPPORTED else "search"

    if not any(_host_matches(host, allowed) for allowed in allowed_hosts):
        return "search"
    if any(_host_matches(host, name) for name in _YOUTUBE_HOSTS):
        return "playlist" if "list" in parse_qs(parsed.query) else "video"
    if _host_matches(host, _SOUNDCLOUD_HOST):
        segments = [segment for segment in parsed.path.split("/") if segment]
        if host == _SOUNDCLOUD_SHORT_HOST:
            return "video" if len(segments) == 1 else "search"
        if len(segments) >= 3 and segments[1] == "sets":
            return "playlist"
        if len(segments) == 2 and segments[1] not in _SOUNDCLOUD_PROFILE_PAGES and segments[1] != "sets":
            return "video"
    return "search"


def extract_youtube_id(url: str) -> Optional[str]:
    """Reads the video ID from a YouTube link.

    Args:
        url: A link in any YouTube form.

    Returns:
        The video ID, or None when ``url`` is not a YouTube video link.
    """
    text = url.strip()
    if not text or " " in text:
        return None
    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.hostname or "").lower()
    segments = [segment for segment in parsed.path.split("/") if segment]
    if _host_matches(host, "youtu.be"):
        return segments[0] if segments else None
    if not _host_matches(host, "youtube.com"):
        return None
    if segments and segments[0] in ("shorts", "live", "embed") and len(segments) > 1:
        return segments[1]
    video_ids = parse_qs(parsed.query).get("v")
    return video_ids[0] if video_ids else None


def _http_get(url: str, timeout: float) -> str:
    """Fetches a page as text (at most 2 MB)."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(_SPOTIFY_PAGE_LIMIT_BYTES).decode("utf-8", "replace")


def parse_spotify_page(page: str) -> Optional[str]:
    """Builds a "artist title" search text from a Spotify track page.

    Args:
        page: The HTML of ``open.spotify.com/track/<id>``.

    Returns:
        The search text, or None when the page has no song information.
    """
    title = re.search(_META.format(prop="og:title"), page)
    description = re.search(_META.format(prop="og:description"), page)
    if not title or not description:
        return None
    song = html.unescape(title.group(1)).strip()
    artist = html.unescape(description.group(1)).split("·")[0].strip()
    if not song or not artist:
        return None
    return f"{artist} {song}"


async def fetch_spotify_search_query(url: str, timeout: float) -> Optional[str]:
    """Looks a Spotify track link up and returns "artist title" to search for.

    Only the canonical ``https://open.spotify.com/track/<id>`` page is requested, built
    from the validated track ID, so the link's own query string or path cannot redirect it.

    Args:
        url: A Spotify track link.
        timeout: Seconds to wait for the page.

    Returns:
        The search text, or None when the link is not a track or the page cannot be read.
    """
    kind, track_id = _spotify_track_id(urlparse(url if "://" in url else f"https://{url}").path)
    if kind != "track" or not track_id or not _SPOTIFY_ID.match(track_id):
        return None
    canonical = f"https://{_SPOTIFY_HOST}/track/{track_id}"
    try:
        page = await asyncio.to_thread(_http_get, canonical, timeout)
    except OSError as error:
        log.warning(f"[音樂] 讀取 Spotify 頁面失敗: {error}")
        return None
    return parse_spotify_page(page)


def is_preview_only(info: Dict[str, Any]) -> bool:
    """Whether every audio format of a track is a preview clip (e.g. SoundCloud Go+ tracks).

    Args:
        info: The yt-dlp info dict.

    Returns:
        True when there are formats and all of them are previews.
    """
    formats = info.get("formats") or []
    return bool(formats) and all("preview" in str(item.get("format_id", "")) for item in formats)


def thumbnail_of(info: Dict[str, Any]) -> Optional[str]:
    """Returns the artwork URL of a non-YouTube track.

    YouTube thumbnails are derived from the video ID instead (the listed one may 404).

    Args:
        info: The yt-dlp info dict.

    Returns:
        The artwork URL, or None for YouTube or when there is none.
    """
    if str(info.get("extractor_key", "")).lower().startswith("youtube"):
        return None
    return info.get("thumbnail") or None
