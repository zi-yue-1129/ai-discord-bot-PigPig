"""User statistics must count each message once, in local time, and keep new words reachable."""

from __future__ import annotations

import ast
import json
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Iterator, List, Tuple

import pytest

from cogs import stats_cog
from cogs.memory.db.connection import DatabaseConnection
from cogs.memory.db.schema import create_tables
from cogs.memory.db.stats_storage import StatsStorage, _MAX_TOP_WORDS
from cogs.stats_cog import StatsCog

REPO = Path(__file__).resolve().parents[1]
GUILD = "903273027993743381"
USER = "608669094580977665"


@pytest.fixture
def storage(tmp_path: Path) -> StatsStorage:
    db = DatabaseConnection(tmp_path / "procedural.db")
    with db.get_connection() as conn:
        create_tables(conn)
    return StatsStorage(db)


@pytest.fixture
def taipei_time(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TZ", "Asia/Taipei")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def _row(storage: StatsStorage) -> dict:
    return storage._get_user_stats_sync(USER, GUILD)


class _Collector:
    def __init__(self) -> None:
        self.live: List[Tuple[str, str, str]] = []
        self.imported: List[tuple] = []

    async def record_message(self, guild_id: str, user_id: str, channel_id: str) -> None:
        self.live.append((guild_id, user_id, channel_id))

    async def bulk_record_messages(self, records: list) -> None:
        self.imported.extend(records)


def _cog(storage: StatsStorage, collector: _Collector) -> StatsCog:
    bot = SimpleNamespace(procedural_storage=SimpleNamespace(db=storage.db), stats_collector=collector)
    return StatsCog(bot)


# ------------------------------------------------------------ #6 counted once


def _calls_record_message(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.Attribute) and node.attr == "record_message" for node in ast.walk(tree)
    )


def test_only_the_stats_cog_records_the_dashboard_message_event() -> None:
    assert not _calls_record_message(REPO / "bot.py")
    assert _calls_record_message(REPO / "cogs" / "stats_cog.py")


@pytest.mark.asyncio
async def test_the_stats_cog_records_one_event_per_message(storage: StatsStorage) -> None:
    collector = _Collector()
    message = SimpleNamespace(
        guild=SimpleNamespace(id=int(GUILD)),
        author=SimpleNamespace(id=int(USER), bot=False),
        channel=SimpleNamespace(id=1, name="chat"),
        created_at=None,
        content="hello there",
    )

    await _cog(storage, collector).on_message(message)

    assert collector.live == [(GUILD, USER, "1")]


# ------------------------------------------------------ #7 no re-import


@pytest.mark.asyncio
async def test_a_fresh_install_imports_only_days_before_today(storage: StatsStorage) -> None:
    assert await storage.get_or_init_live_since("20261012") == "20261012"
    assert await storage.get_or_init_live_since("20261020") == "20261012"


@pytest.mark.asyncio
async def test_an_upgrade_treats_days_after_the_earliest_import_as_already_counted(
    storage: StatsStorage,
) -> None:
    await storage.set_migration_state("1", "20261012")
    await storage.set_migration_state("2", "20251124")

    assert await storage.get_or_init_live_since("20261012") == "20251125"


def _write_log(guild_dir: Path, day: str, count: int) -> None:
    folder = guild_dir / day
    folder.mkdir(parents=True)
    record = {
        "timestamp": f"{day[:4]}-{day[4:6]}-{day[6:]}T01:00:00Z",
        "user_id": USER,
        "action": "receive_message",
        "message": "hello there",
        "channel_or_file": "chat",
        "extra": {"channel_id": "1"},
    }
    (folder / "info.jsonl").write_text("\n".join([json.dumps(record)] * count), encoding="utf-8")


@pytest.mark.asyncio
async def test_days_logged_while_counting_live_are_never_imported_again(
    storage: StatsStorage, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_wait(seconds: float) -> None:
        assert seconds >= 0

    monkeypatch.setattr(stats_cog.asyncio, "sleep", no_wait)
    guild_dir = tmp_path / "logs" / GUILD
    _write_log(guild_dir, "20261010", 2)
    _write_log(guild_dir, "20261011", 3)
    _write_log(guild_dir, "20261012", 5)
    collector = _Collector()

    await _cog(storage, collector)._migrate_guild_logs(GUILD, guild_dir, live_since="20261011")

    assert len(collector.imported) == 2
    assert _row(storage)["total_messages"] == 2


# --------------------------------------------------------- #8 local time


@pytest.mark.asyncio
async def test_active_hours_and_streak_days_use_local_time(storage: StatsStorage, taipei_time: None) -> None:
    await storage.upsert_user_stats(USER, GUILD, "hello there", "1", "2026-10-11T17:30:00Z")

    row = _row(storage)
    assert row["active_hours"] == {"1": 1}
    assert row["streak_last_date"] == "2026-10-12"


@pytest.mark.asyncio
async def test_imported_log_records_also_use_local_time(storage: StatsStorage, taipei_time: None) -> None:
    record = {"user_id": USER, "guild_id": GUILD, "message_content": "hello", "channel_id": "1",
              "timestamp": "2026-10-11T17:30:00Z"}

    await storage.bulk_upsert_user_stats([record])

    assert _row(storage)["active_hours"] == {"1": 1}


# --------------------------------------------------- #9 word cloud moves


@pytest.mark.asyncio
async def test_a_new_favourite_word_enters_a_full_word_cloud(storage: StatsStorage) -> None:
    await storage.upsert_user_stats(USER, GUILD, "hello", "1", "2026-10-11T01:00:00Z")
    old_words = {f"oldword{index:03d}": 3 for index in range(_MAX_TOP_WORDS)}
    with storage.db.get_connection() as conn:
        conn.execute("UPDATE user_stats SET top_words = ?", (json.dumps(old_words),))
        conn.commit()

    for _ in range(10):
        await storage.upsert_user_stats(USER, GUILD, "zebra", "1", "2026-10-11T01:00:00Z")

    top_words = _row(storage)["top_words"]
    assert len(top_words) == _MAX_TOP_WORDS
    assert top_words["zebra"] > 3
    assert max(top_words, key=top_words.get) == "zebra"
