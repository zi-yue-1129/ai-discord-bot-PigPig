"""Saving a list of songs to a text file and reading one back.

The format is one song per line, ``<url>  # <title> (<m:ss>)``. Lines starting
with ``#`` are comments. Any text file with one link per line can be imported, so
a list written by hand or exported from another bot works too.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from .sources import extract_youtube_id
from .ui.text import format_clock

# Songs read from one file at most (a playlist holds fewer; the queue buffers the rest).
MAX_IMPORT_TRACKS = 500
_LINE = re.compile(r"^(?P<url>https?://\S+)(?:\s+#\s*(?P<title>.*?))?(?:\s+\((?P<length>[\d:]+)\))?\s*$")


def tracks_to_text(tracks: Iterable[Dict[str, Any]], header: str) -> str:
    """Writes songs as an importable text file.

    Args:
        tracks: Songs with at least ``url`` (``title`` and ``duration`` are kept as a comment).
        header: A first comment line naming the list.

    Returns:
        The file content.
    """
    lines = [f"# {header}"]
    for track in tracks:
        url = track.get("url")
        if not url:
            continue
        title = str(track.get("title") or "").replace("\n", " ").strip()
        duration = track.get("duration") or 0
        comment = f"  # {title}" if title else ""
        length = f" ({format_clock(duration)})" if title and duration else ""
        lines.append(f"{url}{comment}{length}")
    return "\n".join(lines) + "\n"


def _parse_length(text: str) -> int:
    seconds = 0
    for part in text.split(":"):
        seconds = seconds * 60 + int(part)
    return seconds


def parse_tracks(text: str) -> List[Dict[str, Any]]:
    """Reads the songs of an exported (or hand-written) list.

    Args:
        text: The file content.

    Returns:
        Tracks with ``url``, ``title``, ``duration``, ``video_id`` and ``author``;
        duplicates and lines without a link are skipped.
    """
    tracks: List[Dict[str, Any]] = []
    seen = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _LINE.match(line)
        if match is None:
            continue
        url = match.group("url")
        if url in seen:
            continue
        seen.add(url)
        length = match.group("length")
        tracks.append({
            "url": url,
            "title": (match.group("title") or "").strip() or url,
            "duration": _parse_length(length) if length else 0,
            "video_id": extract_youtube_id(url) or url,
            "author": "",
        })
        if len(tracks) >= MAX_IMPORT_TRACKS:
            break
    return tracks
