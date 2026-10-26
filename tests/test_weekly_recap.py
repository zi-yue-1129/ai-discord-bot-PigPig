"""The weekly server recap: when it is due, what goes in it, rotating titles and who is left out."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional
from zoneinfo import ZoneInfo

import discord
import pytest

from cogs import community as community_module
from cogs.community import CommunityCog
from cogs.community_lib.limits import CommunityLimits
from cogs.community_lib.recap import Recap, format_recap, recap_week_due
from cogs.community_lib.store import CommunityStore
from cogs.memory.db.connection import DatabaseConnection
from cogs.memory.db.schema import create_tables
from cogs.memory.db.stats_storage import StatsStorage
from cogs.music_lib.taste_store import TasteStore
from dashboard.services.stats_collector import StatsCollector

GUILD_ID = 42
TAIPEI = ZoneInfo("Asia/Taipei")
MONDAY = datetime(2026, 10, 19, tzinfo=TAIPEI)
SUNDAY_EVENING = datetime(2026, 10, 25, 20, 0, tzinfo=TAIPEI)


# ------------------------------------------------------------------ timing


def test_a_recap_is_due_from_its_hour_for_a_day() -> None:
    assert recap_week_due(datetime(2026, 10, 25, 19, 59, tzinfo=TAIPEI), 6, 20) is None
    assert recap_week_due(SUNDAY_EVENING, 6, 20) == MONDAY
    # The bot was down on Sunday evening: Monday morning still posts last week's recap.
    assert recap_week_due(datetime(2026, 10, 26, 9, 0, tzinfo=TAIPEI), 6, 20) == MONDAY
    assert recap_week_due(datetime(2026, 10, 26, 20, 1, tzinfo=TAIPEI), 6, 20) is None
    # A Monday 9:00 recap is due on Monday itself.
    assert recap_week_due(datetime(2026, 10, 26, 9, 0, tzinfo=TAIPEI), 0, 9) == datetime(2026, 10, 26, tzinfo=TAIPEI)


def test_the_owner_sets_the_recap_limits() -> None:
    limits = CommunityLimits.from_config({"weekly": {"min_messages": 10, "use_ai": False, "missing_max": 0}})

    assert (limits.weekly_min_messages, limits.weekly_use_ai, limits.missing_max) == (10, False, 0)
    assert CommunityLimits.from_config(None).weekly_max_report_chars == 300


# ------------------------------------------------------------------ queries


@pytest.mark.asyncio
async def test_channel_and_night_counts(tmp_path: Path) -> None:
    collector = StatsCollector(str(tmp_path / "stats.db"))
    await collector.initialize()
    noon = datetime(2026, 10, 20, 12, 0, tzinfo=TAIPEI).timestamp()
    night = datetime(2026, 10, 21, 2, 30, tzinfo=TAIPEI).timestamp()
    for user_id, channel_id, moment in [("1", "a", noon), ("1", "a", night), ("2", "b", night), ("2", "b", night + 60)]:
        await collector.record_message(str(GUILD_ID), user_id, channel_id, moment)

    since, until = MONDAY.timestamp(), SUNDAY_EVENING.timestamp()
    assert await collector.message_counts_by_channel(str(GUILD_ID), since, until) == [("a", 2), ("b", 2)]
    assert await collector.night_counts_by_user(str(GUILD_ID), since, until, 8 * 3600) == [("2", 2), ("1", 1)]
    # Without the messages of excluded members (the ones hidden with /leaderboard optout).
    assert await collector.message_counts_by_channel(str(GUILD_ID), since, until, exclude_user_ids=["1"]) == [("b", 2)]
    assert await collector.message_counts_by_channel(str(GUILD_ID), since, until, exclude_user_ids=[]) == [("a", 2), ("b", 2)]


@pytest.fixture
def storage(tmp_path: Path) -> StatsStorage:
    db = DatabaseConnection(tmp_path / "procedural.db")
    with db.get_connection() as conn:
        create_tables(conn)
    return StatsStorage(db)


@pytest.mark.asyncio
async def test_reactions_are_summed_per_author_and_regulars_listed(storage: StatsStorage) -> None:
    await storage.record_reaction("1", str(GUILD_ID), "5", "10", 100.0, 1)
    await storage.record_reaction("1", str(GUILD_ID), "5", "10", 100.0, 1)
    await storage.record_reaction("2", str(GUILD_ID), "5", "10", 150.0, 1)
    await storage.record_reaction("3", str(GUILD_ID), "5", "11", 120.0, 1)
    await storage.record_reaction("4", str(GUILD_ID), "5", "11", 900.0, 1)  # outside the range
    for _ in range(3):
        await storage.upsert_user_stats("10", str(GUILD_ID), "hi", "5", "2026-09-01T00:00:00+00:00")
    await storage.upsert_user_stats("11", str(GUILD_ID), "hi", "5", "2026-09-01T00:00:00+00:00")

    assert await storage.reactions_by_author(str(GUILD_ID), 0, 500) == [("10", 3), ("11", 1)]
    regulars = await storage.get_regulars(str(GUILD_ID), 2)
    assert [(row["user_id"], row["total_messages"]) for row in regulars] == [("10", 3)]


def test_requesters_are_counted_without_autoplay(tmp_path: Path) -> None:
    taste = TasteStore(tmp_path / "taste.db")
    for requester, autoplay in [(5, False), (5, False), (6, False), (None, True)]:
        taste.add_play_event(GUILD_ID, "a", "A", requester_id=requester, autoplay=autoplay, played_at=100)

    assert taste.top_requesters(GUILD_ID, 0, 200) == [(5, 2), (6, 1)]


def test_titles_are_replaced_each_week(tmp_path: Path) -> None:
    store = CommunityStore(tmp_path / "community.db")
    store.set_titles(GUILD_ID, "2026-10-12", {"talker": 10, "dj": 11})
    store.set_titles(GUILD_ID, "2026-10-19", {"talker": 11, "funny": 11})

    assert store.titles_of(GUILD_ID, 10) == []
    assert store.titles_of(GUILD_ID, 11) == ["funny", "talker"]
    settings = store.get_settings(GUILD_ID)
    assert (settings.weekly_enabled, settings.weekly_day, settings.weekly_hour) == (False, 6, 20)


# ------------------------------------------------------------------ cog


class FakeLang:
    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        return f"{keys[-1]}|" + "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content
        self.jump_url = "https://discord.com/channels/42/500/1"


class FakeChannel:
    def __init__(self, channel_id: int, messages: Optional[dict] = None, public: bool = True) -> None:
        self.id = channel_id
        self.name = f"chan{channel_id}"
        self.mention = f"<#{channel_id}>"
        self.messages = messages or {}
        self.public = public
        self.sent: List[dict] = []
        self.fail_sends = 0
        self.type = discord.ChannelType.text
        self.guild: Any = None  # set when added to a FakeGuild
        self.overwrites: dict = {}

    def permissions_for(self, role: Any) -> SimpleNamespace:
        assert role == "@everyone"
        return SimpleNamespace(view_channel=self.public, read_message_history=self.public)

    async def send(self, content: Any = None, **kwargs: Any) -> None:
        if self.fail_sends:
            self.fail_sends -= 1
            raise discord.HTTPException(SimpleNamespace(status=503, reason="Service Unavailable"), "try again")
        self.sent.append(kwargs)

    async def fetch_message(self, message_id: int) -> FakeMessage:
        if message_id not in self.messages:
            raise discord.NotFound(SimpleNamespace(status=404, reason="Not Found"), "gone")
        return self.messages[message_id]


class FakeMember:
    def __init__(self, member_id: int, bot: bool = False) -> None:
        self.id = member_id
        self.bot = bot
        self.display_name = f"user{member_id}"
        self.mention = f"<@{member_id}>"


class ChannelMap(dict):
    """Channels by id, iterated like ``guild.channels`` (the channels themselves)."""

    def __init__(self, guild: Any, channels: dict) -> None:
        super().__init__()
        self.guild = guild
        for channel_id, channel in channels.items():
            self[channel_id] = channel

    def __setitem__(self, channel_id: int, channel: Any) -> None:
        channel.guild = self.guild
        super().__setitem__(channel_id, channel)

    def __iter__(self) -> Any:
        return iter(list(self.values()))


class FakeGuild:
    def __init__(self) -> None:
        self.id = GUILD_ID
        self.name = "Pig Land"
        self.system_channel = None
        self.default_role = "@everyone"
        self.channel = FakeChannel(500, {2: FakeMessage("best joke ever")})
        self.channels = ChannelMap(self, {500: self.channel, 501: FakeChannel(501)})
        self.members = {i: FakeMember(i) for i in (10, 11, 12, 13)}
        self.members[99] = FakeMember(99, bot=True)
        self.threads: list = []

    def get_channel(self, channel_id: int) -> Optional[FakeChannel]:
        return self.channels.get(channel_id)

    def get_member(self, member_id: int) -> Optional[FakeMember]:
        return self.members.get(member_id)


class FakeCollector:
    def __init__(self, week: list, last_week: list) -> None:
        self.week, self.last_week = week, last_week

    async def message_counts_by_user(self, guild_id: str, since: float, until: float) -> list:
        return self.week if since >= MONDAY.timestamp() else self.last_week

    async def message_counts_by_channel(self, guild_id: str, since: float, until: float, exclude_user_ids: Any = ()) -> list:
        return [("501", 40), ("missing", 5), ("500", 20)]

    async def night_counts_by_user(self, guild_id: str, since: float, until: float, offset: float) -> list:
        assert offset == 8 * 3600
        return [("13", 9), ("12", 4)]


class FakeStorage:
    async def get_weekly_terms(self, guild_id: str, week: str, kind: str, limit: int, channel_ids: Any = None) -> list:
        assert week == "2026-10-19"
        if channel_ids is not None and "500" not in channel_ids:
            return []
        return [("😂", 12)] if kind == "emoji" else [("pizza", 8), ("exam", 3)]

    async def reactions_by_author(self, guild_id: str, since: float, until: float) -> list:
        return [("13", 7), ("11", 5)]

    async def get_top_reacted_messages(self, guild_id: str, since: float, until: float, limit: int) -> list:
        return [
            {"message_id": "1", "channel_id": "500", "author_id": "13", "count": 9},  # hidden author
            {"message_id": "3", "channel_id": "500", "author_id": "11", "count": 6},  # deleted
            {"message_id": "2", "channel_id": "500", "author_id": "11", "count": 5},
        ]

    async def get_regulars(self, guild_id: str, min_messages: int) -> list:
        return [
            {"user_id": "12", "total_messages": 900, "last_active_at": "2026-09-01T00:00:00+00:00"},
            {"user_id": "11", "total_messages": 500, "last_active_at": "2026-10-24T00:00:00+00:00"},
            {"user_id": "77", "total_messages": 400, "last_active_at": "2026-01-01T00:00:00+00:00"},  # left
        ]


class FakeTaste:
    def top_played(self, guild_id: int, since: float, until: float, limit: int) -> list:
        return [("skipme", "Skipped a lot", 4, 3), ("vid", "Theme Song", 3, 1)]

    def top_requesters(self, guild_id: int, since: float, until: float, limit: int) -> list:
        return [(99, 8), (12, 3)]


@pytest.fixture
def guild() -> FakeGuild:
    return FakeGuild()


@pytest.fixture
def store(tmp_path: Path) -> CommunityStore:
    return CommunityStore(tmp_path / "community.db")


@pytest.fixture
def cog(store: CommunityStore, guild: FakeGuild) -> CommunityCog:
    cogs = {"StatsCog": SimpleNamespace(stats_storage=FakeStorage()), "YTMusic": SimpleNamespace(_taste_store=FakeTaste())}
    bot = SimpleNamespace(
        user=SimpleNamespace(id=1),
        orchestrator=None,
        stats_collector=FakeCollector([("13", 50), ("11", 30), ("99", 20), ("10", 5)], [("11", 80)]),
        get_cog=cogs.get,
        get_guild=lambda guild_id: guild if guild_id == GUILD_ID else None,
    )
    instance = CommunityCog(bot, store=store)
    instance.lang_manager = FakeLang()
    instance.limits = CommunityLimits(default_timezone="Asia/Taipei", weekly_min_messages=50)
    store.update_settings(GUILD_ID, announce_channel_id=500)
    store.set_optout(GUILD_ID, 13, True)
    return instance


@pytest.mark.asyncio
async def test_the_recap_is_posted_once_with_titles_and_without_hidden_members(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, weekly_enabled=True, weekly_channel_id=501)
    cog._now = lambda: SUNDAY_EVENING.timestamp()

    await cog.run_daily_jobs()
    await cog.run_daily_jobs()

    assert len(guild.channels[501].sent) == 1
    sent = guild.channels[501].sent[0]
    embed = sent["embed"]
    fields = {field.name: field.value for field in embed.fields}
    assert sent["allowed_mentions"].users is False
    assert embed.title == "weekly_title|guild=Pig Land"
    assert embed.description == "weekly_intro|total=55"  # the hidden member's 50 messages are not counted
    assert fields["weekly_messages|"] == "**55** weekly_trend|change=-31%|previous=80"
    assert fields["weekly_channels|"] == "<#501> · 40\n<#500> · 20"
    assert fields["weekly_talkers|"] == "<@11> · 30\n<@10> · 5"
    assert "best joke ever" in fields["weekly_quote|count=5"] and "<@11>" in fields["weekly_quote|count=5"]
    assert fields["weekly_song|"].startswith("[Theme Song](https://www.youtube.com/watch?v=vid)")
    assert fields["weekly_titles|"] == "🎤 title_talker|：<@11>\n🌙 title_night_owl|：<@12>\n😂 title_funny|：<@11>\n🎧 title_dj|：<@12>"
    assert fields["weekly_missing|"] == "weekly_missing_line|days=54|name=<@12>"
    assert "13" not in str(fields)
    assert store.titles_of(GUILD_ID, 11) == ["funny", "talker"]
    assert store.titles_of(GUILD_ID, 12) == ["dj", "night_owl"]


@pytest.mark.asyncio
async def test_a_quiet_week_is_skipped_but_can_still_be_previewed(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore
) -> None:
    cog.bot.stats_collector.week = [("11", 10)]
    settings = store.update_settings(GUILD_ID, weekly_enabled=True)

    assert await cog.post_weekly_recap(guild, settings, MONDAY, SUNDAY_EVENING) is None
    preview = await cog.post_weekly_recap(guild, settings, MONDAY, SUNDAY_EVENING, preview_channel=guild.channel)

    assert preview is not None and guild.channel.sent == []
    assert store.titles_of(GUILD_ID, 11) == []


@pytest.mark.asyncio
async def test_the_model_writes_the_news_paragraph_when_available(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list = []

    async def fake_compose(orchestrator: Any, bot: Any, channel: Any, task: str, facts: str, mentions: Any) -> str:
        seen.append(facts)
        return "Breaking news: pizza wins again."

    # Patch the globals the cog really uses (other test files may re-import cogs modules).
    monkeypatch.setitem(CommunityCog._write.__globals__, "compose_announcement", fake_compose)
    cog.bot.orchestrator = object()
    settings = store.get_settings(GUILD_ID)

    embed = await cog.post_weekly_recap(guild, settings, MONDAY, SUNDAY_EVENING)

    assert embed.description == "Breaking news: pizza wins again."
    assert "<<<user11>>>" in seen[0] and "<<<best joke ever>>>" in seen[0] and "user13" not in seen[0]


def test_an_empty_recap_shows_only_the_message_count() -> None:
    recap = Recap(week="2026-10-19", start=MONDAY, end=SUNDAY_EVENING, total=60)

    embed = format_recap(recap, lambda key, **kw: key, lambda title_id: title_id, "Pig Land", None)

    assert [field.name for field in embed.fields] == ["weekly_messages"]
    assert embed.fields[0].value == "**60**"


def test_weekday_choices_cover_the_week() -> None:
    assert [choice.value for choice in community_module._WEEKDAYS] == list(range(7))
    assert timedelta(days=6) + MONDAY == datetime(2026, 10, 25, tzinfo=TAIPEI)
    assert SUNDAY_EVENING.astimezone(timezone.utc).hour == 12


@pytest.mark.asyncio
async def test_private_channels_are_never_named_or_quoted(cog: CommunityCog, guild: FakeGuild, store: CommunityStore) -> None:
    secret = FakeChannel(502, {4: FakeMessage("staff only secret")}, public=False)
    guild.channels[502] = secret
    cog.bot.stats_collector.message_counts_by_channel = lambda *args: _rows([("502", 90), ("500", 20)])

    async def top_reacted(*args: Any) -> list:
        return [
            {"message_id": "4", "channel_id": "502", "author_id": "11", "count": 9},
            {"message_id": "2", "channel_id": "500", "author_id": "11", "count": 5},
        ]

    cog.bot.get_cog("StatsCog").stats_storage.get_top_reacted_messages = top_reacted
    embed = await cog.post_weekly_recap(guild, store.get_settings(GUILD_ID), MONDAY, SUNDAY_EVENING)

    fields = {field.name: field.value for field in embed.fields}
    assert fields["weekly_channels|"] == "<#500> · 20"
    assert "best joke ever" in fields["weekly_quote|count=5"]
    assert "secret" not in str(fields) and "502" not in str(fields)


@pytest.mark.asyncio
async def test_hot_words_and_emojis_only_count_public_channels(cog: CommunityCog, guild: FakeGuild, store: CommunityStore) -> None:
    guild.channels[502] = FakeChannel(502, public=False)
    seen: list = []

    async def terms(guild_id: str, week: str, kind: str, limit: int, channel_ids: Any = None) -> list:
        seen.append(channel_ids)
        return []

    cog.bot.get_cog("StatsCog").stats_storage.get_weekly_terms = terms
    await cog.post_weekly_recap(guild, store.get_settings(GUILD_ID), MONDAY, SUNDAY_EVENING)

    assert seen and all(sorted(ids) == ["500", "501"] for ids in seen)


async def _rows(rows: list) -> list:
    return rows


@pytest.mark.asyncio
async def test_spam_words_are_left_out_and_fields_fit_discord(cog: CommunityCog, guild: FakeGuild, store: CommunityStore) -> None:
    async def terms(guild_id: str, week: str, kind: str, limit: int, channel_ids: Any = None) -> list:
        return [("😂", 12)] if kind == "emoji" else [("哈" * 1100, 50), ("pizza", 8)]

    cog.bot.get_cog("StatsCog").stats_storage.get_weekly_terms = terms
    embed = await cog.post_weekly_recap(guild, store.get_settings(GUILD_ID), MONDAY, SUNDAY_EVENING)

    fields = {field.name: field.value for field in embed.fields}
    assert fields["weekly_words|"] == "pizza"
    long = Recap(week="2026-10-19", start=MONDAY, end=SUNDAY_EVENING, total=60, words=[("x" * 30, 1)] * 60)
    embed = format_recap(long, lambda key, **kw: key, lambda title_id: title_id, "Pig Land", None)
    assert all(len(field.value) <= 1024 for field in embed.fields)


@pytest.mark.asyncio
async def test_a_recap_that_could_not_be_posted_is_retried(cog: CommunityCog, guild: FakeGuild, store: CommunityStore) -> None:
    store.update_settings(GUILD_ID, weekly_enabled=True, weekly_channel_id=501)
    cog._now = lambda: SUNDAY_EVENING.timestamp()
    guild.channels[501].fail_sends = 1

    await cog.run_daily_jobs()
    assert guild.channels[501].sent == [] and store.titles_of(GUILD_ID, 11) == []
    cog._now = lambda: SUNDAY_EVENING.timestamp() + CommunityCog.CHECK_SECONDS
    await cog.run_daily_jobs()
    await cog.run_daily_jobs()

    assert len(guild.channels[501].sent) == 1
    assert store.titles_of(GUILD_ID, 11) == ["funny", "talker"]


def test_a_thread_whose_parent_is_not_cached_is_left_out(guild: FakeGuild) -> None:
    from cogs.community_lib.recap import public_channel_ids

    def no_parent(role: Any) -> Any:
        raise discord.ClientException("Parent channel not found")

    guild.threads = [SimpleNamespace(id=900, type=discord.ChannelType.public_thread, permissions_for=no_parent)]

    assert sorted(public_channel_ids(guild)) == ["500", "501"]


def test_a_private_thread_under_a_public_channel_is_not_public(guild: FakeGuild) -> None:
    from cogs.community_lib.recap import is_public

    everyone_can = lambda role: SimpleNamespace(view_channel=True, read_message_history=True)
    private = SimpleNamespace(id=901, type=discord.ChannelType.private_thread, permissions_for=everyone_can)
    public = SimpleNamespace(id=902, type=discord.ChannelType.public_thread, permissions_for=everyone_can, parent=guild.channel)

    assert is_public(guild, private) is False
    assert is_public(guild, public) is True


class _Overwrite:
    def __init__(self, **deny: bool) -> None:
        self.deny = discord.Permissions(**deny)

    def pair(self) -> tuple:
        return discord.Permissions.none(), self.deny


def test_a_channel_that_denies_a_role_is_not_public(guild: FakeGuild) -> None:
    from cogs.community_lib.recap import is_public, public_channel_ids

    guild.channels[501].overwrites = {"staff-only-role": _Overwrite(view_channel=True)}

    assert is_public(guild, guild.channels[501]) is False
    assert public_channel_ids(guild) == ["500"]


@pytest.mark.asyncio
async def test_hidden_members_messages_are_left_out_of_both_weeks_totals(cog: CommunityCog, guild: FakeGuild) -> None:
    from cogs.community_lib.recap import RecapBuilder

    cog.bot.stats_collector = FakeCollector([("13", 50), ("11", 30), ("not-a-member", 4)], [("13", 40), ("11", 10)])

    recap = await RecapBuilder(cog.bot, cog.limits).build(guild, MONDAY, SUNDAY_EVENING, {13})

    assert recap.total == 34 and recap.previous_total == 10  # a row that is no member id cannot be told apart: counted


@pytest.mark.asyncio
async def test_hidden_members_messages_are_left_out_of_the_channel_counts(cog: CommunityCog, guild: FakeGuild) -> None:
    from cogs.community_lib.recap import RecapBuilder

    class ByChannel(FakeCollector):
        async def message_counts_by_channel(self, guild_id: str, since: float, until: float, exclude_user_ids: Any = ()) -> list:
            return [("500", 20 if "13" in set(exclude_user_ids) else 70)]

    cog.bot.stats_collector = ByChannel([("13", 50), ("11", 30)], [])

    recap = await RecapBuilder(cog.bot, cog.limits).build(guild, MONDAY, SUNDAY_EVENING, {13})

    assert [count for _channel, count in recap.channels] == [20]  # the 50 hidden messages would show as 70
