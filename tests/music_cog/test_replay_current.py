"""A request for the song that is already playing is not queued again; the autoplay toggle names the user."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Tuple

import pytest
from music_cog.helpers import GUILD_ID, FakeChannel, FakeVoiceClient, make_interaction, make_song
from music_cog.test_service import FakeYouTube

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.sources import extract_youtube_id

PLAYING = "playing1"
OTHER = "other1"
ROOT = Path(__file__).resolve().parents[2]


def _song(video_id: str) -> dict:
    return make_song(0) | {
        "video_id": video_id,
        "title": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "file_path": None,
    }


class _Youtube(FakeYouTube):
    """Resolves every lookup to the song named by the ``v=`` part of the URL."""

    def __init__(self) -> None:
        super().__init__()
        self.lookups: List[str] = []

    def _resolve(self, url: str) -> Tuple[dict, None]:
        self.lookups.append(url)
        return _song(url.rsplit("v=", 1)[-1].rsplit("/", 1)[-1]), None

    async def get_video_info_without_download(self, url: str, ctx: Any) -> Tuple[dict, None]:
        return self._resolve(url)

    async def download_audio(self, url: str, folder: str, ctx: Any) -> Tuple[dict, None]:
        return self._resolve(url)


@pytest.fixture
def youtube(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> _Youtube:
    fake = _Youtube()
    monkeypatch.setattr(cog, "youtube", fake)
    return fake


def _start_playing(cog: YTMusic, voice_client: FakeVoiceClient, *, paused: bool = False) -> None:
    voice_client.playing = not paused
    voice_client.paused = paused
    cog.state_manager.update_state(GUILD_ID, current_song=_song(PLAYING))


def _queued(cog: YTMusic) -> List[str]:
    return [song["video_id"] for song in cog.queue_manager.get_queue_snapshot(GUILD_ID)]


# ------------------------------------------------------------- url -> id


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={PLAYING}",
        f"https://youtube.com/watch?v={PLAYING}&t=30s",
        f"https://music.youtube.com/watch?v={PLAYING}",
        f"https://youtu.be/{PLAYING}",
        f"https://youtu.be/{PLAYING}?si=abc",
        f"https://www.youtube.com/shorts/{PLAYING}",
        f"youtube.com/watch?v={PLAYING}",
    ],
)
def test_the_video_id_is_read_from_every_youtube_link_form(url: str) -> None:
    assert extract_youtube_id(url) == PLAYING


@pytest.mark.parametrize(
    "url", ["https://soundcloud.com/artist/track", "https://example.com/watch?v=abc", "just some words", ""]
)
def test_other_text_has_no_youtube_id(url: str) -> None:
    assert extract_youtube_id(url) is None


# ----------------------------------------------------------- the request


@pytest.mark.asyncio
async def test_a_search_whose_top_hit_is_the_playing_song_queues_the_next_hit(
    cog: YTMusic, ctx: PlaybackContext, youtube: _Youtube, voice_client: FakeVoiceClient
) -> None:
    _start_playing(cog, voice_client)
    youtube.search_results = [_song(PLAYING), _song(OTHER)]

    result = await cog.service.play(ctx, "some song by the same artist")

    assert result.ok
    assert result.data["title"] == OTHER
    assert _queued(cog) == [OTHER]
    assert youtube.lookups == [f"https://youtube.com/watch?v={OTHER}"]


@pytest.mark.asyncio
async def test_a_search_with_only_the_playing_song_is_refused(
    cog: YTMusic, ctx: PlaybackContext, youtube: _Youtube, voice_client: FakeVoiceClient
) -> None:
    _start_playing(cog, voice_client)
    youtube.search_results = [_song(PLAYING)]

    result = await cog.service.play(ctx, "the song that is playing")

    assert not result.ok
    assert result.reason == "already_playing"
    assert _queued(cog) == []
    assert youtube.lookups == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [f"https://www.youtube.com/watch?v={PLAYING}", f"https://youtu.be/{PLAYING}"],
)
async def test_a_link_to_the_playing_song_is_refused(
    cog: YTMusic, ctx: PlaybackContext, youtube: _Youtube, voice_client: FakeVoiceClient, url: str
) -> None:
    _start_playing(cog, voice_client)

    result = await cog.service.play(ctx, url)

    assert not result.ok
    assert result.reason == "already_playing"
    assert _queued(cog) == []
    assert youtube.lookups == []


@pytest.mark.asyncio
async def test_a_paused_song_still_counts_as_playing(
    cog: YTMusic, ctx: PlaybackContext, youtube: _Youtube, voice_client: FakeVoiceClient
) -> None:
    _start_playing(cog, voice_client, paused=True)

    result = await cog.service.play(ctx, f"https://youtu.be/{PLAYING}")

    assert result.reason == "already_playing"


@pytest.mark.asyncio
async def test_a_song_that_is_not_playing_any_more_can_be_requested_again(
    cog: YTMusic, ctx: PlaybackContext, youtube: _Youtube, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _start_playing(cog, voice_client)
    voice_client.playing = False

    async def no_play_next(source: Any, force_new: bool = False) -> None:
        return None

    monkeypatch.setattr(cog, "play_next", no_play_next)

    result = await cog.service.play(ctx, f"https://youtu.be/{PLAYING}")

    assert result.reason != "already_playing"


@pytest.mark.asyncio
async def test_a_different_song_is_still_queued_behind_the_playing_one(
    cog: YTMusic, ctx: PlaybackContext, youtube: _Youtube, voice_client: FakeVoiceClient
) -> None:
    _start_playing(cog, voice_client)

    result = await cog.service.play(ctx, f"https://youtu.be/{OTHER}")

    assert result.ok
    assert _queued(cog) == [OTHER]


@pytest.mark.parametrize("locale", ("zh_TW", "zh_CN", "en_US", "ja_JP"))
def test_the_refusal_is_translated(locale: str) -> None:
    path = ROOT / "translations" / locale / "system" / "music" / "ai_errors.json"

    assert json.loads(path.read_text(encoding="utf-8"))["already_playing"].strip()


# ------------------------------------------------------- autoplay toggle


class _FormattingLanguages:
    """Fills ``{placeholders}`` of the real zh_TW texts, failing like Python does when one is missing."""

    def translate(self, guild_id: str, *path: str, **kwargs: Any) -> str:
        file = ROOT / "translations" / "zh_TW" / path[0] / path[1] / f"{path[2]}.json"
        data: Any = json.loads(file.read_text(encoding="utf-8"))
        for key in path[3:]:
            data = data[key]
        return data.format(**kwargs)


@pytest.mark.asyncio
async def test_the_autoplay_toggle_message_names_who_toggled_it(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, requester: SimpleNamespace
) -> None:
    cog.lang_manager = _FormattingLanguages()
    cog.state_manager.update_state(GUILD_ID, autoplay=True)
    interaction = make_interaction(guild, text_channel, requester)

    await cog.handle_toggle_autoplay(interaction)

    (sent,) = interaction.response.sent
    assert "{" not in sent["args"][0]
    assert requester.name in sent["args"][0]
