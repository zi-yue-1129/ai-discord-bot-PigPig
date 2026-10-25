"""Schedules ping their owner before each event."""

from __future__ import annotations

from datetime import datetime

from cogs.schedule import events_starting_at, normalize_time_range


def test_time_ranges_are_checked_and_tidied() -> None:
    assert normalize_time_range("9:00 - 10:30") == "09:00-10:30"
    assert normalize_time_range("09:00-10:30") == "09:00-10:30"
    assert normalize_time_range("25:00-26:00") is None
    assert normalize_time_range("morning") is None


def test_events_starting_at_matches_the_weekday_and_start_time() -> None:
    schedule = {
        "Monday": [{"time": "09:00-10:00", "description": "Math"}, {"time": "10:00-11:00", "description": ""}],
        "tuesday": [{"time": "09:00-10:00", "description": "Art"}],
    }
    monday_9 = datetime(2026, 10, 26, 9, 0)  # a Monday

    assert events_starting_at(schedule, monday_9) == [("09:00-10:00", "Math")]
    # Empty template slots are not announced.
    assert events_starting_at(schedule, monday_9.replace(hour=10)) == []
    assert events_starting_at(schedule, datetime(2026, 10, 27, 9, 0)) == [("09:00-10:00", "Art")]


def test_a_broken_schedule_is_ignored() -> None:
    assert events_starting_at({"monday": "oops", "tuesday": [None, "x"]}, datetime(2026, 10, 26, 9, 0)) == []
