"""Weekly word/emoji counts, per-message reaction counts and the played-song log.

These are collected now so weekly recaps and charts have history when they ship.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Iterator, Optional

import discord
import pytest

from cogs.memory.db.connection import DatabaseConnection
from cogs.memory.db.schema import create_tables
from cogs.memory.db.stats_storage import REACTIONS_KEEP_DAYS, StatsStorage, week_start
from cogs.music_lib.taste_store import PLAY_EVENTS_KEEP_SECONDS, TasteStore
from cogs.stats_cog import StatsCog

GUILD = "903273027993743381"
USER = "608669094580977665"
OTHER = "111111111111111111"
BOT_ID = 222222222222222222


@pytest.fixture
def storage(tmp_path: Path) -> StatsStorage:
    db = DatabaseConnection(tmp_path / "procedural.db")
    with db.get_connection() as conn:
        create_tables(conn)
    return StatsStorage(db)


@pytest.fixture(autouse=True)
def taipei_time(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TZ", "Asia/Taipei")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


# ------------------------------------------------------------ weekly terms


def test_a_week_starts_on_its_monday() -> None:
    assert week_start(datetime(2026, 10, 25, 23, 0)) == "2026-10-19"  # Sunday
    assert week_start(datetime(2026, 10, 26, 0, 30)) == "2026-10-26"  # Monday


@pytest.mark.asyncio
async def test_words_and_emojis_are_counted_per_local_week(storage: StatsStorage) -> None:
    # 2026-10-25 17:00 UTC is Monday 2026-10-26 01:00 in Taipei: a new week there.
    await storage.upsert_user_stats(USER, GUILD, "pizza 😀 😀", "1", "2026-10-25T15:00:00Z")
    await storage.upsert_user_stats(OTHER, GUILD, "pizza 😀", "1", "2026-10-25T15:30:00Z")
    await storage.upsert_user_stats(USER, GUILD, "pizza", "1", "2026-10-25T17:00:00Z")

    assert await storage.get_weekly_terms(GUILD, "2026-10-19", "emoji") == [("😀", 3)]
    assert await storage.get_weekly_terms(GUILD, "2026-10-19", "word") == [("pizza", 2)]
    assert await storage.get_weekly_terms(GUILD, "2026-10-26", "word") == [("pizza", 1)]
    assert await storage.get_weekly_terms("other-guild", "2026-10-19", "word") == []


@pytest.mark.asyncio
async def test_terms_can_be_counted_for_some_channels_only(storage: StatsStorage) -> None:
    await storage.upsert_user_stats(USER, GUILD, "pizza", "1", "2026-10-20T04:00:00Z")
    await storage.upsert_user_stats(USER, GUILD, "pizza", "2", "2026-10-20T04:00:00Z")
    await storage.upsert_user_stats(OTHER, GUILD, "secretproject secretproject", "3", "2026-10-20T04:00:00Z")

    assert await storage.get_weekly_terms(GUILD, "2026-10-19", "word") == [("pizza", 2), ("secretproject", 2)]
    assert await storage.get_weekly_terms(GUILD, "2026-10-19", "word", channel_ids=["1", "2"]) == [("pizza", 2)]
    assert await storage.get_weekly_terms(GUILD, "2026-10-19", "word", channel_ids=[]) == []


@pytest.mark.asyncio
async def test_a_quick_add_and_remove_of_a_reaction_leaves_nothing(storage: StatsStorage) -> None:
    import asyncio

    for _ in range(20):
        await asyncio.gather(
            storage.record_reaction("9", GUILD, "1", USER, 100.0, 1, reactor_id=OTHER),
            storage.record_reaction("9", GUILD, "1", None, 100.0, -1, reactor_id=OTHER),
        )

    assert await storage.reactions_by_author(GUILD, 0, 200) == []


@pytest.mark.asyncio
async def test_old_weeks_and_reactions_are_pruned(storage: StatsStorage) -> None:
    now = datetime(2026, 10, 25, 12, 0).astimezone()
    await storage.upsert_user_stats(USER, GUILD, "pizza", "1", "2026-01-05T04:00:00Z")
    await storage.upsert_user_stats(USER, GUILD, "pizza", "1", "2026-10-20T04:00:00Z")
    old = (now - timedelta(days=REACTIONS_KEEP_DAYS + 1)).timestamp()
    await storage.record_reaction("1", GUILD, "1", USER, old, 1)
    await storage.record_reaction("2", GUILD, "1", USER, now.timestamp(), 1)

    await storage.prune_activity_history(now)

    assert await storage.get_weekly_terms(GUILD, "2026-01-05", "word") == []
    assert await storage.get_weekly_terms(GUILD, "2026-10-19", "word") == [("pizza", 1)]
    top = await storage.get_top_reacted_messages(GUILD, 0, now.timestamp() + 1)
    assert [row["message_id"] for row in top] == ["2"]


# --------------------------------------------------------------- reactions


@pytest.mark.asyncio
async def test_reactions_are_counted_net_and_ranked(storage: StatsStorage) -> None:
    await storage.record_reaction("10", GUILD, "1", USER, 100.0, 1)
    await storage.record_reaction("10", GUILD, "1", USER, 100.0, 1)
    await storage.record_reaction("20", GUILD, "1", OTHER, 200.0, 1)
    await storage.record_reaction("20", GUILD, "1", None, 200.0, -1, reactor_id=USER)
    await storage.record_reaction("20", GUILD, "1", None, 200.0, -1, reactor_id=USER)  # never below zero
    await storage.record_reaction("30", GUILD, "1", None, 300.0, -1, reactor_id=USER)  # unknown message

    top = await storage.get_top_reacted_messages(GUILD, 0, 1000)

    assert [(row["message_id"], row["count"], row["author_id"]) for row in top] == [("10", 2, USER)]


@pytest.mark.asyncio
async def test_removing_an_own_reaction_does_not_lower_the_count(storage: StatsStorage) -> None:
    await storage.record_reaction("10", GUILD, "1", USER, 100.0, 1)

    await storage.record_reaction("10", GUILD, "1", None, 100.0, -1, reactor_id=USER)

    assert (await storage.get_top_reacted_messages(GUILD, 0, 1000))[0]["count"] == 1


@pytest.mark.asyncio
async def test_the_top_reacted_messages_stay_inside_the_time_range(storage: StatsStorage) -> None:
    await storage.record_reaction("10", GUILD, "1", USER, 100.0, 1)
    await storage.record_reaction("20", GUILD, "1", USER, 200.0, 1)

    top = await storage.get_top_reacted_messages(GUILD, 150, 250)

    assert [row["message_id"] for row in top] == ["20"]


def _member(member_id: int, bot: bool = False) -> SimpleNamespace:
    return SimpleNamespace(id=member_id, bot=bot)


def _cog(storage: StatsStorage, members: dict) -> StatsCog:
    guild = SimpleNamespace(get_member=members.get)
    bot = SimpleNamespace(
        procedural_storage=SimpleNamespace(db=storage.db),
        get_guild=lambda guild_id: guild if guild_id == int(GUILD) else None,
    )
    return StatsCog(bot)


def _payload(
    message_id: int, user_id: int, author_id: Optional[int], member: Optional[SimpleNamespace] = None
) -> SimpleNamespace:
    return SimpleNamespace(
        message_id=message_id,
        user_id=user_id,
        channel_id=1,
        guild_id=int(GUILD),
        message_author_id=author_id,
        member=member,
    )


@pytest.mark.asyncio
async def test_the_stats_cog_counts_reactions_from_people_on_peoples_messages(storage: StatsStorage) -> None:
    members = {int(USER): _member(int(USER)), int(OTHER): _member(int(OTHER)), BOT_ID: _member(BOT_ID, bot=True)}
    cog = _cog(storage, members)
    message_id = discord.utils.time_snowflake(datetime(2026, 10, 20, 12, 0).astimezone())

    await cog.on_raw_reaction_add(_payload(message_id, int(OTHER), int(USER), members[int(OTHER)]))
    await cog.on_raw_reaction_add(_payload(message_id, int(USER), int(USER), members[int(USER)]))  # own message
    await cog.on_raw_reaction_add(_payload(message_id, BOT_ID, int(USER), members[BOT_ID]))  # a bot reacting
    bot_message = message_id + 1
    await cog.on_raw_reaction_add(_payload(bot_message, int(OTHER), BOT_ID, members[int(OTHER)]))  # bot's message
    await cog.on_raw_reaction_remove(_payload(message_id, BOT_ID, None))

    top = await storage.get_top_reacted_messages(GUILD, 0, time.time())

    assert [(row["message_id"], row["count"]) for row in top] == [(str(message_id), 1)]
    assert top[0]["created_at"] == pytest.approx(datetime(2026, 10, 20, 12, 0).astimezone().timestamp(), abs=1)

    await cog.on_raw_reaction_remove(_payload(message_id, int(OTHER), None))

    assert await storage.get_top_reacted_messages(GUILD, 0, time.time()) == []


# ------------------------------------------------------------ played songs


@pytest.fixture
def taste(tmp_path: Path) -> TasteStore:
    return TasteStore(tmp_path / "music" / "taste.db")


def test_played_songs_are_charted_per_guild_and_time_range(taste: TasteStore) -> None:
    taste.add_play_event(1, "a", "Song A", requester_id=5, autoplay=False, played_at=100)
    skipped = taste.add_play_event(1, "a", "Song A", requester_id=6, autoplay=False, played_at=200)
    taste.add_play_event(1, "b", "Song B", requester_id=None, autoplay=True, played_at=300)
    taste.add_play_event(2, "c", "Song C", requester_id=5, autoplay=False, played_at=300)
    taste.add_play_event(1, "d", "Song D", requester_id=5, autoplay=False, played_at=900)
    taste.mark_play_skipped(skipped, 4.5)

    assert taste.top_played(1, 0, 500) == [("a", "Song A", 2, 1), ("b", "Song B", 1, 0)]
    assert taste.top_played(2, 0, 500) == [("c", "Song C", 1, 0)]


def test_played_songs_past_the_kept_period_are_dropped(taste: TasteStore) -> None:
    now = 1_800_000_000.0
    taste.add_play_event(1, "old", "Old", requester_id=5, autoplay=False, played_at=now - PLAY_EVENTS_KEEP_SECONDS - 1)

    taste.add_play_event(1, "new", "New", requester_id=5, autoplay=False, played_at=now)

    assert [row[0] for row in taste.top_played(1, 0, now + 1)] == ["new"]


def test_a_play_log_failure_does_not_raise(tmp_path: Path) -> None:
    blocker = tmp_path / "not-a-folder"
    blocker.write_text("", encoding="utf-8")

    assert TasteStore(blocker / "taste.db").add_play_event(1, "a", "A", 5, False) is None


def test_very_long_words_are_not_counted() -> None:
    from cogs.memory.db.stats_storage import MAX_WORD_CHARS, _segment_words

    words = _segment_words("pizza " + "a" * (MAX_WORD_CHARS + 1))
    assert "pizza" in words and all(len(w) <= MAX_WORD_CHARS for w in words)
