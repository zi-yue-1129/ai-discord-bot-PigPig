"""Tests for the reply phase timer."""

from typing import Callable, List

import pytest

from llm.utils.phase_timer import PhaseTimer


def make_clock(times: List[float]) -> Callable[[], float]:
    """Return a clock that yields the given readings one by one.

    Args:
        times: The successive values the clock returns.

    Returns:
        A zero-argument callable standing in for ``time.monotonic``.
    """
    readings = iter(times)
    return lambda: next(readings)


def test_mark_records_time_since_the_previous_mark() -> None:
    """Each phase gets the time since the previous mark, the first one since the start."""
    timer = PhaseTimer(clock=make_clock([10.0, 10.5, 12.0]))

    timer.mark("context")
    timer.mark("info_agent")

    assert timer.phases == {"context": pytest.approx(0.5), "info_agent": pytest.approx(1.5)}


def test_marking_a_phase_twice_adds_up() -> None:
    """A phase that runs once per model attempt accumulates its time."""
    timer = PhaseTimer(clock=make_clock([0.0, 1.0, 1.5, 4.0]))

    timer.mark("agent")
    timer.mark("edit")
    timer.mark("agent")

    assert timer.phases["agent"] == pytest.approx(3.5)
    assert timer.phases["edit"] == pytest.approx(0.5)


def test_summary_lists_phases_in_first_seen_order_with_total() -> None:
    """The summary is one line: phases in the order they first happened, then the total."""
    timer = PhaseTimer(clock=make_clock([0.0, 0.25, 1.0, 3.5, 3.5]))

    timer.mark("context")
    timer.mark("info_agent")
    timer.mark("message_agent")

    assert timer.summary() == "context=0.25s info_agent=0.75s message_agent=2.50s | total=3.50s"


def test_summary_without_marks_only_has_the_total() -> None:
    """A timer nobody marked still reports how long it has been running."""
    timer = PhaseTimer(clock=make_clock([5.0, 5.0]))

    assert timer.summary() == "total=0.00s"


def test_summary_does_not_move_the_last_mark() -> None:
    """Asking for the summary must not swallow time that belongs to the next phase."""
    timer = PhaseTimer(clock=make_clock([0.0, 1.0, 2.0, 5.0]))

    timer.mark("a")
    timer.summary()
    timer.mark("b")

    assert timer.phases["b"] == pytest.approx(4.0)
