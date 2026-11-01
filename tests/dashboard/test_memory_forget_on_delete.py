"""Deleting a member's memory as the bot owner also makes the running bot forget what it recalled of them."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

import pytest

from dashboard.routers import admin
from llm.memory.episodic import EpisodicMemoryProvider

MEMBER = 11
GUILD = 42
CHANNEL = 7


class _Request:
    """Stands in for the FastAPI request: a JSON body and the app's bot."""

    def __init__(self, bot: Any) -> None:
        self.app = SimpleNamespace(state=SimpleNamespace(bot=bot))

    async def json(self) -> dict:
        """The confirmation the owner's page sends."""
        return {"confirm": True}


def _bot(deleted: List[str]) -> Any:
    class Store:
        async def delete_vectors_by_user(self, user_id: str) -> int:
            deleted.append(user_id)
            return -1

        async def search_memories_by_vector(self, **kwargs: Any) -> list:
            return []

    known = {"LeaderboardCog": SimpleNamespace(store=SimpleNamespace(read_optouts=lambda guild_id: set()))}
    return SimpleNamespace(get_cog=known.get, vector_manager=SimpleNamespace(store=Store()))


@pytest.mark.asyncio
async def test_the_owner_deleting_a_member_clears_what_the_bot_recalled_of_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(admin, "ROOT_DIR", str(tmp_path))
    monkeypatch.setattr(admin, "_PROCEDURAL_DB", tmp_path / "missing.db")
    deleted: List[str] = []
    bot = _bot(deleted)
    provider = EpisodicMemoryProvider(bot)
    bot.orchestrator = SimpleNamespace(context_manager=SimpleNamespace(episodic_provider=provider))
    fragment = SimpleNamespace(content="the concert plan of the member", metadata={"fragment_id": "a", "author_ids": [str(MEMBER)]})
    provider.remember(str(CHANNEL), [fragment])

    await admin.admin_delete_user_memory(str(MEMBER), _Request(bot), user={"sub": "owner"})

    assert deleted == [str(MEMBER)]
    message = SimpleNamespace(
        content="when was that", channel=SimpleNamespace(id=CHANNEL), guild=SimpleNamespace(id=GUILD), author=SimpleNamespace(id=1)
    )
    assert await provider.get(message) is None
