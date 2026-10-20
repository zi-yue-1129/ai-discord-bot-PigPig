"""Saved playlists, queue reordering and the text file format for exporting songs."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List

import pytest
from music_cog.helpers import GUILD_ID, make_member, make_song

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.music_store import SCOPE_GUILD, SCOPE_USER, MusicStore, PlaylistError
from cogs.music_lib.track_io import parse_tracks, tracks_to_text


def _track(index: int) -> dict:
    return {"url": f"https://youtu.be/v{index}", "title": f"song {index}", "video_id": f"v{index}",
            "author": "artist", "duration": 120}


# ---------------------------------------------------------------- the store


def test_a_playlist_keeps_its_songs_in_order_without_duplicates(tmp_path) -> None:
    store = MusicStore(tmp_path / "music.db")
    store.create_playlist(SCOPE_USER, 1, "Chill")

    added = store.add_tracks(SCOPE_USER, 1, "chill", [_track(1), _track(2), _track(1)])
    again = store.add_tracks(SCOPE_USER, 1, "Chill", [_track(2), _track(3)])

    playlist = store.get_playlist(SCOPE_USER, 1, "CHILL")
    assert (added, again) == (2, 1)
    assert [track["video_id"] for track in playlist.tracks] == ["v1", "v2", "v3"]


def test_personal_and_server_playlists_are_separate(tmp_path) -> None:
    store = MusicStore(tmp_path / "music.db")
    store.create_playlist(SCOPE_USER, 1, "Mix")
    store.create_playlist(SCOPE_GUILD, 1, "Mix")

    assert [p.name for p in store.list_playlists(SCOPE_USER, 1)] == ["Mix"]
    assert [p.name for p in store.list_playlists(SCOPE_GUILD, 1)] == ["Mix"]
    with pytest.raises(PlaylistError) as error:
        store.create_playlist(SCOPE_USER, 1, "mix")
    assert error.value.reason == "exists"


def test_limits_are_enforced(tmp_path) -> None:
    store = MusicStore(tmp_path / "music.db", max_playlists=1, max_tracks=2)
    store.create_playlist(SCOPE_USER, 1, "A")

    assert store.add_tracks(SCOPE_USER, 1, "A", [_track(1), _track(2), _track(3)]) == 2
    with pytest.raises(PlaylistError, match="full"):
        store.add_tracks(SCOPE_USER, 1, "A", [_track(4)])
    with pytest.raises(PlaylistError, match="too_many"):
        store.create_playlist(SCOPE_USER, 1, "B")


def test_removing_a_song_closes_the_gap(tmp_path) -> None:
    store = MusicStore(tmp_path / "music.db")
    store.create_playlist(SCOPE_USER, 1, "A")
    store.add_tracks(SCOPE_USER, 1, "A", [_track(1), _track(2), _track(3)])

    removed = store.remove_track(SCOPE_USER, 1, "A", 2)

    assert removed["video_id"] == "v2"
    assert [t["video_id"] for t in store.get_playlist(SCOPE_USER, 1, "A").tracks] == ["v1", "v3"]
    with pytest.raises(PlaylistError, match="invalid_position"):
        store.remove_track(SCOPE_USER, 1, "A", 5)


# ------------------------------------------------------------- the service


@pytest.mark.asyncio
async def test_sharing_gives_the_other_user_a_numbered_copy(cog: YTMusic, ctx: PlaybackContext) -> None:
    friend = make_member(77, voice_channel=None)
    friend.bot = False
    playlists = cog.playlists
    await playlists.create(ctx, "Chill", "personal")
    await playlists.add_tracks(ctx, "Chill", "personal", [_track(1)])
    cog.store.create_playlist(SCOPE_USER, 77, "Chill")

    result = await playlists.share(ctx, "Chill", friend)

    assert result.ok and result.data == {"name": "Chill (2)", "count": 1}
    # A copy: changing the original leaves the friend's list alone.
    await playlists.add_tracks(ctx, "Chill", "personal", [_track(2)])
    assert cog.store.get_playlist(SCOPE_USER, 77, "Chill (2)").track_count == 1


@pytest.mark.asyncio
async def test_only_managers_and_djs_change_server_playlists(cog: YTMusic, ctx: PlaybackContext) -> None:
    ctx.user.guild_permissions = SimpleNamespace(manage_guild=False, administrator=False)
    ctx.user.roles = []

    refused = await cog.playlists.create(ctx, "Party", "server")
    ctx.user.guild_permissions = SimpleNamespace(manage_guild=True, administrator=False)
    allowed = await cog.playlists.create(ctx, "Party", "server")

    assert refused.reason == "playlist_no_permission"
    assert allowed.ok


@pytest.mark.asyncio
async def test_playing_a_playlist_queues_its_songs_and_buffers_the_rest(cog: YTMusic, ctx: PlaybackContext, monkeypatch) -> None:
    started: List[Any] = []

    async def fake_play_next(source: Any, force_new: bool = False) -> None:
        started.append(source)
        source.guild.voice_client.playing = True

    monkeypatch.setattr(cog, "play_next", fake_play_next)
    monkeypatch.setattr(cog.prefetcher, "schedule", lambda ctx: None)
    await cog.playlists.create(ctx, "Big", "personal")
    await cog.playlists.add_tracks(ctx, "Big", "personal", [_track(i) for i in range(8)])

    result = await cog.playlists.play(ctx, "big")

    assert result.ok and result.data["total"] == 8 and started
    assert len(cog.queue_manager.get_queue_snapshot(GUILD_ID)) == 5
    assert len(cog.queue_manager.guild_playlists[GUILD_ID]) == 3
    queued = cog.queue_manager.get_queue_snapshot(GUILD_ID)[0]
    assert queued["requester"] is ctx.user and queued["file_path"] is None


@pytest.mark.asyncio
async def test_links_to_other_hosts_are_never_opened(cog: YTMusic, ctx: PlaybackContext) -> None:
    result = await cog.service.play_tracks(ctx, [{"url": "http://169.254.169.254/latest", "title": "x"}])

    assert result.reason == "nothing_to_import"


@pytest.mark.asyncio
async def test_saving_the_queue_creates_the_playlist(cog: YTMusic, ctx: PlaybackContext) -> None:
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(1))
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(2))

    result = await cog.playlists.save_queue(ctx, "Tonight", "personal")

    assert result.ok and result.data["added"] == 2
    assert [t["video_id"] for t in cog.store.get_playlist(SCOPE_USER, ctx.user.id, "Tonight").tracks] == ["v1", "v2"]


# ----------------------------------------------------------- queue editing


@pytest.mark.asyncio
async def test_move_and_swap_reorder_the_queue(cog: YTMusic, ctx: PlaybackContext, monkeypatch) -> None:
    monkeypatch.setattr(cog.prefetcher, "schedule", lambda ctx: None)
    for index in (1, 2, 3, 4):
        await cog.queue_manager.add_to_queue(GUILD_ID, make_song(index))

    await cog.service.move(ctx, 4, 1)
    await cog.service.swap(ctx, 2, 3)
    bad = await cog.service.move(ctx, 9, 1)

    assert [s["video_id"] for s in cog.queue_manager.get_queue_snapshot(GUILD_ID)] == ["v4", "v2", "v1", "v3"]
    assert bad.reason == "invalid_position"


def test_an_exported_list_reads_back_the_same() -> None:
    text = tracks_to_text([_track(1), _track(2) | {"duration": 3723}], "My list")

    tracks = parse_tracks(text + "not a link\nhttps://youtu.be/v1\n")

    assert text.startswith("# My list\n")
    assert [(t["url"], t["title"], t["duration"]) for t in tracks] == [
        ("https://youtu.be/v1", "song 1", 120), ("https://youtu.be/v2", "song 2", 3723)
    ]
    assert tracks[0]["video_id"] == "v1"


def test_a_plain_list_of_links_can_be_imported() -> None:
    tracks = parse_tracks("https://www.youtube.com/watch?v=abc\nhttps://soundcloud.com/a/b\n")

    assert [t["title"] for t in tracks] == ["https://www.youtube.com/watch?v=abc", "https://soundcloud.com/a/b"]
    assert tracks[0]["video_id"] == "abc"
