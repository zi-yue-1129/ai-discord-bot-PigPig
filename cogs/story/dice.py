"""Dice notation such as ``2d6+3`` or ``d20 - 1``: parsing and rolling."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

MAX_DICE = 100
MAX_SIDES = 1000
MAX_TERMS = 10
MAX_MODIFIER = 10_000

_TERM = re.compile(r"([+-]?)\s*(?:(\d*)d(\d+)|(\d+))", re.IGNORECASE)


class DiceError(ValueError):
    """The notation cannot be rolled; ``key`` names the response to show."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


@dataclass(frozen=True)
class DiceRoll:
    """One roll of an expression.

    Attributes:
        notation: The expression as normalised, e.g. ``2d6+3``.
        rolls: Each dice term with its sign and faces rolled, e.g. ``[(1, 6, [4, 2])]``.
        modifier: The sum of the constant terms.
    """

    notation: str
    rolls: List[Tuple[int, int, List[int]]]
    modifier: int

    @property
    def total(self) -> int:
        return sum(sign * sum(faces) for sign, _, faces in self.rolls) + self.modifier

    def describe(self) -> str:
        """``2d6+3 → [4, 2] + 3 = 9``."""
        parts = []
        for index, (sign, _, faces) in enumerate(self.rolls):
            prefix = "" if index == 0 and sign > 0 else ("- " if sign < 0 else "+ ")
            shown = ", ".join(map(str, faces)) if len(faces) <= 20 else f"{', '.join(map(str, faces[:20]))}, …"
            parts.append(f"{prefix}[{shown}]")
        if self.modifier:
            parts.append(f"{'+' if self.modifier > 0 else '-'} {abs(self.modifier)}")
        return f"{self.notation} → {' '.join(parts)} = {self.total}"


def parse(notation: str) -> List[Tuple[int, int, int]]:
    """``(sign, count, sides)`` per term; constants have ``sides == 0`` and their value as count.

    Raises:
        DiceError: The notation is empty, malformed or too large.
    """
    text = re.sub(r"\s*([+-])\s*", r"\1", (notation or "").strip())
    if not text or re.search(r"\s", text):
        raise DiceError("dice_invalid")
    terms: List[Tuple[int, int, int]] = []
    position = 0
    while position < len(text):
        match = _TERM.match(text, position)
        if match is None or match.end() == position or (terms and not match.group(1)):
            raise DiceError("dice_invalid")
        sign = -1 if match.group(1) == "-" else 1
        if match.group(3) is not None:
            count, sides = int(match.group(2) or 1), int(match.group(3))
            if count < 1 or sides < 2:
                raise DiceError("dice_invalid")
            if count > MAX_DICE or sides > MAX_SIDES:
                raise DiceError("dice_too_many")
            terms.append((sign, count, sides))
        else:
            value = int(match.group(4))
            if value > MAX_MODIFIER:
                raise DiceError("dice_too_many")
            terms.append((sign, value, 0))
        position = match.end()
    if len(terms) > MAX_TERMS or sum(count for _, count, sides in terms if sides) > MAX_DICE:
        raise DiceError("dice_too_many")
    if not any(sides for _, _, sides in terms):
        raise DiceError("dice_invalid")
    return terms


def roll(notation: str, rng: Optional[random.Random] = None) -> DiceRoll:
    """Rolls ``notation``.

    Raises:
        DiceError: See :func:`parse`.
    """
    rng = rng or random.SystemRandom()
    terms = parse(notation)
    rolls, modifier, shown = [], 0, []
    for index, (sign, count, sides) in enumerate(terms):
        op = "" if index == 0 and sign > 0 else ("-" if sign < 0 else "+")
        if sides:
            rolls.append((sign, sides, [rng.randint(1, sides) for _ in range(count)]))
            shown.append(f"{op}{count}d{sides}")
        else:
            modifier += sign * count
            shown.append(f"{op}{count}")
    return DiceRoll("".join(shown), rolls, modifier)
