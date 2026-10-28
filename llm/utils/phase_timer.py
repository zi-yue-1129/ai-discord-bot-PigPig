"""Timing of the phases of one reply, to find out where the seconds go."""

import time
from typing import Callable, Dict


class PhaseTimer:
    """Measures how long each named phase of a reply takes.

    Call :meth:`mark` right after a phase finishes; the phase is credited with the time since the
    previous mark (or since the timer was created). Marking the same name again adds up, which suits
    phases that run once per model attempt.

    Attributes:
        phases: Seconds per phase, in the order the phases were first marked.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Starts the timer.

        Args:
            clock: Source of the current time in seconds; replaced in tests.
        """
        self._clock = clock
        self._started_at: float = clock()
        self._last_mark: float = self._started_at
        self.phases: Dict[str, float] = {}

    def mark(self, phase: str) -> None:
        """Ends a phase.

        Args:
            phase: Name of the phase that just finished.
        """
        now = self._clock()
        self.phases[phase] = self.phases.get(phase, 0.0) + (now - self._last_mark)
        self._last_mark = now

    def summary(self) -> str:
        """Renders the phases and the total as one log line.

        Returns:
            For example ``context=0.25s info_agent=0.75s | total=1.00s``. Asking for it does not
            affect the phase that is currently running.
        """
        total = self._clock() - self._started_at
        total_text = f"total={total:.2f}s"
        if not self.phases:
            return total_text
        phase_text = " ".join(f"{name}={seconds:.2f}s" for name, seconds in self.phases.items())
        return f"{phase_text} | {total_text}"
