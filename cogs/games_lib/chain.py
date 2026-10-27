"""Word chain: each word has to start with the last character of the one before it.

Chinese and Japanese words chain by character (Japanese small kana, the long-vowel mark
and katakana/hiragana are folded, so ``コーヒー`` continues with ``ひ``); words in Latin letters chain by letter.
With ``homophones`` on, a Chinese character with the same pinyin (tones ignored) also counts,
which needs the optional ``pypinyin`` package.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

# Points per accepted word.
WORD_POINTS = 10
MAX_CJK_LENGTH = 8
MAX_LATIN_LENGTH = 20

_CJK_RE = re.compile(r"^[぀-ヿ㐀-䶿一-鿿豈-﫿]{2,%d}$" % MAX_CJK_LENGTH)
_LATIN_RE = re.compile(r"^[a-z]{2,%d}$" % MAX_LATIN_LENGTH)
_SMALL_KANA = str.maketrans("ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ", "あいうえおつやゆよわアイウエオツヤユヨワカケ")
# Nothing starts with these, so a word ending in one could never be continued.
_DEAD_ENDS = {"ん", "ン"}

# The bot's own moves are recorded under this player id.
BOT_PLAYER = 0

try:  # optional: only needed for homophones
    from pypinyin import Style, pinyin
except ImportError:  # pragma: no cover - depends on the installation
    pinyin = None


def homophones_available() -> bool:
    return pinyin is not None


def normalise_word(text: str) -> Optional[str]:
    """Returns ``text`` as a playable word (lower case, NFKC), or None when it is not one word."""
    word = unicodedata.normalize("NFKC", (text or "").strip()).casefold()
    if _CJK_RE.match(word) or _LATIN_RE.match(word):
        return word
    return None


def _fold(char: str) -> str:
    """Small kana as large, katakana as hiragana."""
    char = char.translate(_SMALL_KANA)
    return chr(ord(char) - 0x60) if "\u30a1" <= char <= "\u30f6" else char


def last_char(word: str) -> str:
    """The character the next word has to start with."""
    trimmed = word.rstrip("ー")
    return (trimmed or word)[-1].translate(_SMALL_KANA)


def _readings(char: str) -> Set[str]:
    if pinyin is None or not "㐀" <= char <= "﫿":
        return set()
    return {reading for readings in pinyin(char, style=Style.NORMAL, heteronym=True) for reading in readings}


def chains(previous: str, word: str, homophones: bool = False) -> bool:
    """Whether ``word`` may follow ``previous``."""
    end, start = last_char(previous), word[0]
    if _fold(end) == _fold(start):
        return True
    return homophones and bool(_readings(end) & _readings(start))


@dataclass
class WordChain:
    """The words played so far and who played them."""

    first_word: str
    homophones: bool = False
    words: List[str] = field(default_factory=list)
    players: List[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.words = [self.first_word]
        self.players = [BOT_PLAYER]

    @property
    def last_word(self) -> str:
        return self.words[-1]

    @property
    def last_player(self) -> int:
        return self.players[-1]

    def problem(self, word: str, player: int) -> Optional[str]:
        """Why ``word`` cannot be played by ``player`` now (a response key), or None when it can."""
        if not chains(self.last_word, word, self.homophones):
            return "wrong_start"
        if word in self.words:
            return "used"
        if last_char(word) in _DEAD_ENDS:
            return "dead_end"
        if player != BOT_PLAYER and player == self.last_player:
            return "twice"
        return None

    def play(self, word: str, player: int) -> Optional[str]:
        """Plays ``word`` when allowed; returns the problem otherwise."""
        problem = self.problem(word, player)
        if problem is None:
            self.words.append(word)
            self.players.append(player)
        return problem

    def counts(self) -> Dict[int, int]:
        """Accepted words per player (the bot's own words are left out)."""
        result: Dict[int, int] = {}
        for player in self.players[1:]:
            if player != BOT_PLAYER:
                result[player] = result.get(player, 0) + 1
        return result

    def points(self) -> Dict[int, int]:
        return {player: count * WORD_POINTS for player, count in self.counts().items()}
