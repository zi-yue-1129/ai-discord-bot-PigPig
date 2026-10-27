"""The AI can list and cancel the caller's own reminders."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional

import pytest

from cogs.remind import ReminderCog
from cogs.remind_lib.store import ReminderStore
from llm.tools.reminder import ReminderTools

NOW = 1_800_000_000.0


def _runtime(tmp_path: Path, author_id: int = 1, with_cog: bool = True, hidden: Optional[set] = frozenset()) -> SimpleNamespace:
    """A runtime for the reminder tools. ``hidden`` is the /leaderboard optout list (None: it cannot be read)."""
    cog: Optional[ReminderCog] = None
    if with_cog:
        cog = ReminderCog(SimpleNamespace())
        cog.store = ReminderStore(tmp_path / "reminders.db")

    def read_optouts(guild_id: int) -> set:
        if hidden is None:
            raise sqlite3.OperationalError("database is locked")
        return set(hidden)

    leaderboard = SimpleNamespace(store=SimpleNamespace(read_optouts=read_optouts))
    cogs = {"ReminderCog": cog, "LeaderboardCog": leaderboard}
    bot = SimpleNamespace(get_cog=lambda name: cogs.get(name))
    message = SimpleNamespace(author=SimpleNamespace(id=author_id))
    return SimpleNamespace(bot=bot, message=message, logger=SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None))


def _tools(runtime: SimpleNamespace) -> Dict[str, Any]:
    return {tool.name: tool for tool in ReminderTools(runtime).get_tools()}


def _add(runtime: SimpleNamespace, *, creator: int, message: str, due_at: float, target: int = 2) -> int:
    return runtime.bot.get_cog("ReminderCog").store.add(
        guild_id="7", channel_id=70, creator_id=creator, target_id=target, message=message, created_at=NOW, due_at=due_at
    )


def test_the_reminder_tools_are_registered(tmp_path: Path) -> None:
    assert set(_tools(_runtime(tmp_path))) == {"set_reminder", "list_reminders", "cancel_reminder"}


@pytest.mark.asyncio
async def test_listing_shows_only_the_callers_pending_reminders_with_their_ids(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, author_id=1)
    later = _add(runtime, creator=1, message="call mom", due_at=NOW + 7200)
    sooner = _add(runtime, creator=1, message="drink water", due_at=NOW + 600, target=3)
    _add(runtime, creator=5, message="someone else's secret", due_at=NOW + 60)

    text = await _tools(runtime)["list_reminders"].ainvoke({})

    assert "someone else's secret" not in text
    assert text.index(f"#{sooner}") < text.index(f"#{later}")
    assert "drink water" in text and "call mom" in text
    assert "<@3>" in text


@pytest.mark.asyncio
async def test_listing_never_names_a_member_who_hid(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, author_id=2, hidden={5, 3})
    _add(runtime, creator=5, target=2, message="from a hidden member", due_at=NOW + 60)
    _add(runtime, creator=2, target=3, message="for a hidden member", due_at=NOW + 120)
    _add(runtime, creator=2, target=4, message="for a visible member", due_at=NOW + 180)

    text = await _tools(runtime)["list_reminders"].ainvoke({})

    assert "<@5>" not in text and "<@3>" not in text
    assert "from a hidden member" in text and "for a hidden member" in text, "the caller still sees their own reminders"
    assert "<@4>" in text


@pytest.mark.asyncio
async def test_listing_names_nobody_while_the_opt_out_list_is_unreadable(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, author_id=2, hidden=None)
    _add(runtime, creator=5, target=2, message="from someone", due_at=NOW + 60)
    _add(runtime, creator=2, target=4, message="for someone", due_at=NOW + 120)

    text = await _tools(runtime)["list_reminders"].ainvoke({})

    assert "<@5>" not in text and "<@4>" not in text
    assert "from someone" in text and "for someone" in text


@pytest.mark.asyncio
async def test_listing_without_reminders_says_so(tmp_path: Path) -> None:
    text = await _tools(_runtime(tmp_path))["list_reminders"].ainvoke({})

    assert "no pending reminders" in text.lower()


@pytest.mark.asyncio
async def test_a_reminder_is_cancelled_by_its_creator(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, author_id=1)
    reminder_id = _add(runtime, creator=1, message="call mom", due_at=NOW + 600)

    text = await _tools(runtime)["cancel_reminder"].ainvoke({"reminder_id": reminder_id})

    assert "cancelled" in text.lower() and "call mom" in text
    assert runtime.bot.get_cog("ReminderCog").store.pending() == []


@pytest.mark.asyncio
async def test_someone_elses_reminder_cannot_be_cancelled(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, author_id=1)
    reminder_id = _add(runtime, creator=5, message="theirs", due_at=NOW + 600)

    text = await _tools(runtime)["cancel_reminder"].ainvoke({"reminder_id": reminder_id})

    assert "not found" in text.lower()
    assert len(runtime.bot.get_cog("ReminderCog").store.pending()) == 1


@pytest.mark.asyncio
async def test_the_member_a_reminder_is_for_can_cancel_it(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, author_id=2)
    reminder_id = _add(runtime, creator=5, target=2, message="from someone", due_at=NOW + 600)

    listing = await _tools(runtime)["list_reminders"].ainvoke({})
    text = await _tools(runtime)["cancel_reminder"].ainvoke({"reminder_id": reminder_id})

    assert "from someone" in listing and "others set for you" in listing
    assert "cancelled" in text.lower()
    assert runtime.bot.get_cog("ReminderCog").store.pending() == []


@pytest.mark.asyncio
async def test_cancelling_an_unknown_reminder_is_reported(tmp_path: Path) -> None:
    text = await _tools(_runtime(tmp_path))["cancel_reminder"].ainvoke({"reminder_id": 999})

    assert "not found" in text.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name, arguments", [("list_reminders", {}), ("cancel_reminder", {"reminder_id": 1})])
async def test_without_the_reminder_cog_the_tools_report_an_error(tmp_path: Path, tool_name: str, arguments: dict) -> None:
    text = await _tools(_runtime(tmp_path, with_cog=False))[tool_name].ainvoke(arguments)

    assert text.startswith("Error")
