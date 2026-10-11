"""Tests for volume control and queue management."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

import discord
import pytest
from music_cog.helpers import (
    GUILD_ID,
    FakeChannel,
    FakeVoiceClient,
    make_member,
    make_song,
)

from cogs.music import YTMusic
from cogs.music_lib import audio_manager as audio_manager_module
from cogs.music_lib.audio_manager import AudioManager
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.queue_manager import QueueManager
from cogs.music_lib.service import MusicService


class SilentSource(discord.AudioSource):
    """An audio source producing no audio and spawning no process."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args

    def read(self) -> bytes:
        return b""


@pytest.fixture
def service(cog: YTMusic) -> MusicService:
    return cog.service


# --- QueueManager.remove_at ---------------------------------------------------


@pytest.mark.asyncio
async def test_remove_at_returns_and_removes_the_song_at_that_index() -> None:
    queue_manager = QueueManager(bot=SimpleNamespace(user=SimpleNamespace(id=1)))
    for index in range(3):
        await queue_manager.add_to_queue(GUILD_ID, make_song(index))

    removed = queue_manager.remove_at(GUILD_ID, 1)

    assert removed["title"] == "song 1"
    assert [song["title"] for song in queue_manager.get_queue_snapshot(GUILD_ID)] == ["song 0", "song 2"]


@pytest.mark.asyncio
@pytest.mark.parametrize("index", [-1, 3, 99])
async def test_remove_at_returns_none_for_an_index_outside_the_queue(index: int) -> None:
    queue_manager = QueueManager(bot=SimpleNamespace(user=SimpleNamespace(id=1)))
    for position in range(3):
        await queue_manager.add_to_queue(GUILD_ID, make_song(position))

    assert queue_manager.remove_at(GUILD_ID, index) is None
    assert len(queue_manager.get_queue_snapshot(GUILD_ID)) == 3


# --- volume ---------------------------------------------------------------------


def test_audio_manager_applies_the_requested_volume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(audio_manager_module, "FFmpegPCMAudio", SilentSource)
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"x")

    source = AudioManager().create_audio_source({"file_path": str(audio_file)}, volume=0.25)

    assert isinstance(source, discord.PCMVolumeTransformer)
    assert source.volume == pytest.approx(0.25)


@pytest.mark.asyncio
async def test_set_volume_updates_the_state_and_the_live_source(
    service: MusicService, ctx: PlaybackContext, cog: YTMusic, voice_client: FakeVoiceClient,
) -> None:
    voice_client.source = discord.PCMVolumeTransformer(SilentSource(), volume=1.0)

    result = await service.set_volume(ctx, 40)

    assert result.ok
    assert result.data["volume"] == 40
    assert cog.state_manager.get_state(GUILD_ID).volume == pytest.approx(0.4)
    assert voice_client.source.volume == pytest.approx(0.4)


@pytest.mark.asyncio
@pytest.mark.parametrize("percent", [-1, 101, 1000])
async def test_set_volume_rejects_values_outside_zero_to_one_hundred(
    service: MusicService, ctx: PlaybackContext, cog: YTMusic, percent: int,
) -> None:
    result = await service.set_volume(ctx, percent)

    assert not result.ok
    assert result.reason == "invalid_volume"
    assert cog.state_manager.get_state(GUILD_ID).volume == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_set_volume_is_rejected_for_users_outside_the_bot_channel(
    service: MusicService, guild: SimpleNamespace, text_channel: FakeChannel, cog: YTMusic,
) -> None:
    outsider = PlaybackContext(guild=guild, channel=text_channel, user=make_member(5, voice_channel=object()))

    result = await service.set_volume(outsider, 10)

    assert result.reason == "not_in_bot_channel"
    assert cog.state_manager.get_state(GUILD_ID).volume == pytest.approx(1.0)


# --- queue management --------------------------------------------------------------


async def _queue_songs(cog: YTMusic, count: int, tmp_path: Path) -> List[Path]:
    """Queues ``count`` songs that already have downloaded files."""
    files = []
    for index in range(count):
        path = tmp_path / f"{index}.mp3"
        path.write_bytes(b"audio")
        files.append(path)
        song = make_song(index) | {"file_path": str(path)}
        await cog.queue_manager.add_to_queue(GUILD_ID, song)
    return files


@pytest.mark.asyncio
async def test_remove_from_queue_uses_one_based_positions_and_deletes_the_file(
    service: MusicService, ctx: PlaybackContext, cog: YTMusic, tmp_path: Path,
) -> None:
    files = await _queue_songs(cog, 3, tmp_path)

    result = await service.remove_from_queue(ctx, 2)

    assert result.ok
    assert result.data["title"] == "song 1"
    assert service.queue_titles(GUILD_ID) == ["song 0", "song 2"]
    assert not files[1].exists()
    assert files[0].exists() and files[2].exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("position", [0, -3, 4, 50])
async def test_remove_from_queue_rejects_positions_outside_the_queue(
    service: MusicService, ctx: PlaybackContext, cog: YTMusic, tmp_path: Path, position: int,
) -> None:
    await _queue_songs(cog, 3, tmp_path)

    result = await service.remove_from_queue(ctx, position)

    assert not result.ok
    assert result.reason == "invalid_position"
    assert len(service.queue_titles(GUILD_ID)) == 3


@pytest.mark.asyncio
async def test_clear_queue_empties_the_queue_and_playlist_but_keeps_the_current_song(
    service: MusicService, ctx: PlaybackContext, cog: YTMusic, tmp_path: Path,
    voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    files = await _queue_songs(cog, 3, tmp_path)
    cog.queue_manager.set_playlist(GUILD_ID, [make_song(50), make_song(51)])
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(99))

    result = await service.clear_queue(ctx)

    assert result.ok
    assert result.data["removed"] == 3
    assert service.queue_titles(GUILD_ID) == []
    assert not cog.queue_manager.has_playlist_songs(GUILD_ID)
    assert cog.state_manager.get_state(GUILD_ID).current_song["title"] == "song 99"
    assert not any(path.exists() for path in files)
    assert voice_client.stop_calls == 0


@pytest.mark.asyncio
async def test_queue_changes_are_rejected_for_users_outside_the_bot_channel(
    service: MusicService, guild: SimpleNamespace, text_channel: FakeChannel, cog: YTMusic,
    tmp_path: Path,
) -> None:
    await _queue_songs(cog, 2, tmp_path)
    outsider = PlaybackContext(guild=guild, channel=text_channel, user=make_member(5, voice_channel=object()))

    removed = await service.remove_from_queue(outsider, 1)
    cleared = await service.clear_queue(outsider)

    assert removed.reason == cleared.reason == "not_in_bot_channel"
    assert len(service.queue_titles(GUILD_ID)) == 2
