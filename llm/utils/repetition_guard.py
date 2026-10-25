"""Detects a model that is stuck repeating itself so its output can be cut where the loop begins.

A language model that falls into a loop keeps emitting the same character or phrase until
it runs out of context, which on this bot means minutes of generation and a channel full
of continuation messages. :func:`find_loop` recognises such a tail in text that is already
produced, and :class:`RepetitionGuard` does the same for text that arrives piece by piece.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Most characters a reply may show in the channel (three Discord messages).
MAX_REPLY_CHARS = 6000

# Repeating units longer than this are not searched for.
_MAX_PERIOD = 120
# A run of one character this long is a loop ("好好好..." with nothing else).
_SINGLE_CHAR_RUN = 80
# Horizontal rules and underlines are long runs of one character on purpose.
_SEPARATOR_CHARS = frozenset("-=_*#~─━")
_SEPARATOR_RUN = 400
# A longer unit must repeat at least this often and fill at least this many characters.
_MIN_REPEATS = 5
_MIN_RUN_CHARS = 100
# When cutting a loop, keep at least this many characters of its first copies.
_KEEP_MIN_CHARS = 3
# Only the end of the text is searched; a loop is reported as soon as it is long enough,
# so its start is always inside this window.
_TAIL_CHARS = 4000


@dataclass(frozen=True)
class Loop:
    """Where a repeating tail begins and how long its repeating unit is.

    Attributes:
        keep_length: Number of leading characters to keep; everything after them is the
            repeated tail. The first copies of the unit stay so the reply reads as cut off,
            not as missing its end.
        period: Length in characters of the repeating unit.
    """

    keep_length: int
    period: int


def find_loop(text: str) -> Optional[Loop]:
    """Finds a repeating tail in ``text``.

    Args:
        text: Text produced so far; only its last few thousand characters are searched.

    Returns:
        The loop, or None when the end of the text is not a loop.
    """
    window = text[-_TAIL_CHARS:]
    offset = len(text) - len(window)
    length = len(window)
    for period in range(1, min(_MAX_PERIOD, length // 2) + 1):
        if period > 1 and len(set(window[-period:])) == 1:
            # A run of one character is judged once, as a period of 1, with its own limits.
            continue
        cursor = length - period - 1
        while cursor >= 0 and window[cursor] == window[cursor + period]:
            cursor -= 1
        start = cursor + 1
        run = length - start
        if period == 1:
            limit = _SEPARATOR_RUN if window[-1] in _SEPARATOR_CHARS else _SINGLE_CHAR_RUN
            is_loop = run >= limit
        else:
            is_loop = run >= _MIN_RUN_CHARS and run // period >= _MIN_REPEATS
        if is_loop:
            copies = -(-_KEEP_MIN_CHARS // period)
            return Loop(keep_length=offset + start + period * copies, period=period)
    return None


class RepetitionGuard:
    """Watches text that arrives in pieces and reports the first loop in it."""

    def __init__(self) -> None:
        """Starts with no text seen."""
        self._tail = ""
        self._length = 0
        self._loop: Optional[Loop] = None

    def feed(self, text: str) -> Optional[Loop]:
        """Adds the next piece of text.

        Args:
            text: The piece that just arrived.

        Returns:
            The loop once one is found, counted from the start of everything fed so far;
            None while the text is not looping. After the first loop the same value is
            returned for every later piece.
        """
        if self._loop is not None:
            return self._loop
        self._tail = (self._tail + text)[-_TAIL_CHARS:]
        self._length += len(text)
        found = find_loop(self._tail)
        if found is not None:
            self._loop = Loop(
                keep_length=self._length - len(self._tail) + found.keep_length,
                period=found.period,
            )
        return self._loop
