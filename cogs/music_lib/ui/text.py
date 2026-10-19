"""Fitting song titles into the narrow player interface."""

from __future__ import annotations

import unicodedata

_ELLIPSIS = "…"


def _char_width(char: str) -> int:
    """Returns 2 for full-width characters (CJK, full-width punctuation), otherwise 1."""
    return 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1


def display_width(text: str) -> int:
    """Returns how many columns ``text`` takes, counting full-width characters twice.

    Args:
        text: Any text.

    Returns:
        The column count.
    """
    return sum(_char_width(char) for char in text)


def shorten(text: str, max_width: int) -> str:
    """Cuts ``text`` to at most ``max_width`` columns, ending with an ellipsis when cut.

    Args:
        text: The text (usually a song title).
        max_width: The column budget, ellipsis included.

    Returns:
        ``text`` unchanged when it fits, otherwise its beginning followed by ``…``.
    """
    if display_width(text) <= max_width:
        return text
    budget = max_width - _char_width(_ELLIPSIS)
    kept = []
    used = 0
    for char in text:
        width = _char_width(char)
        if used + width > budget:
            break
        kept.append(char)
        used += width
    return "".join(kept).rstrip() + _ELLIPSIS
