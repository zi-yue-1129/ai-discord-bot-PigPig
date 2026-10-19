"""Regression tests for the second audit of the music feature."""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional, Tuple

import discord
import pytest
from music_cog.helpers import (
    BOT_USER_ID,
    GUILD_ID,
    REQUESTER_ID,
    FakeChannel,
    FakeVoiceClient,
    make_interaction,
    make_member,
    make_song,
)
from music_cog.test_music_tools import FakeService, _runtime, _tools
from music_cog.test_service import FakeYouTube

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.service import ActionResult
from cogs.music_lib.youtube import YouTubeManager, parse_view_count

REPO = Path(__file__).resolve().parents[2]
LOCALES = ("en_US", "ja_JP", "zh_CN", "zh_TW")

# Translation keys the music code uses; each must exist in every locale.
REQUIRED_KEYS = [
    ("system", "music", "select", "timeout"),
    ("system", "music", "select", "queue_full"),
    ("system", "music", "select", "wait_message"),
    ("system", "music", "select", "error"),
    ("system", "music", "player", "live"),
    ("system", "music", "controls", "no_songs"),
    ("commands", "shuffle", "responses", "enabled"),
    ("commands", "shuffle", "responses", "disabled"),
]


def _lookup(locale: str, path: Tuple[str, ...]) -> Optional[str]:
    """Resolves a translation key against the JSON files, like LanguageManager does."""
    for split in range(len(path) - 1, 0, -1):
        file = REPO / "translations" / locale / Path(*path[:split]).with_suffix(".json")
        if file.exists():
            node: Any = json.loads(file.read_text(encoding="utf-8"))
            for part in path[split:]:
                if not isinstance(node, dict) or part not in node:
                    return None
                node = node[part]
            return node if isinstance(node, str) else None
    return None


@pytest.mark.parametrize("locale", LOCALES)
@pytest.mark.parametrize("path", REQUIRED_KEYS, ids=[".".join(key) for key in REQUIRED_KEYS])
def test_every_translation_key_the_music_code_uses_exists(locale: str, path: Tuple[str, ...]) -> None:
    assert _lookup(locale, path)


@pytest.mark.parametrize("locale", LOCALES)
def test_the_shuffle_confirmation_names_the_new_state(locale: str) -> None:
    assert "{status}" in str(_lookup(locale, ("commands", "shuffle", "responses", "success")))


@pytest.mark.parametrize("locale", LOCALES)
def test_the_player_footer_shows_who_added_the_song(locale: str) -> None:
    assert "{user}" in str(_lookup(locale, ("system", "music", "player", "added_by")))


# ----------------------------------------------------------------- live stream queue button


class _View:
    """Control view stand-in holding a real embed."""

    def __init__(self, embed: discord.Embed) -> None:
        self.current_embed = embed
        self.updated: List[str] = []
        self.button_updates = 0

    async def update_embed(self, interaction: Any, title: str, color: Any) -> None:
        self.updated.append(title)

    async def update_button_state(self) -> None:
        self.button_updates += 1


@pytest.mark.asyncio
async def test_the_queue_button_works_on_a_live_stream_embed_without_a_progress_field(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel
) -> None:
    embed = discord.Embed(title="live now")
    # A live embed has no progress field, so the queue field sits at index 3, not 4.
    for name in ("uploader", "duration", "views", "queue"):
        embed.add_field(name=f"system.music.player.{name}", value="placeholder")
    cog.ui_manager.get_current_view = lambda guild_id: _View(embed)
    interaction = make_interaction(guild, text_channel, make_member(REQUESTER_ID, voice_channel=None))

    await cog.handle_show_queue(interaction)

    queue_field = next(field for field in embed.fields if field.name == "system.music.player.queue")
    assert queue_field.value != "placeholder"
    assert len(embed.fields) == 4


# ------------------------------------------------------------ bot left behind after a failed play


@pytest.mark.asyncio
async def test_a_play_that_finds_nothing_does_not_keep_the_bot_in_the_channel_forever(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    youtube = FakeYouTube()
    youtube.search_results = []
    monkeypatch.setattr(cog, "youtube", youtube)

    result = await cog.service.play(ctx, "xyzzy")

    assert not result.ok
    timer = cog.disconnect_timers[GUILD_ID]
    assert not timer.done()
    timer.cancel()


@pytest.mark.asyncio
async def test_a_failed_play_leaves_a_player_that_is_busy_alone(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    youtube = FakeYouTube()
    youtube.search_results = []
    monkeypatch.setattr(cog, "youtube", youtube)
    voice_client.playing = True

    await cog.service.play(ctx, "xyzzy")

    assert GUILD_ID not in cog.disconnect_timers


# ------------------------------------------------------------------- slash commands refresh


@pytest.mark.asyncio
async def test_the_mode_command_refreshes_the_player_buttons(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient,
    requester: SimpleNamespace,
) -> None:
    view = _View(discord.Embed())
    cog.ui_manager.get_current_view = lambda guild_id: view
    interaction = make_interaction(guild, text_channel, requester)

    async def original_response() -> Any:
        return SimpleNamespace()

    interaction.original_response = original_response

    await cog.mode.callback(cog, interaction, SimpleNamespace(value="loop_single"))

    assert view.button_updates == 1


@pytest.mark.asyncio
async def test_the_shuffle_command_refreshes_the_player_buttons(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient,
    requester: SimpleNamespace,
) -> None:
    view = _View(discord.Embed())
    cog.ui_manager.get_current_view = lambda guild_id: view
    interaction = make_interaction(guild, text_channel, requester)

    async def original_response() -> Any:
        return SimpleNamespace()

    interaction.original_response = original_response

    await cog.shuffle.callback(cog, interaction)

    assert view.button_updates == 1


# ------------------------------------------------------------------ what the AI is told


@pytest.mark.asyncio
async def test_skip_does_not_claim_the_queue_is_empty_when_more_songs_are_coming() -> None:
    service = FakeService()
    service.result = ActionResult(ok=True, data={"skipped": "稻香", "next": None, "more_coming": True})

    reply = await _tools(_runtime(service))["skip_music"].ainvoke({})

    assert "empty" not in reply
    assert "More songs" in reply


@pytest.mark.asyncio
async def test_a_playlist_that_only_fills_the_buffer_says_so() -> None:
    service = FakeService()
    service.result = ActionResult(
        ok=True,
        data={"kind": "playlist", "added": 0, "total": 30, "buffered": 30, "titles": [], "channel": "General"},
    )

    reply = await _tools(_runtime(service))["play_music"].ainvoke({"query": "https://youtube.com/playlist?list=PL1"})

    assert "Queued 0" not in reply
    assert "30 songs" in reply
    assert "after the current queue" in reply


@pytest.mark.asyncio
async def test_the_service_reports_whether_more_songs_follow_a_skip(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient
) -> None:
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))
    cog.queue_manager.set_playlist(GUILD_ID, [make_song(5)])

    result = await cog.service.skip(ctx)

    assert result.data["more_coming"] is True


@pytest.mark.asyncio
async def test_a_playlist_result_counts_the_buffered_songs(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeYouTube()
    monkeypatch.setattr(cog, "youtube", fake)
    for index in range(5):
        await cog.queue_manager.add_to_queue(GUILD_ID, make_song(index))

    added, total, failure = await cog.service.enqueue_playlist(ctx, "https://youtube.com/playlist?list=PL1")

    assert failure is None
    assert (len(added or []), total) == (0, 8)
    assert len(cog.queue_manager.guild_playlists[GUILD_ID]) == 8


# ---------------------------------------------------------------- voice move failure


@pytest.mark.asyncio
async def test_a_failed_move_to_the_requesters_channel_is_reported_not_raised(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def failing_move(channel: object) -> None:
        raise discord.ClientException("cannot move")

    monkeypatch.setattr(voice_client, "move_to", failing_move)
    ctx.user.voice = SimpleNamespace(channel=object())

    result = await cog.service.play(ctx, "怪物")

    assert not result.ok
    assert result.reason == "voice_connect_failed"


# --------------------------------------------------------- the same song twice, removals


@pytest.mark.asyncio
async def test_a_queued_song_whose_file_is_gone_is_downloaded_again_instead_of_failing(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    downloaded: List[str] = []

    async def fake_ensure(context: Any, song: dict) -> Tuple[dict, None]:
        downloaded.append(song["video_id"])
        fresh = tmp_path / "fresh.mp3"
        fresh.write_bytes(b"x")
        song["file_path"] = str(fresh)
        return song, None

    monkeypatch.setattr(cog.prefetcher, "ensure_downloaded", fake_ensure)
    gone = make_song(1) | {"file_path": str(tmp_path / "deleted-by-the-first-play.mp3")}
    await cog.queue_manager.add_to_queue(GUILD_ID, gone)

    next_song = await cog._get_next_song(ctx, GUILD_ID, force_new=False)

    assert downloaded == ["v1"]
    assert next_song["file_path"].endswith("fresh.mp3")


@pytest.mark.asyncio
async def test_a_finished_song_keeps_its_file_while_a_queued_copy_still_needs_it(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async def no_next(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog, "play_next", no_next)
    shared = tmp_path / "v1.mp3"
    shared.write_bytes(b"x")
    playing = make_song(1) | {"file_path": str(shared)}
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1) | {"file_path": str(shared)})
    cog.state_manager.update_state(GUILD_ID, current_song=playing)

    await cog._handle_after_play(ctx, playing)

    assert shared.exists()


@pytest.mark.asyncio
async def test_removing_a_song_cancels_its_prefetch_download(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    cancelled: List[Tuple[int, str]] = []

    async def record(guild_id: int, video_id: str) -> None:
        cancelled.append((guild_id, video_id))

    monkeypatch.setattr(cog.prefetcher, "cancel_song", record)
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1))

    result = await cog.service.remove_from_queue(ctx, 1)

    assert result.ok
    assert cancelled == [(GUILD_ID, "v1")]


@pytest.mark.asyncio
async def test_cancel_song_stops_only_that_songs_download(cog: YTMusic, ctx: PlaybackContext) -> None:
    started = asyncio.Event()

    async def forever() -> None:
        started.set()
        await asyncio.sleep(100)

    target = asyncio.create_task(forever())
    other = asyncio.create_task(asyncio.sleep(100))
    cog.prefetcher._inflight[(GUILD_ID, "v1")] = target
    cog.prefetcher._inflight[(GUILD_ID, "v2")] = other
    await started.wait()

    await cog.prefetcher.cancel_song(GUILD_ID, "v1")

    assert target.cancelled()
    assert not other.done()
    other.cancel()


@pytest.mark.asyncio
async def test_asking_for_a_song_the_bot_recommended_makes_it_the_users_and_moves_it_to_the_front(
    cog: YTMusic,
) -> None:
    queue = cog.queue_manager
    await queue.add_to_queue(GUILD_ID, make_song(1) | {"added_by": REQUESTER_ID})
    await queue.add_to_queue(GUILD_ID, make_song(2) | {"added_by": BOT_USER_ID})
    await queue.add_to_queue(GUILD_ID, make_song(3) | {"added_by": BOT_USER_ID})

    assert await queue.add_to_front_of_queue(GUILD_ID, make_song(3) | {"added_by": REQUESTER_ID})

    snapshot = queue.get_queue_snapshot(GUILD_ID)
    assert [song["video_id"] for song in snapshot] == ["v3", "v1", "v2"]
    assert snapshot[0]["added_by"] == REQUESTER_ID


@pytest.mark.asyncio
async def test_a_second_playlist_is_added_after_the_buffered_rest_of_the_first(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeYouTube()
    monkeypatch.setattr(cog, "youtube", fake)

    await cog.service.enqueue_playlist(ctx, "https://youtube.com/playlist?list=PL1")
    first_rest = [song["video_id"] for song in cog.queue_manager.guild_playlists[GUILD_ID]]
    fake.playlist = [make_song(300 + index) for index in range(4)]
    await cog.service.enqueue_playlist(ctx, "https://youtube.com/playlist?list=PL2")

    buffered = [song["video_id"] for song in cog.queue_manager.guild_playlists[GUILD_ID]]
    assert buffered[: len(first_rest)] == first_rest
    assert len(buffered) == len(first_rest) + 4


# ------------------------------------------------------------------ search and recommendations


def test_view_counts_are_compared_as_numbers() -> None:
    assert parse_view_count("1,234,567 views") == 1234567
    assert parse_view_count("9,000 views") < parse_view_count("12,000,000 views")
    assert parse_view_count("No views") == 0
    assert parse_view_count(42) == 42
    assert parse_view_count(None) == 0


@pytest.mark.asyncio
async def test_a_search_that_never_returns_gives_up_instead_of_hanging(monkeypatch: pytest.MonkeyPatch) -> None:
    release = threading.Event()

    class Hanging:
        def __init__(self, query: str, max_results: int = 10) -> None:
            release.wait(timeout=5)

        def to_dict(self) -> list:
            return []

    monkeypatch.setattr("cogs.music_lib.youtube.YoutubeSearch", Hanging)
    monkeypatch.setattr("cogs.music_lib.youtube.SEARCH_TIMEOUT_SECONDS", 0.05)
    manager = YouTubeManager()

    results = await asyncio.wait_for(manager.search_videos("怪物"), timeout=2)
    release.set()

    assert results == []
