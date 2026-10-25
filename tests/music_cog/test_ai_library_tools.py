"""AI tools for playlists, the play history and the server's music settings."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

import pytest
from music_cog.helpers import GUILD_ID, FakeChannel, FakeLangManager, make_member

from cogs.music_lib.service import ActionResult
from llm.tools.music_tools import MusicTools


def _playlist(name: str, titles: List[str]) -> SimpleNamespace:
    tracks = [{"title": title, "url": f"https://youtu.be/{index}", "duration": 200} for index, title in enumerate(titles)]
    return SimpleNamespace(name=name, tracks=tracks, track_count=len(tracks))


class _Playlists:
    """Playlist service stand-in that records what the tools ask for."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.result = ActionResult(ok=True, data={})
        self.names_value: Dict[str, List[Any]] = {"personal": [], "server": []}
        self.found = _playlist("Chill", ["Lemon", "Kick Back"])

    async def create(self, ctx: Any, name: str, scope: str) -> ActionResult:
        self.calls.append(("create", name, scope))
        return ActionResult(ok=True, data={"name": name}) if self.result.ok else self.result

    async def names(self, ctx: Any) -> Dict[str, List[Any]]:
        self.calls.append(("names",))
        return self.names_value

    async def find(self, ctx: Any, name: str) -> ActionResult:
        self.calls.append(("find", name))
        if not self.result.ok:
            return self.result
        return ActionResult(ok=True, data={"playlist": self.found, "scope": "personal"})

    async def remove_track(self, ctx: Any, name: str, position: int, scope: str) -> ActionResult:
        self.calls.append(("remove_track", name, position, scope))
        return ActionResult(ok=True, data={"title": "Lemon", "position": position}) if self.result.ok else self.result

    async def save_queue(self, ctx: Any, name: str, scope: str) -> ActionResult:
        self.calls.append(("save_queue", name, scope))
        return ActionResult(ok=True, data={"added": 3, "skipped": 1, "name": name}) if self.result.ok else self.result


class _Service:
    def __init__(self) -> None:
        self.songs: List[dict] = []

    def history(self, guild_id: int) -> List[dict]:
        return self.songs


class _Store:
    def __init__(self, settings: SimpleNamespace) -> None:
        self._settings = settings

    def get_settings(self, guild_id: int) -> SimpleNamespace:
        return self._settings


SETTINGS = SimpleNamespace(
    dj_role_id=555, vote_ratio=0.5, default_volume=40, stay_247=True, stay_channel_id=777,
    request_channel_id=888, stage_announce=False,
)


def _tools(playlists: _Playlists, service: _Service = None, settings: SimpleNamespace = SETTINGS) -> Dict[str, Any]:
    message = SimpleNamespace(guild=SimpleNamespace(id=GUILD_ID), channel=FakeChannel(),
                              author=make_member(42, voice_channel=object()))
    cog = SimpleNamespace(service=service or _Service(), playlists=playlists, store=_Store(settings))
    bot = SimpleNamespace(get_cog={"YTMusic": cog, "LanguageManager": FakeLangManager()}.get)
    runtime = SimpleNamespace(bot=bot, message=message, logger=None)
    return {tool.name: tool for tool in MusicTools(runtime).get_tools()}


@pytest.mark.asyncio
async def test_the_ai_can_create_a_personal_or_a_server_playlist() -> None:
    playlists = _Playlists()
    tools = _tools(playlists)

    personal = await tools["create_music_playlist"].ainvoke({"name": "Chill"})
    server = await tools["create_music_playlist"].ainvoke({"name": "Party", "server_playlist": True})

    assert playlists.calls == [("create", "Chill", "personal"), ("create", "Party", "server")]
    assert "Chill" in personal and "Party" in server
    assert not personal.startswith("Error")


@pytest.mark.asyncio
async def test_the_ai_lists_both_kinds_of_playlists_with_their_sizes() -> None:
    playlists = _Playlists()
    playlists.names_value = {"personal": [_playlist("Chill", ["a", "b"])], "server": [_playlist("Party", [])]}

    reply = await _tools(playlists)["list_music_playlists"].ainvoke({})

    assert "Chill (2" in reply and "Party (0" in reply
    assert reply.index("Chill") < reply.index("Party")


@pytest.mark.asyncio
async def test_the_ai_says_when_there_are_no_playlists() -> None:
    reply = await _tools(_Playlists())["list_music_playlists"].ainvoke({})

    assert "no playlists" in reply.lower()


@pytest.mark.asyncio
async def test_viewing_a_playlist_numbers_its_songs_so_one_can_be_removed() -> None:
    playlists = _Playlists()

    reply = await _tools(playlists)["view_music_playlist"].ainvoke({"name": "chill"})

    assert playlists.calls == [("find", "chill")]
    assert "1. Lemon" in reply and "2. Kick Back" in reply


@pytest.mark.asyncio
async def test_a_long_playlist_is_cut_with_a_count_of_the_rest() -> None:
    playlists = _Playlists()
    playlists.found = _playlist("Big", [f"song {index}" for index in range(60)])

    reply = await _tools(playlists)["view_music_playlist"].ainvoke({"name": "Big"})

    assert "40. song 39" in reply
    assert "41." not in reply
    assert "20 more" in reply


@pytest.mark.asyncio
async def test_the_ai_removes_a_song_from_a_playlist_by_position() -> None:
    playlists = _Playlists()
    tools = _tools(playlists)

    reply = await tools["remove_song_from_playlist"].ainvoke({"playlist": "Chill", "position": 2})
    await tools["remove_song_from_playlist"].ainvoke({"playlist": "Party", "position": 1, "server_playlist": True})

    assert playlists.calls == [("remove_track", "Chill", 2, "personal"), ("remove_track", "Party", 1, "server")]
    assert "Lemon" in reply and "Chill" in reply


@pytest.mark.asyncio
async def test_the_ai_saves_the_queue_as_a_playlist() -> None:
    playlists = _Playlists()

    reply = await _tools(playlists)["save_queue_as_playlist"].ainvoke({"name": "Tonight"})

    assert playlists.calls == [("save_queue", "Tonight", "personal")]
    assert "3" in reply and "Tonight" in reply


@pytest.mark.asyncio
@pytest.mark.parametrize(("tool", "arguments"), [
    ("create_music_playlist", {"name": "Chill"}),
    ("view_music_playlist", {"name": "Chill"}),
    ("remove_song_from_playlist", {"playlist": "Chill", "position": 1}),
    ("save_queue_as_playlist", {"name": "Chill"}),
])
async def test_a_refused_playlist_action_is_reported_as_an_error(tool: str, arguments: Dict[str, Any]) -> None:
    playlists = _Playlists()
    playlists.result = ActionResult(ok=False, reason="playlist_not_found", detail="No such playlist.")

    reply = await _tools(playlists)[tool].ainvoke(arguments)

    assert reply == "Error: No such playlist."


@pytest.mark.asyncio
async def test_the_ai_can_read_what_was_played_this_session() -> None:
    service = _Service()
    service.songs = [{"title": "Lemon", "duration": 255}, {"title": "Kick Back", "duration": 193}]

    reply = await _tools(_Playlists(), service)["get_music_history"].ainvoke({})

    assert "1. Lemon" in reply and "2. Kick Back" in reply


@pytest.mark.asyncio
async def test_an_empty_history_is_said_plainly() -> None:
    reply = await _tools(_Playlists())["get_music_history"].ainvoke({})

    assert "nothing" in reply.lower()


@pytest.mark.asyncio
async def test_the_ai_can_read_the_servers_music_settings() -> None:
    reply = await _tools(_Playlists())["get_music_settings"].ainvoke({})

    assert "<@&555>" in reply
    assert "50%" in reply and "40%" in reply
    assert "<#777>" in reply and "<#888>" in reply


@pytest.mark.asyncio
async def test_unset_music_settings_read_as_not_set() -> None:
    unset = SimpleNamespace(dj_role_id=None, vote_ratio=0.5, default_volume=100, stay_247=False,
                            stay_channel_id=None, request_channel_id=None, stage_announce=True)

    reply = await _tools(_Playlists(), settings=unset)["get_music_settings"].ainvoke({})

    assert "<@&" not in reply and "<#" not in reply
    assert "not set" in reply.lower()
