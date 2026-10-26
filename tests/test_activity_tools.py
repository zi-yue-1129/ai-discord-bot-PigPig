"""AI tools for starting a server game, who is playing what, and the most played songs."""

from __future__ import annotations

import asyncio
import sqlite3
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from cogs.community_lib.limits import CommunityLimits
from cogs.community_lib.store import CommunityStore
from cogs.games import MAX_GAME_OFFERS, GameOfferView, GamesCog
from cogs.music_lib.taste_store import TasteStore
from cogs.playing import PlayingCog
from llm import tools_factory
from llm.tools.activity_tools import GameTools, PlayingTools, PopularSongTools
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

    def permissions_for(self, member: Any) -> Any:
        return SimpleNamespace(view_channel=self.viewers is None or member.id in self.viewers)

    async def send(self, content: Any = None, **kwargs: Any) -> Any:
        self.sent.append((content, kwargs))
        message = FakeMessage(len(self.sent))
        self.messages.append(message)
        return message


class FakeResponse:
    def __init__(self) -> None:
        self.sent: List[tuple] = []
        self.edited: List[dict] = []

    async def send_message(self, content: Any = None, **kwargs: Any) -> None:
        self.sent.append((content, kwargs))

    async def edit_message(self, **kwargs: Any) -> None:
        self.edited.append(kwargs)


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


async def _press(view: GameOfferView, key: str, user: Any) -> FakeResponse:
    """Presses the offer's button whose label is ``key`` as ``user``."""
    response = FakeResponse()
    interaction = SimpleNamespace(user=user, response=response)
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
async def test_who_is_playing_fails_closed_and_reads_no_database_when_built(playing: PlayingCog, monkeypatch: pytest.MonkeyPatch) -> None:
    members = {HOST_ID: _member(HOST_ID)}
    playing.tracker.update(GUILD_ID, HOST_ID, ("Minecraft", None), time.time())

    def no_database(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("the tool list must be built without reading a database")

    with monkeypatch.context() as patch:
        patch.setattr(playing.store, "get_settings", no_database)
        tool = _tool(PlayingTools, _runtime({"PlayingCog": playing, "LeaderboardCog": _optouts(sqlite3.OperationalError)}, FakeChannel(), members))
        assert tool is not None
        # The opt-out list cannot be read: nothing is said (and the settings are not even read).
        assert await tool.coroutine() == UNAVAILABLE

    tool = _tool(PlayingTools, _runtime({"PlayingCog": playing, "LeaderboardCog": _optouts(set())}, FakeChannel(), members))
    assert "turned off" in await tool.coroutine()
    playing.store.update_settings(GUILD_ID, playing_enabled=True)
    assert "<<<user10>>>" in await tool.coroutine()


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
