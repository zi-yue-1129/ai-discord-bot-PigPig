"""Memory must not leak across guilds: dashboard channel memory and episodic global search."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest
from fastapi import HTTPException

from cogs.memory.vector_stores.qdrant_store import QdrantStore
from dashboard.routers import guild as guild_router
from llm.tools.episodic_memory import EpisodicMemoryTools

GUILD = "100"
OTHER_GUILD = "200"
CHANNEL = 555
MEMBER_ID = "42"


# ------------------------------------------------------------- dashboard


def _channel(guild_id: str, readable: bool) -> SimpleNamespace:
    member = SimpleNamespace(id=int(MEMBER_ID))
    guild = SimpleNamespace(id=int(guild_id), get_member=lambda user_id: member if user_id == int(MEMBER_ID) else None)
    return SimpleNamespace(id=CHANNEL, guild=guild, permissions_for=lambda who: SimpleNamespace(read_messages=readable))


def _request(channel: Optional[SimpleNamespace]) -> SimpleNamespace:
    bot = SimpleNamespace(get_channel=lambda channel_id: channel if channel_id == CHANNEL else None)
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(bot=bot, qdrant_client=None)))


def _member() -> Dict[str, Any]:
    return {"sub": MEMBER_ID, "role": "user", "guild_ids": [GUILD]}


@pytest.fixture(autouse=True)
def no_databases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guild_router, "_EPISODIC_DB", tmp_path / "missing_episodic.db")
    monkeypatch.setattr(guild_router, "_PROCEDURAL_DB", tmp_path / "missing_procedural.db")


@pytest.mark.asyncio
async def test_a_channel_of_another_guild_cannot_be_read_through_my_guild() -> None:
    request = _request(_channel(OTHER_GUILD, readable=True))

    with pytest.raises(HTTPException) as raised:
        await guild_router.get_channel_memory(GUILD, str(CHANNEL), request, user=_member())

    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_an_unknown_channel_is_not_found() -> None:
    with pytest.raises(HTTPException) as raised:
        await guild_router.get_channel_memory(GUILD, "999", _request(None), user=_member())

    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_a_channel_the_member_cannot_see_is_forbidden() -> None:
    request = _request(_channel(GUILD, readable=False))

    with pytest.raises(HTTPException) as raised:
        await guild_router.get_channel_memory(GUILD, str(CHANNEL), request, user=_member())

    assert raised.value.status_code == 403


@pytest.mark.asyncio
async def test_a_member_can_read_a_channel_they_can_see() -> None:
    request = _request(_channel(GUILD, readable=True))

    response = await guild_router.get_channel_memory(GUILD, str(CHANNEL), request, user=_member())

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_the_owner_can_read_any_channel_of_the_guild() -> None:
    request = _request(_channel(GUILD, readable=False))
    owner = {"sub": "1", "role": "owner", "guild_ids": []}

    response = await guild_router.get_channel_memory(GUILD, str(CHANNEL), request, user=owner)

    assert response.status_code == 200


# ------------------------------------------------------- episodic search


class _Store:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    async def search(self, **kwargs: Any) -> list:
        self.calls.append(kwargs)
        return []


def _search_tool(store: _Store, guild: Optional[SimpleNamespace]) -> Any:
    bot = SimpleNamespace(vector_manager=SimpleNamespace(store=store))
    message = SimpleNamespace(channel=SimpleNamespace(id=CHANNEL), guild=guild)
    runtime = SimpleNamespace(bot=bot, message=message, logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]
    return tool


@pytest.mark.asyncio
async def test_a_global_search_covers_every_channel_of_this_guild_only() -> None:
    store = _Store()

    await _search_tool(store, SimpleNamespace(id=int(GUILD))).ainvoke({"vector_query": "trip", "global_search": True})

    assert store.calls[0]["channel_id"] is None
    assert store.calls[0]["guild_id"] == GUILD


@pytest.mark.asyncio
async def test_a_normal_search_stays_in_this_channel_and_guild() -> None:
    store = _Store()

    await _search_tool(store, SimpleNamespace(id=int(GUILD))).ainvoke({"vector_query": "trip"})

    assert store.calls[0]["channel_id"] == str(CHANNEL)
    assert store.calls[0]["guild_id"] == GUILD


@pytest.mark.asyncio
async def test_a_global_search_in_a_direct_message_stays_in_that_conversation() -> None:
    store = _Store()

    await _search_tool(store, None).ainvoke({"vector_query": "trip", "global_search": True})

    assert store.calls[0]["channel_id"] == str(CHANNEL)
    assert store.calls[0]["guild_id"] is None


def _keys(conditions: list) -> Dict[str, Any]:
    return {condition.key: condition for condition in conditions}


def test_the_qdrant_filter_restricts_the_guild() -> None:
    conditions = _keys(QdrantStore._metadata_conditions(user_id=None, channel_id=None, guild_id=GUILD))

    assert set(conditions) == {"metadata.guild_id"}
    assert conditions["metadata.guild_id"].match.value == GUILD


def test_the_qdrant_filter_combines_user_channel_and_guild() -> None:
    conditions = _keys(QdrantStore._metadata_conditions(user_id="7", channel_id=str(CHANNEL), guild_id=GUILD))

    assert set(conditions) == {"metadata.author_ids", "metadata.channel_id", "metadata.guild_id"}
