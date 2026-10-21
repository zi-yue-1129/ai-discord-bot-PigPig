"""Seeking, audio effects, the previous button and the session history."""

from __future__ import annotations

from typing import Any, List

import pytest
from music_cog.helpers import GUILD_ID, FakeVoiceClient, make_song

from cogs.music import YTMusic
from cogs.music_lib.audio_manager import AudioManager
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.filters import FILTER_NAMES, get_preset
from cogs.music_lib.queue_manager import PlayMode
from cogs.music_lib.ui.text import format_clock, parse_clock


@pytest.fixture
def sources(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> List[dict]:
    """Records every audio source the cog creates; the player loop is not run."""
    made: List[dict] = []

    def fake_source(song: dict, volume: float = 1.0, start_offset: float = 0.0, audio_filter: Any = None) -> str:
        made.append({"song": song["video_id"], "offset": start_offset, "filter": audio_filter})
        return "source"

    async def no_loop(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog.audio_manager, "create_audio_source", fake_source)
    monkeypatch.setattr(cog, "_player_loop", no_loop)
    return made


def _playing(cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, index: int = 1, **extra: Any) -> dict:
    """Makes song ``index`` the one that is playing."""
    song = make_song(index) | {"duration": 200} | extra
    cog.state_manager.update_state(GUILD_ID, current_song=song, playback_ctx=ctx)
    voice_client.playing = True
    return song


# ------------------------------------------------------------------- seeking


@pytest.mark.asyncio
async def test_seek_restarts_the_song_at_the_requested_time(cog, ctx, voice_client, sources) -> None:
    _playing(cog, ctx, voice_client)

    result = await cog.service.seek(ctx, 95)

    assert result.ok and result.data["position"] == 95
    assert sources == [{"song": "v1", "offset": 95.0, "filter": None}]
    assert voice_client.stop_calls == 1 and voice_client.playing
    assert cog.state_manager.get_state(GUILD_ID).position == 95


@pytest.mark.asyncio
async def test_forward_and_rewind_count_from_the_current_position(cog, ctx, voice_client, sources) -> None:
    _playing(cog, ctx, voice_client)
    cog.state_manager.get_state(GUILD_ID).position = 50

    await cog.service.seek(ctx, 10, relative=True)
    await cog.service.seek(ctx, -100, relative=True)

    assert [source["offset"] for source in sources] == [60.0, 0.0]


@pytest.mark.asyncio
async def test_seeking_past_the_end_is_refused(cog, ctx, voice_client, sources) -> None:
    _playing(cog, ctx, voice_client)

    result = await cog.service.seek(ctx, 500)

    assert not result.ok and result.reason == "invalid_seek"
    assert sources == []


@pytest.mark.asyncio
async def test_a_live_stream_cannot_be_seeked(cog, ctx, voice_client, sources) -> None:
    _playing(cog, ctx, voice_client, is_live=True)

    result = await cog.service.seek(ctx, 10)

    assert result.reason == "cannot_seek_live"


@pytest.mark.asyncio
async def test_a_paused_song_stays_paused_at_the_new_position(cog, ctx, voice_client, sources) -> None:
    _playing(cog, ctx, voice_client)
    voice_client.pause()

    await cog.service.seek(ctx, 30)

    assert voice_client.paused


@pytest.mark.asyncio
async def test_nothing_to_seek_when_nothing_plays(cog, ctx, sources) -> None:
    result = await cog.service.seek(ctx, 30)

    assert result.reason == "nothing_playing"


def test_times_are_read_and_written_like_a_clock() -> None:
    assert parse_clock("90") == 90
    assert parse_clock("1:30") == 90
    assert parse_clock("1:02:03") == 3723
    assert format_clock(3723) == "1:02:03"
    assert format_clock(65) == "1:05"
    with pytest.raises(ValueError):
        parse_clock("1:3a")


# ------------------------------------------------------------------- effects


@pytest.mark.asyncio
async def test_an_effect_restarts_the_song_where_it_was_with_the_filter(cog, ctx, voice_client, sources) -> None:
    _playing(cog, ctx, voice_client)
    cog.state_manager.get_state(GUILD_ID).position = 42

    result = await cog.service.set_filter(ctx, "nightcore")

    assert result.ok
    assert sources == [{"song": "v1", "offset": 42.0, "filter": get_preset("nightcore").chain}]


@pytest.mark.asyncio
async def test_the_effect_stays_on_for_the_next_song(cog, ctx, voice_client, sources) -> None:
    await cog.service.set_filter(ctx, "8d")

    cog._make_source(GUILD_ID, make_song(2))

    assert sources[-1] == {"song": "v2", "offset": 0.0, "filter": get_preset("8d").chain}


@pytest.mark.asyncio
async def test_an_unknown_effect_is_refused(cog, ctx, sources) -> None:
    result = await cog.service.set_filter(ctx, "chipmunk")

    assert result.reason == "invalid_filter"
    assert cog.state_manager.get_state(GUILD_ID).audio_filter == "off"


def test_ffmpeg_gets_the_filter_and_the_start_offset(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    calls: List[dict] = []

    class _Recorded:
        def __init__(self, source: str, **kwargs: Any) -> None:
            calls.append({"source": source, **kwargs})

    monkeypatch.setattr("cogs.music_lib.audio_manager.FFmpegPCMAudio", _Recorded)
    monkeypatch.setattr("cogs.music_lib.audio_manager.PCMVolumeTransformer", lambda source, volume: source)
    file = tmp_path / "song.mp3"
    file.touch()

    AudioManager().create_audio_source({"file_path": str(file)}, start_offset=12, audio_filter="atempo=1.25")
    AudioManager().create_audio_source({"file_path": None, "stream_url": "https://u"}, start_offset=30)

    assert calls[0]["before_options"] == "-ss 12"
    assert '-af "atempo=1.25"' in calls[0]["options"]
    assert calls[1]["before_options"].startswith("-ss 30 ")


def test_every_effect_has_a_name_in_every_language() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "translations"
    for locale in ("zh_TW", "zh_CN", "en_US", "ja_JP"):
        names = json.loads((root / locale / "system" / "music" / "filters.json").read_text(encoding="utf-8"))
        assert set(FILTER_NAMES) <= set(names), locale


# ----------------------------------------------------------- history & back


@pytest.mark.asyncio
async def test_finished_songs_are_remembered_newest_first(cog, ctx, voice_client, sources, monkeypatch) -> None:
    async def no_next(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog, "play_next", no_next)
    for index in (1, 2):
        song = _playing(cog, ctx, voice_client, index)
        await cog._handle_after_play(ctx, song)

    assert [song["video_id"] for song in cog.service.history(GUILD_ID)] == ["v2", "v1"]


@pytest.mark.asyncio
async def test_previous_plays_the_earlier_song_then_the_current_one_again(cog, ctx, voice_client, sources) -> None:
    earlier = make_song(1)
    cog.state_manager.get_state(GUILD_ID).history = [earlier]
    _playing(cog, ctx, voice_client, 2)
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(3))

    result = await cog.service.previous(ctx)

    assert result.ok and result.data["title"] == "song 1"
    queue = [song["video_id"] for song in cog.queue_manager.get_queue_snapshot(GUILD_ID)]
    assert queue == ["v1", "v2", "v3"]
    assert voice_client.stop_calls == 1
    state = cog.state_manager.get_state(GUILD_ID)
    assert state.history == [] and state.going_back and state.force_next


@pytest.mark.asyncio
async def test_the_song_left_by_previous_is_not_added_to_the_history(cog, ctx, voice_client, sources, monkeypatch) -> None:
    async def no_next(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog, "play_next", no_next)
    cog.state_manager.get_state(GUILD_ID).history = [make_song(1)]
    song = _playing(cog, ctx, voice_client, 2)
    await cog.service.previous(ctx)

    await cog._handle_after_play(ctx, song)

    assert cog.service.history(GUILD_ID) == []


@pytest.mark.asyncio
async def test_previous_without_history_starts_the_song_over(cog, ctx, voice_client, sources) -> None:
    _playing(cog, ctx, voice_client)
    cog.state_manager.get_state(GUILD_ID).position = 80

    result = await cog.service.previous(ctx)

    assert result.ok and result.data["replayed"]
    assert sources[-1]["offset"] == 0.0


@pytest.mark.asyncio
async def test_in_loop_queue_mode_previous_does_not_queue_the_current_song_twice(cog, ctx, voice_client, sources) -> None:
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_QUEUE)
    cog.state_manager.get_state(GUILD_ID).history = [make_song(1)]
    _playing(cog, ctx, voice_client, 2)

    await cog.service.previous(ctx)

    assert [song["video_id"] for song in cog.queue_manager.get_queue_snapshot(GUILD_ID)] == ["v1"]


@pytest.mark.asyncio
async def test_leaving_the_channel_forgets_the_session(cog, ctx, voice_client, sources) -> None:
    state = cog.state_manager.get_state(GUILD_ID)
    state.history = [make_song(1)]
    state.audio_filter = "nightcore"

    await cog._cleanup_voice_session(GUILD_ID)

    assert state.history == [] and state.audio_filter == "off"
