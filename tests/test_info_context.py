"""Tests for the short context note the info agent gets instead of the full system context."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from langchain_core.messages import HumanMessage

from llm.utils.info_context import build_info_context_message

_MOMENT = datetime(2026, 10, 31, 14, 17, 28, tzinfo=timezone.utc)


def test_the_note_is_a_human_message() -> None:
    assert isinstance(build_info_context_message("general", _MOMENT), HumanMessage)


def test_the_note_names_the_channel_and_the_time() -> None:
    text = build_info_context_message("general", _MOMENT).content

    assert "Channel: #general" in text
    assert "Current Time: 2026-10-31 14:17:28 UTC" in text
    assert f"Timestamp: {_MOMENT.timestamp()}" in text


def test_a_time_with_another_zone_is_shown_in_utc() -> None:
    taipei = _MOMENT.astimezone(timezone(timedelta(hours=8)))

    assert "Current Time: 2026-10-31 14:17:28 UTC" in build_info_context_message("general", taipei).content


def test_a_time_without_a_zone_counts_as_utc() -> None:
    naive = _MOMENT.replace(tzinfo=None)

    assert "Current Time: 2026-10-31 14:17:28 UTC" in build_info_context_message("general", naive).content


def test_a_missing_time_uses_the_clock() -> None:
    text = build_info_context_message("general", None, now=lambda: _MOMENT).content

    assert "Current Time: 2026-10-31 14:17:28 UTC" in text


def test_the_note_says_it_is_not_a_user_message() -> None:
    text = build_info_context_message("general", _MOMENT).content

    assert "not a user message" in text


def test_the_player_status_is_included_when_there_is_one() -> None:
    text = build_info_context_message("general", _MOMENT, music_context="Now playing: Lemon").content

    assert "Now playing: Lemon" in text


def test_nothing_about_music_appears_when_there_is_no_player_status() -> None:
    text = build_info_context_message("general", _MOMENT, music_context="").content

    assert "playing" not in text.lower()


def test_user_memory_and_knowledge_are_not_part_of_the_note() -> None:
    # That block made the model write a reply instead of calling tools (measured on the live model).
    text = build_info_context_message("general", _MOMENT).content

    assert "Background:" not in text
    assert "Guild Knowledge" not in text
