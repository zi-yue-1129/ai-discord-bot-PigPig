"""Fixtures for the music cog tests."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from music_cog.helpers import (
    BOT_USER_ID,
    GUILD_ID,
    REQUESTER_ID,
    FakeChannel,
    FakeLangManager,
    FakeVoiceClient,
    async_noop,
    make_member,
)

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.state_manager import StateManager


@pytest.fixture
def voice_channel() -> object:
    """The voice channel the bot is connected to."""
    return object()


@pytest.fixture
def text_channel() -> FakeChannel:
    return FakeChannel()


@pytest.fixture
def voice_client(voice_channel: object) -> FakeVoiceClient:
    return FakeVoiceClient(voice_channel)


@pytest.fixture
def guild(voice_client: FakeVoiceClient) -> SimpleNamespace:
    return SimpleNamespace(id=GUILD_ID, name="guild", voice_client=voice_client)


@pytest.fixture
def cog(
    guild: SimpleNamespace, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch
) -> YTMusic:
    """A music cog wired to fakes; no Discord connection or network is used."""

    async def _no_report(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr("cogs.music.func.report_error", _no_report)

    ui_manager = SimpleNamespace(
        views={},
        get_current_view=lambda guild_id: None,
        cleanup_view=async_noop,
    )
    bot = SimpleNamespace(
        user=SimpleNamespace(id=BOT_USER_ID),
        state_manager=StateManager(),
        ui_manager=ui_manager,
        loop=asyncio.get_event_loop_policy().get_event_loop(),
        get_cog=lambda name: None,
        get_guild=lambda guild_id: guild if guild_id == GUILD_ID else None,
    )
    music = YTMusic(bot)
    music.lang_manager = FakeLangManager()
    return music


@pytest.fixture
def requester(voice_channel: object) -> SimpleNamespace:
    """A user standing in the bot's voice channel."""
    return make_member(REQUESTER_ID, voice_channel)


@pytest.fixture
def ctx(
    guild: SimpleNamespace, text_channel: FakeChannel, requester: SimpleNamespace
) -> PlaybackContext:
    return PlaybackContext(guild=guild, channel=text_channel, user=requester)


