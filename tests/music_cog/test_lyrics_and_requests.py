"""Lyrics lookup and display, the song request channel, and the AI tools for the new features."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

import discord
import pytest
from music_cog.helpers import GUILD_ID, FakeChannel, FakeLangManager, make_member, make_song

from addons.settings import LyricsSettings
from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.lyrics import Lyrics, LyricsClient, clean_title, paginate, parse_lrc, search_queries, synced_excerpt
from cogs.music_lib.service import ActionResult
from llm.tools.music_tools import MusicTools

SYNCED = "[00:01.00] first\n[00:05.50] second\n[00:09.00] third"


def _client(results: List[Any], calls: List[Dict[str, str]] = None) -> LyricsClient:
    async def fetch(url: str, params: Dict[str, str]) -> Any:
        if calls is not None:
            calls.append(params)
        return results

    return LyricsClient(LyricsSettings(), fetch=fetch)


# ------------------------------------------------------------------ parsing


def test_lrc_lines_are_read_in_time_order() -> None:
    assert parse_lrc("[01:00.00][00:02.00] chorus\n[00:01.5] intro\nno stamp") == [
        (1.5, "intro"), (2.0, "chorus"), (60.0, "chorus")
    ]


def test_video_noise_is_removed_from_titles() -> None:
    assert clean_title("Rick Astley - Never Gonna Give You Up (Official Music Video) [4K]") == \
        "Rick Astley - Never Gonna Give You Up"
    assert clean_title("YOASOBI「アイドル」 Official Music Video") == "YOASOBI「アイドル」"
    assert clean_title("Song feat. Someone | Channel") == "Song"


def test_an_artist_dash_title_is_searched_by_artist_and_title() -> None:
    queries = search_queries("Rick Astley - Never Gonna Give You Up (Official Video)", "RickAstleyVEVO")

    assert queries[0] == {"track_name": "Never Gonna Give You Up", "artist_name": "Rick Astley"}
    assert len(queries) <= 4


def test_the_current_line_is_bold_between_its_neighbours() -> None:
    lyrics = Lyrics(track="t", artist="a", plain="", synced=parse_lrc(SYNCED))

    excerpt = synced_excerpt(lyrics, 6.0)

    assert excerpt.splitlines() == ["first", "**▶ second**", "third"]
    assert synced_excerpt(lyrics, 0.0).splitlines()[0] == "**♪**"


def test_long_lyrics_are_split_into_pages_at_line_breaks() -> None:
    pages = paginate("line\n" * 1000, page_size=100)

    assert len(pages) > 1 and all(len(page) <= 100 for page in pages)


# ------------------------------------------------------------------ lookup


@pytest.mark.asyncio
async def test_time_stamped_lyrics_of_the_right_length_win() -> None:
    client = _client([
        {"trackName": "Song", "artistName": "A", "duration": 300, "plainLyrics": "wrong version", "syncedLyrics": SYNCED},
        {"trackName": "Song", "artistName": "A", "duration": 201, "plainLyrics": "plain only"},
        {"trackName": "Song", "artistName": "A", "duration": 199, "plainLyrics": "right", "syncedLyrics": SYNCED},
    ])

    found = await client.search({"q": "song"}, duration=200)

    assert found.plain == "right" and len(found.synced) == 3


@pytest.mark.asyncio
async def test_lyrics_are_looked_up_once_per_song() -> None:
    calls: List[Dict[str, str]] = []
    client = _client([{"trackName": "Song", "artistName": "A", "plainLyrics": "la la"}], calls)
    song = {"video_id": "v1", "title": "A - Song", "author": "A", "duration": 0}

    first = await client.for_song(song)
    second = await client.for_song(song)

    assert first is second and first.plain == "la la"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_no_lyrics_is_remembered_too() -> None:
    calls: List[Dict[str, str]] = []
    client = _client([], calls)
    song = {"video_id": "v1", "title": "Song", "author": "A", "duration": 0}

    assert await client.for_song(song) is None
    tries = len(calls)
    assert await client.for_song(song) is None
    assert len(calls) == tries


# --------------------------------------------------------- player display


@pytest.mark.asyncio
async def test_the_lyrics_field_follows_the_position(cog: YTMusic) -> None:
    song = make_song(1)
    state = cog.state_manager.get_state(GUILD_ID)
    state.current_song = song
    state.show_lyrics = True
    state.lyrics = ("v1", Lyrics(track="t", artist="a", plain="", synced=parse_lrc(SYNCED)))
    state.position = 9.5
    view = SimpleNamespace(guild=SimpleNamespace(id=GUILD_ID), current_embed=discord.Embed(title="x"))

    assert cog.refresh_lyrics_field(view)
    assert "**▶ third**" in view.current_embed.fields[0].value

    state.show_lyrics = False
    cog.refresh_lyrics_field(view)
    assert view.current_embed.fields == []


@pytest.mark.asyncio
async def test_lyrics_without_time_stamps_say_so(cog: YTMusic) -> None:
    state = cog.state_manager.get_state(GUILD_ID)
    state.current_song = make_song(1)
    state.show_lyrics = True
    state.lyrics = ("v1", Lyrics(track="t", artist="a", plain="la"))
    view = SimpleNamespace(guild=SimpleNamespace(id=GUILD_ID), current_embed=discord.Embed(title="x"))

    cog.refresh_lyrics_field(view)

    assert view.current_embed.fields[0].value == "system.music.lyrics.not_synced"


# --------------------------------------------------------- request channel


class _Message:
    def __init__(self, guild: Any, channel: Any, author: Any, content: str) -> None:
        self.guild, self.channel, self.author, self.content = guild, channel, author, content
        self.deleted = False

    async def delete(self) -> None:
        self.deleted = True


@pytest.mark.asyncio
async def test_a_message_in_the_request_channel_is_a_song_request(cog: YTMusic, guild: Any, requester: Any, monkeypatch) -> None:
    channel = FakeChannel()
    channel.id, channel.guild = 123, guild
    cog.store.update_settings(GUILD_ID, request_channel_id=123)
    requests: List[str] = []

    async def fake_play(ctx: PlaybackContext, query: str, play_next: bool = False) -> ActionResult:
        requests.append(query)
        assert ctx.channel is channel and ctx.user is requester
        return ActionResult(ok=True, data={"kind": "video", "title": "Lemon", "started": False, "position": 2})

    monkeypatch.setattr(cog.service, "play", fake_play)
    message = _Message(guild, channel, requester, "米津玄師 Lemon")

    handled = await cog.requests.handle(message)

    assert handled and message.deleted and requests == ["米津玄師 Lemon"]
    assert channel.sent[0].kwargs["embed"].title.endswith("system.music.request_channel.queued")
    assert channel.sent[0].kwargs["delete_after"] > 0


@pytest.mark.asyncio
async def test_other_channels_are_left_to_the_chat(cog: YTMusic, guild: Any, requester: Any) -> None:
    channel = FakeChannel()
    channel.id, channel.guild = 124, guild
    cog.store.update_settings(GUILD_ID, request_channel_id=123)

    assert not await cog.requests.handle(_Message(guild, channel, requester, "hello"))


# ----------------------------------------------------------------- AI tools


class _Service:
    def __init__(self) -> None:
        self.calls: List[tuple] = []

    async def seek(self, ctx: Any, seconds: float, relative: bool = False) -> ActionResult:
        self.calls.append(("seek", seconds, relative))
        return ActionResult(ok=True, data={"position": 90, "duration": 200, "title": "Lemon"})

    async def set_filter(self, ctx: Any, name: str) -> ActionResult:
        self.calls.append(("set_filter", name))
        return ActionResult(ok=True, data={"filter": name})

    async def previous(self, ctx: Any) -> ActionResult:
        self.calls.append(("previous",))
        return ActionResult(ok=True, data={"title": "Lemon", "replayed": False})

    async def move(self, ctx: Any, position: int, to: int) -> ActionResult:
        self.calls.append(("move", position, to))
        return ActionResult(ok=True, data={"title": "Lemon", "position": to})


def _tools(service: _Service, playlists: Any = None) -> Dict[str, Any]:
    message = SimpleNamespace(guild=SimpleNamespace(id=GUILD_ID), channel=FakeChannel(),
                              author=make_member(42, voice_channel=object()))
    cog = SimpleNamespace(service=service, playlists=playlists)
    bot = SimpleNamespace(get_cog={"YTMusic": cog, "LanguageManager": FakeLangManager()}.get)
    runtime = SimpleNamespace(bot=bot, message=message, logger=None)
    return {tool.name: tool for tool in MusicTools(runtime).get_tools()}


@pytest.mark.asyncio
@pytest.mark.parametrize(("name", "arguments", "call"), [
    ("seek_music", {"seconds": -10, "relative": True}, ("seek", -10, True)),
    ("set_music_effect", {"effect": "nightcore"}, ("set_filter", "nightcore")),
    ("play_previous_song", {}, ("previous",)),
    ("move_song_in_queue", {"position": 3, "to": 1}, ("move", 3, 1)),
])
async def test_the_new_ai_tools_call_the_service(name: str, arguments: Dict[str, Any], call: tuple) -> None:
    service = _Service()

    reply = await _tools(service)[name].ainvoke(arguments)

    assert service.calls == [call]
    assert not reply.startswith("Error")


@pytest.mark.asyncio
async def test_the_ai_can_play_a_saved_playlist() -> None:
    played: List[tuple] = []

    class _Playlists:
        async def play(self, ctx: Any, name: str, scope: Any = None, *, shuffle: bool = False) -> ActionResult:
            played.append((name, shuffle))
            return ActionResult(ok=True, data={"name": "Chill", "total": 12, "channel": "vc"})

    reply = await _tools(_Service(), _Playlists())["play_saved_playlist"].ainvoke({"name": "chill", "shuffle": True})

    assert played == [("chill", True)]
    assert "12" in reply and "Chill" in reply


# ------------------------------------------------------- timing accuracy


@pytest.mark.asyncio
async def test_an_entry_of_unknown_length_does_not_beat_one_of_the_right_length() -> None:
    client = _client([
        {"trackName": "Song", "artistName": "A", "plainLyrics": "unknown length", "syncedLyrics": SYNCED},
        {"trackName": "Song", "artistName": "A", "duration": 238, "plainLyrics": "right length", "syncedLyrics": SYNCED},
    ])

    found = await client.search({"q": "song"}, duration=238)

    assert found.plain == "right length"


@pytest.mark.asyncio
async def test_time_stamps_of_a_recording_ten_seconds_off_in_length_are_kept() -> None:
    # Measured against YouTube's own captions: an entry 10 s shorter than the video was still
    # within about a second of the real timing, so a length gap alone does not mean a shifted axis.
    client = _client([
        {"trackName": "Song", "artistName": "A", "duration": 150, "plainLyrics": "la la", "syncedLyrics": SYNCED},
    ])

    found = await client.search({"q": "song"}, duration=160)

    assert found.plain == "la la"
    assert len(found.synced) == 3


@pytest.mark.asyncio
async def test_time_stamps_of_a_recording_a_few_seconds_off_are_kept() -> None:
    client = _client([
        {"trackName": "Song", "artistName": "A", "duration": 156, "plainLyrics": "la la", "syncedLyrics": SYNCED},
    ])

    found = await client.search({"q": "song"}, duration=160)

    assert len(found.synced) == 3


@pytest.mark.asyncio
async def test_the_lyrics_field_shows_the_line_that_is_about_to_be_sung(cog: YTMusic) -> None:
    state = cog.state_manager.get_state(GUILD_ID)
    state.current_song = make_song(1)
    state.show_lyrics = True
    state.lyrics = ("v1", Lyrics(track="t", artist="a", plain="", synced=parse_lrc(SYNCED)))
    view = SimpleNamespace(guild=SimpleNamespace(id=GUILD_ID), current_embed=discord.Embed(title="x"))

    state.position = 7.6
    cog.refresh_lyrics_field(view)
    assert "**▶ third**" in view.current_embed.fields[0].value

    state.position = 7.4
    cog.refresh_lyrics_field(view)
    assert "**▶ second**" in view.current_embed.fields[0].value
