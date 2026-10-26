"""AI tools for rankings, achievements, the weekly recap, birthdays and events.

The model's answer is posted for everyone in the channel, so each tool may only return what
a public post would show: hidden members (``/leaderboard optout``) are never named, and text
from a channel only appears when everyone can read that channel.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import pytest

import addons.visibility as visibility
import cogs.community_lib.recap as recap_module
from cogs.community_lib.limits import CommunityLimits
from cogs.community_lib.recap import Recap
from cogs.community_lib.store import CommunityStore
from cogs.events_lib.store import GOING, EventStore
from cogs.leaderboard import LeaderboardCog
from llm import tools_factory
from llm.tools import community_tools
from llm.tools.community_tools import CommunityTools, EventTools
from llm.tools.user_stats import _profile_extras

GUILD_ID = 42
AUTHOR_ID = 10
TAIPEI = ZoneInfo("Asia/Taipei")
NOW = datetime(2026, 10, 25, 12, 0, tzinfo=TAIPEI)  # a Sunday


class FakeLang:
    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        return f"{keys[-1]}|" + "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))


class FakeMember:
    def __init__(self, member_id: int, bot: bool = False) -> None:
        self.id = member_id
        self.bot = bot
        self.display_name = f"user{member_id}"
        self.mention = f"<@{member_id}>"


class FakeChannel:
    def __init__(self, channel_id: int, public: bool = True) -> None:
        self.id = channel_id
        self.name = f"channel{channel_id}"
        self.public = public


class FakeGuild:
    def __init__(self) -> None:
        self.id = GUILD_ID
        self.members: Dict[int, FakeMember] = {}
        self.channels: Dict[int, FakeChannel] = {}

    def add(self, member_id: int, bot: bool = False) -> FakeMember:
        self.members[member_id] = FakeMember(member_id, bot)
        return self.members[member_id]

    def get_member(self, member_id: int) -> Optional[FakeMember]:
        return self.members.get(member_id)

    def channel(self, channel_id: int, public: bool = True) -> FakeChannel:
        self.channels[channel_id] = FakeChannel(channel_id, public)
        return self.channels[channel_id]

    def get_channel_or_thread(self, channel_id: int) -> Optional[FakeChannel]:
        return self.channels.get(channel_id)

    get_channel = get_channel_or_thread


class FakeStorage:
    def __init__(self) -> None:
        self.rows = {"total": [], "streak": []}

    async def get_guild_rankings(self, guild_id: str, kind: str) -> list:
        return self.rows[kind]


class FakeCollector:
    def __init__(self, rows: list) -> None:
        self.rows = rows

    async def message_counts_by_user(self, guild_id: str, since: float, until: float) -> list:
        return self.rows


@pytest.fixture(autouse=True)
def public_channels(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fake channel is public when its ``public`` flag says so."""
    monkeypatch.setattr(visibility, "audience_can_read", lambda channel: bool(getattr(channel, "public", False)))
    monkeypatch.setattr(recap_module, "is_public", lambda guild, channel: bool(getattr(channel, "public", False)))
    community_tools._recap_cache.clear()


@pytest.fixture
def world(tmp_path: Path) -> SimpleNamespace:
    guild = FakeGuild()
    for member_id in (AUTHOR_ID, 11, 12, 13):
        guild.add(member_id)
    guild.add(99, bot=True)
    here = guild.channel(500)
    store = CommunityStore(tmp_path / "community.db")
    storage = FakeStorage()
    cogs: Dict[str, Any] = {"StatsCog": SimpleNamespace(stats_storage=storage)}
    bot = SimpleNamespace(stats_collector=FakeCollector([("11", 9), ("10", 5), ("12", 3)]), get_cog=cogs.get)
    leaderboard = LeaderboardCog(bot, store=store)
    leaderboard.lang_manager = FakeLang()
    leaderboard.limits = CommunityLimits(default_timezone="Asia/Taipei")
    leaderboard._now = lambda: NOW.timestamp()
    community = SimpleNamespace(
        bot=bot,
        store=store,
        limits=CommunityLimits(default_timezone="Asia/Taipei"),
        _local_now=lambda settings: NOW,
        title_name=lambda guild_id, title_id: f"title_{title_id}",
    )
    cogs["LeaderboardCog"] = leaderboard
    cogs["CommunityCog"] = community
    message = SimpleNamespace(guild=guild, author=guild.get_member(AUTHOR_ID), channel=here)
    runtime = SimpleNamespace(bot=bot, message=message, logger=None)
    return SimpleNamespace(guild=guild, store=store, storage=storage, cogs=cogs, runtime=runtime, here=here, bot=bot)


def _tools(world: SimpleNamespace, cls: Any = CommunityTools) -> Dict[str, Any]:
    return {tool.name: tool for tool in cls(world.runtime).get_tools()}


async def _call(world: SimpleNamespace, name: str, cls: Any = CommunityTools, **kwargs: Any) -> str:
    return await _tools(world, cls)[name].coroutine(**kwargs)


# ------------------------------------------------------------------ loading
def test_tools_are_only_offered_when_their_cogs_are_loaded(world: SimpleNamespace) -> None:
    assert set(_tools(world)) == {"get_leaderboard", "get_achievements", "set_my_stats_visibility", "get_server_recap"}

    del world.cogs["CommunityCog"]
    assert set(_tools(world)) == {"get_leaderboard", "get_achievements", "set_my_stats_visibility"}
    del world.cogs["LeaderboardCog"]
    assert _tools(world) == {}
    assert _tools(world, EventTools) == {}


def test_the_birthday_tool_comes_only_when_birthdays_are_on(world: SimpleNamespace) -> None:
    world.store.update_settings(GUILD_ID, birthday_enabled=True)

    assert "get_upcoming_birthdays" in _tools(world)


def test_hiding_oneself_is_a_core_tool_and_the_rest_are_community_tools(world: SimpleNamespace) -> None:
    world.store.update_settings(GUILD_ID, birthday_enabled=True)
    groups = {name: tools_factory.tool_group(tool) for name, tool in _tools(world).items()}

    assert groups.pop("set_my_stats_visibility") == tools_factory.CORE_TOOL_GROUP
    assert set(groups.values()) == {"community"}


# ------------------------------------------------------------------ leaderboard
@pytest.mark.asyncio
async def test_the_leaderboard_never_names_hidden_members_or_bots(world: SimpleNamespace) -> None:
    world.storage.rows["total"] = [("99", 50), ("11", 9), ("10", 5), ("12", 3)]
    world.store.set_optout(GUILD_ID, 11, True)

    text = await _call(world, "get_leaderboard", kind="messages", period="all")

    assert "user11" not in text and "user99" not in text
    assert text.splitlines()[1].startswith("🥇 **user10**")


@pytest.mark.asyncio
async def test_unknown_leaderboard_choices_fall_back_to_this_weeks_messages(world: SimpleNamespace) -> None:
    text = await _call(world, "get_leaderboard", kind="karma", period="forever")

    assert text.startswith("title_week|") and "user11" in text


# ------------------------------------------------------------------ achievements
@pytest.mark.asyncio
async def test_achievements_of_a_hidden_member_are_refused(world: SimpleNamespace) -> None:
    world.store.set_optout(GUILD_ID, 11, True)
    world.store.unlock(GUILD_ID, 11, ["msg_100"], NOW.timestamp())

    reply = await _call(world, "get_achievements", user_id="<@11>")

    assert "hide" in reply and "✅" not in reply


@pytest.mark.asyncio
async def test_a_hidden_member_asking_about_themselves_is_sent_to_the_private_command(world: SimpleNamespace) -> None:
    world.store.set_optout(GUILD_ID, AUTHOR_ID, True)

    reply = await _call(world, "get_achievements")

    assert "/achievements" in reply and "✅" not in reply


@pytest.mark.asyncio
async def test_achievements_list_locked_and_unlocked_ones(world: SimpleNamespace) -> None:
    world.store.unlock(GUILD_ID, 12, ["msg_100"], NOW.timestamp())

    lines = (await _call(world, "get_achievements", user_id="12")).splitlines()

    assert any(line.startswith("✅") for line in lines) and any(line.startswith("🔒") for line in lines)


@pytest.mark.asyncio
async def test_a_bad_member_id_is_explained(world: SimpleNamespace) -> None:
    assert "not a Discord user ID" in await _call(world, "get_achievements", user_id="bob")
    assert "not on this server" in await _call(world, "get_achievements", user_id="12345")


# ------------------------------------------------------------------ hiding oneself
@pytest.mark.asyncio
async def test_hiding_only_ever_changes_the_person_asking(world: SimpleNamespace) -> None:
    tool = _tools(world)["set_my_stats_visibility"]
    assert set(tool.args) == {"hide"}

    await tool.coroutine(hide=True)
    assert world.store.optouts(GUILD_ID) == {AUTHOR_ID}
    await tool.coroutine(hide=False)
    assert world.store.optouts(GUILD_ID) == set()


# ------------------------------------------------------------------ recap
def _recap(world: SimpleNamespace) -> Recap:
    guild = world.guild
    public, private = guild.channel(600), guild.channel(666, public=False)
    start = NOW - timedelta(days=6)
    return Recap(
        week="2026-10-19",
        start=start,
        end=NOW,
        total=17,
        previous_total=10,
        channels=[(public, 12), (private, 5)],
        talkers=[(guild.get_member(11), 9), (guild.get_member(12), 3)],
        quote={"member": guild.get_member(12), "content": "hello", "url": "https://discord.com/channels/42/600/7", "count": 4},
        titles={"talker": (guild.get_member(11), 9), "dj": (guild.get_member(12), 2)},
        missing=[(guild.get_member(13), 40)],
    )


@pytest.mark.asyncio
async def test_the_recap_is_built_once_and_rechecked_on_every_answer(world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    built: List[Any] = []
    recap = _recap(world)

    async def build(self: Any, guild: Any, start: datetime, end: datetime, hidden: set) -> Recap:
        built.append((start, end, hidden))
        return recap

    monkeypatch.setattr(recap_module.RecapBuilder, "build", build)

    first = await _call(world, "get_server_recap")
    assert "user11" in first and "<<<hello>>>" in first and "channel666" not in first
    assert built[0][0] == datetime(2026, 10, 19, tzinfo=TAIPEI)

    # Later answers reuse the recap, but leave out whoever hid themselves since and any
    # channel that stopped being public.
    world.store.set_optout(GUILD_ID, 11, True)
    world.guild.channels[600].public = False
    second = await _call(world, "get_server_recap")

    assert len(built) == 1
    assert "user11" not in second and "channel600" not in second and "<<<hello>>>" not in second
    assert "user12" in second and "user13" in second


@pytest.mark.asyncio
async def test_the_recap_is_rebuilt_when_the_public_channels_change(world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    built: List[Any] = []

    async def build(self: Any, guild: Any, start: datetime, end: datetime, hidden: set) -> Recap:
        built.append(start)
        return _recap(world)

    public = ["600"]
    monkeypatch.setattr(recap_module, "RecapBuilder", type("Builder", (recap_module.RecapBuilder,), {"build": build}))
    monkeypatch.setattr(recap_module, "public_channel_ids", lambda guild: list(public))

    await _call(world, "get_server_recap")
    await _call(world, "get_server_recap")
    assert len(built) == 1
    # The week's words were counted from the channels public at build time.
    public.remove("600")
    await _call(world, "get_server_recap")
    assert len(built) == 2


@pytest.mark.asyncio
async def test_last_weeks_recap_covers_monday_to_monday(world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    built: List[Any] = []

    async def build(self: Any, guild: Any, start: datetime, end: datetime, hidden: set) -> Optional[Recap]:
        built.append((start, end))
        return None

    monkeypatch.setattr(recap_module.RecapBuilder, "build", build)

    assert "not available" in await _call(world, "get_server_recap", period="last_week")
    assert built == [(datetime(2026, 10, 12, tzinfo=TAIPEI), datetime(2026, 10, 19, tzinfo=TAIPEI))]


# ------------------------------------------------------------------ birthdays
@pytest.mark.asyncio
async def test_upcoming_birthdays_leave_out_hidden_members_bots_and_leavers(world: SimpleNamespace) -> None:
    store = world.store
    store.update_settings(GUILD_ID, birthday_enabled=True)
    store.set_birthday(GUILD_ID, 12, 10, 27)
    store.set_birthday(GUILD_ID, 11, 10, 26)  # hidden
    store.set_birthday(GUILD_ID, 99, 10, 26)  # a bot
    store.set_birthday(GUILD_ID, 77, 10, 26)  # left the server
    store.set_birthday(GUILD_ID, 13, 12, 1)  # too far
    store.set_optout(GUILD_ID, 11, True)

    text = await _call(world, "get_upcoming_birthdays", days=7)

    assert text.splitlines()[1:] == ["10/27: <<<user12>>>"]
    assert "No saved birthdays" in await _call(world, "get_upcoming_birthdays", days=1)


# ------------------------------------------------------------------ events
@pytest.mark.asyncio
async def test_only_events_everyone_here_could_read_are_listed(world: SimpleNamespace, tmp_path: Path) -> None:
    guild = world.guild
    guild.channel(600)
    guild.channel(666, public=False)
    world.here.public = False
    store = EventStore(tmp_path / "events.db")
    soon = datetime.now(timezone.utc).timestamp() + 3600
    for channel_id, title in ((600, "public raid"), (666, "secret meeting"), (500, "this room"), (777, "gone channel")):
        event_id = store.add(GUILD_ID, channel_id, AUTHOR_ID, title, soon, 4, 15, 0)
        store.set_message(event_id, 1000 + channel_id)
        store.sign_up(event_id, AUTHOR_ID, GOING, 0)
    world.cogs["EventsCog"] = SimpleNamespace(store=store)

    text = await _call(world, "list_upcoming_events", EventTools)

    assert "public raid" in text and "this room" in text
    assert "secret meeting" not in text and "gone channel" not in text
    assert f"<t:{int(soon)}:F>" in text and "going: 1/4" in text


@pytest.mark.asyncio
async def test_no_events_is_said_plainly(world: SimpleNamespace, tmp_path: Path) -> None:
    world.cogs["EventsCog"] = SimpleNamespace(store=EventStore(tmp_path / "events.db"))
    tool = _tools(world, EventTools)["list_upcoming_events"]

    assert tools_factory.tool_group(tool) == "events"
    assert "no upcoming events" in await tool.coroutine()


# ------------------------------------------------------------------ profile extras
@pytest.mark.asyncio
async def test_the_stats_tool_adds_rank_titles_and_badges(world: SimpleNamespace) -> None:
    world.storage.rows["total"] = [("11", 9), ("10", 5)]
    world.store.unlock(GUILD_ID, AUTHOR_ID, ["msg_100"], NOW.timestamp())
    world.store.set_titles(GUILD_ID, "2026-10-19", {"talker": AUTHOR_ID})

    lines = await _profile_extras(world.runtime, world.guild, str(AUTHOR_ID))

    assert lines[0] == "profile_rank|rank=2|total=2"
    assert lines[1].startswith("profile_titles|") and lines[2].startswith("profile_badges|")
    # Without the leaderboard cog, or for someone who left, there is nothing to add.
    assert await _profile_extras(world.runtime, world.guild, "77") == []
    del world.cogs["LeaderboardCog"]
    assert await _profile_extras(world.runtime, world.guild, str(AUTHOR_ID)) == []
