"""Tests for the LLM-facing music tools."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest
from music_cog.helpers import make_member

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
}


class FakeService:
    """Records the calls made by the tools and returns canned results."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.result = ActionResult(ok=True, detail="Done.", data={})
        self.status_value: Dict[str, Any] = {
            "state": "idle", "current": None, "queue": [], "mode": "no_loop",
            "shuffle": False, "autoplay": False,
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

    def status(self, guild_id: int) -> Dict[str, Any]:
        self.calls.append(("status", guild_id))
        return self.status_value


def _runtime(service: Optional[FakeService], *, in_guild: bool = True) -> SimpleNamespace:
    guild = SimpleNamespace(id=7) if in_guild else None
    message = SimpleNamespace(
        guild=guild, channel=object(), author=make_member(42, voice_channel=object())
    )
    cog = SimpleNamespace(service=service) if service is not None else None
    bot = SimpleNamespace(get_cog=lambda name: cog if name == "YTMusic" else None)
    return SimpleNamespace(bot=bot, message=message, logger=None)


def _tools(runtime: SimpleNamespace) -> Dict[str, Any]:
    return {tool.name: tool for tool in MusicTools(runtime).get_tools()}


def test_exposes_the_expected_tools() -> None:
    tools = _tools(_runtime(FakeService()))

    assert set(tools) == ACTION_TOOLS | {"get_music_status"}


def test_actions_belong_to_the_message_agent_and_status_to_the_info_agent() -> None:
    tools = _tools(_runtime(FakeService()))

    for name in ACTION_TOOLS:
        assert tools[name].__dict__["target_agent_mode"] == "message", name
    assert tools["get_music_status"].__dict__.get("target_agent_mode", "info") == "info"


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
