"""Tests for the building blocks of first-song streaming: settings, stream resolution, audio sources."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest
from discord import AudioSource

from addons.settings import MusicConfig, StreamingSettings
from cogs.music_lib.audio_manager import AudioManager
from cogs.music_lib.youtube import YouTubeManager


def test_streaming_settings_defaults() -> None:
    settings = StreamingSettings()

    assert settings.enabled is True
    assert settings.drop_tolerance_seconds == 10
    assert settings.max_resumes == 2


def test_music_config_reads_the_streaming_block(tmp_path: Path) -> None:
    path = tmp_path / "music.yaml"
    path.write_text("streaming:\n  enabled: false\n  max_resumes: 1\n", encoding="utf-8")

    config = MusicConfig(str(path))

    assert config.streaming.enabled is False
    assert config.streaming.max_resumes == 1
    assert config.streaming.drop_tolerance_seconds == 10


def test_music_config_rejects_unknown_streaming_keys(tmp_path: Path) -> None:
    path = tmp_path / "music.yaml"
    path.write_text("streaming:\n  enable: true\n", encoding="utf-8")

    with pytest.raises(TypeError):
        MusicConfig(str(path))


class _FakeYoutubeDL:
    """Stands in for ``yt_dlp.YoutubeDL``; returns the prepared info."""

    info: Dict[str, Any] = {}

    def __init__(self, opts: Dict[str, Any]) -> None:
        self.opts = opts

    def __enter__(self) -> "_FakeYoutubeDL":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def extract_info(self, url: str, download: bool = False) -> Dict[str, Any]:
        assert download is False
        return dict(self.info)


@pytest.fixture
def manager(monkeypatch: pytest.MonkeyPatch) -> YouTubeManager:
    monkeypatch.setattr("cogs.music_lib.youtube.yt_dlp.YoutubeDL", _FakeYoutubeDL)
    return YouTubeManager(time_limit=1800)


def _ctx() -> SimpleNamespace:
    user = SimpleNamespace(id=7, display_avatar=SimpleNamespace(url="https://cdn/avatar.png"))
    return SimpleNamespace(guild=SimpleNamespace(id=1), user=user)


def _info(**overrides: Any) -> Dict[str, Any]:
    info = {
        "id": "abc", "title": "怪物", "duration": 200, "uploader": "YOASOBI", "view_count": 5,
        "webpage_url": "https://youtube.com/watch?v=abc", "url": "https://rr1.googlevideo.com/audio",
        "http_headers": {"User-Agent": "UA"}, "is_live": False,
    }
    info.update(overrides)
    return info


@pytest.mark.asyncio
async def test_resolve_stream_returns_a_playable_entry_without_downloading(manager: YouTubeManager) -> None:
    _FakeYoutubeDL.info = _info()

    song, error = await manager.resolve_stream("https://youtube.com/watch?v=abc", _ctx())

    assert error is None
    assert song["stream_url"] == "https://rr1.googlevideo.com/audio"
    assert song["stream_headers"] == {"User-Agent": "UA"}
    assert song["title"] == "怪物"
    assert song["duration"] == 200
    assert song["video_id"] == "abc"
    assert song["file_path"] is None
    assert song["is_live"] is False


@pytest.mark.asyncio
async def test_resolve_stream_refuses_videos_over_the_time_limit(manager: YouTubeManager) -> None:
    _FakeYoutubeDL.info = _info(duration=3600)

    song, error = await manager.resolve_stream("https://youtube.com/watch?v=abc", _ctx())

    assert song is None
    assert "30" in str(error)


@pytest.mark.asyncio
async def test_resolve_stream_leaves_live_streams_to_the_download_path(manager: YouTubeManager) -> None:
    _FakeYoutubeDL.info = _info(is_live=True)

    song, error = await manager.resolve_stream("https://youtube.com/watch?v=abc", _ctx())

    assert song is None
    assert error is None


@pytest.mark.asyncio
async def test_resolve_stream_without_a_url_falls_back_to_download(manager: YouTubeManager) -> None:
    _FakeYoutubeDL.info = _info(url=None)

    song, error = await manager.resolve_stream("https://youtube.com/watch?v=abc", _ctx())

    assert song is None
    assert error is None


class _RecordedSource(AudioSource):
    """Captures how ffmpeg would have been started."""

    calls: List[Dict[str, Any]] = []

    def __init__(self, source: str, **kwargs: Any) -> None:
        super().__init__()
        self.calls.append({"source": source, **kwargs})


@pytest.fixture
def audio(monkeypatch: pytest.MonkeyPatch) -> AudioManager:
    _RecordedSource.calls = []
    monkeypatch.setattr("cogs.music_lib.audio_manager.FFmpegPCMAudio", _RecordedSource)
    return AudioManager()


def test_a_song_with_a_local_file_plays_from_the_file_even_if_it_has_a_stream_url(
    audio: AudioManager, tmp_path: Path
) -> None:
    file = tmp_path / "abc.mp3"
    file.write_bytes(b"x")

    audio.create_audio_source({"file_path": str(file), "stream_url": "https://u"})

    assert _RecordedSource.calls[0]["source"] == str(file)


def test_a_song_without_a_file_streams_with_its_headers(audio: AudioManager) -> None:
    song = {"file_path": None, "stream_url": "https://u", "stream_headers": {"User-Agent": "UA"}}

    audio.create_audio_source(song)

    call = _RecordedSource.calls[0]
    assert call["source"] == "https://u"
    assert "-reconnect 1" in call["before_options"]
    assert "User-Agent: UA" in call["before_options"]
    assert call["options"] == "-vn"


def test_a_start_offset_seeks_into_the_local_file(audio: AudioManager, tmp_path: Path) -> None:
    file = tmp_path / "abc.mp3"
    file.write_bytes(b"x")

    audio.create_audio_source({"file_path": str(file)}, start_offset=95.5)

    assert "-ss 95.5" in _RecordedSource.calls[0]["before_options"]


def test_a_song_with_neither_file_nor_stream_is_rejected(audio: AudioManager) -> None:
    with pytest.raises(ValueError, match="neither a local file nor a stream URL"):
        audio.create_audio_source({"file_path": None})
