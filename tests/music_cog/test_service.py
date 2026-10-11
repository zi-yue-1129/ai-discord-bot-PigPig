"""Tests for the interaction-free music service used by commands and the AI tools."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List, Optional

import pytest
from music_cog.helpers import (
    GUILD_ID,
    FakeChannel,
    FakeVoiceClient,
    make_member,
    make_song,
)

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.queue_manager import PlayMode
from cogs.music_lib.service import MusicService, classify_query


class FakeYouTube:
    """YouTube manager stand-in that never touches the network."""

    def __init__(self) -> None:
        self.time_limit = 1800
        self.search_results: List[dict] = [make_song(100), make_song(101)]
        self.playlist: List[dict] = [make_song(200 + i) for i in range(8)]
        self.error: Optional[str] = None
        self.downloaded: List[str] = []
        self.stream_song: Optional[dict] = None
        self.stream_error: Optional[str] = None
        self.resolved: List[str] = []

    async def search_videos(self, query: str, max_results: int = 10) -> List[dict]:
        return self.search_results

    async def resolve_stream(self, url: str, ctx: Any) -> tuple:
        self.resolved.append(url)
        return self.stream_song, self.stream_error

    async def download_audio(self, url: str, folder: str, ctx: Any) -> tuple:
        self.downloaded.append(url)
        if self.error:
            return None, self.error
        return make_song(901) | {"url": url, "title": "downloaded"}, None

    async def get_video_info_without_download(self, url: str, ctx: Any) -> tuple:
        if self.error:
            return None, self.error
        return make_song(900) | {"url": url, "title": "queued"}, None

    async def download_playlist(self, url: str, folder: str, ctx: Any) -> tuple:
        if self.error:
            return None, self.error
        return list(self.playlist), None


@pytest.fixture
def youtube(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> FakeYouTube:
    fake = FakeYouTube()
    monkeypatch.setattr(cog, "youtube", fake)
    return fake


@pytest.fixture
def played(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> List[PlaybackContext]:
    """Records play_next calls and pretends playback started, without real audio."""
    calls: List[PlaybackContext] = []

    async def fake_play_next(source: Any, force_new: bool = False) -> None:
        context = PlaybackContext.coerce(source)
        calls.append(context)
        # A real play_next leaves the voice client playing; play() now checks for that.
        context.guild.voice_client.playing = True

    monkeypatch.setattr(cog, "play_next", fake_play_next)
    return calls


@pytest.fixture
def service(cog: YTMusic) -> MusicService:
    return cog.service


def test_classify_query_detects_playlists_videos_and_searches() -> None:
    assert classify_query("https://www.youtube.com/playlist?list=PL123") == "playlist"
    assert classify_query("https://www.youtube.com/watch?v=abc&list=PL123") == "playlist"
    assert classify_query("https://www.youtube.com/watch?v=abc") == "video"
    assert classify_query("https://youtu.be/abc") == "video"
    assert classify_query("周杰倫 稻香") == "search"
    assert classify_query("playlist of chill songs") == "search"
    assert classify_query("https://example.com/not-youtube") == "search"


@pytest.mark.asyncio
async def test_play_requires_the_user_to_be_in_a_voice_channel(
    service: MusicService, guild: SimpleNamespace, text_channel: FakeChannel,
    youtube: FakeYouTube, played: List[PlaybackContext],
) -> None:
    lurker = make_member(5, voice_channel=None)
    ctx = PlaybackContext(guild=guild, channel=text_channel, user=lurker)

    result = await service.play(ctx, "some song")

    assert not result.ok
    assert result.reason == "user_not_in_voice"
    assert played == []
    assert service.queue_titles(GUILD_ID) == []


@pytest.mark.asyncio
async def test_play_rejects_users_in_a_different_channel_while_the_bot_is_busy(
    service: MusicService, guild: SimpleNamespace, text_channel: FakeChannel,
    youtube: FakeYouTube, played: List[PlaybackContext], voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    elsewhere = make_member(5, voice_channel=object())
    ctx = PlaybackContext(guild=guild, channel=text_channel, user=elsewhere)

    result = await service.play(ctx, "some song")

    assert not result.ok
    assert result.reason == "not_in_bot_channel"
    assert played == []


@pytest.mark.asyncio
async def test_play_moves_an_idle_bot_to_the_users_channel(
    service: MusicService, guild: SimpleNamespace, text_channel: FakeChannel,
    youtube: FakeYouTube, played: List[PlaybackContext], voice_client: FakeVoiceClient,
) -> None:
    new_channel = object()
    member = make_member(5, voice_channel=new_channel)
    ctx = PlaybackContext(guild=guild, channel=text_channel, user=member)

    result = await service.play(ctx, "some song")

    assert result.ok
    assert voice_client.moved_to is new_channel
    assert len(played) == 1


@pytest.mark.asyncio
async def test_play_connects_to_the_users_channel_when_the_bot_is_idle(
    service: MusicService, text_channel: FakeChannel, youtube: FakeYouTube,
    played: List[PlaybackContext], voice_channel: object,
) -> None:
    connected: List[FakeVoiceClient] = []
    guild = SimpleNamespace(id=GUILD_ID, name="g", voice_client=None)

    async def connect() -> FakeVoiceClient:
        client = FakeVoiceClient(voice_channel)
        guild.voice_client = client
        connected.append(client)
        return client

    user_channel = SimpleNamespace(connect=connect)
    member = make_member(5, voice_channel=user_channel)
    ctx = PlaybackContext(guild=guild, channel=text_channel, user=member)

    result = await service.play(ctx, "some song")

    assert result.ok
    assert len(connected) == 1
    assert len(played) == 1


@pytest.mark.asyncio
async def test_play_search_queues_the_top_result_and_starts_playback(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext],
) -> None:
    result = await service.play(ctx, "稻香")

    assert result.ok
    assert result.data["title"] == "downloaded"
    assert youtube.downloaded == [youtube.search_results[0]["url"]]
    assert len(played) == 1


@pytest.mark.asyncio
async def test_play_does_not_restart_playback_when_something_is_already_playing(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext], voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True

    result = await service.play(ctx, "稻香")

    assert result.ok
    assert played == []
    assert len(service.queue_titles(GUILD_ID)) == 1


@pytest.mark.asyncio
async def test_play_with_no_search_results_reports_not_found(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext],
) -> None:
    youtube.search_results = []

    result = await service.play(ctx, "zzzz nothing")

    assert not result.ok
    assert result.reason == "no_results"
    assert played == []


@pytest.mark.asyncio
async def test_play_reports_a_download_error(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext],
) -> None:
    youtube.error = "HTTP 403"

    result = await service.play(ctx, "https://youtu.be/abc")

    assert not result.ok
    assert result.reason == "lookup_failed"
    assert "HTTP 403" in result.detail
    assert played == []


@pytest.mark.asyncio
async def test_play_playlist_queues_the_first_five_and_keeps_the_rest(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext], cog: YTMusic,
) -> None:
    result = await service.play(ctx, "https://www.youtube.com/playlist?list=PL1")

    assert result.ok
    assert result.data["added"] == 5
    assert result.data["total"] == 8
    assert cog.queue_manager.has_playlist_songs(GUILD_ID)
    assert len(played) == 1


@pytest.mark.asyncio
async def test_play_reports_a_full_queue(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext], cog: YTMusic, voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    for index in range(cog.queue_manager.MAX_QUEUE_SIZE):
        await cog.queue_manager.add_to_queue(GUILD_ID, make_song(index, added_by=9))

    result = await service.play(ctx, "https://youtu.be/new")

    assert not result.ok
    assert result.reason == "queue_full"


@pytest.mark.asyncio
async def test_skip_stops_the_current_song(
    service: MusicService, ctx: PlaybackContext, voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True

    result = await service.skip(ctx)

    assert result.ok
    assert voice_client.stop_calls == 1


@pytest.mark.asyncio
async def test_skip_with_nothing_playing_is_reported(
    service: MusicService, ctx: PlaybackContext, voice_client: FakeVoiceClient,
) -> None:
    result = await service.skip(ctx)

    assert not result.ok
    assert result.reason == "nothing_playing"
    assert voice_client.stop_calls == 0


@pytest.mark.asyncio
async def test_controls_are_rejected_for_users_outside_the_bot_channel(
    service: MusicService, guild: SimpleNamespace, text_channel: FakeChannel,
    voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    outsider = PlaybackContext(
        guild=guild, channel=text_channel, user=make_member(5, voice_channel=object())
    )

    for action in (service.skip, service.pause, service.stop):
        result = await action(outsider)
        assert not result.ok
        assert result.reason == "not_in_bot_channel"

    assert voice_client.stop_calls == 0
    assert voice_client.pause_calls == 0
    assert not voice_client.disconnected


@pytest.mark.asyncio
async def test_pause_then_resume(
    service: MusicService, ctx: PlaybackContext, voice_client: FakeVoiceClient,
    monkeypatch: pytest.MonkeyPatch, cog: YTMusic,
) -> None:
    async def no_timer(guild_id: int) -> None:
        return None

    monkeypatch.setattr(cog, "_start_disconnect_timer", no_timer)
    voice_client.playing = True

    paused = await service.pause(ctx)
    resumed = await service.resume(ctx)

    assert paused.ok and resumed.ok
    assert voice_client.pause_calls == 1
    assert voice_client.resume_calls == 1
    assert voice_client.paused is False


@pytest.mark.asyncio
async def test_stop_disconnects_and_clears_the_queue(
    service: MusicService, ctx: PlaybackContext, voice_client: FakeVoiceClient,
    cog: YTMusic,
) -> None:
    voice_client.playing = True
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1))

    result = await service.stop(ctx)

    assert result.ok
    assert voice_client.disconnected
    assert service.queue_titles(GUILD_ID) == []


@pytest.mark.asyncio
async def test_set_mode_and_shuffle_update_the_queue_settings(
    service: MusicService, ctx: PlaybackContext, cog: YTMusic,
) -> None:
    mode_result = await service.set_mode(ctx, "loop_queue")
    shuffle_result = await service.set_shuffle(ctx, True)

    assert mode_result.ok and shuffle_result.ok
    assert cog.queue_manager.get_play_mode(GUILD_ID) == PlayMode.LOOP_QUEUE
    assert cog.queue_manager.is_shuffle_enabled(GUILD_ID) is True


@pytest.mark.asyncio
async def test_set_mode_rejects_unknown_modes(
    service: MusicService, ctx: PlaybackContext,
) -> None:
    result = await service.set_mode(ctx, "party")

    assert not result.ok
    assert result.reason == "invalid_mode"


@pytest.mark.asyncio
async def test_status_describes_the_current_song_and_queue(
    service: MusicService, cog: YTMusic, voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1))
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(2))

    status = service.status(GUILD_ID)

    assert status["state"] == "playing"
    assert status["current"]["title"] == "song 0"
    assert [song["title"] for song in status["queue"]] == ["song 1", "song 2"]
    assert status["mode"] == "no_loop"
    assert status["shuffle"] is False
    assert status["autoplay"] is False


def test_status_when_idle(service: MusicService) -> None:
    status = service.status(GUILD_ID)

    assert status["state"] == "idle"
    assert status["current"] is None
    assert status["queue"] == []


@pytest.mark.asyncio
async def test_play_reports_the_voice_channel_name(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube, played: List[PlaybackContext],
    voice_client: FakeVoiceClient,
) -> None:
    voice_client.channel = SimpleNamespace(name="General")
    ctx.user.voice.channel = voice_client.channel

    result = await service.play(ctx, "稻香")

    assert result.data["channel"] == "General"


@pytest.mark.asyncio
async def test_a_queued_song_reports_what_is_playing_now(
    service: MusicService, cog: YTMusic, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext], voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))

    result = await service.play(ctx, "稻香")

    assert result.data["current"] == "song 0"


@pytest.mark.asyncio
async def test_skip_reports_the_next_song(
    service: MusicService, cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1))

    result = await service.skip(ctx)

    assert result.data == {"skipped": "song 0", "next": "song 1"}


@pytest.mark.asyncio
async def test_pause_reports_the_song_title(
    service: MusicService, cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def no_timer(guild_id: int) -> None:
        return None

    monkeypatch.setattr(cog, "_start_disconnect_timer", no_timer)
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))

    result = await service.pause(ctx)

    assert result.data == {"title": "song 0"}


@pytest.mark.asyncio
async def test_stop_reports_how_many_queued_songs_were_dropped(
    service: MusicService, cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1))
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(2))

    result = await service.stop(ctx)

    assert result.data == {"cleared": 2}


@pytest.mark.asyncio
async def test_a_refused_request_names_the_channel_the_bot_is_in(
    service: MusicService, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient,
) -> None:
    voice_client.channel = SimpleNamespace(name="Music Room")
    voice_client.playing = True
    outsider = PlaybackContext(guild=guild, channel=text_channel, user=make_member(5, voice_channel=object()))

    result = await service.skip(outsider)

    assert "Music Room" in result.detail


@pytest.mark.asyncio
async def test_search_skips_results_longer_than_the_limit_without_probing_them(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext],
) -> None:
    too_long = make_song(100) | {"duration": 3000}
    fine = make_song(101) | {"duration": 200}
    youtube.search_results = [too_long, fine]

    result = await service.play(ctx, "稻香")

    assert result.ok
    assert youtube.downloaded == [fine["url"]]


@pytest.mark.asyncio
async def test_search_keeps_results_whose_duration_is_unknown_such_as_live_streams(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext],
) -> None:
    live = make_song(100) | {"duration": 0}
    youtube.search_results = [live]

    await service.play(ctx, "lofi radio")

    assert youtube.downloaded == [live["url"]]


@pytest.mark.asyncio
async def test_search_where_everything_is_too_long_reports_it(
    service: MusicService, ctx: PlaybackContext, youtube: FakeYouTube,
    played: List[PlaybackContext],
) -> None:
    youtube.search_results = [make_song(100) | {"duration": 9000}]

    result = await service.play(ctx, "完整專輯")

    assert not result.ok
    assert result.reason == "no_results"
    assert "30 minutes" in result.detail
    assert youtube.downloaded == []
