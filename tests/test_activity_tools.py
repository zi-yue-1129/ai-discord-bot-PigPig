"""AI tools for starting a server game, who is playing what, and the most played songs."""

from __future__ import annotations

import asyncio
import sqlite3
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import discord
import pytest

from cogs.community_lib.limits import CommunityLimits
from cogs.community_lib.store import CommunityStore
from cogs.games import GAME_OFFER_SECONDS, MAX_GAME_OFFERS, GameOfferView, GamesCog
from cogs.music_lib.taste_store import TasteStore
from cogs.playing import PlayingCog
from llm import tools_factory
from llm.tools.activity_tools import MAX_NAMES, GameTools, PlayingTools, PopularSongTools, heard_by_everyone
from llm.tools.community_tools import UNAVAILABLE

GUILD_ID = 42
HOST_ID = 10


class FakeLang:
    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        return f"{keys[-1]}|" + "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))


class FakeMessage:
    def __init__(self, message_id: int) -> None:
        self.id = message_id
        self.edits: List[dict] = []

    async def edit(self, **kwargs: Any) -> None:
        self.edits.append(kwargs)


class FakeChannel:
    def __init__(self, channel_id: int = 500, viewers: Optional[set] = None) -> None:
        self.id = channel_id
        self.viewers = viewers  # None: everyone sees it
        self.sent: List[tuple] = []
        self.messages: List[FakeMessage] = []
        self.muted: set = set()  # members who may see the channel but not post or use commands
        self.broken = False  # sending fails

    def permissions_for(self, member: Any) -> Any:
        view = self.viewers is None or member.id in self.viewers
        post = view and member.id not in self.muted
        return SimpleNamespace(
            view_channel=view, read_message_history=view, manage_threads=False, send_messages=post,
            use_application_commands=post,
        )

    async def send(self, content: Any = None, **kwargs: Any) -> Any:
        if self.broken:
            raise discord.HTTPException(SimpleNamespace(status=500, reason="down"), "down")
        self.sent.append((content, kwargs))
        message = FakeMessage(len(self.sent))
        self.messages.append(message)
        return message


class FakeResponse:
    def __init__(self) -> None:
        self.sent: List[tuple] = []
        self.edited: List[dict] = []
        self.on_defer: Any = None  # runs while the press is being acknowledged

    async def send_message(self, content: Any = None, **kwargs: Any) -> None:
        self.sent.append((content, kwargs))

    async def edit_message(self, **kwargs: Any) -> None:
        self.edited.append(kwargs)

    async def defer(self) -> None:
        self.deferred = True
        if self.on_defer is not None:
            await self.on_defer()


def _member(member_id: int, bot: bool = False, voice: Any = None, name: Optional[str] = None) -> Any:
    return SimpleNamespace(
        id=member_id, bot=bot, display_name=name or f"user{member_id}", mention=f"<@{member_id}>", voice=voice
    )


def _optouts(hidden: Any) -> Any:
    """A leaderboard cog whose opt-out list is ``hidden`` (an exception class: reading it fails)."""

    def read_optouts(guild_id: int) -> set:
        if isinstance(hidden, type):
            raise hidden("locked")
        return set(hidden)

    return SimpleNamespace(store=SimpleNamespace(read_optouts=read_optouts))


def _runtime(cogs: Dict[str, Any], channel: FakeChannel, members: Dict[int, Any], guild: Any = None) -> Any:
    guild = guild or SimpleNamespace(id=GUILD_ID, get_member=members.get, voice_client=None)
    message = SimpleNamespace(guild=guild, author=members[HOST_ID], channel=channel)
    return SimpleNamespace(bot=SimpleNamespace(get_cog=cogs.get), message=message, logger=None)


def _tool(cls: Any, runtime: Any) -> Any:
    tools = cls(runtime).get_tools()
    return tools[0] if tools else None


async def _press(view: GameOfferView, key: str, user: Any, on_defer: Any = None) -> FakeResponse:
    """Presses the offer's button whose label is ``key`` as ``user``."""
    response = FakeResponse()
    response.on_defer = on_defer
    async def edit_original_response(**kwargs: Any) -> None:
        response.edited.append(kwargs)

    interaction = SimpleNamespace(user=user, response=response, edit_original_response=edit_original_response)
    button = next(item for item in view.children if str(item.label).startswith(key + "|"))
    if await view.interaction_check(interaction):
        await button.callback(interaction)
    return response


# ------------------------------------------------------------------ games
@pytest.fixture
def games(tmp_path: Path) -> GamesCog:
    cog = GamesCog(SimpleNamespace(get_cog=lambda name: None), store=CommunityStore(tmp_path / "community.db"))
    cog.lang_manager = FakeLang()
    return cog


def _hold_chain(games: GamesCog, monkeypatch: pytest.MonkeyPatch) -> tuple:
    finish = asyncio.Event()
    played: list = []

    async def run_chain(channel: Any, guild: Any, chain: Any, host_id: Any = None) -> Any:
        played.append(host_id)
        await finish.wait()

    monkeypatch.setattr(games, "run_chain", run_chain)
    return finish, played


@pytest.mark.asyncio
async def test_the_ai_only_offers_a_game_and_the_asker_starts_it(games: GamesCog, monkeypatch: pytest.MonkeyPatch) -> None:
    channel = FakeChannel()
    members = {HOST_ID: _member(HOST_ID), 11: _member(11)}
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, members))
    assert tools_factory.tool_group(tool) == "games"
    finish, played = _hold_chain(games, monkeypatch)

    reply = await tool.coroutine(game="chain")

    assert reply.startswith("Posted a Start button")
    # Nothing is claimed or started before the button is pressed.
    assert games.limits.running == set() and games.limits.hosts == set() and games._tasks == set()
    text, kwargs = channel.sent[0]
    assert text.startswith("offer|") and "game=game_chain|" in text
    assert kwargs["allowed_mentions"].users is False and kwargs["allowed_mentions"].everyone is False
    view = kwargs["view"]

    # Someone else cannot start it.
    other = await _press(view, "offer_start", members[11])
    assert other.sent[0][0] == "offer_not_yours|" and other.sent[0][1]["ephemeral"] is True
    assert games._tasks == set()

    pressed = await _press(view, "offer_start", members[HOST_ID])
    assert pressed.edited[0]["content"].startswith("offer_started|") and pressed.edited[0]["view"] is None
    assert games.limits.running == {channel.id} and games.limits.hosts == {HOST_ID}
    await asyncio.sleep(0)
    assert played == [HOST_ID]
    rules, rules_kwargs = channel.sent[1]
    assert rules.startswith("chain_rules|") and rules_kwargs["allowed_mentions"].users is False
    # A second press does nothing.
    again = await _press(view, "offer_start", members[HOST_ID])
    assert again.sent[0][0] == "offer_expired|" and len(games._tasks) == 1

    finish.set()
    await asyncio.sleep(0.01)
    assert games.limits.running == set() and games.limits.hosts == set() and games._tasks == set()
    assert games._offers == {}


@pytest.mark.asyncio
async def test_a_cancelled_or_expired_offer_starts_nothing(games: GamesCog) -> None:
    channel = FakeChannel()
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: _member(HOST_ID)}))

    await tool.coroutine(game="chain")
    view = channel.sent[0][1]["view"]
    cancelled = await _press(view, "offer_cancel", _member(HOST_ID))
    assert cancelled.edited[0]["content"] == "offer_cancelled|"
    assert (await _press(view, "offer_start", _member(HOST_ID))).sent[0][0] == "offer_expired|"

    await tool.coroutine(game="chain")
    view = channel.sent[1][1]["view"]
    await view.on_timeout()
    assert channel.messages[1].edits[0] == {"content": "offer_expired|", "view": None}
    assert (await _press(view, "offer_start", _member(HOST_ID))).sent[0][0] == "offer_expired|"
    assert games._tasks == set() and games._offers == {} and games.limits.running == set()


@pytest.mark.asyncio
async def test_a_new_offer_replaces_the_old_one_and_a_server_has_few(games: GamesCog) -> None:
    channel = FakeChannel()
    members = {i: _member(i) for i in range(HOST_ID, HOST_ID + MAX_GAME_OFFERS + 1)}
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, members))

    await tool.coroutine(game="chain")
    await tool.coroutine(game="chain")
    # The same host's first offer is taken down: one open offer per host.
    assert channel.messages[0].edits == [{"content": "offer_expired|", "view": None}]
    assert list(games._offers) == [HOST_ID] and games._offers[HOST_ID] is channel.sent[1][1]["view"]

    guild = SimpleNamespace(id=GUILD_ID)
    for host_id in range(HOST_ID + 1, HOST_ID + MAX_GAME_OFFERS):
        assert await games.offer_game("chain", guild, channel, members[host_id]) is None
    assert await games.offer_game("chain", guild, channel, members[HOST_ID + MAX_GAME_OFFERS]) == "offer_limit|"
    # Another server is not affected.
    assert await games.offer_game("chain", SimpleNamespace(id=GUILD_ID + 1), channel, _member(99)) is None
    assert len(games._offers) == MAX_GAME_OFFERS + 1


@pytest.mark.asyncio
async def test_start_checks_again_when_pressed(games: GamesCog) -> None:
    channel = FakeChannel()
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: _member(HOST_ID)}))
    await tool.coroutine(game="chain")
    view = channel.sent[0][1]["view"]

    games.limits.running.add(channel.id)  # someone started a game here meanwhile
    pressed = await _press(view, "offer_start", _member(HOST_ID))

    assert pressed.edited[0]["content"] == "busy|" and games._tasks == set()


@pytest.mark.asyncio
async def test_games_that_cannot_start_say_why(games: GamesCog) -> None:
    channel = FakeChannel()
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: _member(HOST_ID)}))

    assert "must be" in await tool.coroutine(game="poker")
    assert await tool.coroutine(game="quiz") == "The game could not start: unavailable|"
    assert "song_need_voice|" in await tool.coroutine(game="guess song")
    assert "whole numbers" in await tool.coroutine(game="chain", rounds="many")
    assert channel.sent == [] and games.limits.running == set() and games._offers == {}


def test_no_game_tool_without_the_games_cog_or_in_dms(games: GamesCog) -> None:
    assert _tool(GameTools, _runtime({}, FakeChannel(), {HOST_ID: _member(HOST_ID)})) is None
    runtime = _runtime({"GamesCog": games}, FakeChannel(), {HOST_ID: _member(HOST_ID)})
    runtime.message.guild = None
    assert _tool(GameTools, runtime) is None


@pytest.mark.asyncio
async def test_start_checks_the_hosts_permissions_as_they_are_now(games: GamesCog) -> None:
    channel = FakeChannel()
    host = _member(HOST_ID)
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: host}))
    await tool.coroutine(game="chain")
    view = channel.sent[0][1]["view"]

    channel.muted.add(HOST_ID)  # may still see the channel, no longer post or use commands
    pressed = await _press(view, "offer_start", host)

    assert pressed.edited[0]["content"] == "offer_denied|" and pressed.deferred is True
    assert games._tasks == set() and games.limits.running == set()
    # Nor is a new offer posted for them.
    assert await tool.coroutine(game="chain") == "The game could not start: offer_denied|"
    assert len(channel.sent) == 1


@pytest.mark.asyncio
async def test_offer_options_are_kept_in_range(games: GamesCog) -> None:
    channel = FakeChannel()
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: _member(HOST_ID)}))
    games.bot.orchestrator = object()
    games.bot.vector_manager = SimpleNamespace(store=SimpleNamespace(sample_memories=None))

    await tool.coroutine(game="quiz", rounds=50, days=99999, this_channel=True)
    assert channel.sent[-1][1]["view"].options == {"rounds": 10, "days": 3650, "this_channel": True}
    await tool.coroutine(game="quiz", rounds=1, days=0)
    assert channel.sent[-1][1]["view"].options == {"rounds": 3, "days": None, "this_channel": False}
    await tool.coroutine(game="chain", rounds=7, homophones=True)
    assert channel.sent[-1][1]["view"].options == {"homophones": True}


@pytest.mark.asyncio
async def test_an_offer_that_cannot_be_posted_is_dropped_and_unloading_closes_offers(games: GamesCog) -> None:
    channel = FakeChannel()
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: _member(HOST_ID)}))

    channel.broken = True
    assert await tool.coroutine(game="chain") == "The game could not start: failed|"
    assert games._offers == {}

    channel.broken = False
    await tool.coroutine(game="chain")
    view = channel.sent[0][1]["view"]
    await games.cog_unload()
    assert games._offers == {} and view.done and view.is_finished()
    assert (await _press(view, "offer_start", _member(HOST_ID))).sent[0][0] == "offer_expired|"


@pytest.mark.asyncio
async def test_a_game_cancelled_before_it_ran_frees_the_channel_and_host(games: GamesCog, monkeypatch: pytest.MonkeyPatch) -> None:
    channel, host = FakeChannel(), _member(HOST_ID)
    guild = SimpleNamespace(id=GUILD_ID)
    _hold_chain(games, monkeypatch)

    assert await games.start_game("chain", guild, channel, host) is None
    assert games.limits.running == {channel.id} and games.limits.hosts == {HOST_ID}
    await games.cog_unload()  # before the task's first step
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert games.limits.running == set() and games.limits.hosts == set() and games._tasks == set()
    # The unloaded cog starts nothing more; a reloaded one (sharing the limits) can start right away.
    assert await games.start_game("chain", guild, channel, host) == "unavailable|"
    fresh = GamesCog(games.bot, store=games.store)
    fresh.lang_manager = FakeLang()
    assert fresh.limits is games.limits
    _hold_chain(fresh, monkeypatch)
    assert await fresh.start_game("chain", guild, channel, host) is None
    await fresh.cog_unload()
    await asyncio.sleep(0.01)
    assert games.limits.running == set() and games.limits.hosts == set()


@pytest.mark.asyncio
async def test_round_two_game_regressions(games: GamesCog, monkeypatch: pytest.MonkeyPatch) -> None:
    channel = FakeChannel()
    host = _member(HOST_ID)
    members = {HOST_ID: host}
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, members))

    # The offer lasts two minutes, and days below 1 become 1.
    assert GAME_OFFER_SECONDS == 120
    games.bot.orchestrator = object()
    games.bot.vector_manager = SimpleNamespace(store=SimpleNamespace(sample_memories=None))
    await tool.coroutine(game="quiz", days=-5)
    view = channel.sent[-1][1]["view"]
    assert view.options["days"] == 1 and view.timeout == 120
    await view.expire()

    # Start plays with the host as they are now, not the snapshot taken when the AI offered.
    await tool.coroutine(game="chain")
    view = channel.sent[-1][1]["view"]
    now_host = _member(HOST_ID, name="renamed")
    members[HOST_ID] = now_host
    hosts: list = []

    async def play_chain(guild: Any, channel: Any, host: Any, homophones: bool, announce: Any) -> None:
        hosts.append(host)

    monkeypatch.setattr(games, "_play_chain", play_chain)
    await _press(view, "offer_start", host)
    await asyncio.sleep(0.01)
    assert hosts == [now_host]


def test_thread_games_need_the_thread_send_permission() -> None:
    thread = SimpleNamespace(type=discord.ChannelType.public_thread)
    host = _member(HOST_ID)

    def allowed(**flags: bool) -> bool:
        thread.permissions_for = lambda member: SimpleNamespace(view_channel=True, use_application_commands=True, **flags)
        return GamesCog.host_may_play(thread, host)

    assert allowed(send_messages=False, send_messages_in_threads=True)
    assert not allowed(send_messages=True, send_messages_in_threads=False)


@pytest.mark.asyncio
async def test_a_cancelled_offer_post_leaves_no_offer(games: GamesCog) -> None:
    channel = FakeChannel()

    async def cancelled(*args: Any, **kwargs: Any) -> Any:
        raise asyncio.CancelledError()

    channel.send = cancelled
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: _member(HOST_ID)}))
    with pytest.raises(asyncio.CancelledError):
        await tool.coroutine(game="chain")
    assert games._offers == {}


@pytest.mark.asyncio
async def test_a_start_press_waiting_while_the_cog_unloads_starts_nothing(games: GamesCog, monkeypatch: pytest.MonkeyPatch) -> None:
    channel = FakeChannel()
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: _member(HOST_ID)}))
    _hold_chain(games, monkeypatch)
    await tool.coroutine(game="chain")
    view = channel.sent[0][1]["view"]

    pressed = await _press(view, "offer_start", _member(HOST_ID), on_defer=games.cog_unload)

    assert pressed.edited[0]["content"] == "unavailable|"
    assert games._tasks == set() and games.limits.running == set() and games.limits.hosts == set()


@pytest.mark.asyncio
async def test_the_song_pool_is_read_off_the_event_loop(games: GamesCog, monkeypatch: pytest.MonkeyPatch) -> None:
    import threading

    loop_thread = threading.current_thread()
    music = SimpleNamespace(youtube=object(), queue_manager=SimpleNamespace(is_queue_empty=lambda guild_id: True))
    games.bot.get_cog = lambda name: music if name == "YTMusic" else None
    seen: list = []

    def song_pool(music: Any, guild_id: int) -> list:
        seen.append(threading.current_thread() is not loop_thread)
        return [("a", "A"), ("b", "B"), ("c", "C")]

    monkeypatch.setattr(games, "song_pool", song_pool)
    channel = FakeChannel()
    host = _member(HOST_ID, voice=SimpleNamespace(channel=SimpleNamespace(id=1, mention="#voice")))
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: host}))

    assert (await tool.coroutine(game="guess_song")).startswith("Posted a Start button")
    assert seen == [True]


@pytest.mark.asyncio
async def test_round_three_offer_regressions(games: GamesCog, monkeypatch: pytest.MonkeyPatch) -> None:
    import threading

    channel = FakeChannel()
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: _member(HOST_ID)}))

    # Cancelled while the replaced offer is taken down: neither offer is left holding a place.
    await tool.coroutine(game="chain")

    async def cancelled_edit(**kwargs: Any) -> None:
        raise asyncio.CancelledError()

    channel.messages[0].edit = cancelled_edit
    with pytest.raises(asyncio.CancelledError):
        await tool.coroutine(game="chain")
    assert games._offers == {}

    # Permissions taken away while guess the song reads its pool: Start does not start it.
    music = SimpleNamespace(youtube=object(), queue_manager=SimpleNamespace(is_queue_empty=lambda guild_id: True))
    games.bot.get_cog = lambda name: music if name == "YTMusic" else None
    reads: list = []

    def song_pool(music: Any, guild_id: int) -> list:
        reads.append(threading.current_thread())
        if len(reads) == 2:  # the read for Start
            channel.muted.add(HOST_ID)
        return [("a", "A"), ("b", "B"), ("c", "C")]

    monkeypatch.setattr(games, "song_pool", song_pool)
    host = _member(HOST_ID, voice=SimpleNamespace(channel=SimpleNamespace(id=1, mention="#voice")))
    tool = _tool(GameTools, _runtime({"GamesCog": games}, channel, {HOST_ID: host}))
    await tool.coroutine(game="guess_song")
    pressed = await _press(channel.sent[-1][1]["view"], "offer_start", host)
    assert pressed.edited[0]["content"] == "offer_denied|"
    assert games._tasks == set() and games.limits.running == set() and games.limits.song_guilds == set()


@pytest.mark.asyncio
async def test_slash_guess_song_waiting_on_its_pool_when_the_cog_unloads_starts_nothing(games: GamesCog, monkeypatch: pytest.MonkeyPatch) -> None:
    music = SimpleNamespace(youtube=object(), queue_manager=SimpleNamespace(is_queue_empty=lambda guild_id: True))
    games.bot.get_cog = lambda name: music if name == "YTMusic" else None

    def song_pool(music: Any, guild_id: int) -> list:
        games._unloaded = True  # cog_unload ran while this was read
        return [("a", "A"), ("b", "B"), ("c", "C")]

    monkeypatch.setattr(games, "song_pool", song_pool)
    played: list = []

    async def play_song_game(*args: Any) -> None:
        played.append(args)

    monkeypatch.setattr(games, "_play_song_game", play_song_game)
    response = FakeResponse()
    host = _member(HOST_ID, voice=SimpleNamespace(channel=SimpleNamespace(id=1, mention="#voice")))
    interaction = SimpleNamespace(
        guild=SimpleNamespace(id=GUILD_ID, voice_client=None), channel=FakeChannel(), user=host, response=response
    )

    await GamesCog.guess_song.callback(games, interaction)

    assert response.sent == [("unavailable|", {"ephemeral": True})] and played == []
    assert games.limits.running == set() and games.limits.song_guilds == set()


# ------------------------------------------------------------------ who is playing
@pytest.fixture
def playing(tmp_path: Path) -> PlayingCog:
    store = CommunityStore(tmp_path / "community.db")
    return PlayingCog(SimpleNamespace(guilds=[]), store=store, limits=CommunityLimits())


@pytest.mark.asyncio
async def test_who_is_playing_names_and_counts_only_visible_members_who_did_not_hide(playing: PlayingCog) -> None:
    members = {i: _member(i) for i in (HOST_ID, 11, 12, 13, 15)}
    members[14] = _member(14, bot=True)
    members[16] = _member(16, name="@everyone <@1> https://x.example")
    channel = FakeChannel(viewers={HOST_ID, 11, 12, 14, 15, 16})
    now = time.time()
    for user_id, game in (
        (11, "VALORANT"), (12, "valorant "), (13, "VALORANT"), (14, "VALORANT"),
        (HOST_ID, "Minecraft"), (16, "Minecraft"), (15, "Secret Game"),
    ):
        playing.tracker.update(GUILD_ID, user_id, (game, None), now)
    playing.store.update_settings(GUILD_ID, playing_enabled=True)
    runtime = _runtime({"PlayingCog": playing, "LeaderboardCog": _optouts({12, 15})}, channel, members)
    tool = _tool(PlayingTools, runtime)
    assert tools_factory.tool_group(tool) == "playing"

    text = await tool.coroutine()

    assert "<<<user11>>>" in text and "<<<user10>>>" in text
    # Hidden (12, 15), unable to see the channel (13) or a bot (14): neither named nor counted.
    assert "user12" not in text and "user13" not in text and "user14" not in text
    assert "VALORANT>>>: 1 playing" in text
    # A game only hidden members play is not mentioned at all.
    assert "Secret" not in text
    # Names are made safe.
    assert "@everyone" not in text and "<@1>" not in text and "x.example" not in text
    # Most players first.
    assert text.splitlines()[1].startswith("<<<Minecraft>>>: 2 playing")


@pytest.mark.asyncio
async def test_who_is_playing_says_nothing_when_the_opt_out_list_cannot_be_read(playing: PlayingCog) -> None:
    members = {HOST_ID: _member(HOST_ID)}
    playing.tracker.update(GUILD_ID, HOST_ID, ("Minecraft", None), time.time())
    playing.store.update_settings(GUILD_ID, playing_enabled=True)  # on, and its settings readable

    unreadable = _tool(PlayingTools, _runtime({"PlayingCog": playing, "LeaderboardCog": _optouts(sqlite3.OperationalError)}, FakeChannel(), members))
    assert await unreadable.coroutine() == UNAVAILABLE

    readable = _tool(PlayingTools, _runtime({"PlayingCog": playing, "LeaderboardCog": _optouts(set())}, FakeChannel(), members))
    assert "<<<user10>>>" in await readable.coroutine()
    playing.store.update_settings(GUILD_ID, playing_enabled=False)
    assert "turned off" in await readable.coroutine()


@pytest.mark.asyncio
async def test_who_is_playing_caps_names_and_games(playing: PlayingCog) -> None:
    members = {i: _member(i) for i in range(HOST_ID, HOST_ID + MAX_NAMES + 3)}
    now = time.time()
    for user_id in members:
        playing.tracker.update(GUILD_ID, user_id, ("G" * 300, None), now)
    for index in range(15):
        playing.tracker.update(GUILD_ID, 1000 + index, (f"Game {index}", None), now)
        members[1000 + index] = _member(1000 + index)
    playing.store.update_settings(GUILD_ID, playing_enabled=True)
    tool = _tool(PlayingTools, _runtime({"PlayingCog": playing, "LeaderboardCog": _optouts(set())}, FakeChannel(), members))

    lines = (await tool.coroutine()).splitlines()[1:]

    assert len(lines) == 10
    assert lines[0].count("<<<user") == MAX_NAMES and lines[0].endswith(" and 3 more)")
    assert "G" * 100 not in lines[0] and "G" * 98 + "…" in lines[0]


def test_tools_are_built_without_reading_a_database(playing: PlayingCog, monkeypatch: pytest.MonkeyPatch) -> None:
    def no_database(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("the tool list must be built without reading a database")

    for name in ("get_settings", "read_optouts", "optouts"):
        monkeypatch.setattr(playing.store, name, no_database)
    taste = SimpleNamespace(plays_with_places=no_database, top_played=no_database)
    leaderboard = SimpleNamespace(store=SimpleNamespace(read_optouts=no_database, optouts=no_database))
    cogs = {"PlayingCog": playing, "YTMusic": SimpleNamespace(_taste_store=taste), "LeaderboardCog": leaderboard}
    runtime = _runtime(cogs, FakeChannel(), {HOST_ID: _member(HOST_ID)})

    assert _tool(PlayingTools, runtime) is not None and _tool(PopularSongTools, runtime) is not None


def test_no_playing_or_song_tools_in_dms(playing: PlayingCog) -> None:
    cogs = {"PlayingCog": playing, "YTMusic": SimpleNamespace(_taste_store=SimpleNamespace(plays_with_places=None))}
    runtime = _runtime(cogs, FakeChannel(), {HOST_ID: _member(HOST_ID)})
    runtime.message.guild = None
    assert _tool(PlayingTools, runtime) is None and _tool(PopularSongTools, runtime) is None


# ------------------------------------------------------------------ popular songs
PUBLIC_VOICE, PUBLIC_TEXT, PRIVATE_VOICE, PRIVATE_TEXT, NSFW_TEXT, HERE = 600, 601, 602, 603, 604, 500


@pytest.fixture
def song_world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    module = sys.modules[PopularSongTools.__module__]
    public = {PUBLIC_VOICE, PUBLIC_TEXT}
    # Decides from the channel itself, like community_tools.shareable (tested with real channels there).
    monkeypatch.setattr(module, "shareable", lambda channel: channel is not None and channel.id in public)
    channels = {i: SimpleNamespace(id=i) for i in (PUBLIC_VOICE, PUBLIC_TEXT, PRIVATE_VOICE, PRIVATE_TEXT, NSFW_TEXT, HERE)}
    guild = SimpleNamespace(id=GUILD_ID, get_member=lambda i: None, voice_client=None, get_channel=channels.get)
    taste = TasteStore(tmp_path / "taste.db")
    return SimpleNamespace(taste=taste, guild=guild)


def _songs_tool(world: SimpleNamespace, hidden: Any) -> Any:
    cogs = {"YTMusic": SimpleNamespace(_taste_store=world.taste), "LeaderboardCog": _optouts(hidden)}
    return _tool(PopularSongTools, _runtime(cogs, FakeChannel(HERE), {HOST_ID: _member(HOST_ID)}, world.guild))


@pytest.mark.asyncio
async def test_popular_songs_count_only_what_everyone_could_hear(song_world: SimpleNamespace) -> None:
    taste, now = song_world.taste, time.time()

    def play(video: str, title: str, requester: Optional[int], text: Optional[int], voice: Optional[int], ago: float = 60, autoplay: bool = False) -> Optional[int]:
        return taste.add_play_event(
            GUILD_ID, video, title, requester_id=requester, autoplay=autoplay, played_at=now - ago,
            text_channel_id=text, voice_channel_id=voice,
        )

    for _ in range(3):
        play("a", "Song <A> @everyone", 11, PUBLIC_TEXT, PUBLIC_VOICE)
    taste.mark_play_skipped(play("b", "Song B", None, HERE, PUBLIC_VOICE, autoplay=True), 5)
    play("b", "Song B", 11, PUBLIC_TEXT, PUBLIC_VOICE)
    for _ in range(5):
        play("h", "Hidden pick", 12, PUBLIC_TEXT, PUBLIC_VOICE)  # requested by a hidden member
        play("p", "Private room song", 11, PUBLIC_TEXT, PRIVATE_VOICE)
        play("t", "Private text song", 11, PRIVATE_TEXT, PUBLIC_VOICE)
        play("n", "NSFW text song", 11, NSFW_TEXT, PUBLIC_VOICE)
        play("o", "Logged before channels", 11, None, None)
    play("m", "Month ago", 11, PUBLIC_TEXT, PUBLIC_VOICE, ago=20 * 86400)
    tool = _songs_tool(song_world, {12})
    assert tools_factory.tool_group(tool) == "music"

    week = await tool.coroutine(period="week", limit=50)

    assert week.splitlines()[1:] == [
        "1. <<<Song ‹A› @​everyone>>> — 3 plays",
        "2. <<<Song B>>> — 2 plays, skipped 1",
    ]
    month = await tool.coroutine(period="month", limit=1)
    assert month.splitlines()[1:] == week.splitlines()[1:2]
    assert "Month ago" in await tool.coroutine(period="month")


@pytest.mark.asyncio
async def test_popular_songs_fail_closed(song_world: SimpleNamespace) -> None:
    song_world.taste.add_play_event(
        GUILD_ID, "a", "Song A", requester_id=11, autoplay=False, text_channel_id=PUBLIC_TEXT, voice_channel_id=PUBLIC_VOICE
    )
    assert await _songs_tool(song_world, sqlite3.OperationalError).coroutine() == UNAVAILABLE
    assert "Song A" in await _songs_tool(song_world, set()).coroutine()
    assert _tool(PopularSongTools, _runtime({}, FakeChannel(), {HOST_ID: _member(HOST_ID)})) is None


def test_an_old_play_log_gets_the_channel_columns(tmp_path: Path) -> None:
    path = tmp_path / "taste.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE play_events (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, "
            "video_id TEXT NOT NULL, title TEXT NOT NULL DEFAULT '', requester_id INTEGER, "
            "autoplay INTEGER NOT NULL DEFAULT 0, played_at REAL NOT NULL, skipped INTEGER NOT NULL DEFAULT 0, "
            "listened_seconds REAL)"
        )
        connection.execute("INSERT INTO play_events (guild_id, video_id, played_at) VALUES (1, 'old', 10)")
    connection.close()
    taste = TasteStore(path)

    taste.add_play_event(1, "new", "New", requester_id=5, autoplay=False, played_at=20, text_channel_id=7, voice_channel_id=8)

    assert taste.plays_with_places(1, 0, 100) == [("new", "New", 5, 0, 7, 8), ("old", "", None, 0, None, None)]


def test_the_music_player_logs_where_a_song_played(tmp_path: Path) -> None:
    from cogs.music import YTMusic

    taste = TasteStore(tmp_path / "taste.db")
    cog = SimpleNamespace(bot=SimpleNamespace(user=SimpleNamespace(id=1)), _taste_store=taste)
    ctx = SimpleNamespace(channel=SimpleNamespace(id=PUBLIC_TEXT))
    voice_client = SimpleNamespace(channel=SimpleNamespace(id=PUBLIC_VOICE))

    YTMusic._record_play_event(cog, GUILD_ID, {"video_id": "v", "title": "T", "added_by": 11}, ctx, voice_client)

    assert taste.plays_with_places(GUILD_ID, 0, time.time() + 1) == [("v", "T", 11, 0, PUBLIC_TEXT, PUBLIC_VOICE)]


@pytest.mark.asyncio
async def test_popular_songs_list_at_most_ten(song_world: SimpleNamespace) -> None:
    for index in range(15):
        song_world.taste.add_play_event(
            GUILD_ID, f"v{index}", f"Song {index}", requester_id=11, autoplay=False,
            text_channel_id=PUBLIC_TEXT, voice_channel_id=PUBLIC_VOICE,
        )
    tool = _songs_tool(song_world, set())
    assert len((await tool.coroutine(limit=50)).splitlines()) == 1 + 10
    assert len((await tool.coroutine(limit=0)).splitlines()) == 1 + 5
    assert len((await tool.coroutine(limit=-3)).splitlines()) == 1 + 1


class FakeOverwrite:
    def __init__(self, connect: bool) -> None:
        self.connect = connect

    def pair(self) -> tuple:
        return SimpleNamespace(), SimpleNamespace(connect=not self.connect)


class FakeVoiceChannel:
    """A voice channel everyone can see and read; ``connect`` is what ``@everyone`` may do."""

    def __init__(self, connect: bool = True, overwrites: Optional[dict] = None, nsfw: bool = False) -> None:
        self.id = 700
        self.type = discord.ChannelType.voice
        self.guild = SimpleNamespace(default_role="everyone")
        self.connect = connect
        self.overwrites = overwrites or {}
        self.nsfw = nsfw

    def permissions_for(self, role: Any) -> Any:
        return SimpleNamespace(view_channel=True, read_message_history=True, connect=self.connect)

    def is_nsfw(self) -> bool:
        return self.nsfw


def test_a_voice_channel_counts_only_when_everyone_can_join_it() -> None:
    assert heard_by_everyone(FakeVoiceChannel())
    assert not heard_by_everyone(FakeVoiceChannel(connect=False))
    assert not heard_by_everyone(FakeVoiceChannel(overwrites={"members": FakeOverwrite(connect=False)}))
    assert heard_by_everyone(FakeVoiceChannel(overwrites={"members": FakeOverwrite(connect=True)}))
    assert not heard_by_everyone(FakeVoiceChannel(nsfw=True))
    assert not heard_by_everyone(None)


@pytest.mark.asyncio
async def test_databases_are_read_off_the_event_loop(song_world: SimpleNamespace, playing: PlayingCog, monkeypatch: pytest.MonkeyPatch) -> None:
    import threading

    loop_thread = threading.current_thread()
    seen: list = []

    def watched(function: Any) -> Any:
        def call(*args: Any, **kwargs: Any) -> Any:
            seen.append(threading.current_thread() is not loop_thread)
            return function(*args, **kwargs)

        return call

    monkeypatch.setattr(song_world.taste, "plays_with_places", watched(song_world.taste.plays_with_places))
    monkeypatch.setattr(playing, "feature_on_read_only", watched(playing.feature_on_read_only))
    leaderboard = _optouts(set())
    leaderboard.store.read_optouts = watched(leaderboard.store.read_optouts)
    cogs = {"YTMusic": SimpleNamespace(_taste_store=song_world.taste), "PlayingCog": playing, "LeaderboardCog": leaderboard}
    runtime = _runtime(cogs, FakeChannel(HERE), {HOST_ID: _member(HOST_ID)}, song_world.guild)

    await _tool(PopularSongTools, runtime).coroutine()
    await _tool(PlayingTools, runtime).coroutine()

    assert seen == [True] * 4


@pytest.mark.asyncio
async def test_someone_who_hides_while_the_tools_read_is_left_out(song_world: SimpleNamespace, playing: PlayingCog, monkeypatch: pytest.MonkeyPatch) -> None:
    hidden: set = set()
    leaderboard = SimpleNamespace(store=SimpleNamespace(read_optouts=lambda guild_id: set(hidden)))
    members = {HOST_ID: _member(HOST_ID), 12: _member(12)}

    # who_is_playing: user10 hides while the server settings are read.
    playing.tracker.update(GUILD_ID, HOST_ID, ("Minecraft", None), time.time())
    playing.store.update_settings(GUILD_ID, playing_enabled=True)
    feature_on = playing.feature_on_read_only

    def hide_while_reading(guild_id: int) -> bool:
        hidden.add(HOST_ID)
        return feature_on(guild_id)

    monkeypatch.setattr(playing, "feature_on_read_only", hide_while_reading)
    runtime = _runtime({"PlayingCog": playing, "LeaderboardCog": leaderboard}, FakeChannel(), members)
    assert "user10" not in await _tool(PlayingTools, runtime).coroutine()

    # get_popular_songs: the requester hides while the play log is read.
    hidden.clear()
    song_world.taste.add_play_event(
        GUILD_ID, "h", "Hidden pick", requester_id=12, autoplay=False, text_channel_id=PUBLIC_TEXT, voice_channel_id=PUBLIC_VOICE
    )
    read = song_world.taste.plays_with_places

    def hide_while_reading_log(*args: Any) -> list:
        hidden.add(12)
        return read(*args)

    monkeypatch.setattr(song_world.taste, "plays_with_places", hide_while_reading_log)
    cogs = {"YTMusic": SimpleNamespace(_taste_store=song_world.taste), "LeaderboardCog": leaderboard}
    text = await _tool(PopularSongTools, _runtime(cogs, FakeChannel(HERE), members, song_world.guild)).coroutine()
    assert "Hidden pick" not in text


def test_a_slow_chart_read_does_not_hold_up_the_players_writes(tmp_path: Path) -> None:
    import threading

    taste = TasteStore(tmp_path / "taste.db")
    taste.add_play_event(GUILD_ID, "a", "A", requester_id=1, autoplay=False)
    reading, done = threading.Event(), threading.Event()

    def slow_read() -> None:
        with taste._reader() as connection:
            connection.execute("BEGIN")
            connection.execute("SELECT * FROM play_events").fetchall()
            reading.set()
            done.wait(2)  # a read transaction still open, as during a slow query
            connection.rollback()

    reader = threading.Thread(target=slow_read)
    reader.start()
    try:
        assert reading.wait(2)
        started = time.monotonic()
        assert taste.add_play_event(GUILD_ID, "b", "B", requester_id=1, autoplay=False) is not None
        taste.add_played(GUILD_ID, "b", keep=10)
        assert time.monotonic() - started < 0.5
    finally:
        done.set()
        reader.join()


@pytest.mark.asyncio
async def test_who_is_playing_names_only_members_of_a_private_thread(playing: PlayingCog) -> None:
    members = {HOST_ID: _member(HOST_ID), 6: _member(6)}
    thread = FakeChannel(700)
    thread.type = discord.ChannelType.private_thread
    thread.members = [members[HOST_ID]]  # member 6 sees the parent, but is not in the thread
    now = time.time()
    playing.tracker.update(GUILD_ID, 6, ("Minecraft", None), now)
    playing.tracker.update(GUILD_ID, HOST_ID, ("Chess", None), now)
    playing.store.update_settings(GUILD_ID, playing_enabled=True)
    tool = _tool(PlayingTools, _runtime({"PlayingCog": playing, "LeaderboardCog": _optouts(set())}, thread, members))

    text = await tool.coroutine()

    assert "user6" not in text and "Minecraft" not in text and "<<<user10>>>" in text


def test_worker_thread_reads_do_not_wait_for_the_stores_locks(tmp_path: Path, playing: PlayingCog) -> None:
    from concurrent.futures import ThreadPoolExecutor

    taste = TasteStore(tmp_path / "taste.db")
    taste.add_play_event(GUILD_ID, "a", "A", requester_id=1, autoplay=False)
    playing.store.update_settings(GUILD_ID, playing_enabled=True)
    # A write on the event loop holds each lock (as a slow write or a waiting reader would).
    pool = ThreadPoolExecutor(3)
    try:
        with taste._lock, playing.store._lock:
            reads = [
                pool.submit(taste.top_played, GUILD_ID, 0, time.time() + 1),
                pool.submit(taste.plays_with_places, GUILD_ID, 0, time.time() + 1),
                pool.submit(playing.feature_on_read_only, GUILD_ID),
            ]
            results = [read.result(timeout=2) for read in reads]
    finally:
        pool.shutdown(wait=True)
    assert results[0][0][0] == "a" and results[1][0][0] == "a" and results[2] is True
