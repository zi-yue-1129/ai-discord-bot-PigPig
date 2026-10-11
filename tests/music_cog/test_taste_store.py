"""The guild taste memory is kept in a SQLite database and survives restarts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

import pytest
from music_cog.helpers import GUILD_ID, REQUESTER_ID, FakeVoiceClient, make_song

from addons.settings import AutoplaySettings
from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.recommender import TasteMemory
from cogs.music_lib.taste_store import TasteStore


@pytest.fixture
def store(tmp_path: Path) -> TasteStore:
    return TasteStore(tmp_path / "music" / "taste.db")


def _reopen(store: TasteStore, guild_id: int, history_size: int = 10) -> TasteMemory:
    """A fresh memory over the same database file, as after a bot restart."""
    return TasteMemory(history_size=history_size, store=TasteStore(store.path), guild_id=guild_id)


def test_the_default_database_path_is_in_the_data_folder() -> None:
    assert AutoplaySettings().database_path == "data/music/taste.db"


def test_a_new_guild_starts_empty(store: TasteStore) -> None:
    memory = _reopen(store, guild_id=1)

    assert memory.played_ids() == set()
    assert dict(memory.requested) == {}


def test_history_requests_and_skips_survive_a_restart(store: TasteStore) -> None:
    memory = TasteMemory(history_size=10, store=store, guild_id=1)
    memory.record_played("a")
    memory.record_played("b")
    memory.record_request("YOASOBI - Topic")
    memory.record_request("yoasobi")
    memory.record_skip("Eve")

    restored = _reopen(store, guild_id=1)

    assert restored.played_ids() == {"a", "b"}
    assert restored.requested["yoasobi"] == 2
    assert restored.skipped["eve"] == 1


def test_guilds_do_not_share_their_taste(store: TasteStore) -> None:
    first = TasteMemory(history_size=10, store=store, guild_id=1)
    first.record_played("a")
    first.record_request("Eve")

    other = _reopen(store, guild_id=2)

    assert other.played_ids() == set()
    assert other.requested["eve"] == 0


def test_only_the_most_recent_songs_are_kept_in_the_database(store: TasteStore) -> None:
    memory = TasteMemory(history_size=3, store=store, guild_id=1)
    for video_id in ("a", "b", "c", "d", "e"):
        memory.record_played(video_id)

    assert _reopen(store, guild_id=1, history_size=3).played_ids() == {"c", "d", "e"}
    assert store.history_row_count(1) == 3


def test_a_smaller_history_size_trims_what_is_loaded(store: TasteStore) -> None:
    memory = TasteMemory(history_size=5, store=store, guild_id=1)
    for video_id in ("a", "b", "c", "d"):
        memory.record_played(video_id)

    assert _reopen(store, guild_id=1, history_size=2).played_ids() == {"c", "d"}


def test_a_database_that_cannot_be_used_is_reported_but_the_memory_still_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where a folder is needed", encoding="utf-8")
    errors: List[str] = []

    class _Log:
        def error(self, message: str, *args: Any, **kwargs: Any) -> None:
            errors.append(message)

    monkeypatch.setattr("cogs.music_lib.taste_store.log", _Log())
    memory = TasteMemory(history_size=3, store=TasteStore(blocker / "taste.db"), guild_id=1)

    memory.record_played("a")
    memory.record_request("Eve")

    assert memory.played_ids() == {"a"}
    assert memory.requested["eve"] == 1
    assert len(errors) >= 2


# ------------------------------------------------------------------ the cog


@pytest.mark.asyncio
async def test_the_cog_restores_the_taste_after_a_restart(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_ui(*args: Any, **kwargs: Any) -> None:
        return None

    async def idle() -> None:
        return None

    monkeypatch.setattr(cog.audio_manager, "create_audio_source", lambda song, volume=1.0, start_offset=0.0: "source")
    monkeypatch.setattr(cog.ui_manager, "update_player_ui", fake_ui, raising=False)
    monkeypatch.setattr(cog, "_player_loop", lambda ctx, song, start_offset=0.0: idle())
    song = make_song(1) | {"author": "Eve - Topic", "added_by": REQUESTER_ID}
    await cog._play_song(ctx, song, voice_client)

    cog._taste.clear()  # what a restart does to the in-memory state

    restored = cog.taste_for(GUILD_ID)
    assert restored.played_ids() == {"v1"}
    assert restored.requested["eve"] == 1
