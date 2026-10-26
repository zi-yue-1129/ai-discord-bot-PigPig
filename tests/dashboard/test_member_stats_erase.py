"""Every way of deleting a member's data from the dashboard also deletes their public words."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from cogs.memory.db.connection import DatabaseConnection
from cogs.memory.db.schema import create_tables
from cogs.memory.db.stats_storage import StatsStorage

USER = "608669094580977665"
GUILD = "903273027993743381"
OTHER_GUILD = "111111111111111111"


def _run(coroutine: Any) -> Any:
    """Runs a coroutine on a private loop. Not ``asyncio.run``: it would leave the thread
    without a current event loop, which breaks the tests that run after these."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


def _seed(path: Path) -> StatsStorage:
    db = DatabaseConnection(path)
    with db.get_connection() as conn:
        create_tables(conn)
    storage = StatsStorage(db)

    async def write() -> None:
        for guild in (GUILD, OTHER_GUILD):
            await storage.upsert_user_stats(USER, guild, "publicword", "1", "2026-10-20T04:00:00Z", public=True)

    _run(write())
    return storage


def _words(storage: StatsStorage, guild: str) -> list:
    return _run(storage.get_user_public_terms(USER, guild, "word", ["1"]))


def _client(monkeypatch: pytest.MonkeyPatch, db_path: Path, payload: dict[str, Any]) -> Any:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from dashboard.middleware.permission import get_current_user, require_owner
    from dashboard.routers import admin, user

    for module in (admin, user):
        monkeypatch.setattr(module, "_PROCEDURAL_DB", db_path)
        monkeypatch.setattr(module, "ROOT_DIR", str(db_path.parent))
    app = FastAPI()
    app.state.bot = SimpleNamespace(vector_manager=None)
    app.include_router(admin.router)
    app.include_router(user.router)
    app.dependency_overrides[get_current_user] = lambda: payload
    app.dependency_overrides[require_owner] = lambda: payload
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("route", "body", "left"),
    [
        (f"/api/user/memory/episodic/{GUILD}", None, [OTHER_GUILD]),
        ("/api/user/memory", {"confirm": True}, []),
        (f"/api/admin/users/{USER}/memory", {"confirm": True}, []),
    ],
)
def test_each_erase_path_removes_public_words_and_they_do_not_come_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: str, body: Any, left: list
) -> None:
    storage = _seed(tmp_path / "procedural.db")
    client = _client(monkeypatch, tmp_path / "procedural.db", {"sub": USER, "role": "owner", "guild_ids": []})

    response = client.request("DELETE", route, json=body)

    assert response.status_code == 200, response.text
    for guild in (GUILD, OTHER_GUILD):
        assert bool(_words(storage, guild)) == (guild in left)
    # A new message starts a fresh profile: the erased words do not reappear.
    _run(storage.upsert_user_stats(USER, GUILD, "freshword", "1", "2026-10-21T04:00:00Z", public=True))
    assert _words(storage, GUILD) == [("freshword", 1)]
    assert _run(storage.get_user_stats(USER, GUILD))["total_messages"] == 1


def test_erasing_works_on_a_database_without_the_public_words_table(tmp_path: Path) -> None:
    import aiosqlite

    from dashboard.services.member_stats import delete_member_stats

    async def run() -> dict:
        async with aiosqlite.connect(str(tmp_path / "old.db")) as db:
            await db.execute("CREATE TABLE user_stats (user_id TEXT, guild_id TEXT)")
            await db.execute("INSERT INTO user_stats VALUES (?, ?)", (USER, GUILD))
            return await delete_member_stats(db, USER, GUILD)

    assert _run(run()) == {"user_stats": 1, "user_public_terms": 0}
