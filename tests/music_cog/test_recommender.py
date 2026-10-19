"""Tests for the autoplay recommender: candidate filtering, ranking, taste memory and the Mix source."""

from __future__ import annotations

import asyncio
import random
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest
from music_cog.helpers import BOT_USER_ID, GUILD_ID, REQUESTER_ID, FakeVoiceClient, make_song

from addons.settings import AutoplaySettings, MusicConfig
from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.recommender import (
    TasteMemory,
    filter_candidates,
    normalize_author,
    rank_candidates,
)
from cogs.music_lib.youtube import YouTubeManager


def _candidate(video_id: str, author: str = "A", duration: int = 200, title: str = "", is_live: bool = False) -> dict:
    return {"video_id": video_id, "title": title or f"title {video_id}", "author": author, "duration": duration,
            "is_live": is_live, "url": f"https://youtube.com/watch?v={video_id}"}


def _ids(candidates: List[dict]) -> List[str]:
    return [candidate["video_id"] for candidate in candidates]


BANNED = ("1 hour", "nightcore")


# ------------------------------------------------------------------ settings


def test_autoplay_settings_defaults() -> None:
    settings = AutoplaySettings()

    assert settings.use_mix is True
    assert settings.max_per_author == 2
    assert settings.history_size == 50
    assert "nightcore" in settings.banned_keywords


def test_music_config_reads_the_autoplay_block(tmp_path: Path) -> None:
    path = tmp_path / "music.yaml"
    path.write_text("autoplay:\n  max_per_author: 1\n  banned_keywords:\n    - karaoke\n", encoding="utf-8")

    config = MusicConfig(str(path))

    assert config.autoplay.max_per_author == 1
    assert config.autoplay.banned_keywords == ("karaoke",)


def test_music_config_rejects_unknown_autoplay_keys(tmp_path: Path) -> None:
    path = tmp_path / "music.yaml"
    path.write_text("autoplay:\n  max_per_artist: 1\n", encoding="utf-8")

    with pytest.raises(TypeError):
        MusicConfig(str(path))


# --------------------------------------------------------------- authors, memory


def test_authors_are_compared_without_channel_decorations() -> None:
    assert normalize_author("YOASOBI - Topic") == "yoasobi"
    assert normalize_author("HoneyWorks OFFICIAL") == "honeyworks"
    assert normalize_author("Ado VEVO") == "ado"
    assert normalize_author("  Eve ") == "eve"


def test_the_history_keeps_only_the_most_recent_songs() -> None:
    memory = TasteMemory(history_size=3)

    for video_id in ("a", "b", "c", "d"):
        memory.record_played(video_id)

    assert memory.played_ids() == {"b", "c", "d"}


def test_requests_and_skips_are_counted_per_normalized_author() -> None:
    memory = TasteMemory(history_size=3)

    memory.record_request("YOASOBI - Topic")
    memory.record_request("yoasobi")
    memory.record_skip("Eve")

    assert memory.requested["yoasobi"] == 2
    assert memory.skipped["eve"] == 1


# ------------------------------------------------------------------- filtering


def test_filtering_drops_excluded_live_short_long_and_unwanted_versions() -> None:
    pool = [
        _candidate("keep1"),
        _candidate("seen"),
        _candidate("live", is_live=True),
        _candidate("short", duration=20),
        _candidate("long", duration=9000),
        _candidate("loop", title="Song [1 HOUR] loop"),
        _candidate("fast", title="Song NightCore edit"),
        _candidate("keep2", duration=60),
    ]

    kept = filter_candidates(pool, exclude_ids={"seen"}, min_duration=60, max_duration=1800, banned_keywords=BANNED)

    assert _ids(kept) == ["keep1", "keep2"]


def test_filtering_ignores_candidates_without_an_id() -> None:
    pool = [_candidate(""), _candidate("ok")]

    assert _ids(filter_candidates(pool, exclude_ids=set(), min_duration=0, max_duration=999, banned_keywords=())) == ["ok"]


# --------------------------------------------------------------------- ranking


def _rank(pool: List[dict], **overrides: Any) -> List[dict]:
    options: Dict[str, Any] = {"seed_author": "seed", "taste": TasteMemory(history_size=10), "max_per_author": 2,
                               "limit": 10, "rng": random.Random(1), "jitter": 0.0}
    options.update(overrides)
    return rank_candidates(pool, **options)


def test_without_any_signal_the_mix_order_is_kept() -> None:
    pool = [_candidate(name, author=name) for name in "abcd"]

    assert _ids(_rank(pool, limit=3)) == ["a", "b", "c"]


def test_one_author_cannot_fill_the_batch() -> None:
    pool = [_candidate(f"a{i}", author="A") for i in range(5)] + [_candidate(f"b{i}", author="B") for i in range(3)]

    assert _ids(_rank(pool, limit=4)) == ["a0", "a1", "b0", "b1"]


def test_the_cap_is_relaxed_when_there_is_nothing_else_to_choose() -> None:
    pool = [_candidate(f"a{i}", author="A") for i in range(5)]

    assert len(_rank(pool, limit=4)) == 4


def test_authors_the_guild_requests_are_preferred() -> None:
    taste = TasteMemory(history_size=10)
    for _ in range(3):
        taste.record_request("Y")
    pool = [_candidate("x1", author="X"), _candidate("y1", author="Y")]

    assert _ids(_rank(pool, taste=taste)) == ["y1", "x1"]


def test_authors_whose_songs_get_skipped_are_demoted() -> None:
    taste = TasteMemory(history_size=10)
    taste.record_skip("X")
    taste.record_skip("X")
    pool = [_candidate("x1", author="X"), _candidate("y1", author="Y")]

    assert _ids(_rank(pool, taste=taste)) == ["y1", "x1"]


def test_ranking_is_repeatable_with_the_same_random_generator() -> None:
    pool = [_candidate(f"s{i}", author=f"author{i}") for i in range(12)]

    first = _ids(_rank(pool, jitter=0.5, rng=random.Random(5), limit=6))
    second = _ids(_rank(pool, jitter=0.5, rng=random.Random(5), limit=6))

    assert first == second


def test_jitter_varies_the_order_between_generators() -> None:
    pool = [_candidate(f"s{i}", author=f"author{i}") for i in range(12)]

    orders = {tuple(_ids(_rank(pool, jitter=0.5, rng=random.Random(seed), limit=6))) for seed in range(8)}

    assert len(orders) > 1


# ------------------------------------------------------------ the Mix source


class _FakeYoutubeDL:
    """yt-dlp stand-in returning a canned Mix."""

    entries: List[Dict[str, Any]] = []
    started = threading.Event()
    release = threading.Event()
    block = False
    urls: List[str] = []

    def __init__(self, opts: Dict[str, Any]) -> None:
        self.opts = opts

    def __enter__(self) -> "_FakeYoutubeDL":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def extract_info(self, url: str, download: bool = False) -> Dict[str, Any]:
        type(self).urls.append(url)
        if type(self).block:
            type(self).started.set()
            type(self).release.wait(timeout=5)
        return {"entries": list(type(self).entries)}


@pytest.fixture
def mix_manager(monkeypatch: pytest.MonkeyPatch) -> YouTubeManager:
    _FakeYoutubeDL.block = False
    _FakeYoutubeDL.urls = []
    monkeypatch.setattr("cogs.music_lib.youtube.yt_dlp.YoutubeDL", _FakeYoutubeDL)
    manager = YouTubeManager()
    manager.settings = SimpleNamespace(autoplay=AutoplaySettings(), youtube_cookies_path="/nonexistent/cookies.txt")
    return manager


@pytest.mark.asyncio
async def test_the_mix_of_a_video_is_read_and_normalized(mix_manager: YouTubeManager) -> None:
    _FakeYoutubeDL.entries = [
        {"id": "seed", "title": "Seed", "duration": 209, "channel": "YOASOBI", "url": "https://www.youtube.com/watch?v=seed",
         "live_status": "not_live"},
        {"id": "b", "title": "B", "duration": 259.0, "uploader": "Eve", "live_status": "is_live"},
        {"id": None, "title": "broken"},
    ]

    pool = await mix_manager.get_mix_candidates("seed", limit=20)

    assert _FakeYoutubeDL.urls == ["https://www.youtube.com/watch?v=seed&list=RDseed"]
    assert [(c["video_id"], c["author"], c["duration"], c["is_live"]) for c in pool] == [
        ("seed", "YOASOBI", 209, False), ("b", "Eve", 259, True),
    ]
    assert pool[0]["url"] == "https://youtube.com/watch?v=seed"


@pytest.mark.asyncio
async def test_a_mix_that_cannot_be_read_gives_no_candidates(mix_manager: YouTubeManager, monkeypatch: pytest.MonkeyPatch) -> None:
    def failing(self: Any, url: str, download: bool = False) -> Dict[str, Any]:
        raise OSError("network down")

    monkeypatch.setattr(_FakeYoutubeDL, "extract_info", failing)

    assert await mix_manager.get_mix_candidates("seed", limit=20) == []


@pytest.mark.asyncio
async def test_a_mix_lookup_that_hangs_gives_up(mix_manager: YouTubeManager, monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeYoutubeDL.block = True
    _FakeYoutubeDL.started.clear()
    _FakeYoutubeDL.release.clear()
    monkeypatch.setattr("cogs.music_lib.youtube.MIX_TIMEOUT_SECONDS", 0.05)

    pool = await asyncio.wait_for(mix_manager.get_mix_candidates("seed", limit=20), timeout=2)
    _FakeYoutubeDL.release.set()

    assert pool == []


# --------------------------------------------------- related videos use the Mix


def _context() -> SimpleNamespace:
    user = SimpleNamespace(id=1, display_avatar=SimpleNamespace(url="x"))
    return SimpleNamespace(guild=SimpleNamespace(id=1), user=user)


@pytest.fixture
def searches(mix_manager: YouTubeManager, monkeypatch: pytest.MonkeyPatch) -> List[str]:
    """Records keyword searches (the fallback) and answers them with one result."""
    queries: List[str] = []

    async def search(query: str, max_results: int = 10) -> List[dict]:
        queries.append(query)
        return [{"video_id": "found", "title": "found", "url": "https://youtube.com/watch?v=found", "duration": 200,
                 "author": "Someone", "views": 5}]

    monkeypatch.setattr(mix_manager, "search_videos", search)
    return queries


def _mix(monkeypatch: pytest.MonkeyPatch, manager: YouTubeManager, pool: List[dict]) -> None:
    async def mix(video_id: str, limit: int = 25) -> List[dict]:
        return pool

    monkeypatch.setattr(manager, "get_mix_candidates", mix)


@pytest.mark.asyncio
async def test_recommendations_come_from_the_mix_without_any_keyword_search(
    mix_manager: YouTubeManager, searches: List[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    pool = [_candidate("seed", author="YOASOBI"), _candidate("a", author="Eve"), _candidate("b", author="Ado"),
            _candidate("c", author="Eve"), _candidate("d", author="Eve"), _candidate("shortie", duration=10)]
    _mix(monkeypatch, mix_manager, pool)

    videos, error = await mix_manager.get_related_videos("seed", "Seed", "YOASOBI", _context(), limit=3, exclude_ids={"b"})

    assert error is None
    assert _ids(videos) == ["a", "c", "d"]
    assert "seed" not in _ids(videos) and "b" not in _ids(videos) and "shortie" not in _ids(videos)
    assert searches == []


@pytest.mark.asyncio
async def test_recommendations_have_the_shape_the_queue_expects(
    mix_manager: YouTubeManager, searches: List[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _mix(monkeypatch, mix_manager, [_candidate("a", author="Eve")])

    videos, _ = await mix_manager.get_related_videos("seed", "Seed", "YOASOBI", _context(), limit=1)

    assert videos[0] | {"requester": None} == {
        "file_path": None, "title": "title a", "url": "https://youtube.com/watch?v=a", "stream_url": None, "duration": 200,
        "video_id": "a", "author": "Eve", "views": 0, "requester": None, "user_avatar": "x", "is_live": False,
    }


@pytest.mark.asyncio
async def test_without_a_usable_mix_the_keyword_search_still_works(
    mix_manager: YouTubeManager, searches: List[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _mix(monkeypatch, mix_manager, [])

    videos, error = await mix_manager.get_related_videos("seed", "Seed", "YOASOBI", _context(), limit=1)

    assert error is None
    assert _ids(videos) == ["found"]
    assert searches


@pytest.mark.asyncio
async def test_the_mix_can_be_switched_off(
    mix_manager: YouTubeManager, searches: List[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _mix(monkeypatch, mix_manager, [_candidate("a")])
    mix_manager.settings = SimpleNamespace(autoplay=AutoplaySettings(use_mix=False), youtube_cookies_path="/nonexistent")

    videos, _ = await mix_manager.get_related_videos("seed", "Seed", "YOASOBI", _context(), limit=1)

    assert _ids(videos) == ["found"]


@pytest.mark.asyncio
async def test_a_short_mix_is_completed_by_the_keyword_search(
    mix_manager: YouTubeManager, searches: List[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _mix(monkeypatch, mix_manager, [_candidate("a", author="Eve")])

    videos, _ = await mix_manager.get_related_videos("seed", "Seed", "YOASOBI", _context(), limit=2)

    assert _ids(videos)[0] == "a"
    assert len(videos) == 2


@pytest.mark.asyncio
async def test_the_guilds_taste_reorders_the_mix(
    mix_manager: YouTubeManager, searches: List[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _mix(monkeypatch, mix_manager, [_candidate("x1", author="X"), _candidate("y1", author="Y")])
    taste = TasteMemory(history_size=10)
    for _ in range(3):
        taste.record_request("Y")

    videos, _ = await mix_manager.get_related_videos("seed", "Seed", "S", _context(), limit=1, taste=taste)

    assert _ids(videos) == ["y1"]


# ------------------------------------------------- the cog feeds the memory


@pytest.fixture
def wired_player(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_source(song: dict, volume: float = 1.0, start_offset: float = 0.0) -> str:
        return "source"

    async def fake_ui(*args: Any, **kwargs: Any) -> None:
        return None

    def fake_loop(ctx: Any, song: dict, start_offset: float = 0.0) -> Any:
        return asyncio.sleep(0)

    monkeypatch.setattr(cog.audio_manager, "create_audio_source", fake_source)
    monkeypatch.setattr(cog.ui_manager, "update_player_ui", fake_ui, raising=False)
    monkeypatch.setattr(cog, "_player_loop", fake_loop)


@pytest.mark.asyncio
async def test_playing_a_song_is_remembered_and_a_users_request_counts(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, wired_player: None
) -> None:
    song = make_song(1) | {"author": "Eve - Topic", "added_by": REQUESTER_ID}

    await cog._play_song(ctx, song, voice_client)

    taste = cog.taste_for(GUILD_ID)
    assert taste.played_ids() == {"v1"}
    assert taste.requested["eve"] == 1


@pytest.mark.asyncio
async def test_a_song_the_bot_chose_is_remembered_but_is_not_a_request(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, wired_player: None
) -> None:
    song = make_song(2) | {"author": "Ado", "added_by": BOT_USER_ID}

    await cog._play_song(ctx, song, voice_client)

    taste = cog.taste_for(GUILD_ID)
    assert taste.played_ids() == {"v2"}
    assert taste.requested["ado"] == 0


async def _skip_after(cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, song: dict, seconds: float) -> None:
    clock = {"now": 100.0}
    cog._clock = lambda: clock["now"]
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=song, song_started_at=clock["now"])
    clock["now"] += seconds

    await cog.service.skip(ctx)


@pytest.mark.asyncio
async def test_skipping_a_recommendation_right_away_demotes_its_author(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient
) -> None:
    await _skip_after(cog, ctx, voice_client, make_song(3) | {"author": "Ado", "added_by": BOT_USER_ID}, seconds=5)

    assert cog.taste_for(GUILD_ID).skipped["ado"] == 1


@pytest.mark.asyncio
async def test_skipping_late_or_skipping_a_request_is_no_complaint_about_the_author(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient
) -> None:
    await _skip_after(cog, ctx, voice_client, make_song(4) | {"author": "Ado", "added_by": BOT_USER_ID}, seconds=120)
    await _skip_after(cog, ctx, voice_client, make_song(5) | {"author": "Ado", "added_by": REQUESTER_ID}, seconds=5)

    assert cog.taste_for(GUILD_ID).skipped["ado"] == 0


@pytest.mark.asyncio
async def test_autoplay_avoids_what_was_played_recently_and_passes_the_taste(
    cog: YTMusic, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: Dict[str, Any] = {}

    async def related(video_id: str, title: str, author: str, ctx: Any, limit: int = 5,
                      exclude_ids: Any = None, taste: Any = None) -> tuple:
        captured.update(exclude_ids=set(exclude_ids), taste=taste, limit=limit)
        return [], "none"

    monkeypatch.setattr(cog, "youtube", SimpleNamespace(get_related_videos=related))
    cog.taste_for(GUILD_ID).record_played("old1")
    cog.state_manager.update_state(GUILD_ID, autoplay=True, current_song=make_song(9) | {"author": "Ado"})
    ctx = SimpleNamespace(guild=SimpleNamespace(id=GUILD_ID), user=SimpleNamespace(id=1))

    await cog._trigger_autoplay(ctx, GUILD_ID)

    assert "old1" in captured["exclude_ids"]
    assert captured["taste"] is cog.taste_for(GUILD_ID)
