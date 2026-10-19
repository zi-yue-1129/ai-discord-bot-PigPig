"""Playback sources beyond YouTube: SoundCloud links, Spotify track links and the host allow-list."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest
from music_cog.helpers import make_song
from music_cog.test_service import FakeYouTube

from addons.settings import MusicConfig, SourcesSettings
from cogs.music import YTMusic
from cogs.music_lib import sources
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.service import classify_query
from cogs.music_lib.sources import (
    classify_url,
    fetch_spotify_search_query,
    is_preview_only,
    parse_spotify_page,
    thumbnail_of,
)
from cogs.music_lib.ui_manager import UIManager
from cogs.music_lib.youtube import YouTubeManager

ALLOWED = ("youtube.com", "youtu.be", "soundcloud.com")
SPOTIFY_TRACK = "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"


def _classify(query: str, allowed: tuple = ALLOWED, spotify: bool = True) -> str:
    return classify_url(query, allowed_hosts=allowed, spotify_enabled=spotify)


# ------------------------------------------------------------------ settings


def test_sources_settings_defaults() -> None:
    settings = SourcesSettings()

    assert settings.allowed_hosts == ("youtube.com", "youtu.be", "soundcloud.com")
    assert settings.spotify is True
    assert settings.spotify_timeout_seconds == 10


def test_music_config_reads_the_sources_block(tmp_path: Path) -> None:
    path = tmp_path / "music.yaml"
    path.write_text("sources:\n  allowed_hosts: [youtube.com]\n  spotify: false\n", encoding="utf-8")

    config = MusicConfig(str(path))

    assert config.sources.allowed_hosts == ("youtube.com",)
    assert config.sources.spotify is False


def test_music_config_rejects_unknown_sources_keys(tmp_path: Path) -> None:
    path = tmp_path / "music.yaml"
    path.write_text("sources:\n  allowed_host: [youtube.com]\n", encoding="utf-8")

    with pytest.raises(TypeError):
        MusicConfig(str(path))


# ------------------------------------------------------------- classification


def test_youtube_links_keep_their_kinds() -> None:
    assert _classify("https://www.youtube.com/watch?v=abc") == "video"
    assert _classify("https://youtu.be/abc") == "video"
    assert _classify("https://www.youtube.com/playlist?list=PL1") == "playlist"


@pytest.mark.parametrize(
    "link",
    [
        "https://soundcloud.com/yoasobimusic/idol",
        "https://m.soundcloud.com/yoasobimusic/idol?si=abc",
        "soundcloud.com/yoasobimusic/idol",
        "https://on.soundcloud.com/AbCdEf",
    ],
)
def test_soundcloud_track_links_are_videos(link: str) -> None:
    assert _classify(link) == "video"


def test_soundcloud_sets_are_playlists() -> None:
    assert _classify("https://soundcloud.com/yoasobimusic/sets/the-book") == "playlist"


@pytest.mark.parametrize(
    "link",
    [
        "https://soundcloud.com/yoasobimusic",
        "https://soundcloud.com/yoasobimusic/likes",
        "https://soundcloud.com/yoasobimusic/tracks",
        "https://soundcloud.com/discover",
    ],
)
def test_soundcloud_profiles_and_pages_are_not_played(link: str) -> None:
    assert _classify(link) == "search"


@pytest.mark.parametrize(
    "link",
    [
        "https://soundcloud.com.evil.example/user/track",
        "https://evilsoundcloud.com/user/track",
        "http://169.254.169.254/latest/meta-data",
        "http://localhost:8080/user/track",
        "https://example.com/not-music",
    ],
)
def test_hosts_outside_the_allow_list_are_never_played(link: str) -> None:
    assert _classify(link) == "search"


def test_a_host_removed_from_the_allow_list_is_not_played() -> None:
    assert _classify("https://soundcloud.com/a/b", allowed=("youtube.com", "youtu.be")) == "search"


def test_plain_words_are_searches() -> None:
    assert _classify("soundcloud") == "search"
    assert _classify("周杰倫 稻香") == "search"


@pytest.mark.parametrize(
    "link",
    [SPOTIFY_TRACK, SPOTIFY_TRACK + "?si=abc123", "https://open.spotify.com/intl-ja/track/4cOdK2wGLETKBW3PvgPWqT"],
)
def test_spotify_track_links_are_recognized(link: str) -> None:
    assert _classify(link) == "spotify"


@pytest.mark.parametrize(
    "link",
    ["https://open.spotify.com/album/4cOdK2wGLETKBW3PvgPWqT", "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"],
)
def test_other_spotify_links_are_reported_as_unsupported(link: str) -> None:
    assert _classify(link) == "spotify_unsupported"


def test_spotify_links_are_plain_searches_when_spotify_is_off() -> None:
    assert _classify(SPOTIFY_TRACK, spotify=False) == "search"


def test_spotify_look_alike_hosts_are_not_trusted() -> None:
    assert _classify("https://open.spotify.com.evil.example/track/4cOdK2wGLETKBW3PvgPWqT") == "search"


def test_the_service_classifier_uses_the_configured_sources() -> None:
    assert classify_query("https://soundcloud.com/yoasobimusic/idol") == "video"
    assert classify_query(SPOTIFY_TRACK) == "spotify"


# ------------------------------------------------------------------- Spotify

PAGE = (
    '<html><head><title>Never Gonna Give You Up - song and lyrics by Rick Astley | Spotify</title>'
    '<meta property="og:title" content="Never Gonna Give You Up"/>'
    '<meta property="og:description" content="Rick Astley · Whenever You Need Somebody · Song · 1987"/></head></html>'
)


def test_the_artist_and_title_are_read_from_the_page() -> None:
    assert parse_spotify_page(PAGE) == "Rick Astley Never Gonna Give You Up"


def test_html_entities_in_the_page_are_decoded() -> None:
    page = PAGE.replace("Never Gonna Give You Up\"/>", "Rock &amp; Roll\"/>", 1).replace("Rick Astley", "Guns &amp; Roses")

    assert parse_spotify_page(page) == "Guns & Roses Rock & Roll"


def test_a_page_without_song_information_gives_nothing() -> None:
    assert parse_spotify_page("<html><head><title>Spotify</title></head></html>") is None


@pytest.mark.asyncio
async def test_only_the_canonical_track_page_is_fetched(monkeypatch: pytest.MonkeyPatch) -> None:
    requested: List[str] = []

    def fake_get(url: str, timeout: float) -> str:
        requested.append(url)
        return PAGE

    monkeypatch.setattr(sources, "_http_get", fake_get)

    query = await fetch_spotify_search_query(
        "https://open.spotify.com/intl-ja/track/4cOdK2wGLETKBW3PvgPWqT?si=x&redirect=http://evil.example", timeout=5
    )

    assert query == "Rick Astley Never Gonna Give You Up"
    assert requested == ["https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"]


@pytest.mark.asyncio
async def test_an_unreachable_spotify_page_gives_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_get(url: str, timeout: float) -> str:
        raise OSError("offline")

    monkeypatch.setattr(sources, "_http_get", failing_get)

    assert await fetch_spotify_search_query(SPOTIFY_TRACK, timeout=5) is None


@pytest.mark.asyncio
async def test_a_link_that_is_not_a_track_is_never_fetched(monkeypatch: pytest.MonkeyPatch) -> None:
    def must_not_run(url: str, timeout: float) -> str:
        raise AssertionError("no request may be made")

    monkeypatch.setattr(sources, "_http_get", must_not_run)

    assert await fetch_spotify_search_query("https://open.spotify.com/album/4cOdK2wGLETKBW3PvgPWqT", timeout=5) is None


# ------------------------------------------------------------ service wiring


@pytest.fixture
def youtube(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> FakeYouTube:
    fake = FakeYouTube()
    monkeypatch.setattr(cog, "youtube", fake)
    return fake


@pytest.fixture
def spotify_page(monkeypatch: pytest.MonkeyPatch) -> List[str]:
    requested: List[str] = []

    def fake_get(url: str, timeout: float) -> str:
        requested.append(url)
        return PAGE

    monkeypatch.setattr(sources, "_http_get", fake_get)
    return requested


@pytest.mark.asyncio
async def test_a_spotify_track_becomes_a_search_text(cog: YTMusic, spotify_page: List[str]) -> None:
    query, failure = await cog.service.resolve_query(SPOTIFY_TRACK)

    assert (query, failure) == ("Rick Astley Never Gonna Give You Up", None)


@pytest.mark.asyncio
async def test_ordinary_queries_pass_through_untouched(cog: YTMusic, spotify_page: List[str]) -> None:
    assert await cog.service.resolve_query("周杰倫 稻香") == ("周杰倫 稻香", None)
    assert await cog.service.resolve_query("https://soundcloud.com/a/b") == ("https://soundcloud.com/a/b", None)
    assert spotify_page == []


@pytest.mark.asyncio
async def test_an_unreadable_spotify_link_is_a_lookup_failure(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_get(url: str, timeout: float) -> str:
        raise OSError("offline")

    monkeypatch.setattr(sources, "_http_get", failing_get)

    query, failure = await cog.service.resolve_query(SPOTIFY_TRACK)

    assert query == ""
    assert failure is not None and failure.reason == "lookup_failed" and "Spotify" in failure.detail


@pytest.mark.asyncio
async def test_a_spotify_album_is_refused_with_an_explanation(cog: YTMusic) -> None:
    query, failure = await cog.service.resolve_query("https://open.spotify.com/album/4cOdK2wGLETKBW3PvgPWqT")

    assert failure is not None and failure.reason == "lookup_failed" and "track" in failure.detail


@pytest.mark.asyncio
async def test_playing_a_spotify_track_searches_for_its_artist_and_title(
    cog: YTMusic, youtube: FakeYouTube, spotify_page: List[str], ctx: PlaybackContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    searched: List[str] = []
    original = youtube.search_videos

    async def spy(query: str, max_results: int = 10) -> List[dict]:
        searched.append(query)
        return await original(query, max_results)

    async def fake_play_next(source: Any, force_new: bool = False) -> None:
        PlaybackContext.coerce(source).guild.voice_client.playing = True

    monkeypatch.setattr(youtube, "search_videos", spy)
    monkeypatch.setattr(cog, "play_next", fake_play_next)

    result = await cog.service.play(ctx, SPOTIFY_TRACK)

    assert result.ok
    assert searched == ["Rick Astley Never Gonna Give You Up"]


# --------------------------------------------------- previews and thumbnails


def test_a_track_with_only_preview_formats_is_detected() -> None:
    info = {"formats": [{"format_id": "hls_mp3_1_0_preview"}, {"format_id": "http_mp3_1_0_preview"}]}

    assert is_preview_only(info) is True


def test_a_track_with_a_full_format_is_not_a_preview() -> None:
    info = {"formats": [{"format_id": "http_mp3_1_0_preview"}, {"format_id": "hls_opus_0_0"}]}

    assert is_preview_only(info) is False


def test_info_without_formats_is_not_a_preview() -> None:
    assert is_preview_only({}) is False
    assert is_preview_only({"formats": []}) is False


def test_soundcloud_keeps_its_own_artwork_but_youtube_does_not() -> None:
    artwork = "https://i1.sndcdn.com/artworks-x-original.jpg"

    assert thumbnail_of({"extractor_key": "Soundcloud", "thumbnail": artwork}) == artwork
    assert thumbnail_of({"extractor_key": "Youtube", "thumbnail": "https://i.ytimg.com/vi/x/maxres.jpg"}) is None
    assert thumbnail_of({"extractor_key": "Soundcloud"}) is None


def test_the_player_embed_shows_the_songs_own_thumbnail() -> None:
    song = make_song(1) | {"thumbnail": "https://i1.sndcdn.com/artworks-x-original.jpg", "is_live": False,
                           "requester": SimpleNamespace(name="u"), "user_avatar": "https://x/a.png"}
    youtube = SimpleNamespace(get_thumbnail_url=lambda video_id: "https://img.youtube.com/never-used.jpg")
    manager = SimpleNamespace(_get_fallback_text=lambda key, **kwargs: key)

    embed = UIManager._create_player_embed(manager, song, youtube)

    assert embed.thumbnail.url == "https://i1.sndcdn.com/artworks-x-original.jpg"


def test_the_player_embed_falls_back_to_the_youtube_thumbnail() -> None:
    song = make_song(1) | {"is_live": False, "requester": SimpleNamespace(name="u"), "user_avatar": "https://x/a.png"}
    youtube = SimpleNamespace(get_thumbnail_url=lambda video_id: f"https://img.youtube.com/{video_id}.jpg")
    manager = SimpleNamespace(_get_fallback_text=lambda key, **kwargs: key)

    embed = UIManager._create_player_embed(manager, song, youtube)

    assert embed.thumbnail.url == "https://img.youtube.com/v1.jpg"


# ----------------------------------------------- the YouTubeManager lookups


class _FakeDL:
    """yt-dlp stand-in that serves one canned info dict and records downloads."""

    info: Dict[str, Any] = {}
    downloads: List[str] = []

    def __init__(self, opts: Dict[str, Any]) -> None:
        self.opts = opts

    def __enter__(self) -> "_FakeDL":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def extract_info(self, url: str, download: bool = False) -> Dict[str, Any]:
        return dict(type(self).info)

    def download(self, urls: List[str]) -> None:
        type(self).downloads.extend(urls)


PREVIEW_INFO = {
    "id": "1480684741", "title": "アイドル", "uploader": "YOASOBI", "duration": 30.0, "url": "https://cf-preview/x.mp3",
    "webpage_url": "https://soundcloud.com/yoasobimusic/idol", "extractor_key": "Soundcloud",
    "thumbnail": "https://i1.sndcdn.com/artworks.jpg", "formats": [{"format_id": "http_mp3_1_0_preview"}],
}
FULL_INFO = PREVIEW_INFO | {"duration": 250.0, "url": "https://cf-media/x.mp3", "formats": [{"format_id": "http_mp3_0_0"}]}


@pytest.fixture
def manager(monkeypatch: pytest.MonkeyPatch) -> YouTubeManager:
    _FakeDL.downloads = []
    monkeypatch.setattr("cogs.music_lib.youtube.yt_dlp.YoutubeDL", _FakeDL)
    youtube = YouTubeManager()
    youtube.settings = SimpleNamespace(youtube_cookies_path="/nonexistent/cookies.txt")
    return youtube


def _lookup_context() -> SimpleNamespace:
    user = SimpleNamespace(id=1, display_avatar=SimpleNamespace(url="x"))
    return SimpleNamespace(guild=SimpleNamespace(id=1), user=user)


@pytest.mark.asyncio
async def test_a_preview_only_track_is_refused_when_streaming(manager: YouTubeManager) -> None:
    _FakeDL.info = PREVIEW_INFO

    song, error = await manager.resolve_stream("https://soundcloud.com/yoasobimusic/idol", _lookup_context())

    assert song is None and error is not None and "30" in error


@pytest.mark.asyncio
async def test_a_full_soundcloud_track_streams_with_its_artwork(manager: YouTubeManager) -> None:
    _FakeDL.info = FULL_INFO

    song, error = await manager.resolve_stream("https://soundcloud.com/yoasobimusic/idol", _lookup_context())

    assert error is None
    assert (song["title"], song["author"], song["duration"]) == ("アイドル", "YOASOBI", 250.0)
    assert song["thumbnail"] == "https://i1.sndcdn.com/artworks.jpg"
    assert song["stream_url"] == "https://cf-media/x.mp3"


@pytest.mark.asyncio
async def test_a_preview_only_track_is_refused_when_queued_behind_others(manager: YouTubeManager) -> None:
    _FakeDL.info = PREVIEW_INFO

    song, error = await manager.get_video_info_without_download("https://soundcloud.com/yoasobimusic/idol", _lookup_context())

    assert song is None and error is not None and "30" in error


@pytest.mark.asyncio
async def test_a_preview_only_track_is_never_downloaded(manager: YouTubeManager, tmp_path: Path) -> None:
    _FakeDL.info = PREVIEW_INFO

    song, error = await asyncio.wait_for(
        manager.download_audio("https://soundcloud.com/yoasobimusic/idol", str(tmp_path), _lookup_context()), timeout=10
    )

    assert song is None and error is not None and "30" in error
    assert _FakeDL.downloads == []


@pytest.mark.asyncio
async def test_youtube_results_carry_no_thumbnail_of_their_own(manager: YouTubeManager) -> None:
    _FakeDL.info = FULL_INFO | {"extractor_key": "Youtube", "id": "abc", "thumbnail": "https://i.ytimg.com/vi/abc/maxres.jpg"}

    song, _ = await manager.resolve_stream("https://www.youtube.com/watch?v=abc", _lookup_context())

    assert song["thumbnail"] is None
