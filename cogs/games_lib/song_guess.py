"""Guess the song: which guesses count for a YouTube title, and where to start the clip.

YouTube titles carry noise ("Artist - Song (Official MV) [4K]"), so a title is split into the
parts a player might type: the text around ``-``/``|``/``/`` and inside 「」『』《》 brackets,
without bracketed tags such as "Official Music Video". A guess counts when it is close to one
of those parts. Traditional and Simplified Chinese are compared alike when OpenCC is installed.
"""

from __future__ import annotations

import random
import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Optional

CLIP_SECONDS = 15
# Guesses are taken from the start of the clip until this many seconds have passed.
GUESS_SECONDS = 30
MATCH_RATIO = 0.8
BASE_POINTS = 500
SPEED_POINTS = 500

_NOISE = re.compile(
    r"official|music\s*video|lyric|audio|visuali[sz]er|\bmv\b|\bpv\b|\bhd\b|\bhq\b|\b4k\b|\b1080p\b|"
    r"\blive\b|\bvideo\b|remaster|full\s*ver|ver\.|version|feat\.|ft\.|prod\.|官方|高清|歌詞|字幕|動態|动态|完整版|中字|"
    r"cover|翻唱",
    re.IGNORECASE,
)
_TITLE_BRACKETS = re.compile(r"[「『《〈](.+?)[」』》〉]")
_TAG_BRACKETS = re.compile(r"[(\[（【［](.*?)[)\]）】］]")
_SEPARATORS = re.compile(r"\s[-–—~]\s|[|｜/／]|\s-|-\s")
_FEATURING = re.compile(r"\s(?:feat\.?|ft\.?|featuring)\s.*$", re.IGNORECASE)
_SCRIPT_RUNS = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]+|[a-zA-Z0-9][a-zA-Z0-9' ]*[a-zA-Z0-9]")
_KEEP = re.compile(r"[\w぀-ヿ㐀-鿿]+")

try:  # optional: compare Traditional and Simplified Chinese alike
    from opencc import OpenCC

    _to_simplified = OpenCC("t2s").convert
except Exception:  # pragma: no cover - depends on the installation
    _to_simplified = None


def normalise(text: str) -> str:
    """Lower case, NFKC, Simplified Chinese, letters and digits only."""
    text = unicodedata.normalize("NFKC", text or "").casefold()
    if _to_simplified is not None:
        text = _to_simplified(text)
    return "".join(_KEEP.findall(text)).replace("_", "")


def title_parts(title: str) -> List[str]:
    """The normalised parts of ``title`` a guess may match (song name, artist, …)."""
    raw: List[str] = list(_TITLE_BRACKETS.findall(title))
    raw.extend(tag for tag in _TAG_BRACKETS.findall(title) if not _NOISE.search(tag))
    outer = _TAG_BRACKETS.sub(" ", _TITLE_BRACKETS.sub(" ", title))
    raw.extend(_FEATURING.sub("", part) for part in _SEPARATORS.split(outer))
    parts: List[str] = []
    for part in raw:
        part = _NOISE.sub(" ", part)
        # "告白氣球 Love Confession": the Chinese and the English name each count too.
        for value in [normalise(part), *(normalise(run) for run in _SCRIPT_RUNS.findall(part))]:
            if len(value) >= 2 and value not in parts:
                parts.append(value)
    if not parts and normalise(title):
        parts.append(normalise(title))
    return parts


def is_correct(guess: str, title: str) -> bool:
    """Whether ``guess`` names the song (or its artist) closely enough."""
    value = normalise(guess)
    if len(value) < 2:
        return False
    return any(SequenceMatcher(None, value, part).ratio() >= MATCH_RATIO for part in title_parts(title))


def answer_name(title: str) -> str:
    """The title without tags such as "(Official MV)", for showing the answer."""
    cleaned = _TAG_BRACKETS.sub(lambda m: "" if _NOISE.search(m.group(1)) else m.group(0), title)
    cleaned = re.sub(
        r"(?:(?:\s+|(?<=[\])）】」』]))(?:official\s+)?(?:music\s+video|mv|live\s+video|lyric\s+video|audio|official))+\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s{2,}", " ", cleaned).strip() or title


def clip_start(duration: Optional[float], rng: random.Random = random) -> float:
    """A random start in the middle part of the song (20%–60%), leaving room for the clip."""
    if not duration or duration < CLIP_SECONDS * 3:
        return 0.0
    low, high = duration * 0.2, min(duration * 0.6, duration - CLIP_SECONDS)
    return round(rng.uniform(low, high), 1)


def points_for(elapsed: float) -> int:
    """Points for a correct guess given after ``elapsed`` seconds."""
    left = max(0.0, min(1.0, 1 - elapsed / GUESS_SECONDS))
    return BASE_POINTS + round(SPEED_POINTS * left)
