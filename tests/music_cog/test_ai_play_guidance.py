"""A bot that is not in a voice channel is just idle; the AI must not treat it as an obstacle."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import pytest
from music_cog.helpers import GUILD_ID, FakeChannel, FakeLangManager, make_member

from addons.settings import MusicAISettings
from cogs.music import YTMusic

from llm.music_context import build_music_context, render_music_context
from llm.tools.music_tools import MusicTools

LOCALES = ("zh_TW", "zh_CN", "en_US", "ja_JP")

DISCONNECTED: Dict[str, Any] = {
    "state": "disconnected",
    "current": None,
    "queue": [],
    "mode": "no_loop",
    "shuffle": False,
    "autoplay": False,
    "volume": 100,
}


IDLE: Dict[str, Any] = {
    "state": "idle",
    "current": None,
    "queue": [],
    "mode": "no_loop",
    "shuffle": False,
    "autoplay": False,
    "volume": 100,
}


class StatusOnlyService:
    def status(self, guild_id: int) -> Dict[str, Any]:
        return IDLE


def _tools() -> Dict[str, Any]:
    guild = SimpleNamespace(id=7)
    message = SimpleNamespace(guild=guild, channel=FakeChannel(), author=make_member(42, voice_channel=object()))
    cogs = {"YTMusic": SimpleNamespace(service=StatusOnlyService()), "LanguageManager": FakeLangManager()}
    runtime = SimpleNamespace(bot=SimpleNamespace(get_cog=cogs.get), message=message, logger=None)
    return {tool.name: tool for tool in MusicTools(runtime).get_tools()}


def test_a_guild_without_a_voice_connection_is_reported_as_idle(cog: YTMusic, guild: SimpleNamespace) -> None:
    guild.voice_client = None

    assert cog.service.status(GUILD_ID)["state"] == "idle"


def test_the_status_never_mentions_a_voice_connection() -> None:
    text = render_music_context(IDLE, list_titles=True, max_titles=10)

    assert "disconnected" not in text.lower()
    assert "voice" not in text.lower()


@pytest.mark.asyncio
async def test_no_context_is_added_when_the_bot_is_not_connected_and_nothing_is_queued(
    cog: YTMusic, guild: SimpleNamespace,
) -> None:
    guild.voice_client = None
    bot = SimpleNamespace(get_cog=lambda name: cog)

    assert await build_music_context(bot, SimpleNamespace(id=GUILD_ID), MusicAISettings()) == ""


def test_play_music_tells_the_model_not_to_decide_voice_presence_itself() -> None:
    description = _tools()["play_music"].description

    assert "joins" in description
    assert "do not refuse" in description.lower()


@pytest.mark.parametrize("locale", LOCALES)
def test_every_music_tool_has_a_progress_message(locale: str) -> None:
    path = Path("translations") / locale / "system" / "chat_bot.json"
    texts = json.loads(path.read_text(encoding="utf-8"))["responses"]["tools"]

    missing = [name for name in _tools() if name not in texts]

    assert missing == []

