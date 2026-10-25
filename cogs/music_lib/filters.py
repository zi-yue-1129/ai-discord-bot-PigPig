"""Audio filter presets applied through FFmpeg's ``-af`` option.

PigPig plays every song through FFmpeg, so an effect is an FFmpeg filter chain added
when the audio source is created. Changing the filter of a playing song restarts it
at the same position with the new chain.

Some presets change the playback speed. ``speed`` is how many seconds of the song
play per second of real time, so the progress bar and seeking stay in song time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Changing the sample rate re-pitches the song; resampling to 48 kHz first makes the
# factor exact whatever the source rate is (YouTube audio is often 44.1 kHz).
_RATE = 48000


def _repitch(factor: float) -> str:
    """Returns a chain that plays ``factor`` times faster and higher (like a turntable)."""
    return f"aresample={_RATE},asetrate={_RATE}*{factor:g},aresample={_RATE}"


@dataclass(frozen=True)
class FilterPreset:
    """One selectable effect.

    Attributes:
        name: Stable key (used in commands, translations and the database).
        emoji: Shown in the player's effect menu.
        chain: The FFmpeg ``-af`` filter chain, or ``None`` for no effect.
        speed: Song seconds played per real second.
    """

    name: str
    emoji: str
    chain: Optional[str]
    speed: float = 1.0


PRESETS: Tuple[FilterPreset, ...] = (
    FilterPreset("off", "🚫", None),
    FilterPreset("nightcore", "🌙", _repitch(1.25), 1.25),
    FilterPreset("vaporwave", "🌴", _repitch(0.8), 0.8),
    FilterPreset("slowed_reverb", "🌧️", _repitch(0.85) + ",aecho=0.8:0.88:60:0.4", 0.85),
    FilterPreset("8d", "🎧", "apulsator=hz=0.125"),
    FilterPreset("bassboost", "🔊", "bass=g=8"),
    FilterPreset("karaoke", "🎤", "pan=stereo|c0=c0-c1|c1=c1-c0"),
    FilterPreset("soft", "☁️", "lowpass=f=1200"),
    FilterPreset("tremolo", "〰️", "tremolo=f=5:d=0.5"),
    FilterPreset("vibrato", "🎻", "vibrato=f=6:d=0.5"),
    FilterPreset("speed_up", "⏩", "atempo=1.25", 1.25),
    FilterPreset("slow_down", "🐢", "atempo=0.8", 0.8),
)

_BY_NAME: Dict[str, FilterPreset] = {preset.name: preset for preset in PRESETS}
FILTER_NAMES: Tuple[str, ...] = tuple(_BY_NAME)


def get_preset(name: Optional[str]) -> FilterPreset:
    """Returns the preset called ``name`` (no effect for an unknown or empty name)."""
    return _BY_NAME.get(name or "off", _BY_NAME["off"])


def is_known(name: str) -> bool:
    """Tells whether ``name`` is a preset."""
    return name in _BY_NAME
