"""/memory clear forgets what the member said: the words and emojis counted from their messages."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from cogs.memory.db.connection import DatabaseConnection
from cogs.memory.db.procedural_storage import ProceduralStorage
from cogs.memory.db.stats_storage import StatsStorage
from cogs.memory.users.manager import SQLiteUserManager
from cogs.userdata import ClearMemoryConfirmView, UserDataCog

USER = 608669094580977665
GUILD = "903273027993743381"


class _Response:
    async def edit_message(self, **kwargs: Any) -> None:
        pass


class _Interaction:
    def __init__(self) -> None:
        self.user = SimpleNamespace(id=USER, display_name="pig", name="pig")
        self.guild_id = int(GUILD)
        self.guild = SimpleNamespace(id=int(GUILD))
        self.response = _Response()
        self.edits: List[Dict[str, Any]] = []

    async def edit_original_response(self, **kwargs: Any) -> None:
        self.edits.append(kwargs)


@pytest.mark.asyncio
async def test_erasing_from_the_button_forgets_the_words_but_keeps_the_counts(tmp_path: Path) -> None:
    db = DatabaseConnection(tmp_path / "procedural.db")
    stats = StatsStorage(db)
    procedural = ProceduralStorage(db)
    await procedural.update_user_data(discord_id=str(USER), discord_name="pig", procedural_memory="likes pizza")
    await stats.upsert_user_stats(str(USER), GUILD, "publicword 😀", "1", "2026-10-20T04:00:00Z", public=True)
    bot = SimpleNamespace(get_cog=lambda name: None, orchestrator=None)
    cog = UserDataCog(bot, SQLiteUserManager(procedural))
    cog._translate = lambda guild_id, *path, fallback_key=None, **kwargs: fallback_key
    interaction = _Interaction()

    await ClearMemoryConfirmView(cog, user_id=USER, guild_id=GUILD).confirm.callback(interaction)

    assert interaction.edits[-1]["content"] == "clear_success"
    assert await stats.get_user_public_terms(str(USER), GUILD, "word", ["1"]) == []
    kept = await stats.get_user_stats(str(USER), GUILD)
    assert kept["top_words"] == {} and kept["top_emojis"] == {} and kept["total_messages"] == 1
    # A new message starts the words over: the forgotten ones do not come back.
    await stats.upsert_user_stats(str(USER), GUILD, "freshword", "1", "2026-10-21T04:00:00Z", public=True)
    assert await stats.get_user_public_terms(str(USER), GUILD, "word", ["1"]) == [("freshword", 1)]
    assert (await stats.get_user_stats(str(USER), GUILD))["top_words"] == {"freshword": 1}


@pytest.mark.asyncio
async def test_a_member_with_only_counted_words_can_still_erase_them(tmp_path: Path) -> None:
    db = DatabaseConnection(tmp_path / "procedural.db")
    stats = StatsStorage(db)
    await stats.upsert_user_stats(str(USER), GUILD, "publicword", "1", "2026-10-20T04:00:00Z", public=True)

    assert await ProceduralStorage(db).delete_user_data(str(USER)) is True
    assert await stats.get_user_public_terms(str(USER), GUILD, "word", ["1"]) == []
