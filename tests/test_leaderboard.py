"""Leaderboards, opt-outs, profiles and achievements."""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional
from zoneinfo import ZoneInfo

import pytest

from cogs.community_lib.achievements import (
    DEFAULT_ACHIEVEMENTS,
    Achievement,
    load_achievements,
    reached,
    stat_values,
)
from cogs.community_lib.limits import CommunityLimits
from cogs.community_lib.store import CommunityStore, GuildSettings
from cogs.leaderboard import LeaderboardCog
from cogs.memory.db.connection import DatabaseConnection
from cogs.memory.db.schema import create_tables
from cogs.memory.db.stats_storage import StatsStorage
from cogs.stats_cog import StatsCog
from dashboard.services.stats_collector import StatsCollector

ROOT = Path(__file__).resolve().parents[1]
GUILD_ID = 42
TAIPEI = ZoneInfo("Asia/Taipei")
NOW = datetime(2026, 10, 25, 12, 0, tzinfo=TAIPEI)  # a Sunday


@pytest.fixture
def store(tmp_path: Path) -> CommunityStore:
    return CommunityStore(tmp_path / "community.db")


# ------------------------------------------------------------------ store


# guild_settings as it shipped before achievement announcements.
_OLD_GUILD_SETTINGS = """
CREATE TABLE guild_settings (
    guild_id INTEGER PRIMARY KEY,
    announce_channel_id INTEGER,
    timezone TEXT,
    welcome_enabled INTEGER NOT NULL DEFAULT 0,
    welcome_channel_id INTEGER,
    welcome_note TEXT NOT NULL DEFAULT '',
    farewell_enabled INTEGER NOT NULL DEFAULT 0,
    birthday_enabled INTEGER NOT NULL DEFAULT 0,
    birthday_hour INTEGER NOT NULL DEFAULT 9,
    birthday_role_id INTEGER,
    anniversary_enabled INTEGER NOT NULL DEFAULT 0
)
"""


def test_an_older_database_gets_the_new_settings_column(tmp_path: Path) -> None:
    path = tmp_path / "community.db"
    with sqlite3.connect(path) as connection:
        connection.execute(_OLD_GUILD_SETTINGS)
        connection.execute("INSERT INTO guild_settings (guild_id, welcome_enabled) VALUES (?, 1)", (GUILD_ID,))

    store = CommunityStore(path)

    settings = store.get_settings(GUILD_ID)
    assert settings.welcome_enabled is True and settings.achievement_mode == "off"
    assert store.update_settings(GUILD_ID, achievement_mode="reply").achievement_mode == "reply"


def test_opt_outs_are_kept_per_guild(store: CommunityStore) -> None:
    store.set_optout(GUILD_ID, 7, True)
    store.set_optout(GUILD_ID, 7, True)
    store.set_optout(99, 8, True)

    assert store.optouts(GUILD_ID) == {7}
    store.set_optout(GUILD_ID, 7, False)
    assert not store.is_opted_out(GUILD_ID, 7) and store.is_opted_out(99, 8)


def test_an_achievement_is_unlocked_once(store: CommunityStore) -> None:
    assert store.unlock(GUILD_ID, 7, ["a", "b"], 100.0) == ["a", "b"]
    assert store.unlock(GUILD_ID, 7, ["b", "c"], 200.0) == ["c"]

    assert store.achievements(GUILD_ID, 7) == [("a", 100.0), ("b", 100.0), ("c", 200.0)]
    assert store.achievements(99, 7) == []
    assert not store.was_checked(GUILD_ID, 7)
    store.mark_checked(GUILD_ID, 7)
    assert store.was_checked(GUILD_ID, 7)


# ------------------------------------------------------------------ rankings


@pytest.fixture
def storage(tmp_path: Path) -> StatsStorage:
    db = DatabaseConnection(tmp_path / "procedural.db")
    with db.get_connection() as conn:
        create_tables(conn)
    return StatsStorage(db)


def _set_stats(storage: StatsStorage, user_id: str, total: int, streak: int, last: str) -> None:
    with storage.db.get_connection() as conn:
        conn.execute(
            "INSERT INTO user_stats (user_id, guild_id, total_messages, streak_days, streak_last_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, str(GUILD_ID), total, streak, last),
        )
        conn.commit()


@pytest.mark.asyncio
async def test_rankings_by_total_and_by_live_streak(storage: StatsStorage) -> None:
    _set_stats(storage, "1", 50, 3, "2026-10-25")
    _set_stats(storage, "2", 80, 9, "2026-10-24")
    _set_stats(storage, "3", 10, 20, "2026-10-23")  # streak broken: no message yesterday or today

    today = date(2026, 10, 25)

    assert await storage.get_guild_rankings(str(GUILD_ID), "total", today) == [("2", 80), ("1", 50), ("3", 10)]
    assert await storage.get_guild_rankings(str(GUILD_ID), "streak", today) == [("2", 9), ("1", 3)]


@pytest.mark.asyncio
async def test_upserting_a_message_returns_the_fresh_stats_and_the_previous_message_time(storage: StatsStorage) -> None:
    first = await storage.upsert_user_stats("1", str(GUILD_ID), "hi", "c", "2026-10-01T04:00:00+00:00")
    second = await storage.upsert_user_stats("1", str(GUILD_ID), "hi", "c", "2026-10-20T04:00:00+00:00")

    assert first["total_messages"] == 1 and first["previous_active_at"] is None
    assert second["total_messages"] == 2 and second["previous_active_at"] == "2026-10-01T04:00:00+00:00"


@pytest.mark.asyncio
async def test_message_counts_by_user_stay_inside_the_range(tmp_path: Path) -> None:
    collector = StatsCollector(str(tmp_path / "stats.db"))
    await collector.initialize()
    for user_id, moment in [("1", 100), ("1", 150), ("2", 120), ("2", 300), ("3", 99)]:
        await collector.record_message(str(GUILD_ID), user_id, "c", moment)
    await collector.record_message("other", "1", "c", 120)

    assert await collector.message_counts_by_user(str(GUILD_ID), 100, 200) == [("1", 2), ("2", 1)]


# ------------------------------------------------------------------ achievement rules


def test_stat_values_from_a_stats_row() -> None:
    now = datetime(2026, 10, 25, tzinfo=timezone.utc)
    stats = {
        "total_messages": 10,
        "streak_days": 4,
        "active_hours": {"1": 3, "4": 1, "5": 6},
        "previous_active_at": "2026-09-25T00:00:00+00:00",
        "first_message_at": "2025-10-25T00:00:00Z",
    }

    values = stat_values(stats, now)

    assert values == {
        "total_messages": 10.0,
        "streak_days": 4.0,
        "gap_days": 30.0,
        "night_ratio": 0.4,
        "membership_days": 365.0,
    }
    assert set(reached(DEFAULT_ACHIEVEMENTS, values)) == {"diver", "veteran"}
    assert stat_values({}, now)["gap_days"] == 0.0


def test_owner_achievements_replace_the_built_in_list_and_bad_entries_are_skipped() -> None:
    loaded = load_achievements(
        [
            {"id": "five", "emoji": "5️⃣", "name": "Five", "when": {"total_messages": 5}},
            {"id": "five", "when": {"total_messages": 6}},  # duplicate id
            {"id": "typo", "when": {"total_mesages": 5}},
            {"id": "text", "when": {"total_messages": "many"}},
            {"id": "empty"},
            {"when": {"total_messages": 1}},
            "not a mapping",
        ]
    )

    assert loaded == [Achievement("five", "5️⃣", {"total_messages": 5.0}, name="Five")]
    assert load_achievements(None) == DEFAULT_ACHIEVEMENTS


# ------------------------------------------------------------------ cog


class FakeLang:
    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        return f"{keys[-1]}|" + "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))


class FakeChannel:
    def __init__(self, channel_id: int = 500) -> None:
        self.id = channel_id
        self.sent: List[tuple] = []

    async def send(self, text: str, allowed_mentions: Any = None) -> None:
        self.sent.append((text, allowed_mentions))


class FakeMember:
    def __init__(self, member_id: int, bot: bool = False) -> None:
        self.id = member_id
        self.bot = bot
        self.display_name = f"user{member_id}"
        self.mention = f"<@{member_id}>"


class FakeGuild:
    def __init__(self) -> None:
        self.id = GUILD_ID
        self.channel = FakeChannel()
        self.system_channel = None
        self.members = {}

    def get_channel(self, channel_id: int) -> Optional[FakeChannel]:
        return self.channel if channel_id == self.channel.id else None

    def get_member(self, member_id: int) -> Optional[FakeMember]:
        return self.members.get(member_id)

    def add(self, member_id: int, bot: bool = False) -> FakeMember:
        self.members[member_id] = FakeMember(member_id, bot)
        return self.members[member_id]


class FakeMessage:
    def __init__(self, guild: FakeGuild, author: FakeMember) -> None:
        self.guild = guild
        self.author = author
        self.reactions: List[str] = []
        self.replies: List[tuple] = []

    async def add_reaction(self, emoji: str) -> None:
        self.reactions.append(emoji)

    async def reply(self, text: str, mention_author: bool = True, allowed_mentions: Any = None) -> None:
        self.replies.append((text, mention_author, allowed_mentions))


class FakeStorage:
    def __init__(self) -> None:
        self.rows = {"total": [], "streak": []}
        self.stats = {}

    async def get_guild_rankings(self, guild_id: str, kind: str) -> list:
        return self.rows[kind]

    async def get_user_stats(self, user_id: str, guild_id: str) -> Optional[dict]:
        return self.stats.get(user_id)


class FakeCollector:
    def __init__(self) -> None:
        self.calls: list = []

    async def message_counts_by_user(self, guild_id: str, since: float, until: float) -> list:
        self.calls.append((since, until))
        return [("10", 5), ("11", 3)]


@pytest.fixture
def guild() -> FakeGuild:
    return FakeGuild()


@pytest.fixture
def stats_storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def cog(store: CommunityStore, guild: FakeGuild, stats_storage: FakeStorage) -> LeaderboardCog:
    stats_cog = SimpleNamespace(stats_storage=stats_storage)
    bot = SimpleNamespace(
        stats_collector=FakeCollector(),
        get_cog=lambda name: stats_cog if name == "StatsCog" else None,
    )
    instance = LeaderboardCog(bot, store=store)
    instance.lang_manager = FakeLang()
    instance.limits = CommunityLimits(default_timezone="Asia/Taipei")
    instance._now = lambda: NOW.timestamp()
    store.update_settings(GUILD_ID, announce_channel_id=guild.channel.id)
    return instance


def _stats(total: int = 1, gap_days: float = 0) -> dict:
    previous = (NOW - timedelta(days=gap_days)).isoformat() if gap_days else None
    return {"total_messages": total, "streak_days": 1, "active_hours": {"12": total}, "previous_active_at": previous}


@pytest.mark.asyncio
async def test_progress_from_before_the_feature_is_recorded_quietly(
    cog: LeaderboardCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, achievement_mode="reply")
    message = FakeMessage(guild, guild.add(10))

    assert await cog.check_achievements(message, _stats(total=1500)) == ["msg_100", "msg_1000"]

    assert message.replies == [] and message.reactions == []
    assert [i for i, _ in store.achievements(GUILD_ID, 10)] == ["msg_100", "msg_1000"]


@pytest.mark.asyncio
async def test_a_long_silence_is_announced_even_on_the_first_check(
    cog: LeaderboardCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, achievement_mode="reply")
    message = FakeMessage(guild, guild.add(10))

    await cog.check_achievements(message, _stats(total=150, gap_days=40))

    assert message.reactions == ["🏆"]
    text, mention_author, allowed = message.replies[0]
    assert text == "unlocked|achievements=🤿 **diver|**|name=<@10>"
    assert mention_author is False and allowed.users is False


@pytest.mark.asyncio
async def test_new_achievements_are_announced_once_a_day_in_the_channel(
    cog: LeaderboardCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, achievement_mode="channel")
    member = guild.add(10)
    await cog.check_achievements(FakeMessage(guild, member), _stats(total=50))

    await cog.check_achievements(FakeMessage(guild, member), _stats(total=100))
    await cog.check_achievements(FakeMessage(guild, member), _stats(total=1000))

    assert [text for text, _ in guild.channel.sent] == ["unlocked|achievements=💬 **msg_100|**|name=<@10>"]
    assert [i for i, _ in store.achievements(GUILD_ID, 10)] == ["msg_100", "msg_1000"]


@pytest.mark.asyncio
async def test_nothing_is_announced_when_off_or_for_hidden_members(
    cog: LeaderboardCog, guild: FakeGuild, store: CommunityStore
) -> None:
    member, hidden = guild.add(10), guild.add(11)
    store.set_optout(GUILD_ID, hidden.id, True)
    for who in (member, hidden):
        await cog.check_achievements(FakeMessage(guild, who), _stats(total=50))

    await cog.check_achievements(FakeMessage(guild, member), _stats(total=100))  # mode is off
    store.update_settings(GUILD_ID, achievement_mode="channel")
    await cog.check_achievements(FakeMessage(guild, hidden), _stats(total=100))

    assert guild.channel.sent == []
    assert store.achievements(GUILD_ID, hidden.id)[0][0] == "msg_100"


@pytest.mark.asyncio
async def test_the_leaderboard_skips_bots_leavers_and_hidden_members(
    cog: LeaderboardCog, guild: FakeGuild, store: CommunityStore, stats_storage: FakeStorage
) -> None:
    for member_id in range(1, 14):
        guild.add(member_id, bot=member_id == 2)
    del guild.members[3]
    store.set_optout(GUILD_ID, 4, True)
    stats_storage.rows["total"] = [(str(i), 100 - i) for i in range(1, 14)]

    ranked = await cog.rankings(guild, "messages", "all")
    text = cog.leaderboard_text(GUILD_ID, ranked, "messages", "all", viewer_id=13)

    assert [member.id for member, _ in ranked] == [1, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    lines = text.splitlines()
    assert lines[0] == "title_all|"
    assert lines[1] == "🥇 **user1** — value_messages|count=99" and lines[4].startswith("`#4` **user7**")
    assert len(lines) == 11  # title and the top 10; the viewer is already in it
    assert "you_hidden|" in cog.leaderboard_text(GUILD_ID, ranked, "messages", "all", viewer_id=4)
    assert "you_unranked|" in cog.leaderboard_text(GUILD_ID, ranked[:3], "messages", "all", viewer_id=13)


@pytest.mark.asyncio
async def test_the_week_starts_on_the_local_monday(cog: LeaderboardCog, guild: FakeGuild) -> None:
    guild.add(10)
    guild.add(11)

    ranked = await cog.rankings(guild, "messages", "week")

    since, _ = cog.bot.stats_collector.calls[0]
    assert since == datetime(2026, 10, 19, tzinfo=TAIPEI).timestamp()
    assert [(member.id, value) for member, value in ranked] == [(10, 5), (11, 3)]
    await cog.rankings(guild, "messages", "month")
    assert cog.bot.stats_collector.calls[1][0] == datetime(2026, 10, 1, tzinfo=TAIPEI).timestamp()


@pytest.mark.asyncio
async def test_profiles_show_rank_and_badges(
    cog: LeaderboardCog, guild: FakeGuild, store: CommunityStore, stats_storage: FakeStorage
) -> None:
    member = guild.add(10)
    guild.add(11)
    stats_storage.rows["total"] = [("11", 9), ("10", 5)]
    stats_storage.stats["10"] = {"total_messages": 5, "streak_days": 1}
    store.unlock(GUILD_ID, 10, ["diver", "msg_100"], NOW.timestamp())

    text = await cog.profile_text(guild, member)

    assert "profile_rank|rank=2|total=2" in text
    assert f"profile_badges|badges=🤿 💬|done=2|total={len(DEFAULT_ACHIEVEMENTS)}" in text
    assert (await cog.profile_text(guild, guild.get_member(11))) == "no_stats|name=user11"


def test_the_achievement_list_shows_locked_and_unlocked_ones(cog: LeaderboardCog, store: CommunityStore) -> None:
    store.unlock(GUILD_ID, 10, ["msg_100"], datetime(2026, 10, 20, tzinfo=timezone.utc).timestamp())

    lines = cog.achievements_text(GUILD_ID, FakeMember(10)).splitlines()

    assert lines[0] == f"achievements_title|done=1|name=user10|total={len(DEFAULT_ACHIEVEMENTS)}"
    assert lines[1] == "✅ 💬 **msg_100|** — needs_total_messages|value=100 (2026-10-20)"
    assert lines[6].startswith("🔒 🦉 **night_owl|** — needs_night_ratio|value=40%")


@pytest.mark.asyncio
async def test_the_stats_cog_hands_fresh_stats_to_other_cogs(storage: StatsStorage) -> None:
    dispatched: list = []
    bot = SimpleNamespace(procedural_storage=SimpleNamespace(db=storage.db), dispatch=lambda *args: dispatched.append(args))
    stats_cog = StatsCog(bot)
    message = SimpleNamespace(
        guild=SimpleNamespace(id=GUILD_ID),
        author=SimpleNamespace(id=10, bot=False),
        channel=SimpleNamespace(id=5, name="general"),
        content="hello",
        created_at=datetime(2026, 10, 25, 4, 0, tzinfo=timezone.utc),
    )

    await stats_cog.on_message(message)

    name, sent_message, stats = dispatched[0]
    assert name == "user_stats_updated" and sent_message is message and stats["total_messages"] == 1


# ------------------------------------------------------------------ translations


@pytest.mark.parametrize("folder", ["en_US", "zh_TW", "zh_CN", "ja_JP"])
def test_every_language_has_the_same_leaderboard_texts(folder: str) -> None:
    def load(lang: str) -> dict:
        return json.loads((ROOT / "translations" / lang / "commands" / "leaderboard.json").read_text("utf-8"))

    data, english = load(folder), load("en_US")
    assert set(data["responses"]) == set(english["responses"])
    assert set(data["achievements"]) == {a.id for a in DEFAULT_ACHIEVEMENTS}


def test_achievement_modes_are_in_settings() -> None:
    assert GuildSettings(guild_id=1).achievement_mode == "off"
