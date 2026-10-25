"""Song lyrics from LRCLIB (https://lrclib.net), a free lyrics database that needs no key.

Many entries carry time-stamped (LRC) lyrics, which the player shows line by line
as the song plays. YouTube titles are noisy ("Artist - Song (Official MV) [4K]"),
so the title is cleaned up and a few searches are tried before giving up.
"""

from __future__ import annotations

import asyncio
import bisect
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import aiohttp

from addons.logging import get_logger
from addons.settings import LyricsSettings

log = get_logger(server_id="Bot", source=__name__)

# Bracketed parts of a title holding one of these words are dropped ("(Official MV)", "【中字】").
_NOISE = re.compile(
    r"official|music\s*video|\bmv\b|\bpv\b|\bm/v\b|video|audio|lyrics?|visuali[sz]er|\bhd\b|\bhq\b|\b4k\b|"
    r"remaster|live|cover|歌詞|中字|中文|字幕|官方|完整版|動態|動画|ミュージック|歌ってみた",
    re.IGNORECASE,
)
_BRACKETS = re.compile(r"[\(\[【（「『〔][^\)\]】）」』〕]*[\)\]】）」』〕]")
_TRAILING_NOISE = re.compile(
    r"\s*(?:official\s+(?:music\s+)?(?:video|audio|mv)|music\s+video|lyrics?\s+video|\bm/?v\b|\bpv\b)\s*$",
    re.IGNORECASE,
)
_FEAT = re.compile(r"\s+(?:feat\.?|ft\.?|featuring)\s+.*$", re.IGNORECASE)
_AUTHOR_NOISE = re.compile(r"\s*(?:-\s*topic|vevo|official(?:\s+channel)?|官方頻道|官方|オフィシャル)\s*$", re.IGNORECASE)
_LRC_TIME = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")
# A search result whose length differs more than this from the song is another version.
_DURATION_TOLERANCE = 15
_CACHE_SIZE = 200
# Searches tried per song before giving up (each is one request to LRCLIB).
_MAX_QUERIES = 4


@dataclass
class Lyrics:
    """Lyrics of one song.

    Attributes:
        track: The song name as LRCLIB knows it.
        artist: The artist as LRCLIB knows it.
        plain: The lyrics as text.
        synced: ``(seconds, line)`` pairs in time order; empty when not time-stamped.
    """

    track: str
    artist: str
    plain: str
    synced: List[Tuple[float, str]] = field(default_factory=list)

    def line_index(self, position: float) -> int:
        """Returns the index of the synced line sung at ``position`` (-1 before the first)."""
        times = [time for time, _ in self.synced]
        return bisect.bisect_right(times, position) - 1


def parse_lrc(text: str) -> List[Tuple[float, str]]:
    """Reads time-stamped LRC lyrics.

    Args:
        text: LRC text, e.g. ``"[00:12.34] first line"`` (a line may carry several stamps).

    Returns:
        ``(seconds, line)`` pairs sorted by time.
    """
    lines: List[Tuple[float, str]] = []
    for raw in (text or "").splitlines():
        stamps = _LRC_TIME.findall(raw)
        if not stamps:
            continue
        words = _LRC_TIME.sub("", raw).strip()
        for minutes, seconds in stamps:
            lines.append((int(minutes) * 60 + float(seconds), words))
    lines.sort(key=lambda item: item[0])
    return lines


def clean_title(title: str) -> str:
    """Removes video noise from a title: "(Official MV)", "[4K]", "feat. X", "| channel"."""
    def drop(match: re.Match) -> str:
        return " " if _NOISE.search(match.group(0)) else match.group(0)

    text = _BRACKETS.sub(drop, title or "")
    text = text.split("|")[0]
    text = _TRAILING_NOISE.sub("", text)
    text = _FEAT.sub("", text)
    return re.sub(r"\s+", " ", text).strip(" -–—")


def clean_author(author: str) -> str:
    """Removes channel noise from an uploader name ("Artist - Topic", "ArtistVEVO")."""
    return _AUTHOR_NOISE.sub("", author or "").strip()


def search_queries(title: str, author: str) -> List[Dict[str, str]]:
    """Returns the LRCLIB searches to try for a song, most precise first."""
    cleaned = clean_title(title)
    artist = clean_author(author)
    queries: List[Dict[str, str]] = []
    for separator in (" - ", " – ", " — ", "／", " / "):
        if separator in cleaned:
            left, right = (part.strip() for part in cleaned.split(separator, 1))
            if left and right:
                queries.append({"track_name": clean_title(_strip_quotes(right)), "artist_name": left})
                queries.append({"track_name": clean_title(_strip_quotes(left)), "artist_name": right})
            break
    stripped = _strip_quotes(cleaned)
    if artist:
        queries.append({"track_name": stripped, "artist_name": artist})
    queries.append({"q": f"{artist} {stripped}".strip() if artist and artist not in stripped else stripped})
    unique: List[Dict[str, str]] = []
    for query in queries:
        if query not in unique and all(value for value in query.values()):
            unique.append(query)
    return unique[:_MAX_QUERIES]


def _strip_quotes(text: str) -> str:
    """Takes the quoted name out of 「Song」 or 『Song』 titles."""
    match = re.search(r"[「『【\"“](.+?)[」』】\"”]", text)
    return match.group(1).strip() if match else text


Fetch = Callable[[str, Dict[str, str]], Awaitable[Any]]


class LyricsClient:
    """Looks lyrics up on LRCLIB, caching what it found per song.

    Args:
        settings: The ``lyrics:`` block of music.yaml.
        fetch: Replaces the HTTP GET (``(url, params) -> JSON``); used by tests.
    """

    def __init__(self, settings: LyricsSettings, fetch: Optional[Fetch] = None) -> None:
        self.settings = settings
        self._fetch = fetch or self._http_get
        self._cache: "OrderedDict[str, Optional[Lyrics]]" = OrderedDict()

    async def _http_get(self, url: str, params: Dict[str, str]) -> Any:
        timeout = aiohttp.ClientTimeout(total=self.settings.timeout_seconds)
        headers = {"User-Agent": "PigPig Discord bot (https://github.com/starpig1129/discord-LLM-bot-PigPig)"}
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                return await response.json(content_type=None)

    async def search(self, query: Dict[str, str], duration: float = 0) -> Optional[Lyrics]:
        """Runs one LRCLIB search and returns the best match.

        Args:
            query: ``track_name``/``artist_name`` or ``q`` parameters.
            duration: The song's length (0 when unknown); results far off are skipped.
        """
        try:
            results = await self._fetch(f"{self.settings.api_url.rstrip('/')}/search", query)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            log.warning("Lyrics search failed for %s", query, exc_info=True)
            return None
        if not isinstance(results, list):
            return None
        candidates = [item for item in results if isinstance(item, dict) and not item.get("instrumental")
                      and (item.get("plainLyrics") or item.get("syncedLyrics"))]
        if duration:
            candidates = [item for item in candidates
                          if not item.get("duration") or abs(float(item["duration"]) - duration) <= _DURATION_TOLERANCE]
        if not candidates:
            return None
        def length_gap(item: Dict[str, Any]) -> Optional[float]:
            """Seconds between the entry's length and the song's (``None`` when either is unknown)."""
            return abs(float(item["duration"]) - duration) if duration and item.get("duration") else None

        # Time-stamped lyrics first; an entry of unknown length ranks after the ones known to fit,
        # then the closest length wins.
        best = min(candidates, key=lambda item: (
            not item.get("syncedLyrics"), length_gap(item) is None, length_gap(item) or 0,
        ))
        synced = parse_lrc(best.get("syncedLyrics") or "")
        plain = (best.get("plainLyrics") or "\n".join(line for _, line in synced)).strip()
        return Lyrics(track=str(best.get("trackName") or ""), artist=str(best.get("artistName") or ""),
                      plain=plain, synced=synced)

    async def for_song(self, song: Dict[str, Any]) -> Optional[Lyrics]:
        """Finds the lyrics of a queue entry (cached by video ID).

        Args:
            song: A song with ``title``, ``author``, ``duration`` and ``video_id``.

        Returns:
            The lyrics, or ``None`` when none were found.
        """
        key = str(song.get("video_id") or song.get("url") or song.get("title"))
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        duration = float(song.get("duration") or 0)
        found: Optional[Lyrics] = None
        for query in search_queries(str(song.get("title") or ""), str(song.get("author") or "")):
            found = await self.search(query, duration)
            if found is not None:
                break
        self._cache[key] = found
        while len(self._cache) > _CACHE_SIZE:
            self._cache.popitem(last=False)
        return found

    async def for_text(self, text: str) -> Optional[Lyrics]:
        """Finds lyrics for a song typed by a user ("artist song")."""
        return await self.search({"q": text.strip()}) if text.strip() else None


def synced_excerpt(lyrics: Lyrics, position: float, *, before: int = 1, after: int = 2, limit: int = 1000) -> str:
    """Formats the lines around ``position`` with the current line in bold.

    Args:
        lyrics: Time-stamped lyrics.
        position: Seconds into the song.
        before: Lines shown above the current one.
        after: Lines shown below it.
        limit: Maximum length of the result (an embed field holds 1024 characters).

    Returns:
        The excerpt.
    """
    index = lyrics.line_index(position)
    lines = []
    for offset in range(index - before, index + after + 1):
        if 0 <= offset < len(lyrics.synced):
            words = lyrics.synced[offset][1] or "♪"
            lines.append(f"**▶ {words}**" if offset == index else words)
        elif offset == index:
            lines.append("**♪**")
    return "\n".join(lines)[:limit] or "♪"


def paginate(text: str, page_size: int = 1800) -> List[str]:
    """Splits lyrics into pages at line breaks.

    Args:
        text: The lyrics.
        page_size: Maximum characters per page.

    Returns:
        At least one page.
    """
    pages: List[str] = []
    current = ""
    for line in text.splitlines():
        while len(line) > page_size:
            pages.append(line[:page_size])
            line = line[page_size:]
        if len(current) + len(line) + 1 > page_size:
            pages.append(current.rstrip("\n"))
            current = ""
        current += line + "\n"
    if current.strip() or not pages:
        pages.append(current.rstrip("\n"))
    return pages
