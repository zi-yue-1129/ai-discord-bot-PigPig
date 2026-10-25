"""Community features: settings storage, date rules, welcome batching and the daily celebrations."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional
from zoneinfo import ZoneInfo

import pytest

from cogs import community as community_module
from cogs.community import CommunityCog
from cogs.community_lib.dates import (
    anniversary_years,
    birthdays_on,
    celebrated_on,
    is_valid_birthday,
    local_now,
    upcoming_birthdays,
)
from cogs.community_lib.joins import JoinTracker
from cogs.community_lib.limits import CommunityLimits
from cogs.community_lib.store import CommunityStore, GuildSettings

ROOT = Path(__file__).resolve().parents[1]
GUILD_ID = 42
TAIPEI = ZoneInfo("Asia/Taipei")


# ------------------------------------------------------------------ store


@pytest.fixture
def store(tmp_path: Path) -> CommunityStore:
    return CommunityStore(tmp_path / "community.db")


def test_a_new_guild_has_every_feature_off(store: CommunityStore) -> None:
    assert store.get_settings(GUILD_ID) == GuildSettings(guild_id=GUILD_ID)


def test_settings_changes_are_kept(store: CommunityStore) -> None:
    store.update_settings(GUILD_ID, welcome_enabled=True, welcome_note="read #rules")
    store.update_settings(GUILD_ID, birthday_enabled=True, birthday_hour=8)

    settings = CommunityStore(store.path).get_settings(GUILD_ID)

    assert settings.welcome_enabled is True and settings.welcome_note == "read #rules"
    assert settings.birthday_enabled is True and settings.birthday_hour == 8
    assert settings.anniversary_enabled is False
    assert [s.guild_id for s in store.guilds_with_daily_jobs()] == [GUILD_ID]


def test_unknown_settings_are_refused(store: CommunityStore) -> None:
    with pytest.raises(TypeError):
        store.update_settings(GUILD_ID, nonsense=True)


def test_birthdays_are_kept_per_guild(store: CommunityStore) -> None:
    store.set_birthday(GUILD_ID, 7, 3, 14)
    store.set_birthday(GUILD_ID, 7, 4, 1)  # replaces
    store.set_birthday(99, 7, 12, 25)

    assert store.get_birthday(GUILD_ID, 7) == (4, 1)
    assert store.birthdays(99) == [(7, 12, 25)]
    assert store.remove_birthday(GUILD_ID, 7) is True
    assert store.remove_birthday(GUILD_ID, 7) is False
    assert store.get_birthday(99, 7) == (12, 25)


def test_a_job_is_claimed_once_per_period(store: CommunityStore) -> None:
    assert store.claim_run(GUILD_ID, "birthday", "2026-10-25") is True
    assert store.claim_run(GUILD_ID, "birthday", "2026-10-25") is False
    assert store.claim_run(GUILD_ID, "anniversary", "2026-10-25") is True
    assert store.claim_run(GUILD_ID, "birthday", "2026-10-26") is True


# ------------------------------------------------------------------ dates


def test_feb_29_is_celebrated_on_feb_28_in_common_years() -> None:
    assert celebrated_on(2, 29, 2027) == (2, 28)
    assert celebrated_on(2, 29, 2028) == (2, 29)
    assert is_valid_birthday(2, 29) and not is_valid_birthday(2, 30) and not is_valid_birthday(13, 1)


def test_birthdays_today() -> None:
    rows = [(1, 10, 25), (2, 2, 29), (3, 10, 26)]

    assert birthdays_on(date(2026, 10, 25), rows) == [1]
    assert birthdays_on(date(2027, 2, 28), rows) == [2]


def test_anniversaries_count_full_years_on_the_local_join_day() -> None:
    # 2024-10-24 18:00 UTC is 2024-10-25 02:00 in Taipei.
    joined = datetime(2024, 10, 24, 18, 0, tzinfo=timezone.utc)

    assert anniversary_years(date(2026, 10, 25), joined, TAIPEI) == 2
    assert anniversary_years(date(2026, 10, 24), joined, TAIPEI) == 0
    assert anniversary_years(date(2024, 10, 25), joined, TAIPEI) == 0  # the join day itself
    assert anniversary_years(date(2026, 10, 25), None, TAIPEI) == 0


def test_upcoming_birthdays_wrap_into_next_year() -> None:
    rows = [(1, 1, 5), (2, 12, 30), (3, 6, 1)]

    assert upcoming_birthdays(date(2026, 12, 20), rows, 30) == [(2, date(2026, 12, 30)), (1, date(2027, 1, 5))]


def test_local_time_prefers_the_guild_zone_then_the_default() -> None:
    now = datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc)

    assert local_now(now, "Asia/Taipei").hour == 4
    assert local_now(now, None, "Asia/Tokyo").hour == 5
    assert local_now(now, "Not/AZone", "Asia/Tokyo").hour == 5


# ------------------------------------------------------------------ limits and joins


def test_limits_fall_back_to_defaults_for_missing_or_bad_values() -> None:
    limits = CommunityLimits.from_config({"welcome": {"max_ai_per_hour": 3, "burst_threshold": "x"}, "birthday": {"use_ai": False}})

    assert limits.welcome_max_ai_per_hour == 3
    assert limits.welcome_burst_threshold == CommunityLimits().welcome_burst_threshold
    assert limits.birthday_use_ai is False
    assert CommunityLimits.from_config(None) == CommunityLimits()


def test_the_base_config_has_a_community_block() -> None:
    import yaml

    data = yaml.safe_load((ROOT / "base_configs" / "base.yaml").read_text(encoding="utf-8"))
    limits = CommunityLimits.from_config(data["community"])

    assert limits.welcome_max_ai_per_hour == 20 and limits.birthday_max_mentions == 20


def test_close_joins_share_a_batch_and_bursts_count_as_raids() -> None:
    tracker = JoinTracker(burst_threshold=3, burst_seconds=60, max_ai_per_hour=10)

    assert tracker.add(1, "a", 0) is True
    assert tracker.add(1, "b", 1) is False
    assert tracker.take_batch(1) == ["a", "b"]
    assert not tracker.is_raid(1, 2)
    tracker.add(1, "c", 2)
    assert tracker.is_raid(1, 2)
    assert not tracker.is_raid(1, 200)


def test_ai_welcomes_have_an_hourly_budget() -> None:
    tracker = JoinTracker(burst_threshold=3, burst_seconds=60, max_ai_per_hour=2)

    assert [tracker.use_ai(1, t) for t in (0, 1, 2)] == [True, True, False]
    assert tracker.use_ai(2, 2) is True
    assert tracker.use_ai(1, 3601) is True


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


class FakeRole:
    def __init__(self, role_id: int) -> None:
        self.id = role_id


class FakeMember:
    def __init__(self, member_id: int, guild: "FakeGuild", joined_at: Optional[datetime] = None, bot: bool = False) -> None:
        self.id = member_id
        self.guild = guild
        self.bot = bot
        self.display_name = f"user{member_id}"
        self.mention = f"<@{member_id}>"
        self.joined_at = joined_at
        self.roles: List[FakeRole] = []

    async def add_roles(self, role: FakeRole, reason: str = "") -> None:
        self.roles.append(role)

    async def remove_roles(self, role: FakeRole, reason: str = "") -> None:
        self.roles.remove(role)


class FakeGuild:
    def __init__(self) -> None:
        self.id = GUILD_ID
        self.name = "Pig Land"
        self.channel = FakeChannel()
        self.system_channel = None
        self.emojis: list = []
        self.members: List[FakeMember] = []
        self.roles = {77: FakeRole(77)}

    @property
    def member_count(self) -> int:
        return len(self.members)

    def get_channel(self, channel_id: int) -> Optional[FakeChannel]:
        return self.channel if channel_id == self.channel.id else None

    def get_member(self, member_id: int) -> Optional[FakeMember]:
        return next((m for m in self.members if m.id == member_id), None)

    def get_role(self, role_id: int) -> Optional[FakeRole]:
        return self.roles.get(role_id)

    def add(self, member_id: int, **kwargs: Any) -> FakeMember:
        member = FakeMember(member_id, self, **kwargs)
        self.members.append(member)
        return member


@pytest.fixture
def guild() -> FakeGuild:
    return FakeGuild()


@pytest.fixture
def cog(store: CommunityStore, guild: FakeGuild, monkeypatch: pytest.MonkeyPatch) -> CommunityCog:
    bot = SimpleNamespace(
        user=SimpleNamespace(id=1),
        orchestrator=None,
        get_guild=lambda guild_id: guild if guild_id == GUILD_ID else None,
    )
    instance = CommunityCog(bot, store=store)
    instance.lang_manager = FakeLang()
    instance.limits = CommunityLimits(default_timezone="Asia/Taipei", welcome_batch_seconds=0)
    instance.joins = JoinTracker(3, 60, 10)
    store.update_settings(GUILD_ID, announce_channel_id=guild.channel.id)
    return instance


def _at(cog: CommunityCog, local: datetime) -> None:
    cog._now = lambda: local.timestamp()


@pytest.mark.asyncio
async def test_a_welcome_falls_back_to_the_fixed_text_and_pings_only_the_new_member(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, welcome_enabled=True, welcome_note="See #rules")
    member = guild.add(10)

    await cog.welcome(guild, [member])

    text, allowed = guild.channel.sent[0]
    assert text == "welcome_single|count=1|guild=Pig Land|mention=<@10>\nSee #rules"
    assert allowed.everyone is False and allowed.roles is False
    assert [user.id for user in allowed.users] == [10]


@pytest.mark.asyncio
async def test_a_model_written_welcome_is_used_when_available(
    cog: CommunityCog, guild: FakeGuild, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list = []

    async def fake_compose(orchestrator: Any, bot: Any, channel: Any, task: str, facts: str, mentions: Any) -> str:
        calls.append((facts, list(mentions)))
        return "Hi <@10>!"

    monkeypatch.setattr(community_module, "compose_announcement", fake_compose)
    cog.bot.orchestrator = object()

    await cog.welcome(guild, [guild.add(10)])

    assert guild.channel.sent[0][0] == "Hi <@10>!"
    assert "<<<user10>>>" in calls[0][0] and calls[0][1] == ["<@10>"]


@pytest.mark.asyncio
async def test_a_raid_gets_one_fixed_text_message_without_the_model(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def must_not_run(*args: Any, **kwargs: Any) -> str:
        raise AssertionError("the model must not be called during a raid")

    monkeypatch.setattr(community_module, "compose_announcement", must_not_run)
    cog.bot.orchestrator = object()
    store.update_settings(GUILD_ID, welcome_enabled=True)
    _at(cog, datetime(2026, 10, 25, 12, 0, tzinfo=TAIPEI))
    members = [guild.add(i) for i in (10, 11, 12)]
    for member in members:
        cog.joins.add(GUILD_ID, member, cog._now())

    await cog.welcome(guild, cog.joins.take_batch(GUILD_ID))

    assert [text for text, _ in guild.channel.sent] == ["welcome_many|guild=Pig Land|mentions=<@10> <@11> <@12>"]


@pytest.mark.asyncio
async def test_joins_are_ignored_while_welcomes_are_off_and_bots_are_never_welcomed(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore
) -> None:
    await cog.on_member_join(guild.add(10))
    store.update_settings(GUILD_ID, welcome_enabled=True)
    await cog.on_member_join(guild.add(11, bot=True))

    assert cog.joins.take_batch(GUILD_ID) == []


@pytest.mark.asyncio
async def test_a_farewell_is_posted_only_when_turned_on(cog: CommunityCog, guild: FakeGuild, store: CommunityStore) -> None:
    store.update_settings(GUILD_ID, welcome_enabled=True)
    await cog.on_member_remove(guild.add(10))
    store.update_settings(GUILD_ID, farewell_enabled=True)
    await cog.on_member_remove(guild.add(11))

    assert [text for text, _ in guild.channel.sent] == ["farewell|name=user11"]


@pytest.mark.asyncio
async def test_birthdays_are_celebrated_once_after_the_set_hour(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, birthday_enabled=True, birthday_hour=9, birthday_role_id=77)
    guild.add(10)
    guild.add(11)
    store.set_birthday(GUILD_ID, 10, 10, 25)
    store.set_birthday(GUILD_ID, 11, 10, 26)
    store.set_birthday(GUILD_ID, 12, 10, 25)  # no longer in the guild

    _at(cog, datetime(2026, 10, 25, 8, 59, tzinfo=TAIPEI))
    await cog.run_daily_jobs()
    assert guild.channel.sent == []

    _at(cog, datetime(2026, 10, 25, 9, 0, tzinfo=TAIPEI))
    await cog.run_daily_jobs()
    await cog.run_daily_jobs()

    assert [text for text, _ in guild.channel.sent] == ["birthday|mentions=<@10>"]
    assert [role.id for role in guild.get_member(10).roles] == [77]

    _at(cog, datetime(2026, 10, 26, 0, 1, tzinfo=TAIPEI))
    await cog.run_daily_jobs()  # before 9:00: nothing posted, but yesterday's role is taken back
    assert guild.get_member(10).roles == []


@pytest.mark.asyncio
async def test_join_anniversaries_are_combined_into_one_message(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, anniversary_enabled=True, birthday_hour=9)
    guild.add(10, joined_at=datetime(2025, 10, 25, 3, 0, tzinfo=timezone.utc))
    guild.add(11, joined_at=datetime(2023, 10, 25, 3, 0, tzinfo=timezone.utc))
    guild.add(12, joined_at=datetime(2026, 10, 25, 3, 0, tzinfo=timezone.utc))  # joined today
    guild.add(13, joined_at=datetime(2024, 10, 25, 3, 0, tzinfo=timezone.utc), bot=True)

    _at(cog, datetime(2026, 10, 25, 10, 0, tzinfo=TAIPEI))
    await cog.run_daily_jobs()

    text, allowed = guild.channel.sent[0]
    assert text == (
        "anniversary|lines=anniversary_line|mention=<@10>|years=1\nanniversary_line|mention=<@11>|years=3"
    )
    assert [user.id for user in allowed.users] == [10, 11]


@pytest.mark.parametrize("folder", ["en_US", "zh_TW", "zh_CN", "ja_JP"])
def test_every_language_has_the_same_community_texts(folder: str) -> None:
    def keys(lang: str) -> set:
        return set(json.loads((ROOT / "translations" / lang / "commands" / "community.json").read_text("utf-8"))["responses"])

    assert keys(folder) == keys("en_US")


# ------------------------------------------------------------------ announcement writer


class _HistoryChannel:
    def __init__(self) -> None:
        self.guild = SimpleNamespace(id=GUILD_ID)

    def history(self, limit: int) -> Any:
        async def generator() -> Any:
            yield SimpleNamespace(content="hello all", author=SimpleNamespace(id=5, display_name="Al"))

        return generator()


class _Model:
    def __init__(self, reply: Any = None, error: Optional[Exception] = None) -> None:
        self.reply, self.error, self.seen = reply, error, []

    async def ainvoke(self, messages: List[Any]) -> Any:
        self.seen = messages
        if self.error:
            raise self.error
        return SimpleNamespace(content=self.reply)


class _Breaker:
    def __init__(self) -> None:
        self.failures: List[str] = []

    def is_available(self, name: str) -> bool:
        return True

    def record_failure(self, name: str, error: Exception) -> None:
        self.failures.append(name)


@pytest.mark.asyncio
async def test_the_announcement_writer_tries_the_next_model_and_adds_missing_mentions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from llm import announcement_writer

    breaker = _Breaker()
    models = {"bad": _Model(error=RuntimeError("down")), "good": _Model(reply="Welcome aboard!")}
    monkeypatch.setattr(announcement_writer, "get_model_circuit_breaker", lambda: breaker)
    monkeypatch.setattr(announcement_writer, "create_model_instance", lambda name, **kwargs: models[name])
    orchestrator = SimpleNamespace(
        model_manager=SimpleNamespace(get_model_priority_list=lambda agent: ["bad", "good"]),
        build_persona_prompt=lambda bot_id, message: "PERSONA",
    )

    text = await announcement_writer.compose_announcement(
        orchestrator, SimpleNamespace(user=SimpleNamespace(id=1)), _HistoryChannel(), "TASK", "FACTS", ["<@10>"]
    )

    assert text == "<@10> Welcome aboard!"
    assert breaker.failures == ["bad"]
    system, human = models["good"].seen
    assert system.content.startswith("PERSONA\n\nTASK")
    assert human.content.startswith("FACTS") and "Al: hello all" in human.content


@pytest.mark.asyncio
async def test_the_announcement_writer_gives_none_when_every_model_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from llm import announcement_writer

    monkeypatch.setattr(announcement_writer, "get_model_circuit_breaker", lambda: _Breaker())
    monkeypatch.setattr(announcement_writer, "create_model_instance", lambda name, **kwargs: _Model(reply="  "))
    orchestrator = SimpleNamespace(
        model_manager=SimpleNamespace(get_model_priority_list=lambda agent: ["m"]),
        build_persona_prompt=lambda bot_id, message: "PERSONA",
    )

    text = await announcement_writer.compose_announcement(
        orchestrator, SimpleNamespace(user=SimpleNamespace(id=1)), _HistoryChannel(), "TASK", "FACTS"
    )

    assert text is None


# ------------------------------------------------------------------ review fixes


def _http_error() -> Exception:
    import discord

    return discord.HTTPException(SimpleNamespace(status=503, reason="Service Unavailable"), "try again")


@pytest.mark.asyncio
async def test_a_birthday_post_that_fails_is_retried_at_the_next_check(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, birthday_enabled=True, birthday_hour=9)
    guild.add(10)
    store.set_birthday(GUILD_ID, 10, 10, 25)
    _at(cog, datetime(2026, 10, 25, 9, 0, tzinfo=TAIPEI))
    original = guild.channel.send
    failures = [_http_error()]

    async def flaky(text: str, allowed_mentions: Any = None) -> None:
        if failures:
            raise failures.pop()
        await original(text, allowed_mentions)

    guild.channel.send = flaky
    await cog.run_daily_jobs()
    assert guild.channel.sent == []
    await cog.run_daily_jobs()
    await cog.run_daily_jobs()
    assert [text for text, _ in guild.channel.sent] == ["birthday|mentions=<@10>"]


@pytest.mark.asyncio
async def test_a_job_that_keeps_failing_is_given_up(cog: CommunityCog, store: CommunityStore) -> None:
    calls: list = []

    async def fail() -> bool:
        calls.append(1)
        return False

    for _ in range(CommunityCog.MAX_JOB_ATTEMPTS + 2):
        await cog._run_job(GUILD_ID, "birthday", "2026-10-25", fail)

    assert len(calls) == CommunityCog.MAX_JOB_ATTEMPTS
    assert store.has_run(GUILD_ID, "birthday", "2026-10-25")


@pytest.mark.asyncio
async def test_a_member_who_already_had_the_birthday_role_keeps_it(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, birthday_enabled=True, birthday_hour=9, birthday_role_id=77)
    member = guild.add(10)
    member.roles.append(guild.get_role(77))
    store.set_birthday(GUILD_ID, 10, 10, 25)

    _at(cog, datetime(2026, 10, 25, 9, 0, tzinfo=TAIPEI))
    await cog.run_daily_jobs()
    _at(cog, datetime(2026, 10, 26, 0, 1, tzinfo=TAIPEI))
    await cog.run_daily_jobs()

    assert [role.id for role in member.roles] == [77]


@pytest.mark.asyncio
async def test_a_birthday_role_that_could_not_be_removed_is_retried(
    cog: CommunityCog, guild: FakeGuild, store: CommunityStore
) -> None:
    store.update_settings(GUILD_ID, birthday_enabled=True, birthday_hour=9, birthday_role_id=77)
    member = guild.add(10)
    store.set_birthday(GUILD_ID, 10, 10, 25)
    _at(cog, datetime(2026, 10, 25, 9, 0, tzinfo=TAIPEI))
    await cog.run_daily_jobs()
    original = member.remove_roles

    async def refuse(role: FakeRole, reason: str = "") -> None:
        raise _http_error()

    member.remove_roles = refuse
    _at(cog, datetime(2026, 10, 26, 0, 1, tzinfo=TAIPEI))
    await cog.run_daily_jobs()
    assert [role.id for role in member.roles] == [77]

    member.remove_roles = original
    _at(cog, datetime(2026, 10, 26, 0, 6, tzinfo=TAIPEI))
    await cog.run_daily_jobs()
    assert member.roles == []
    assert store.due_birthday_roles(cog._now()) == []


def _role(position: int, permissions: int = 0, assignable: bool = True) -> Any:
    import discord

    class Role:
        def __init__(self) -> None:
            self.position = position
            self.permissions = discord.Permissions(permissions)

        def is_assignable(self) -> bool:
            return assignable

        def __ge__(self, other: Any) -> bool:
            return self.position >= other.position

    return Role()


def test_the_birthday_role_must_be_one_the_admin_could_give_themselves() -> None:
    import discord

    def interaction(manage_roles: bool, top: int, owner: bool = False) -> Any:
        user = SimpleNamespace(
            id=5, guild_permissions=discord.Permissions(manage_roles=manage_roles), top_role=_role(top)
        )
        return SimpleNamespace(guild=SimpleNamespace(owner_id=5 if owner else 1), user=user)

    plain = _role(3)
    check = CommunityCog._birthday_role_problem
    assert check(interaction(True, 5), plain) is None
    assert check(interaction(False, 5), plain) == "birthday_role_not_yours"
    assert check(interaction(True, 3), plain) == "birthday_role_not_yours"
    assert check(interaction(False, 0, owner=True), plain) is None
    assert check(interaction(True, 5), _role(3, discord.Permissions(ban_members=True).value)) == "birthday_role_elevated"
    assert check(interaction(True, 5), _role(3, assignable=False)) == "birthday_role_unassignable"


def test_long_messages_are_split_under_the_discord_limit() -> None:
    from cogs.community import split_message

    mentions = " ".join(f"<@{100000000000000000 + i}>" for i in range(100))
    chunks = split_message(f"Welcome!\n{mentions}")
    assert len(chunks) > 1 and all(len(chunk) <= 2000 for chunk in chunks)
    assert " ".join(chunks).replace("\n", " ").split() == f"Welcome! {mentions}".split()
    assert split_message("x" * 4500) == ["x" * 2000, "x" * 2000, "x" * 500]
    assert split_message("hi") == ["hi"]


@pytest.mark.asyncio
async def test_an_older_welcome_task_does_not_drop_the_newer_one(cog: CommunityCog, guild: FakeGuild) -> None:
    import asyncio

    newer = asyncio.get_running_loop().create_future()

    async def older() -> None:
        cog._flushes[GUILD_ID] = newer  # a new batch was scheduled while this one ran
        await cog._flush_after_delay(guild)

    task = asyncio.ensure_future(older())
    cog._flushes[GUILD_ID] = task
    await task
    assert cog._flushes[GUILD_ID] is newer
    newer.cancel()
