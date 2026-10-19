"""KTV-style requests: songs play in the order they were requested, with an explicit cut-in."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List, Tuple

import pytest
from music_cog.helpers import (
    BOT_USER_ID,
    GUILD_ID,
    REQUESTER_ID,
    FakeChannel,
    FakeVoiceClient,
    make_song,
)
from music_cog.test_music_tools import FakeService, _runtime, _tools
from music_cog.test_service import FakeYouTube
from music_cog.test_shuffle_and_play_guard import _play_interaction

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext

OTHER_USER = 77


class _UrlYouTube(FakeYouTube):
    """Answers every video lookup with a song named after the last part of the URL."""

    @staticmethod
    def _song(url: str) -> dict:
        video_id = url.rsplit("/", 1)[-1]
        return make_song(0) | {"video_id": video_id, "title": video_id, "url": url, "file_path": None}

    async def get_video_info_without_download(self, url: str, ctx: Any) -> Tuple[dict, None]:
        return self._song(url), None

    async def download_audio(self, url: str, folder: str, ctx: Any) -> Tuple[dict, None]:
        return self._song(url), None


@pytest.fixture
def youtube(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> _UrlYouTube:
    fake = _UrlYouTube()
    monkeypatch.setattr(cog, "youtube", fake)
    return fake


def _order(cog: YTMusic) -> List[str]:
    return [song["video_id"] for song in cog.queue_manager.get_queue_snapshot(GUILD_ID)]


async def _queue(cog: YTMusic, video_id: str, added_by: int) -> None:
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(0) | {"video_id": video_id, "title": video_id, "added_by": added_by})


@pytest.mark.asyncio
async def test_songs_requested_one_after_another_play_in_that_order(
    cog: YTMusic, ctx: PlaybackContext, youtube: _UrlYouTube, voice_client: FakeVoiceClient
) -> None:
    voice_client.playing = True

    for name in ("x", "y", "z"):
        result = await cog.service.play(ctx, f"https://youtu.be/{name}")
        assert result.ok

    assert _order(cog) == ["x", "y", "z"]


@pytest.mark.asyncio
async def test_a_request_goes_after_earlier_requests_but_before_the_bots_recommendations(cog: YTMusic) -> None:
    await _queue(cog, "u1", REQUESTER_ID)
    await _queue(cog, "bot1", BOT_USER_ID)

    await cog.queue_manager.enqueue_request(GUILD_ID, make_song(0) | {"video_id": "u2", "added_by": OTHER_USER})

    assert _order(cog) == ["u1", "u2", "bot1"]


@pytest.mark.asyncio
async def test_a_cut_in_plays_next(cog: YTMusic) -> None:
    await _queue(cog, "u1", REQUESTER_ID)
    await _queue(cog, "bot1", BOT_USER_ID)

    await cog.queue_manager.enqueue_request(
        GUILD_ID, make_song(0) | {"video_id": "cut", "added_by": OTHER_USER}, play_next=True
    )

    assert _order(cog) == ["cut", "u1", "bot1"]


@pytest.mark.asyncio
async def test_requesting_a_recommended_song_turns_it_into_a_request_in_its_place(cog: YTMusic) -> None:
    await _queue(cog, "u1", REQUESTER_ID)
    await _queue(cog, "bot1", BOT_USER_ID)
    await _queue(cog, "bot2", BOT_USER_ID)

    await cog.queue_manager.enqueue_request(GUILD_ID, make_song(0) | {"video_id": "bot2", "added_by": OTHER_USER})

    snapshot = cog.queue_manager.get_queue_snapshot(GUILD_ID)
    assert [song["video_id"] for song in snapshot] == ["u1", "bot2", "bot1"]
    assert snapshot[1]["added_by"] == OTHER_USER


@pytest.mark.asyncio
async def test_requesting_a_song_that_is_already_a_request_changes_nothing(cog: YTMusic) -> None:
    await _queue(cog, "u1", REQUESTER_ID)
    await _queue(cog, "u2", REQUESTER_ID)

    assert await cog.queue_manager.enqueue_request(GUILD_ID, make_song(0) | {"video_id": "u2", "added_by": OTHER_USER})

    assert _order(cog) == ["u1", "u2"]


@pytest.mark.asyncio
async def test_the_service_can_cut_in(
    cog: YTMusic, ctx: PlaybackContext, youtube: _UrlYouTube, voice_client: FakeVoiceClient
) -> None:
    voice_client.playing = True
    await cog.service.play(ctx, "https://youtu.be/first")

    await cog.service.play(ctx, "https://youtu.be/cut", play_next=True)

    assert _order(cog) == ["cut", "first"]


@pytest.mark.asyncio
async def test_the_slash_command_cuts_in_with_the_insert_option(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient,
    requester: SimpleNamespace, youtube: _UrlYouTube,
) -> None:
    voice_client.playing = True
    await _queue(cog, "first", REQUESTER_ID)
    interaction = _play_interaction(guild, text_channel, requester)

    await cog.play.callback(cog, interaction, "https://youtu.be/cut", True)

    assert _order(cog) == ["cut", "first"]


@pytest.mark.asyncio
async def test_the_slash_command_without_the_option_queues_in_order(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient,
    requester: SimpleNamespace, youtube: _UrlYouTube,
) -> None:
    voice_client.playing = True
    await _queue(cog, "first", REQUESTER_ID)
    interaction = _play_interaction(guild, text_channel, requester)

    await cog.play.callback(cog, interaction, "https://youtu.be/second")

    assert _order(cog) == ["first", "second"]


@pytest.mark.asyncio
async def test_the_ai_tool_passes_the_cut_in_request_on() -> None:
    service = FakeService()
    tools = _tools(_runtime(service))

    await tools["play_music"].ainvoke({"query": "怪物", "play_next": True})
    await tools["play_music"].ainvoke({"query": "夜に駆ける"})

    assert [call["play_next"] for call in service.play_calls] == [True, False]


def test_the_ai_is_told_when_to_cut_in() -> None:
    description = _tools(_runtime(FakeService()))["play_music"].description

    assert "play_next" in description
    assert "only" in description
