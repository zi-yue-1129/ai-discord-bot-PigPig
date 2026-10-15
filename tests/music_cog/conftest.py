"""Fixtures for the music cog tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from music_cog.helpers import (
    BOT_USER_ID,
    GUILD_ID,
    REQUESTER_ID,
    EditableChannel,
    FakeChannel,
    FakeLangManager,
    FakeVoiceClient,
    async_noop,
    make_member,
)

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.state_manager import StateManager
from cogs.music_lib.taste_store import TasteStore
from cogs.music_lib.ui_manager import UIManager


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
    guild: SimpleNamespace, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
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
    # Never touch the real data/music/taste.db from a test.
    music._taste_store = TasteStore(tmp_path / "taste.db")
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




@pytest.fixture
def editable_channel() -> EditableChannel:
    return EditableChannel()


@pytest.fixture
def player(
    cog: YTMusic, guild: SimpleNamespace, requester: SimpleNamespace, editable_channel: EditableChannel
) -> PlaybackContext:
    """A context posting into a channel whose messages can be edited, with the real UI manager in the cog."""
    manager = UIManager(bot=None)
    manager.lang_manager = cog.lang_manager
    cog.ui_manager = manager
    return PlaybackContext(guild=guild, channel=editable_channel, user=requester)
