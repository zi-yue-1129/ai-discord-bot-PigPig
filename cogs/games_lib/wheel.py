"""Decision wheel: the options a player typed, and the frames of a spin that stops on one of them."""

from __future__ import annotations

import random
import re
from typing import List, Sequence

MIN_OPTIONS = 2
MAX_OPTIONS = 20
MAX_OPTION_LENGTH = 80
# Frames shown before the result (each one is a message edit).
SPIN_FRAMES = 3

_SEPARATORS = re.compile(r"[,，、;；|｜\n]")


def parse_options(text: str) -> List[str]:
    """The distinct options in ``text`` (comma, 、, ; or | separated), in the order typed."""
    options: List[str] = []
    seen = set()
    for raw in _SEPARATORS.split(text or ""):
        option = " ".join(raw.split())[:MAX_OPTION_LENGTH]
        if option and option.casefold() not in seen:
            seen.add(option.casefold())
            options.append(option)
    return options[:MAX_OPTIONS]


def spin(options: Sequence[str], rng: random.Random = random) -> List[int]:
    """Indexes the wheel points at, frame by frame; the last one is the result.

    Neighbouring frames never repeat an option, so every edit visibly moves.
    """
    frames = [rng.randrange(len(options))]
    # Built backwards from the result, so no frame repeats the one after it.
    for _ in range(SPIN_FRAMES):
        frames.insert(0, rng.choice([i for i in range(len(options)) if i != frames[0]]))
    return frames


def render(options: Sequence[str], pointer: int, final: bool = False) -> str:
    """The wheel as text, with the pointer on ``options[pointer]``."""
    lines = []
    for index, option in enumerate(options):
        if index == pointer:
            lines.append(f"{'🎯' if final else '▶️'} **{option}**")
        else:
            lines.append(f"▫️ {option}")
    return "\n".join(lines)
