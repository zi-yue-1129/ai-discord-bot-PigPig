"""Tests for what the AI knows about the music player and how failures surface."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

import pytest
from music_cog.helpers import (
    GUILD_ID,
    FakeChannel,
    FakeLangManager,
    FakeVoiceClient,
    make_member,
    make_song,
)

from addons.settings import MusicAISettings, MusicConfig, music_config
from cogs.music import YTMusic
from cogs.music_lib import service as service_module
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.service import FAILURE_REASONS, ActionResult, MusicService
from llm.music_context import build_music_context, render_music_context
from llm.tools.music_tools import MusicTools

LOCALES = ("zh_TW", "zh_CN", "en_US", "ja_JP")


def _status(**overrides: Any) -> dict:
    status = {
        "state": "playing",
        "current": {"title": "稻香", "author": "Jay", "duration": 223, "url": "u"},
        "queue": [
            {"title": f"next {index}", "author": "x", "duration": 100, "url": "v"}
            for index in range(1, 4)
        ],
        "mode": "loop_queue",
        "shuffle": True,
        "autoplay": False,
        "volume": 40,
    }
    status.update(overrides)
    return status


# --- settings ---------------------------------------------------------------------


def test_ai_settings_defaults() -> None:
    settings = MusicAISettings()

    assert settings.status_in_context is True
    assert settings.list_queue_titles is True
    # The info agent's tool results reach the reply agent, which reports failures itself.
    assert settings.announce_failures is False
    assert settings.max_queue_titles == 10
    assert settings.start_confirm_timeout_seconds == pytest.approx(5.0)


def test_music_config_reads_the_ai_block(tmp_path: Path) -> None:
    path = tmp_path / "music.yaml"
    path.write_text("ai:\n  list_queue_titles: false\n  max_queue_titles: 3\n", encoding="utf-8")

    config = MusicConfig(str(path))

    assert config.ai.list_queue_titles is False
    assert config.ai.max_queue_titles == 3
    assert config.ai.announce_failures is False


def test_music_config_rejects_unknown_ai_keys(tmp_path: Path) -> None:
    path = tmp_path / "music.yaml"
    path.write_text("ai:\n  list_queue_title: false\n", encoding="utf-8")

    with pytest.raises(TypeError, match="list_queue_title"):
        MusicConfig(str(path))


# --- context rendering --------------------------------------------------------------


def test_render_lists_the_current_song_the_queue_and_the_settings() -> None:
    text = render_music_context(_status(), list_titles=True, max_titles=10)

    assert "稻香" in text
    assert "1. 'next 1'" in text and "3. 'next 3'" in text
    assert "loop_queue" in text
    assert "40%" in text
    assert "shuffle: on" in text


def test_render_limits_the_listed_titles() -> None:
    text = render_music_context(_status(), list_titles=True, max_titles=2)

    assert "'next 2'" in text
    assert "'next 3'" not in text
    assert "1 more" in text


def test_render_can_hide_the_queue_titles() -> None:
    text = render_music_context(_status(), list_titles=False, max_titles=10)

    assert "稻香" in text
    assert "next 1" not in text
    assert "3 songs" in text


@pytest.mark.asyncio
async def test_build_context_returns_the_rendered_status(cog: YTMusic, voice_client: FakeVoiceClient) -> None:
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1))
    guild = SimpleNamespace(id=GUILD_ID)
    bot = SimpleNamespace(get_cog=lambda name: cog if name == "YTMusic" else None)

    text = await build_music_context(bot, guild, MusicAISettings())

    assert "song 0" in text and "song 1" in text


@pytest.mark.asyncio
async def test_build_context_is_empty_when_disabled(cog: YTMusic, voice_client: FakeVoiceClient) -> None:
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))
    bot = SimpleNamespace(get_cog=lambda name: cog)

    text = await build_music_context(bot, SimpleNamespace(id=GUILD_ID), MusicAISettings(status_in_context=False))

    assert text == ""


@pytest.mark.asyncio
async def test_build_context_is_empty_when_nothing_is_going_on(cog: YTMusic) -> None:
    bot = SimpleNamespace(get_cog=lambda name: cog)

    text = await build_music_context(bot, SimpleNamespace(id=GUILD_ID), MusicAISettings())

    assert text == ""


@pytest.mark.asyncio
async def test_build_context_is_empty_without_the_music_cog_or_a_guild() -> None:
    bot = SimpleNamespace(get_cog=lambda name: None)

    assert await build_music_context(bot, SimpleNamespace(id=GUILD_ID), MusicAISettings()) == ""
    assert await build_music_context(bot, None, MusicAISettings()) == ""


# --- confirming that playback really started --------------------------------------------


@pytest.fixture
def idle_service(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> MusicService:
    """A service whose YouTube lookups succeed instantly."""

    class QuickYouTube:
        async def search_videos(self, query: str, max_results: int = 10) -> List[dict]:
            return [make_song(100)]

        async def download_audio(self, url: str, folder: str, ctx: Any) -> tuple:
            return make_song(101), None

        async def get_video_info_without_download(self, url: str, ctx: Any) -> tuple:
            return make_song(102), None

    monkeypatch.setattr(cog, "youtube", QuickYouTube())
    cog.service.settings = replace(cog.service.settings, start_confirm_timeout_seconds=0.05)
    return cog.service


@pytest.mark.asyncio
async def test_play_fails_when_the_player_never_starts(
    idle_service: MusicService, cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def play_next_that_gives_up(source: Any, force_new: bool = False) -> None:
        return None

    monkeypatch.setattr(cog, "play_next", play_next_that_gives_up)

    result = await idle_service.play(ctx, "稻香")

    assert not result.ok
    assert result.reason == "playback_not_started"


@pytest.mark.asyncio
async def test_play_reports_that_playback_started(
    idle_service: MusicService, cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def play_next_that_plays(source: Any, force_new: bool = False) -> None:
        voice_client.playing = True

    monkeypatch.setattr(cog, "play_next", play_next_that_plays)

    result = await idle_service.play(ctx, "稻香")

    assert result.ok
    assert result.data["started"] is True


@pytest.mark.asyncio
async def test_play_does_not_wait_when_confirmation_is_disabled(
    idle_service: MusicService, cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def play_next_that_gives_up(source: Any, force_new: bool = False) -> None:
        return None

    monkeypatch.setattr(cog, "play_next", play_next_that_gives_up)
    idle_service.settings = replace(idle_service.settings, start_confirm_timeout_seconds=0)

    result = await idle_service.play(ctx, "稻香")

    assert result.ok
    assert result.data["started"] is False


@pytest.mark.asyncio
async def test_a_song_queued_behind_the_current_one_reports_its_position(
    idle_service: MusicService, cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(7))

    result = await idle_service.play(ctx, "稻香")

    assert result.ok
    assert result.data["started"] is False
    assert result.data["position"] == 1


# --- failures become visible in the channel -----------------------------------------------


def _tool_runtime(cog: YTMusic, channel: FakeChannel) -> SimpleNamespace:
    guild = SimpleNamespace(id=GUILD_ID)
    message = SimpleNamespace(guild=guild, channel=channel, author=make_member(42, voice_channel=object()))
    lang = FakeLangManager()
    cogs = {"YTMusic": cog, "LanguageManager": lang}
    return SimpleNamespace(bot=SimpleNamespace(get_cog=cogs.get), message=message, logger=None)


class RefusingService:
    """Service stand-in whose every action fails."""

    async def play(self, ctx: PlaybackContext, query: str) -> ActionResult:
        return ActionResult(ok=False, reason="user_not_in_voice", detail="join first")

    async def skip(self, ctx: PlaybackContext) -> ActionResult:
        return ActionResult(ok=True, data={"skipped": "x"})


@pytest.mark.asyncio
async def test_a_failed_action_is_announced_publicly(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> None:
    channel = FakeChannel()
    monkeypatch.setattr(music_config, "ai", replace(music_config.ai, announce_failures=True))
    monkeypatch.setattr(cog, "service", RefusingService())
    tools = {tool.name: tool for tool in MusicTools(_tool_runtime(cog, channel)).get_tools()}

    reply = await tools["play_music"].ainvoke({"query": "x"})

    assert reply == "Error: join first"
    assert len(channel.sent) == 1
    embed = channel.sent[0].kwargs["embed"]
    assert "ai_errors.user_not_in_voice" in embed.title


@pytest.mark.asyncio
async def test_a_successful_action_is_not_announced(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> None:
    channel = FakeChannel()
    monkeypatch.setattr(cog, "service", RefusingService())
    tools = {tool.name: tool for tool in MusicTools(_tool_runtime(cog, channel)).get_tools()}

    await tools["skip_music"].ainvoke({})

    assert channel.sent == []


@pytest.mark.asyncio
async def test_announcements_can_be_turned_off(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> None:
    channel = FakeChannel()
    monkeypatch.setattr(cog, "service", RefusingService())
    monkeypatch.setattr(music_config, "ai", replace(music_config.ai, announce_failures=False))
    tools = {tool.name: tool for tool in MusicTools(_tool_runtime(cog, channel)).get_tools()}

    reply = await tools["play_music"].ainvoke({"query": "x"})

    assert reply.startswith("Error:")
    assert channel.sent == []


# --- translations cover every failure the service can report ------------------------------


def test_every_failure_reason_the_service_emits_is_declared() -> None:
    source = Path(service_module.__file__).read_text(encoding="utf-8")
    emitted = set(re.findall(r'_fail\(\s*"(\w+)"', source))

    assert emitted <= set(FAILURE_REASONS)
    assert "playback_not_started" in FAILURE_REASONS


@pytest.mark.parametrize("locale", LOCALES)
def test_every_failure_reason_is_translated(locale: str) -> None:
    path = Path("translations") / locale / "system" / "music" / "ai_errors.json"

    texts = json.loads(path.read_text(encoding="utf-8"))

    assert set(FAILURE_REASONS) <= set(texts)
    assert all(texts[reason].strip() for reason in FAILURE_REASONS)
