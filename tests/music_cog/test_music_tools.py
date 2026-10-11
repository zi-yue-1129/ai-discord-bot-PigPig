"""Tests for the LLM-facing music tools."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest
from music_cog.helpers import FakeChannel, FakeLangManager, make_member

from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.service import ActionResult
from llm.tools.music_tools import MusicTools

ACTION_TOOLS = {
    "play_music",
    "skip_music",
    "pause_music",
    "resume_music",
    "stop_music",
    "set_music_loop_mode",
    "set_music_shuffle",
    "set_music_volume",
    "remove_song_from_queue",
    "clear_music_queue",
}


class FakeService:
    """Records the calls made by the tools and returns canned results."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.result = ActionResult(ok=True, detail="Done.", data={})
        self.status_value: Dict[str, Any] = {
            "state": "idle", "current": None, "queue": [], "mode": "no_loop",
            "shuffle": False, "autoplay": False, "volume": 100,
        }

    async def _record(self, name: str, ctx: PlaybackContext, *args: Any) -> ActionResult:
        self.calls.append((name, ctx, *args))
        return self.result

    async def play(self, ctx: PlaybackContext, query: str) -> ActionResult:
        return await self._record("play", ctx, query)

    async def skip(self, ctx: PlaybackContext) -> ActionResult:
        return await self._record("skip", ctx)

    async def pause(self, ctx: PlaybackContext) -> ActionResult:
        return await self._record("pause", ctx)

    async def resume(self, ctx: PlaybackContext) -> ActionResult:
        return await self._record("resume", ctx)

    async def stop(self, ctx: PlaybackContext) -> ActionResult:
        return await self._record("stop", ctx)

    async def set_mode(self, ctx: PlaybackContext, mode: str) -> ActionResult:
        return await self._record("set_mode", ctx, mode)

    async def set_shuffle(self, ctx: PlaybackContext, enabled: bool) -> ActionResult:
        return await self._record("set_shuffle", ctx, enabled)

    async def set_volume(self, ctx: PlaybackContext, percent: int) -> ActionResult:
        return await self._record("set_volume", ctx, percent)

    async def remove_from_queue(self, ctx: PlaybackContext, position: int) -> ActionResult:
        return await self._record("remove_from_queue", ctx, position)

    async def clear_queue(self, ctx: PlaybackContext) -> ActionResult:
        return await self._record("clear_queue", ctx)

    def status(self, guild_id: int) -> Dict[str, Any]:
        self.calls.append(("status", guild_id))
        return self.status_value


def _runtime(service: Optional[FakeService], *, in_guild: bool = True) -> SimpleNamespace:
    guild = SimpleNamespace(id=7) if in_guild else None
    message = SimpleNamespace(
        guild=guild, channel=FakeChannel(), author=make_member(42, voice_channel=object())
    )
    cog = SimpleNamespace(service=service) if service is not None else None
    cogs = {"YTMusic": cog, "LanguageManager": FakeLangManager()}
    bot = SimpleNamespace(get_cog=cogs.get)
    return SimpleNamespace(bot=bot, message=message, logger=None)


def _tools(runtime: SimpleNamespace) -> Dict[str, Any]:
    return {tool.name: tool for tool in MusicTools(runtime).get_tools()}


def test_exposes_the_expected_tools() -> None:
    tools = _tools(_runtime(FakeService()))

    assert set(tools) == ACTION_TOOLS | {"get_music_status"}


def test_every_music_tool_belongs_to_the_info_agent() -> None:
    """The info agent's tool results are handed to the reply agent, which never sees the
    results of its own tools; music replies depend on what actually happened."""
    tools = _tools(_runtime(FakeService()))

    for name, tool in tools.items():
        assert tool.__dict__.get("target_agent_mode", "info") == "info", name


@pytest.mark.asyncio
async def test_play_music_passes_the_message_context_to_the_service() -> None:
    service = FakeService()
    runtime = _runtime(service)
    service.result = ActionResult(ok=True, data={"kind": "video", "title": "稻香", "duration": 223})

    reply = await _tools(runtime)["play_music"].ainvoke({"query": "稻香"})

    name, ctx, query = service.calls[0]
    assert (name, query) == ("play", "稻香")
    assert ctx.guild is runtime.message.guild
    assert ctx.channel is runtime.message.channel
    assert ctx.user is runtime.message.author
    assert "稻香" in reply


@pytest.mark.asyncio
async def test_play_music_reports_playlists() -> None:
    service = FakeService()
    service.result = ActionResult(
        ok=True, data={"kind": "playlist", "added": 5, "total": 12, "titles": ["a", "b"]}
    )

    reply = await _tools(_runtime(service))["play_music"].ainvoke({"query": "https://youtube.com/playlist?list=x"})

    assert "5" in reply and "12" in reply


@pytest.mark.asyncio
async def test_failures_are_returned_as_error_text_the_model_can_relay() -> None:
    service = FakeService()
    service.result = ActionResult(ok=False, reason="user_not_in_voice", detail="The user must join a voice channel first.")

    reply = await _tools(_runtime(service))["play_music"].ainvoke({"query": "x"})

    assert reply.startswith("Error:")
    assert "voice channel" in reply


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "arguments", "service_call"),
    [
        ("skip_music", {}, ("skip",)),
        ("pause_music", {}, ("pause",)),
        ("resume_music", {}, ("resume",)),
        ("stop_music", {}, ("stop",)),
        ("set_music_loop_mode", {"mode": "loop_queue"}, ("set_mode", "loop_queue")),
        ("set_music_shuffle", {"enabled": True}, ("set_shuffle", True)),
        ("set_music_volume", {"percent": 30}, ("set_volume", 30)),
        ("remove_song_from_queue", {"position": 2}, ("remove_from_queue", 2)),
        ("clear_music_queue", {}, ("clear_queue",)),
    ],
)
async def test_each_control_calls_the_matching_service_method(
    tool_name: str, arguments: Dict[str, Any], service_call: tuple
) -> None:
    service = FakeService()

    await _tools(_runtime(service))[tool_name].ainvoke(arguments)

    name, _ctx, *rest = service.calls[0]
    assert (name, *rest) == service_call


@pytest.mark.asyncio
async def test_status_describes_the_player() -> None:
    service = FakeService()
    service.status_value = {
        "state": "playing",
        "current": {"title": "稻香", "author": "Jay", "duration": 223, "url": "u"},
        "queue": [{"title": "next song", "author": "x", "duration": 100, "url": "v"}],
        "mode": "loop_queue",
        "shuffle": True,
        "autoplay": False,
        "volume": 55,
    }

    reply = await _tools(_runtime(service))["get_music_status"].ainvoke({})

    assert "playing" in reply
    assert "稻香" in reply
    assert "next song" in reply
    assert "loop_queue" in reply


@pytest.mark.asyncio
async def test_tools_refuse_to_run_in_direct_messages() -> None:
    service = FakeService()

    reply = await _tools(_runtime(service, in_guild=False))["skip_music"].ainvoke({})

    assert reply.startswith("Error:")
    assert service.calls == []


@pytest.mark.asyncio
async def test_tools_report_a_missing_music_cog() -> None:
    reply = await _tools(_runtime(None))["skip_music"].ainvoke({})

    assert reply.startswith("Error:")
    assert "not loaded" in reply


@pytest.mark.asyncio
async def test_remove_song_reports_which_song_was_removed() -> None:
    service = FakeService()
    service.result = ActionResult(ok=True, data={"title": "稻香", "position": 2})

    reply = await _tools(_runtime(service))["remove_song_from_queue"].ainvoke({"position": 2})

    assert "稻香" in reply


@pytest.mark.asyncio
async def test_clear_queue_reports_how_many_songs_were_removed() -> None:
    service = FakeService()
    service.result = ActionResult(ok=True, data={"removed": 4})

    reply = await _tools(_runtime(service))["clear_music_queue"].ainvoke({})

    assert "4" in reply


@pytest.mark.asyncio
async def test_volume_failures_are_returned_as_error_text() -> None:
    service = FakeService()
    service.result = ActionResult(ok=False, reason="invalid_volume", detail="Volume must be between 0 and 100.")

    reply = await _tools(_runtime(service))["set_music_volume"].ainvoke({"percent": 500})

    assert reply == "Error: Volume must be between 0 and 100."


@pytest.mark.asyncio
async def test_status_states_where_the_requester_is() -> None:
    runtime = _runtime(FakeService())
    runtime.message.author = make_member(42, voice_channel=SimpleNamespace(name="General"))

    reply = await _tools(runtime)["get_music_status"].ainvoke({})

    assert "Requester is in the voice channel 'General'" in reply


@pytest.mark.asyncio
async def test_status_states_when_the_requester_is_not_in_a_voice_channel() -> None:
    runtime = _runtime(FakeService())
    runtime.message.author = make_member(42, voice_channel=None)

    reply = await _tools(runtime)["get_music_status"].ainvoke({})

    assert "Requester is not in a voice channel" in reply


@pytest.mark.asyncio
async def test_play_reports_the_voice_channel_it_plays_in() -> None:
    service = FakeService()
    service.result = ActionResult(
        ok=True, data={"kind": "video", "title": "綠光", "duration": 200, "started": True, "channel": "General"}
    )

    reply = await _tools(_runtime(service))["play_music"].ainvoke({"query": "綠光"})

    assert reply == "Now playing '綠光' (03:20) in the voice channel 'General'."


@pytest.mark.asyncio
async def test_a_queued_song_names_the_one_it_waits_behind() -> None:
    service = FakeService()
    service.result = ActionResult(
        ok=True,
        data={"kind": "video", "title": "綠光", "duration": 200, "started": False, "position": 2,
              "current": "稻香", "channel": "General"},
    )

    reply = await _tools(_runtime(service))["play_music"].ainvoke({"query": "綠光"})

    assert reply == "Queued '綠光' (03:20) at position 2 in the voice channel 'General'; it plays after '稻香'."


@pytest.mark.asyncio
async def test_skip_names_the_next_song() -> None:
    service = FakeService()
    service.result = ActionResult(ok=True, data={"skipped": "稻香", "next": "綠光"})

    reply = await _tools(_runtime(service))["skip_music"].ainvoke({})

    assert reply == "Skipped '稻香'. Up next: '綠光'."


@pytest.mark.asyncio
async def test_skip_says_when_nothing_follows() -> None:
    service = FakeService()
    service.result = ActionResult(ok=True, data={"skipped": "稻香", "next": None})

    reply = await _tools(_runtime(service))["skip_music"].ainvoke({})

    assert reply == "Skipped '稻香'. The queue is now empty."


@pytest.mark.asyncio
async def test_stop_says_how_many_queued_songs_were_dropped() -> None:
    service = FakeService()
    service.result = ActionResult(ok=True, data={"cleared": 3})

    reply = await _tools(_runtime(service))["stop_music"].ainvoke({})

    assert reply == "Stopped the music, dropped 3 queued songs and left the voice channel."


@pytest.mark.asyncio
async def test_pause_names_the_song() -> None:
    service = FakeService()
    service.result = ActionResult(ok=True, data={"title": "稻香"})

    reply = await _tools(_runtime(service))["pause_music"].ainvoke({})

    assert reply == "Paused '稻香'."
